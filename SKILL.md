---
name: cumcm-rigorous-workflow
description: Shared three-GPT evidence-driven workflow for CUMCM and similar mathematical-modeling competitions, covering modeling, coding, validation, handoffs, paper, figures, freezing and final submission.
---

# CUMCM Rigorous Workflow v2.1.2 Dispatcher

本仓库的 Runtime Skill 由 FYQ、XXT、CYQ 三套 GPT 共用。任何任务先执行 Shared Core，再加载当前 Role Profile；Profile 不得覆盖 Shared Core、官方材料、当前 `project_state.yaml` 或 Frozen Source of Truth。

## 0. 每次回答前先调用 Skill

对本项目的每一次实质性回答、审查、分工、建模、编程、论文或图表任务，**每次回答前都必须先调用一次本 Skill**，然后再开始分析或输出。不得以“上一轮已经读过”“当前上下文还记得”为由跳过。

本轮调用至少完成：

1. 读取本 dispatcher；
2. 读取 Shared Core；
3. 解析当前 `ACTIVE_ROLE` 并读取对应 Role Profile；
4. 按任务类型读取直接相关的 canonical Gate / workflow。

若运行平台支持原生 Skill invocation，优先调用 canonical Skill；若只能访问仓库文件，则按上述顺序读取等价文件。无法完成本轮调用时，先明确阻断原因，不得假装已按 Skill 执行。

## 1. 先读 Shared Core

必须读取：

`skills/cumcm-rigorous-workflow/core/SHARED_CORE.md`

然后读取 `README.md`、当前比赛 `project_state.yaml`（若存在）和与任务直接相关的 workflow / Gate。不要无目的地一次性读取整个仓库。

## 2. 解析 ACTIVE_ROLE

只允许三个角色值：

- `FYQ_TECHNICAL_ORCHESTRATOR`
- `XXT_MATHEMATICAL`
- `CYQ_PAPER`

绑定优先级：

1. 环境或用户显式给出的 `ACTIVE_ROLE`；
2. 当前 `project_state.yaml` 的 `agent_bindings`；
3. 用户首次启动时声明；
4. 仍无法确定时，不猜角色。只询问一次，或在不需要角色权限的任务中采用 role-neutral read-only 模式。

解析后加载：

- FYQ → `skills/cumcm-rigorous-workflow/profiles/FYQ_TECHNICAL_ORCHESTRATOR.md`
- XXT → `skills/cumcm-rigorous-workflow/profiles/XXT_MATHEMATICAL.md`
- CYQ → `skills/cumcm-rigorous-workflow/profiles/CYQ_PAPER.md`

可以为了 Review 阅读其他 Profile，但输出必须以当前主 Profile 的权限和交付格式为准。

## 3. 按任务加载 canonical Gate

- 建模、实验、比较、敏感性、稳健性、不可行诊断：读取 `04_验收冻结/05_模型证据充分性Gate.md`。
- 论文写作、逐问短导语、润色、审稿：读取 `05_论文与图表/01_论文流水线.md` 与 `05_论文与图表/05_逐问写作与算法呈现Gate.md`。
- 图表：同时读取 `05_论文与图表/02_图表工作流.md`。
- 模型到论文交付：使用 `06_协作与交接/05_Paper_Handoff规范.md`。
- 最终提交：执行 `08_提交终检/01_FINAL_SUBMISSION_GATE.md`。

## 4. Evidence before prose

每问先确定：输出、输入、分析单位、变量、目标、约束、baseline、正式模型、验证、关键结果、不确定性和下游接口。

缺少必要实验、Frozen source、真实求解步骤或正式数字时，返回 Missing Evidence / INCOMPLETE 或显式占位符。禁止用通用语言掩盖缺口。

非平凡求解必须有本题专属伪代码或算法流程，写出真实输入、关键变量、候选/循环、hard constraint、接受/停止条件、失败分支与输出复算。

## 5. Freeze 与共同事实源

正式同步只认：`project_state.yaml`、Task、Interface、Handoff、Frozen Source of Truth、Figure Registry、Git commit / PR。

聊天上下文不能覆盖这些来源。`FROZEN` 内容只有 P0 问题才能重开，并建立新版本后重跑依赖 Gate。

## 6. Runtime Lite

日常 Skill 不携带大型论文 PDF/PNG。运行包只保留 dispatcher、Shared Core、三个 Profile、必要 workflow、templates、source index 与 provenance。全文证据按 `skills/cumcm-rigorous-workflow/references/SOURCE_INDEX.md` 检索。

## Completion

一个模块只有在数学、工程、evidence 和论文接口均有可追溯证据后才能进入 FROZEN / PAPER_LOCKED。单次“跑通”、结果 Excel 或聊天规划都不构成完成。
