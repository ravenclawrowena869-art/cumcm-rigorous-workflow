"""Independent synthetic ledger/state replay. Never imports engine or ledger."""
from datetime import timedelta
import math
from .common import digest,start,instant

def validate(result):
    observations={};failures={};metrics={};date=result.get('date') if isinstance(result,dict) else None
    def record(name,violation=0.,slot=None,stage=None,detail=None,tol=1e-7):
        observations.setdefault(name,[]).append((violation,slot,stage))
        if not math.isfinite(violation) or violation>tol or detail:
            failures.setdefault(name,[]).append(dict(slot=slot,stage=stage,detail=detail,max_violation=violation if math.isfinite(violation) else None))
    def same(name,expected,actual,slot=None,stage=None):
        record(name,slot=slot,stage=stage,detail=None if expected==actual else dict(expected=expected,actual=actual))
    def finite(obj):
        if isinstance(obj,float) and not math.isfinite(obj):raise ValueError('NONFINITE')
        if isinstance(obj,dict):
            for v in obj.values():finite(v)
        if isinstance(obj,list):
            for v in obj:finite(v)
    try:
        finite(result)
        if result['scope']!='SYNTHETIC_ONLY_NOT_SCREENING':raise ValueError('AUTHORITY_UNRESOLVED')
        trace=result['trace'];events=result['events'];calls=result['stage_calls'];source=result['source_inputs'];cfg=result['config']
        same('V01_RUN_CLASS','SYNTHETIC',cfg.get('run_class'))
        same('V01_FORMAL_RESULT',False,result.get('formal_result'))
        same('V01_PLANNING_HORIZON','DAY_END',cfg.get('planning_horizon'))
        same('V01_ACTUAL_TIMING','AT_ENDPOINT_SYNTHETIC_REACTIVE',cfg.get('actual_timing'))
        same('V01_SOURCE_SPLIT_DOMAIN',True,cfg.get('source_split_mode') in ('GRID_FIRST','PV_FIRST'))
        prices=source.get('prices')
        if not isinstance(prices,list) or len(prices)!=144:raise ValueError('V16_SOURCE_PRICE_VECTOR')
        for slot,p in enumerate(prices,1):
            if type(p) not in (float,int) or not math.isfinite(p):raise ValueError('V16_SOURCE_PRICE_DOMAIN')
            record('V16_SOURCE_PRICE_DOMAIN',max(1e-300-float(p),0.0),slot=slot,tol=0)
        same('V02_SLOT_IDENTITY',list(range(1,145)),[r['slot_id'] for r in trace])
        same('V02_STAGE_IDENTITY',result['update_stages'],[e['stage'] for e in events])
        same('V02_STAGE_CALLS',result['update_stages'],[c['stage'] for c in calls])
        same('V02_ACTUAL_SOURCE_SLOTS',list(range(1,145)),[r['slot_id'] for r in source['actual_rows']])
        if len(trace)!=144 or len(source['actual_rows'])!=144 or not events:raise ValueError('INCOMPLETE_TRACE_OR_LEDGER')
        beta=cfg['beta'];eta_c=cfg['eta_c'];eta_d=cfg['eta_d']
        if beta not in (.5,-.5) or not 0<eta_c<=1 or not 0<eta_d<=1:raise ValueError('INVALID_SYNTHETIC_PARAMETERS')
        same('V16_PRICE_MODE','DELIVERY_SLOT_PRICE',cfg['price_time_mode'])
        same('V12_POLICY','FIXED_REFERENCE_SAFETY',cfg['storage_execution_policy'])
        active={};states_at_stage={};seen=set();base=0.;adj=0.;last_stage=-1
        for event in events:
            h=event['stage'];eid=event['event_id'];rows=event['rows']
            same('V06_EVENT_ID_UNIQUE',False,eid in seen,stage=h);seen.add(eid)
            same('V05_PARENT',digest(active),event['parent_commitment_hash'],stage=h)
            same('V03_STAGE_ORDER',True,h>last_stage and h in (0,6,12,18),stage=h);last_stage=h
            same('V03_FUTURE_SLOTS',list(range(h*6+1,145)),[r['slot_id'] for r in rows],stage=h)
            call=next(c for c in calls if c['stage']==h)
            decision=start(date)+timedelta(hours=h)
            same('V02_EVENT_RUN_ID',result['run_id'],event['run_id'],stage=h)
            same('V02_EVENT_DATE',date,event['date'],stage=h)
            same('V05_CALL_EVENT_ID',event['event_id'],call['event_id'],stage=h)
            same('V08_REQUEST_DATE',date,call['request'].get('date'),stage=h)
            same('V08_REQUEST_STAGE',h,call['request'].get('stage'),stage=h)
            same('V08_DECISION_TIME',decision.isoformat(),call['request']['decision_time'],stage=h)
            same('V03_PREFIX_HASH',digest(trace[:h*6]),call['executed_prefix_hash'],stage=h)
            state=result['initial_soc'] if not h else trace[h*6-1]['e_after']
            record('V14_STAGE_SOC',abs(state-call['initial_soc']),stage=h)
            record('V14_REQUEST_SOC',abs(state-call['request']['initial_soc']),stage=h)
            same('V14_STATE_PARENT',result['initial_state_hash'] if not h else digest(trace[h*6-1]),call['parent_state_hash'],stage=h)
            pv=source['pv_forecasts'].get(h,source['pv_forecasts'].get(str(h)))
            ld=source['load_forecast']
            same('V08_REQUEST_FORECAST_ID',pv['forecast_id'],call['request'].get('forecast_id'),stage=h)
            same('V08_REQUEST_LOAD_ID',ld['forecast_id'],call['request'].get('load_forecast_id'),stage=h)
            same('V08_LOAD_VECTOR',ld['values'],call['request']['load_kwh'],stage=h)
            same('V08_PV_VECTOR',pv['values'],call['request']['pv_kwh'],stage=h)
            same('V16_REQUEST_PRICES',source['prices'],call['request']['prices'],stage=h)
            saved_previous={int(k):v for k,v in call['request']['previous_active'].items()}
            same('V05_REQUEST_PARENT',active,saved_previous,stage=h)
            same('V03_REQUEST_FUTURE',list(range(h*6+1,145)),call['request']['future_slots'],stage=h)
            record('V08_LOAD_KNOWN_AT',max((instant(ld['known_at'])-start(date)).total_seconds(),0.),stage=h,tol=0)
            record('V08_PV_KNOWN_AT',max((instant(pv['known_at'])-decision).total_seconds(),0.),stage=h,tol=0)
            plan=[]
            for r in rows:
                t=r['slot_id'];q=r['new_active_q'];p=source['prices'][t-1]
                record('V04_NONNEGATIVE',max(-q,-r['c_ref'],-r['d_ref'],0),t,h)
                same('V16_PRICE_SOURCE',p,r['price_value'],t,h)
                same('V08_VINTAGE_ID',pv['forecast_id'],r['forecast_vintage_id'],t,h)
                same('V08_LOAD_ID',ld['forecast_id'],r['load_forecast_id'],t,h)
                same('V08_ISSUE_TIME',decision.isoformat(),r['issue_time'],t,h)
                known_at_max=instant(r['known_at_max'])
                dependency_known_at=max(instant(ld['known_at']),instant(pv['known_at']))
                record('V08_KNOWN_AT_MAX',max((known_at_max-decision).total_seconds(),(dependency_known_at-known_at_max).total_seconds(),0.0),t,h,tol=0)
                if h==0:
                    same('V06_BASE_NULL_DELTA',(None,None,None),(r['previous_active_q'],r['delta_plus'],r['delta_minus']),t,h)
                    same('V06_BASE_IDENTITY',q,r['base_q'],t,h);fee=p*q;base+=fee
                else:
                    prev=active[t]
                    same('V05_PREVIOUS_ACTIVE',prev['q'],r['previous_active_q'],t,h)
                    same('V05_BASE_IMMUTABLE',prev['base_q'],r['base_q'],t,h)
                    plus=max(q-prev['q'],0.);minus=max(prev['q']-q,0.)
                    record('V04_DELTA_IDENTITY',max(abs(plus-r['delta_plus']),abs(minus-r['delta_minus'])),t,h)
                    fee=p*(1.5*plus+beta*minus);adj+=fee
                record('V06_FEE_RECOMPUTE',abs(fee-r['fee_delta']),t,h,tol=max(1e-7,1e-10*abs(fee)))
                active[t]=dict(q=q,c_ref=r['c_ref'],d_ref=r['d_ref'],base_q=r['base_q'],event_id=eid)
                plan.append(dict(slot_id=t,q=q,c_ref=r['c_ref'],d_ref=r['d_ref']))
            same('V05_COMMITMENT_HASH',digest(active),event['commitment_hash'],stage=h)
            same('V07_REFERENCE_HASH',digest(plan),event['reference_plan_hash'],stage=h)
            states_at_stage[h]={k:dict(v) for k,v in active.items()}
        e=result['initial_soc'];parent=result['initial_state_hash'];emergency=0.;emergency_energy=0.;states=[e]
        for row,actual in zip(trace,source['actual_rows']):
            t=row['slot_id'];h=max(h for h in result['update_stages'] if h*6<t)
            ref=states_at_stage[h][t];p=source['prices'][t-1]
            end=start(date)+timedelta(minutes=t*10)
            same('V02_END',end.isoformat(),row['delivery_end'],t,h)
            same('V02_START',(end-timedelta(minutes=10)).isoformat(),row['delivery_start'],t,h)
            same('V08_ACTUAL_TIMING',end.isoformat(),row['actual_available_at'],t,h)
            same('V08_ACTION_TIME',end.isoformat(),row['action_decision_time'],t,h)
            same('V08_SOURCE_ACTUAL_TIME',actual['actual_available_at'],row['actual_available_at'],t,h)
            same('V07_Q',ref['q'],row['q'],t,h)
            same('V07_REFERENCE',(ref['c_ref'],ref['d_ref'],ref['event_id']),(row['c_ref'],row['d_ref'],row['active_commitment_event_id']),t,h)
            same('V10_ACTUAL_SOURCE',(actual['load_kwh'],actual['pv_kwh']),(row['actual_L'],row['actual_S']),t,h)
            same('V14_PARENT_STATE',parent,row['parent_state_hash'],t,h)
            record('V13_SOC_CONTINUITY',abs(row['e_before']-e),t,h)
            q=row['q'];s=row['actual_S'];l=row['actual_L'];c=row['c'];d=row['d'];r=row['r'];w=row['w'];v=row['v']
            balance=q+s-l
            c_expected=min(ref['c_ref'],balance,5000/6,max((10800-e)/eta_c,0.)) if balance>=0 else 0.
            d_expected=min(ref['d_ref'],-balance,5000/6,max(eta_d*(e-1200),0.)) if balance<0 else 0.
            record('V12_SAFETY_POLICY',max(abs(c-c_expected),abs(d-d_expected)),t,h)
            record('V12_ACTION_BOUNDS',max(-c,-d,c-5000/6,d-5000/6,min(c,d),0.),t,h)
            record('V10_ENERGY_BALANCE',abs(math.fsum([q,-w,r,s,d,-l,-c,-v])),t,h)
            record('V10_SOURCE_BOUNDS',max(-q,-r,-w,w-q,-v,v-s,-s,-l,0.),t,h)
            record('V11_EMERGENCY',abs(r-max(l+c-q-s-d,0.)),t,h)
            if r>1e-7:record('V11_NO_EMERGENCY_CHARGE_SPILL',max(c,w+v),t,h)
            u=max(q+s+d-l-c,0.)
            same('V10_SOURCE_SPLIT_MODE',cfg.get('source_split_mode'),row.get('source_split_mode'),t,h)
            if cfg.get('source_split_mode')=='GRID_FIRST':ew=min(q,u)
            elif cfg.get('source_split_mode')=='PV_FIRST':ew=u-min(s,u)
            else:raise ValueError('INVALID_SOURCE_SPLIT_MODE')
            record('V10_SOURCE_SPLIT',max(abs(w-ew),abs(v-(u-ew))),t,h)
            e=e+eta_c*c-d/eta_d;states.append(e)
            record('V13_SOC_RECURSION',abs(row['e_after']-e),t,h)
            record('V15_SOC_BOUNDS',max(1200-e,e-10800,1200-row['e_before'],row['e_before']-10800,0.),t,h)
            same('V16_DELIVERY_PRICE',p,row['price'],t,h)
            record('V17_EMERGENCY_COST',abs(5*p*r-row['cost_emergency']),t,h)
            emergency+=5*p*r;emergency_energy+=r;parent=digest(row)
        record('V14_FINAL_SOC',abs(e-result['final_soc']),144)
        same('V14_FINAL_HASH',parent,result['final_state_hash'],144)
        metrics=dict(base_plan_cost=base,adjustment_cost=adj,emergency_cost=emergency,
                     total_cost=math.fsum([base,adj,emergency]),emergency_energy=emergency_energy,
                     soc_min=min(states),soc_max=max(states),final_soc=e,
                     charge_kwh=math.fsum(r['c'] for r in trace),discharge_kwh=math.fsum(r['d'] for r in trace),
                     paid_unused_kwh=math.fsum(r['w'] for r in trace),pv_unused_kwh=math.fsum(r['v'] for r in trace))
    except (ValueError,KeyError,TypeError,IndexError,StopIteration,ArithmeticError) as exc:
        record('INPUT_OR_CONTRACT_INVALID',detail=f'{type(exc).__name__}: {exc}')
    checks=[]
    for name,values in observations.items():
        maximum,slot,stage=max(values,key=lambda v:v[0])
        checks.append(dict(check=name,status='FAIL' if name in failures else 'PASS',max_violation=maximum if math.isfinite(maximum) else None,
                           argmax=dict(date=date,stage=stage,slot=slot),count=len(failures.get(name,[])),
                           first_failure=failures.get(name,[None])[0]))
    for name,reason in [('V01_FORMAL_AUTHORITY','A1_A6_NOT_RELEASED_SYNTHETIC_ONLY'),('V09_INTERPOLATION','MOCK_ENERGY_VECTORS; utility tested separately'),
                        ('V19_REAL_SCREENING','NO_FROZEN_LOAD_OR_RELEASED_REGISTRY'),('V20_OFFICIAL_WRITER','NOT_IN_PHASE_A'),
                        ('V21_LP_OPTIMALITY','INJECTED_MOCK_PLANNER_NOT_LP'),('V22_SENSITIVITY','NO_FORMAL_SENSITIVITY_AUTHORIZATION')]:
        checks.append(dict(check=name,status='NOT_APPLICABLE',reason=reason))
    return dict(status='FAIL_REOPEN_IMPLEMENTATION' if failures else 'PASS_FOR_XXT_REVIEW',
                scope='SYNTHETIC_ONLY',checks=checks,metrics=metrics,formal_result=False,frozen=False)
