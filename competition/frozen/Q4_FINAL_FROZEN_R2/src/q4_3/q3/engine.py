"""Unified Q3 rolling event loop with synthetic and injected FORMAL_LP planners."""
from copy import deepcopy
from datetime import timedelta
from time import perf_counter
from .common import digest,numeric,instant,start
from .ledger import Ledger


def _formal_release_mode(config):
    release = config.get('formal_release')
    if not isinstance(release, dict):
        raise ValueError('FORMAL_RELEASE_HOLD: missing release envelope')
    status = release.get('status')
    if status not in ('UNIT_TEST_ONLY', 'RELEASED'):
        raise ValueError('FORMAL_RELEASE_HOLD: Controller RELEASE required')
    if not release.get('authority') or not release.get('source_hash'):
        raise ValueError('FORMAL_RELEASE_HOLD: incomplete release provenance')
    return status


def solve_q3_day(date,load_forecast_provider,pv_vintage_provider,update_stages,initial_soc,
                 actual_rows,prices,config,initial_state_hash,*,planner):
    run_class=config.get('run_class')
    if run_class not in ('SYNTHETIC','FORMAL'):
        raise ValueError('HOLD_SPEC_AND_INPUT: unsupported run class')
    formal_mode=None
    if run_class=='SYNTHETIC':
        if update_stages not in ([0],[0,6],[0,6,12],[0,6,12,18]):raise ValueError('INVALID_STAGE_SUBSET')
        if config.get('storage_execution_policy')!='FIXED_REFERENCE_SAFETY' or config.get('planning_horizon')!='DAY_END':raise ValueError('UNSUPPORTED_SYNTHETIC_BINDING')
        if config.get('price_time_mode')!='DELIVERY_SLOT_PRICE' or config.get('actual_timing')!='AT_ENDPOINT_SYNTHETIC_REACTIVE':raise ValueError('UNSUPPORTED_SYNTHETIC_BINDING')
        if config.get('source_split_mode') not in ('GRID_FIRST','PV_FIRST'):raise ValueError('UNRESOLVED_SURPLUS')
    else:
        formal_mode=_formal_release_mode(config)
        expected=[0] if config.get('strategy_id')=='B0' else [0,6,12,18] if config.get('strategy_id') in ('B1A','B1B') else [0,6,12] if config.get('strategy_id')=='B1B_NO18' else None
        if expected is None or update_stages!=expected or config.get('update_stages')!=expected:raise ValueError('FORMAL_STRATEGY_STAGE_MISMATCH')
        if config.get('storage_execution_policy')!='STAGE_REFERENCE_SAFETY_OVERRIDE_V1':raise ValueError('FORMAL_POLICY_MISMATCH')
        if config.get('planning_horizon')!='CURRENT_DAY_REMAINDER':raise ValueError('FORMAL_HORIZON_MISMATCH')
        if config.get('price_time_mode')!='DELIVERY_SLOT_PRICE' or config.get('actual_timing')!='AT_ENDPOINT_CURRENT_SLOT_ACTUAL':raise ValueError('FORMAL_TIMING_MISMATCH')
        if config.get('source_split_mode')!='GRID_FIRST' or config.get('beta')!=-0.5:raise ValueError('FORMAL_ACCOUNTING_MISMATCH')
        if config.get('terminal_contract')!='FREE_BOUNDED_YEAR_END':raise ValueError('FORMAL_TERMINAL_MISMATCH')
    actual_rows=deepcopy(actual_rows)
    prices=deepcopy(prices)
    if len(prices)!=144:raise ValueError('PRICE_SLOTS')
    for p in prices:numeric(p,1e-300)
    eta_c=numeric(config['eta_c'],1e-12,1.);eta_d=numeric(config['eta_d'],1e-12,1.)
    e=numeric(initial_soc,1200.,10800.)
    if not initial_state_hash:raise ValueError('MISSING_STATE_PROVENANCE')
    if [r.get('slot_id') for r in actual_rows]!=list(range(1,145)):raise ValueError('ACTUAL_SLOT_IDENTITY')
    load=deepcopy(load_forecast_provider)
    if len(load['values'])!=144:raise ValueError('LOAD_INPUT_NOT_READY')
    if instant(load['known_at'])>start(date):raise ValueError('LOAD_LEAKAGE')
    for v in load['values']:numeric(v)
    used_pv={h:deepcopy(pv_vintage_provider[h]) for h in update_stages}
    for h,p in used_pv.items():
        if len(p['values'])!=144:raise ValueError('PV_INPUT_NOT_READY')
        if instant(p['known_at'])>start(date)+timedelta(hours=h):raise ValueError('PV_LEAKAGE')
        for v in p['values']:numeric(v)
    run_id=('SYNTHETIC_' if run_class=='SYNTHETIC' else 'FORMAL_')+digest([date,config,update_stages,initial_soc,initial_state_hash,load,used_pv[0],prices])[:16]
    ledger=Ledger(run_id,date,prices,config['beta'])
    trace=[];stage_calls=[];last_state=initial_state_hash;runtime=perf_counter();planner_max_violation=0.0
    for slot in range(1,145):
        h=(slot-1)//6
        if (slot-1)%36==0 and h in update_stages:
            ledger.executed_count=slot-1
            pv=used_pv[h];prefix_hash=digest(trace)
            dependency_known_at=max(instant(load['known_at']),instant(pv['known_at'])).isoformat()
            request=dict(date=date,stage=h,decision_time=(start(date)+timedelta(hours=h)).isoformat(),
                         future_slots=list(range(slot,145)),load_kwh=deepcopy(load['values']),
                         pv_kwh=deepcopy(pv['values']),prices=deepcopy(prices),initial_soc=e,
                         previous_active=ledger.active,executed_prefix_hash=prefix_hash,
                         forecast_id=pv['forecast_id'],load_forecast_id=load['forecast_id'],
                         dependency_known_at=dependency_known_at)
            begin=perf_counter();raw=planner(deepcopy(request));elapsed=perf_counter()-begin
            if isinstance(raw,list):
                if run_class!='SYNTHETIC':raise ValueError('FORMAL_PLANNER_PROTOCOL')
                reference=raw;planner_kind='INJECTED_MOCK_NOT_LP';solver_status='NOT_APPLICABLE_MOCK';solver_metadata=None;validation=None
            elif isinstance(raw,dict):
                reference=raw.get('plan');planner_kind=raw.get('planner_kind');solver_metadata=deepcopy(raw.get('solver_metadata'))
                validation=deepcopy(raw.get('validation'));solver_status=(solver_metadata or {}).get('status')
                if run_class!='FORMAL' or planner_kind!='FORMAL_LP':raise ValueError('FORMAL_PLANNER_PROTOCOL')
                if solver_status!='OPTIMAL' or not isinstance(validation,dict) or validation.get('status')!='PASS':raise ValueError('FORMAL_PLANNER_FAIL_CLOSED')
                violation=float(validation.get('max_violation',float('inf')))
                if violation>float(config.get('hard_tolerance',1e-7)):raise ValueError('FORMAL_PLANNER_HARD_VIOLATION')
                planner_max_violation=max(planner_max_violation,violation)
            else:raise ValueError('PLANNER_PROTOCOL')
            event=ledger.commit(f'{run_id}:{date}:{h:02d}',h,reference,ledger.state_hash,pv['forecast_id'],load['forecast_id'],known_at_max=dependency_known_at)
            stage_calls.append(dict(stage=h,initial_soc=e,parent_state_hash=last_state,
                                    executed_prefix_hash=prefix_hash,request=request,
                                    event_id=event['event_id'],planner_kind=planner_kind,
                                    solver_status=solver_status,runtime_seconds=elapsed,
                                    solver_metadata=solver_metadata,planner_validation=validation))
            if digest(trace)!=prefix_hash:raise ValueError('PAST_MUTATED')
        active=ledger.active[slot];actual=actual_rows[slot-1]
        end=start(date)+timedelta(minutes=10*slot)
        if instant(actual['actual_available_at'])!=end:raise ValueError('ACTUAL_TIMING_MISMATCH')
        load_actual=numeric(actual['load_kwh']);pv_actual=numeric(actual['pv_kwh'])
        q=active['q'];balance=q+pv_actual-load_actual
        if balance>=0:
            c=min(active['c_ref'],balance,5000/6,max((10800-e)/eta_c,0.));d=0.
        else:
            c=0.;d=min(active['d_ref'],-balance,5000/6,max(eta_d*(e-1200),0.))
        emergency=max(load_actual+c-q-pv_actual-d,0.)
        unused=max(q+pv_actual+d-load_actual-c,0.)
        if config['source_split_mode']=='GRID_FIRST':w=min(q,unused);v=unused-w
        else:v=min(pv_actual,unused);w=unused-v
        next_e=e+eta_c*c-d/eta_d
        row=dict(run_id=run_id,date=date,slot_id=slot,delivery_start=(end-timedelta(minutes=10)).isoformat(),
                 delivery_end=end.isoformat(),active_commitment_event_id=active['event_id'],
                 q=q,actual_L=load_actual,actual_S=pv_actual,actual_available_at=end.isoformat(),
                 action_decision_time=end.isoformat(),c_ref=active['c_ref'],d_ref=active['d_ref'],
                 c=c,d=d,e_before=e,e_after=next_e,r=emergency,w=w,v=v,
                 price=prices[slot-1],cost_emergency=5*prices[slot-1]*emergency,
                 source_split_mode=config['source_split_mode'],override_c=active['c_ref']-c,
                 override_d=active['d_ref']-d,fallback_reason=None,parent_state_hash=last_state)
        last_state=digest(row);trace.append(row);e=next_e
    if run_class=='SYNTHETIC':scope='SYNTHETIC_ONLY_NOT_SCREENING';formal_result=False
    elif formal_mode=='UNIT_TEST_ONLY':scope='FORMAL_UNIT_TEST_ONLY';formal_result=False
    else:scope='FORMAL_SCREENING';formal_result=True
    return dict(scope=scope,run_id=run_id,date=date,config=deepcopy(config),
                update_stages=update_stages.copy(),initial_soc=initial_soc,initial_state_hash=initial_state_hash,
                final_soc=e,final_state_hash=last_state,events=ledger.events,trace=trace,stage_calls=stage_calls,
                source_inputs=dict(load_forecast=load,pv_forecasts=used_pv,prices=prices,actual_rows=actual_rows),
                runtime_seconds=perf_counter()-runtime,formal_result=formal_result,
                max_planner_hard_violation=planner_max_violation)
