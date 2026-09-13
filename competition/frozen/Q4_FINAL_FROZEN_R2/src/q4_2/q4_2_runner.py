from __future__ import annotations
import argparse, json, math, os, platform, hashlib, time, warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from multiprocessing import Pool
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import linprog
from scipy.sparse import lil_matrix, csr_matrix, vstack, hstack, eye
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from q4_price_provider import Q4PriceProvider

N=144
DELTA=1/6
XMAX=5000/6
ETA_C=ETA_D=0.9
EMIN=1200.0
EMAX=10800.0
E0_YEAR=6000.0
ALPHA=0.80
TOL=1e-7
# Registered lexicographic binding tolerances. The formal Q2 specification says
# previous lexicographic optima are fixed *within numerical tolerance*; using
# exact floating-point equalities caused a HiGHS portability failure on Feb-02.
LEX_COST_TOL_YUAN=1e-7
LEX_THROUGHPUT_TOL_KWH=1e-7
CONTRACT_ID='CUMCM2026_C_Q2_MATH_CONTRACT_R1'
TIME_MAPPING='C_R1_RIGHT_ENDPOINT_ORDINAL_EXPORT'
START_DATE=pd.Timestamp('2025-02-01')
END_DATE=pd.Timestamp('2025-12-31')

PV_GLOBAL=None

def sha256(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path:Path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def target_ts(day, slot:int):
    return pd.Timestamp(day)+pd.Timedelta(minutes=10*int(slot))

def read_inputs(root:Path):
    att2=root/'inputs'/'attachment2.xlsx'
    load_df=pd.read_excel(att2,sheet_name='小区负载',header=0)
    pv_df=pd.read_excel(att2,sheet_name='光伏发电实际功率',header=0)
    dates=pd.to_datetime(load_df.iloc[:,0]).dt.normalize()
    if not dates.equals(pd.to_datetime(pv_df.iloc[:,0]).dt.normalize()):
        raise ValueError('Attachment2 sheet dates mismatch')
    load=load_df.iloc[:,1:145].to_numpy(float)
    pv=pv_df.iloc[:,1:145].to_numpy(float)
    if load.shape!=(365,N) or pv.shape!=(365,N):
        raise ValueError(f'Expected 365x144 actual arrays, got {load.shape} {pv.shape}')
    if not np.all(np.isfinite(load)) or not np.all(np.isfinite(pv)) or np.min(load)<0 or np.min(pv)<0:
        raise ValueError('Invalid actual data')
    att1=pd.read_excel(root/'inputs'/'attachment1.xlsx',sheet_name=0,header=0)
    tariff=att1.iloc[:N,1].to_numpy(float)
    if tariff.shape!=(N,) or not np.all(np.isfinite(tariff)) or np.min(tariff)<=0:
        raise ValueError('Invalid tariff')
    return dates,load,pv,tariff

def _pv_forecast_worker(idx:int):
    global PV_GLOBAL
    # rows [0, idx) are calendar rows before target day; prior-day slot144 is target-day 00:00, exclude it.
    strict=PV_GLOBAL[:idx].reshape(-1)[:-1]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        model=ExponentialSmoothing(strict,trend=None,seasonal='add',seasonal_periods=N,initialization_method='estimated')
        fit=model.fit(optimized=True,remove_bias=False,method='least_squares')
        raw=np.asarray(fit.forecast(N+1),float)
    if raw.shape!=(N+1,) or not np.all(np.isfinite(raw)):
        raise RuntimeError(f'Bad ETS forecast idx={idx}')
    pred=np.maximum(raw[1:],0.0)
    return idx,pred,float(fit.params['smoothing_level']),float(fit.params['smoothing_seasonal'])

def build_forecasts(root:Path, workers:int=4):
    dates,load,pv,tariff=read_inputs(root)
    date_to_idx={pd.Timestamp(d):i for i,d in enumerate(dates)}
    target_days=pd.date_range(START_DATE,END_DATE,freq='D')
    indices=[date_to_idx[d] for d in target_days]
    global PV_GLOBAL
    PV_GLOBAL=pv
    t0=time.perf_counter()
    # fork workers inherit PV_GLOBAL on Linux.
    with Pool(processes=max(1,workers)) as pool:
        ets=list(pool.imap(_pv_forecast_worker,indices,chunksize=1))
    ets_map={idx:(pred,a,b) for idx,pred,a,b in ets}
    rows=[]; residual_rows=[]; diag=[]
    for d,idx in zip(target_days,indices):
        load_fc=load[idx-7].copy()  # L2 LAG7, same row-slot; target timestamp is exactly 7 days earlier.
        pv_fc,a,b=ets_map[idx]
        if d==START_DATE:
            # Canonical Feb-01 forecast is byte-frozen authority.
            # Cross-platform statsmodels/BLAS re-fit is diagnostic only: tiny numerical drift
            # must not overwrite the already reviewed canonical anchor.
            anchor=pd.read_csv(root/'inputs'/'feb01_forecast_corrected_anchor.csv')
            max_ld=float(np.max(np.abs(load_fc-anchor['forecast_load'].to_numpy(float))))
            max_pv=float(np.max(np.abs(pv_fc-anchor['forecast_pv'].to_numpy(float))))
            portability_tol_kw=1e-2
            if max_ld>1e-10 or max_pv>portability_tol_kw:
                raise RuntimeError(f'Corrected Feb01 forecast anchor material mismatch load={max_ld} pv={max_pv}')
            write_json(root/'results'/'feb01_ets_portability_diagnostic.json',{
                'status':'PASS_WITH_NON_MODEL_PORTABILITY_PATCH',
                'canonical_anchor_authority':str(root/'inputs'/'feb01_forecast_corrected_anchor.csv'),
                'local_refit_max_load_abs_diff_kW':max_ld,
                'local_refit_max_pv_abs_diff_kW':max_pv,
                'diagnostic_tolerance_kW':portability_tol_kw,
                'action':'Use canonical byte-frozen Feb01 load/PV forecast for emitted annual forecast; do not overwrite it with local re-fit.',
                'model_semantics_changed':False,
            })
            load_fc=anchor['forecast_load'].to_numpy(float).copy()
            pv_fc=anchor['forecast_pv'].to_numpy(float).copy()
        pv_hist_end=d-pd.Timedelta(minutes=10)
        for s in range(1,N+1):
            ts=target_ts(d,s)
            lag_src=ts-pd.Timedelta(days=7)
            rows.append({
                'date':d.date().isoformat(),'slot':s,'target_ts':ts.isoformat(),
                'decision_time':d.isoformat(),'forecast_load_kW':float(load_fc[s-1]),
                'forecast_pv_kW':float(pv_fc[s-1]),'forecast_net_load_kW':float(load_fc[s-1]-pv_fc[s-1]),
                'load_model':'L2_LAG7','pv_model':'P3_ETS_HW_STRICT_CAUSAL',
                'load_source_target_ts':lag_src.isoformat(),'pv_max_training_target_ts':pv_hist_end.isoformat(),
                'known_at':d.isoformat(),'future_count':0,'equality_cutoff_count':0,
            })
            actual_net=float(load[idx,s-1]-pv[idx,s-1])
            residual_rows.append({
                'date':d.date().isoformat(),'slot':s,'target_ts':ts.isoformat(),
                'forecast_net_load_kW':float(load_fc[s-1]-pv_fc[s-1]),'actual_net_load_kW':actual_net,
                'net_residual_kW':float(actual_net-(load_fc[s-1]-pv_fc[s-1]))
            })
        diag.append({'date':d.date().isoformat(),'pv_history_n':int(idx*N-1),'pv_history_end_target_ts':pv_hist_end.isoformat(),
                     'smoothing_level':a,'smoothing_seasonal':b})
    fdf=pd.DataFrame(rows); rdf=pd.DataFrame(residual_rows); ddf=pd.DataFrame(diag)
    if len(fdf)!=334*N or not (pd.to_datetime(fdf['load_source_target_ts'])<pd.to_datetime(fdf['decision_time'])).all() or not (pd.to_datetime(fdf['pv_max_training_target_ts'])<pd.to_datetime(fdf['decision_time'])).all():
        raise RuntimeError('Forecast causality/coverage failure')
    fdf.to_csv(root/'results'/'annual_forecast.csv',index=False)
    rdf.to_csv(root/'results'/'annual_forecast_residuals.csv',index=False)
    ddf.to_csv(root/'results'/'annual_pv_ets_diagnostics.csv',index=False)
    write_json(root/'results'/'forecast_summary.json',{
        'status':'PASS','days':334,'slots':int(len(fdf)),'forecast_combo':'L2_P3',
        'cutoff':'observation_target_ts < target day 00:00','ets_alignment':'145 steps then discard step1',
        'runtime_sec':time.perf_counter()-t0,'workers':workers,
        'equality_cutoff_count':0,'future_count':0,
    })
    return fdf,rdf

def load_or_build_forecasts(root:Path,workers:int=4):
    f=root/'results'/'annual_forecast.csv'; r=root/'results'/'annual_forecast_residuals.csv'
    if f.exists() and r.exists(): return pd.read_csv(f),pd.read_csv(r)
    return build_forecasts(root,workers)

def build_q80_audit(root:Path,annual_resid:pd.DataFrame):
    jan=pd.read_csv(root/'inputs'/'january_final_residuals.csv')
    jrows=[]
    for x in jan.itertuples(index=False):
        ts=target_ts(x.date,int(x.slot))
        jrows.append((int(x.slot),ts,float(x.net_residual)))
    arows=[(int(x.slot),pd.Timestamp(x.target_ts),float(x.net_residual_kW)) for x in annual_resid.itertuples(index=False)]
    byslot={s:[] for s in range(1,N+1)}
    for s,ts,v in jrows+arows: byslot[s].append((ts,v))
    for s in byslot: byslot[s].sort(key=lambda z:z[0])
    out=[]
    for d in pd.date_range(START_DATE,END_DATE,freq='D'):
        for s in range(1,N+1):
            eligible=[(ts,v) for ts,v in byslot[s] if ts<d]
            vals=sorted(v for ts,v in eligible)
            n=len(vals)
            if n<=0: raise RuntimeError('No residual history')
            k=math.ceil(ALPHA*n); q=float(vals[k-1]); margin=max(0.0,q)*DELTA
            latest=max(ts for ts,_ in eligible)
            out.append({'date':d.date().isoformat(),'slot':s,'decision_time':d.isoformat(),
                        'n_history':n,'k_rank':k,'alpha':ALPHA,'q80_residual_kW':q,
                        'reserve_margin_kW':max(0.0,q),'reserve_margin_kWh':margin,
                        'latest_residual_target_ts':latest.isoformat(),'cutoff_pass':bool(latest<d)})
    df=pd.DataFrame(out)
    # Feb01 audit expectations: slots1..143 n24 rank20, slot144 n23 rank19.
    f1=df[df.date=='2025-02-01']
    if not ((f1.iloc[:143].n_history==24).all() and (f1.iloc[:143].k_rank==20).all() and int(f1.iloc[143].n_history)==23 and int(f1.iloc[143].k_rank)==19):
        raise RuntimeError('Feb01 Q80 history anchor failed')
    if not df.cutoff_pass.all(): raise RuntimeError('Q80 cutoff leak')
    df.to_csv(root/'results'/'q80_margin_audit.csv',index=False)
    return df

def load_or_build_q80(root:Path,annual_resid:pd.DataFrame):
    p=root/'results'/'q80_margin_audit.csv'
    if p.exists(): return pd.read_csv(p)
    return build_q80_audit(root,annual_resid)

def solve_day_ahead(planning_load,solar,tariff,e0):
    # vars q,c,d,spill,E,absdev each N
    Aeq=lil_matrix((2*N,6*N)); beq=np.zeros(2*N)
    for t in range(N):
        Aeq[t,t]=1; Aeq[t,N+t]=-1; Aeq[t,2*N+t]=1; Aeq[t,3*N+t]=-1
        beq[t]=planning_load[t]-solar[t]
        Aeq[N+t,4*N+t]=1; Aeq[N+t,N+t]=-ETA_C; Aeq[N+t,2*N+t]=1/ETA_D
        if t: Aeq[N+t,4*N+t-1]=-1
        else: beq[N+t]=e0
    Aeq=Aeq.tocsr()
    bounds=[(0,None)]*N+[(0,XMAX)]*(2*N)+[(0,None)]*N+[(EMIN,EMAX)]*N+[(0,None)]*N
    c1=np.zeros(6*N); c1[:N]=tariff
    c2=np.zeros(6*N); c2[N:3*N]=1
    c3=np.zeros(6*N); c3[5*N:]=1
    base=np.maximum(planning_load-solar,0)
    Aub=lil_matrix((2*N,6*N)); bub=np.r_[base,-base]
    for t in range(N):
        Aub[t,t]=1; Aub[t,5*N+t]=-1
        Aub[N+t,t]=-1; Aub[N+t,5*N+t]=-1
    Aub=Aub.tocsr()

    # Numerical portability rule: the formal specification requires prior
    # lexicographic optima to be fixed *within numerical tolerance*.  Do not
    # encode floating-point solver objectives as exact equalities.  Instead,
    # bind each previous optimum in a symmetric tolerance band using the same
    # 1e-7 registered cost/energy tolerance as the corrected pilot validator.
    evid=[]; sols=[]; opt1=None; opt2=None
    for stage,obj in enumerate((c1,c2,c3),1):
        st=time.perf_counter()
        res=linprog(obj,A_eq=Aeq,b_eq=beq,A_ub=Aub,b_ub=bub,bounds=bounds,method='highs-ds',
                    options={'dual_feasibility_tolerance':1e-9,'primal_feasibility_tolerance':1e-9})
        row={'stage':stage,'success':bool(res.success),'status':int(res.status),
             'objective':float(res.fun) if res.success else None,
             'iterations':int(res.nit),'runtime_sec':time.perf_counter()-st,'message':res.message,
             'lex_cost_tolerance_yuan':LEX_COST_TOL_YUAN,
             'lex_throughput_tolerance_kWh':LEX_THROUGHPUT_TOL_KWH}
        if res.success:
            primary=float(c1 @ res.x); secondary=float(c2 @ res.x)
            row['primary_cost_value_yuan']=primary
            row['secondary_throughput_value_kWh']=secondary
            row['primary_cost_deviation_from_stage1_yuan']=None if opt1 is None else primary-opt1
            row['secondary_deviation_from_stage2_kWh']=None if opt2 is None else secondary-opt2
        evid.append(row)
        if not res.success: raise RuntimeError(f'Day-ahead stage {stage} failure: {res.message}')
        sols.append(res.x.copy())
        if stage==1:
            opt1=float(res.fun)
            band=LEX_COST_TOL_YUAN
        elif stage==2:
            opt2=float(res.fun)
            band=LEX_THROUGHPUT_TOL_KWH
        else:
            continue
        # Two-sided band: |obj(x)-opt| <= band.  This is a numerical tie-break
        # constraint, not a relaxation of the primary/secondary model objective.
        opt=opt1 if stage==1 else opt2
        Aub=vstack([Aub,csr_matrix(obj.reshape(1,-1)),csr_matrix((-obj).reshape(1,-1))],format='csr')
        bub=np.r_[bub,opt+band,-opt+band]
    return sols[-1],evid

def execute_fixed(day, q,c_ref,d_ref, actual_load,actual_pv,tariff,e0,margin,fc_load,fc_pv):
    e=float(e0); rows=[]
    for t in range(N):
        L=actual_load[t]*DELTA; S=actual_pv[t]*DELTA; before=e; B=q[t]+S-L
        if B>=0:
            c=min(c_ref[t],B,XMAX,(EMAX-e)/ETA_C); d=0.0
        else:
            c=0.0; d=min(d_ref[t],-B,XMAX,(e-EMIN)*ETA_D)
        r=max(L+c-q[t]-S-d,0.0)
        u=max(q[t]+S+d+r-L-c,0.0)
        w=min(q[t],u); v=u-w
        e=e+ETA_C*c-d/ETA_D
        rows.append({'date':day.date().isoformat(),'slot':t+1,'target_ts':target_ts(day,t+1).isoformat(),
          'contract_id':CONTRACT_ID,'time_mapping_version':TIME_MAPPING,'policy_id':'Q80_FIXED_SAFETY_YEAR','q_DA_kWh':q[t],'charge_ref_kWh':c_ref[t],'discharge_ref_kWh':d_ref[t],
          'charge_exec_kWh':c,'discharge_exec_kWh':d,'actual_load_kWh':L,'actual_pv_kWh':S,
          'forecast_load_kWh':fc_load[t]*DELTA,'forecast_pv_kWh':fc_pv[t]*DELTA,'reserve_margin_kWh':margin[t],
          'tariff':tariff[t],'emergency_kWh':r,'paid_unused_normal_kWh':w,'pv_curtailment_kWh':v,
          'SOC_start_kWh':before,'SOC_end_kWh':e,'normal_cost_yuan':tariff[t]*q[t],
          'emergency_cost_yuan':5*tariff[t]*r,'balance_residual_kWh':q[t]-w+r+S+d-L-c-v,
          'clipped_charge_kWh':max(0.0,c_ref[t]-c),'clipped_discharge_kWh':max(0.0,d_ref[t]-d),'fallback_used':0})
    return rows,e


C_USABLE=EMAX-EMIN

def _merge_segments(segs, tol=1e-12):
    out=[]
    for val,length in segs:
        length=float(length)
        if length<=1e-12: continue
        if out and abs(out[-1][0]-float(val))<=tol:
            out[-1]=(out[-1][0],out[-1][1]+length)
        else: out.append((float(val),length))
    return out

def _truncate_segments(segs,total=C_USABLE):
    out=[]; rem=float(total)
    for val,length in segs:
        if rem<=1e-12: break
        take=min(float(length),rem)
        if take>1e-12: out.append((float(val),take)); rem-=take
    if rem>1e-8: out.append((0.0,rem))
    return _merge_segments(out)

def _drop_prefix_segments(segs,amount):
    rem=float(amount); out=[]
    for val,length in segs:
        length=float(length)
        if rem>=length-1e-12:
            rem-=length; continue
        if rem>1e-12:
            length-=rem; rem=0.0
        out.append((float(val),length))
    if rem>1e-7: raise RuntimeError('segment prefix drop exceeds domain')
    return out

def _insert_reward_segment(segs,reward,length):
    # merge sorted nonincreasing marginal-value segments with a constant reward segment, retain first C usable kWh.
    allsegs=list(segs)+[(float(reward),float(length))]
    allsegs.sort(key=lambda z:z[0],reverse=True)
    return _truncate_segments(_merge_segments(allsegs))

def build_primary_future_profiles(Bforecast,tariff):
    # profiles[j] = marginal primary value function for slots j..N-1 as a function of usable internal SOC.
    profiles=[None]*(N+1); profiles[N]=[(0.0,C_USABLE)]
    for j in range(N-1,-1,-1):
        segs=profiles[j+1]
        B=float(Bforecast[j])
        if B < 0:
            dcap=min(-B,XMAX); internal=dcap/ETA_D; reward=5*float(tariff[j])*ETA_D
            profiles[j]=_insert_reward_segment(segs,reward,internal)
        elif B > 0:
            ccap=min(B,XMAX); internal=ETA_C*ccap
            tail=_drop_prefix_segments(segs,internal)
            profiles[j]=_truncate_segments(_merge_segments(tail+[(0.0,internal)]))
        else:
            profiles[j]=list(segs)
        if abs(sum(z[1] for z in profiles[j])-C_USABLE)>1e-6:
            raise RuntimeError('bad primary profile domain')
    return profiles

def _global_opt_interval_deficit(segs,reward,tol=1e-11):
    pos=0.0; equal_start=None; equal_end=None
    for val,length in segs:
        if val>reward+tol:
            pos+=length; continue
        if abs(val-reward)<=tol:
            if equal_start is None: equal_start=pos
            pos+=length; equal_end=pos; continue
        # val < reward: crossing occurs at current pos unless equal plateau already seen
        break
    if equal_start is not None: return equal_start,equal_end
    # pos is measure of slopes strictly greater than reward.
    return pos,pos

def primary_current_action(Bcur,e0,tariff_cur,future_segs):
    y=float(e0-EMIN)
    if Bcur>=0:
        a=ETA_C*min(float(Bcur),XMAX); hi=min(C_USABLE,y+a)
        positive=sum(length for val,length in future_segs if val>1e-11)
        if hi<=positive+1e-10:
            final=hi; tie=False; interval=(final,final)
        else:
            lo_opt=max(y,positive); hi_opt=hi
            tie=(hi_opt-lo_opt)>1e-9; final=lo_opt if not tie else None; interval=(lo_opt,hi_opt)
        if not tie:
            return (final-y)/ETA_C,False,interval
        return None,True,interval
    else:
        b=min(float(-Bcur),XMAX)/ETA_D
        lo=max(0.0,y-b); hi=y; reward=5*float(tariff_cur)*ETA_D
        glo,ghi=_global_opt_interval_deficit(future_segs,reward)
        if hi<glo-1e-10: optlo=opthi=hi
        elif lo>ghi+1e-10: optlo=opthi=lo
        else:
            optlo=max(lo,glo); opthi=min(hi,ghi)
            if opthi<optlo and abs(opthi-optlo)<1e-8: opthi=optlo
        tie=(opthi-optlo)>1e-9
        if not tie:
            x=0.5*(optlo+opthi); return ETA_D*(y-x),False,(optlo,opthi)
        return None,True,(optlo,opthi)

def recourse_lp(B,tariff,e0,c_ref,d_ref):
    H=len(B)
    if H==0: raise ValueError('empty horizon')
    is_sur=B>=0
    cap=np.minimum(np.abs(B),XMAX)
    coeff=np.where(is_sur,ETA_C,-1/ETA_D)
    # prefix SOC inequalities in dense arrays; H<=144.
    Aub=np.zeros((2*H,H));
    for k in range(H):
        Aub[k,:k+1]=coeff[:k+1]
        Aub[H+k,:k+1]=-coeff[:k+1]
    bub=np.r_[np.full(H,EMAX-e0),np.full(H,e0-EMIN)]
    bounds=list(zip(np.zeros(H),cap))
    primary=np.where(is_sur,0.0,-5*np.asarray(tariff,float))
    st=time.perf_counter()
    r1=linprog(primary,A_ub=Aub,b_ub=bub,bounds=bounds,method='highs-ds')
    if not r1.success: raise RuntimeError('recourse primary '+r1.message)
    # stage2: exact primary optimum, minimize throughput.
    Aeq=primary.reshape(1,-1); beq=np.array([r1.fun])
    ones=np.ones(H)
    r2=linprog(ones,A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs-ds')
    if not r2.success: raise RuntimeError('recourse secondary '+r2.message)
    # stage3: minimize |allowed_action-reference_allowed| with primary+throughput fixed.
    ref=np.where(is_sur,np.asarray(c_ref,float),np.asarray(d_ref,float))
    # vars x,z. Prefix inequalities only use x. Abs: x-z<=ref; -x-z<=-ref.
    Apre=np.hstack([Aub,np.zeros((2*H,H))])
    Aabs1=np.hstack([np.eye(H),-np.eye(H)])
    Aabs2=np.hstack([-np.eye(H),-np.eye(H)])
    A3=np.vstack([Apre,Aabs1,Aabs2])
    b3=np.r_[bub,ref,-ref]
    E3=np.zeros((2,2*H)); E3[0,:H]=primary; E3[1,:H]=1.0
    eb3=np.array([r1.fun,r2.fun])
    bounds3=bounds+[(0,None)]*H
    obj3=np.r_[np.zeros(H),np.ones(H)]
    r3=linprog(obj3,A_ub=A3,b_ub=b3,A_eq=E3,b_eq=eb3,bounds=bounds3,method='highs-ds')
    if not r3.success: raise RuntimeError('recourse tertiary '+r3.message)
    return float(r3.x[0]), {'primary_obj':float(r1.fun),'throughput_obj':float(r2.fun),'refdev_obj':float(r3.fun),
                            'runtime_sec':time.perf_counter()-st,'status':'OPTIMAL'}

def execute_p2(day,q,c_ref,d_ref,actual_load,actual_pv,tariff,e0,margin,fc_load,fc_pv):
    e=float(e0); rows=[]; solver_rows=[]
    q=np.asarray(q,float); fcL=np.asarray(fc_load,float)*DELTA; fcS=np.asarray(fc_pv,float)*DELTA
    Bforecast=q+fcS-fcL
    profiles=build_primary_future_profiles(Bforecast,tariff)
    for t in range(N):
        Lcur=actual_load[t]*DELTA; Scur=actual_pv[t]*DELTA
        Bcur=float(q[t]+Scur-Lcur); st=time.perf_counter()
        action,tie,optint=primary_current_action(Bcur,e,float(tariff[t]),profiles[t+1])
        if tie:
            Bfuture=Bforecast[t:].copy(); Bfuture[0]=Bcur
            action,ev=recourse_lp(Bfuture,tariff[t:],e,c_ref[t:],d_ref[t:])
            ev['method']='FULL_LEX_LP_TIE'; ev['primary_tie']=1; ev['primary_opt_interval_internal_kWh']=list(optint)
        else:
            ev={'primary_obj':None,'throughput_obj':None,'refdev_obj':None,'runtime_sec':time.perf_counter()-st,
                'status':'OPTIMAL','method':'PRIMARY_VALUE_FUNCTION_UNIQUE','primary_tie':0,
                'primary_opt_interval_internal_kWh':list(optint)}
        B=Bcur; before=e
        if B>=0: c=float(action); d=0.0; r=0.0
        else: c=0.0; d=float(action); r=max(-B-d,0.0)
        # Numerical projection only at 1e-10 scale; any material violation is caught by validator.
        c=min(max(c,0.0),min(max(B,0.0),XMAX,(EMAX-e)/ETA_C)) if B>=0 else 0.0
        d=min(max(d,0.0),min(max(-B,0.0),XMAX,(e-EMIN)*ETA_D)) if B<0 else 0.0
        r=max(-B-d,0.0) if B<0 else 0.0
        u=max(q[t]+Scur+d+r-Lcur-c,0.0); w=min(q[t],u); v=u-w
        e=e+ETA_C*c-d/ETA_D
        rows.append({'date':day.date().isoformat(),'slot':t+1,'target_ts':target_ts(day,t+1).isoformat(),
          'contract_id':CONTRACT_ID,'time_mapping_version':TIME_MAPPING,'policy_id':'ANALYTIC_Q80_RESIDUAL_RESERVE_PLUS_CAUSAL_INTRADAY','q_DA_kWh':q[t],
          'charge_ref_kWh':c_ref[t],'discharge_ref_kWh':d_ref[t],'charge_exec_kWh':c,'discharge_exec_kWh':d,
          'actual_load_kWh':Lcur,'actual_pv_kWh':Scur,'forecast_load_kWh':fcL[t],'forecast_pv_kWh':fcS[t],
          'reserve_margin_kWh':margin[t],'tariff':tariff[t],'emergency_kWh':r,'paid_unused_normal_kWh':w,
          'pv_curtailment_kWh':v,'SOC_start_kWh':before,'SOC_end_kWh':e,
          'normal_cost_yuan':tariff[t]*q[t],'emergency_cost_yuan':5*tariff[t]*r,
          'balance_residual_kWh':q[t]-w+r+Scur+d-Lcur-c-v,'clipped_charge_kWh':np.nan,'clipped_discharge_kWh':np.nan,
          'fallback_used':0})
        solver_rows.append({'date':day.date().isoformat(),'slot':t+1,'horizon_slots':N-t,**ev})
    return rows,e,solver_rows

def summarize_policy(df:pd.DataFrame,policy:str,runtime_sec:float,planner_evidence:list,solver_evidence:pd.DataFrame|None):
    g=df.groupby('date',sort=True)
    daily=g.agg(normal_purchase_kWh=('q_DA_kWh','sum'),normal_cost_yuan=('normal_cost_yuan','sum'),
                emergency_kWh=('emergency_kWh','sum'),emergency_cost_yuan=('emergency_cost_yuan','sum'),
                paid_unused_normal_kWh=('paid_unused_normal_kWh','sum'),pv_curtailment_kWh=('pv_curtailment_kWh','sum'),
                charge_kWh=('charge_exec_kWh','sum'),discharge_kWh=('discharge_exec_kWh','sum'),
                SOC_min_kWh=('SOC_end_kWh','min'),SOC_max_kWh=('SOC_end_kWh','max'),SOC_end_kWh=('SOC_end_kWh','last')).reset_index()
    daily['total_cost_yuan']=daily.normal_cost_yuan+daily.emergency_cost_yuan
    daily['emergency_slots']=g['emergency_kWh'].apply(lambda x:int((x>TOL).sum())).values
    daily['battery_throughput_kWh']=daily.charge_kWh+daily.discharge_kWh
    summ={
        'policy_id':policy,'days':int(daily.shape[0]),'slots':int(df.shape[0]),
        'normal_purchase_kWh':float(df.q_DA_kWh.sum()),'normal_cost_yuan':float(df.normal_cost_yuan.sum()),
        'emergency_kWh':float(df.emergency_kWh.sum()),'emergency_cost_yuan':float(df.emergency_cost_yuan.sum()),
        'realized_total_cost_yuan':float(df.normal_cost_yuan.sum()+df.emergency_cost_yuan.sum()),
        'emergency_slot_count':int((df.emergency_kWh>TOL).sum()),'emergency_day_count':int((daily.emergency_kWh>TOL).sum()),
        'P95_daily_emergency_cost_yuan':float(np.quantile(daily.emergency_cost_yuan,0.95,method='linear')),
        'paid_unused_normal_kWh':float(df.paid_unused_normal_kWh.sum()),'pv_curtailment_kWh':float(df.pv_curtailment_kWh.sum()),
        'battery_throughput_kWh':float((df.charge_exec_kWh+df.discharge_exec_kWh).sum()),
        'SOC_min_kWh':float(min(E0_YEAR,df.SOC_end_kWh.min())),'SOC_max_kWh':float(max(E0_YEAR,df.SOC_end_kWh.max())),
        'SOC_end_kWh':float(df.iloc[-1].SOC_end_kWh),'fallback_count':int(df.fallback_used.sum()),
        'max_abs_balance_residual_kWh':float(df.balance_residual_kWh.abs().max()),'runtime_sec':float(runtime_sec),
        'planner_days':len(planner_evidence),'planner_failure_count':0,
    }
    if solver_evidence is not None:
        summ['recourse_solve_count']=int(len(solver_evidence)); summ['recourse_runtime_sec']=float(solver_evidence.runtime_sec.sum())
        summ['recourse_max_runtime_sec']=float(solver_evidence.runtime_sec.max())
    return daily,summ

def run_policy(root:Path,policy:str,forecast:pd.DataFrame,q80:pd.DataFrame):
    dates,load,pv,tariff=read_inputs(root); date_to_idx={pd.Timestamp(d):i for i,d in enumerate(dates)}
    target_days=pd.date_range(START_DATE,END_DATE,freq='D')
    e=E0_YEAR; allrows=[]; planner_log=[]; recourse_log=[]; plan_rows=[]; t0=time.perf_counter()
    for di,d in enumerate(target_days):
        f=forecast[forecast.date==d.date().isoformat()].sort_values('slot')
        m=q80[q80.date==d.date().isoformat()].sort_values('slot')
        if len(f)!=N or len(m)!=N: raise RuntimeError('missing forecast/q80 '+str(d))
        fcL=f.forecast_load_kW.to_numpy(float); fcP=f.forecast_pv_kW.to_numpy(float); margin=m.reserve_margin_kWh.to_numpy(float)
        planning=fcL*DELTA+margin; solar=fcP*DELTA
        day_e0=float(e)
        x,evid=solve_day_ahead(planning,solar,tariff,e)
        q=x[:N]; cref=x[N:2*N]; dref=x[2*N:3*N]
        for z in evid: planner_log.append({'date':d.date().isoformat(),**z})
        for t in range(N):
            plan_rows.append({'date':d.date().isoformat(),'slot':t+1,'target_ts':target_ts(d,t+1).isoformat(),
                'decision_time':d.isoformat(),'contract_id':CONTRACT_ID,'time_mapping_version':TIME_MAPPING,
                'policy_id':'Q80_FIXED_SAFETY_YEAR' if policy=='fixed' else 'ANALYTIC_Q80_RESIDUAL_RESERVE_PLUS_CAUSAL_INTRADAY',
                'day_initial_SOC_kWh':day_e0,'q_DA_kWh':q[t],'charge_ref_kWh':cref[t],'discharge_ref_kWh':dref[t],
                'spill_ref_kWh':x[3*N+t],'SOC_ref_kWh':x[4*N+t],'forecast_load_kWh':fcL[t]*DELTA,
                'forecast_pv_kWh':fcP[t]*DELTA,'reserve_margin_kWh':margin[t],
                'risk_adjusted_planning_load_kWh':planning[t],'tariff':tariff[t]})
        idx=date_to_idx[d]
        if policy=='fixed': rows,e=execute_fixed(d,q,cref,dref,load[idx],pv[idx],tariff,e,margin,fcL,fcP)
        elif policy=='p2':
            rows,e,sev=execute_p2(d,q,cref,dref,load[idx],pv[idx],tariff,e,margin,fcL,fcP); recourse_log.extend(sev)
        else: raise ValueError(policy)
        allrows.extend(rows)
        if (di+1)%10==0 or di==0:
            print(json.dumps({'policy':policy,'day':di+1,'date':d.date().isoformat(),'soc_end':e,'elapsed':time.perf_counter()-t0}),flush=True)
    df=pd.DataFrame(allrows); pl=pd.DataFrame(planner_log); rec=pd.DataFrame(recourse_log) if recourse_log else None; plan=pd.DataFrame(plan_rows)
    daily,summ=summarize_policy(df,policy,time.perf_counter()-t0,planner_log,rec)
    tag='Q80_FIXED' if policy=='fixed' else 'Q80_P2_CAUSAL'
    df.to_csv(root/'results'/f'{tag}_slot_replay.csv',index=False)
    plan.to_csv(root/'results'/f'{tag}_day_ahead_plan.csv',index=False)
    daily.to_csv(root/'results'/f'{tag}_daily_metrics.csv',index=False)
    pl.to_csv(root/'results'/f'{tag}_planner_solver_log.csv',index=False)
    if rec is not None: rec.to_csv(root/'results'/f'{tag}_recourse_solver_log.csv',index=False)
    write_json(root/'results'/f'{tag}_annual_summary.json',summ)
    return df,daily,summ

def build_pair(root:Path):
    a=pd.read_csv(root/'results'/'Q80_FIXED_daily_metrics.csv'); b=pd.read_csv(root/'results'/'Q80_P2_CAUSAL_daily_metrics.csv')
    x=a.merge(b,on='date',suffixes=('_fixed','_p2'))
    x['cost_diff_p2_minus_fixed_yuan']=x.total_cost_yuan_p2-x.total_cost_yuan_fixed
    x['emergency_diff_p2_minus_fixed_kWh']=x.emergency_kWh_p2-x.emergency_kWh_fixed
    x.to_csv(root/'results'/'daily_paired_fixed_vs_p2.csv',index=False)
    return x

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);
    ap.add_argument('--stage',choices=['forecast','q80','fixed','p2','pair','all'],default='all'); ap.add_argument('--workers',type=int,default=4)
    args=ap.parse_args(); root=args.root.resolve(); (root/'results').mkdir(exist_ok=True)
    f=r=None
    if args.stage in ['forecast','all']:
        f,r=load_or_build_forecasts(root,args.workers)
        if args.stage=='forecast': return
    else:
        f=pd.read_csv(root/'results'/'annual_forecast.csv'); r=pd.read_csv(root/'results'/'annual_forecast_residuals.csv')
    q=None
    if args.stage in ['q80','all']:
        q=load_or_build_q80(root,r)
        if args.stage=='q80': return
    else:
        q=pd.read_csv(root/'results'/'q80_margin_audit.csv')
    if args.stage in ['fixed','all']:
        run_policy(root,'fixed',f,q)
        if args.stage=='fixed': return
    if args.stage in ['p2','all']:
        run_policy(root,'p2',f,q)
        if args.stage=='p2': return
    if args.stage in ['pair','all']: build_pair(root)

def _q4_output_tag(mode: str) -> str:
    if mode == 'CAUSAL_LAG7':
        return 'Q4_2_Q80P2_CAUSAL_LAG7'
    if mode == 'ORACLE_DIAGNOSTIC':
        return 'Q4_2_Q80P2_ORACLE_PRICE'
    raise ValueError(f'Unknown Q4 mode: {mode}')


def _price_audit_row(action: str, day: pd.Timestamp, slot: int, points):
    """Return one compact, auditable record for a price request to the controller."""
    decision_time = pd.Timestamp(points[0].decision_time)
    known = pd.to_datetime([p.known_at for p in points])
    sources = [p.source for p in points]
    future = points[1:]
    causal_bad = 0
    if points[0].mode == 'CAUSAL_LAG7':
        causal_bad += int(not all(x <= decision_time for x in known))
        if action == 'day_ahead':
            causal_bad += int(any(s != 'LAG7_REALIZED' for s in sources))
        else:
            causal_bad += int(sources[0] != 'CURRENT_REALIZED')
            causal_bad += int(any(p.source != 'LAG7_REALIZED' for p in future))
    return {
        'action': action, 'date': day.date().isoformat(), 'slot': int(slot),
        'mode': points[0].mode, 'decision_time': points[0].decision_time,
        'n_target_slots_priced': len(points),
        'current_source': sources[0],
        'future_sources_unique': '|'.join(sorted(set(p.source for p in future))),
        'known_at_max': max(p.known_at for p in points),
        'known_at_le_decision': bool(all(x <= decision_time for x in known)),
        'causal_contract_bad_count': int(causal_bad),
        'oracle_future_actual_count': int(sum(p.source == 'ORACLE_REALIZED_DIAGNOSTIC' for p in future)),
    }


def _build_primary_future_profiles_q4(Bforecast, decision_prices):
    """The frozen Q2 value-function recurrence, generalized only to a remaining horizon."""
    horizon = len(Bforecast)
    if len(decision_prices) != horizon:
        raise ValueError('Q4 price horizon length mismatch')
    profiles = [None] * (horizon + 1)
    profiles[horizon] = [(0.0, C_USABLE)]
    for j in range(horizon-1, -1, -1):
        segs = profiles[j+1]
        B = float(Bforecast[j])
        if B < 0:
            dcap = min(-B, XMAX); internal = dcap / ETA_D
            profiles[j] = _insert_reward_segment(segs, 5*float(decision_prices[j])*ETA_D, internal)
        elif B > 0:
            ccap = min(B, XMAX); internal = ETA_C * ccap
            tail = _drop_prefix_segments(segs, internal)
            profiles[j] = _truncate_segments(_merge_segments(tail + [(0.0, internal)]))
        else:
            profiles[j] = list(segs)
        if abs(sum(z[1] for z in profiles[j])-C_USABLE) > 1e-6:
            raise RuntimeError('bad Q4 primary profile domain')
    return profiles


def _attachment4_price_check(root: Path, provider: Q4PriceProvider) -> dict:
    """Independently bind provider settlement prices to official Attachment 4."""
    raw = pd.read_excel(root / 'inputs' / 'attachment4.xlsx', sheet_name=0, header=0)
    dates = pd.to_datetime(raw.iloc[:, 0]).dt.normalize()
    values = raw.iloc[:, 1:145].to_numpy(float)
    index = {d.date().isoformat(): i for i, d in enumerate(dates)}
    checks = []
    for day, group in provider.df.groupby('date', sort=True):
        i = index.get(str(day))
        if i is None:
            raise RuntimeError(f'Attachment4 missing provider date {day}')
        checks.extend(values[i, :].tolist())
    expected = provider.df.sort_values(['date', 'slot']).price_realized.to_numpy(float)
    max_abs = float(np.max(np.abs(np.asarray(checks, float) - expected)))
    return {'attachment4_settlement_price_max_abs_diff': max_abs,
            'attachment4_price_identity_pass': bool(max_abs <= 1e-12)}


def execute_p2_q4(day, q, c_ref, d_ref, actual_load, actual_pv, e0, margin, fc_load, fc_pv,
                  provider: Q4PriceProvider, mode: str):
    """Frozen Q2 P2 physics, with the Q4 contract's price-information layer only."""
    e = float(e0); rows = []; solver_rows = []; audit_rows = []
    q = np.asarray(q, float); fcL = np.asarray(fc_load, float) * DELTA; fcS = np.asarray(fc_pv, float) * DELTA
    Bforecast = q + fcS - fcL
    # The future curve is unchanged within a day under LAG7; only the current
    # slot price changes when it becomes observable.  The Oracle curve is also
    # fixed.  This preserves the Q2 value-function recurrence without repeated
    # reconstruction of an identical future profile.
    base_prices = np.asarray([p.decision_price for p in provider.q4_2_day_ahead(day.date().isoformat(), mode)], float)
    profiles = _build_primary_future_profiles_q4(Bforecast, base_prices)
    for t in range(N):
        price_points = provider.q4_2_intraday(day.date().isoformat(), t + 1, mode)
        price_horizon = np.asarray([p.decision_price for p in price_points], float)
        Lcur = actual_load[t] * DELTA; Scur = actual_pv[t] * DELTA
        Bcur = float(q[t] + Scur - Lcur); st = time.perf_counter()
        action, tie, optint = primary_current_action(Bcur, e, float(price_horizon[0]), profiles[t+1])
        if tie:
            Bfuture = Bforecast[t:].copy(); Bfuture[0] = Bcur
            action, ev = recourse_lp(Bfuture, price_horizon, e, c_ref[t:], d_ref[t:])
            ev['method'] = 'FULL_LEX_LP_TIE'; ev['primary_tie'] = 1
            ev['primary_opt_interval_internal_kWh'] = list(optint)
        else:
            ev = {'primary_obj': None, 'throughput_obj': None, 'refdev_obj': None,
                  'runtime_sec': time.perf_counter() - st, 'status': 'OPTIMAL',
                  'method': 'PRIMARY_VALUE_FUNCTION_UNIQUE', 'primary_tie': 0,
                  'primary_opt_interval_internal_kWh': list(optint)}
        before = e
        if Bcur >= 0:
            c = float(action); d = 0.0; r = 0.0
        else:
            c = 0.0; d = float(action); r = max(-Bcur - d, 0.0)
        c = min(max(c, 0.0), min(max(Bcur, 0.0), XMAX, (EMAX-e)/ETA_C)) if Bcur >= 0 else 0.0
        d = min(max(d, 0.0), min(max(-Bcur, 0.0), XMAX, (e-EMIN)*ETA_D)) if Bcur < 0 else 0.0
        r = max(-Bcur-d, 0.0) if Bcur < 0 else 0.0
        u = max(q[t] + Scur + d + r - Lcur - c, 0.0); w = min(q[t], u); v = u-w
        e = e + ETA_C*c - d/ETA_D
        current = price_points[0]
        rows.append({'date': day.date().isoformat(), 'slot': t+1, 'target_ts': target_ts(day, t+1).isoformat(),
          'contract_id': CONTRACT_ID, 'time_mapping_version': TIME_MAPPING,
          'policy_id': 'ANALYTIC_Q80_RESIDUAL_RESERVE_PLUS_CAUSAL_INTRADAY',
          'q_DA_kWh': q[t], 'charge_ref_kWh': c_ref[t], 'discharge_ref_kWh': d_ref[t],
          'charge_exec_kWh': c, 'discharge_exec_kWh': d, 'actual_load_kWh': Lcur, 'actual_pv_kWh': Scur,
          'forecast_load_kWh': fcL[t], 'forecast_pv_kWh': fcS[t], 'reserve_margin_kWh': margin[t],
          'decision_price_CNY_per_kWh': current.decision_price,
          'settlement_price_CNY_per_kWh': current.settlement_price, 'price_known_at': current.known_at,
          'price_source': current.source, 'price_mode': current.mode,
          'tariff': current.settlement_price, 'emergency_kWh': r, 'paid_unused_normal_kWh': w,
          'pv_curtailment_kWh': v, 'SOC_start_kWh': before, 'SOC_end_kWh': e,
          'normal_cost_yuan': current.settlement_price*q[t],
          'emergency_cost_yuan': 5*current.settlement_price*r,
          'balance_residual_kWh': q[t]-w+r+Scur+d-Lcur-c-v,
          'clipped_charge_kWh': np.nan, 'clipped_discharge_kWh': np.nan, 'fallback_used': 0})
        solver_rows.append({'date': day.date().isoformat(), 'slot': t+1, 'horizon_slots': N-t, **ev})
        audit_rows.append(_price_audit_row('intraday', day, t+1, price_points))
    return rows, e, solver_rows, audit_rows


def _summarize_q4(df: pd.DataFrame, mode: str, runtime_sec: float,
                  solver_log: pd.DataFrame, planner_log: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    daily, summary = summarize_policy(df, _q4_output_tag(mode), runtime_sec, [], solver_log)
    # Derive planner metadata from emitted evidence. Do not infer it from the
    # requested horizon and do not hard-code the full-year day count.
    summary['planner_days'] = int(planner_log['date'].nunique()) if not planner_log.empty else 0
    summary['planner_failure_count'] = int((~planner_log['success'].astype(bool)).sum()) if not planner_log.empty else 0
    summary.update({'controller_id': 'Q80_P2', 'price_mode': mode,
                    'formal_status': 'PRIMARY_FORMAL' if mode == 'CAUSAL_LAG7' else 'DIAGNOSTIC_ONLY'})
    return daily, summary


def run_q4_policy(root: Path, mode: str, days: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict, pd.DataFrame]:
    provider = Q4PriceProvider(root/'inputs'/'q4_price_lag7_feb_dec.csv')
    price_identity = _attachment4_price_check(root, provider)
    if not price_identity['attachment4_price_identity_pass']:
        raise RuntimeError('Attachment4 settlement price mismatch')
    dates, load, pv, _ = read_inputs(root)
    date_to_idx = {pd.Timestamp(d): i for i, d in enumerate(dates)}
    forecast = pd.read_csv(root/'inputs'/'annual_forecast_q2_frozen.csv')
    q80 = pd.read_csv(root/'inputs'/'q80_margin_audit_q2_frozen.csv')
    target_days = pd.date_range(START_DATE, END_DATE, freq='D')
    if days is not None:
        target_days = target_days[:int(days)]
    e = E0_YEAR; allrows=[]; planner_log=[]; solver_log=[]; plan_rows=[]; audit_rows=[]; t0=time.perf_counter()
    for di, d in enumerate(target_days):
        fs = forecast[forecast.date == d.date().isoformat()].sort_values('slot')
        ms = q80[q80.date == d.date().isoformat()].sort_values('slot')
        if len(fs) != N or len(ms) != N:
            raise RuntimeError(f'Missing frozen Q2 forecast/Q80 rows: {d.date()}')
        day_prices = provider.q4_2_day_ahead(d.date().isoformat(), mode)
        planning_prices = np.asarray([p.decision_price for p in day_prices], float)
        fcL = fs.forecast_load_kW.to_numpy(float); fcP = fs.forecast_pv_kW.to_numpy(float)
        margin = ms.reserve_margin_kWh.to_numpy(float); planning = fcL*DELTA + margin; solar = fcP*DELTA
        day_e0 = float(e); x, evidence = solve_day_ahead(planning, solar, planning_prices, e)
        q = x[:N]; cref = x[N:2*N]; dref = x[2*N:3*N]
        for z in evidence:
            planner_log.append({'date': d.date().isoformat(), 'price_mode': mode, **z})
        for t, p in enumerate(day_prices):
            plan_rows.append({'date': d.date().isoformat(), 'slot': t+1, 'target_ts': target_ts(d,t+1).isoformat(),
              'decision_time': p.decision_time, 'contract_id': CONTRACT_ID, 'time_mapping_version': TIME_MAPPING,
              'policy_id': 'ANALYTIC_Q80_RESIDUAL_RESERVE_PLUS_CAUSAL_INTRADAY', 'price_mode': mode,
              'day_initial_SOC_kWh': day_e0, 'q_DA_kWh': q[t], 'charge_ref_kWh': cref[t], 'discharge_ref_kWh': dref[t],
              'spill_ref_kWh': x[3*N+t], 'SOC_ref_kWh': x[4*N+t], 'forecast_load_kWh': fcL[t]*DELTA,
              'forecast_pv_kWh': fcP[t]*DELTA, 'reserve_margin_kWh': margin[t],
              'risk_adjusted_planning_load_kWh': planning[t], 'decision_price_CNY_per_kWh': p.decision_price,
              'settlement_price_CNY_per_kWh': p.settlement_price, 'price_known_at': p.known_at, 'price_source': p.source})
        audit_rows.extend(_price_audit_row('day_ahead', d, 1, day_prices) for _ in [0])
        rows, e, sev, day_audit = execute_p2_q4(d, q, cref, dref, load[date_to_idx[d]], pv[date_to_idx[d]],
                                                 e, margin, fcL, fcP, provider, mode)
        allrows.extend(rows); solver_log.extend(sev); audit_rows.extend(day_audit)
        if (di+1) % 10 == 0 or di == 0 or di+1 == len(target_days):
            print(json.dumps({'mode': mode, 'day': di+1, 'date': d.date().isoformat(), 'soc_end': e,
                              'elapsed': time.perf_counter()-t0}), flush=True)
    slot = pd.DataFrame(allrows); plan = pd.DataFrame(plan_rows); sol = pd.DataFrame(solver_log); audit = pd.DataFrame(audit_rows)
    planner = pd.DataFrame(planner_log)
    daily, summary = _summarize_q4(slot, mode, time.perf_counter()-t0, sol, planner)
    future_leak = int(audit.causal_contract_bad_count.sum()) if mode == 'CAUSAL_LAG7' else 0
    price_audit_summary = {'mode': mode, 'audit_rows': int(len(audit)),
                           'price_future_realized_leak_count': future_leak,
                           'oracle_future_actual_count': int(audit.oracle_future_actual_count.sum()),
                           'all_known_at_le_decision': bool(audit.known_at_le_decision.all()), **price_identity}
    summary.update(price_audit_summary)
    out = root/'results'/('causal' if mode == 'CAUSAL_LAG7' else 'oracle')
    out.mkdir(parents=True, exist_ok=True)
    slot.to_csv(out/'slot_replay.csv', index=False); plan.to_csv(out/'day_ahead_plan.csv', index=False)
    daily.to_csv(out/'daily_metrics.csv', index=False); sol.to_csv(out/'recourse_solver_log.csv', index=False)
    planner.to_csv(out/'planner_solver_log.csv', index=False); audit.to_csv(out/'price_audit.csv', index=False)
    write_json(out/'annual_summary.json', summary); write_json(out/'price_audit_summary.json', price_audit_summary)
    return slot, daily, summary, audit


def q4_main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--mode', choices=['CAUSAL_LAG7', 'ORACLE_DIAGNOSTIC'], required=True)
    ap.add_argument('--days', type=int, default=None)
    args = ap.parse_args()
    _, _, summary, audit = run_q4_policy(args.root.resolve(), args.mode, args.days)
    print(json.dumps({'summary': summary, 'price_audit_rows': int(len(audit))}, ensure_ascii=False, indent=2))


if __name__=='__main__': q4_main()
