from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from q4_price_provider import Q4PriceProvider

p=Q4PriceProvider(ROOT/'inputs/q4_price_lag7_feb_dec.csv')
checks={}
for d in ('2025-02-01','2025-06-21','2025-12-31'):
    a=p.q4_2_day_ahead(d,'CAUSAL_LAG7'); assert len(a)==144
    checks[f'{d}_day_ahead_slots']=len(a)
expected={0:144,6:108,12:72,18:36}
for h,n in expected.items():
    x=p.q4_3_stage('2025-02-01',h,'CAUSAL_LAG7'); assert len(x)==n
    assert all(z.known_at<=z.decision_time for z in x)
    checks[f'stage_{h}_slots']=len(x)
x=p.q4_2_intraday('2025-02-01',37,'CAUSAL_LAG7'); assert x[0].source=='CURRENT_REALIZED'
assert all(z.source=='LAG7_REALIZED' for z in x[1:]); assert all(z.known_at<=z.decision_time for z in x)
xo=p.q4_3_stage('2025-02-01',12,'ORACLE_DIAGNOSTIC')
assert all(abs(z.decision_price-z.settlement_price)<=1e-15 for z in xo)
assert all(z.source=='ORACLE_REALIZED_DIAGNOSTIC' for z in xo)
checks['oracle_tag_ok']=True
out={'status':'PASS','checks':checks}
(ROOT/'04_PATCH_R2/PRICE_PROVIDER_TEST_REPORT_R2.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS')
