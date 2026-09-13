from __future__ import annotations
import json, math, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

N=144; TOL=1e-7; ETA=.9; EMIN=1200.; EMAX=10800.; XMAX=5000/6; E0=6000.; DELTA=1/6
CONTRACT='CUMCM2026_C_Q2_MATH_CONTRACT_R1'; TM='C_R1_RIGHT_ENDPOINT_ORDINAL_EXPORT'
START=pd.Timestamp('2025-02-01'); END=pd.Timestamp('2025-12-31')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def target_ts(day,slot): return pd.Timestamp(day)+pd.Timedelta(minutes=10*int(slot))
def savej(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x: x.item() if isinstance(x,np.generic) else str(x))+'\n',encoding='utf-8')

def read_actual(root):
    p=root/'inputs'/'附件2.xlsx'
    L=pd.read_excel(p,sheet_name='小区负载',header=0); S=pd.read_excel(p,sheet_name='光伏发电实际功率',header=0)
    dates=pd.to_datetime(L.iloc[:,0]).dt.normalize(); load=L.iloc[:,1:145].to_numpy(float); pv=S.iloc[:,1:145].to_numpy(float)
    tariff=pd.read_excel(root/'inputs'/'附件1.xlsx',header=0).iloc[:N,1].to_numpy(float)
    return dates,load,pv,tariff

def check_q80(root,qdf,annual_resid):
    jan=pd.read_csv(root/'inputs'/'january_final_residuals.csv')
    by={s:[] for s in range(1,N+1)}
    for x in jan.itertuples(index=False): by[int(x.slot)].append((target_ts(x.date,int(x.slot)),float(x.net_residual)))
    for x in annual_resid.itertuples(index=False): by[int(x.slot)].append((pd.Timestamp(x.target_ts),float(x.net_residual_kW)))
    for s in by: by[s].sort()
    max_qdiff=0.; bad=0; max_n=0
    for x in qdf.itertuples(index=False):
        d=pd.Timestamp(x.date); elig=[(ts,v) for ts,v in by[int(x.slot)] if ts<d]; vals=sorted(v for _,v in elig)
        n=len(vals); k=math.ceil(.8*n); q=vals[k-1]; latest=max(ts for ts,_ in elig)
        max_qdiff=max(max_qdiff,abs(q-float(x.q80_residual_kW))); max_n=max(max_n,abs(n-int(x.n_history)))
        if k!=int(x.k_rank) or latest!=pd.Timestamp(x.latest_residual_target_ts) or not latest<d: bad+=1
    return {'pass':bad==0 and max_qdiff<=1e-10 and max_n==0,'max_q80_abs_diff_kW':max_qdiff,'n_mismatch_max':max_n,'bad_rows':bad}

def emergency_intervals(df):
    rows=[]
    for day,g in df.groupby('date',sort=True):
        slots=g.loc[g.emergency_kWh>TOL,'slot'].astype(int).tolist()
        if not slots: continue
        start=prev=slots[0]
        def emit(a,b):
            def left(s):
                m=10*(s-1); return f'{m//60:02d}:{m%60:02d}'
            def right(s):
                m=10*s
                if m==1440:return '24:00'
                return f'{m//60:02d}:{m%60:02d}'
            sub=g[(g.slot>=a)&(g.slot<=b)]
            rows.append({'date':day,'start_slot':a,'end_slot':b,'start_time':left(a),'end_time':right(b),
                         'emergency_kWh':float(sub.emergency_kWh.sum()),'emergency_cost_yuan':float(sub.emergency_cost_yuan.sum())})
        for s in slots[1:]:
            if s==prev+1: prev=s
            else: emit(start,prev); start=prev=s
        emit(start,prev)
    return pd.DataFrame(rows)

def validate_policy(root,tag,policy,actual_dates,actual_load,actual_pv,tariff,forecast,q80):
    df=pd.read_csv(root/'results'/f'{tag}_slot_replay.csv'); plan=pd.read_csv(root/'results'/f'{tag}_day_ahead_plan.csv')
    daily=pd.read_csv(root/'results'/f'{tag}_daily_metrics.csv'); summ=json.loads((root/'results'/f'{tag}_annual_summary.json').read_text())
    checks={}; details={}
    checks['V01_contract']=set(df.contract_id)=={CONTRACT} and set(plan.contract_id)=={CONTRACT}
    checks['V02_time_mapping']=set(df.time_mapping_version)=={TM} and len(df)==334*N and df.groupby('date').size().eq(N).all()
    ts_expected=pd.to_datetime(df['date'])+pd.to_timedelta(df['slot']*10,unit='m')
    checks['V02_target_ts']=bool((pd.to_datetime(df.target_ts).values==ts_expected.values).all())
    price_expected=np.tile(tariff,334)
    checks['V03_tariff']=float(np.max(np.abs(df.tariff.to_numpy(float)-price_expected)))<=1e-12
    checks['V04_q_immutability']=float(np.max(np.abs(df.q_DA_kWh.to_numpy(float)-plan.q_DA_kWh.to_numpy(float))))<=1e-10
    f=forecast.sort_values(['date','slot']).reset_index(drop=True); qq=q80.sort_values(['date','slot']).reset_index(drop=True)
    checks['V05_forecast_identity']=float(np.max(np.abs(df.forecast_load_kWh.to_numpy(float)-f.forecast_load_kW.to_numpy(float)*DELTA)))<=1e-9 and float(np.max(np.abs(df.forecast_pv_kWh.to_numpy(float)-f.forecast_pv_kW.to_numpy(float)*DELTA)))<=1e-9
    checks['V05_forecast_causality']=bool((pd.to_datetime(f.load_source_target_ts)<pd.to_datetime(f.decision_time)).all() and (pd.to_datetime(f.pv_max_training_target_ts)<pd.to_datetime(f.decision_time)).all() and int(f.future_count.sum())==0 and int(f.equality_cutoff_count.sum())==0)
    checks['V24_margin_identity']=float(np.max(np.abs(df.reserve_margin_kWh.to_numpy(float)-qq.reserve_margin_kWh.to_numpy(float))))<=1e-10
    idx={pd.Timestamp(d).date().isoformat():i for i,d in enumerate(actual_dates)}
    expL=[]; expS=[]
    for day in pd.date_range(START,END):
        i=idx[day.date().isoformat()]; expL.extend(actual_load[i]*DELTA); expS.extend(actual_pv[i]*DELTA)
    expL=np.asarray(expL); expS=np.asarray(expS)
    checks['actual_attachment_identity']=float(np.max(np.abs(df.actual_load_kWh.to_numpy(float)-expL)))<=1e-10 and float(np.max(np.abs(df.actual_pv_kWh.to_numpy(float)-expS)))<=1e-10
    B=df.q_DA_kWh.to_numpy(float)+df.actual_pv_kWh.to_numpy(float)-df.actual_load_kWh.to_numpy(float)
    c=df.charge_exec_kWh.to_numpy(float); d=df.discharge_exec_kWh.to_numpy(float); r=df.emergency_kWh.to_numpy(float)
    w=df.paid_unused_normal_kWh.to_numpy(float); v=df.pv_curtailment_kWh.to_numpy(float)
    pos=B>=-TOL; neg=B<-TOL
    checks['V07_direction']=bool((d[pos]<=TOL).all() and (r[B>=0]<=TOL).all() and (c[neg]<=TOL).all() and ((w+v)[neg]<=TOL).all())
    expected_r=np.maximum(-B-d,0.0)
    checks['V08_emergency_last']=float(np.max(np.abs(r-expected_r)))<=TOL and bool((c[r>TOL]<=TOL).all() and ((w+v)[r>TOL]<=TOL).all())
    checks['V09_no_simul_cd']=bool((np.minimum(c,d)<=TOL).all())
    bal=df.q_DA_kWh.to_numpy(float)-w+r+df.actual_pv_kWh.to_numpy(float)+d-df.actual_load_kWh.to_numpy(float)-c-v
    checks['V10_balance']=float(np.max(np.abs(bal)))<=TOL
    soc=[]; cur=E0; maxrec=0.; bridge_bad=0
    for x in df.itertuples(index=False):
        if abs(float(x.SOC_start_kWh)-cur)>TOL: bridge_bad+=1
        nxt=cur+ETA*float(x.charge_exec_kWh)-float(x.discharge_exec_kWh)/ETA
        maxrec=max(maxrec,abs(nxt-float(x.SOC_end_kWh))); soc.append(nxt); cur=nxt
    soc=np.asarray(soc)
    checks['V11_soc_recursion']=maxrec<=TOL; checks['V12_soc_bounds']=bool(soc.min()>=EMIN-TOL and soc.max()<=EMAX+TOL)
    checks['V13_power_bounds']=bool((c>=-TOL).all() and (d>=-TOL).all() and (c<=XMAX+TOL).all() and (d<=XMAX+TOL).all())
    checks['V14_cross_day']=bridge_bad==0
    checks['V15_feb1_bridge']=abs(float(df.iloc[0].SOC_start_kWh)-E0)<=TOL
    checks['V16_free_bounded_year_end']=EMIN-TOL<=float(df.iloc[-1].SOC_end_kWh)<=EMAX+TOL
    checks['V18_efficiency_primary']=maxrec<=TOL
    normal=float(np.sum(price_expected*df.q_DA_kWh.to_numpy(float))); emerg=float(np.sum(5*price_expected*r)); total=normal+emerg
    checks['V20_cost_recompute']=abs(total-float(summ['realized_total_cost_yuan']))<=1e-6
    checks['V21_decomposition']=abs(normal-float(summ['normal_cost_yuan']))<=1e-6 and abs(emerg-float(summ['emergency_cost_yuan']))<=1e-6
    checks['S1A_bounds']=bool((w>=-TOL).all() and (w<=df.q_DA_kWh.to_numpy(float)+TOL).all() and (v>=-TOL).all() and (v<=df.actual_pv_kWh.to_numpy(float)+TOL).all())
    checks['V25_alpha']=bool(np.allclose(qq.alpha.to_numpy(float),.8,rtol=0,atol=1e-15))
    checks['V26_risk_history']=bool((qq.n_history>0).all() and qq.cutoff_pass.astype(bool).all())
    if tag=='Q80_FIXED':
        cref=df.charge_ref_kWh.to_numpy(float); dref=df.discharge_ref_kWh.to_numpy(float)
        checks['V27_fixed_rule']=bool((c<=cref+TOL).all() and (d<=dref+TOL).all())
        clipc=df.clipped_charge_kWh.to_numpy(float); clipd=df.clipped_discharge_kWh.to_numpy(float)
        checks['V28_clipping']=float(np.max(np.abs(clipc-(cref-c))))<=TOL and float(np.max(np.abs(clipd-(dref-d))))<=TOL
    else:
        checks['V27_fixed_rule']=True; checks['V28_clipping']=True
    checks['V29_fallback']=int(df.fallback_used.sum())==0 and int(summ['fallback_count'])==0
    checks['V30_full_leakage']=checks['V05_forecast_causality'] and bool((pd.to_datetime(qq.latest_residual_target_ts)<pd.to_datetime(qq.decision_time)).all())
    checks['V31_coverage']=len(df)==48096 and len(daily)==334 and df.groupby('date').slot.nunique().eq(144).all()
    required={'2025-03-20','2025-06-21','2025-09-23','2025-12-21'}
    checks['V33_required_dates']=required.issubset(set(df.date))
    checks['Feb01_fixed_anchor']=True
    if tag=='Q80_FIXED':
        feb=df[df.date=='2025-02-01']; ft=float(feb.normal_cost_yuan.sum()+feb.emergency_cost_yuan.sum()); fek=float(feb.emergency_kWh.sum()); fs=int((feb.emergency_kWh>TOL).sum())
        checks['Feb01_fixed_anchor']=abs(ft-23986.491044337)<=1e-6 and abs(fek-80.457724342)<=1e-6 and fs==5
        details['feb01']={'total_cost':ft,'emergency_kWh':fek,'emergency_slots':fs}
    checks['V22_forecast_provenance_superseded']=bool(set(f.load_model)=={'L2_LAG7'} and set(f.pv_model)=={'P3_ETS_HW_STRICT_CAUSAL'})
    expected_input_hashes={
        '附件1.xlsx':'66b87134f5ecccd68184d3539bb1293ef039f9e0fdd955a589b9bfa7f227c377',
        '附件2.xlsx':'2e95fd446bfafa0d8c59577b5c2e2ea8b3f1def20dde54a3062556f4da9b4c72',
        'january_final_residuals.csv':'0f10e14df142021ce179adfe0b11e7dbb1b99c5eb13841571d130b331e19b8b2',
        'feb01_forecast_corrected_anchor.csv':'bc5334f23d0a83761a5c7a7a1b1ab65b5ac7ef89187705c80e79f79a87212a51',
    }
    actual_input_hashes={name:sha(root/'inputs'/name) for name in expected_input_hashes}
    checks['V34_source_hashes']=actual_input_hashes==expected_input_hashes
    details['input_hashes']={'expected':expected_input_hashes,'actual':actual_input_hashes}
    details['not_in_task']=['V17 terminal sensitivities','V19 efficiency alternative','V23 offline challenger audit']
    details.update({'max_balance_abs':float(np.max(np.abs(bal))),'max_soc_recursion_abs':maxrec,'bridge_mismatch_count':bridge_bad,
                    'recomputed_normal_cost':normal,'recomputed_emergency_cost':emerg,'recomputed_total_cost':total,
                    'soc_end':float(soc[-1]),'soc_min':float(soc.min()),'soc_max':float(soc.max())})
    intervals=emergency_intervals(df); intervals.to_csv(root/'results'/f'{tag}_emergency_intervals.csv',index=False)
    hard_pass=all(checks.values())
    return {'policy_id':policy,'all_applicable_hard_pass':hard_pass,'checks':checks,'details':details}

def block_bootstrap(root):
    p=pd.read_csv(root/'results'/'daily_paired_fixed_vs_p2.csv'); x=p.cost_diff_p2_minus_fixed_yuan.to_numpy(float); n=len(x); block=7; rng=np.random.default_rng(20260912); means=[]
    starts=np.arange(0,n-block+1)
    for _ in range(5000):
        vals=[]
        while len(vals)<n:
            s=int(rng.choice(starts)); vals.extend(x[s:s+block])
        means.append(float(np.mean(vals[:n])))
    lo,hi=np.quantile(means,[.025,.975]); out={'n_days':n,'block_days':block,'bootstrap_reps':5000,'seed':20260912,
      'mean_daily_cost_diff_p2_minus_fixed_yuan':float(np.mean(x)),'median_daily_diff_yuan':float(np.median(x)),
      'fraction_days_p2_cheaper':float(np.mean(x<0)),'mean_daily_diff_95pct_block_bootstrap':[float(lo),float(hi)],
      'annual_total_cost_diff_p2_minus_fixed_yuan':float(np.sum(x))}
    savej(root/'results'/'paired_stability.json',out); return out

def main():
    root=Path(__file__).resolve().parents[1]
    actual_dates,L,S,tariff=read_actual(root)
    forecast=pd.read_csv(root/'results'/'annual_forecast.csv'); q80=pd.read_csv(root/'results'/'q80_margin_audit.csv'); resid=pd.read_csv(root/'results'/'annual_forecast_residuals.csv')
    qcheck=check_q80(root,q80,resid)
    fixed=validate_policy(root,'Q80_FIXED','Q80_FIXED_SAFETY_YEAR',actual_dates,L,S,tariff,forecast,q80)
    p2=validate_policy(root,'Q80_P2_CAUSAL','ANALYTIC_Q80_RESIDUAL_RESERVE_PLUS_CAUSAL_INTRADAY',actual_dates,L,S,tariff,forecast,q80)
    stability=block_bootstrap(root)
    result={'validator_verdict':'PASS_FOR_XXT_REVIEW' if qcheck['pass'] and fixed['all_applicable_hard_pass'] and p2['all_applicable_hard_pass'] else 'FAIL_REOPEN_IMPLEMENTATION',
            'q80_independent_recompute':qcheck,'fixed':fixed,'p2':p2,'paired_stability':stability,
            'spec_conflict_note':'XXT_Q2_VALIDATOR_SPEC_R1 V22 names an older PREDECLARED_BASELINE PV=TRAILING7_MEAN. ANNUAL_COMMON_CONTRACT_R1 and Q2_FORECAST_CAUSAL_REVIEW_R2 supersede it for this run with corrected L2_P3. Validator evaluates provenance against the newer R1 annual contract.',
            'freeze_scope_note':'This assigned XXT annual task does not execute V17 terminal sensitivities, V19 efficiency alternative, or V23 offline challenger audit; those remain downstream Q2 Freeze requirements.'}
    savej(root/'results'/'annual_validator.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2,default=lambda x: x.item() if isinstance(x,np.generic) else str(x)))
    if result['validator_verdict']!='PASS_FOR_XXT_REVIEW': raise SystemExit(2)
if __name__=='__main__': main()
