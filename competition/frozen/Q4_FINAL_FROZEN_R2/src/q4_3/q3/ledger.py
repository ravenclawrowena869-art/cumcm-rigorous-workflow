"""Atomic previous-active commitment events; no formal settlement selection."""
from copy import deepcopy
from datetime import timedelta
from .common import digest,numeric,start

class Ledger:
    def __init__(self,run_id,date,prices,beta):
        if beta not in (.5,-.5):raise ValueError('UNRESOLVED_CANCELLATION_MODE')
        if len(prices)!=144:raise ValueError('PRICE_SLOTS')
        self.prices=[numeric(p,1e-300) for p in prices]
        self.beta=beta;self.date=date;self.run_id=run_id
        self._active={};self._events=[];self._ids={};self.executed_count=0

    @property
    def active(self):return deepcopy(self._active)
    @property
    def events(self):return deepcopy(self._events)
    @property
    def state_hash(self):return digest(self._active)

    def commit(self,event_id,stage,plan,parent_hash,forecast_id,load_forecast_id,known_at_max=None):
        payload=dict(event_id=event_id,stage=stage,plan=plan,parent_hash=parent_hash,
                     forecast_id=forecast_id,load_forecast_id=load_forecast_id)
        fingerprint=digest(payload)
        if event_id in self._ids:
            if self._ids[event_id]!=fingerprint:raise ValueError('LEDGER_ID_COLLISION')
            return next(deepcopy(e) for e in self._events if e['event_id']==event_id)
        if parent_hash!=self.state_hash:raise ValueError('PARENT_MISMATCH')
        if stage not in (0,6,12,18) or self.executed_count!=stage*6:raise ValueError('STAGE_CHRONOLOGY')
        if (stage==0 and self._events) or (stage>0 and not self._events):raise ValueError('BASE_IDENTITY')
        if self._events and stage<=self._events[-1]['stage']:raise ValueError('STAGE_CHRONOLOGY')
        if [r.get('slot_id') for r in plan]!=list(range(stage*6+1,145)):raise ValueError('PAST_OR_MISSING_SLOT')
        rows=[];updated=deepcopy(self._active)
        issue=(start(self.date)+timedelta(hours=stage)).isoformat()
        known_at_max = known_at_max or issue
        for reference in plan:
            t=reference['slot_id'];q=numeric(reference['q']);c=numeric(reference['c_ref'],0,5000/6);d=numeric(reference['d_ref'],0,5000/6)
            if min(c,d)>1e-7:raise ValueError('REFERENCE_SIMULTANEOUS_CD')
            old=self._active[t]['q'] if stage else None
            dp=max(q-old,0.) if stage else None;dm=max(old-q,0.) if stage else None
            fee=self.prices[t-1]*(1.5*dp+self.beta*dm) if stage else self.prices[t-1]*q
            base=self._active[t]['base_q'] if stage else q
            rows.append(dict(date=self.date,stage=stage,slot_id=t,base_q=base,previous_active_q=old,
                             new_active_q=q,delta_plus=dp,delta_minus=dm,price_value=self.prices[t-1],
                             fee_delta=fee,c_ref=c,d_ref=d,issue_time=issue,known_at_max=known_at_max,
                             forecast_vintage_id=forecast_id,load_forecast_id=load_forecast_id))
            updated[t]=dict(q=q,c_ref=c,d_ref=d,base_q=base,event_id=event_id)
        event=dict(event_id=event_id,run_id=self.run_id,date=self.date,stage=stage,
                   parent_commitment_hash=parent_hash,commitment_hash=digest(updated),
                   reference_plan_hash=digest(plan),payload_hash=fingerprint,rows=rows)
        self._active=updated;self._events.append(event);self._ids[event_id]=fingerprint
        return deepcopy(event)
