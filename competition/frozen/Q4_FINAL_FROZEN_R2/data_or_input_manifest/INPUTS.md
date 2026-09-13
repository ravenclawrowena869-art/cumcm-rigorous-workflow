# Q4 input manifest

The uploaded code is the frozen source, but full-year replay still depends on the frozen competition inputs.

## Q4-2

Primary source package: `Q4_XXT_R2_FORMAT_FIXED.zip`.

Required runtime inputs include the official attachments, frozen Q2 annual forecast, January residuals, Q80 margin audit and LAG7 price forecast carried by that package. The formal runtime lock is `src/q4_2/RUNTIME_LOCK_R2.json`.

## Q4-3

Primary source package: `Q4_FYQ_FEEDBACK_R2_FIXED.zip`.

Required runtime inputs include the official attachments, frozen Q2 annual forecast, Q3 frozen controller references and LAG7 price forecast carried by that package.

The source package SHA256 values remain recorded in the Q4 freeze manifest and source-hash registry. Input files must be taken from those sealed packages for a formal replay.
