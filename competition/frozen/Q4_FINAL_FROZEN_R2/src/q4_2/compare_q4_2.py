from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[1]
c=pd.read_csv(root/'results/causal/daily_metrics.csv').sort_values('date').reset_index(drop=True)
o=pd.read_csv(root/'results/oracle/daily_metrics.csv').sort_values('date').reset_index(drop=True)
p=pd.read_csv(root/'inputs/q4_price_lag7_feb_dec.csv')
if not c.date.equals(o.date): raise RuntimeError('daily date mismatch')
x=c[['date','total_cost_yuan','normal_cost_yuan','emergency_cost_yuan','emergency_kWh']].merge(o[['date','total_cost_yuan','normal_cost_yuan','emergency_cost_yuan','emergency_kWh']],on='date',suffixes=('_causal','_oracle'))
x['daily_cost_gap_yuan']=x.total_cost_yuan_causal-x.total_cost_yuan_oracle
x['daily_cost_gap_pct_of_causal']=100*x.daily_cost_gap_yuan/x.total_cost_yuan_causal
price_day=p.groupby('date',sort=True).agg(daily_price_forecast_abs_error=('forecast_abs_error','sum')).reset_index()
x=x.merge(price_day,on='date',how='left')
x.to_csv(root/'results/causal_vs_oracle.csv',index=False)
cs=json.loads((root/'results/causal/annual_summary.json').read_text()); os=json.loads((root/'results/oracle/annual_summary.json').read_text())
gap=cs['realized_total_cost_yuan']-os['realized_total_cost_yuan']
summary={'causal':{k:cs[k] for k in ['realized_total_cost_yuan','normal_cost_yuan','emergency_cost_yuan','normal_purchase_kWh','emergency_kWh','emergency_slot_count','emergency_day_count','P95_daily_emergency_cost_yuan','paid_unused_normal_kWh','pv_curtailment_kWh','battery_throughput_kWh','SOC_min_kWh','SOC_max_kWh','SOC_end_kWh','runtime_sec','fallback_count','price_future_realized_leak_count']},
         'oracle_diagnostic':{k:os[k] for k in ['realized_total_cost_yuan','normal_cost_yuan','emergency_cost_yuan','normal_purchase_kWh','emergency_kWh','emergency_slot_count','emergency_day_count','P95_daily_emergency_cost_yuan','paid_unused_normal_kWh','pv_curtailment_kWh','battery_throughput_kWh','SOC_min_kWh','SOC_max_kWh','SOC_end_kWh','runtime_sec','fallback_count','oracle_future_actual_count']},
         'perfect_price_information_gap_yuan':gap,'perfect_price_information_gap_pct_of_causal':100*gap/cs['realized_total_cost_yuan'],
         'daily_gap_yuan':{'mean':float(x.daily_cost_gap_yuan.mean()),'median':float(x.daily_cost_gap_yuan.median()),'P95':float(np.quantile(x.daily_cost_gap_yuan,.95))},
         'daily_price_error_gap_correlation':float(x.daily_price_forecast_abs_error.corr(x.daily_cost_gap_yuan)),
         'top20_gap_dates':x.nlargest(20,'daily_cost_gap_yuan')[['date','daily_cost_gap_yuan','daily_cost_gap_pct_of_causal']].to_dict(orient='records'),
         'formal_result':'causal_only','oracle_label':'DIAGNOSTIC_ONLY'}
(root/'results/q4_2_comparison_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
