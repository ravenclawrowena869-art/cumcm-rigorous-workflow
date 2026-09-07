# 条件触发 Gate 与证据协议 v2.2

本协议解决一个常见问题：**多个 Agent 都检查过，模型仍可能留下评委能攻击的结构性缺口。**

原因通常不是“没人检查”，而是所有人都在同一前提下检查代码是否可行，却没有根据模型结构自动触发对应的反证、稳定性、边界和接口语义验证。

因此，从 v2.2 起，Gate 不再只有“所有题通用检查”，还必须建立 **Conditional Gate Registry（条件触发 Gate 清单）**。

---

## 一、总原则：先识别触发器，再验收

每个子问题进入 `VALIDATING` 后，由 Model Owner 与至少一名非 Owner Reviewer 共同填写 Triggered Gate List。

任何满足触发条件的 Gate 都必须处于以下三种状态之一：

- `PASS`：验收标准满足，且存在可追溯证据；
- `PASS_WITH_LIMITATION`：模型主线可保留，但论文必须主动缩小 Claim；
- `FAIL / REOPEN`：关键证据缺失或验证失败，不得 Freeze。

禁止只写 `PASS=true` 而不记录证据文件和判定标准。

---

## 二、条件触发 Gate

### CG1 — Assumption Challenge Gate（关键假设挑战）

**触发条件**：存在会明显改变可行域、目标值或结论的重要简化假设，例如：

- 区域之间无交互/无交换；
- 忽略某类成本、损耗、传输或约束；
- 输入被假定确定；
- 某资源、网络或设备被视为同质；
- 为便于求解固定了原本可决策的结构。

**必须回答**：

1. 假设来自题面、附件、文献还是人为简化；
2. 如果移除/放松该假设，模型结构会如何改变；
3. 可计算时，至少做一个 assumption ablation、理想上界或对照；
4. 若暂时不能计算，必须在论文中限定适用范围，不得把简化模型结论写成普遍结论。

---

### CG2 — Path Dependence Gate（路径/顺序依赖）

**触发条件**：当前决策会改变后续可行域或评分，包括：

- 贪心逐个插入；
- 构造型启发式；
- 局部搜索；
- tie-breaking 会影响后续状态；
- 随机优化、多起点算法。

**必须检查**：

- 输入顺序扰动；
- 同优先级任务的 tie-breaking；
- 多随机种子/多起点（适用时）；
- 目标值、可行率、核心指标和最终策略的均值、标准差、极差；
- 若顺序敏感明显，报告最坏退化并考虑更稳健的排序或二次修复。

注意：**确定性算法重复运行得到相同结果，不等于没有路径依赖。**

---

### CG3 — Optimality Anchor Gate（启发式质量锚点）

**触发条件**：正式方案不是可证明全局最优的精确算法，却声称“高质量”“较优”“接近最优”或据此选为正式方案。

**至少完成一种**：

- 小规模 MILP/DP/枚举精确真值；
- LP 松弛或可核验下界；
- 已知可行上界；
- 多次独立运行的最好值与分布。

必须报告 gap 或可比较的质量指标。仅比较若干人工预设策略不能证明接近最优。

---

### CG4 — Feasibility Margin Gate（可行余量）

**触发条件**：结果通过硬约束，但一个或多个关键约束接近边界；或后续问题仍会继续改变当前解。

除 `violation=0` 外，必须报告关键 headroom/slack，例如：

- 容量余量；
- 碳预算余量；
- deadline slack；
- 电网购售电余量；
- SOC 上下界余量；
- SLA/时延余量。

若余量很小，应追加局部扰动测试，判断结果是否属于“脆弱可行”。

---

### CG5 — Feedback Safety Gate（反馈安全）

**触发条件**：存在 A→B→A 的交替优化、分解协调或跨模块反馈。

**必须检查**：

1. 上游调整动作是否可能让下游问题失去可行性；
2. 下游反馈是否同时包含收益信号与关键约束余量；
3. 任务/决策调整前是否有下游可行域预筛；
4. 若反馈导致不可行，是否有 rollback、步长缩小、区域禁入或恢复机制；
5. 每轮是否同时记录目标值、hard gate、服务质量和关键 headroom。

---

### CG6 — Derived Signal Validation Gate（派生信号语义验证）

**触发条件**：一个模型输出的派生量被另一个模型直接用作决策信号，例如：

- LP dual / shadow price；
- marginal value；
- score；
- surrogate risk；
- SHAP/importance；
- 估计梯度或灵敏度。

不能只验证字段、单位和行数。还必须验证**数学语义**。

推荐方法：抽取若干代表点，对原输入施加小扰动 `ε`，重求模型并比较

`(F(x+ε)-F(x))/ε`

与派生信号的符号、数量级和局部趋势是否一致。

若存在退化、非光滑、符号约定或尺度问题，必须记录并限制信号使用方式。

---

### CG7 — Convergence Credibility Gate（收敛可信度）

**触发条件**：论文出现“迭代”“收敛”“固定点”“交替优化”“直到稳定”等表述。

**必须区分**：

- 真正满足停止准则；
- 排程/解不再变化；
- 达到最大迭代次数；
- 改善低于阈值；
- 因不可行停止；
- 单步敏感性试验。

需要检查：

- 多初值/多起点（适用时）；
- 停止阈值变化；
- 是否出现振荡或循环；
- 不同场景的迭代轨迹和停止原因；
- 声称“收敛”时是否真的有足够证据。

---

### CG8 — Boundary Regime Gate（边界与局部窗口）

**触发条件**：存在终端状态、起始边界、峰值、约束切换、阶段切换、异常点、不可行点或政策阈值。

必须对这些位置做局部复算，并判断是否需要：

- 末端/起始窗口放大图；
- 峰值附近局部图；
- 约束激活前后对照；
- 边界值表；
- 单独的机制解释。

不是所有题都必须加局部图，但“是否需要”必须经过显式判断。

---

### CG9 — Comparison Fairness Gate（对照公平）

**触发条件**：论文比较两个以上模型、策略或方案，并据此声称某方案更优。

所有对照必须统一：

- 输入数据版本；
- 时域和样本；
- 可用信息；
- hard constraints；
- 指标定义；
- 初始条件；
- 求解预算/运行次数（适用时）。

若某基线被人为削弱或使用了不同信息集，必须明确说明，不得作为主要性能证据。

---

### CG10 — Scale & Plausibility Gate（数量级与物理合理性）

**触发条件**：正式结果出现异常漂亮、接近零、负值、极大值、数量级突变或与常识直觉冲突的现象。

必须独立检查：

- 单位与量纲；
- 分子/分母；
- 汇总时域；
- 符号约定；
- 是否重复计入/遗漏；
- 是否由题目边界条件或经济机制真实产生。

若结果真实但反直觉，正文必须解释机制，不能只报数字。

---

## 三、Gate Evidence 最低字段

每一个被触发的 Gate 至少记录：

```yaml
gate_id: CG2_PATH_DEPENDENCE
question: Q2
triggered: true
trigger_reason: "sequential greedy placement changes later feasible regions"
owner: "Q2 Model Owner"
reviewer: "non-owner reviewer"
status: PASS
criteria:
  - "30 perturbation runs all feasible"
  - "worst objective degradation < 1.5%"
evidence:
  - "validation/order_sensitivity.csv"
  - "validation/order_sensitivity_summary.json"
  - "figures/order_sensitivity.pdf"
limitations: []
waiver: null
```

Reviewer 不得仅凭 Owner 的口头说明签字。

---

## 四、角色隔离

- Model Owner 可以执行实验，但不能独立批准自己的关键 Gate；
- Technical Reviewer 负责运行、数据源、接口、复现和证据文件真实性；
- Mathematical Reviewer 负责触发条件、数学语义、对照公平和 Claim 是否过强；
- 跨模型反馈信号应优先由下游模块 Reviewer 或独立 Reviewer 验证；
- Red Team 不参与原模型构建，见 `07_AI协作/05_Red-Team独立评审协议.md`。

---

## 五、Waiver 规则

比赛时间不足时，允许 `PASS_WITH_LIMITATION` 或 waiver，但必须同时满足：

1. 明确记录未完成的 Gate；
2. 说明为什么无法补实验；
3. 主动缩小论文 Claim；
4. 在“模型局限”或对应结果段写明适用边界；
5. 不得把 waiver 项写成“已验证”。

缺少以上任一项，不能 Freeze。

---

## 六、Freeze 条件

一个模块只有在以下条件全部满足后才能进入 `FROZEN`：

1. 通用 Technical / Mathematical 验收通过；
2. `04_验收冻结/05_模型证据充分性Gate.md` 通过；
3. Triggered Gate List 已完成；
4. 所有 `triggered=true` 的 Gate 为 `PASS` 或有正式 limitation/waiver；
5. 每个 Gate 都有 Evidence；
6. Red Team 的阻断项已关闭或转化为明确 Claim 限制；
7. clean replay 与来源链完整。
