# 平台无关 Skill 与 Agent 切换

FYQ 的优势应沉淀为 **AI Engineering Methodology**，
而不是“只会和某一个工具交互”。

## 核心资产必须落盘

```text
/prompts
/skills
/interfaces
/tests
/docs
/project_state.yaml
```

不得只存在：
- 某个 ChatGPT Project
- 某个 Codex session
- 某个 Claude session
- 某个临时聊天上下文

---

# Skill 建议格式

Skill 至少有一个平台无关 Markdown 版本：

```text
Purpose
Inputs
Workflow
Allowed Changes
Forbidden Changes
Validation
Outputs
Failure Handling
```

这样 Primary Agent 故障后：

```text
Primary Agent
    ↓
Secondary Agent
    ↓
读取同一个 repo + Skill + state
    ↓
继续原角色原任务
```

---

# Coding Agent 的定位

Agent 是可替换工具，不是团队角色。

因此：
- Codex 挂了 ≠ FYQ 失去 Technical Lead 身份
- Claude Code 挂了 ≠ 改由 XXT 做 Technical Lead
- 工具问题优先在工具层解决


## v2.1：怎样让规则真正约束 AI

仓库根目录提供 `SKILL.md`。使用方式分三类：

- 在仓库目录内启动 Codex：`AGENTS.md` 作为仓库级规则生效，论文任务还必须读取两个 Gate；
- 在支持 Skill 的平台：安装或加载本仓库，显式调用 `cumcm-rigorous-workflow`；
- 在普通对话或其他 Coding Agent：把 `07_AI协作/02_AI_Prompt模板.md` 的论文追加段与相关 Gate 一并提供。

仅把规则放在 GitHub 上不会自动改变所有 AI。必须让当前 Agent 实际读取 `SKILL.md` / `AGENTS.md` 和任务相关 Gate，并提供当前比赛的 `project_state.yaml` 与 Paper Handoff。
