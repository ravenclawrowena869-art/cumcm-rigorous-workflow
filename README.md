# 数模比赛全流程工作流 v2.2.0

## 从自己的角色开始

先读根 `SKILL.md` 与 Shared Core，按本次 `ACTIVE_ROLE` 进入一个角色入口：

| 角色 | 入口 |
|---|---|
| FYQ：技术总控 | [controller/ROLE.md](skills/cumcm-rigorous-workflow/roles/controller/ROLE.md) |
| XXT：数学建模与验算 | [modeling/ROLE.md](skills/cumcm-rigorous-workflow/roles/modeling/ROLE.md) |
| CYQ：论文 | [paper/ROLE.md](skills/cumcm-rigorous-workflow/roles/paper/ROLE.md) |

这是一个 Skill 的三个入口，不是三个独立 Skill。公共规则保留在原 Shared Core，职责保留在原 Profile，旧文件和旧任务引用仍有效。角色入口只告诉当前 AI 本次要读哪些材料。

论文框架新增[动态框架规则](05_论文与图表/06_动态论文框架.md)；逐问概述、图表顺序分别并入原写作 Gate、图表工作流；[表达参考](05_论文与图表/07_表达参考.md)可完全不用。未合并的分支仅为修改提案，不对团队自动生效。

这是面向 FYQ、XXT、CYQ 三人协作的数学建模竞赛工作流与 Shared Runtime Skill。当前战略默认主选 2026 CUMCM C 题，同时保留 A-Track 中可迁移的数值与优化验证经验。

v2.1 的核心变化：

- 三套 GPT 共用同一个 Shared Core；
- 通过 `ACTIVE_ROLE` 加载 FYQ / XXT / CYQ 不同 Profile；
- GitHub main 作为 Skill、Workflow、Prompt、Template 的 Single Source of Truth；
- 把华数杯 C 题三等奖评委反馈转化为 evidence Gate；
- Paper Handoff 升级为可直接服务 CYQ 写作的正式接口；
- Runtime Skill 与大型优秀论文 PDF/PNG corpus 解耦；
- 三个人都可以通过 branch + PR 共同维护 Skill。

---

## 1. Shared Three-GPT Architecture

```text
                         GitHub Repo
                    Single Source of Truth
                              │
                        Shared Core
                              │
              ACTIVE_ROLE / project_state
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
 FYQ GPT Profile       XXT GPT Profile       CYQ GPT Profile
 Technical +           Mathematical           Paper Lead
 Orchestrator          Lead                    │
          │                   │                   │
          └───────── Task / Handoff / Frozen Evidence ────────┘
```

三个角色值固定为：

- `FYQ_TECHNICAL_ORCHESTRATOR`
- `XXT_MATHEMATICAL`
- `CYQ_PAPER`

角色解析优先级：显式 `ACTIVE_ROLE` → `project_state.yaml.agent_bindings` → 用户一次声明 → role-neutral read-only。无法确定时不得猜角色。

---

## 2. Shared Core

三套 GPT 都必须执行：

`skills/cumcm-rigorous-workflow/core/SHARED_CORE.md`

其中固定：

- 官方题面/规则 authority；
- `project_state.yaml` 与 Frozen Source of Truth；
- Interface First；
- evidence before claims；
- Freeze 边界；
- 数据、leakage、约束和独立复算；
- 稳定性、敏感性、鲁棒性；
- AI 使用真实性；
- 三方 Git 协作规则。

Profile 可以改变默认工作重点，不能覆盖 Shared Core。

---

## 3. 三个长期角色

### FYQ — Technical Lead / Orchestrator

默认 Profile：`FYQ_TECHNICAL_ORCHESTRATOR`

负责：
- Question Map、Roadmap、技术路线集成；
- FYQ/XXT 建模与编程 Block 分发；
- Codex / Coding Agent；
- Git、数据、接口、测试、版本；
- Source of Truth、Freeze、clean replay；
- 三层 Review 和 Missing Evidence；
- 给 CYQ 的 Paper Handoff 初稿。

FYQ 统一集成主线，但不能越过 XXT 对数学目标、约束、单位和可行性的正式 Review。

### XXT — Mathematical Lead

默认 Profile：`XXT_MATHEMATICAL`

负责：
- 题意数学化；
- 决策变量、目标、hard constraints；
- 模型选择、推导和参数范围；
- validator specification；
- exact anchor / bound / optimization adequacy；
- 独立指标复算和 Mathematical Review。

专项冻结任务中不另行维护第二套主模型；发现 P0 时提出最小替代或重开建议，由 FYQ 统一集成。

### CYQ — Paper Lead

默认 Profile：`CYQ_PAPER`

负责：
- 论文骨架、问题分析、模型建立、问题求解；
- 结果解释、稳健性表达、摘要；
- Figure Registry、图表叙事和版面；
- AI 使用说明；
- 将 Paper Handoff 转成自然、以结论为中心的论文初稿。

证据不足时返回 `INCOMPLETE + 缺口清单`，不猜 Frozen 数字，不用通用算法介绍填空。

---

## 4. 正式共享状态

三套 GPT 不通过“另一边聊天里说过”同步正式状态。

只认：

- `project_state.yaml`；
- Task；
- Interface；
- Handoff；
- Frozen Source of Truth；
- Figure Registry；
- Git commit / PR。

事实优先级：

官方题目/规则/附件 → project_state → Frozen Source → canonical workflow → Task/Handoff → 临时聊天。

---

## 5. 比赛主流程

```text
官方题面/附件
→ Question Contract
→ Data Audit / 口径冻结
→ Atlas + 学术原型
→ EDA 排除模型
→ Baseline
→ Targeted Upgrade
→ Cross-question Interface
→ Validation / Robustness
→ Freeze
→ Paper Handoff
→ Paper / Figure QA
→ Final Submission Gate
```

长期原则：先判断题目真正要求输出什么，再选择模型。复杂模型必须证明相对 baseline 有真实增益。

---

## 6. 模型 Evidence Gate

正式 Gate：

`04_验收冻结/05_模型证据充分性Gate.md`

优化结果区分：

- `FEASIBLE`：hard constraints 通过；
- `COMPETITIVE`：稳定优于合理 baseline；
- `NEAR-OPTIMAL`：还有 exact anchor / bound / gap 等最优性证据。

华数杯三等奖评委反馈已经转化为通用检查：

- 简单预测的时序突变适配；
- 预测区间的 downstream protection；
- 顺序启发式的 permutation stress；
- exact/MILP anchor；
- 结构假设 counterfactual；
- 容量/功率和经验阈值扫描；
- 多指标迭代终止；
- 场景收敛差异；
- 不可行边界定量诊断。

具体的 20% 调整上限、RegionA 等仍属于对应华数杯 Q4 rehearsal，不是所有赛题的固定参数。

---

## 7. Paper Handoff 与论文线

模型通过 Evidence Gate 后，技术数学线使用：

`06_协作与交接/05_Paper_Handoff规范.md`

向 CYQ 交付：

- 本问合同；
- 本问中心逻辑；
- 核心数学；
- 本题专属求解/伪代码；
- baseline、稳定性、敏感性、鲁棒性；
- Frozen Metrics；
- 正式来源；
- Figure Registry；
- 论文禁区；
- 自然语言初稿。

论文组织强调：

`解决什么 → 为什么这样做 → 有什么好处 → 如何求解 → 什么证据支持 → 如何服务下一问/全文结论`

---

## 8. Figure Registry

图表分为：

- `result`
- `mechanism`
- `diagnostic`
- `robustness`

正式链路：

```text
Frozen Output → Figure Data → Figure Script → Figure → Paper
```

最终 PDF 还要检查大块空白、孤行、图表漂移、标题只剩 2–3 个字跨行等问题。

---

## 9. AI 使用说明

使用 AI Use Ledger，从比赛第一小时开始记录。

推荐流程：

`聊天记录 → 知识库 → 团队框架 → 人工重写`

该流程用于真实的人类审核、知识沉淀和论文质量控制，不用于规避 AI 检测。最终声明必须与真实使用深度一致。

---

## 10. Runtime Lite

运行 Skill 不再内置大型论文 PDF/PNG。

构建：

```bash
python tools/build_runtime_skill.py
python tools/validate_runtime_skill.py
```

Runtime Lite 包含 dispatcher、Shared Core、三个 Profile、必要 Gate、templates、source index 和 manifest。

大型优秀论文保留在 Project Files / Full Archive，需要全文时按索引检索。

---

## 11. 三人共同维护

推荐分支：

- `fyq/<topic>`
- `xxt/<topic>`
- `cyq/<topic>`
- `shared/<topic>`

Shared Core 改动至少需要另一角色 Review。Paper Handoff 等跨角色接口至少由输出方和消费方各审一次。

详细规则：

`06_协作与交接/06_三GPT协作与Skill共同维护.md`

禁止形成长期的 `FYQ_skill_final.zip / XXT_skill_final2.zip / CYQ_skill_newest.zip` 三套分叉。

---

## 12. 目录导航

- `00_总览/`：总流程、状态机和 Gate
- `01_赛前准备/`：环境与容灾
- `02_开赛与拆题/`：读题、路线评审、Owner、接口
- `03_建模与代码/`：MVP、实验循环、约束、场景
- `04_验收冻结/`：独立验收、Freeze、Source of Truth、模型 Evidence Gate
- `05_论文与图表/`：Paper Pipeline、写作 Gate、Figure Registry
- `06_协作与交接/`：角色、Task、Handoff、共同维护
- `07_AI协作/`：Prompt、AI Use Ledger、平台无关 Skill
- `08_提交终检/`：Final Submission Gate
- `09_本次比赛复盘/`：华数杯 C 实战经验
- `10_容灾与应急/`：工具、设备、人员 Plan B
- `11_题型插件/`：不同题型附加验收
- `skills/cumcm-rigorous-workflow/`：Runtime Shared Core、三个角色入口与原 Profile
- `templates/`：可复制模板
- `tools/`、`tests/`：Runtime Lite 构建与静态验证

---

## 13. 完成定义

一个模块只有在题意、数学、工程、evidence、接口和论文来源链都通过对应 Gate 后才算完成。聊天规划、单个 Excel、单次程序跑通都不能替代可复现证据。
