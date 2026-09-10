---
name: cumcm-rigorous-workflow
description: Shared three-GPT evidence-driven workflow for CUMCM and similar mathematical-modeling competitions, covering modeling, coding, validation, handoffs, paper, figures, freezing and final submission.
---

# CUMCM Rigorous Workflow v2.2.0 Dispatcher

本仓库的 Runtime Skill 由 FYQ、XXT、CYQ 三套 GPT 共用。任何任务先执行 Shared Core，再加载当前 Role Profile；Profile 不得覆盖 Shared Core、官方材料、当前 `project_state.yaml` 或 Frozen Source of Truth。

## 0. 每次回答前先调用 Skill

对本项目的每一次实质性回答、审查、分工、建模、编程、论文或图表任务，**每次回答前都必须先调用一次本 Skill**，然后再开始分析或输出。不得以“上一轮已经读过”“当前上下文还记得”为由跳过。

本轮调用至少完成：

1. 读取本 dispatcher；
2. 读取 Shared Core；
3. 解析当前 `ACTIVE_ROLE`，从角色入口读取对应 Role Profile；
4. 按任务类型读取直接相关的 canonical Gate / workflow。

若运行平台支持原生 Skill invocation，优先调用 canonical Skill；若只能访问仓库文件，则按上述顺序读取等价文件。无法完成本轮调用时，先明确阻断原因，不得假装已按 Skill 执行。

## 1. 先读 Shared Core

必须读取：

`skills/cumcm-rigorous-workflow/core/SHARED_CORE.md`

然后读取当前比赛 `project_state.yaml`（若存在）。`README.md` 用于初次了解仓库或部署，不是每个任务的必读项。不要把空白比赛模板当成当前比赛状态，不要无目的地一次性读取整个仓库。

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

解析后只进入对应角色文件夹：

| ACTIVE_ROLE | 角色入口 | 职责权威文件（原路径保留） |
|---|---|---|
| `FYQ_TECHNICAL_ORCHESTRATOR` | [总控入口](skills/cumcm-rigorous-workflow/roles/controller/ROLE.md) | `skills/cumcm-rigorous-workflow/profiles/FYQ_TECHNICAL_ORCHESTRATOR.md` |
| `XXT_MATHEMATICAL` | [数学建模入口](skills/cumcm-rigorous-workflow/roles/modeling/ROLE.md) | `skills/cumcm-rigorous-workflow/profiles/XXT_MATHEMATICAL.md` |
| `CYQ_PAPER` | [论文入口](skills/cumcm-rigorous-workflow/roles/paper/ROLE.md) | `skills/cumcm-rigorous-workflow/profiles/CYQ_PAPER.md` |

角色入口负责阅读顺序和任务导航，Profile 仍是职责权威，Shared Core 仍是公共规则唯一来源。不要复制公共规则、建立三个独立 Skill，或加载三个角色的全部任务材料。旧任务直接引用 Profile 时仍有效，再按本节补读相应入口即可。角色名称不改变单问 Owner，也不把 XXT 等同于编程手。

可以为了 Review 阅读其他 Profile，但输出必须以当前主 Profile 的权限和交付格式为准。

## 3. 按任务加载 canonical Gate

- 建模、实验、比较、敏感性、稳健性、不可行诊断：读取 `04_验收冻结/05_模型证据充分性Gate.md`。
- **参数选取、阈值/权重/步长/每轮调整比例、Top-K、平滑系数、风险参数等调参任务：除 Evidence Gate 外，必须同时读取 `03_建模与代码/05_参数选择协议.md`。**
- 论文写作、逐问短导语、润色、审稿：读取 `05_论文与图表/01_论文流水线.md` 与 `05_论文与图表/05_逐问写作与算法呈现Gate.md`。
- 图表：同时读取 `05_论文与图表/02_图表工作流.md`。
- 论文框架、队友运行期间的论文工作：读取 [动态论文框架](05_论文与图表/06_动态论文框架.md)。逐问短导语仍由写作 Gate 规定；[表达参考](05_论文与图表/07_表达参考.md) 仅在需要措辞参考时选读，不是必选词库。
- 模型到论文交付：使用 `06_协作与交接/05_Paper_Handoff规范.md`。
- 最终提交：执行 `08_提交终检/01_FINAL_SUBMISSION_GATE.md`。
- **创建、修改、删除 Skill / Workflow / Gate / Profile / Template / README / VERSION 或执行任何 GitHub 仓库写操作：必须先读取 `06_协作与交接/06_三GPT协作与Skill共同维护.md`，并执行 Repository Write Gate。**
- **ML / DL / 预训练模型、外部公开数据、论文对应 Hugging Face 资产或远程 HF 计算任务：条件触发 `02_开赛与拆题/05_HuggingFace研究资产协议.md` 的 `HF Research Lane`。** 该 Lane 只用于解决已定义的研究缺口，不得作为所有赛题的默认必经步骤。

## 4. Repository Write Gate

任何 GitHub 写操作都必须在写入前确认目标分支和授权范围。

默认流程：

`读取共同维护规范 → 新建非 main 分支 → 修改/提交 → 创建 PR → required review → merge`

硬规则：

- **用户批准“修改内容”“加进 Skill”“更新 GitHub”“写一个新 Skill”不等于批准直接写 `main`，也不等于批准 merge。**
- 除非用户明确说“直接改 main”“不用 PR”或“直接 merge”，否则不得向默认分支执行 create / update / delete 等写操作，也不得自行 merge PR。
- 创建或修改 canonical Shared Core、Profile、Gate、Workflow 等团队正式文件时，必须遵守 `06_三GPT协作与Skill共同维护.md` 中的 Review Ownership 和 PR 必填字段。
- 写操作前如果没有明确 branch，视为阻断条件；不得依赖 API 的“默认分支”行为。
- 若工具调用可能因省略 `branch` 参数而落到默认分支，必须显式传入非 main branch。

## 5. Hugging Face 条件路由

当问题确实涉及以下任一情形时，可进入 HF Research Lane：

- 需要预测、分类、视觉、NLP、Embedding 等 pretrained challenger；
- 需要赛题规则允许的外部公开数据；
- 已找到论文，需要定位对应模型、数据集、Space 或 GitHub 实现；
- 需要核对 checkpoint、量化格式、framework、license 或 hardware compatibility。

Hugging Face 的 Model Card、Dataset Card、Space、下载量、趋势或第三方 benchmark 只能作为候选发现和资产信息，**不能替代本题 local benchmark、独立复算或 Evidence Gate**。HF 插件/Hub 不可用时直接回退到原论文 + 学术/Web 检索 + GitHub + 本地实验，不阻塞比赛主线。

## 6. 外部资料参考与原创性边界

允许检索和参考公开学术论文、教材、算法资料、标准、公开数据、开源实现与其他可核查来源，用于理解方法、形成候选模型、寻找参数先验、比较技术路线或辅助实现。

**不得把他人的完整解题思路、整套模型结构、代码、文字、图表或结果直接作为本队成果照搬。** 若参考了外部模型或思路，应根据本题的 Question Contract 重新确定变量、目标、hard constraints、参数与求解流程，并在本题数据、评价口径和验证体系下独立求解、比较和核验；进入论文或正式代码的外部资料应按规则记录来源并规范引用。

经典模型、通用算法或行业标准方法可以合理采用，不要求为了制造表面差异而刻意改名或改结构。判断重点是：团队是否真正完成了本题化建模、独立分析与验证，而不是把外部成品答案直接移植为本题结论。

## 7. Evidence before prose

每问先确定：输出、输入、分析单位、变量、目标、约束、baseline、正式模型、验证、关键结果、不确定性和下游接口。

缺少必要实验、Frozen source、真实求解步骤或正式数字时，返回 Missing Evidence / INCOMPLETE 或显式占位符。禁止用通用语言掩盖缺口。

非平凡求解必须有本题专属伪代码或算法流程，写出真实输入、关键变量、候选/循环、hard constraint、接受/停止条件、失败分支与输出复算。

## 8. Freeze 与共同事实源

正式同步只认：`project_state.yaml`、Task、Interface、Handoff、Frozen Source of Truth、Figure Registry、Git commit / PR。

聊天上下文不能覆盖这些来源。`FROZEN` 内容只有 P0 问题才能重开，并建立新版本后重跑依赖 Gate。

## 9. Runtime Lite

日常 Skill 不携带大型论文 PDF/PNG。运行包只保留 dispatcher、Shared Core、三个 Profile、必要 workflow、templates、source index 与 provenance。全文证据按 `skills/cumcm-rigorous-workflow/references/SOURCE_INDEX.md` 检索。

## Completion

一个模块只有在数学、工程、evidence 和论文接口均有可追溯证据后才能进入 FROZEN / PAPER_LOCKED。单次“跑通”、结果 Excel、聊天规划或外部 Model Card 指标都不构成完成。
