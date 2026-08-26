# Version 2.0 — Parallel Team Architecture

## 核心升级

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
