# Shared Core v2.1

本文件对 FYQ、XXT、CYQ 三套 GPT 同时生效。任何 Role Profile 都不得覆盖 Shared Core。

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

## CORE-FREEZE-001 Freeze 边界

`FROZEN` 模型或结果只有出现 P0 问题时才允许重开，例如题意、硬约束、正式指标、数字、复现或官方合规错误。重开必须建立新版本并重跑依赖 Gate。

## CORE-EVIDENCE-001 Evidence before claims

“能够运行”不等于“可以写进论文”。任何核心结论先建立证据，再生成正文。缺少基线、独立复算、敏感性、稳健性、算法步骤或正式来源时，输出缺口清单或显式占位符，不用通用语言补齐。

## CORE-INTERFACE-001 Interface First

跨问依赖先冻结字段、单位、粒度、版本与失败行为；允许 Mock 解耦开发。下游不得偷偷使用真实应用时不可获得的未来值或未冻结结果。

## CORE-ROBUST-001 稳定性、敏感性、鲁棒性分开验证

按模型结构选择实验，不机械统一做 ±10%。关键结论应尽量给出稳定范围、敏感方向和失效边界。若预测、排序、聚类或简化模型作为下游决策 proxy，必须做 full replay 检查其真实决策收益。

## CORE-OPT-001 优化质量等级

- `FEASIBLE`：全部硬约束通过；
- `COMPETITIVE`：同口径下稳定优于合理 baseline；
- `NEAR-OPTIMAL`：另外有 exact anchor、bound、gap、强基线或其他最优性证据。

只满足约束不得写成“最优”。

## CORE-AI-001 AI 使用记录真实

从比赛早期维护 AI Use Ledger。AI 使用说明应如实反映实际参与深度，不以规避 AI 检测为目标。推荐流程：聊天记录 → 知识库 → 团队框架 → 人工重写。

## CORE-COLLAB-001 三人共同维护

GitHub main 是 Skill / Workflow 唯一正式源。三个人都可通过 branch + PR 修改仓库；未 merge 的聊天建议或个人 ZIP 不得宣称为团队正式规则。

## CORE-CODE-001 先测后跑与独立复算

关键公式、parser、leakage、hard constraints、边界、export schema 和 end-to-end smoke 应尽可能先建立测试。正式目标与核心指标不能只读取优化器报告值，应有独立复算。

## CORE-PAPER-001 论文服务于结论链

每问正文按“解决什么 → 为什么这样做 → 这样做有什么好处 → 如何求解 → 什么证据支持 → 如何服务下一问或全文结论”组织。模型优势必须有本题证据，不写教材式通用优点。
