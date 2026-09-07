---
name: cumcm-rigorous-workflow
description: Apply an evidence-driven workflow to CUMCM and similar mathematical-modeling competitions, including problem decomposition, model and code validation, paper drafting and review, figures, handoffs, freezing, conditional gates, red-team review, and final submission.
---

# CUMCM Rigorous Workflow

Treat the official problem, data, model, code, frozen results, figures, tables, and paper as one evidence chain. Do not invent results or write claims whose evidence has not been produced.

## Start from repository context

Read `README.md`, then the current competition's `project_state.yaml` when present, followed by only the workflow files relevant to the task. Respect `AGENTS.md` and the priority of official materials, frozen sources of truth, and current handoffs.

## Route the task

- For modeling, experiments, comparison, sensitivity, robustness, or infeasibility analysis, read `04_验收冻结/05_模型证据充分性Gate.md` before accepting a model as paper-ready.
- Before declaring validation complete, read `04_验收冻结/06_条件触发Gate与证据协议.md`, identify all triggered structural gates, and record evidence for each triggered item.
- For AI multi-agent review or independent attack, apply `07_AI协作/05_Red-Team独立评审协议.md`.
- For paper drafting, rewriting, or reviewing, read `05_论文与图表/01_论文流水线.md` and `05_论文与图表/05_逐问写作与算法呈现Gate.md`.
- For figures and tables, also read `05_论文与图表/02_图表工作流.md`.
- For model-to-paper transfer, use `06_协作与交接/05_Paper_Handoff规范.md`.
- Before submission, apply `08_提交终检/01_FINAL_SUBMISSION_GATE.md`.

## Enforce evidence before prose

For each subquestion, identify its required output, inputs, variables, constraints, method, solver, comparison baseline, validation, decisive result, uncertainty, and downstream interface. If a required experiment or frozen source is missing, return a missing-evidence list or explicit placeholder. Do not fill the gap with generic language.

Every non-trivial solution must have task-specific pseudocode or an algorithm flow that names the actual inputs, decision variables, feasibility checks, stopping rule, and output. A generic sequence such as “preprocess, build model, solve, analyze” does not pass.

## Trigger structural gates before Freeze

Do not assume that `hard constraint PASS` means the model is sufficiently validated. Trigger additional gates when the model contains:

- important simplifying assumptions;
- sequential greedy or path-dependent decisions;
- heuristic solutions requiring a quality anchor;
- hard constraints with small slack/headroom;
- alternating feedback between modules;
- derived signals such as dual values or marginal scores;
- convergence or iterative stopping claims;
- terminal, peak, switching, or infeasible boundary regimes;
- comparative performance claims;
- unusually large, small, negative, or near-zero results.

A triggered gate must have a non-owner reviewer, explicit pass criteria, and evidence files. Missing evidence blocks Freeze unless the claim is explicitly reduced and the limitation recorded.

## Preserve the freeze boundary

Do not modify a `FROZEN` model merely to improve presentation. Reopen it only for a demonstrated problem in question interpretation, constraints, metrics, official compliance, reproducibility, required validation, or an unresolved blocking Red-Team finding, and create a new version with dependent checks rerun.

## Completion condition

A paper section is complete only when its claims trace to frozen evidence, all triggered gates are resolved, blocking Red-Team items are closed or converted into explicit claim limitations, its algorithm presentation passes the writing Gate, its tables and figures are referenced and readable, and its language states the problem-specific logic directly.
