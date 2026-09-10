# Role Entry / Paper Framework v2.2.1 — Draft Review

## Scope and authority

- ACTIVE_ROLE: CYQ_PAPER; user authorized continuation of the role-entry and paper-framework change.
- Base: `ceb5b9c09046ab2189be83b5fa2871475467179b` (GitHub main checked on 2026-09-10).
- Branch: `cyq/role-entry-paper-framework-20260910`; status: proposal, not a team release.
- Existing Shared Core, FYQ/XXT Profiles, role IDs, handoff schemas and frozen contest artifacts remain unchanged.
- This change targets the shared GitHub workflow. It does not update the installed personal Skill.

## Why / behavior change

The existing shared core and role profiles already define responsibilities, but users need direct role entrypoints and a way to start paper work before results are ready. Add navigation over existing authorities, preserve approved per-question structures, request figure fields early, and distinguish draft material from supported conclusions.

## Validation performed

- `python3 -m unittest discover -s tests -v`: 40 tests passed, including the existing contract suite and the new navigation, release, `TECH_DIRECTION_STABLE`, two-level handoff and role-entry boundary checks.
- `python3 tools/validate_runtime_skill.py .`: PASS.
- `python3 tools/build_runtime_skill.py`: PASS, 34 runtime files.
- `python3 tools/validate_runtime_skill.py dist/cumcm-rigorous-workflow-runtime-lite`: PASS.
- Skill Creator frontmatter validation on the built runtime: PASS.
- `git diff --check`: PASS.
- New navigation checks resolve links in source and built runtime, preserve profile bytes in the build, reject mismatched manifest and VERSION releases, verify that the runtime has one SKILL.md, and cover the paper-waiting route's no-guess/no-unapproved-run boundaries.

The release validator now compares manifest and dispatcher versions, plus VERSION.md in repository mode, instead of requiring the historical value 2.1.4. Component documents may retain their own older versions when unchanged.

## Independent forward use

One independent agent received only the workflow path, CYQ role, and an isolated practice request: a weekly-sales forecasting paper comparing seasonal naive and ridge regression while rolling validation is unfinished and the downstream replenishment model is undecided. The user-approved three-section outline was supplied as task input. The agent had no expected answer or proposed diagnosis and did not modify files or access external services.

Observed output:

- Preserved the approved Q1 sections and gave a short introductory paragraph below the question title.
- Kept Q2 provisional and deferred inventory/cost claims until a common replenishment rule and replay exist.
- Requested object/week identifiers, train cutoffs, actual/predicted values, units, metric definitions, sample scope, configurations and source versions.
- Did not invent results, declare a winning model, import scheduling-specific parameters, or start technical work.

This is one bounded behavioral trial, not proof of general reliability or a substitute for required role review.

## Source limitation and remaining release gates

The three project-mandated original archives could not be located in the PR author's current workspace or by exact and shortened Library title searches:

- `write-update-math-modeling-paper-complete.zip`
- `math-modeling-master-workflow-v2.2.0.zip`
- `cumcm-rigorous-workflow-main (1).zip`

Two role reviews were received on 2026-09-10:

- FYQ technical review (`REQUEST_CHANGES / KEEP_DRAFT`), source ZIP SHA-256 `2143217b8f658ac923b08c9590583aa07c19037ceffeb3df4c3bc1f0ba2cf608`;
- XXT joint PR #14/#15 review, source DOCX SHA-256 `fcc5a82daefe778e5bba75092f701adf67b1c8a2cd6f2ee89903dfe77eb955cc`.

XXT's report states that it jointly checked the current PRs against all three archives and provides a high-level Gate crosswalk. This is evidence that the sources were reviewed by another role, but it does not include archive hashes, exact file readability records, or a complete source-diff/conflict disposition for the files changed by PR #15. Therefore `SOURCE_CONFORMANCE` advances from “no review evidence” to `PARTIAL / INCOMPLETE`, not PASS.

The review-requested semantic patches are included in v2.2.1: `TECH_DIRECTION_STABLE`, separate `Pre-Paper Brief` and `Formal Paper Handoff`, and high-risk strong claims moved out of the expression library. These changes require a focused output/consumer re-review because the cross-role handoff interface changed.

PR #14 remains unmerged. PR #15 reserves v2.2.1, stays Draft, and must be rebased onto the v2.2.0 main produced by PR #14 before release validation. Until then the current branch is not a deployable team release.

Keep the PR in draft until source conformance, PR #14 integration, and the review ownership in `06_协作与交接/06_三GPT协作与Skill共同维护.md` are satisfied. FYQ reviews runtime/engineering; CYQ reviews paper/figure rules. The revised two-level handoff needs output-side and consumer-side confirmation. No approval or merge is recorded by this report.

## Migration

No old file is moved or deleted. Existing Profile paths remain valid; new role files route to them. No competing shared handoff protocol or independent role Skill is introduced. The runtime builder includes the new navigation and paper references. Merge and deployment remain separate from this draft delivery.
