# Runtime Source Index

Runtime Lite 只保存执行所需规则与索引，不内置大型论文 PDF/PNG。

## Canonical workflow

- `README.md`：团队总架构与赛时入口。
- `AGENTS.md`：仓库级 Agent 行为规范。
- `04_验收冻结/05_模型证据充分性Gate.md`：模型进入论文前的证据 Gate。
- `05_论文与图表/01_论文流水线.md`：论文生产线。
- `05_论文与图表/02_图表工作流.md`：Figure Registry 与图表证据链。
- `05_论文与图表/05_逐问写作与算法呈现Gate.md`：逐问论文表达 Gate。
- `06_协作与交接/05_Paper_Handoff规范.md`：模型到论文的正式交付。
- `07_AI协作/02_AI_Prompt模板.md`：角色化 Agent 任务模板。
- `07_AI协作/03_AI使用记录.md`：AI Use Ledger。
- `08_提交终检/01_FINAL_SUBMISSION_GATE.md`：最终提交 Gate。

## 外置知识库

全文证据按需从以下来源检索：

1. 当前 ChatGPT Project Files / 项目来源；
2. GitHub 中的轻量 references、经验总结与 case notes；
3. Full Archive 中的原始优秀论文、截图与完整 corpus；
4. 任务明确要求时的外部学术检索。

## 赛题经验边界

- 2026 CUMCM：当前默认主选 C 题。
- 2026 华数杯 C：作为已结束的三等奖实战 Failure Evidence，不继续修改正式参赛版本。
- A-Track：保留 Objective Interpretation、Pathwise Validation、Numerical Engineering、Surrogate Fidelity、Optimization Adequacy 等可迁移经验。

## 重要原则

优秀论文用于学习结构、验证方式、写作和模型原型，不自动成为标准答案。正式结论仍由官方题面、冻结代码、独立复算和当前 evidence 决定。
