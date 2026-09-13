# Q4 FINAL_FROZEN R2 code and result files

This directory contains the two official Q4 result workbooks and the source files used by the frozen Q4-2 and Q4-3 branches.

## Result files

- `output/result4-2.xlsx`: official Q4-2 workbook.
- `output/result4-3.xlsx`: official Q4-3 workbook.

Their SHA256 values are recorded in `CODE_RESULT_SHA256SUMS.txt` and must match the frozen hashes.

## Q4-2

Source: `src/q4_2/`.

Formal annual numbers remain tied to the Python 3.12 runtime recorded in `src/q4_2/RUNTIME_LOCK_R2.json`. The source files are copied byte-for-byte from `Q4_XXT_R2_FORMAT_FIXED.zip`.

## Q4-3

Source: `src/q4_3/`.

The runtime used for the R2 standalone validation is recorded in `src/q4_3/environment.txt`. The source files are copied byte-for-byte from `Q4_FYQ_FEEDBACK_R2_FIXED.zip`.

## Inputs

Large competition inputs are not duplicated here. Required inputs and their frozen source packages are listed in `data_or_input_manifest/INPUTS.md`. Full replay must use the frozen input artifacts; do not substitute files with the same name from another run.

## Source identity

`CODE_SOURCE_MAP.csv` records the original source-package path for each uploaded code file. No comments or logic were rewritten for this GitHub copy.
