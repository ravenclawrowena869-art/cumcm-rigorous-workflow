# v2.1.5 执行资源路由与中文任务书设计

日期：2026-09-10  
状态：DESIGN_APPROVED_IN_CHAT / WAITING_WRITTEN_SPEC_REVIEW

## 1. 背景

团队现在同时具备三类执行资源：

1. `CODEX_ASTRA`：最高性能 Coding Agent；
2. `CODEX_SOL`：常规高质量 Coding Agent；
3. `GPT_EXECUTION`：直接在 GPT 执行窗口完成读取、运行、复算、审查、打包等任务。

现有 Skill 已规定 Codex / Coding Agent 是可替换执行工具，并要求 Prompt 包含背景、输入、目标、允许/禁止修改、验收、测试、风险和回滚，但尚未解决两个问题：

- 每个任务应该用哪一档执行资源，没有统一判定与自动升级规则；
- 团队任务书存在英文正文，FYQ / XXT / CYQ 无法快速人工审阅。

本设计把这两个问题固化为共享 Skill 的正式能力。

## 2. 设计目标

### 2.1 执行资源路由

每个正式 Task / Prompt 在生成时必须明确：

```text
【执行资源路由】
推荐执行器：CODEX_ASTRA / CODEX_SOL / GPT_EXECUTION
执行级别：REQUIRED / PREFERRED / SUFFICIENT
选择原因：……
是否允许降级：YES / NO
降级条件：……
升级触发：……
```

FYQ 负责给出初始路由；执行中如果出现高风险信号，允许自动建议升级到 Astra，但不能因此改变角色权限、Authority、Source of Truth 或 Mathematical Gate。

### 2.2 中文任务书

所有面向团队成员阅读的 Task / Authority 摘要 / Handoff / Controller routing / Missing Evidence 默认使用简体中文。

以下内容保持原始英文，不机械翻译：

- 文件名、路径、branch、commit、SHA；
- class / function / variable / enum / status code；
- 命令、schema 字段、测试名；
- 需要与代码或外部工具精确匹配的标识符。

目标是保证人能直观看懂，同时保持工程接口精确。

## 3. 三档路由模型

### 3.1 `CODEX_ASTRA`

适用于错误可能改变正式数学模型、可行性、核心结果或跨模块执行路径的任务。

典型触发：

- 首次实现或实质修改 LP / MILP / CP-SAT / 复杂调度器 / 交替优化 controller；
- objective、hard constraint、unit、state recursion、accounting 的核心实现；
- 从论文/数学规格首次落地非平凡算法；
- exact/MILP anchor 本身复杂且必须与 heuristic 同目标、同约束、同口径；
- surrogate/full-model、fixed/adaptive controller 等多路径状态机；
- Frozen 主线发现 P0 后的正式修复；
- 多模块耦合、难定位根因、solver 与独立复算矛盾；
- Freeze 前仍需修改核心算法代码。

默认级别：`REQUIRED` 或 `PREFERRED`。

### 3.2 `CODEX_SOL`

适用于数学定义已经冻结，主要工作是工程实现、测试、批跑、包装和小范围修复的任务。

典型触发：

- data loader / schema / CSV 转换；
- experiment runner / seed runner / sweep harness；
- validator / tests / provenance / hash 工具；
- package-relative path 修复；
- CLI wrapper / batch scenario runner；
- 冻结公式下的小范围 bugfix；
- 图表脚本、日志字段、导出格式；
- Astra 完成核心实现后的测试补强。

默认级别：`SUFFICIENT`。

若执行中触及数学定义、正式约束或核心 Claim，应停止自行裁决并升级到 FYQ/XXT，必要时路由为 Astra。

### 3.3 `GPT_EXECUTION`

适用于不需要长期修改真实代码仓库，重点是读取、执行、复算、审查、解释和交接的任务。

典型触发：

- ZIP CRC / SHA / manifest 验证；
- 运行已有 tests / scripts；
- independent metric recomputation；
- CSV 统计与结果解释；
- Controller Review / XXT Mathematical Review；
- evidence matrix / Paper Handoff / Figure Registry；
- 文件比对 / package completeness audit；
- 文献和候选初筛；
- 论文结构审查与 CYQ evidence placeholder；
- AI Use Ledger 整理；
- 打包与下一 Wave 任务书生成。

默认级别：`SUFFICIENT`。

## 4. 路由判定原则

路由不按“任务看起来难不难”粗略判断，而按风险和执行形态判断。

优先检查：

1. 是否需要修改真实代码仓库；
2. 是否涉及 objective / hard constraints / unit / accounting / path-dependent state；
3. 错误是否可能 materially 改变 feasibility / solution ranking / core claim；
4. 是否跨多个核心模块或需要重构执行路径；
5. 数学规格是否已经由 Authority / XXT 冻结；
6. 任务主要是实现，还是运行/复算/审查现有资产。

判定逻辑：

```text
无需长期修改代码仓库，主要是运行/复算/审查
→ GPT_EXECUTION

需要改代码，但数学/接口已冻结，工作以工程落实为主
→ CODEX_SOL

需要改核心算法/状态机/正式数学路径，或错误可改变正式结论
→ CODEX_ASTRA
```

## 5. 自动升级与降级

### 5.1 升级到 Astra

以下任一条件触发 `EXECUTION_ESCALATION = CODEX_ASTRA`：

- 连续两轮 minimal fix 仍未解决根因；
- 修改开始跨多个核心模块；
- 出现 objective / hard constraint / unit / accounting 风险；
- solver 与 independent recomputation 矛盾；
- surrogate 可能 materially 改变正式结果；
- 动态 replay 出现无法解释的 violation；
- 任务从“按规格实现”升级成“重新设计算法”；
- Sol 出现 patch-on-patch；
- 测试很多但无法证明真实 execution path。

升级只改变执行器，不改变 FYQ / XXT / CYQ 权限。

### 5.2 Astra 不可用

`ASTRA_REQUIRED` 但 Astra 临时不可用时，不允许降低 Evidence Gate。

流程：

1. 判断是否可等待；
2. 若不能等待，把任务拆成更小 Frozen Blocks；
3. Sol 逐 Block 实现；
4. 强制 TDD；
5. 强制 independent replay；
6. 数学关键路径单独送 XXT / GPT Review；
7. 最终 Freeze 条件不变。

## 6. Task / Prompt 新结构

正式 Task 顶部固定加入：

```text
【负责人】
FYQ / XXT / CYQ

【执行资源路由】
推荐执行器：...
执行级别：...
选择原因：...
是否允许降级：...
降级条件：...
升级触发：...

【任务语言】
中文；代码标识符、路径、命令保持原文。
```

随后再进入原有：

- 任务背景；
- 必须读取；
- Source of Truth；
- Required Gate；
- 唯一目标；
- 允许修改；
- 禁止修改；
- 执行步骤；
- 验收；
- 交付与 Handoff。

## 7. 计划修改文件

目标版本：`v2.1.5`

计划修改：

1. `SKILL.md`
   - Dispatcher 加载执行资源路由协议；
   - 明确正式 Task 必须带 execution route。

2. `skills/cumcm-rigorous-workflow/core/SHARED_CORE.md`
   - 新增 `CORE-EXEC-ROUTING-001`；
   - 新增 `CORE-TASK-LANG-001`。

3. `skills/cumcm-rigorous-workflow/profiles/FYQ_TECHNICAL_ORCHESTRATOR.md`
   - FYQ 每次分发任务必须给推荐执行器、级别、理由、降级/升级条件。

4. `07_AI协作/01_AI_Codex工作协议.md`
   - 扩展为三档执行器与升级/降级规则。

5. `07_AI协作/02_AI_Prompt模板.md`
   - 模板加入执行资源路由段；
   - 默认中文正文。

6. `07_AI协作/04_平台无关Skill与Agent切换.md`
   - 明确能力档是资源，不是角色；
   - Astra 不可用时的降级流程。

7. 新增 `07_AI协作/05_执行资源路由协议.md`
   - 完整路由矩阵、典型任务、升级/降级和比赛时快速决策表。

8. tests / runtime manifest
   - 增加 contract tests；
   - 若协议进入 Runtime Lite，同步 manifest / validator。

## 8. TDD / Skill 测试设计

按照 skill-edit TDD，实施前必须先建立会失败的 contract / pressure tests。

### RED 场景

至少覆盖：

1. **核心 MILP 实现任务**
   - 旧 Skill 未要求执行器路由；
   - 期望新版输出 `CODEX_ASTRA`。

2. **CSV runner / path fix**
   - 期望 `CODEX_SOL`。

3. **ZIP 验证 / Independent Review**
   - 期望 `GPT_EXECUTION`。

4. **Sol 执行中发现 hard-constraint 风险**
   - 期望升级 `CODEX_ASTRA`。

5. **面向团队的 Task**
   - 旧模板可能出现英文正文；
   - 新版必须有中文结构字段。

6. **Astra 不可用**
   - 必须给降级 Block 化与不降低 Gate 的流程，不能直接把 `REQUIRED` 改成 `SUFFICIENT`。

### GREEN 验收

- 新 contract tests 全部 PASS；
- 原有 Skill tests 全部 PASS；
- canonical Runtime Lite validator PASS；
- built Runtime Lite validator PASS；
- task template 同时包含：
  `推荐执行器 / 执行级别 / 选择原因 / 是否允许降级 / 降级条件 / 升级触发 / 中文正文规则`。

## 9. 非目标

本版本不做：

- 按模型名称硬编码“某个模型永远最好”；
- 改变 FYQ / XXT / CYQ 权限；
- 让 Astra 成为比赛单点故障；
- 因使用更强模型而降低 TDD / Mathematical Review / Evidence Gate；
- 把所有任务都升级到 Astra；
- 自动替用户消耗高性能额度而不在任务书中说明。

## 10. 成功标准

上线后，任何正式任务书在人工打开时都能在前几十行回答：

1. 谁负责；
2. 应该开什么执行器；
3. 为什么；
4. 能不能降级；
5. 什么情况下必须升级；
6. 这份任务到底要做什么；
7. 哪些内容不能碰。

同时，执行器选择不得覆盖 Mathematical Gate、Frozen Source of Truth 与 Evidence before claims。
