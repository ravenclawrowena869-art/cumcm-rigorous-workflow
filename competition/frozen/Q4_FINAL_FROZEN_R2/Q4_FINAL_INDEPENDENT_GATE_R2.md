# Q4 Final Independent Gate — R2

## Verdict

**PASS** — Q4 reaches `FINAL_FROZEN` at the problem-4 model/result level.

The whole-paper Submission Gate is intentionally deferred to the global paper workflow; this does not reopen Q4 unless the later full-paper check finds a Q4 evidence inconsistency.

## Independent checks completed

- Source package CRC and internal `SHA256SUMS.txt`: **PASS** for XXT, FYQ, Q4-2 CYQ audit, Q4-3 independent audit, and Joint Gate packages.
- Frozen source-package and formal-workbook hashes match `SOURCE_HASHES_R2.json`: **PASS**.
- Q4-2 annual causal/oracle costs match the XXT frozen source and CYQ independent accounting: **PASS**.
- Q4-2 hard constraints, price causality and full `result4-2.xlsx` causal readback: **PASS**.
- Q4-3 annual causal/oracle costs match FYQ frozen source and independent Phase-B accounting: **PASS**.
- Q4-3 334×144 hard constraints, cross-day SOC, stage/settlement identities and price causality: **PASS**.
- Frozen Q3 B1B lambda identity in Q4-3, 1,002 Feb–Dec rows: **exact PASS**.
- Full `result4-3.xlsx` causal readback: **PASS**.
- Formal workbooks imported with `artifact_tool`; expected sheets present and formula-error scan found no `#REF!/#DIV/0!/#VALUE!/#NAME?/#N/A`: **PASS**.
- Final result table, status JSON and paper number registry agree with the frozen source values: **PASS**.
- Every `READY_*` candidate figure registered for Q4 has figure-ready data, plotting code, PNG, SVG and README: **PASS**.
- No stale `ACCEPTED/HOLD/not FINAL_FROZEN` status remains in final Q4 governance/paper-handoff documents: **PASS**.

## Frozen formal numbers

### Q4-2 — Q80_P2 + causal LAG7

- total: **19,573,328.548728 yuan**
- normal purchase: **13,942,442.588470 yuan**
- emergency purchase: **5,630,885.960257 yuan**
- emergency energy: **1,051,947.272513 kWh**
- Oracle diagnostic gap: **105,150.693084 yuan (0.537214%)**

### Q4-3 — B1B + causal LAG7

- total: **15,865,665.795889 yuan**
- base commitment: **13,050,650.153093 yuan**
- adjustment: **380,123.566811 yuan**
- emergency purchase: **2,434,892.075985 yuan**
- emergency energy: **549,309.855236 kWh**
- Oracle diagnostic gap: **77,551.510177 yuan (0.488801%)**

Under the same causal LAG7 price-information baseline, Q4-3 is lower by **3,707,662.752839 yuan (18.9424%)**. The allowed interpretation is the economic value of richer intraday PV information plus rolling adjustment rights, not a pure algorithm-only comparison.

## Model-selection decision

Both perfect-future-price Oracle gaps are below 0.6% of the corresponding causal annual cost. The preregistered price-model upgrade trigger is therefore not met. **STOP_EXPANSION** is frozen: no ARIMA/ML/price-scenario/CVaR mainline addition is justified by the current evidence.
