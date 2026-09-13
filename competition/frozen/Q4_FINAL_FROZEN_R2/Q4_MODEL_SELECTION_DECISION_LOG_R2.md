# Q4 Model Selection Decision Log — R2

Date: 2026-09-13

## Decision 1 — dynamic-price baseline

Candidate A: causal LAG7 same-slot price.
Candidate B: more complex causal forecasting (intraday correction / time-series / ML / scenario price model).
Diagnostic upper-information comparator: perfect future realized price (Oracle, non-deployable).

Evidence:
- LAG7 preflight MAE ≈ 0.04715 yuan/kWh, WAPE ≈ 6.224%, slot correlation ≈ 0.9811;
- Q4-2 perfect-price-information annual gap = 0.5372%;
- Q4-3 perfect-price-information annual gap = 0.4888%;
- both formal causal branches pass leakage/hard/accounting Gates.

Final choice: **LAG7 stays mainline; STOP EXPANSION.**

Reason: a more complex model has no validated material economic defect to solve. Tail effects are reported as a limitation but do not meet the mainline upgrade trigger.

## Decision 2 — Q4-2 controller

Inherited/frozen: `Q80_P2` from Q2. No alpha retuning under Q4.

Reason: dynamic positive price scales the normal/emergency asymmetry without by itself invalidating the Q80=0.8 critical-fractile logic; the frozen controller is preserved to isolate the effect of price information.

## Decision 3 — Q4-3 controller

Inherited/frozen: `B1B_PRIMARY_L1_MAE_W28_H14` from Q3; 00/06/12/18 stages retained.

Reason: Q4 studies the effect of dynamic prices while preserving Q3's validated causal rolling controller. The frozen lambda ledger is exactly inherited.
