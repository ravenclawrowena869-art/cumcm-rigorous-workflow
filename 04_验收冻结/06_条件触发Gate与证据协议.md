# 条件触发 Gate Registry v2.2-lite

本文件不重复 `05_模型证据充分性Gate.md` 的通用验证方法，只负责回答：**当前模型有哪些结构性风险，应该额外触发哪些检查。**

使用顺序：先通过通用 Evidence Gate，再识别下列触发器。命中后执行对应检查并保存证据；未命中则标记 `NOT_APPLICABLE`。

## CG1 — 关键假设挑战

触发：存在会明显改变可行域、目标值或结论的重要简化假设，例如区域独立、忽略损耗/交互、确定性输入、固定原本可决策的结构。

要求：说明假设来源；可计算时做 ablation / counterfactual / 理想上界；不能计算时缩小论文 Claim。

## CG2 — 路径/顺序依赖

触发：贪心、逐个插入、局部搜索、tie-breaking、随机优化、多起点等当前决策会改变后续可行域或评分的算法。

要求：检查输入顺序、并列规则、seed/初值；报告可行率和核心指标变化。确定性重复得到相同结果不等于没有路径依赖。

## CG3 — 最优性锚点

触发：非精确算法却声称“较优、高质量、接近最优”。

要求：按 Claim 强度使用 small-scale truth、MILP/DP/枚举、valid bound、relaxation、MIP gap 或等价 certificate。只比较人工预设策略不能证明 near-optimal。

## CG4 — 可行余量

触发：虽然 `violation=0`，但关键约束接近边界，或下游还会继续改变当前解。

要求：报告关键 slack/headroom，如容量、deadline、SOC、SLA、碳预算、购售电余量；余量过小时做局部扰动，判断是否属于脆弱可行。

## CG5 — 反馈安全

触发：A→B→A 的交替优化、分解协调或跨模块反馈。

要求：检查上游动作是否会使下游不可行；反馈同时包含收益和关键余量；必要时有预筛、rollback、步长缩小、禁入或恢复机制；每轮同时记录目标、可行性、QoS 与关键余量。

## CG6 — 派生信号语义

触发：LP dual / shadow price、marginal value、score、surrogate risk、SHAP/importance、估计梯度等中间量被直接用于下游决策。

要求：不能只检查字段和单位；应通过小扰动重求解或等价方法验证符号、数量级和局部趋势。若语义失真足以改变正式结果，按 Mathematical P0 处理。

## CG7 — 收敛可信度

触发：论文或模型出现“迭代、收敛、固定点、交替优化、直到稳定”等表述。

要求：区分真正满足停止准则、解不再变化、改善不足、达到上限、不可行停止；检查阈值变化、振荡/循环、多初值（适用时）及不同场景停止原因。

## CG8 — 边界/局部窗口

触发：终端状态、起始边界、峰值、约束切换、阶段切换、异常点、不可行点、政策阈值。

要求：做局部复算，并显式判断是否需要局部放大图、边界表或机制解释。不得为了“好看”随意挑窗口。

## CG9 — 对照公平

触发：比较两个以上模型、策略或方案并据此声称更优。

要求：统一输入版本、时域/样本、可用信息、hard constraints、指标定义、初始条件和合理的求解预算。被人为削弱的 baseline 不得作为主要性能证据。

## CG10 — 数量级与物理合理性

触发：结果异常漂亮、接近零、负值、极大值、数量级突变或明显反直觉。

要求：独立检查单位、分子/分母、汇总时域、符号、重复计入/遗漏；若数字真实但反直觉，正文必须解释机制。

## 最低记录格式

```yaml
gate_id: CG2_PATH_DEPENDENCE
question: Q2
triggered: true
trigger_reason: "sequential placement changes later feasible regions"
owner: "Model Owner"
reviewer: "non-owner reviewer"
status: PASS
criteria:
  - "all perturbation runs feasible"
  - "worst degradation within accepted threshold"
evidence:
  - "validation/..."
limitations: []
waiver: null
```

## Review 与 Waiver

- Model Owner 可以执行实验，但不能单独批准自己的关键 Gate；
- Reviewer 必须看到证据文件，不能只听口头说明；
- 时间不足时允许 `PASS_WITH_LIMITATION` / waiver，但必须记录未完成项、原因、缩小后的 Claim 和论文中的限制位置；
- `FAIL / REOPEN` 或未关闭的阻断项不得进入 Freeze。

## 与通用 Gate 的关系

本文件只负责“触发什么”，详细实验做法仍以 `04_验收冻结/05_模型证据充分性Gate.md`、Shared Core 和当前模型专属 validator 为准。不要把同一验证规则复制到多个文件。