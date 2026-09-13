# Q4 Paper Argument Map — R2

## Core narrative

1. **New difficulty:** electricity price is no longer a fixed known daily template; future realized dynamic prices cannot be assumed known in advance.
2. **Causal price layer:** use strict same-slot LAG7 as the formal future-price baseline; separate decision price from realized settlement price.
3. **Q4-2:** keep frozen Q2 Q80_P2 unchanged and replace only the price-information/settlement layer.
4. **Q4-3:** keep frozen Q3 B1B rolling controller unchanged; at 00/06/12/18 optimize future slots with legal LAG7 prices while PV information updates causally.
5. **Validation:** both branches pass 334-day causal replay, hard constraints, accounting and workbook readback.
6. **Economic result:** Q4-3 costs 15.866 million yuan versus Q4-2 19.573 million yuan under the same causal LAG7 price baseline; the difference is mainly emergency-purchase reduction.
7. **Price information value:** perfect future price information improves annual total by only 0.537% (Q4-2) and 0.489% (Q4-3), so no extra price-model complexity is justified.
8. **Boundary:** Q4-3/Q4-2 is a richer-information/action-set comparison, not a pure algorithm-only win; Oracle is diagnostic only.
