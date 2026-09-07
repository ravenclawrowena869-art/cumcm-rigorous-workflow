# 数模比赛全流程工作流 v2.1

这是基于 2026 华数杯 C 题完整实战复盘后重构的 **三人数学建模竞赛工程工作流**。

v2.1 在 v2.0 三轨并行架构上新增“模型证据充分性 Gate”和“逐问写作与算法呈现 Gate”，把赛后教师与评委意见转化为 AI 可执行的阻断规则。v2.0 的核心仍是重构团队生产方式：

> **论文线、技术线、数学线三轨并行；**
> **角色长期稳定，单问 Owner 动态分配；**
> **依赖通过接口和 Mock 解耦；**
> **工具故障优先换工具，不换角色；**
> **论文从前期开始持续写，不等四问结束；**
> **模型、图表、论文都通过 Gate 和 Source of Truth 进入最终稿。**

---

## 三个长期角色

### CYQ — Paper Lead
负责：
- 文献与优秀论文学习
- 论文骨架
- 摘要
- 表述优化
- 结果解释
- 图表叙事与最终呈现
- 页数与最终成稿

不再默认承担：
- 联合模型总控
- 每轮 solver 调度
- 版本与接口总管理
- 所有代码验收

### FYQ — Technical Lead
负责：
- AI / Coding Agent 协作
- Skill / Prompt
- 数据与工程流水线
- Git / 环境 / 测试
- Source of Truth
- 接口、版本、Freeze、clean replay
- 联合模型技术集成

### XXT — Mathematical Lead
负责：
- 数学抽象
- 决策变量、目标、约束
- 模型选择与推导
- 数学合理性
- hard constraint specification
- 参数与数值合理性
- A/B 题中的机理、量纲、初边值、数值收敛审核

三个人都参与建模，但不再让三个人承担完全同质的工作。

---

## v2.0 的八条核心规则

1. **长期角色固定，具体问题 Owner 动态分配。**
2. **Leader 不等于 Model Integrator。**
3. **文献搜索结束、第一版模型路线确定后，Paper Pipeline 立即启动。**
4. **跨问依赖使用 Interface First + Mock Data，不等待正式上游结果才开发。**
5. **团队允许“主任务 blocked”，不允许“人 blocked”。**
6. **工具故障先切备用工具，原则上不交换 FYQ/XXT 角色。**
7. **图表是一级证据流水线，不是最后的美化阶段。**
8. **任何正式数字都遵循：官方输入 → Frozen Code → Frozen Output → Paper Metrics → 图/表 → 正文/摘要。**
9. **模型能够运行不等于证据充分：基线、真值锚点、重排/多种子、参数重算与不可行诊断按题型进入验收。**
10. **每问必须有题目特定的概述与求解过程；缺少真实伪代码、比较或冻结来源时，AI 不得生成“可直接定稿”的正文。**

---

## 目录导航

- `00_总览/`：总流程、三轨并行、时间线、状态机与 Gate
- `01_赛前准备/`：环境、双 Agent、故障演练、仓库准备
- `02_开赛与拆题/`：读题、路线评审、Owner 分配、接口优先
- `03_建模与代码/`：MVP、实验循环、约束、场景
- `04_验收冻结/`：三重验收、Freeze、clean replay、Source of Truth、模型证据充分性 Gate
- `05_论文与图表/`：Paper Pipeline、逐问写作与算法呈现 Gate、Figure Registry、图表与页数
- `06_协作与交接/`：三角色分工、Blocked Rule、Paper Handoff、任务单
- `07_AI协作/`：平台无关 Skill、Coding Agent、Prompt
- `08_提交终检/`：最终提交 Gate
- `09_本次比赛复盘/`：2026 华数杯 C 题经验与问题
- `10_容灾与应急/`：工具、设备、人员三级 Plan B
- `11_题型插件/`：数据型、运筹型、机理型问题的额外验收
- `templates/`：下次比赛可直接复制的模板

---

## 推荐使用方式

正式比赛开始后：

1. 复制 `templates/project_state模板.yaml`
2. 指定 Paper / Technical / Mathematical 三个长期角色
3. 为每问指定 Owner / Reviewer
4. 2–4 小时完成第一次路线评审
5. 立即启动论文线
6. 8–10 小时前尽量冻结跨问 interface schema
7. 每个模块按 `IDEA → BASELINE → MAINLINE → VALIDATING → EVIDENCE_PASS → FROZEN → PAPER_LOCKED`
8. 冻结前通过模型证据充分性 Gate，冻结后完成 Paper Handoff
9. 各问正文通过逐问写作与算法呈现 Gate 后才能进入最终稿
10. 最后 4–6 小时启用 `Model Change Ban`

这套工作流的目标不是让三个人“都忙”，而是让三条生产线真正同时向最终论文推进。
