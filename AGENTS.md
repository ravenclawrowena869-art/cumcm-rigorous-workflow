# AGENTS.md

本仓库是 FYQ、XXT、CYQ 三人共同维护的数学建模比赛工作流与 Skill 唯一正式源。ChatGPT、Codex、Claude Code 等 Agent 执行相关任务前必须先读取本文件和根 `SKILL.md`。

## 1. 启动顺序

默认读取：

1. `SKILL.md`；
2. `skills/cumcm-rigorous-workflow/core/SHARED_CORE.md`；
3. 当前比赛 `project_state.yaml`（若存在）；
4. 当前 `ACTIVE_ROLE` 对应 Profile；
5. 与任务直接相关的 workflow / Gate。

不要一次性无目的读取全部仓库。

## 2. Role Binding

只允许：

- `FYQ_TECHNICAL_ORCHESTRATOR`
- `XXT_MATHEMATICAL`
- `CYQ_PAPER`

优先使用环境/用户显式 `ACTIVE_ROLE`，其次读取 `project_state.yaml.agent_bindings`。仍无法确定时只询问一次，不得默认猜成 FYQ、XXT 或 CYQ。

本地可使用 `.cumcm-agent.local.yaml` 保存个人绑定，该文件不得进入 Git。

## 3. 三套 GPT 都是一等消费者

FYQ、XXT、CYQ 的 GPT 都加载同一个 Shared Core。三套 GPT 可以互相读取 Profile 做接口理解或 Review，但不允许维护长期个人 Skill 分叉。

正式共享状态只通过：

- `project_state.yaml`；
- Task；
- Interface；
- Handoff；
- Frozen Source of Truth；
- Figure Registry；
- Git commit / PR。

“另一边聊天里已经说过”只能作为上下文，不能覆盖正式状态。

## 4. 人类角色与默认 Profile

### FYQ — Technical Lead / Orchestrator

主要负责 Coding Agent、Git/环境/测试、数据与工程 pipeline、接口、版本、Source of Truth、Freeze、clean replay、跨问技术集成，并由其 GPT 负责整体 Question Map、路线裁决、FYQ/XXT Block 分派和 Paper Handoff 初稿。

### XXT — Mathematical Lead

主要负责题意数学化、变量、目标、约束、模型选择与推导、参数/单位、validator、exact anchor/bound、数学验收和独立复算。

### CYQ — Paper Lead

主要负责论文骨架、问题分析、模型建立、问题求解、结果解释、Figure Registry、图表叙事、稳健性写作、摘要、AI 使用说明、版面和 Final Paper。

三个人都可以参与建模；长期角色与单问 Owner 分开管理。

## 5. 正式事实优先级

1. 官方题面、规则、模板、附件；
2. 当前比赛 `project_state.yaml`；
3. Frozen Model / Interface / Source of Truth；
4. canonical workflow / Gate；
5. 当前 Task / Handoff；
6. 聊天中的临时描述。

出现冲突时必须指出，不自行和稀泥。

## 6. 修改前要求

涉及代码、模型、接口、Skill、论文来源或正式结果时，先明确：

- 当前阶段和 Source of Truth；
- 本轮唯一目标；
- 允许修改；
- 禁止修改；
- 计划修改文件；
- required Gate；
- 验收标准。

专项冻结任务如果明确“不推翻主模型、只做必要修改”，必须先审计并区分：代码确实缺少、代码已有但论文未写清、需要补实验三类问题。只修改被证明确实存在的缺陷。

## 7. Freeze

`FROZEN` 只有 P0 问题才能重开，例如题意、hard constraint、正式指标、数字、复现或官方合规错误。重开建立新版本并重跑依赖验收。

## 8. Evidence / Paper Gate

模型进入论文前读取 `04_验收冻结/05_模型证据充分性Gate.md`。论文写作必须读取：

- `05_论文与图表/01_论文流水线.md`；
- `05_论文与图表/05_逐问写作与算法呈现Gate.md`；
- `06_协作与交接/05_Paper_Handoff规范.md`。

证据不足时必须列缺口，不得用教材式文字、猜测数字或虚构稳健性实验补成可定稿正文。

## 9. Coding Agent 与工具故障

Coding Agent 是工具，不是长期团队角色。工具故障优先切备用 Agent，不自动交换 FYQ/XXT/CYQ 的长期职责。

## 10. Blocked Rule

主任务因依赖阻塞约 15–30 分钟，切换 Secondary Queue。允许 Task BLOCKED，不允许成员纯等待。

## 11. Skill 共同维护

正式源只认 GitHub main。推荐分支：`fyq/*`、`xxt/*`、`cyq/*`、`shared/*`。重要 Shared Core 改动至少需要另一角色 Review，跨角色 Handoff 模板至少由输出方和消费方共同 Review。

未合并的聊天建议、个人 ZIP、临时 Prompt 只能算 Proposal。
