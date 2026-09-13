from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import linprog as scipy_linprog
import q3.formal_lp as flp
from q3.common import digest,start,instant
from q4_engine import _tz8
from run_q4_3 import derive_loads,build_schedules,q4_config,Q4PriceProvider,INPUTS,PKG_ROOT,load_actuals,load_vintages,validate_q4_day
from q4_engine import solve_q4_day

OUT=PKG_ROOT/'04_PATCH_R2'
OUT.mkdir(exist_ok=True)
EVENTS=[
 ('CAUSAL_LAG7','causal','2025-07-29'),
 ('ORACLE_DIAGNOSTIC','oracle','2025-05-18'),
 ('ORACLE_DIAGNOSTIC','oracle','2025-08-03'),
]

def build_request(day,mode,initial_soc,loads,schedules,provider):
    pts=provider.q4_3_stage(day,0,mode=mode)
    prices=[float(x.decision_price) for x in pts]
    pv=schedules[day][0]; load=loads[day]
    if mode=='CAUSAL_LAG7':
        pmax=max(instant(_tz8(str(x.known_at))) for x in pts)
        dep=max(instant(load['known_at']),instant(pv['known_at']),pmax).isoformat()
    else:
        dep=max(instant(load['known_at']),instant(pv['known_at'])).isoformat()
    return {
        'date':day,'stage':0,'decision_time':start(day).isoformat(),'future_slots':list(range(1,145)),
        'load_kwh':list(load['values']),'pv_kwh':list(pv['values']),'prices':prices,'initial_soc':float(initial_soc),
        'previous_active':{},'executed_prefix_hash':digest([]),'forecast_id':pv['forecast_id'],'load_forecast_id':load['forecast_id'],
        'dependency_known_at':dep,
    }

def x_to_plan(x,n=144):
    offsets={'q':0,'c':n,'d':2*n,'r':3*n,'w':4*n,'v':5*n,'e':6*n,'z':7*n}
    out=[]
    for i,t in enumerate(range(1,n+1)):
        out.append({'slot_id':t,'q':max(float(x[offsets['q']+i]),0.0),'c_ref':max(float(x[offsets['c']+i]),0.0),
                    'd_ref':max(float(x[offsets['d']+i]),0.0),'predicted_emergency_kwh':max(float(x[offsets['r']+i]),0.0),
                    'predicted_unused_grid_kwh':max(float(x[offsets['w']+i]),0.0),'predicted_pv_curtail_kwh':max(float(x[offsets['v']+i]),0.0),
                    'reference_soc_after_kwh':float(x[offsets['e']+i])})
    return out

def diagnose_one(mode,branch,day,loads,schedules,provider,cfg,actuals):
    refday=pd.read_csv(PKG_ROOT/f'results/{branch}/daily.csv').set_index('date').loc[day]
    req=build_request(day,mode,float(refday['initial_soc_kwh']),loads,schedules,provider)
    orig=flp.linprog; calls=[]
    def wrapped(c,A_ub=None,b_ub=None,A_eq=None,b_eq=None,bounds=None,method='highs',options=None,**kw):
        res=orig(c,A_ub=A_ub,b_ub=b_ub,A_eq=A_eq,b_eq=b_eq,bounds=bounds,method=method,options=options,**kw)
        calls.append({'c':np.array(c,copy=True),'A_ub':None if A_ub is None else np.array(A_ub,copy=True),
                      'b_ub':None if b_ub is None else np.array(b_ub,copy=True),'A_eq':None if A_eq is None else np.array(A_eq,copy=True),
                      'b_eq':None if b_eq is None else np.array(b_eq,copy=True),'bounds':bounds,'method':method,'options':options,
                      'success':bool(res.success),'status':int(res.status),'message':str(res.message),'x':None if not res.success else np.array(res.x,copy=True)})
        return res
    flp.linprog=wrapped
    try:
        base=flp.solve_formal_lp(req,cfg)
    finally:
        flp.linprog=orig
    sm=base['solver_metadata']
    # First two calls are economic and throughput. Tertiary first-attempt matrix is call 2.
    if len(calls)<3: raise RuntimeError(f'CAPTURE_CALLS_TOO_FEW:{day}:{len(calls)}')
    econ_c=calls[0]['c']; thr_c=calls[1]['c']; ter=calls[2]
    variants=[]; successful_plans=[]; opts={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9}
    for method,presolve in [('highs-ds',True),('highs-ds',False),('highs-ipm',True),('highs',False)]:
        try:
            res=scipy_linprog(ter['c'],A_ub=ter['A_ub'],b_ub=ter['b_ub'],A_eq=ter['A_eq'],b_eq=ter['b_eq'],bounds=ter['bounds'],method=method,options={**opts,'presolve':presolve})
            rec={'method':method,'presolve':presolve,'success':bool(res.success),'status':int(res.status),'message':str(res.message)}
            if res.success:
                x=np.array(res.x)
                plan=x_to_plan(x)
                v=flp.validate_formal_plan(req,cfg,plan)
                rec.update({'economic_value_yuan':float(econ_c@x),'throughput_kwh':float(thr_c@x),'tertiary_objective':float(ter['c']@x),
                            'economic_excess_over_optimum':float(econ_c@x-float(sm['economic_objective_yuan'])),
                            'throughput_excess_over_optimum':float(thr_c@x-float(sm['throughput_optimum_kwh'])),
                            'hard_validation':v['status'],'max_hard_violation':float(v['max_violation']),
                            'max_q_diff_vs_fallback':max(abs(float(a['q'])-float(b['q'])) for a,b in zip(plan,base['plan'])),
                            'max_c_diff_vs_fallback':max(abs(float(a['c_ref'])-float(b['c_ref'])) for a,b in zip(plan,base['plan'])),
                            'max_d_diff_vs_fallback':max(abs(float(a['d_ref'])-float(b['d_ref'])) for a,b in zip(plan,base['plan']))})
                successful_plans.append((method,presolve,plan,rec))
            variants.append(rec)
        except Exception as ex:
            variants.append({'method':method,'presolve':presolve,'success':False,'exception':repr(ex)})
    day_impact=None
    # If current replay or an alternate path produces a tertiary plan, inject only the stage-0 tie-break plan
    # and re-run that day. Primary/secondary economics and all later stages remain unchanged.
    inject_plan=None; inject_label=None
    if sm.get('fallback_count',0)==0:
        inject_plan=base['plan']; inject_label='CURRENT_STANDARD_REPLAY_TERTIARY'
    elif successful_plans:
        inject_label=f"ALT_{successful_plans[0][0]}_presolve_{successful_plans[0][1]}"; inject_plan=successful_plans[0][2]
    if inject_plan is not None:
        from q3.formal_lp import solve_formal_lp
        def custom_planner(request):
            if int(request['stage'])==0:
                v=flp.validate_formal_plan(request,cfg,inject_plan)
                return {'planner_kind':'FORMAL_LP','plan':inject_plan,'solver_metadata':{'status':'OPTIMAL','solver_id':'DIAGNOSTIC_INJECTED_TERTIARY','stages':[],
                        'economic_objective_yuan':sm['economic_objective_yuan'],'final_economic_value_yuan':sm['economic_objective_yuan'],
                        'economic_tolerance_yuan':cfg['tol_cost_yuan'],'throughput_optimum_kwh':sm['throughput_optimum_kwh'],'final_throughput_kwh':sm['throughput_optimum_kwh'],
                        'tie_break_status':inject_label,'fallback_count':0,'numerical_recovery_count':0,'numerical_recovery_policy':'DIAGNOSTIC_ONLY'},'validation':v}
            return solve_formal_lp(request,cfg)
        pts={h:provider.q4_3_stage(day,h,mode=mode) for h in (0,6,12,18)}
        settlement=[float(x.settlement_price) for x in provider.q4_3_stage(day,0,mode=mode)]
        run=solve_q4_day(date=day,load_forecast_provider=loads[day],pv_vintage_provider=schedules[day],initial_soc=float(refday['initial_soc_kwh']),actual_rows=actuals[day],
                         price_points_by_stage=pts,settlement_prices=settlement,config=cfg,initial_state_hash=digest(['DIAG',mode,day,float(refday['initial_soc_kwh'])]),planner=custom_planner,mode=mode)
        vv=validate_q4_day(run); mm=vv['metrics']
        day_impact={'injected_path':inject_label,'validator':vv['status'],'total_cost_delta_yuan':float(mm['total_cost_yuan']-float(refday['total_cost_yuan'])),
                    'emergency_energy_delta_kwh':float(mm['emergency_energy_kwh']-float(refday['emergency_energy_kwh'])),
                    'terminal_soc_delta_kwh':float(mm['terminal_soc_kwh']-float(refday['terminal_soc_kwh']))}
    return {'date':day,'mode':mode,'r1_recorded_fallback':True,'current_replay_tie_break_status':sm.get('tie_break_status'),'current_replay_fallback_count':sm.get('fallback_count'),
            'captured_solver_attempts':[{'method':c['method'],'options':c['options'],'success':c['success'],'status':c['status'],'message':c['message']} for c in calls],
            'alternative_same_lp_same_1e9':variants,'day_impact_if_tertiary_available':day_impact}

def main():
    loads=derive_loads(); actuals=load_actuals(INPUTS/'attachment2.xlsx');vints=load_vintages(INPUTS/'attachment3.xlsx');vmap={x['issue_time']:x for x in vints}
    schedules,_=build_schedules(actuals,vmap);cfg,_=q4_config();provider=Q4PriceProvider(INPUTS/'q4_price_lag7_feb_dec.csv')
    rows=[diagnose_one(*e,loads,schedules,provider,cfg,actuals) for e in EVENTS]
    verdict='PASS'
    # A numerical fallback is acceptable when the primary and secondary optima are preserved.
    # Current replay may or may not reproduce the exact tertiary solver status; that itself is evidence of numerical path dependence.
    for r in rows:
        for v in r['alternative_same_lp_same_1e9']:
            if v.get('success') and (v.get('hard_validation')!='PASS' or v.get('economic_excess_over_optimum',1)>1.5e-7 or v.get('throughput_excess_over_optimum',1)>1.5e-7): verdict='FAIL'
        imp=r.get('day_impact_if_tertiary_available')
        if imp and (imp.get('validator')!='PASS' or abs(imp.get('total_cost_delta_yuan',0))>1e-4 or abs(imp.get('terminal_soc_delta_kwh',0))>1e-4): verdict='FAIL'
    out={'schema':'Q4_3_TERTIARY_FALLBACK_DIAGNOSTIC_R2','verdict':verdict,'events':rows,
         'interpretation':'Same LP and same 1e-9 feasibility tolerances were tested with alternate HiGHS paths. No formal result is replaced by this diagnostic.'}
    (OUT/'TERTIARY_FALLBACK_DIAGNOSTIC_R2.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+'\n')
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if verdict=='PASS' else 2)
if __name__=='__main__':main()
