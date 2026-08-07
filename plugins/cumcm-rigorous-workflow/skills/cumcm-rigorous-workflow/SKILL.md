---
name: cumcm-rigorous-workflow
description: Apply a rigorous, evidence-driven workflow to CUMCM and similar mathematical-modeling competitions. Use for contest problem decomposition, team planning, data audits, model selection and comparison, coding tasks, validation, paper drafting or review, handoffs, time-block logs, and final submission checks. Also use when reviewing a teammate's modeling result or deciding whether a complex model is justified.
---

# Rigorous CUMCM Workflow

Treat the model, code, numerical results, paper, and required submission files as one evidence chain. Prioritize answering the stated question reproducibly over displaying model complexity.

## Set the operating mode

Identify whether the user asks to plan, analyze, implement, review, write, or submit. Do not mutate files when the request is only to analyze or review. When implementation is requested, make the smallest complete change, test it, and report outputs, risks, and unfinished work.

When the request spans a competition time block, maintain a compact work log with:

- actual start and end time;
- task and owner;
- expected deliverable and acceptance condition;
- actual result, blocker, and next handoff.

Use this log later to reconstruct the team's workflow figure. Do not invent missing historical activity; mark it unknown and ask when it matters.

## Build a question contract before selecting models

For every subquestion, record:

1. required final output;
2. scope, horizon, granularity, and units;
3. input tables, fields, and join keys;
4. estimated parameters or decision variables;
5. hard constraints and required output format;
6. evaluation or acceptance metric;
7. output passed to later subquestions.

Give each subquestion one primary output, not necessarily one model. Add supporting statistical, predictive, or optimization components only when they serve that output.

## Audit data before modeling

Keep raw files read-only. Check schema, sheet names, row counts, keys, duplicates, missingness, ranges, units, time and spatial granularity, and cross-file relationships. Record every cleaning rule and the number of affected rows.

Before splitting data, identify dependence:

- repeated observations from one subject require subject-aware splitting and usually mixed models, GEE, clustered inference, or grouped bootstrap;
- multi-region, multi-item, or multi-device time series require group-wise lag and rolling features;
- time prediction requires chronological or rolling-origin validation;
- preprocessors must be fit on training data only;
- current or future targets must never enter predictors.

## Use a model ladder

Start with the simplest runnable baseline that answers the question. Compare candidates on the same data split, metrics, constraints, and output definition.

Promote a more complex model only if at least one condition holds:

- it fixes a structural defect in the baseline;
- it produces a material and stable out-of-sample improvement;
- it enables a required uncertainty, feasibility, or decision output;
- it remains explainable and reproducible within contest time.

Do not claim superiority from one favorable split, a tiny untested difference, or in-sample fit. Do not convert correlation into causation or treat an optimizer status alone as proof of physical feasibility.

Use [model-routing.md](references/model-routing.md) for task-specific baselines, upgrades, and validation.

## Close the validation loop

Validate the failure mode that matters for the chosen model:

- prediction: naive/statistical baseline, grouped chronological backtesting, residuals, extreme errors, and uncertainty;
- classification: imbalance-aware metrics, confusion matrix, calibration, threshold cost, and subject-aware validation;
- ranking: indicator direction, weight source, equal-weight or alternative baseline, perturbation, and Top-k stability;
- clustering: scaling, K choice, multiple seeds or resampling, internal metrics, and interpretable cluster profiles;
- optimization: variable domains, all balances and bounds, solver status, objective recomputation, constraint and bound violations, benchmark strategies, sensitivity, and runtime;
- stochastic or robust models: parameter source, dependence among uncertain variables, quantiles, worst cases, feasibility rate, regret, and risk-parameter sensitivity.

Use [quality-gates.md](references/quality-gates.md) for formal review and submission checks.

## Preserve the evidence chain

Generate final tables and figures from the frozen result files or final script. Keep data filters, parameters, random seeds, objectives, constraints, units, and rounded values consistent across code, outputs, and paper.

For every important result, explain:

- the main pattern and decisive number;
- the comparison baseline;
- whether the gain is statistically, numerically, and practically meaningful;
- how it answers this question or feeds the next one;
- uncertainty, exceptions, and boundary conditions.

State limitations concretely and pair each with a possible remedy such as more data, a missing covariate, a grouped design, an uncertainty model, a tighter physical constraint, or a larger-scale solver.

## Coordinate the team by deliverables

Assign work dynamically by current bottleneck and member strength. Do not force permanent programmer/modeler/writer roles. During early ambiguity, compare a small number of bounded candidate routes in parallel; once evidence favors one route, converge and give one owner responsibility for the frozen result.

Every handoff must include:

- question and version;
- exact input files and fields;
- mathematical definitions and parameter values;
- produced files and test results;
- known risks and failed attempts;
- next owner, action, acceptance condition, and deadline.

Avoid three people independently redoing all questions unless the user explicitly wants an independent audit. Prefer one primary analysis plus targeted independent checks of high-risk assumptions.

## Apply competition gates

Use four gates, scaled to the actual contest duration rather than fixed clock hours:

1. Contract gate: questions, data map, baseline, and required outputs are clear.
2. Mainline gate: every question has a runnable path and the inter-question data flow closes.
3. Quality gate: key claims have baselines, diagnostics, sensitivity or robustness, and limitations.
4. Submission gate: final files regenerate, cross-document values match, and all required formats pass manual inspection.

Freeze model structure before final writing and submission checks. After freezing, change the main model only for a demonstrated critical defect.

## Route compute-power scheduling tasks

When the task involves AI data centers, workload migration, renewable energy, storage, electricity trading, carbon, latency, or multiobjective scheduling, read [compute-power-scheduling.md](references/compute-power-scheduling.md) before judging a model or implementation.

## Boundaries of the imported Atlas package

Treat the uploaded Atlas CUMCM v1.1 archive as a source of workflow ideas, not as authoritative code or citations. Do not cite its paper summaries without checking the original paper. Do not reuse its Python templates without task-specific tests. In particular, do not assume its generic time-feature builder is group-safe, its MILP diagnostic checks variable bounds, its winner-frequency logic handles ties, or its independent scenario generator preserves correlations.
