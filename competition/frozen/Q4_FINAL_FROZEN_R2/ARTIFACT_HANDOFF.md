# Q4 FINAL_FROZEN R2 — Artifact Handoff

This GitHub record freezes the Q4 result identity, paper-number registry, validation evidence, and exact SHA256 provenance.

The full source/replay packages and official `.xlsx` workbooks are treated as **controlled binary artifacts** rather than duplicated into ordinary Git. This follows `competition/README.md`, which directs large/binary competition assets to Git LFS, controlled storage, or an explicit handoff method.

## Formal binary artifacts

- `result4-2.xlsx` — official Q4-2 causal workbook; SHA256 is pinned in `SOURCE_HASHES_R2.json` / `FREEZE_MANIFEST.csv`.
- `result4-3.xlsx` — official Q4-3 causal workbook; SHA256 is pinned in the same manifests.
- `Q4_FINAL_FROZEN_R2.zip` — full sealed Q4 frozen archive; hash pinned in `FREEZE_MANIFEST.csv`.

## Consumption rule

Paper/code consumers must verify the artifact hash against this Git record before using a controlled binary artifact. Paper numbers must be copied from `Q4_PAPER_NUMBER_REGISTRY_R2.csv`; chat text and screenshots are not formal sources.

Any model/code/settlement/formal-number change requires reopening Q4 under the canonical Freeze rule. Ordinary paper wording/layout edits do not.
