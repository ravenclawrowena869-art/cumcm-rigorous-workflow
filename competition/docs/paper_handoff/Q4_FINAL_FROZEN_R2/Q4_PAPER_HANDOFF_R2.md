# Q4 Paper Handoff — FINAL_FROZEN R2

## Recommended modeling wording

Problem 4 is treated as an extension of the frozen Q2/Q3 dispatch systems rather than a new controller family. The key additional uncertainty is the future real-time electricity price. To avoid future-information leakage, two price objects are separated: the price available when a decision is made and the realized delivery-slot price used for ex-post settlement. For future slots the formal controller uses the same-slot realized price seven days earlier, while the realized Attachment-4 price is only used after delivery for accounting.

For Q4-2, all Q2 `Q80_P2` forecast, reserve, storage and emergency-purchase rules remain unchanged. For Q4-3, all Q3 B1B rolling-update and trust-weight rules remain unchanged, including the 00:00/06:00/12:00/18:00 decision stages. Thus Q4 isolates the effect of dynamic price information instead of simultaneously replacing the upstream controller.

## Recommended result wording

Across the consecutive 334-day replay from 2025-02-01 to 2025-12-31, the causal Q4-2 strategy costs **19.573 million yuan**, of which **5.631 million yuan** is emergency-purchase cost. The causal Q4-3 rolling strategy costs **15.866 million yuan**, including **0.380 million yuan** of adjustment cost and **2.435 million yuan** of emergency-purchase cost.

Under the same causal LAG7 price-information baseline, Q4-3 reduces annual cost by **3.708 million yuan (18.942%)** relative to Q4-2. Emergency-purchase cost and energy fall by **56.758%** and **47.782%**, respectively. This should be attributed to the additional intraday PV information and rolling adjustment rights inherited from Q3, rather than described as a pure algorithm-only advantage.

To assess whether a more complicated electricity-price predictor is necessary, a non-deployable Oracle diagnostic supplies perfect future prices while keeping all other information and controller rules unchanged. The annual Oracle gap is only **0.537%** for Q4-2 and **0.489%** for Q4-3. Therefore the simple causal LAG7 price model is retained, and further price-model expansion is stopped. Localized high-price-tail effects are still reported as a limitation because large positive and negative daily/slot effects can offset in the annual net gap.

## Recommended formulas

Causal price forecast:

`p_hat(d,t) = p_realized(d-7,t)`.

Q4-2 realized accounting:

`C_Q4-2 = Σ_t p_t^real q_t^DA + Σ_t 5 p_t^real r_t`.

Q4-3 realized accounting:

`C_Q4-3 = Σ_t p_t^real q_t^0 + Σ_(h,t) p_t^real(1.5 Δq^+_(h,t) - 0.5 Δq^-_(h,t)) + Σ_t 5p_t^real r_t`.

The optimization stage uses the legal decision-price forecast for future target slots; the formulas above are realized settlement accounting.

## Headline numbers allowed in the paper

- Q4-2 causal total: **19,573,328.55 yuan**
- Q4-2 emergency cost: **5,630,885.96 yuan**
- Q4-2 emergency energy: **1,051,947.27 kWh**
- Q4-2 Oracle gap: **105,150.69 yuan (0.5372%)**
- Q4-3 causal total: **15,865,665.80 yuan**
- Q4-3 base cost: **13,050,650.15 yuan**
- Q4-3 adjustment cost: **380,123.57 yuan**
- Q4-3 emergency cost: **2,434,892.08 yuan**
- Q4-3 emergency energy: **549,309.86 kWh**
- Q4-3 Oracle gap: **77,551.51 yuan (0.4888%)**
- Q4-3 vs Q4-2 saving: **3,707,662.75 yuan (18.9424%)**
- Q4-3 vs Q4-2 emergency-cost reduction: **3,195,993.88 yuan (56.7583%)**
- Q4-3 vs Q4-2 emergency-energy reduction: **502,637.42 kWh (47.7816%)**

Every paper number must be copied from `Q4_PAPER_NUMBER_REGISTRY_R2.csv`, not from chat text.

## Do not write

- that the controller knows future realized Attachment-4 prices;
- that Oracle is a feasible strategy;
- that Q4-3 is “18.94% better because the algorithm is more advanced”;
- that LAG7 is universally optimal or that more complex price forecasting is always useless;
- that fixed-price-vs-dynamic-price cost difference measures controller quality.
