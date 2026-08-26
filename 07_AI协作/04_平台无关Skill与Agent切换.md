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
