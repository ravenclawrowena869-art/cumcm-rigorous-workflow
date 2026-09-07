# Runtime Lite / Knowledge Corpus Policy

## 1. 目的

`cumcm-rigorous-workflow` 的日常运行包只携带执行规则、角色 Profile、Gate、模板和索引，避免每次更新 Skill 都重新打包几十 MB 的优秀论文 PDF 与截图。

## 2. 三层知识结构

### Runtime Lite

用于三套 GPT 的日常加载。包含：
- `SKILL.md` dispatcher；
- Shared Core；
- FYQ / XXT / CYQ 三 Profile；
- 必要 workflow / Gate；
- templates；
- source index；
- manifest / provenance。

不得包含 `.pdf/.png/.jpg/.jpeg` 等大型 corpus 文件。

### Project Files / 当前比赛知识库

用于当前赛题的官方题面、附件、老师批注、优秀论文、当前交付包和冻结结果。需要全文证据时按任务检索，不把全部材料注入 Runtime Skill。

### Full Archive

长期备份：
- 原始优秀论文；
- 页面截图；
- 完整 corpus；
- provenance / hash；
- 历史大型 Skill 包。

用于迁移、灾难恢复和离线重建，不作为日常 Runtime 依赖。

## 3. 检索顺序

需要正文证据时：

1. 当前 Project Files / 官方材料；
2. GitHub 轻量 references 与 case notes；
3. Full Archive；
4. 用户明确要求研究或验证时，再做外部学术检索。

不得用旧聊天记忆替代可检索的正式文件。

## 4. 更新规则

- 修改 Shared Core、Profile、Gate、Prompt 或模板时，只更新 GitHub canonical 文件；
- Runtime Lite 由 `tools/build_runtime_skill.py` 从 manifest 重新组装；
- Skill 小改动不需要重新打包原始论文；
- 新增优秀论文时更新 source index / provenance，全文仍外置；
- 禁止长期存在 FYQ/XXT/CYQ 各自“最新最终 Skill ZIP”。

## 5. 证据边界

轻量 source index 只负责告诉 Agent“去哪里找”。真正的论文结论、数字、模型细节仍应读取原文件后再使用。索引摘要不能替代原文证据。

## 6. 发布形态

### Runtime Lite
适合 ChatGPT Project、Codex、其他 Agent 日常安装和快速更新。

### Full Archive
适合长期保存和完整迁移，不要求每次比赛都加载。
