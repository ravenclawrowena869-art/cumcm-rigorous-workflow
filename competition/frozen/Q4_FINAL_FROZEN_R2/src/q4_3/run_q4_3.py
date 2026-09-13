from __future__ import annotations
from pathlib import Path
from datetime import date,timedelta
import sys,json,csv,math,time,hashlib,platform,os
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
from q3.data import load_actuals,load_vintages
from q3.annual_runner import stage_pv,date_range
from q3.formal_lp import make_formal_lp_planner, build_formal_config
from q3.common import digest,start,instant
from q4_engine import solve_q4_day
from q4_price_provider import Q4PriceProvider

PKG_ROOT=Path(__file__).resolve().parents[1]
INPUTS=PKG_ROOT/'inputs'
AUTH=PKG_ROOT/'authority/q3_frozen_refs'
OUT=Path(os.environ.get('Q4_R2_OUT', str(PKG_ROOT/'replay_work'))).resolve()
OUT.mkdir(parents=True,exist_ok=True)

def jload(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def write_json(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False,default=str)+'\n',encoding='utf-8')
def append_csv(path,rows,fields):
 path=Path(path);new=not path.exists();path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('a',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
  if new:w.writeheader()
  for r in rows:w.writerow({k:r.get(k,'') for k in fields})

def derive_loads():
 df=pd.read_csv(INPUTS/'Q2_FROZEN_annual_forecast.csv')
 if len(df)!=48096: raise ValueError('LOAD_ROWS')
 out={}
 for day,g in df.groupby('date',sort=False):
  g=g.sort_values('slot');
  if g.slot.tolist()!=list(range(1,145)): raise ValueError('LOAD_SLOTS:'+day)
  known=f'{day}T00:00:00+08:00'
  out[day]={'forecast_id':f'L2_LAG7:Q2_FINAL_FROZEN_R1_SLOT_START_ADAPTER_V1:{day}','known_at':known,
            'values':[float(x)/6.0 for x in g.forecast_load_kW.tolist()]}
 return out

def check_load_adapter(loads):
 # R2 standalone proof: bind the exact Q2 frozen annual forecast by hash and validate
 # the deterministic kW->kWh adapter without requiring an external sandbox path.
 src=INPUTS/'Q2_FROZEN_annual_forecast.csv'
 df=pd.read_csv(src)
 expected_sha='c91583954fbf3e9d388b08d82fc8e67c9a12e3684d22e38a9f1db7ce73b65ac0'
 hash_ok=(sha(src)==expected_sha)
 rows_ok=(len(df)==48096)
 slots_ok=True; meta_bad=0; maxdiff=0.0
 for day,g in df.groupby('date',sort=False):
  g=g.sort_values('slot')
  if g.slot.tolist()!=list(range(1,145)): slots_ok=False; continue
  cur=loads[str(day)]
  exp_known=f'{day}T00:00:00+08:00'
  if cur['known_at']!=exp_known or cur['forecast_id']!=f'L2_LAG7:Q2_FINAL_FROZEN_R1_SLOT_START_ADAPTER_V1:{day}': meta_bad+=1
  maxdiff=max(maxdiff,max(abs(float(a)/6.0-float(b)) for a,b in zip(g.forecast_load_kW,cur['values'])))
 status='PASS' if hash_ok and rows_ok and slots_ok and meta_bad==0 and maxdiff<=1e-12 else 'FAIL'
 return {'status':status,'source_q2_annual_forecast_sha256':sha(src),'expected_source_sha256':expected_sha,'source_hash_match':hash_ok,
         'rows':len(df),'slots_ok':slots_ok,'max_kwh_diff':maxdiff,'metadata_mismatch_days':meta_bad,
         'prior_authority_adapter_sha256':'8ceb83944d445eeef6316a98769f5421bb1820385dbd62d7f1d3ceab856eb790',
         'prior_authority_adapter_check':'See 03_VALIDATION/reconstruction_load_adapter_check_R1_original.json; Feb-01 Q3 exact reproduction is the semantic no-drift Gate.'}

def blend(ref,new,lam,first_slot):
 vals=list(ref['values'])
 for i in range(first_slot-1,144): vals[i]=lam*float(new['values'][i])+(1-lam)*float(ref['values'][i])
 return {'forecast_id':f"B1B:{new['forecast_id']}:{digest([lam,ref['forecast_id'],first_slot])[:16]}", 'known_at':new['known_at'],'values':vals,'interpolation':'PV_HOURLY_LINEAR_CAUSAL_BOUNDARY_V1','boundary_mode':'B1B_BLEND_AFTER_A4'}
class Hist:
 def __init__(self):self.h={6:[],12:[],18:[]}
 def lambdas(self):
  o={}
  for s in (6,12,18):
   sel=self.h[s][-28:];n=len(sel)
   if n<14:o[s]=(1.,None,None,sel,'FALLBACK_TO_B1A_INSUFFICIENT_HISTORY')
   else:
    en=sum(x['L_new'] for x in sel)/n;er=sum(x['L_ref'] for x in sel)/n
    if en+er<=1e-12:o[s]=(1.,en,er,sel,'FALLBACK_TO_B1A_DEGENERATE_ZERO_LOSS')
    else:o[s]=(min(max(er/(en+er),0.),1.),en,er,sel,'NONE')
  return o
 def record(self,day,legal,refs,actual):
  for s,first in ((6,37),(12,73),(18,109)):
   slots=list(range(first,145))
   def mae(vals):return sum(abs(float(vals[t-1])-float(actual[t-1]['pv_kwh'])) for t in slots)/len(slots)
   self.h[s].append({'date':day,'L_new':mae(legal[s]['values']),'L_ref':mae(refs[s]['values'])})
def legal_day(vmap,day):
 pv={};prefix=[]
 for st in (0,6,12,18):
  x=stage_pv(vmap,day,st,prefix);pv[st]=x;prefix=x['values'][:(st+6)*6]
 return pv
def build_schedules(actuals,vmap):
 hist=Hist();schedules={};ledger=[];d=date(2025,1,2);end=date(2025,12,31)
 while d<=end:
  day=d.isoformat();legal=legal_day(vmap,day);lams=hist.lambdas();eff={0:legal[0]};refs={}
  for s,first in ((6,37),(12,73),(18,109)):
   refs[s]=eff[{6:0,12:6,18:12}[s]];lam,en,er,sel,fb=lams[s];eff[s]=blend(refs[s],legal[s],lam,first)
   ledger.append({'date':day,'stage':s,'lambda':lam,'e_new':en,'e_ref':er,'valid_history_count':len(sel),
                  'training_start_date':sel[0]['date'] if sel else None,'training_end_date':sel[-1]['date'] if sel else None,
                  'training_cutoff_date':(d-timedelta(days=1)).isoformat(),'window_id':'TRAILING_28_VALID_DAYS','method_id':'L1_INVERSE_OOS_ERROR',
                  'loss_id':'MAE','fallback_status':fb,'history_source_hash':digest(sel),'pv_new_source_hash':digest(legal[s]),
                  'pv_ref_reconstruction_hash':digest(refs[s]),'new_forecast_id':legal[s]['forecast_id']})
  schedules[day]=eff;hist.record(day,legal,refs,actuals[day]);d+=timedelta(days=1)
 return schedules,ledger

def q4_config():
 cfg=build_formal_config('B1A')
 rel=jload(AUTH/'Q3_B1B_CONTROLLER_RELEASE_R5_5.json')
 cfg['strategy_id']='B1B';cfg['pv_vintage_policy']='BLENDED_TRUST_WITH_FROZEN_CAUSAL_LAMBDA'
 cfg['formal_release']={'status':'RELEASED','authority':rel['authority'],'source_hash':sha(AUTH/'Q3_B1B_CONTROLLER_RELEASE_R5_5.json'),'release_id':rel['release_id'],'scope':'Q4_3_INHERITED_B1B'}
 return cfg,rel

def validate_q4_day(run):
 tol=1e-7;fails=[];maxv=0.;arg=None
 def hit(name,v,loc=None):
  nonlocal maxv,arg
  v=float(v)
  if v>maxv:maxv=v;arg={'check':name,'location':loc}
  if v>tol:fails.append({'check':name,'violation':v,'location':loc})
 tr=run['trace'];evs=run['events'];calls=run['stage_calls'];mode=run['price_mode']
 if len(tr)!=144:fails.append({'check':'TRACE_144','violation':1})
 # physical
 for r in tr:
  t=r['slot_id']; hit('ENERGY_BALANCE',abs((r['q']-r['w']+r['r']+r['actual_S']+r['d'])-(r['actual_L']+r['c']+r['v'])),t)
  calc=r['e_before']+0.9*r['c']-r['d']/0.9;hit('SOC_RECURSION',abs(calc-r['e_after']),t)
  hit('SOC_BOUNDS',max(1200-r['e_after'],r['e_after']-10800,0),t);hit('POWER',max(r['c']-5000/6,r['d']-5000/6,0),t)
  hit('W_Q',max(r['w']-r['q'],0),t);hit('V_PV',max(r['v']-r['actual_S'],0),t);hit('SIMUL_CD',min(r['c'],r['d']),t);hit('EMERGENCY_CHARGE',min(r['r'],r['c']),t)
 # planner and event identity
 expected=[0,6,12,18]
 if [c['stage'] for c in calls]!=expected:fails.append({'check':'STAGES','violation':1})
 for c in calls:
  if c['solver_status']!='OPTIMAL' or c['planner_validation']['status']!='PASS':fails.append({'check':'SOLVER','violation':1,'location':c['stage']})
 for e in evs:
  if [x['slot_id'] for x in e['rows']]!=list(range(e['stage']*6+1,145)):fails.append({'check':'EVENT_SLOTS','violation':1,'location':e['stage']})
 # price causality
 future_leaks=0
 for e in evs:
  decision=instant(e['rows'][0]['issue_time']) if e['rows'] else None
  for x in e['rows']:
   if mode=='CAUSAL_LAG7' and instant(x['price_known_at'])>decision:future_leaks+=1
 if mode=='CAUSAL_LAG7' and future_leaks:fails.append({'check':'PRICE_FUTURE_LEAK','violation':future_leaks})
 # accounting independent
 base=sum(float(x['settlement_price'])*float(x['new_active_q']) for x in evs[0]['rows'])
 adj=0.
 for e in evs[1:]:
  adj+=sum(float(x['settlement_price'])*(1.5*float(x['delta_plus'])-0.5*float(x['delta_minus'])) for x in e['rows'])
 em=sum(5*float(r['settlement_price'])*float(r['r']) for r in tr);total=base+adj+em
 metrics={'base_cost_yuan':base,'adjustment_cost_yuan':adj,'emergency_cost_yuan':em,'total_cost_yuan':total,
          'emergency_energy_kwh':sum(float(r['r']) for r in tr),'terminal_soc_kwh':float(tr[-1]['e_after']),
          'soc_min_kwh':min(float(r['e_after']) for r in tr),'soc_max_kwh':max(float(r['e_after']) for r in tr),
          'throughput_kwh':sum(float(r['c'])+float(r['d']) for r in tr),'price_future_realized_leak_count':future_leaks,
          'planner_max_violation':max(float(c['planner_validation'].get('max_violation',0)) for c in calls),
          'solver_runtime_seconds':sum(float(c['runtime_seconds']) for c in calls)}
 return {'status':'PASS' if not fails else 'FAIL','failure_count':len(fails),'failures':fails,'max_hard_violation':maxv,'argmax':arg,'metrics':metrics}

def run_mode(mode,loads,actuals,schedules,provider,cfg,rel,days=None):
 od=OUT/'results'/('causal' if mode=='CAUSAL_LAG7' else 'oracle');od.mkdir(parents=True,exist_ok=True)
 for p in od.glob('*'): 
  if p.is_file():p.unlink()
 dates=date_range('2025-02-01','2025-12-31');
 if days: dates=dates[:days]
 soc=6000.; state=digest({'protocol':'Q4_3_B1B_CONSECUTIVE_STATE_R1','mode':mode,'date':dates[0],'initial_soc_kWh':6000.,'q3_release_id':rel['release_id']})
 daily=[];annual_start=time.perf_counter();price_audit=[]
 TRACE_FIELDS=['date','mode','slot_id','q','actual_L','actual_S','c_ref','d_ref','c','d','e_before','e_after','r','w','v','settlement_price','active_decision_price','cost_emergency_settlement','active_commitment_event_id']
 LEDGER_FIELDS=['date','mode','event_id','stage','slot_id','base_q','previous_active_q','new_active_q','delta_plus','delta_minus','decision_price','settlement_price','decision_fee_delta','settlement_fee_delta','price_known_at','price_source','price_mode','c_ref','d_ref','issue_time','known_at_max','forecast_vintage_id','load_forecast_id']
 for ix,day in enumerate(dates):
  pts={h:provider.q4_3_stage(day,h,mode=mode) for h in (0,6,12,18)}; settlement=[float(x.settlement_price) for x in provider.q4_3_stage(day,0,mode=mode)]
  run=solve_q4_day(date=day,load_forecast_provider=loads[day],pv_vintage_provider=schedules[day],initial_soc=soc,actual_rows=actuals[day],
                   price_points_by_stage=pts,settlement_prices=settlement,config=cfg,initial_state_hash=state,planner=make_formal_lp_planner(cfg),mode=mode)
  val=validate_q4_day(run)
  if val['status']!='PASS':
   write_json(od/'FAILED_DAY.json',{'date':day,'validator':val});raise RuntimeError(f'Q4_DAY_FAIL:{mode}:{day}:{val["failures"][:3]}')
  m=val['metrics'];
  with (od/'stage_solver_metadata.jsonl').open('a',encoding='utf-8') as f:
   for c in run['stage_calls']:
    f.write(json.dumps({'date':day,'mode':mode,'stage':c['stage'],'solver_status':c['solver_status'],'runtime_seconds':c['runtime_seconds'],'solver_metadata':c['solver_metadata'],'planner_validation':c['planner_validation']},ensure_ascii=False,default=str)+'\n')
  recoveries=[]
  for c in run['stage_calls']:
   sm=c.get('solver_metadata') or {}
   if int(sm.get('fallback_count',0))>0 or int(sm.get('numerical_recovery_count',0))>0:
    recoveries.append({'date':day,'mode':mode,'stage':c['stage'],'fallback_count':int(sm.get('fallback_count',0)),'numerical_recovery_count':int(sm.get('numerical_recovery_count',0)),'tie_break_status':sm.get('tie_break_status'),'policy':sm.get('numerical_recovery_policy')})
  if recoveries:
   append_csv(od/'numerical_recovery.csv',recoveries,['date','mode','stage','fallback_count','numerical_recovery_count','tie_break_status','policy'])
  append_csv(od/'trace.csv',[{'date':day,'mode':mode,**r} for r in run['trace']],TRACE_FIELDS)
  lrows=[]
  for e in run['events']:
   for r in e['rows']:lrows.append({'date':day,'mode':mode,'event_id':e['event_id'],**r})
  append_csv(od/'stage_ledger.csv',lrows,LEDGER_FIELDS)
  for h in (0,6,12,18):
   for x in pts[h]:price_audit.append({'date':day,'stage':h,'slot':x.slot,'decision_time':x.decision_time,'decision_price':x.decision_price,'settlement_price':x.settlement_price,'known_at':x.known_at,'source':x.source,'mode':mode})
  daily.append({'date':day,'mode':mode,**m,'initial_soc_kwh':soc,'hard_failure_count':0,'max_hard_violation':val['max_hard_violation']})
  soc=float(m['terminal_soc_kwh']);state=run['final_state_hash']
  if (ix+1)%25==0 or ix==0 or ix+1==len(dates): print(f'{mode} {ix+1}/{len(dates)} {day} cost={m["total_cost_yuan"]:.2f} soc={soc:.2f}',flush=True)
 pd.DataFrame(daily).to_csv(od/'daily.csv',index=False);pd.DataFrame(price_audit).to_csv(od/'price_audit.csv',index=False)
 annual={k:sum(float(x[k]) for x in daily) for k in ['base_cost_yuan','adjustment_cost_yuan','emergency_cost_yuan','total_cost_yuan','emergency_energy_kwh','throughput_kwh','solver_runtime_seconds']}
 annual.update({'mode':mode,'days':len(daily),'initial_soc_kwh':6000.,'terminal_soc_kwh':soc,'soc_min_kwh':min(x['soc_min_kwh'] for x in daily),'soc_max_kwh':max(x['soc_max_kwh'] for x in daily),
                'price_future_realized_leak_count':sum(int(x['price_future_realized_leak_count']) for x in daily),'hard_failure_count':0,'wall_seconds':time.perf_counter()-annual_start,
                'oracle_diagnostic_only':mode!='CAUSAL_LAG7'})
 write_json(od/'annual.json',annual);write_json(od/'validator.json',{'status':'PASS','days':len(daily),'hard_failure_count':0,'price_future_realized_leak_count':annual['price_future_realized_leak_count'],'max_daily_hard_violation':max(x['max_hard_violation'] for x in daily)})
 return annual,pd.DataFrame(daily)

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');ap.add_argument('--mode',choices=['causal','oracle','both'],default='both');args=ap.parse_args()
 loads=derive_loads();adapter=check_load_adapter(loads);write_json(OUT/'reconstruction_load_adapter_check.json',adapter)
 if adapter['status']!='PASS':raise RuntimeError('LOAD_ADAPTER_MISMATCH')
 actuals=load_actuals(INPUTS/'attachment2.xlsx');vints=load_vintages(INPUTS/'attachment3.xlsx');vmap={x['issue_time']:x for x in vints};schedules,ll=build_schedules(actuals,vmap)
 pd.DataFrame(ll).to_csv(OUT/'lambda_ledger_all.csv',index=False)
 cfg,rel=q4_config();provider=Q4PriceProvider(INPUTS/'q4_price_lag7_feb_dec.csv')
 results={};dfs={}
 modes=[]
 if args.mode in ('causal','both'):modes.append('CAUSAL_LAG7')
 if args.mode in ('oracle','both'):modes.append('ORACLE_DIAGNOSTIC')
 for mode in modes:
  a,d=run_mode(mode,loads,actuals,schedules,provider,cfg,rel,days=1 if args.smoke else None);results[mode]=a;dfs[mode]=d
 if len(results)==2:
  c=results['CAUSAL_LAG7'];o=results['ORACLE_DIAGNOSTIC'];gap=c['total_cost_yuan']-o['total_cost_yuan'];pct=100*gap/c['total_cost_yuan']
  comp={'causal_total_cost_yuan':c['total_cost_yuan'],'oracle_total_cost_yuan':o['total_cost_yuan'],'causal_minus_oracle_yuan':gap,'gap_pct_of_causal':pct,
        'causal_emergency_cost_yuan':c['emergency_cost_yuan'],'oracle_emergency_cost_yuan':o['emergency_cost_yuan'],'causal_adjustment_cost_yuan':c['adjustment_cost_yuan'],'oracle_adjustment_cost_yuan':o['adjustment_cost_yuan']}
  pd.DataFrame([comp]).to_csv(OUT/'results/causal_vs_oracle.csv',index=False);write_json(OUT/'results/causal_vs_oracle.json',comp)
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
