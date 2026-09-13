from __future__ import annotations
from pathlib import Path
import argparse,json,time
import pandas as pd
from run_q4_3 import (derive_loads,check_load_adapter,build_schedules,q4_config,validate_q4_day,
                      Q4PriceProvider,INPUTS,PKG_ROOT,digest,date_range,load_actuals,load_vintages,
                      solve_q4_day,make_formal_lp_planner,write_json)

OUT=PKG_ROOT/'04_PATCH_R2'
OUT.mkdir(exist_ok=True)

def run(mode):
    loads=derive_loads(); adapter=check_load_adapter(loads)
    if adapter['status']!='PASS': raise RuntimeError('LOAD_ADAPTER_MISMATCH')
    actuals=load_actuals(INPUTS/'attachment2.xlsx')
    vints=load_vintages(INPUTS/'attachment3.xlsx'); vmap={x['issue_time']:x for x in vints}
    schedules,ll=build_schedules(actuals,vmap)
    cfg,rel=q4_config(); provider=Q4PriceProvider(INPUTS/'q4_price_lag7_feb_dec.csv')
    branch='causal' if mode=='CAUSAL_LAG7' else 'oracle'
    ref=pd.read_csv(PKG_ROOT/f'results/{branch}/daily.csv').set_index('date')
    dates=date_range('2025-02-01','2025-12-31')
    soc=6000.; state=digest({'protocol':'Q4_3_B1B_CONSECUTIVE_STATE_R1','mode':mode,'date':dates[0],'initial_soc_kWh':6000.,'q3_release_id':rel['release_id']})
    meta_path=OUT/f'{branch}_stage_solver_metadata_R2.jsonl'
    if meta_path.exists(): meta_path.unlink()
    maxdiff={k:0.0 for k in ['total_cost_yuan','base_cost_yuan','adjustment_cost_yuan','emergency_cost_yuan','emergency_energy_kwh','terminal_soc_kwh']}
    fallback=[]; hard_fail=0; started=time.perf_counter()
    with meta_path.open('w',encoding='utf-8') as f:
        for ix,day in enumerate(dates):
            pts={h:provider.q4_3_stage(day,h,mode=mode) for h in (0,6,12,18)}
            settlement=[float(x.settlement_price) for x in provider.q4_3_stage(day,0,mode=mode)]
            run=solve_q4_day(date=day,load_forecast_provider=loads[day],pv_vintage_provider=schedules[day],initial_soc=soc,actual_rows=actuals[day],
                             price_points_by_stage=pts,settlement_prices=settlement,config=cfg,initial_state_hash=state,planner=make_formal_lp_planner(cfg),mode=mode)
            val=validate_q4_day(run)
            if val['status']!='PASS': hard_fail+=1
            m=val['metrics']; rr=ref.loc[day]
            for k in maxdiff: maxdiff[k]=max(maxdiff[k],abs(float(m[k])-float(rr[k])))
            for c in run['stage_calls']:
                sm=c['solver_metadata']
                rec={'date':day,'mode':mode,'stage':c['stage'],'solver_status':c['solver_status'],'runtime_seconds':c['runtime_seconds'],
                     'solver_metadata':sm,'planner_validation':c['planner_validation']}
                f.write(json.dumps(rec,ensure_ascii=False,default=str)+'\n')
                if int(sm.get('fallback_count',0))>0:
                    fallback.append({'date':day,'stage':c['stage'],'tie_break_status':sm.get('tie_break_status'),'economic_objective_yuan':sm.get('economic_objective_yuan'),'throughput_optimum_kwh':sm.get('throughput_optimum_kwh')})
            soc=float(m['terminal_soc_kwh']); state=run['final_state_hash']
            if (ix+1)%50==0 or ix==0 or ix+1==len(dates): print(mode,ix+1,day,flush=True)
    rep={'schema':'Q4_3_STAGE_METADATA_REPLAY_R2','mode':mode,'days':len(dates),'stages':len(dates)*4,'hard_failures':hard_fail,
         'max_abs_diff_vs_R1_daily':maxdiff,'fallback_events':fallback,'elapsed_seconds':time.perf_counter()-started,
         'verdict':'PASS' if hard_fail==0 and max(maxdiff.values())<=1e-7 else 'FAIL'}
    write_json(OUT/f'{branch}_stage_metadata_replay_report_R2.json',rep)
    print(json.dumps(rep,indent=2))
    return 0 if rep['verdict']=='PASS' else 2

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['causal','oracle'],required=True);a=ap.parse_args()
    raise SystemExit(run('CAUSAL_LAG7' if a.mode=='causal' else 'ORACLE_DIAGNOSTIC'))
