# 平台无关 Shared Skill 与 Agent 切换 v2.2

团队的长期能力必须沉淀在 GitHub repo，而不能只存在某一个 ChatGPT Project、Codex session 或 Claude session 中。

## 1. 核心资产落盘

```text
/SKILL.md
/skills/cumcm-rigorous-workflow/
/interfaces
/tests
/docs
/templates
/project_state.yaml
```

GitHub main 是唯一正式源。

## 2. 三套 GPT 共用一个 Skill

FYQ、XXT、CYQ 不维护三份长期 Skill。

统一流程：

```text
同一个 GitHub Repo
→ 同一个 Shared Core
→ ACTIVE_ROLE 路由
→ FYQ / XXT / CYQ Profile
→ 同一个 project_state / Handoff / Frozen Source
```

角色值：

- `FYQ_TECHNICAL_ORCHESTRATOR`
- `XXT_MATHEMATICAL`
- `CYQ_PAPER`

平台允许本地文件时，可在 `.cumcm-agent.local.yaml` 保存个人角色绑定；该文件不进入 Git。平台不支持时，各自 Project / Custom Instructions 只保留一条简短 `ACTIVE_ROLE` 绑定，详细规则仍从共享 Skill 读取。

## 3. Agent 是工具

Codex、Claude Code、其他 Coding Agent 都是可替换工具。工具故障不自动改变 FYQ、XXT、CYQ 的长期角色。

例如：

```text
Primary Coding Agent
→ Secondary Agent
→ 读取同一个 repo + Skill + project_state
→ 继续原角色原任务
```

## 4. 能力档是资源，不是角色

团队可同时使用：

- `CODEX_ASTRA`
- `CODEX_SOL`
- `GPT_EXECUTION`

能力档是资源，不是角色。选择 `CODEX_ASTRA` 只表示该任务使用更高性能的 Coding Agent，不改变 FYQ / XXT / CYQ 的角色绑定，也不能替代 Mathematical Gate、Evidence Gate、官方 Authority 或 Frozen Source of Truth。

正式 Task / Prompt 的资源选择遵循：

`07_AI协作/05_执行资源路由协议.md`

如果 `ASTRA_REQUIRED` 但 Astra 临时不可用，可以在保持原 Task 权限和证据要求的前提下拆成更小 Frozen Blocks，再由 Sol 逐 Block 实现。降级必须保留原路由、实际使用执行器和原因；TDD、independent replay、XXT Review 与 Freeze 前置条件不降低。

## 5. 如何让规则真正约束 AI

### 仓库内 Coding Agent

读取 `AGENTS.md`、`SKILL.md`、Shared Core、当前 Profile、执行资源路由协议与任务相关 Gate。

### 支持 Skill 的平台

加载 `cumcm-rigorous-workflow`，显式提供或解析 `ACTIVE_ROLE`。

### 普通对话

至少提供：
- `ACTIVE_ROLE`；
- 当前 `project_state.yaml` / Handoff；
- 与任务相关的 Gate 或 Prompt 模板；
- 正式 Task 中的执行资源路由。

只把 GitHub URL 发给 AI 但没有实际读取，不等于规则已经生效。

## 6. Runtime Lite

日常 Runtime Skill 只携带：
- dispatcher；
- Shared Core；
- 三个 Profile；
- 必要 workflow / Gate；
- execution routing protocol；
- templates；
- source index；
- provenance / manifest。

优秀论文 PDF、截图和大型 corpus 外置。Skill 规则更新不要求重新打包几十 MB 原文。

## 7. 三方共同维护

任何人都可以通过 branch + PR 更新 Skill。正式规则只认 merge 后的 main。重要 Shared Core 改动至少由另一角色 Review，跨角色 Handoff 由输出方与消费方共同 Review。

个人聊天中发现的新规则先作为 Proposal；未 merge 前不得宣称已经对另外两套 GPT 生效。
