from run_q4_3 import *
import argparse, shutil

def run_chunk(mode, loads, actuals, schedules, provider, cfg, rel, chunk_days, reset=False):
    od=OUT/'results'/('causal' if mode=='CAUSAL_LAG7' else 'oracle'); od.mkdir(parents=True,exist_ok=True)
    cp_path=od/'checkpoint.json'
    if reset:
        for p in od.glob('*'):
            if p.is_file(): p.unlink()
    dates=date_range('2025-02-01','2025-12-31')
    cp=jload(cp_path) if cp_path.exists() else None
    idx=int(cp['days_completed']) if cp else 0
    if idx>=len(dates): print('ALREADY_COMPLETE',mode); return
    stop=min(idx+chunk_days,len(dates))
    if cp:
        soc=float(cp['soc_kwh']); state=cp['state_hash']
    else:
        soc=6000.; state=digest({'protocol':'Q4_3_B1B_CONSECUTIVE_STATE_R1','mode':mode,'date':dates[0],'initial_soc_kWh':6000.,'q3_release_id':rel['release_id']})
    TRACE_FIELDS=['date','mode','slot_id','q','actual_L','actual_S','c_ref','d_ref','c','d','e_before','e_after','r','w','v','settlement_price','active_decision_price','cost_emergency_settlement','active_commitment_event_id']
    LEDGER_FIELDS=['date','mode','event_id','stage','slot_id','base_q','previous_active_q','new_active_q','delta_plus','delta_minus','decision_price','settlement_price','decision_fee_delta','settlement_fee_delta','price_known_at','price_source','price_mode','c_ref','d_ref','issue_time','known_at_max','forecast_vintage_id','load_forecast_id']
    DAILY_FIELDS=['date','mode','base_cost_yuan','adjustment_cost_yuan','emergency_cost_yuan','total_cost_yuan','emergency_energy_kwh','terminal_soc_kwh','soc_min_kwh','soc_max_kwh','throughput_kwh','price_future_realized_leak_count','planner_max_violation','solver_runtime_seconds','initial_soc_kwh','hard_failure_count','max_hard_violation']
    PRICE_FIELDS=['date','stage','slot','decision_time','decision_price','settlement_price','known_at','source','mode']
    begun=time.perf_counter()
    for ix in range(idx,stop):
        day=dates[ix]; initial=soc
        pts={h:provider.q4_3_stage(day,h,mode=mode) for h in (0,6,12,18)}
        settlement=[float(x.settlement_price) for x in provider.q4_3_stage(day,0,mode=mode)]
        run=solve_q4_day(date=day,load_forecast_provider=loads[day],pv_vintage_provider=schedules[day],initial_soc=soc,actual_rows=actuals[day],
                         price_points_by_stage=pts,settlement_prices=settlement,config=cfg,initial_state_hash=state,planner=make_formal_lp_planner(cfg),mode=mode)
        val=validate_q4_day(run)
        recoveries=[]
        for c in run['stage_calls']:
            sm=c.get('solver_metadata') or {}
            if int(sm.get('fallback_count',0))>0 or int(sm.get('numerical_recovery_count',0))>0:
                recoveries.append({'date':day,'mode':mode,'stage':c['stage'],'fallback_count':int(sm.get('fallback_count',0)),'numerical_recovery_count':int(sm.get('numerical_recovery_count',0)),'tie_break_status':sm.get('tie_break_status'),'policy':sm.get('numerical_recovery_policy')})
        if recoveries:
            append_csv(od/'numerical_recovery.csv',recoveries,['date','mode','stage','fallback_count','numerical_recovery_count','tie_break_status','policy'])
        if val['status']!='PASS':
            write_json(od/'FAILED_DAY.json',{'date':day,'validator':val}); raise RuntimeError(f'Q4_DAY_FAIL:{mode}:{day}')
        m=val['metrics']
        with (od/'stage_solver_metadata.jsonl').open('a',encoding='utf-8') as f:
            for c in run['stage_calls']:
                f.write(json.dumps({'date':day,'mode':mode,'stage':c['stage'],'solver_status':c['solver_status'],'runtime_seconds':c['runtime_seconds'],'solver_metadata':c['solver_metadata'],'planner_validation':c['planner_validation']},ensure_ascii=False,default=str)+'\n')
        append_csv(od/'trace.csv',[{'date':day,'mode':mode,**r} for r in run['trace']],TRACE_FIELDS)
        lrows=[]
        for e in run['events']:
            for r in e['rows']:lrows.append({'date':day,'mode':mode,'event_id':e['event_id'],**r})
        append_csv(od/'stage_ledger.csv',lrows,LEDGER_FIELDS)
        prows=[]
        for h in (0,6,12,18):
            for x in pts[h]:prows.append({'date':day,'stage':h,'slot':x.slot,'decision_time':x.decision_time,'decision_price':x.decision_price,'settlement_price':x.settlement_price,'known_at':x.known_at,'source':x.source,'mode':mode})
        append_csv(od/'price_audit.csv',prows,PRICE_FIELDS)
        append_csv(od/'daily.csv',[{'date':day,'mode':mode,**m,'initial_soc_kwh':initial,'hard_failure_count':0,'max_hard_violation':val['max_hard_violation']}],DAILY_FIELDS)
        soc=float(m['terminal_soc_kwh']); state=run['final_state_hash']
        write_json(cp_path,{'status':'COMPLETE' if ix+1==len(dates) else 'IN_PROGRESS','days_completed':ix+1,'last_date':day,'soc_kwh':soc,'state_hash':state,'mode':mode})
        if (ix+1)%25==0 or ix==idx or ix+1==stop: print(f'{mode} {ix+1}/{len(dates)} {day} cost={m["total_cost_yuan"]:.2f} soc={soc:.2f}',flush=True)
    print(json.dumps({'status':'CHUNK_COMPLETE','mode':mode,'from':idx+1,'to':stop,'elapsed':time.perf_counter()-begun}))
    if stop==len(dates):
        df=pd.read_csv(od/'daily.csv')
        annual={k:float(df[k].sum()) for k in ['base_cost_yuan','adjustment_cost_yuan','emergency_cost_yuan','total_cost_yuan','emergency_energy_kwh','throughput_kwh','solver_runtime_seconds']}
        annual.update({'mode':mode,'days':len(df),'initial_soc_kwh':6000.,'terminal_soc_kwh':float(df.iloc[-1].terminal_soc_kwh),
                       'soc_min_kwh':float(df.soc_min_kwh.min()),'soc_max_kwh':float(df.soc_max_kwh.max()),
                       'price_future_realized_leak_count':int(df.price_future_realized_leak_count.sum()),'hard_failure_count':int(df.hard_failure_count.sum()),
                       'oracle_diagnostic_only':mode!='CAUSAL_LAG7'})
        write_json(od/'annual.json',annual)
        write_json(od/'validator.json',{'status':'PASS','days':len(df),'hard_failure_count':annual['hard_failure_count'],'price_future_realized_leak_count':annual['price_future_realized_leak_count'],'max_daily_hard_violation':float(df.max_hard_violation.max())})
        print('ANNUAL',json.dumps(annual))

def main2():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['causal','oracle'],required=True);ap.add_argument('--chunk-days',type=int,default=70);ap.add_argument('--reset',action='store_true');args=ap.parse_args()
    loads=derive_loads();adapter=check_load_adapter(loads);write_json(OUT/'reconstruction_load_adapter_check.json',adapter)
    if adapter['status']!='PASS':raise RuntimeError('LOAD_ADAPTER_MISMATCH')
    actuals=load_actuals(TASK/'03_INPUTS/attachment2.xlsx');vints=load_vintages(TASK/'03_INPUTS/attachment3.xlsx');vmap={x['issue_time']:x for x in vints};schedules,ll=build_schedules(actuals,vmap)
    if not (OUT/'lambda_ledger_all.csv').exists():pd.DataFrame(ll).to_csv(OUT/'lambda_ledger_all.csv',index=False)
    cfg,rel=q4_config();provider=Q4PriceProvider(TASK/'03_INPUTS/q4_price_lag7_feb_dec.csv',TASK/'03_INPUTS/q4_price_stage_vintages_lag7.csv')
    run_chunk('CAUSAL_LAG7' if args.mode=='causal' else 'ORACLE_DIAGNOSTIC',loads,actuals,schedules,provider,cfg,rel,args.chunk_days,args.reset)
if __name__=='__main__':main2()
