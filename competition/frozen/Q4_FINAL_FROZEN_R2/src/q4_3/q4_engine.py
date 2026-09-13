from __future__ import annotations
from copy import deepcopy
from datetime import timedelta
from time import perf_counter
import math
from q3.common import digest,numeric,instant,start

class Q4Ledger:
    def __init__(self,run_id,date,beta):
        if beta != -0.5: raise ValueError('Q4_LEDGER_BETA')
        self.beta=beta; self.date=date; self.run_id=run_id
        self._active={}; self._events=[]; self._ids={}; self.executed_count=0
    @property
    def active(self): return deepcopy(self._active)
    @property
    def events(self): return deepcopy(self._events)
    @property
    def state_hash(self): return digest(self._active)
    def commit(self,event_id,stage,plan,parent_hash,forecast_id,load_forecast_id,
               known_at_max, price_meta_by_slot):
        if parent_hash != self.state_hash: raise ValueError('PARENT_MISMATCH')
        if stage not in (0,6,12,18) or self.executed_count != stage*6: raise ValueError('STAGE_CHRONOLOGY')
        if [r.get('slot_id') for r in plan] != list(range(stage*6+1,145)): raise ValueError('PAST_OR_MISSING_SLOT')
        rows=[]; updated=deepcopy(self._active); issue=(start(self.date)+timedelta(hours=stage)).isoformat()
        payload={'event_id':event_id,'stage':stage,'plan':plan,'parent_hash':parent_hash,'forecast_id':forecast_id,'load_forecast_id':load_forecast_id,
                 'price_meta':price_meta_by_slot}
        fp=digest(payload)
        if event_id in self._ids:
            if self._ids[event_id] != fp: raise ValueError('LEDGER_ID_COLLISION')
            return next(deepcopy(e) for e in self._events if e['event_id']==event_id)
        for ref in plan:
            t=ref['slot_id']; q=numeric(ref['q']);
            raw_c=float(ref['c_ref']); raw_d=float(ref['d_ref']); pmax=5000/6; tol=1e-7
            if (not math.isfinite(raw_c)) or (not math.isfinite(raw_d)) or raw_c < -tol or raw_d < -tol or raw_c > pmax+tol or raw_d > pmax+tol:
                raise ValueError(f'REFERENCE_CD_OUTSIDE_HARD_TOL:{t}:{raw_c}:{raw_d}')
            c=min(max(raw_c,0.0),pmax); d=min(max(raw_d,0.0),pmax)
            if min(c,d)>1e-7: raise ValueError('REFERENCE_SIMULTANEOUS_CD')
            pm=price_meta_by_slot[t]
            dp=dm=None; old=None
            if stage:
                old=float(self._active[t]['q']); dp=max(q-old,0.0); dm=max(old-q,0.0)
            decision_fee=float(pm['decision_price'])*(q if stage==0 else 1.5*dp+self.beta*dm)
            settlement_fee=float(pm['settlement_price'])*(q if stage==0 else 1.5*dp+self.beta*dm)
            base=self._active[t]['base_q'] if stage else q
            rows.append({'date':self.date,'stage':stage,'slot_id':t,'base_q':base,'previous_active_q':old,'new_active_q':q,
                         'delta_plus':dp,'delta_minus':dm,'decision_price':float(pm['decision_price']),
                         'settlement_price':float(pm['settlement_price']),'decision_fee_delta':decision_fee,
                         'settlement_fee_delta':settlement_fee,'price_known_at':pm['known_at'],'price_source':pm['source'],'price_mode':pm['mode'],
                         'c_ref':c,'d_ref':d,'issue_time':issue,'known_at_max':known_at_max,
                         'forecast_vintage_id':forecast_id,'load_forecast_id':load_forecast_id})
            updated[t]={'q':q,'c_ref':c,'d_ref':d,'base_q':base,'event_id':event_id,'decision_price':float(pm['decision_price'])}
        event={'event_id':event_id,'run_id':self.run_id,'date':self.date,'stage':stage,'parent_commitment_hash':parent_hash,
               'commitment_hash':digest(updated),'reference_plan_hash':digest(plan),'payload_hash':fp,'rows':rows}
        self._active=updated;self._events.append(event);self._ids[event_id]=fp
        return deepcopy(event)


def _tz8(ts: str) -> str:
    # Price preflight timestamps are local wall-clock timestamps without offset.
    return ts if ('+' in ts[10:] or ts.endswith('Z')) else ts + '+08:00'


def solve_q4_day(*,date,load_forecast_provider,pv_vintage_provider,initial_soc,actual_rows,
                 price_points_by_stage,settlement_prices,config,initial_state_hash,planner,mode):
    update_stages=[0,6,12,18]
    actual_rows=deepcopy(actual_rows); load=deepcopy(load_forecast_provider); used_pv={h:deepcopy(pv_vintage_provider[h]) for h in update_stages}
    if len(settlement_prices)!=144: raise ValueError('SETTLEMENT_PRICE_SLOTS')
    eta_c=numeric(config['eta_c'],1e-12,1.); eta_d=numeric(config['eta_d'],1e-12,1.)
    e=numeric(initial_soc,1200.,10800.)
    # Build complete stage price vectors and metadata. Past entries are never optimized; give them realized prices for numeric completeness.
    stage_price_vec={}; stage_meta={}; stage_price_known_max={}
    for h in update_stages:
        first=h*6+1; pts=price_points_by_stage[h]
        if [int(x.slot) for x in pts] != list(range(first,145)): raise ValueError(f'PRICE_STAGE_SLOT_IDENTITY:{h}')
        vec=list(map(float,settlement_prices)); meta={}
        for x in pts:
            known=_tz8(str(x.known_at)); decision=_tz8(str(x.decision_time))
            if mode=='CAUSAL_LAG7' and instant(known)>instant(decision): raise ValueError(f'FUTURE_PRICE_LEAKAGE:{h}:{x.slot}')
            vec[x.slot-1]=float(x.decision_price)
            meta[x.slot]={'decision_price':float(x.decision_price),'settlement_price':float(x.settlement_price),'known_at':known,'source':x.source,'mode':x.mode}
        stage_price_vec[h]=vec; stage_meta[h]=meta
        if mode=='CAUSAL_LAG7': stage_price_known_max[h]=max(instant(meta[t]['known_at']) for t in meta).isoformat()
        else: stage_price_known_max[h]=None
    run_id='Q4_3_'+mode+'_'+digest([date,config,initial_soc,initial_state_hash,load,used_pv,stage_price_vec])[:16]
    ledger=Q4Ledger(run_id,date,config['beta']); trace=[];stage_calls=[];last_state=initial_state_hash;planner_max=0.; runtime=perf_counter()
    for slot in range(1,145):
        h=(slot-1)//6
        if (slot-1)%36==0 and h in update_stages:
            ledger.executed_count=slot-1; pv=used_pv[h]; prefix_hash=digest(trace)
            base_known=max(instant(load['known_at']),instant(pv['known_at']))
            dependency_known_at=(max(base_known,instant(stage_price_known_max[h])) if mode=='CAUSAL_LAG7' else base_known).isoformat()
            request={'date':date,'stage':h,'decision_time':(start(date)+timedelta(hours=h)).isoformat(),
                     'future_slots':list(range(slot,145)),'load_kwh':deepcopy(load['values']),'pv_kwh':deepcopy(pv['values']),
                     'prices':deepcopy(stage_price_vec[h]),'initial_soc':e,'previous_active':ledger.active,
                     'executed_prefix_hash':prefix_hash,'forecast_id':pv['forecast_id'],'load_forecast_id':load['forecast_id'],
                     'dependency_known_at':dependency_known_at}
            try:
                beg=perf_counter(); raw=planner(deepcopy(request)); elapsed=perf_counter()-beg
            except Exception as ex:
                raise RuntimeError(f'Q4_PLANNER_EXCEPTION:{date}:stage={h}:slot={slot}:{type(ex).__name__}:{ex}') from ex
            if not isinstance(raw,dict) or raw.get('planner_kind')!='FORMAL_LP': raise ValueError('Q4_PLANNER_PROTOCOL')
            sm=deepcopy(raw.get('solver_metadata')); val=deepcopy(raw.get('validation'))
            if (sm or {}).get('status')!='OPTIMAL' or (val or {}).get('status')!='PASS': raise ValueError('Q4_PLANNER_FAIL')
            planner_max=max(planner_max,float(val.get('max_violation',0.)))
            event=ledger.commit(f'{run_id}:{date}:{h:02d}',h,raw['plan'],ledger.state_hash,pv['forecast_id'],load['forecast_id'],dependency_known_at,stage_meta[h])
            stage_calls.append({'stage':h,'initial_soc':e,'executed_prefix_hash':prefix_hash,'request':request,'event_id':event['event_id'],
                                'solver_status':sm['status'],'runtime_seconds':elapsed,'solver_metadata':sm,'planner_validation':val,
                                'price_mode':mode,'price_known_at_max':stage_price_known_max[h]})
            if digest(trace)!=prefix_hash: raise ValueError('PAST_MUTATED')
        active=ledger.active[slot]; actual=actual_rows[slot-1]; end=start(date)+timedelta(minutes=10*slot)
        if instant(actual['actual_available_at']) != end: raise ValueError('ACTUAL_TIMING_MISMATCH')
        L=numeric(actual['load_kwh']); S=numeric(actual['pv_kwh']); q=active['q']; bal=q+S-L
        if bal>=0:
            c=min(active['c_ref'],bal,5000/6,max((10800-e)/eta_c,0.));d=0.
        else:
            c=0.;d=min(active['d_ref'],-bal,5000/6,max(eta_d*(e-1200),0.))
        r=max(L+c-q-S-d,0.);unused=max(q+S+d-L-c,0.);w=min(q,unused);v=unused-w;next_e=e+eta_c*c-d/eta_d
        sp=float(settlement_prices[slot-1])
        row={'run_id':run_id,'date':date,'slot_id':slot,'delivery_start':(end-timedelta(minutes=10)).isoformat(),'delivery_end':end.isoformat(),
             'active_commitment_event_id':active['event_id'],'q':q,'actual_L':L,'actual_S':S,'actual_available_at':end.isoformat(),
             'action_decision_time':end.isoformat(),'c_ref':active['c_ref'],'d_ref':active['d_ref'],'c':c,'d':d,'e_before':e,'e_after':next_e,
             'r':r,'w':w,'v':v,'settlement_price':sp,'active_decision_price':active['decision_price'],'cost_emergency_settlement':5*sp*r,
             'source_split_mode':'GRID_FIRST','override_c':active['c_ref']-c,'override_d':active['d_ref']-d,'fallback_reason':None,'parent_state_hash':last_state}
        last_state=digest(row);trace.append(row);e=next_e
    return {'scope':'Q4_3_'+('FORMAL_CAUSAL' if mode=='CAUSAL_LAG7' else 'DIAGNOSTIC_ONLY_ORACLE'), 'run_id':run_id,'date':date,
            'config':deepcopy(config),'update_stages':update_stages,'initial_soc':initial_soc,'initial_state_hash':initial_state_hash,
            'final_soc':e,'final_state_hash':last_state,'events':ledger.events,'trace':trace,'stage_calls':stage_calls,
            'source_inputs':{'load_forecast':load,'pv_forecasts':used_pv,'settlement_prices':list(settlement_prices),'price_mode':mode},
            'runtime_seconds':perf_counter()-runtime,'max_planner_hard_violation':planner_max,'price_mode':mode}
