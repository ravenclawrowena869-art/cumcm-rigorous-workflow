from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

N=144; DELTA=1/6; ETA=.9; EMIN=1200.; EMAX=10800.; XMAX=5000/6; E0=6000.; TOL=1e-7

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False, default=str)+'\n', encoding='utf-8')

def maxabs(x): return float(np.max(np.abs(np.asarray(x, float))))

def validate(root: Path, mode: str):
    folder=root/'results'/('causal' if mode=='CAUSAL_LAG7' else 'oracle')
    df=pd.read_csv(folder/'slot_replay.csv'); plan=pd.read_csv(folder/'day_ahead_plan.csv')
    daily=pd.read_csv(folder/'daily_metrics.csv'); summary=json.loads((folder/'annual_summary.json').read_text())
    audit=pd.read_csv(folder/'price_audit.csv'); price=pd.read_csv(root/'inputs'/'q4_price_lag7_feb_dec.csv')
    forecast=pd.read_csv(root/'inputs'/'annual_forecast_q2_frozen.csv')
    q80=pd.read_csv(root/'inputs'/'q80_margin_audit_q2_frozen.csv')
    dates=pd.date_range('2025-02-01','2025-12-31',freq='D')
    checks={}; detail={}
    checks['coverage']=len(df)==334*N and len(plan)==334*N and len(daily)==334 and df.groupby('date').size().eq(N).all()
    checks['q_da_immutability']=maxabs(df.q_DA_kWh-plan.q_DA_kWh)<=1e-10
    checks['frozen_forecast_identity']=maxabs(df.forecast_load_kWh-forecast.forecast_load_kW*DELTA)<=1e-9 and maxabs(df.forecast_pv_kWh-forecast.forecast_pv_kW*DELTA)<=1e-9
    checks['frozen_q80_identity']=maxabs(df.reserve_margin_kWh-q80.reserve_margin_kWh)<=1e-10 and bool(np.allclose(q80.alpha,.8,rtol=0,atol=1e-15))
    ordered_price=price.sort_values(['date','slot']).reset_index(drop=True)
    ordered=df.sort_values(['date','slot']).reset_index(drop=True); ordered_plan=plan.sort_values(['date','slot']).reset_index(drop=True)
    checks['settlement_price_attachment4']=maxabs(ordered.settlement_price_CNY_per_kWh-ordered_price.price_realized)<=1e-12
    if mode=='CAUSAL_LAG7':
        checks['day_ahead_price_causal']=maxabs(ordered_plan.decision_price_CNY_per_kWh-ordered_price.price_forecast_lag7)<=1e-12 and bool((ordered_plan.price_source=='LAG7_REALIZED').all())
        checks['intraday_current_price_only']=maxabs(ordered.decision_price_CNY_per_kWh-ordered_price.price_realized)<=1e-12 and bool((ordered.price_source=='CURRENT_REALIZED').all())
        checks['price_known_at']=bool((pd.to_datetime(audit.known_at_max)<=pd.to_datetime(audit.decision_time)).all()) and int(audit.causal_contract_bad_count.sum())==0
        checks['future_realized_leakage']=int(summary['price_future_realized_leak_count'])==0
    else:
        checks['oracle_tag_only']=set(ordered.price_mode)=={'ORACLE_DIAGNOSTIC'} and set(ordered_plan.price_mode)=={'ORACLE_DIAGNOSTIC'}
        checks['oracle_prices_actual']=maxabs(ordered.decision_price_CNY_per_kWh-ordered_price.price_realized)<=1e-12 and maxabs(ordered_plan.decision_price_CNY_per_kWh-ordered_price.price_realized)<=1e-12
    b=ordered.q_DA_kWh+ordered.actual_pv_kWh-ordered.actual_load_kWh
    c=ordered.charge_exec_kWh.to_numpy(float); d=ordered.discharge_exec_kWh.to_numpy(float); r=ordered.emergency_kWh.to_numpy(float)
    w=ordered.paid_unused_normal_kWh.to_numpy(float); v=ordered.pv_curtailment_kWh.to_numpy(float)
    checks['direction_no_emergency_charge']=bool((d[b>=-TOL]<=TOL).all() and (r[b>=-TOL]<=TOL).all() and (c[b<-TOL]<=TOL).all() and (c[r>TOL]<=TOL).all())
    checks['emergency_last']=maxabs(r-np.maximum(-b-d,0))<=TOL
    checks['no_simultaneous_charge_discharge']=bool((np.minimum(c,d)<=TOL).all())
    balance=ordered.q_DA_kWh-w+r+ordered.actual_pv_kWh+d-ordered.actual_load_kWh-c-v
    checks['s1a_balance']=maxabs(balance)<=TOL
    checks['s1a_bounds']=bool((w>=-TOL).all() and (w<=ordered.q_DA_kWh+TOL).all() and (v>=-TOL).all() and (v<=ordered.actual_pv_kWh+TOL).all())
    soc=[]; cur=E0; bridge=0
    for x in ordered.itertuples(index=False):
        bridge += int(abs(x.SOC_start_kWh-cur)>TOL)
        cur=cur+ETA*x.charge_exec_kWh-x.discharge_exec_kWh/ETA; soc.append(cur)
    soc=np.asarray(soc)
    checks['soc_recursion_and_cross_day']=maxabs(soc-ordered.SOC_end_kWh)<=TOL and bridge==0
    checks['soc_bounds']=bool(soc.min()>=EMIN-TOL and soc.max()<=EMAX+TOL)
    checks['power_bounds']=bool((c>=-TOL).all() and (d>=-TOL).all() and (c<=XMAX+TOL).all() and (d<=XMAX+TOL).all())
    checks['terminal_contract']=EMIN-TOL<=soc[-1]<=EMAX+TOL
    checks['no_fallback']=int(ordered.fallback_used.sum())==0
    normal=float(np.sum(ordered.settlement_price_CNY_per_kWh*ordered.q_DA_kWh)); emerg=float(np.sum(5*ordered.settlement_price_CNY_per_kWh*ordered.emergency_kWh)); total=normal+emerg
    checks['dynamic_price_accounting']=abs(normal-summary['normal_cost_yuan'])<=1e-6 and abs(emerg-summary['emergency_cost_yuan'])<=1e-6 and abs(total-summary['realized_total_cost_yuan'])<=1e-6
    daily_rebuilt=ordered.groupby('date',sort=True).agg(normal_cost_yuan=('normal_cost_yuan','sum'),emergency_cost_yuan=('emergency_cost_yuan','sum'),emergency_kWh=('emergency_kWh','sum')).reset_index()
    daily_rebuilt['total_cost_yuan']=daily_rebuilt.normal_cost_yuan+daily_rebuilt.emergency_cost_yuan
    checks['daily_metrics_identity']=maxabs(daily_rebuilt.total_cost_yuan-daily.total_cost_yuan)<=1e-6 and maxabs(daily_rebuilt.emergency_cost_yuan-daily.emergency_cost_yuan)<=1e-6
    detail={'mode':mode,'max_balance_abs_kWh':maxabs(balance),'max_soc_recursion_abs_kWh':maxabs(soc-ordered.SOC_end_kWh),'cross_day_bridge_mismatch_count':bridge,
            'recomputed_normal_cost_yuan':normal,'recomputed_emergency_cost_yuan':emerg,'recomputed_total_cost_yuan':total,
            'soc_min_kWh':float(soc.min()),'soc_max_kWh':float(soc.max()),'soc_end_kWh':float(soc[-1]),
            'future_realized_price_leak_count':int(summary.get('price_future_realized_leak_count',0))}
    verdict='PASS' if all(checks.values()) else 'FAIL_REOPEN'
    out={'validator_verdict':verdict,'checks':checks,'details':detail}
    write_json(folder/'validator.json',out)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
    if verdict!='PASS': raise SystemExit(2)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--mode',choices=['CAUSAL_LAG7','ORACLE_DIAGNOSTIC'],required=True)
    a=ap.parse_args(); validate(a.root.resolve(),a.mode)
