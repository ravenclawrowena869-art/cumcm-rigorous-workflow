# 模型证据充分性 Gate v2.2-lite

模型能够运行，只说明进入了验证阶段。进入 Freeze 和 Paper Handoff 前，必须确认结论有足够 evidence。

关键参数的正式选取必须同时遵守 `03_建模与代码/05_参数选择协议.md`。本 Gate 负责“有哪些验证方法和证据标准”；`04_验收冻结/06_条件触发Gate与证据协议.md` 负责“当前模型为什么需要哪些额外验证”。模型类型、算法名称和历史案例只能提供风险线索，不能机械推出固定实验清单。

验证顺序应是：

```text
先确认基础数学/技术正确
→ 看结构与 Claim，提出失败假设
→ 判断风险是否可能实质影响正式结果
→ 再从 Evidence Gate / 参数选择协议 / 专属 validator 中选择匹配验证
```

不要为了形式完整把所有检查都做一遍；也不能因为模型名称“不在清单里”就跳过真实风险。

## 一、结论—证据表

每个拟写入正文的核心结论记录：

| 结论 | 所需证据 | 实际文件/字段 | 状态 |
|---|---|---|---|
| 当前模型优于备选 | 同口径 baseline / challenger |  |  |
| 算法接近最优 | exact anchor、small-scale truth、bound 或 gap |  |  |
| 结果稳定 | 多种子、重排、重采样、重复划分 |  |  |
| 参数选择合理 | 参数语义与是否必须固定 + 题面/理论/可比文献/数据先验 + 合理搜索范围 + 参数扫描/重求解或自适应比较 + 选择准则 + 邻域/跨场景复核 |  |  |
| 模型鲁棒 | 噪声、情景、结构扰动或分布漂移 |  |  |
| 区间有保护作用 | downstream replay / violation-risk reduction |  |  |
| 结构假设合理 | counterfactual / idealized bound |  |  |
| 不可行有现实原因 | 最小可达边界、slack、IIS 或 binding constraints |  |  |

没有证据的结论只能标记待验证，不得改成更肯定的措辞写进论文。

## 二、优化质量等级

### FEASIBLE

全部 hard constraints 通过，目标与核心指标已独立复算。若存在动态/path-dependent hard constraints，还必须完成全过程 replay。

### COMPETITIVE

在同一数据、口径和约束下，稳定优于至少一个合理 baseline，且已经处理会实质影响比较结论的初值、顺序、随机性或其他结构风险。

### NEAR-OPTIMAL

在 COMPETITIVE 基础上，还有 exact anchor、下/上界、MIP gap、松弛界、small-scale truth 或其他可信最优性证据支持剩余 gap 足够小。

强 baseline 本身只能支持 COMPETITIVE，不能单独证明 NEAR-OPTIMAL。禁止把 `FEASIBLE` 直接写成“最优”。

exact anchor / bound / MILP benchmark 按 Claim 强度、模型结构和计算预算条件触发：如果只声明 FEASIBLE，不为形式完整机械增加大型 exact 求解；如果声称 near-optimal，必须给出与该 Claim 匹配的最优性证据。

## 三、模型类型提供“风险线索”，不是固定实验菜单

以下分类用于提醒常见失败模式。只有当相应风险在当前题目中真实存在、且可能影响正式结果或核心 Claim 时，才执行对应额外检查；未触发可标记 `NOT_APPLICABLE`。

### 预测模型

可能需要关注：

- 是否缺少合理朴素/统计 baseline；
- 时间顺序是否正确；
- 是否存在极端误差、系统性偏差、结构突变或分布漂移；
- 给出区间时，coverage、width 是否合理，以及区间是否真的保护后续容量、调度或风险决策；
- 预测结果进入下一问时，误差是否可能改变下游决策。

若这些风险存在，可使用时序 challenger、drift stress test、误差传播、上下界/情景 replay 等方法验证。不能因为 GroupedMean、历史均值等方法简洁稳定，就跳过时序适配性审查。

### 启发式、贪心与随机优化

可能需要关注：

- 任务处理顺序、并列规则、随机种子、初值或停止条件是否会改变后续搜索路径；
- 结果是否对 permutation / shuffle / 多起点敏感；
- 当前 Claim 是否需要 exact anchor、下界或 small-scale truth；
- Top-K、候选比例、惩罚、步长、调整比例等 materially 影响结果的算法参数是否有 Parameter Evidence。

只有存在相应风险时，才做重排、多种子、多起点、MILP/DP/枚举/松弛等实验。确定性重复得到相同结果，不能单独排除路径依赖。

参数相关风险不在这里再复制一套规则：先按 `03_建模与代码/05_参数选择协议.md` 判断参数语义和是否必须固定，再给出可解释搜索范围、参数扫描/重求解或自适应规则及选择依据。

如果主线 authority 已冻结为最小修复，不要求额外建立一套完整竞争主模型；可以按 Claim 强度使用小规模 anchor 或下界完成性能锚定。

### LP、MILP、CP-SAT 与其他约束优化

基础验收仍必须：独立复算 objective、变量边界、平衡式和全部 hard constraints，并报告 solver status、runtime、gap（适用时）和最大违反量。

额外检查按风险选择，例如：

- 若“区域独立”“无互联”“确定性输入”“无限网络”等结构假设可能改变结论，做 counterfactual、理想上界或限制说明；
- 若结果对容量、功率、预算、权重、阈值等参数敏感，按 Parameter Evidence Gate 做改参数→重新求解；
- 参数扫描前先给出范围来源；文献只有在参数定义、尺度和作用机制可比时才可用于缩小先验范围，不得把别题中的相似百分比直接移植；
- 储能等双参数设备若容量与功率共同决定结论，可形成容量×功率 sensitivity surface。

### 动态、状态空间与路径依赖模型

凡 hard constraint 依赖完整轨迹而不是单一终值，例如 SOC、库存、温度、水位、速度/加速度、动态安全距离、累计预算/排放、ODE/PDE 状态、滚动容量等：

- validator 必须逐时段/逐空间点/逐迭代 replay；
- 至少报告 `max_violation`；
- 至少报告发生位置 `argmax_location`；
- 适用时单独报告 terminal violation；
- 对状态递推或守恒式报告最大残差；
- 只检查最终状态，不得 Mathematical PASS。

这是 hard-constraint correctness，不属于“可选稳健性实验”。没有动态约束的模型可明确标记 `NOT_APPLICABLE`。

### 交替迭代与多目标模型

如果模型存在反馈、经验步长/权重、收敛 Claim 或多目标权衡，应根据真实风险检查：

- 调整比例、步长、惩罚权重和终止阈值是否需要 Parameter Evidence；
- 若参数本质上是更新半径、步长、阻尼或每轮调整比例，是否应固定；若存在与问题结构匹配的自适应机制，应至少与固定参数基线比较；
- 粗粒度扫描是否只是 screening，而被误写成“最优参数”证据；
- 每轮是否同时记录正式目标、可行性、服务质量和题目要求的关键指标；
- 接受条件与停止条件是否错误地只看单一成本改善；
- 是否需要区分正常收敛、排程不再变化、改善不足、达到迭代上限和子问题不可行；
- 不同场景的停止原因是否会改变论文结论；
- 若声称多目标权衡，是否需要极端点、规范化依据、Pareto/ε-constraint 或明确主目标—约束结构。

不能把事后统计指标写成模型已经优化的目标。

## 四、Surrogate / Proxy Fidelity

预测输出、TOPSIS 得分、聚类标签、简化成本、coarse simulator 等如果只是下游决策 proxy，且其失真可能改变正式决策，则必须做 full replay。

建议记录：

`candidate, surrogate_score, true_decision_score, surrogate_rank, true_rank, rank_change`

若 full replay 显示 proxy 的失真足以改变正式可行性、正式方案排序或核心 Claim，则触发 `MATHEMATICAL_P0`，XXT 可以要求重开 FROZEN；不得仅以“降级为筛选工具”掩盖已经受影响的正式结果。

只有在失真不影响正式结论时，proxy 才可降为初始化/筛选/加速工具，并在 limitation 中说明。

## 五、不可行性诊断

出现不可行时，不得只写“约束严格”。至少完成一种与冲突结构匹配的诊断：

- 求最小可达目标并与上限比较；
- 引入带惩罚 slack，量化最小放松量；
- 提取 IIS / binding constraints；
- 分区域、分时段、分类别定位冲突；
- 固定上游决策，求子问题理论最小资源/碳/容量边界。

正文必须把数学边界翻译成题目中的物理或业务机制。

## 六、华数杯 C 三等奖反馈形成的 Failure Evidence

这些是“过去哪里翻过车”的案例，用来帮助 AI 提出风险假设，不是“见到同类模型就机械复刻实验”的规定：

- 简单均值预测曾暴露时序突变适配风险；
- 经验预测区间曾暴露 downstream protection 未量化风险；
- 顺序启发式曾暴露输入重排敏感风险；
- 启发式/多策略曾暴露缺 exact/MILP anchor 风险；
- 区域独立求解曾暴露结构假设未对照风险；
- 固定储能硬件曾暴露容量/功率参数风险；
- 固定经验阈值曾暴露阈值来源不足风险；
- 迭代步长/每轮调整比例曾暴露“参数是否应固定”风险；
- 交替迭代曾暴露 QoS、可行性与终止条件脱节风险；
- 多场景曾暴露停止原因未区分风险；
- 不可行解释曾暴露缺定量边界风险。

专项演练中的具体参数、Region 名称和图表只进入对应 Task / Case，不硬编码进 Shared Core。

## 七、Gate 结论

只允许：

- `EVIDENCE PASS`：主要结论均有可追溯证据，且已识别的重要风险已处理；
- `PASS WITH LIMITATION`：主线可用，但论文必须主动限定结论边界，并记录未消除风险；
- `FAIL / ADD EXPERIMENT`：缺关键 baseline、稳定性、敏感性、参数证据、counterfactual、anchor 或存在未处理的实质风险，不得进入完整 Paper Handoff；
- `MATHEMATICAL_P0`：目标、hard constraints、单位/量纲、可行性、正式指标/accounting 或 material surrogate fidelity 出现致命错误，禁止 Freeze，并进入 P0 reopen 流程。
