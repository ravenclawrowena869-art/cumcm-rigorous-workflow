# Version 2.1.2 — Paper Section Intro Hardening

## v2.1.2 增量升级

- 将逐问正式求解章节的开头从“重复问题概述”收敛为大标题下短导语；
- 当前文已有“问题分析”时，禁止再设置“本问目标与难点”等重复小节；
- 短导语统一采用“任务概括 → 核心难点 → 模型选择 → 应用依据”的四步结构；
- 导语不得提前塞入变量、公式、算法步骤、正式数字或未冻结结果；
- 逐问正文推荐顺序调整为“短导语 → 建模依据 → 模型建立 → 求解算法与伪代码 → 结果及证据 → 本问小结”；
- 篇幅紧张时允许删除单独本问小结，但禁止删除结果解释；
- dispatcher、Paper Pipeline、contract tests 与 runtime validator 同步升级。

## v2.1 核心升级

- 新增根目录 `SKILL.md`，允许将仓库作为可安装的数模工作流 Skill 使用；
- 新增模型证据充分性 Gate，要求基线、最优值锚点、稳定性、敏感性、鲁棒性和不可行诊断；
- 新增逐问写作与算法呈现 Gate，强制场景化模型引出和题目特定伪代码/流程；
- AI 在缺少真实步骤、实验或冻结来源时必须阻断定稿；
- Paper Handoff、AI Prompt、Submission Gate 与复盘清单同步升级。

## v2.0 保留架构

v2.0 从“流程规范”升级为“三条长期并行生产线”。

### 1. 重构三人分工
- CYQ：Paper Lead
- FYQ：Technical Lead
- XXT：Mathematical Lead

Leader 不再默认兼任模型总控。

### 2. 论文提前
第一次路线评审后正式启动 Paper Pipeline，
不再等模型全部完成。

### 3. Interface First + Mock
消除“上游未出结果 → 下游无法开发”的串行等待。

### 4. Blocked Rule
允许任务 blocked，不允许成员纯等待。

### 5. 工具容灾
工具故障优先切换工具，不再通过 FYQ/XXT 角色互换解决。

新增：
- 双 Coding Agent
- Failover Runbook
- 设备容灾
- 人员 Deputy
- 赛前故障演练

### 6. 三重验收
- Technical PASS
- Mathematical PASS
- Paper PASS

### 7. Visualization 一级化
新增 Figure Registry 与独立 Visualization Pipeline。

### 8. A/B/C 泛化
新增：
- 数据驱动型
- 运筹优化型
- 机理数值型
三个题型插件。

## 兼容性

保留 v1.0 中：
- Gate
- Freeze
- clean replay
- Source of Truth
- AI Prompt
- Submission Gate
- 2026 华数杯复盘

并对协作、时间线、论文、图表、容灾进行了结构级重写。
