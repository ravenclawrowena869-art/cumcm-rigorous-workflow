# Q4 Final Freeze Decision — R2

## Final decision

**Q4 = `FINAL_FROZEN`**.

The Q4 formal solution inherits the already frozen Q2 and Q3 controllers and adds a causal dynamic-price information layer. No further mainline price-model expansion is authorized.

### Frozen Q4-2

`Q80_P2 + CAUSAL_PRICE_LAG7_R0`

- annual total cost: **19,573,328.548728 yuan**;
- normal purchase cost: **13,942,442.588470 yuan**;
- emergency purchase cost: **5,630,885.960257 yuan**;
- emergency energy: **1,051,947.272513 kWh**;
- terminal SOC: **1,200 kWh**;
- future realized price leakage: **0**;
- inherited hard Gate: **PASS**.

Oracle diagnostic cost = **19,468,177.855644 yuan**. Perfect-price-information gap = **105,150.693084 yuan = 0.537214%** of the causal total.

### Frozen Q4-3

`B1B_PRIMARY_L1_MAE_W28_H14 + CAUSAL_PRICE_LAG7_R0`

- annual total cost: **15,865,665.795889 yuan**;
- base commitment cost: **13,050,650.153093 yuan**;
- adjustment cost: **380,123.566811 yuan**;
- emergency cost: **2,434,892.075985 yuan**;
- emergency energy: **549,309.855236 kWh**;
- terminal SOC: **1,290.653832 kWh**;
- future realized price leakage: **0**;
- frozen Q3 lambda identity: **PASS**;
- inherited hard Gate: **PASS**.

Oracle diagnostic cost = **15,788,114.285712 yuan**. Perfect-price-information gap = **77,551.510177 yuan = 0.488801%** of the causal total.

## Q4-2 vs Q4-3 under the same causal price information

Q4-3 is lower by:

- **3,707,662.752839 yuan**;
- **18.9424%** of Q4-2 annual cost.

Emergency burden is lower by:

- emergency cost: **3,195,993.884273 yuan (56.7583%)**;
- emergency energy: **502,637.417276 kWh (47.7816%)**.

This comparison is not a pure algorithm contest. Q4-3 has additional intraday PV forecast information and legal rolling-adjustment opportunities. The permitted paper claim is therefore: **the additional intraday information and rolling adjustment rights have substantial economic value under the same causal dynamic-price baseline**.

## Why price-model expansion stops

The preregistered Oracle diagnostic asks how much perfect future price information could improve the frozen controllers if all non-price semantics remain unchanged. The annual gaps are below 0.6% for both branches. Therefore the evidence does not justify introducing ARIMA/ML/price scenarios/CVaR solely for complexity.

High-price-tail effects remain locally concentrated and should be discussed as a limitation/diagnostic. They do not overturn the annual stop rule.

## Independent acceptance evidence

Q4-2:
- CYQ Phase-B independent accounting: PASS;
- hard-constraint/price-causality audit: PASS;
- full `result4-2.xlsx` readback: PASS;
- Q4-2 runtime drift under a different Python/SciPy build was isolated; formal numbers remain locked to the independently audited Python-3.12 replay.

Q4-3:
- independent accounting recomputation: PASS;
- 334×144 hard constraints, cross-day SOC, source split, ledger identity and causality: PASS;
- frozen Q3 lambda identity, 1,002 Feb–Dec rows: exact PASS;
- full `result4-3.xlsx` readback with `artifact_tool`: PASS and independently classified as CAUSAL;
- Q3 reconstruction / clean replay / tertiary tie-break diagnostics: PASS WITH NON-MODEL PATCH, no formal economic result change.

## Paper/freeze boundary

Q4 paper argument map, figure registry, number registry and figure-ready source data are complete. The Q4 result layer is now the only permitted source for Q4 paper numbers/figures.

The **whole-paper Submission Gate** (final PDF, anonymity, AI statement, file naming and upload checks) remains deferred to the global paper workflow and does not reopen Q4 unless it discovers a Q4 evidence inconsistency.
