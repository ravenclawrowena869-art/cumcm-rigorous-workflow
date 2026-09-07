# 模型证据充分性 Gate v2.1

模型能够运行，只说明进入了验证阶段。进入 Freeze 和 Paper Handoff 前，必须确认结论有足够 evidence。

## 一、结论—证据表

每个拟写入正文的核心结论记录：

| 结论 | 所需证据 | 实际文件/字段 | 状态 |
|---|---|---|---|
| 当前模型优于备选 | 同口径 baseline / challenger |  |  |
| 算法接近最优 | exact anchor、small-scale truth、bound 或 gap |  |  |
| 结果稳定 | 多种子、重排、重采样、重复划分 |  |  |
| 参数选择合理 | 参数来源 + 参数扫描/重求解 |  |  |
| 模型鲁棒 | 噪声、情景、结构扰动或分布漂移 |  |  |
| 区间有保护作用 | downstream replay / violation-risk reduction |  |  |
| 结构假设合理 | counterfactual / idealized bound |  |  |
| 不可行有现实原因 | 最小可达边界、slack、IIS 或 binding constraints |  |  |

没有证据的结论只能标记待验证，不得改成更肯定的措辞写进论文。

## 二、优化质量等级

### FEASIBLE

全部 hard constraints 通过，目标与核心指标已独立复算。若存在动态/path-dependent hard constraints，还必须完成全过程 replay。

### COMPETITIVE

在同一数据、口径和约束下，稳定优于至少一个合理 baseline，且多初值/顺序/随机性不会轻易推翻结论。

### NEAR-OPTIMAL

在 COMPETITIVE 基础上，还有 exact anchor、下/上界、MIP gap、松弛界、small-scale truth 或其他可信最优性证据支持剩余 gap 足够小。

强 baseline 本身只能支持 COMPETITIVE，不能单独证明 NEAR-OPTIMAL。禁止把 `FEASIBLE` 直接写成“最优”。

exact anchor / bound / MILP benchmark 按 Claim 强度、模型类型和计算预算条件触发：如果只声明 FEASIBLE，不为形式完整机械增加大型 exact 求解；如果声称 near-optimal，必须给出与该 Claim 匹配的最优性证据。

## 三、按模型类型检查

### 预测模型

- 至少保留一个朴素/统计 baseline；
- 简单稳定模型可以成为主模型，但如果题目存在明显时序波动、结构突变或外推风险，必须有时序感知 challenger 或 drift stress test；
- 使用时间顺序正确的验证方式；
- 检查极端误差、系统性偏差和结构突变；
- 给出预测区间时，同时检查 coverage、width，以及区间对后续容量、调度、风险决策的保护效果；
- 预测结果进入下一问时，必须做误差传播或上下界/情景 replay。

不能因为 GroupedMean、历史均值等方法简洁稳定，就跳过时序适配性审查。

### 启发式、贪心与随机优化

- 明确任务处理顺序、并列规则、随机种子和停止条件；
- 对顺序敏感算法做 permutation/shuffle stress test；
- 做多随机种子或多起点，报告均值、标准差、最好/最差；
- 在可计算的小规模或代表性子问题上，用 MILP、DP、枚举、下界或松弛解建立 exact anchor；
- 不能只比较数套人工预设策略后声称最优。

如果主线 authority 已冻结为最小修复，不要求额外建立一套完整竞争主模型；可以用小规模 anchor 或下界完成性能锚定。

### LP、MILP、CP-SAT 与其他约束优化

- 独立复算 objective、变量边界、平衡式和全部 hard constraints；
- 报告 solver status、runtime、gap（适用时）和最大违反量；
- 对“区域独立”“无互联”“确定性输入”“无限网络”等关键结构假设，建立可实现的 counterfactual、理想上界或限制说明；
- 对容量、功率、预算、权重、阈值等关键参数做改参数→重新求解；
- 储能等双参数设备如果结果依赖容量与功率，应优先形成容量×功率 sensitivity surface，而非只改一个参数。

### 动态、状态空间与路径依赖模型

凡 hard constraint 依赖完整轨迹而不是单一终值，例如 SOC、库存、温度、水位、速度/加速度、动态安全距离、累计预算/排放、ODE/PDE 状态、滚动容量等：

- validator 必须逐时段/逐空间点/逐迭代 replay；
- 至少报告 `max_violation`；
- 至少报告发生位置 `argmax_location`；
- 适用时单独报告 terminal violation；
- 对状态递推或守恒式报告最大残差；
- 只检查最终状态，不得 Mathematical PASS。

没有动态约束的模型可明确标记 `NOT_APPLICABLE`。

### 交替迭代与多目标模型

- 经验调整比例、步长、惩罚权重和终止阈值必须有参数扫描或来源依据；
- 每轮同时记录正式目标、可行性、服务质量和题目要求的关键指标；
- 接受条件与停止条件不能只看单一成本改善，如果服务质量是硬约束/接受条件，就必须同步检查；
- 区分正常收敛、排程不再变化、改善不足、达到迭代上限和子问题不可行；
- 不同场景记录收敛速度和停止原因；
- 若声称多目标权衡，至少给出极端点、规范化依据、Pareto/ε-constraint 结果或明确的主目标—约束结构；
- 不能把事后统计指标写成模型已经优化的目标。

## 四、Surrogate / Proxy Fidelity

预测输出、TOPSIS 得分、聚类标签、简化成本、coarse simulator 等如果只是下游决策 proxy，必须做 full replay。

建议记录：

`candidate, surrogate_score, true_decision_score, surrogate_rank, true_rank, rank_change`

若 full replay 显示 proxy 的失真足以改变正式可行性、正式方案排序或核心 Claim，则触发 `MATHEMATICAL_P0`，XXT 可以要求重开 FROZEN；不得仅以“降级为筛选工具”掩盖已经受影响的正式结果。

只有在失真不影响正式结论时，proxy 才可降为初始化/筛选/加速工具，并在 limitation 中说明。

## 五、不可行性诊断

出现不可行时，不得只写“约束严格”。至少完成一种：

- 求最小可达目标并与上限比较；
- 引入带惩罚 slack，量化最小放松量；
- 提取 IIS / binding constraints；
- 分区域、分时段、分类别定位冲突；
- 固定上游决策，求子问题理论最小资源/碳/容量边界。

正文必须把数学边界翻译成题目中的物理或业务机制。

## 六、华数杯 C 三等奖反馈形成的通用检查

这些条目是实战 Failure Evidence，不是对所有新题机械套用的固定实验数值：

- 简单均值预测：检查时序突变适配能力；
- 经验预测区间：量化 downstream protection；
- 顺序启发式：做输入重排敏感性；
- 启发式/多策略：在 Claim 需要且计算可承受时给 exact/MILP anchor；
- 区域独立求解：检查互联 counterfactual 或明确限制；
- 固定储能硬件：做容量/功率参数扫描；
- 固定经验阈值：做阈值扫描；
- 交替迭代：终止条件兼顾 QoS 与可行性；
- 多场景：比较迭代次数和停止原因；
- 不可行：定量解释边界，而非泛泛归因。

专项演练中的具体参数、Region 名称和图表只进入对应 Task / Case，不硬编码进 Shared Core。

## 七、Gate 结论

只允许：

- `EVIDENCE PASS`：主要结论均有可追溯证据；
- `PASS WITH LIMITATION`：主线可用，论文主动限定边界；
- `FAIL / ADD EXPERIMENT`：缺关键 baseline、稳定性、敏感性、counterfactual、anchor 或不可行诊断，不得进入完整 Paper Handoff；
- `MATHEMATICAL_P0`：目标、hard constraints、单位/量纲、可行性、正式指标/accounting 或 material surrogate fidelity 出现致命错误，禁止 Freeze，并进入 P0 reopen 流程。
