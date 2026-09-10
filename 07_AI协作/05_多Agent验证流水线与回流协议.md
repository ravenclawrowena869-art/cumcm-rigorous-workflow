# 多 Agent 验证流水线与回流协议 v1.0

本协议用于把多 Agent 自动化引入数模工作流，同时保持现有 Mathematical Gate、Freeze 和 Source of Truth 的严格性。它是**执行编排层**，不是新的科学裁决层；任何自动化系统都不得通过重试次数、时间预算或“流程继续”绕过正式 Gate。

## 1. 核心定位

多 Agent 流水线可以负责：

- 读题与任务拆解；
- 候选路线原型；
- 建模、编码、复算、解读；
- 图表与论文的受影响项更新；
- 审稿意见台账、返工分发；
- checkpoint、resume、失败恢复；
- 契约检查、干跑验证和流程复盘。

但以下裁决仍由 canonical workflow 决定：

- 模型是否有资格成为正式模型；
- Mathematical PASS 是否成立；
- hard constraints 是否全部通过；
- 结果是否可以 Freeze；
- 数字是否可以进入论文和最终提交。

## 2. ORCH-STATE-001：执行状态与科学状态分离

自动化系统至少区分两类状态：

```text
execution_status: RUNNING / BLOCKED / RETRYING / CONTINUING / STOPPED
validation_status: NOT_STARTED / VALIDATING / PASS / PASS_WITH_LIMITATION / FAIL_REOPEN / MATHEMATICAL_P0
```

允许某一模块 `validation_status=FAIL_REOPEN` 时，其他**不依赖该结论**的任务继续执行；这只表示流程没有整体停机，不表示该模块被科学放行。

硬规则：

- `execution_status=CONTINUING` 绝不等于 `validation_status=PASS`；
- 重试次数耗尽、Agent 超时、工具不可用、预算不足，都不能自动把 FAIL 改成 PASS；
- 任何 `FAIL_REOPEN` / `MATHEMATICAL_P0` 模块不得进入 `FROZEN`；
- 下游若依赖未通过验证的结果，只能使用明确标记的 mock / candidate / placeholder，不得伪装成正式数字。

## 3. ORCH-REDTEAM-001：信息隔离式红队复算

对论文头条数字、核心优化目标、关键排名/预测指标、关键可行性结论，应优先采用信息隔离式独立复算。

红队默认允许读取：

- 官方题面、规则、附件；
- 当前题的 Question Contract / 指标定义；
- 原始输入或已经冻结的合成/仿真输入；
- 待复算的结果声明：数值、单位、样本范围、聚合口径；
- 必要的公开数学定义。

红队默认禁止读取：

- 主建模代码与实现细节；
- 主建模者的推导笔记；
- 主结果目录中除“结果声明”外的中间产物；
- 用于暗示正确答案的审稿结论或预期差异清单。

红队必须从零建立独立计算路径。若信息隔离客观不可行，应在验收报告中说明原因，并改用次强独立性方案，不能把“另一个 Agent 看了一遍原代码”称为独立复算。

详细判定以 `04_验收冻结/01_独立验收协议.md` 为准。

## 4. ORCH-TOURNAMENT-001：候选路线小样锦标赛

当某一问存在两条以上合理路线、主模型尚未确定，或 baseline 暴露出明确结构缺口时，可以启动候选路线小样锦标赛。

要求：

1. 先经过模型资格筛查，明显违背题意、数据条件、时间预算或无法验证的路线不得参赛；
2. 通常保留 baseline + 1–3 个真正相关候选，不追求数量；
3. 在相同 reduced dataset / representative subset、相同信息边界、相近计算预算和统一指标下做原型；
4. 比较结构匹配、验证表现、稳定性、解释性、计算成本和下游接口；
5. 不允许用最终测试集反复选模；
6. 原型结束后必须收敛为 1 个主模型 + 最多 1 个备选，避免长期维护模型动物园。

最终模型选择仍执行 `02_开赛与拆题/02_模型选择协议.md` 与模型证据 Gate。

## 5. ORCH-CHECKPOINT-001：checkpoint 与断点续跑

长任务建议在以下边界落 checkpoint：

- 读题与数据审计完成；
- 候选路线裁决完成；
- 每问主结果产生；
- 独立验收完成；
- Freeze 前；
- 图表/论文一轮受影响项更新完成；
- 最终审稿轮完成。

checkpoint 至少记录：

```text
stage
question/module
source_commit
input_manifest_hash
config/version
completed_artifacts
pending_artifacts
validation_status
blocking_issues
next_action
```

恢复时必须核对 `source_commit`、输入 manifest 和关键配置。若这些内容已经改变，旧 checkpoint 只能作为参考，不得直接跳过受影响 Gate。

自动化运行时自己的临时 `run_state.json`、日志或 PID 不是团队正式 Source of Truth；它们必须能够追溯到 `project_state.yaml`、Task、Handoff、Frozen Source of Truth 或 Git commit / PR。

## 6. ORCH-CHANGESET-001：结果换版与影响传播

任何已被论文、图表或下游问题消费的正式数值发生变化时，必须生成“换版影响清单”，至少包含：

```text
metric/claim
old_value
new_value
unit
authoritative_source
reason_for_change
affected_questions
affected_tables
affected_figures
affected_sections
affected_abstract_claims
status
checked_by
```

更新顺序原则上为：

```text
重新求解/复算
→ 更新 Frozen Output / Paper Metrics
→ 更新图表与表格
→ 更新正文与摘要
→ 全文旧值残留检查
→ Paper Check
```

禁止只替换摘要中的最终数字，或出现“新表 + 旧图”“新正文 + 旧摘要”等混版。

详细来源链执行 `04_验收冻结/04_结果来源链.md`。

## 7. ORCH-LEDGER-001：返工台账是唯一正式回流入口

自动审稿、红队、图评、Paper Review 产生的问题，进入返工前必须落到台账。每条至少记录：

- issue_id；
- evidence；
- severity；
- affected artifact；
- owner；
- required gate；
- status：`OPEN / FIXING / NEEDS_RECHECK / RESOLVED / WONT_FIX_WITH_REASON`；
- verification evidence。

同一问题反复修改仍未解决时，应升级诊断层级：先判断是文字、实现、模型、数据还是接口病根，不能无限重复同一种表面修补。

任何 Agent 不得自己创建“0 条问题”的假审稿记录来覆盖旧台账，也不得自行把未复核问题改为 RESOLVED。

## 8. ORCH-GUARD-001：变化守卫与结构守卫

对定向修订任务，Agent 默认执行最小修改原则。

至少检查：

- 未点名章节是否被大面积重写；
- 主文件引用、章节、附录、图表文件是否意外丢失；
- 冻结数字、单位、变量名、场景名是否被无授权修改；
- 图表数量或正文页数出现异常突增/骤降时是否有解释；
- 结果换版后是否仍残留旧值。

守卫触发表示需要人工/Owner 复核，不应靠“模型自觉”忽略异常。

## 9. ORCH-DRYRUN-001：工作流本身也必须验证

修改自动化编排、状态机、Gate 调用、回流逻辑、resume、文件契约或运行时脚本后，在用于正式赛题前必须至少完成相关干跑。

建议最小场景集：

1. 全链路：正常从输入走到交付；
2. 中断续跑：在 checkpoint 后终止并恢复；
3. Gate FAIL：验证失败后不得进入 Freeze；
4. 级联换版：上游数字变化能触发下游图/表/文更新；
5. 红队不一致：分歧进入仲裁/重开，而非软放行；
6. 输入或 commit 改变：旧 checkpoint 不得错误跳过验证；
7. 工具故障：切换 Agent/工具，但不改变科学判据；
8. 旧值残留：能够发现至少一个故意注入的 stale value。

新增测试场景时，优先先证明它能在缺陷存在时 FAIL，再修复流程并确认 PASS，避免“永远通过”的伪测试。

## 10. ORCH-CONTRACT-001：生产者—消费者契约核对

跨 Agent、跨问题和跨论文流水线传递的结构化文件，应明确：

- producer；
- consumer；
- schema/version；
- required fields；
- unit；
- granularity；
- missing-value behavior；
- source/version/hash；
- failure behavior。

消费者读取的必需字段必须由生产者正式声明并实际产出。字段改名、单位变化、粒度变化或 schema 升级，都必须触发接口复核，不得靠 Agent 猜测兼容。

## 11. ORCH-NO-SOFTPASS-001：禁止科学 Gate 降级转正

自动化系统可以为了避免整体停工而“继续跑不依赖当前失败项的任务”，但**不允许科学 Gate 降级转正**。

以下情况均不得自动 PASS：

- 红队未复算；
- 独立验收超时；
- 多次返工仍不一致；
- hard constraint 仍有违反；
- 关键指标无法追溯；
- 预算耗尽；
- Agent 连续失败。

正确行为是：记录 `BLOCKED / FAIL_REOPEN / MATHEMATICAL_P0`，允许无依赖任务继续，并把缺口带到下一 checkpoint / Handoff。最终 Submission Gate 前，所有 hard blockers 必须清零。

## 12. 外部自动化框架的吸收原则

可以参考其他开源数模自动化框架的角色划分、回流设计、断点机制、干跑测试和故障经验，但不得无条件复制：

- 特定模型名、API 渠道、并发数、超时时间；
- 针对单次真题校准的评分阈值；
- 与本仓库 Mathematical Veto、Freeze 或 AI 合规冲突的软放行规则；
- 不能在本题复现或验证的外部 benchmark。

外部机制进入本仓库后，必须转换成平台无关、证据可核查、可由三角色 Review 的规则。
