from pathlib import Path
from datetime import date,timedelta
import sys,json,hashlib
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
from q3.data import load_actuals,load_tariff,load_vintages
from q3.annual_runner import stage_pv
from q3.engine import solve_q3_day
from q3.formal_lp import make_formal_lp_planner, build_formal_config
from q3.annual_validator import validate_formal_run
from q3.common import digest

PKG_ROOT=Path(__file__).resolve().parents[1]
INPUTS=PKG_ROOT/'inputs'
AUTH=PKG_ROOT/'authority/q3_frozen_refs'
OUT=PKG_ROOT/'replay_work/repro'
OUT.mkdir(parents=True,exist_ok=True)

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def jload(p):return json.loads(Path(p).read_text())

def derive_loads():
 df=pd.read_csv(INPUTS/'Q2_FROZEN_annual_forecast.csv')
 if sha(INPUTS/'Q2_FROZEN_annual_forecast.csv')!='c91583954fbf3e9d388b08d82fc8e67c9a12e3684d22e38a9f1db7ce73b65ac0': raise RuntimeError('Q2_FORECAST_HASH_MISMATCH')
 out={}
 for day,g in df.groupby('date',sort=False):
  g=g.sort_values('slot')
  out[str(day)]={'forecast_id':f'L2_LAG7:Q2_FINAL_FROZEN_R1_SLOT_START_ADAPTER_V1:{day}','known_at':f'{day}T00:00:00+08:00','values':[float(x)/6 for x in g.forecast_load_kW]}
 return out

def blend(ref,new,lam,first_slot):
 vals=list(ref['values'])
 for i in range(first_slot-1,144): vals[i]=lam*float(new['values'][i])+(1-lam)*float(ref['values'][i])
 return {'forecast_id':f"B1B:{new['forecast_id']}:{digest([lam,ref['forecast_id'],first_slot])[:16]}", 'known_at':new['known_at'],'values':vals,'interpolation':'PV_HOURLY_LINEAR_CAUSAL_BOUNDARY_V1','boundary_mode':'B1B_BLEND_AFTER_A4'}
class Hist:
 def __init__(self):self.h={6:[],12:[],18:[]}
 def lambdas(self):
  out={}
  for s in (6,12,18):
   sel=self.h[s][-28:]; n=len(sel)
   if n<14: out[s]=(1.,None,None,sel,'FALLBACK_TO_B1A_INSUFFICIENT_HISTORY')
   else:
    en=sum(x['L_new'] for x in sel)/n; er=sum(x['L_ref'] for x in sel)/n
    out[s]=(1. if en+er<=1e-12 else min(max(er/(en+er),0.),1.),en,er,sel,'FALLBACK_TO_B1A_DEGENERATE_ZERO_LOSS' if en+er<=1e-12 else 'NONE')
  return out
 def record(self,day,legal,refs,actual):
  for s,first in ((6,37),(12,73),(18,109)):
   slots=list(range(first,145))
   self.h[s].append({'date':day,'L_new':sum(abs(float(legal[s]['values'][t-1])-float(actual[t-1]['pv_kwh'])) for t in slots)/len(slots),'L_ref':sum(abs(float(refs[s]['values'][t-1])-float(actual[t-1]['pv_kwh'])) for t in slots)/len(slots)})

def legal_day(vmap,day):
 pv={};prefix=[]
 for st in (0,6,12,18):
  x=stage_pv(vmap,day,st,prefix);pv[st]=x;prefix=x['values'][:(st+6)*6]
 return pv

def build_feb1(actuals,vmap):
 hist=Hist(); eff_feb=None; ledger=[]
 d=date(2025,1,2)
 while d<=date(2025,2,1):
  day=d.isoformat(); legal=legal_day(vmap,day); lams=hist.lambdas(); eff={0:legal[0]};refs={}
  for s,first in ((6,37),(12,73),(18,109)):
   refs[s]=eff[{6:0,12:6,18:12}[s]]
   lam,en,er,sel,fb=lams[s]; eff[s]=blend(refs[s],legal[s],lam,first)
   if day=='2025-02-01': ledger.append({'date':day,'stage':s,'lambda':lam,'e_new':en,'e_ref':er,'valid_history_count':len(sel),'fallback_status':fb})
  if day=='2025-02-01': eff_feb=eff
  hist.record(day,legal,refs,actuals[day]); d+=timedelta(days=1)
 return eff_feb,ledger

release=jload(AUTH/'Q3_B1B_CONTROLLER_RELEASE_R5_5.json')
cfg=build_formal_config('B1A')
cfg['strategy_id']='B1B';cfg['pv_vintage_policy']='BLENDED_TRUST_WITH_FROZEN_CAUSAL_LAMBDA';cfg['formal_release']={'status':'RELEASED','authority':release['authority'],'source_hash':sha(AUTH/'Q3_B1B_CONTROLLER_RELEASE_R5_5.json'),'release_id':release['release_id'],'scope':'FORMAL_334D_B1B_PRIMARY'}
actuals=load_actuals(INPUTS/'attachment2.xlsx')
prices=[r['price_yuan_per_kwh'] for r in load_tariff(INPUTS/'attachment1.xlsx')]
vint=load_vintages(INPUTS/'attachment3.xlsx');vmap={x['issue_time']:x for x in vint};loads=derive_loads()
eff,lambda_rows=build_feb1(actuals,vmap)
initial_hash=digest({'protocol':'Q3_B1B_FORMAL334_CONSECUTIVE_STATE_R5_5','strategy':'B1B','date':'2025-02-01','initial_soc_kWh':6000.,'release_id':release['release_id']})
run=solve_q3_day(date='2025-02-01',load_forecast_provider=loads['2025-02-01'],pv_vintage_provider=eff,update_stages=[0,6,12,18],initial_soc=6000.,actual_rows=actuals['2025-02-01'],prices=prices,config=cfg,initial_state_hash=initial_hash,planner=make_formal_lp_planner(cfg))
val=validate_formal_run(run)
ref_daily=pd.read_csv(AUTH/'Q3_FROZEN_FEB1_DAILY_REFERENCE.csv').iloc[0]
ref_trace=pd.read_csv(AUTH/'Q3_FROZEN_FEB1_TRACE_REFERENCE.csv').reset_index(drop=True)
ref_lambda=pd.read_csv(AUTH/'Q3_FROZEN_FEB1_LAMBDA_REFERENCE.csv').sort_values('stage').reset_index(drop=True)
cols=['q','actual_L','actual_S','c_ref','d_ref','c','d','e_before','e_after','r','w','v','price','cost_emergency']
maxdiff={c:max(abs(float(a)-float(b)) for a,b in zip([x[c] for x in run['trace']],ref_trace[c])) for c in cols}
lam_cur=pd.DataFrame(lambda_rows).sort_values('stage').reset_index(drop=True)
lam_diff=max(abs(float(a)-float(b)) for a,b in zip(lam_cur['lambda'],ref_lambda['lambda']))
m=val['metrics']
deltas={
 'cost':float(m['total_cost_yuan']-float(ref_daily['B1B_total_cost'])),
 'emergency_kwh':float(m['emergency_energy_kwh']-float(ref_daily['B1B_emergency_kwh'])),
 'terminal_soc':float(m['terminal_soc_kwh']-float(ref_daily['B1B_terminal_soc']))}
status='PASS' if val['status']=='PASS' and max(maxdiff.values())<=1e-9 and lam_diff<=1e-12 and max(abs(x) for x in deltas.values())<=1e-9 else 'FAIL'
res={'schema':'Q3_REPRODUCTION_GATE_R2_STANDALONE','status':status,'validator_status':val['status'],'trace_max_abs_diff':maxdiff,'lambda_max_abs_diff':lam_diff,'scalar_deltas':deltas,'stage_solver':[{'stage':c['stage'],'status':c['solver_status'],'runtime':c['runtime_seconds'],'metadata':c['solver_metadata']} for c in run['stage_calls']]}
(OUT/'reproduction_R2.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,default=str)+'\n')
print(json.dumps({'status':status,'max_trace_diff':max(maxdiff.values()),'lambda_diff':lam_diff,'deltas':deltas},indent=2))
if status!='PASS': raise SystemExit(2)
