# 华数杯 C 题 Q4 赛前闭环演练 Authority

> 本文件是正赛前三天用于团队协作演练的专项 authority。它只约束华数杯 C 题 Q4 的“模型审查—必要修改—重跑—敏感性—出图—冻结”演练，不自动成为其他赛题的固定参数规则。

## 1. 范围

- 不重跑 Q1–Q3，不推翻整体框架；
- 保留 Q1/Q2 v4.8 FINAL_FROZEN 与 Q3 v3.1 final 作为上游；
- 除非发现会使 Q4 失效的接口 P0，不修改 Q1–Q3 模型和正式结果；
- Q4 依次完成：复现原主结果 → 审查 → 只修复被证明存在的缺陷 → 重跑完整主线 → 最小必要敏感性 → 图表/论文事实 → Freeze；
- 禁止为了复杂度临时增加完整 Pareto、大型新模型、跨区域电力互济或其他与本次 Q4 修复无关的扩展。

## 2. 角色

### FYQ / `FYQ_TECHNICAL_ORCHESTRATOR`

- 统一 Q4 技术主线，避免 FYQ/XXT 各自形成第二套版本；
- 区分评委意见属于代码缺失、论文表达缺失、还是需要补实验；
- 给 XXT 明确 Task，包括输入、输出、参数、验收；
- 集成代码、实验、正式数字和 Freeze；
- 给 CYQ Paper Handoff / `Q4_PAPER_FACTS.md`；
- 不把版本冲突、数字口径和代码事实交给 CYQ 人工拼接。

FYQ 的主控不覆盖 XXT 的 Mathematical PASS。

### XXT / `XXT_MATHEMATICAL`

- 不另行维护第二套 Q4 主模型；
- 检查目标函数、约束、单位、接受/停止条件；
- 审查任务调整模块的能源信号、迁移收益、排序方向、候选遍历、tie-breaker；
- 检查重复调度、GPU 超容量、deadline、网络时延等 hard constraints；
- 按冻结配置执行主情景与敏感性；
- 独立复算关键指标和最大约束违反量；
- 按 Figure Registry 输出作图数据与第一版图；
- 提交独立验算，不以“程序成功运行”作为结论。

若发现数学 P0，可以提出最小修复/重开要求，由 FYQ 统一集成。

### CYQ / `CYQ_PAPER`

负责论文结构、图表需求、结果解释和最终呈现。若证据不足，回传 Evidence Gap，不代替技术组改代码或拼接冲突数据。

## 3. 修改前必须先产出 `Q4_MODEL_AUDIT.md`

逐项回答：

1. 成本、碳排放、等待时间、网络时延分别属于目标、hard constraint、接受条件还是事后评价；
2. 20% 任务调整上限是否真正 active，正式结果实际调整比例是多少；
3. 接受/停止条件是否覆盖成本、碳、平均等待、P95 等待、网络时延、排程变化率、能源 LP 可行性；
4. 代码是否已有 BestSoFar / QoS 保护但论文没有写清；
5. 各场景停止原因：正常收敛、任务不再变化、改善不足、能源不可行等；
6. RegionA 不可行能否复现，发生在哪个场景、哪一轮；
7. 论文数字能否由当前代码 clean replay，差异来自哪里。

若代码已有 QoS 保护，不重复改模型，补日志、公式和论文说明。若确实只按成本接受，则增加最小 QoS 接受门槛，并记录修改前后差异。

## 4. 最低主线重跑

至少：

- BASE / 原论文正式基准；
- 一个最能体现算电协同效果的可行情景；
- RegionA 严格碳约束只做必要边界诊断。

若原批量脚本稳定，可以跑全部场景；如果需要大量调试，先冻结最低重跑范围，不让论文线被完整批量阻塞。

## 5. 每轮日志字段

必须记录：

- scenario / iteration；
- 总成本、购电支出、售电收入；
- 碳排放；
- 平均等待、P95 等待；
- migration rate、调整任务数、实际调整比例；
- 网络时延 mean/P95；
- RegionA–F GPU utilization；
- 购电峰值、售电峰值、净交换峰值；
- solver status、runtime；
- 能源平衡最大残差；
- GPU 容量、deadline、网络时延等最大 hard violation；
- 本轮 accept/reject 与原因；
- 场景 final stop reason。

关键目标值必须独立复算，不能只读取 solver report。

## 6. 20% 调整上限敏感性

在同一代表性场景、同一输入与其他参数固定时比较：

`rho = 10%, 20%, 30%`

报告：

- 实际调整比例与 cap utilization；
- 总成本；
- 碳排放；
- 平均/P95 等待；
- migration rate；
- 收敛轮数；
- 能源可行性。

裁决：

- 三组实际调整率都明显低于 10% 且结果基本一致：20% cap 当前不 active，记录后停止扩展；
- cap 被触发、结果明显变化或策略排序变化：再补 5% 与 40%；
- 论文命名为“任务调整上限参数敏感性分析”，不能只凭平滑曲线声称模型稳健。

## 7. RegionA 严格碳约束不可行诊断

若能源 LP 不可行，固定该轮 AI 负荷并求 RegionA 最小碳排放，输出：

- `C_min`；
- `C_max`；
- gap = `C_min - C_max`；
- 相比上一轮增加的 AI IT 电量；
- 新能源、储能功率/容量、电网购电边界是否触发；
- binding periods；
- 恢复可行所需的最小碳上限放松量。

禁止只写“碳约束太严格”。

## 8. Figure Registry 专项目标

### 图 1：Q4 迭代收敛

- x：iteration；
- 分面展示 cost、carbon、P95 waiting；
- 标出 accept/reject；
- infeasible scenario 标停止原因；
- source：`q4_iteration_metrics.csv`。

### 图 2：GPU 利用率热力图

- 左：Q2 baseline；
- 右：Q4 final；
- y：RegionA–F；
- x：0–23 h 平均日内；
- 同一色标范围；
- 若平均日内掩盖变化，再按预先定义规则补 48–72 h 局部窗口；
- source：`q4_gpu_utilization_heatmap.csv`。

### 图 3：调整上限敏感性

- x：adjustment cap；
- panel 1：cost/carbon relative change；
- panel 2：mean/P95 waiting；
- 同时标实际 adjustment rate；
- source：`q4_cap_sensitivity.csv`。

RegionA 优先使用紧凑诊断表；多场景出现边界变化才追加图。

正式图内部交付尽量同时保留可编辑脚本、PDF/SVG、300 dpi PNG 和原始 CSV。

## 9. `Q4_PAPER_FACTS.md`

必须给 CYQ：

1. Q4 相较原论文是否修改及修改内容；
2. 目标、约束、参数的准确数学定义；
3. 为什么采用交替优化而非整体巨型联合 MILP；
4. 与本题变量对应的算法步骤；
5. 可直接改成伪代码的真实流程：读取冻结排程 → 能源子问题 → 反馈信号 → 枚举/筛选任务 → 重排 → 双侧可行性 → QoS/目标接受 → BestSoFar → termination；
6. 主结果及精确来源；
7. 每张图支持的结论；
8. cap sensitivity 的变化、异常和边界；
9. RegionA 不可行的定量解释；
10. 具体模型局限与失效条件。

## 10. 最终交付

至少：

- `00_README_Q4_RERUN.md`
- `Q4_MODEL_AUDIT.md`
- `Q4_EXPERIMENT_CONFIG.md`
- 最终代码与依赖
- 自动测试与 constraint audit
- `results/q4_iteration_metrics.csv`
- `results/q4_scenario_summary.csv`
- `results/q4_region_metrics.csv`
- `results/q4_cap_sensitivity.csv`
- RegionA diagnosis（若触发）
- Figure Registry 对应图片/代码/CSV
- `Q4_PAPER_FACTS.md`
- `VALIDATION_REPORT.md`
- `FREEZE_MANIFEST.json`

README 写清版本、输入、运行命令、输出、测试、未解决风险和 Freeze 结论。接手者不需要回看聊天才能理解交付。

## 11. 可迁移到 Shared Core 的部分

本演练向通用 Skill 提供以下模式：

- code missing / prose missing / experiment missing 三分审计；
- 经验阈值参数扫描；
- 顺序敏感性；
- exact anchor；
- counterfactual；
- infeasibility boundary diagnosis；
- multi-metric acceptance / termination；
- raw CSV → reproducible figure → Paper Facts → Freeze。

具体 Region、20% 和图表字段仍停留在本 case。
