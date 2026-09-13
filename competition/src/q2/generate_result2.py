#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from artifact_tool import Blob, SpreadsheetFile

PERIODS = [
    "0:00-4:00", "4:00-8:00", "8:00-12:00",
    "12:00-16:00", "16:00-20:00", "20:00-24:00",
]

def load_rows(slot_csv: Path):
    with slot_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("empty winner slot replay")
    required = {
        "date","slot","q_DA_kWh","charge_exec_kWh","discharge_exec_kWh",
        "emergency_kWh","SOC_start_kWh","SOC_end_kWh","normal_cost_yuan",
    }
    missing = required - set(rows[0])
    if missing:
        raise RuntimeError(f"missing columns: {sorted(missing)}")
    by = {}
    for r in rows:
        by.setdefault(r["date"], []).append(r)
    if len(by) != 334 or len(rows) != 334 * 144:
        raise RuntimeError(f"coverage mismatch days={len(by)} rows={len(rows)}")
    for d, ds in by.items():
        slots = [int(x["slot"]) for x in sorted(ds, key=lambda z: int(z["slot"]))]
        if slots != list(range(1,145)):
            raise RuntimeError(f"{d}: slots not exactly 1..144")
    return rows, by

def build(slot_csv: Path, labels_json: Path, template_xlsx: Path, output_xlsx: Path, tol: float = 1e-9):
    labels = json.loads(labels_json.read_text(encoding="utf-8"))["slot_labels"]
    if len(labels) != 144:
        raise RuntimeError("official slot labels must contain exactly 144 labels")
    rows, by = load_rows(slot_csv)

    s1_rows = [["日期\\时间"] + labels + ["全天购电量", "全天购电费"]]
    s2_rows = [["日期", "时间段", "充电量", "放电量", "时刻", "储电量"]]
    s3_rows = [["日期", "购电时间段", "购电量"]]

    for d in sorted(by):
        ds = sorted(by[d], key=lambda x: int(x["slot"]))
        q = [float(x["q_DA_kWh"]) for x in ds]
        normal_cost = sum(float(x["normal_cost_yuan"]) for x in ds)
        s1_rows.append([datetime.fromisoformat(d)] + q + [sum(q), normal_cost])

        for k, period in enumerate(PERIODS):
            block = ds[k*24:(k+1)*24]
            s2_rows.append([
                datetime.fromisoformat(d) if k == 0 else None,
                period,
                sum(float(x["charge_exec_kWh"]) for x in block),
                sum(float(x["discharge_exec_kWh"]) for x in block),
                "0:00" if k == 0 else ("24:00" if k == 1 else None),
                float(ds[0]["SOC_start_kWh"]) if k == 0 else (
                    float(ds[-1]["SOC_end_kWh"]) if k == 1 else None
                ),
            ])

        active = [int(x["slot"]) for x in ds if float(x["emergency_kWh"]) > tol]
        groups = []
        for s in active:
            if not groups or s != groups[-1][-1] + 1:
                groups.append([s])
            else:
                groups[-1].append(s)
        first = True
        for g in groups:
            first_label = labels[g[0]-1]
            last_label = labels[g[-1]-1]
            start = first_label.split("-", 1)[0]
            end = last_label.split("-", 1)[1]
            amount = sum(float(ds[s-1]["emergency_kWh"]) for s in g)
            s3_rows.append([
                datetime.fromisoformat(d) if first else None,
                f"{start}-{end}",
                amount,
            ])
            first = False

    wb = SpreadsheetFile.import_xlsx(Blob.load(str(template_xlsx)))
    s1 = wb.worksheets.get_item("计划购电量")
    s2 = wb.worksheets.get_item("充放电量")
    s3 = wb.worksheets.get_item("紧急购电量")

    # 官方模板的计划购电表已经覆盖 334 天 × 144 时段。
    s1.get_range("A1:EQ335").values = s1_rows

    # 其余两张表按全年结果展开。
    s2.get_range(f"A1:F{len(s2_rows)}").values = s2_rows
    s3.get_range(f"A1:C{len(s3_rows)}").values = s3_rows

    # 保留模板结构，只设置实际填充区域的格式。
    s1.get_range("A2:A335").format.number_format = "yyyy-mm-dd"
    s1.get_range("B2:EQ335").format.number_format = "0.000000"
    s2.get_range(f"A2:A{len(s2_rows)}").format.number_format = "yyyy-mm-dd"
    s2.get_range(f"C2:D{len(s2_rows)}").format.number_format = "0.000000"
    s2.get_range(f"F2:F{len(s2_rows)}").format.number_format = "0.000000"
    s3.get_range(f"A2:A{len(s3_rows)}").format.number_format = "yyyy-mm-dd"
    s3.get_range(f"C2:C{len(s3_rows)}").format.number_format = "0.000000"

    s1.freeze_panes.freeze_rows(1)
    s2.freeze_panes.freeze_rows(1)
    s3.freeze_panes.freeze_rows(1)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    SpreadsheetFile.export_xlsx(wb).save(str(output_xlsx))
    return {
        "status": "PASS",
        "source_slot_csv": str(slot_csv),
        "output_xlsx": str(output_xlsx),
        "days": 334,
        "slot_rows": 48096,
        "sheet1_rows_including_header": len(s1_rows),
        "sheet2_rows_including_header": len(s2_rows),
        "sheet3_rows_including_header": len(s3_rows),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot-csv", required=True, type=Path)
    ap.add_argument("--labels-json", required=True, type=Path)
    ap.add_argument("--template-xlsx", required=True, type=Path)
    ap.add_argument("--output-xlsx", required=True, type=Path)
    ap.add_argument("--tol", type=float, default=1e-9)
    args = ap.parse_args()
    print(json.dumps(build(args.slot_csv, args.labels_json, args.template_xlsx, args.output_xlsx, args.tol),
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
