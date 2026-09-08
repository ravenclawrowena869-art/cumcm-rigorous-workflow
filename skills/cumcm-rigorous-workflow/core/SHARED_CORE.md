# Shared Core v2.1.1

本文件对 FYQ、XXT、CYQ 三套 GPT 同时生效。任何 Role Profile 都不得覆盖 Shared Core。

## CORE-INVOKE-001 每次回答前调用 Skill

对本项目的每一次实质性回答、审查、分工、建模、编程、论文或图表任务，**每次回答前必须先调用一次本 Skill**，完成 dispatcher → Shared Core → 当前 `ACTIVE_ROLE` Profile → 相关 canonical Gate/workflow 的本轮加载。

不得以已在上一轮读取过为由跳过，也不得仅凭聊天记忆替代本轮 Skill 调用。若平台支持原生 Skill invocation，优先调用 canonical Skill；若只能读取仓库，则按 dispatcher 规定的最小文件集合完成等价调用。无法完成本轮调用时，应先说明阻断原因，不得声称已按 Skill 执行。

## CORE-AUTH-001 官方材料最高优先级

正式事实优先级：

1. 当届官方题面、规则、模板、附件；
2. 当前比赛 `project_state.yaml`；
3. 已冻结的 Source of Truth、接口、模型与结果；
4. 本仓库 canonical workflow / Gate；
5. 当前 Task / Handoff；
6. 聊天中的临时描述。

出现冲突时必须指出冲突，不自行猜测。

## CORE-STATE-001 正式状态只从共享载体同步

三套 GPT 不以“另一边聊天里说过”为正式同步依据。正式共享状态只认：

- `project_state.yaml`；
- Task；
- Interface；
- Handoff；
- Frozen Source of Truth；
- Figure Registry；
- Git commit / PR。

## CORE-MATH-AUTH-001 Mathematical Veto

FYQ 负责统一技术路线、版本和集成，XXT 负责 Mathematical Gate。以下任一问题一旦被证实，XXT 有正式否决权，`mathematical_pass=false`，模块不得进入 Freeze：

- objective definition / objective direction 错误；
- hard constraint 缺失、写错或实现未保持；
- 单位、量纲、时间尺度或统计口径不一致；
- 正式候选解不可行或存在未解释的 hard violation；
- 正式指标、成本、收益、碳排、概率等 accounting / metric 口径错误；
- surrogate / proxy 与正式目标或正式决策严重失真，足以改变可行性、方案排序或论文核心 Claim。

XXT 的 veto 是数学裁决，不等于 XXT 接管 Git、版本或长期维护第二套主模型。修复仍由 FYQ 统一集成；若问题影响已冻结结果，XXT 可以要求 `P0 REOPEN`。

## CORE-PAPER-AUTH-001 Paper Lead 技术事实只读

CYQ / Paper Lead 对当前 Frozen Source of Truth、Mathematical PASS、正式参数、单位、指标口径和正式数字只读。

CYQ 可以读取、引用、发现冲突、返回 Evidence Gap，并向 FYQ / XXT 发起 `reopen request`；CYQ **不得自行修改**数学模型、目标与 hard constraints、正式数字、冻结参数、单位、技术口径或验证结论。

若论文叙事与技术事实冲突，必须以技术事实为准并停止相关定稿。任何技术事实变更都必须回到对应技术 Owner，重新 Review、重新 Freeze 后再进入论文。

## CORE-FREEZE-001 Freeze 边界

`FROZEN` 模型或结果只有出现 P0 问题时才允许重开，例如题意、hard constraints、正式指标/accounting、单位量纲、数学可行性、复现、material surrogate fidelity 或官方合规错误。重开必须建立新版本并重跑依赖 Gate。

“最小修改”“不推翻主线”等专项 authority 不能阻止已证实的数学 P0 重开；它们只限制非 P0 的范围扩张。

## CORE-FREEZE-002 Validation 是 Freeze 的硬前置

`G3_FREEZE` 只能在当前版本 `G2_VALIDATION=PASS` 后进入。最新 Mathematical Review 必须是当前 Source of Truth / 当前 commit 对应的有效 PASS，且不存在未清除的 Mathematical Veto / `P0 REOPEN`。

FYQ 可以管理 Freeze，但不得通过手工修改 state、manifest、Handoff 或换命名空间绕过 Mathematical PASS、独立复算、hard-constraint replay 或 Evidence Gate。任何影响目标、约束、单位、指标口径、surrogate fidelity 的代码/配置改动都会使旧 Mathematical PASS 失效，必须重新 Review。

## CORE-EVIDENCE-001 Evidence before claims

“能够运行”不等于“可以写进论文”。任何核心结论先建立证据，再生成正文。缺少基线、独立复算、敏感性、稳健性、算法步骤或正式来源时，输出缺口清单或显式占位符，不用通用语言补齐。

## CORE-INTERFACE-001 Interface First

跨问依赖先冻结字段、单位、粒度、版本与失败行为；允许 Mock 解耦开发。下游不得偷偷使用真实应用时不可获得的未来值或未冻结结果。

## CORE-DYNAMIC-001 动态约束必须全过程 replay

对 SOC、库存、状态变量、轨迹、累计预算/排放、ODE/PDE 状态、安全距离、滚动容量等 path-dependent / stateful hard constraints，validator 必须检查完整时间、空间或迭代轨迹，而不是只看终端状态。

至少记录：

- `max_violation`；
- 发生位置 `argmax_location`（时段/区域/实体/迭代）；
- terminal violation（适用时）；
- 状态递推/守恒残差（适用时）。

若模型没有动态约束，可显式标记 `NOT_APPLICABLE`；不能用“最终状态合法”替代全过程 Mathematical PASS。

## CORE-ROBUST-001 稳定性、敏感性、鲁棒性分开验证

按模型结构选择实验，不机械统一做 ±10%。关键结论应尽量给出稳定范围、敏感方向和失效边界。若预测、排序、聚类或简化模型作为下游决策 proxy，必须做 full replay 检查其真实决策收益。

若 full replay 显示 surrogate / proxy 的失真足以改变正式可行性、正式方案排序或核心 Claim，则视为 Mathematical P0；若不影响正式结论，才允许降级为初始化、筛选或加速工具并带 limitation 使用。

## CORE-OPT-001 优化质量等级

- `FEASIBLE`：全部 hard constraints 通过，正式目标与核心指标已独立复算；
- `COMPETITIVE`：同一数据、口径和约束下，稳定优于至少一个合理 baseline，并通过与算法结构匹配的顺序/初值/随机性检查；
- `NEAR-OPTIMAL`：在 `COMPETITIVE` 基础上，另有可量化的最优性证据支持剩余 gap 足够小，例如 exact anchor、valid bound、MIP gap、relaxation gap、small-scale truth 或等价 certificate。

强 baseline 本身只能支持 `COMPETITIVE`，不能单独证明 `NEAR-OPTIMAL`。只满足约束不得写成“最优”。

exact anchor / bound / MILP benchmark 按 Claim 强度、模型类型和计算预算条件触发：若只声称 `FEASIBLE`，不得为了形式完整机械增加大型 exact 求解；若声称 near-optimal，必须有与该 Claim 匹配的最优性证据。

## CORE-AI-001 AI 使用记录真实

从比赛早期维护 AI Use Ledger。AI 使用说明应如实反映实际参与深度，不以规避 AI 检测为目标。推荐流程：聊天记录 → 知识库 → 团队框架 → 人工重写。

## CORE-AI-DISCLOSURE-001 AI Disclosure 是阻断 Gate

对 `adopted=yes` 且进入论文、正式代码、正式图表或核心结论的 AI 产物，AI Use Ledger 必须填写并可核查：

- `human_verification`；
- `team_decision`；
- `human_changes`；
- `paper_location`；
- `artifact`。

上述任一必需字段缺失，或 Ledger 与实际 AI 参与程度不一致，则 `AI Disclosure Gate FAIL`，不得进入最终提交状态。`paper_location` 对不进入论文但进入正式代码/图表的产物可写 `NOT_APPLICABLE`，但 `artifact` 必须指向正式载体。

“聊天记录 → 知识库 → 团队框架 → 人工重写”用于人工核验与责任闭环，不得被解释成掩盖或弱化真实 AI 使用。

## CORE-COLLAB-001 三人共同维护

GitHub main 是 Skill / Workflow 唯一正式源。三个人都可通过 branch + PR 修改仓库；未 merge 的聊天建议或个人 ZIP 不得宣称为团队正式规则。

## CORE-CODE-001 先测后跑与独立复算

关键公式、parser、leakage、hard constraints、边界、export schema 和 end-to-end smoke 应尽可能先建立测试。正式目标与核心指标不能只读取优化器报告值，应有独立复算。

## CORE-PAPER-001 论文服务于结论链

每问正文按“解决什么 → 为什么这样做 → 这样做有什么好处 → 如何求解 → 什么证据支持 → 如何服务下一问或全文结论”组织。模型优势必须有本题证据，不写教材式通用优点。
