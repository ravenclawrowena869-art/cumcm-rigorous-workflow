# Runtime Source Index

Runtime Lite 只保存执行所需规则与索引，不内置大型论文 PDF/PNG。

## Canonical workflow

- `README.md`：团队总架构与赛时入口。
- `AGENTS.md`：仓库级 Agent 行为规范。
- `00_总览/03_状态机与冻结规则.md`：正式状态机；多 Agent 场景下区分执行状态与科学验证状态，并规定 checkpoint 恢复边界。
- `02_开赛与拆题/02_模型选择协议.md`：模型选择优先级、baseline、停止规则与候选路线小样锦标赛。
- `02_开赛与拆题/05_HuggingFace研究资产协议.md`：ML / 预训练模型 / 外部公开数据的条件式研究与资产 provenance。
- `03_建模与代码/05_参数选择协议.md`：关键参数、阈值、步长、权重和算法控制量的证据链。
- `04_验收冻结/01_独立验收协议.md`：独立验收、信息隔离式红队复算、同口径复算与随机/合成输入冻结。
- `04_验收冻结/04_结果来源链.md`：Frozen Output → Paper Metrics → Figure/Table → Paper 的数字来源链，以及结果换版影响传播和旧值残留检查。
- `04_验收冻结/05_模型证据充分性Gate.md`：模型进入论文前的证据 Gate。
- `05_论文与图表/01_论文流水线.md`：论文生产线。
- `05_论文与图表/02_图表工作流.md`：Figure Registry 与图表证据链。
- `05_论文与图表/05_逐问写作与算法呈现Gate.md`：逐问论文表达 Gate。
- `06_协作与交接/05_Paper_Handoff规范.md`：模型到论文的正式交付。
- `06_协作与交接/06_三GPT协作与Skill共同维护.md`：多人共同维护、Repository Write Gate 与 Handoff。
- `07_AI协作/02_AI_Prompt模板.md`：角色化 Agent 任务模板。
- `07_AI协作/03_AI使用记录.md`：AI Use Ledger。
- `07_AI协作/04_平台无关Skill与Agent切换.md`：跨 ChatGPT / Codex / Claude 等平台的 Skill 与 Agent 切换规则。
- `07_AI协作/05_多Agent验证流水线与回流协议.md`：多 Agent 编排、红队隔离、checkpoint/resume、换版传播、返工台账、守卫、契约核对与干跑验证；明确禁止科学 Gate 软放行。
- `08_提交终检/01_FINAL_SUBMISSION_GATE.md`：最终提交 Gate。

## Runtime templates

- `templates/红队独立复算报告模板.md`：信息隔离式独立复算的标准报告。
- `templates/结果换版影响清单模板.md`：正式数字改变后的下游影响传播与 stale value 检查。
- `templates/Paper_Handoff模板.md`：模型向 Paper Lead 交付。
- `templates/任务单模板.md`：任务边界、输入、输出、冻结项和 Required Gate。
- `templates/Robustness_Plan模板.md`：敏感性与鲁棒性实验设计。
- `templates/Figure_Registry模板.csv`：图表来源、状态和论文位置。

## Rehearsal / Case Authority

- `09_本次比赛复盘/04_Q4赛前闭环演练Authority.md`：华数杯 C 题 Q4 专项闭环演练，包含 20% 调整上限敏感性、RegionA 不可行诊断和指定图表。它是 case authority，具体参数不升格为 Shared Core。

## 外置知识库

全文证据按需从以下来源检索：

1. 当前 ChatGPT Project Files / 项目来源；
2. GitHub 中的轻量 references、经验总结与 case notes；
3. Full Archive 中的原始优秀论文、截图与完整 corpus；
4. 任务明确要求时的外部学术检索。

### External Research Routing

当任务触发 HF Research Lane 时，可按以下角色使用 Hugging Face：

- **Hugging Face Papers**：语义发现论文与研究方向，最终数学依据仍回到原论文/正式页面；
- **Models**：定位模型仓库、revision、framework、license、Model Card 与硬件需求；
- **Datasets**：定位公开数据、字段、split、license、Dataset Card 与数据版本；
- **Spaces**：查 Demo、接口与实现线索，默认不作为数学依据；
- GitHub：追踪作者/官方实现并进入本地复现链；
- Local Benchmark：在本题冻结数据与评价口径下完成最终裁决。

Hugging Face 不可用时，回退到原论文 + Web/学术检索 + GitHub + 本地实验，不阻塞比赛主线。

## 赛题经验边界

- 2026 CUMCM：当前默认主选 C 题。
- 2026 华数杯 C：作为已结束的三等奖实战 Failure Evidence，不继续修改正式参赛版本；Q4 可以作为赛前复现演练 case。
- A-Track：保留 Objective Interpretation、Pathwise Validation、Numerical Engineering、Surrogate Fidelity、Optimization Adequacy 等可迁移经验。

## 重要原则

优秀论文用于学习结构、验证方式、写作和模型原型，不自动成为标准答案。外部自动化框架的角色划分、断点机制和回流设计也只能作为机制候选；进入本仓库后必须服从 Mathematical Veto、Freeze、独立验收和当前 evidence。Hugging Face 的 Model Card、Dataset Card、Space 或第三方 benchmark 同样不自动成为本题证据。正式结论仍由官方题面、冻结代码、独立复算和当前 evidence 决定。
