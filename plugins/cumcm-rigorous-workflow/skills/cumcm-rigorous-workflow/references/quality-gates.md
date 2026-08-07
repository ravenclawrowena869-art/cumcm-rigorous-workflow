# Quality gates

## 1. Contract gate

- Every subquestion has a final output, scope, units, evaluation criterion, and required file format.
- Input sheets, fields, keys, time granularity, and cross-file joins are explicit.
- One runnable baseline exists for each main output.
- Later questions identify which earlier outputs they consume.
- Assumptions are necessary, testable where possible, and do not contradict the prompt.

## 2. Data gate

- Raw attachments are unchanged.
- Row counts before and after every filter are recorded.
- Missing values, duplicates, outliers, invalid ranges, and units are audited.
- Repeated subjects and grouped time series are identified before splitting.
- All lag, rolling, imputation, scaling, feature-selection, and dimensionality-reduction steps are free of future/test leakage.
- Multi-source joins have cardinality checks and unmatched-row reports.

## 3. Mathematical gate

- Sets, parameters, variables, domains, objectives, losses, and constraints are defined.
- Units balance in every key equation.
- Thresholds and penalty coefficients have data, prompt, literature, or sensitivity support.
- The chosen model directly produces the required output.
- Alternative models and rejection reasons are documented without overstating superiority.

## 4. Numerical and code gate

- A clean run regenerates outputs from documented inputs and configuration.
- Random seeds and dependency versions are recorded where relevant.
- Tests cover normal, boundary, invalid-input, and structure-specific cases.
- No NaN, infinity, silent coercion, dimension mismatch, or accidental index alignment remains.
- Optimization checks include variable bounds, constraint residuals, integrality, energy/material balances, objective recomputation, and solver gap/status.
- Runtime and memory are compatible with contest hardware and remaining time.

## 5. Evidence gate

- Main models are compared with a simple baseline under identical evaluation conditions.
- Validation matches dependence structure: grouped, subject-level, spatial, or chronological as required.
- Key modules have ablation or a structural necessity argument.
- Sensitivity covers influential assumptions, thresholds, weights, and uncertain inputs.
- Aggregate values do not hide important regional, group, horizon, or tail behavior.
- Improvements are described with effect size and uncertainty, not only favorable percentages.

## 6. Paper gate

- Abstract gives each question's method, key number, and conclusion.
- Symbols, parameters, units, and data ranges match code and result files.
- Every figure and table has a number, scope, unit, source, and interpretation.
- Each main result explains baseline, significance, decision meaning, exceptions, and next-question use.
- Correlation is not written as causation; prediction is not written as probability unless the model produces a probability.
- Limitations are specific and connected to plausible remedies.
- References have been read and verified from original sources.

## 7. Handoff gate

- Version, owner, inputs, outputs, tests, risks, next action, deadline, and acceptance condition are present.
- AI chat residue, placeholder prompts, personal paths, and temporary debug outputs are removed from formal deliverables.
- The teammate can reproduce the result without reconstructing missing context from chat history.

## 8. Submission gate

- Every prompt requirement has an identifiable answer location.
- Paper, code, tables, figures, and submission spreadsheets use the same frozen parameters and results.
- Required sheet names, column names, units, decimal places, and filenames are manually checked.
- Final files open successfully and a read-only backup exists.
- After the freeze point, only critical correctness or submission defects are changed.
