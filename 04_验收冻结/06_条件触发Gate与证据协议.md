# 条件触发 Gate Registry v2.2-lite

本文件不是“看到某算法就做某个固定实验”的对照表，而是一套**结构风险雷达**。它只负责回答：当前模型可能怎样翻车、这种风险是否真的存在、因此需要额外检查什么。

详细实验方法仍以 `04_验收冻结/05_模型证据充分性Gate.md`、Shared Core 和当前模型专属 validator 为准；本文件不重复定义实验步骤。

## 一、先找风险，再决定 Gate

进入 `VALIDATING` 后，不先按算法名称对号入座，而按下面四步扫描：

1. **看结构与 Claim**：模型怎样生成决策，哪些量会影响后续状态，论文准备声称什么；
2. **提出失败假设**：如果这里出错，最可能以什么方式改变可行性、方案排序、核心指标或论文结论；
3. **判断是否重要**：只有风险真实存在且可能影响正式结果/核心 Claim 时才触发对应 Gate；
4. **选择验证**：再去 Evidence Gate 或专属 validator 中选择合适的复算、扰动、对照或边界实验。

算法名、模型名和常见例子只是**风险线索**，不是自动触发器。一个模型可以同时命中多个风险；同一种风险也可以来自完全不同的算法。

建议先输出一张很短的风险表：

| 风险假设 | 为什么可能发生 | 可能影响 | 是否触发 | 对应 Gate |
|---|---|---|---|---|
|  |  | 可行性/排序/指标/Claim | YES/NO | CGx |

未发现真实风险时标记 `NOT_APPLICABLE`，不要为了形式完整机械补实验。

## 二、十类常见风险

### CG1 — 关键假设风险

风险问题：某个简化假设一旦被放松，是否可能明显改变可行域、目标值或主要结论？

常见线索包括区域独立、忽略损耗/交互、确定性输入、固定原本可决策的结构等，但是否触发取决于该假设对本题结论是否重要。

触发后：说明假设来源，并按需要做 ablation / counterfactual / 理想上界；无法验证时缩小论文 Claim。

### CG2 — 路径/顺序依赖风险

风险问题：当前一步的选择、顺序、并列处理或随机起点，是否会改变后续可行域、搜索路径或最终方案？

贪心、逐个插入、局部搜索、tie-breaking、随机优化、多起点只是常见线索，不是自动触发条件。

触发后：检查实际敏感来源，如输入顺序、并列规则、seed、初值或初始化策略，并观察可行率和核心指标是否被明显改变。

### CG3 — 最优性 Claim 风险

风险问题：论文对方案质量的表述，是否比现有证据更强？例如当前只有“可行”或“优于一个 baseline”，却准备写成“高质量、接近最优、最优”。

触发后：按 Claim 强度寻找 small-scale truth、MILP/DP/枚举、valid bound、relaxation、MIP gap 或其他可信 certificate。强 baseline 本身不能证明 near-optimal。

### CG4 — 脆弱可行风险

风险问题：虽然 `violation=0`，但解是否紧贴关键约束边界，以至于轻微扰动或下游修改就可能变成不可行？

触发后：检查真正相关的 slack/headroom，例如容量、deadline、SOC、SLA、碳预算或购售电余量；必要时做局部扰动。

### CG5 — 跨模块反馈风险

风险问题：一个模块的动作是否会改变另一个模块的可行域，而后者的反馈又反过来影响前者，从而出现不可行、震荡、误导性改善或循环？

交替优化、分解协调、A→B→A 反馈只是常见线索。

触发后：检查收益信号与关键余量是否同时被传递，并按需要检查预筛、rollback、步长缩小、禁入/恢复机制，以及每轮目标、可行性、QoS 与关键余量。

### CG6 — 派生信号语义风险

风险问题：某个中间量被下游当作“方向、价值、风险或重要性”来用时，它的数学含义是否真的支持这种用法？

LP dual / shadow price、marginal value、score、surrogate risk、SHAP/importance、估计梯度只是例子。

触发后：不能只检查字段和单位；应按模型结构用小扰动重求解或等价方法验证符号、数量级和局部趋势。若语义失真足以改变正式结果，按 Mathematical P0 处理。

### CG7 — 收敛 Claim 风险

风险问题：模型或论文声称“收敛、稳定、固定点”时，实际停止现象是否真的支持这个词？

触发后：区分满足停止准则、解不再变化、改善不足、达到上限、不可行停止等情况，并按需要检查阈值、振荡/循环、多初值和不同场景停止原因。

### CG8 — 边界与局部异常风险

风险问题：终端、起始、峰值、约束切换、阶段切换、异常点、不可行点或政策阈值附近，是否可能出现全局统计掩盖的问题？

触发后：做局部复算，并判断是否需要局部图、边界表或机制解释。不得为了“好看”随意挑窗口。

### CG9 — 对照公平风险

风险问题：两个模型/策略的比较，是否因为输入、信息、约束、初始条件或计算预算不一致而产生假优势？

触发后：统一真正影响比较公平性的口径。被人为削弱的 baseline 不得作为主要性能证据。

### CG10 — 数量级与合理性风险

风险问题：某个正式结果是否异常漂亮、接近零、负值、极大、突然跳变或明显反直觉，以至于需要怀疑单位、汇总、符号、重复计入或遗漏？

触发后：独立检查数量级与会计口径；若数字真实但反直觉，正文解释产生该现象的机制。

## 三、最低记录格式

```yaml
risk_id: RISK-01
risk_hypothesis: "sequential choices may change later feasible regions"
why_plausible: "current decision removes capacity available to later tasks"
material_effect: "may change feasibility and objective ranking"
triggered_gate: CG2_PATH_DEPENDENCE
question: Q2
owner: "Model Owner"
reviewer: "non-owner reviewer"
status: PASS
criteria:
  - "all selected perturbation checks feasible"
  - "observed degradation within accepted threshold"
evidence:
  - "validation/..."
limitations: []
waiver: null
```

## 四、Review 与 Waiver

- Model Owner 可以执行实验，但不能单独批准自己的关键 Gate；
- Reviewer 必须判断“风险假设是否成立”，而不是只看算法名称；
- Reviewer 必须看到证据文件，不能只听口头说明；
- 时间不足时允许 `PASS_WITH_LIMITATION` / waiver，但必须记录未完成项、原因、缩小后的 Claim 和论文中的限制位置；
- `FAIL / REOPEN` 或未关闭的阻断项不得进入 Freeze。

## 五、与其他 Gate 的关系

本文件负责“发现并归类风险”；Evidence Gate 和专属 validator 负责“如何验证”。若出现现有十类无法自然容纳、但可能实质影响正式结果的新风险，记录为 `CUSTOM_RISK`，不要为了套模板硬塞进 CG1–CG10，也不要立刻扩充成新的长期 Gate；先在当前任务中验证其重要性，再决定是否值得沉淀为通用规则。