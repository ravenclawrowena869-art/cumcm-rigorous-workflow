# CUMCM2026 C题 Q4 FINAL_FROZEN R2

## Status

**Q4 = `FINAL_FROZEN`** at the problem-4 model/result level.

Formal deployable branches:

- **Q4-2:** frozen Q2 `Q80_P2` + `CAUSAL_PRICE_LAG7_R0`;
- **Q4-3:** frozen Q3 `B1B_PRIMARY_L1_MAE_W28_H14` + `CAUSAL_PRICE_LAG7_R0`.

Formal annual costs:

- Q4-2: **19,573,328.55 yuan**;
- Q4-3: **15,865,665.80 yuan**.

Under the same causal LAG7 price-information baseline, Q4-3 is lower by **3,707,662.75 yuan (18.9424%)**. This is interpreted as the economic value of additional intraday PV information plus rolling-adjustment rights, not a pure algorithm-only comparison.

Perfect-future-price Oracle gaps are **0.5372%** for Q4-2 and **0.4888%** for Q4-3, so the preregistered trigger for a more complex causal price model is not met. `STOP_EXPANSION` is frozen.

## Binary artifact policy

The full replay/source ZIPs and official `result4-2.xlsx` / `result4-3.xlsx` workbooks are controlled binary artifacts. They are not duplicated into ordinary Git in this record. Their exact SHA256 values are pinned in `SOURCE_HASHES_R2.json` and `FREEZE_MANIFEST.csv`, following `competition/README.md`'s controlled-storage / explicit-handoff rule for binary competition assets.

Paper numbers must be copied from `Q4_PAPER_NUMBER_REGISTRY_R2.csv`, not from chat text or screenshots.
