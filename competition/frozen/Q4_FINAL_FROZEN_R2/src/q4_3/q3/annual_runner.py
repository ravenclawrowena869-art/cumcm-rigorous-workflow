from __future__ import annotations

import csv, json, hashlib, time
from datetime import date, timedelta
from pathlib import Path

from .common import digest, start
from .data import load_actuals, load_tariff, load_vintages
from .formal_lp import make_formal_lp_planner
from .interpolation import PREVIOUS_LEGAL_VINTAGE, POINT_POWER, interpolate
from .annual_validator import validate_formal_run
from .engine import solve_q3_day


def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024), b''): h.update(c)
    return h.hexdigest()


def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))

def write_json(p, x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def write_csv(p, rows, fields):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,'') for k in fields})


def load_frozen_load(path: Path):
    with path.open('r',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)!=48096: raise ValueError(f'FORMAL334_LOAD_ROWCOUNT:{len(rows)}')
    g={}
    for r in rows: g.setdefault(r['source_date'],[]).append(r)
    if len(g)!=334: raise ValueError(f'FORMAL334_LOAD_DAYCOUNT:{len(g)}')
    out={}
    for day, rr in g.items():
        rr=sorted(rr,key=lambda x:int(x['source_slot']))
        if [int(x['source_slot']) for x in rr]!=list(range(1,145)): raise ValueError(f'FORMAL334_LOAD_SLOTS:{day}')
        known={x['known_at'] for x in rr}; models={x['model_id'] for x in rr}; versions={x['forecast_version'] for x in rr}
        if len(known)!=1 or len(models)!=1 or len(versions)!=1: raise ValueError(f'FORMAL334_LOAD_METADATA:{day}')
        out[day]={'forecast_id':f'{next(iter(models))}:{next(iter(versions))}:{day}', 'known_at':next(iter(known)), 'values':[float(x['load_forecast_kw'])/6.0 for x in rr]}
    return out


def verify_outer_release(r54_root: Path):
    release=load_json(r54_root/'Q3_FORMAL334_RELEASE_R5_4.json')
    if release.get('status')!='RELEASED' or not release.get('formal_334d_authorized'): raise ValueError('FORMAL334_RELEASE_NOT_GRANTED')
    if release.get('scope')!='FORMAL_334D_BASELINE_B0_B1A_ONLY': raise ValueError('FORMAL334_SCOPE_MISMATCH')
    if release.get('b1b_authorized') or release.get('winner_declaration_authorized') or release.get('q3_freeze_authorized'): raise ValueError('FORMAL334_SCOPE_OVERBROAD')
    mapping={
      'Q2_TO_Q3_FROZEN_HANDOFF_R1.zip': r54_root/'inputs/Q2_TO_Q3_FROZEN_HANDOFF_R1(1).zip',
      'Q3_FYQ_R5_2_FORMAL14_TASK.zip': r54_root/'inputs/Q3_FYQ_R5_2_FORMAL14_TASK.zip',
      'FYQ_FORMAL14_RETURN_R5_2.zip': r54_root/'inputs/f7d40af7-865f-4f12-a70f-869e7feb3dcf.zip',
      'Q3_XXT_R5_3_FORMAL14_GATE_DELIVERY_FINAL.zip': r54_root/'inputs/Q3_XXT_R5_3_FORMAL14_GATE_DELIVERY_FINAL.zip'}
    rows=[]
    for name, exp in release['required_inputs_sha256'].items():
        p=mapping[name]; got=sha256_file(p) if p.is_file() else None
        rows.append({'name':name,'path':str(p.relative_to(r54_root)),'expected_sha256':exp,'actual_sha256':got,'status':'MATCH' if got==exp else 'MISMATCH'})
    if any(r['status']!='MATCH' for r in rows): raise ValueError('FORMAL334_INPUT_PIN_MISMATCH')
    return release, {'schema':'Q3_FORMAL334_RELEASE_PIN_AUDIT_R5_4_V1','status':'PASS','pins':rows,'release_sha256':sha256_file(r54_root/'Q3_FORMAL334_RELEASE_R5_4.json')}


def date_range(start_s='2025-02-01', end_s='2025-12-31'):
    y,m,d=map(int,start_s.split('-')); a=date(y,m,d); y,m,d=map(int,end_s.split('-')); b=date(y,m,d)
    out=[]
    while a<=b: out.append(a.isoformat()); a+=timedelta(days=1)
    return out


def stage_pv(vintage_by_issue, day, stage, prefix):
    from datetime import timedelta
    decision=start(day)+timedelta(hours=stage)
    cur=vintage_by_issue.get(decision.isoformat()); prev=vintage_by_issue.get((decision-timedelta(hours=6)).isoformat())
    if cur is None or prev is None: raise ValueError(f'FORMAL334_PV_VINTAGE_MISSING:{day}:{stage}')
    first=stage*6+1
    targets=[(start(day)+timedelta(minutes=10*slot)).isoformat() for slot in range(first,145)]
    it=interpolate(cur,targets,decision.isoformat(),boundary_mode=PREVIOUS_LEGAL_VINTAGE,quantity_semantics=POINT_POWER,previous_vintage=prev)
    values=list(prefix)+[float(r['pv_kwh']) for r in it]
    if len(values)!=144: raise ValueError(f'FORMAL334_PV_LENGTH:{day}:{stage}')
    known=max(r['known_at'] for r in it)
    if known!=decision.isoformat(): raise ValueError(f'FORMAL334_PV_KNOWN_AT:{day}:{stage}')
    return {'forecast_id':cur['vintage_id'],'known_at':known,'values':values,'interpolation':'PV_HOURLY_LINEAR_CAUSAL_BOUNDARY_V1','boundary_mode':'PREVIOUS_LEGAL_VINTAGE_AT_STAGE_HOUR'}


def build_day_shared(ctx, day):
    load=ctx['loads'].get(day); actual=ctx['actuals'].get(day)
    if load is None or actual is None: raise ValueError(f'FORMAL334_DAY_INPUT_MISSING:{day}')
    pv={}; prefix=[]
    for st in (0,6,12,18):
        p=stage_pv(ctx['vintage_by_issue'],day,st,prefix); pv[st]=p; prefix=p['values'][:(st+6)*6]
    return {'date':day,'load':load,'actual_rows':actual,'prices':ctx['prices'],'pv_by_stage':pv}


def release_envelope(ctx):
    rel=ctx['release']; return {'status':'RELEASED','authority':rel['authority'],'source_hash':ctx['pin_audit']['release_sha256'],'release_id':rel['release_id'],'scope':rel['scope']}


def run_one(ctx, shared, strategy, initial_soc, initial_state_hash):
    cfg=dict(ctx['configs'][strategy]); cfg['formal_release']=release_envelope(ctx)
    stages=[0] if strategy=='B0' else [0,6,12,18]
    pv={0:shared['pv_by_stage'][0]} if strategy=='B0' else dict(shared['pv_by_stage'])
    run=solve_q3_day(date=shared['date'],load_forecast_provider=shared['load'],pv_vintage_provider=pv,update_stages=stages,initial_soc=float(initial_soc),actual_rows=shared['actual_rows'],prices=shared['prices'],config=cfg,initial_state_hash=initial_state_hash,planner=make_formal_lp_planner(cfg))
    v=validate_formal_run(run)
    if v['status']!='PASS': raise RuntimeError(f"FORMAL334_DAY_VALIDATION_FAIL:{shared['date']}:{strategy}")
    return run,v


def run_annual(ctx, out_dir: Path, *, max_days=None):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    dates=date_range(ctx['release']['date_range']['start'],ctx['release']['date_range']['end'])
    if max_days is not None: dates=dates[:int(max_days)]
    if max_days is None and len(dates)!=334: raise ValueError('FORMAL334_DATE_COUNT')
    states={'B0':6000.0,'B1A':6000.0}
    last_terminal={'B0':None,'B1A':None}
    state_hashes={s:digest({'protocol':'Q3_FORMAL334_CONSECUTIVE_STATE_R5_4','strategy':s,'date':dates[0],'initial_soc_kWh':6000.0,'release_id':ctx['release']['release_id']}) for s in states}
    trace_rows=[]; ledger_rows=[]; solver_runs=[]; val_summ=[]; daily=[]; provenance=[]; continuity=[]
    started=time.perf_counter()
    for i,day in enumerate(dates):
        shared=build_day_shared(ctx,day)
        day_runs={}
        for strategy in ('B0','B1A'):
            init=float(states[strategy]); init_hash=state_hashes[strategy]
            run,val=run_one(ctx,shared,strategy,init,init_hash)
            m=val['metrics']; day_runs[strategy]=(run,val,m)
            expected_initial=6000.0 if last_terminal[strategy] is None else float(last_terminal[strategy])
            continuation_residual=abs(init-expected_initial)
            continuity.append({'date':day,'strategy':strategy,'initial_soc_kwh':init,'previous_terminal_soc_kwh':expected_initial,'terminal_soc_kwh':float(m['terminal_soc_kwh']),'initial_state_hash':init_hash,'final_state_hash':run['final_state_hash'],'continuity_residual_kwh':continuation_residual})
            states[strategy]=float(m['terminal_soc_kwh']); last_terminal[strategy]=states[strategy]; state_hashes[strategy]=run['final_state_hash']
            for r in run['trace']: trace_rows.append({'date':day,'strategy':strategy,**r})
            for ev in run['events']:
                for r in ev['rows']: ledger_rows.append({'date':day,'strategy':strategy,'event_id':ev['event_id'],**r})
            for call in run['stage_calls']:
                solver_runs.append({'date':day,'strategy':strategy,'stage':call['stage'],'planner_kind':call['planner_kind'],'solver_status':call['solver_status'],'runtime_seconds':call['runtime_seconds'],'event_id':call['event_id'],'executed_prefix_hash':call['executed_prefix_hash'],'solver_metadata':call['solver_metadata'],'planner_validation':call['planner_validation']})
            val_summ.append({'date':day,'strategy':strategy,'status':val['status'],'failure_count':val['failure_count'],**m})
            provenance.append({'date':day,'strategy':strategy,'run_id':run['run_id'],'initial_state_hash':run['initial_state_hash'],'final_state_hash':run['final_state_hash'],'load_hash':digest(run['source_inputs']['load_forecast']),'pv_hash':digest(run['source_inputs']['pv_forecasts']),'actual_hash':digest(run['source_inputs']['actual_rows']),'prices_hash':digest(run['source_inputs']['prices']),'shared_contract_sha256':run['config']['shared_contract_sha256'],'formal_result':run['formal_result']})
        b0=day_runs['B0'][2]; b1=day_runs['B1A'][2]
        daily.append({'date':day,'B0_total_cost':b0['total_cost_yuan'],'B1A_total_cost':b1['total_cost_yuan'],'delta_B1A_minus_B0':b1['total_cost_yuan']-b0['total_cost_yuan'],'B0_emergency_kwh':b0['emergency_energy_kwh'],'B1A_emergency_kwh':b1['emergency_energy_kwh'],'B0_initial_soc':day_runs['B0'][0]['initial_soc'],'B0_terminal_soc':b0['terminal_soc_kwh'],'B1A_initial_soc':day_runs['B1A'][0]['initial_soc'],'B1A_terminal_soc':b1['terminal_soc_kwh'],'hard_violation_count_B0':day_runs['B0'][1]['failure_count'],'hard_violation_count_B1A':day_runs['B1A'][1]['failure_count'],'B0_adjustment_cost':b0['adjustment_cost_yuan'],'B1A_adjustment_cost':b1['adjustment_cost_yuan'],'B0_emergency_cost':b0['emergency_cost_yuan'],'B1A_emergency_cost':b1['emergency_cost_yuan']})
        if (i+1)%25==0 or i==0 or i+1==len(dates): print(f'PROGRESS {i+1}/{len(dates)} {day} B0_SOC={states["B0"]:.3f} B1A_SOC={states["B1A"]:.3f}', flush=True)

    trace_fields=list(trace_rows[0].keys()); ledger_fields=list(ledger_rows[0].keys()); daily_fields=list(daily[0].keys()); cont_fields=list(continuity[0].keys())
    write_csv(out/'per_slot_trace.csv',trace_rows,trace_fields); write_csv(out/'stage_ledger.csv',ledger_rows,ledger_fields); write_csv(out/'paired_daily_summary.csv',daily,daily_fields); write_csv(out/'soc_continuity_report.csv',continuity,cont_fields)
    monthly=[]
    for month in range(2,13):
        rr=[r for r in daily if int(r['date'][5:7])==month]
        monthly.append({'month':month,'day_count':len(rr),'B0_total_cost':sum(r['B0_total_cost'] for r in rr),'B1A_total_cost':sum(r['B1A_total_cost'] for r in rr),'delta_B1A_minus_B0':sum(r['delta_B1A_minus_B0'] for r in rr),'B0_emergency_kwh':sum(r['B0_emergency_kwh'] for r in rr),'B1A_emergency_kwh':sum(r['B1A_emergency_kwh'] for r in rr),'B1A_better_days':sum(r['delta_B1A_minus_B0']<0 for r in rr),'B1A_worse_days':sum(r['delta_B1A_minus_B0']>0 for r in rr)})
    write_csv(out/'monthly_summary.csv',monthly,list(monthly[0].keys()))
    write_json(out/'solver_metadata.json',{'schema':'Q3_FORMAL334_SOLVER_METADATA_R5_4_V1','runs':solver_runs})
    write_json(out/'validator_report.json',{'schema':'Q3_FORMAL334_VALIDATOR_SUMMARY_R5_4_V1','status':'PASS' if all(r['status']=='PASS' for r in val_summ) else 'FAIL','runs':val_summ})
    write_json(out/'input_provenance.json',{'schema':'Q3_FORMAL334_INPUT_PROVENANCE_R5_4_V1','runs':provenance})
    write_json(out/'config_snapshot.json',{'schema':'Q3_FORMAL334_CONFIG_R5_4_V1','release':ctx['release'],'configs':ctx['configs']})
    max_cont=max((abs(float(r['continuity_residual_kwh'])) for r in continuity),default=0.0)
    max_hard=max((float(r['hard_violation_max']) for r in val_summ),default=0.0)
    max_known=max((float(r['known_at_violation_seconds']) for r in val_summ),default=0.0)
    past=sum(int(r['past_mutation_count']) for r in val_summ); fallback=sum(int(r['fallback_count']) for r in val_summ)
    b0_intraday=max((abs(float(r['intraday_adjustment_kwh'])) for r in val_summ if r['strategy']=='B0'),default=0.0)
    acc={'schema':'Q3_FORMAL334_ACCEPTANCE_R5_4_V1','checks':{'day_count_expected':len(dates)==(334 if max_days is None else int(max_days)),'all_day_validators_pass':all(r['status']=='PASS' for r in val_summ),'cross_day_soc_continuity':max_cont<=1e-7,'known_at_zero':max_known==0.0,'past_mutations_zero':past==0,'fallback_zero':fallback==0,'b0_intraday_adjustment_zero':b0_intraday==0.0,'max_hard_residual_within_1e_7':max_hard<=1e-7,'year_end_soc_in_bounds':all(1200<=states[s]<=10800 for s in states)},'metrics':{'days':len(dates),'strategy_runs':len(val_summ),'trace_rows':len(trace_rows),'stage_ledger_rows':len(ledger_rows),'solver_stage_calls':len(solver_runs),'max_cross_day_soc_residual_kwh':max_cont,'max_hard_residual':max_hard,'max_known_at_violation_seconds':max_known,'past_mutation_count':past,'fallback_count':fallback,'max_b0_intraday_adjustment_kwh':b0_intraday,'B0_year_end_soc_kwh':states['B0'],'B1A_year_end_soc_kwh':states['B1A']}}
    acc['status']='PASS_FOR_XXT_REVIEW' if all(acc['checks'].values()) else 'FAIL_FORMAL334_ACCEPTANCE'; write_json(out/'acceptance_report.json',acc)
    total_b0=sum(r['B0_total_cost'] for r in daily); total_b1=sum(r['B1A_total_cost'] for r in daily); delta=total_b1-total_b0
    summary={'schema':'Q3_FORMAL334_FINAL_STATUS_R5_4_V1','PRIMARY':acc['status'],'formal_334d_executed':max_days is None,'days_executed':len(dates),'B0_total_cost_yuan':total_b0,'B1A_total_cost_yuan':total_b1,'delta_B1A_minus_B0_yuan':delta,'B0_emergency_kwh':sum(r['B0_emergency_kwh'] for r in daily),'B1A_emergency_kwh':sum(r['B1A_emergency_kwh'] for r in daily),'B1A_better_days':sum(r['delta_B1A_minus_B0']<0 for r in daily),'B1A_worse_days':sum(r['delta_B1A_minus_B0']>0 for r in daily),'B1A_equal_days':sum(abs(r['delta_B1A_minus_B0'])<=1e-12 for r in daily),'B0_year_end_soc_kwh':states['B0'],'B1A_year_end_soc_kwh':states['B1A'],'b1b_executed':False,'winner_declared':False,'q3_freeze_declared':False,'elapsed_seconds':time.perf_counter()-started,'next_gate':'XXT_CONTROLLER_ANNUAL_BASELINE_AUDIT_AND_B1B_RELEASE'}; write_json(out/'FINAL_STATUS.json',summary)
    write_json(out/'year_end_state.json',{'B0':{'terminal_soc_kwh':states['B0'],'final_state_hash':state_hashes['B0']},'B1A':{'terminal_soc_kwh':states['B1A'],'final_state_hash':state_hashes['B1A']}})
    write_json(out/'checkpoint.json',{'status':'COMPLETE','last_date':dates[-1],'days_completed':len(dates),'state':states,'state_hashes':state_hashes})
    write_json(out/'MANIFEST.json',{'schema':'Q3_FORMAL334_RESULT_MANIFEST_R5_4_V1','status':acc['status'],'formal_334d':max_days is None,'b1b':False,'winner':None,'freeze':False,'release_pin_audit_status':ctx['pin_audit']['status']})
    return summary


def build_context(r54_root: Path, r52_root: Path):
    release,pin=verify_outer_release(r54_root)
    impl=r52_root/'Q3_FYQ_R5_IMPLEMENTATION'
    loads=load_frozen_load(r52_root/'authority_inputs/Q3_FROZEN_LOAD_FORECAST_R1.csv')
    actuals=load_actuals(impl/'inputs/attachment2.xlsx')
    prices=[r['price_yuan_per_kwh'] for r in load_tariff(impl/'inputs/attachment1.xlsx')]
    vint=load_vintages(impl/'inputs/attachment3.xlsx'); vb={r['issue_time']:r for r in vint}
    configs={'B0':load_json(r52_root/'config/formal_b0.json'),'B1A':load_json(r52_root/'config/formal_b1a.json')}
    return {'r54_root':r54_root,'r52_root':r52_root,'release':release,'pin_audit':pin,'loads':loads,'actuals':actuals,'prices':prices,'vintage_by_issue':vb,'configs':configs}
