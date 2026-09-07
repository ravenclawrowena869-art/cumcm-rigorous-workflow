# AGENTS.md

本仓库是 FYQ、XXT、CYQ 三人共同维护的数学建模比赛工作流与 Skill 唯一正式源。ChatGPT、Codex、Claude Code 等 Agent 执行相关任务前必须读取本文件和根 `SKILL.md`。

## 1. 启动顺序与按需读取

默认先读取：

1. `SKILL.md`；
2. `skills/cumcm-rigorous-workflow/core/SHARED_CORE.md`；
3. 当前比赛 `project_state.yaml`（若存在）；
4. 当前 `ACTIVE_ROLE` 对应 Profile；
5. 与当前任务直接相关的 workflow / Gate。

不要无目的地一次性读取整个仓库。

### 团队协作、分工、阶段规划

优先读取：
- `00_总览/`
- `06_协作与交接/`

### 代码、AI Agent、版本、接口、冻结

优先读取：
- `01_赛前准备/`
- `03_建模与代码/`
- `04_验收冻结/`
- `07_AI协作/`
- `10_容灾与应急/`

### 论文或绘图

必须读取：
- `05_论文与图表/01_论文流水线.md`
- `05_论文与图表/05_逐问写作与算法呈现Gate.md`
- `06_协作与交接/05_Paper_Handoff规范.md`

涉及最终图表时再读取：
- `05_论文与图表/02_图表工作流.md`

### 数学模型选择、推导、审核

优先读取：
- `02_开赛与拆题/`
- `03_建模与代码/`
- `04_验收冻结/05_模型证据充分性Gate.md`
- `11_题型插件/`

---

## 2. Role Binding

只允许三个角色值：

- `FYQ_TECHNICAL_ORCHESTRATOR`
- `XXT_MATHEMATICAL`
- `CYQ_PAPER`

绑定优先级：

1. 环境或用户显式给出的 `ACTIVE_ROLE`；
2. 当前 `project_state.yaml.agent_bindings`；
3. 用户首次启动时声明；
4. 仍无法确定时只询问一次，或在无需角色权限的任务中使用 role-neutral read-only。

不得默认猜成 FYQ、XXT 或 CYQ。

平台允许本地配置时可使用 `.cumcm-agent.local.yaml`，该文件只保存个人角色绑定，不进入 Git。

---

## 3. 三套 GPT 都是一等消费者

FYQ、XXT、CYQ 的 GPT 都加载同一个 Shared Core。可以读取其他 Profile 用于理解接口或 Review，但输出必须服从当前主 Profile 的权限与交付格式。

三套 GPT 不以“另一边聊天里说过”作为正式状态同步。正式共享只通过：

- `project_state.yaml`；
- Task；
- Interface；
- Handoff；
- Frozen Source of Truth；
- Figure Registry；
- Git commit / PR。

聊天记录可以提供上下文，但不能覆盖这些来源。

---

## 4. 三个长期人类角色与默认 GPT Profile

### FYQ — Technical Lead / Orchestrator

默认 Profile：`FYQ_TECHNICAL_ORCHESTRATOR`

主要负责：
- AI / Coding Agent 协作；
- Skill / Prompt；
- Question Map、Roadmap、技术路线集成；
- FYQ/XXT 建模与编程 Block 分发；
- Git / 环境 / 测试；
- 数据与工程流水线；
- Source of Truth；
- Interface / Version；
- Freeze / clean replay；
- 联合模型技术集成；
- Missing Evidence 与 Paper Handoff 初稿。

FYQ 负责统一技术集成，但不能越过 XXT 对目标、约束、单位和数学可行性的正式 Review。

### XXT — Mathematical Lead

默认 Profile：`XXT_MATHEMATICAL`

主要负责：
- 数学抽象；
- 决策变量、目标函数、hard constraints；
- 模型选择与推导；
- 参数、单位和数值合理性；
- validator specification；
- exact anchor / bound / optimization adequacy；
- 独立指标复算；
- Mathematical Review。

专项冻结任务中不另行维护第二套主模型；若发现 P0 数学错误，可提交最小替代或重开建议，由 FYQ 统一集成。

### CYQ — Paper Lead

默认 Profile：`CYQ_PAPER`

主要负责：
- 文献与优秀论文学习；
- 论文框架和摘要；
- 问题分析、模型建立、问题求解；
- 表述优化和结果解释；
- Figure Registry 与图表叙事；
- 稳健性/敏感性结果的论文组织；
- AI 使用说明；
- 页数控制和 Final Paper。

CYQ 不默认承担：
- 联合模型技术总控；
- 每轮 solver 调度；
- 全部接口和版本管理；
- 所有代码技术验收；
- 从多个冲突结果里人工拼接正式数字。

三个人都可以参与实际建模。长期角色与具体问题 Owner 是两套概念。

---

## 5. 当前比赛事实优先级

如果存在 `project_state.yaml`，它是当前比赛状态的主要事实来源之一。

优先级为：

1. 官方题目、官方规则、官方模板与官方附件；
2. 当前比赛 `project_state.yaml`；
3. 已冻结的模型、接口与 Source of Truth；
4. 本仓库 canonical workflow / Gate；
5. 当前 Task / Handoff；
6. 聊天中的临时描述。

来源冲突时不得自行猜测，应指出冲突并按 authority 处理。

---

## 6. 工作流核心原则

必须遵守：

- 长期角色固定，单问 Owner 动态分配；
- Leader 不等于 Model Integrator；
- Paper Pipeline 前期启动；
- Interface First + Mock Data；
- 任务可以 blocked，人不能纯等待；
- 工具故障优先换工具，不换长期角色；
- 图表属于模型 evidence chain，不是最后美化；
- 正式数字必须可追溯到冻结结果；
- evidence before claims；
- 先 baseline，再根据真实 gap 升级；
- 复杂模型没有可量化增益时降为对照。

正式结果来源链：

```text
官方输入
→ Frozen Code
→ Frozen Output
→ Paper Metrics
→ Figure/Table
→ Paper / Abstract
```

---

## 7. 修改前行为要求

如果任务涉及修改代码、模型、接口、Skill、论文来源或正式结果，先完成：

1. 读取当前状态；
2. 明确当前阶段和 `ACTIVE_ROLE`；
3. 明确本轮唯一目标；
4. 明确允许修改范围；
5. 明确禁止修改范围；
6. 确认 Source of Truth；
7. 列出计划修改文件；
8. 指定 Required Gate；
9. 定义验收标准。

不得在没有必要的情况下修改无关文件。

专项冻结任务如果明确“不推翻主模型、只做必要修改”，必须先审计并区分：

- 代码确实缺少；
- 代码已有，但论文没有写清；
- 需要补实验才能判断。

只修复被证明确实存在的缺陷。

---

## 8. Freeze 规则

标记为 `FROZEN` 的模型或结果不得因为“可能还能更好”自行修改。

只有发现 P0 问题时才允许重开，例如：

- 题意理解错误；
- hard constraint 错误；
- 结果口径错误；
- 正式数字错误；
- 无法复现；
- 官方规则违规。

重开后建立新版本，并重新执行所有受影响的依赖验收。

---

## 9. Model Evidence / Paper Gate

模型进入论文前必须读取并通过：

`04_验收冻结/05_模型证据充分性Gate.md`

正文再通过：

`05_论文与图表/05_逐问写作与算法呈现Gate.md`

缺少 baseline、exact anchor、顺序/seed 稳定性、参数敏感性、必要鲁棒性、真实求解步骤或 Frozen source 时，AI 必须列出缺口，不得用通用文字补成“可直接定稿”。

论文表达优先保护：

- 自然；
- 清晰；
- 规范；
- 可解释；
- 与本题变量、困难、结果直接相关。

避免：

- AI 味；
- 元叙述；
- 术语堆砌；
- 教材式通用算法介绍；
- 问题分析与模型建立重复；
- 图、表、正文重复报同一信息；
- 没有证据的“显著、稳健、优越”。

模型冻结后优先通过 Paper Handoff 向 CYQ 交付，不要求 Paper Lead 自己进入代码包寻找事实。

---

## 10. Agent 工具故障

Coding Agent 是工具，不是团队角色。

如果 Codex 不可用：

```text
Codex
→ Claude Code / 其他备用 Agent
→ 普通 IDE + AI 对话辅助
```

不得因为工具故障就让 FYQ、XXT、CYQ交换长期角色。只有成员本人无法继续比赛时，才启动人员级 Deputy。

---

## 11. Blocked Rule

如果 Primary Task 因上游结果或其他依赖阻塞约 15–30 分钟，应切换 Secondary Queue。

正确记录：

```text
Primary Task: BLOCKED
Blocker: ...
Secondary Task: ...
Next Checkpoint: ...
```

允许 Task blocked，不允许成员纯等待。

---

## 12. Skill 共同维护

正式源只认 GitHub main。

推荐分支：
- `fyq/<topic>`
- `xxt/<topic>`
- `cyq/<topic>`
- `shared/<topic>`

重要 Shared Core 改动至少需要另一角色 Review。跨角色 Handoff 模板至少由输出方和消费方共同 Review。

未 merge 的聊天建议、个人 ZIP、临时 Prompt 只能算 Proposal，不得宣称已经对另外两套 GPT 生效。

详细规则见：

`06_协作与交接/06_三GPT协作与Skill共同维护.md`

---

## 13. Agent 开始复杂任务前的默认输出

简短报告：

- 当前阶段；
- `ACTIVE_ROLE`；
- 当前模块状态；
- 本轮唯一目标；
- Source of Truth；
- Consumer；
- 允许修改；
- 禁止修改；
- Required Gate；
- 验收标准。

只读分析或简单问答不需要机械输出全部字段。
