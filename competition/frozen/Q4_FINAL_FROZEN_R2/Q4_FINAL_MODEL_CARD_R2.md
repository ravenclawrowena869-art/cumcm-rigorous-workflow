# Q4 Frozen Model Card — R2

## Overall structure

Q4 does not introduce a new physical controller family. It freezes a **dynamic-price information layer** on top of the already frozen Q2/Q3 controllers.

### Price baseline

For day `d`, target slot `t`:

`p_hat(d,t) = p_realized(d-7 days,t)`.

The optimizer uses the causal `decision_price`; realized accounting uses the target-slot `settlement_price`. Future realized Attachment-4 prices never enter the formal causal optimizer.

### Q4-2

Inherited controller: `Q80_P2 / ANALYTIC_Q80_RESIDUAL_RESERVE_PLUS_CAUSAL_INTRADAY`.

Frozen inheritance includes alpha=0.80, L2_P3 forecast authority, storage physics, S1-A source split, no selling/refund, no emergency charging and free-bounded year-end terminal semantics.

Realized cost:

`C = Σ p_real*q_DA + Σ 5*p_real*r`.

### Q4-3

Inherited controller: `B1B_PRIMARY_L1_MAE_W28_H14`.

Frozen inheritance includes legal 00/06/12/18 stages, causal B1B PV-trust logic, beta=-0.5 and `DELIVERY_SLOT_PRICE` adjustment semantics.

Realized cost:

`C = Σ p_real*q0 + Σ p_real*(1.5*delta_plus - 0.5*delta_minus) + Σ 5*p_real*r`.

## Oracle diagnostic

Oracle changes only future decision-price information to the realized target-slot price. It does not change load/PV forecasts, controller family, storage constraints or settlement accounting. It is **not deployable** and is never used for the official result workbooks.

## Model-selection conclusion

LAG7 is retained because both frozen controllers have an annual causal-vs-Oracle gap below 0.6%. A more complex price predictor is not promoted without a new, validated defect that materially changes decisions/results.

## Important interpretation limits

- `DELIVERY_SLOT_PRICE` is inherited from Q3 and extended to dynamic price settlement as a modeling interpretation; the official statement does not spell out every advance price-fixing detail.
- Q4-3 versus Q4-2 reflects both algorithm/controller differences and a richer information/action set.
- Fixed-price Q3 versus dynamic-price Q4 costs are different environments, not direct controller-quality comparisons.
