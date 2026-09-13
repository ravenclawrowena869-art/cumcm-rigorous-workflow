#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from artifact_tool import Blob, SpreadsheetFile

EXCEL_EPOCH = datetime(1899, 12, 30)
PERIODS = [
    "0:00-4:00", "4:00-8:00", "8:00-12:00",
    "12:00-16:00", "16:00-20:00", "20:00-24:00",
]
REQUIRED_DATES = {"2025-03-20","2025-06-21","2025-09-23","2025-12-21"}

def serial_to_date(v):
    if v is None:
        return None
    if isinstance(v, (int,float)):
        return (EXCEL_EPOCH + timedelta(days=float(v))).date().isoformat()
    if isinstance(v, datetime):
        return v.date().isoformat()
    return str(v)[:10]

def load_source(slot_csv: Path):
    with slot_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by = {}
    for r in rows:
        by.setdefault(r["date"], []).append(r)
    for d in by:
        by[d] = sorted(by[d], key=lambda x: int(x["slot"]))
    return rows, by

def expected_groups(ds, labels, tol):
    active = [int(x["slot"]) for x in ds if float(x["emergency_kWh"]) > tol]
    groups = []
    for s in active:
        if not groups or s != groups[-1][-1] + 1:
            groups.append([s])
        else:
            groups[-1].append(s)
    out = []
    for g in groups:
        start = labels[g[0]-1].split("-",1)[0]
        end = labels[g[-1]-1].split("-",1)[1]
        amount = sum(float(ds[s-1]["emergency_kWh"]) for s in g)
        out.append((f"{start}-{end}", amount, g[0], g[-1]))
    return out

def validate(workbook_xlsx: Path, slot_csv: Path, labels_json: Path, annual_summary_json: Path, tol=1e-7):
    labels = json.loads(labels_json.read_text(encoding="utf-8"))["slot_labels"]
    rows, by = load_source(slot_csv)
    summary = json.loads(annual_summary_json.read_text(encoding="utf-8"))
    wb = SpreadsheetFile.import_xlsx(Blob.load(str(workbook_xlsx)))
    s1 = wb.worksheets.get_item("计划购电量")
    s2 = wb.worksheets.get_item("充放电量")
    s3 = wb.worksheets.get_item("紧急购电量")
    v1 = s1.get_range("A1:EQ335").values
    v2 = s2.get_range("A1:F2005").values

    group_count = sum(len(expected_groups(by[d], labels, 1e-9)) for d in sorted(by))
    v3 = s3.get_range(f"A1:C{group_count+1}").values

    checks = {}
    details = {}

    checks["sheet_names"] = True
    checks["sheet1_header"] = v1[0] == ["日期\\时间"] + labels + ["全天购电量","全天购电费"]
    checks["sheet1_334x144"] = len(v1) == 335 and all(len(r) == 147 for r in v1)
    exp_dates = sorted(by)
    got_dates = [serial_to_date(r[0]) for r in v1[1:]]
    checks["sheet1_dates"] = got_dates == exp_dates

    max_slot_diff = 0.0
    max_daily_energy_diff = 0.0
    max_daily_cost_diff = 0.0
    wb_normal_energy = 0.0
    wb_normal_cost = 0.0
    for i,d in enumerate(exp_dates, start=1):
        ds = by[d]
        wbq = [float(x) for x in v1[i][1:145]]
        srcq = [float(x["q_DA_kWh"]) for x in ds]
        max_slot_diff = max(max_slot_diff, max(abs(a-b) for a,b in zip(wbq,srcq)))
        src_e = sum(srcq)
        src_c = sum(float(x["normal_cost_yuan"]) for x in ds)
        max_daily_energy_diff = max(max_daily_energy_diff, abs(float(v1[i][145])-src_e))
        max_daily_cost_diff = max(max_daily_cost_diff, abs(float(v1[i][146])-src_c))
        wb_normal_energy += float(v1[i][145])
        wb_normal_cost += float(v1[i][146])

    checks["sheet1_slot_identity"] = max_slot_diff <= tol
    checks["sheet1_daily_totals"] = max_daily_energy_diff <= tol and max_daily_cost_diff <= tol
    checks["annual_normal_energy"] = abs(wb_normal_energy - float(summary["normal_purchase_kWh"])) <= 1e-6
    checks["annual_normal_cost"] = abs(wb_normal_cost - float(summary["normal_cost_yuan"])) <= 1e-6
    details["sheet1_max_slot_abs_diff_kWh"] = max_slot_diff
    details["sheet1_max_daily_energy_abs_diff_kWh"] = max_daily_energy_diff
    details["sheet1_max_daily_cost_abs_diff_yuan"] = max_daily_cost_diff
    details["workbook_normal_purchase_kWh"] = wb_normal_energy
    details["workbook_normal_cost_yuan"] = wb_normal_cost

    checks["sheet2_rows"] = len(v2) == 2005
    max_cd_diff = 0.0
    max_soc_diff = 0.0
    bad_period = 0
    bad_date = 0
    for day_idx,d in enumerate(exp_dates):
        ds = by[d]
        base = 1 + day_idx*6
        for k,p in enumerate(PERIODS):
            r = v2[base+k]
            if r[1] != p:
                bad_period += 1
            if k == 0 and serial_to_date(r[0]) != d:
                bad_date += 1
            if k > 0 and r[0] is not None:
                bad_date += 1
            block = ds[k*24:(k+1)*24]
            exp_c = sum(float(x["charge_exec_kWh"]) for x in block)
            exp_d = sum(float(x["discharge_exec_kWh"]) for x in block)
            max_cd_diff = max(max_cd_diff, abs(float(r[2])-exp_c), abs(float(r[3])-exp_d))
            if k == 0:
                max_soc_diff = max(max_soc_diff, abs(float(r[5])-float(ds[0]["SOC_start_kWh"])))
            elif k == 1:
                max_soc_diff = max(max_soc_diff, abs(float(r[5])-float(ds[-1]["SOC_end_kWh"])))

    checks["sheet2_period_identity"] = bad_period == 0 and bad_date == 0
    checks["sheet2_charge_discharge_identity"] = max_cd_diff <= tol
    checks["sheet2_soc_identity"] = max_soc_diff <= tol
    details["sheet2_max_charge_discharge_abs_diff_kWh"] = max_cd_diff
    details["sheet2_max_soc_abs_diff_kWh"] = max_soc_diff

    expected3 = []
    for d in exp_dates:
        groups = expected_groups(by[d], labels, 1e-9)
        first = True
        for label,amount,s0,s1idx in groups:
            expected3.append((d if first else None, label, amount, s0, s1idx, d))
            first = False

    checks["sheet3_row_count"] = len(v3)-1 == len(expected3)
    max_emerg_diff = 0.0
    bad3 = 0
    wb_emerg = 0.0
    for i,exp in enumerate(expected3, start=1):
        dcell,label,amount,s0,s1idx,full_d = exp
        got = v3[i]
        gd = serial_to_date(got[0]) if got[0] is not None else None
        if gd != dcell or got[1] != label:
            bad3 += 1
        max_emerg_diff = max(max_emerg_diff, abs(float(got[2])-amount))
        wb_emerg += float(got[2])

    checks["sheet3_interval_identity"] = bad3 == 0 and max_emerg_diff <= tol
    checks["annual_emergency_energy"] = abs(wb_emerg-float(summary["emergency_kWh"])) <= 1e-6

    recomputed_emerg_cost = sum(float(r["emergency_cost_yuan"]) for r in rows)
    checks["annual_emergency_cost_recompute"] = abs(recomputed_emerg_cost-float(summary["emergency_cost_yuan"])) <= 1e-6
    details["sheet3_group_count"] = len(expected3)
    details["sheet3_max_emergency_abs_diff_kWh"] = max_emerg_diff
    details["workbook_emergency_kWh"] = wb_emerg
    details["recomputed_emergency_cost_yuan"] = recomputed_emerg_cost

    required = {}
    for d in sorted(REQUIRED_DATES):
        day_i = exp_dates.index(d)+1
        ds = by[d]
        qdiff = max(abs(float(v1[day_i][1+s])-float(ds[s]["q_DA_kWh"])) for s in range(144))
        base = 1 + (day_i-1)*6
        cddiff = 0.0
        for k in range(6):
            block = ds[k*24:(k+1)*24]
            cddiff = max(
                cddiff,
                abs(float(v2[base+k][2])-sum(float(x["charge_exec_kWh"]) for x in block)),
                abs(float(v2[base+k][3])-sum(float(x["discharge_exec_kWh"]) for x in block)),
            )
        required[d] = {"max_plan_abs_diff_kWh":qdiff,"max_block_cd_abs_diff_kWh":cddiff}

    checks["required_four_dates"] = all(
        x["max_plan_abs_diff_kWh"] <= tol and x["max_block_cd_abs_diff_kWh"] <= tol
        for x in required.values()
    )
    details["required_dates"] = required

    checks["annual_total_cost"] = abs((wb_normal_cost+recomputed_emerg_cost)-float(summary["realized_total_cost_yuan"])) <= 1e-6
    details["workbook_linked_total_cost_yuan"] = wb_normal_cost+recomputed_emerg_cost

    verdict = "PASS" if all(checks.values()) else "FAIL"
    return {"verdict":verdict,"checks":checks,"details":details}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook",type=Path,required=True)
    ap.add_argument("--slot-csv",type=Path,required=True)
    ap.add_argument("--labels-json",type=Path,required=True)
    ap.add_argument("--annual-summary-json",type=Path,required=True)
    ap.add_argument("--output-json",type=Path,required=True)
    args = ap.parse_args()
    out = validate(args.workbook,args.slot_csv,args.labels_json,args.annual_summary_json)
    args.output_json.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if out["verdict"] != "PASS":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
