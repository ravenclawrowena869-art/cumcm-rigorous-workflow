# v2.1.6 Codex Execution Kernel + Task Capsule 架构修订

日期：2026-09-10  
状态：DESIGN_APPROVED_IN_CHAT / WAITING_WRITTEN_SPEC_REVIEW  
来源：PR #11 执行资源路由设计 + CYQ independent review + Codex marketplace compatibility 复盘

## 1. 背景与版本调整

当前 GitHub `main` 已推进到 v2.1.5，因此 PR #11 原计划使用的 v2.1.5 版本号已经发生冲突。本修订目标版本统一改为：

`v2.1.6`

PR #11 现有执行资源路由与中文任务书设计保留为设计输入，但不再直接按旧结构 merge。后续实现必须基于最新 `main` 重新集成，避免覆盖 v2.1.5 已加入的原创性与提交硬化规则。

## 2. 核心架构决定

完整 `cumcm-rigorous-workflow` 继续作为 FYQ / XXT / CYQ 三套 GPT 的上层控制面，不把完整 Runtime Lite 原样加载进 Codex。

新的消费层分为：

```text
Canonical Full Skill
├─ GPT Runtime Lite
│  ├─ Shared Core
│  ├─ FYQ Profile
│  ├─ XXT Profile
│  ├─ CYQ Profile
│  ├─ Evidence / Paper / Freeze workflows
│  └─ Team coordination
│
└─ Codex Execution Layer
   ├─ Codex Execution Kernel
   ├─ Task Capsule Contract
   └─ Optional Marketplace Distribution
```

固定原则：

```text
FULL_SKILL_TO_CODEX = NO
CODEX_CONTEXT_MODE = TASK_CAPSULE_FIRST
MARKETPLACE_REQUIRED_FOR_COMPETITION = NO
AGENTS_PLUS_CAPSULE_FALLBACK = REQUIRED
```

Codex 只消费执行当前 Block 真正需要的规则，不消费无关角色、无关 Question、论文工作流、完整历史 Handoff 或大型参考库。

## 3. Codex Execution Kernel

Execution Kernel 是一个小型、稳定、平台可迁移的执行内核。它只保留 Codex 反复需要的硬规则，不复制完整 Shared Core。

必须包含：

1. 先读当前 Task Capsule；
2. Source of Truth / Authority 优先；
3. 只修改 `ALLOWED_WRITE_PATHS`；
4. 禁止修改 `FORBIDDEN_PATHS`；
5. TDD：RED → GREEN；
6. 禁止 mock / stub / placeholder / hardcode 冒充完成；
7. 正式目标与核心指标需要独立复算；
8. 动态 hard constraints 需要 full replay；
9. 不自行修改数学定义、单位、accounting、hard constraints；
10. 数学规格不清楚时 fail-closed，并返回 `STOP_AND_ESCALATE`；
11. 不自行发布 Mathematical PASS / Freeze；
12. 输出 tests / evidence / provenance / checksums / handoff；
13. 执行器升级只改变资源，不改变角色权限。

### 3.1 不进入 Kernel 的内容

以下内容默认留在 Full Skill，不注入 Codex：

- FYQ / XXT / CYQ 完整 Profile；
- Paper Pipeline；
- Figure Registry 规则；
- AI Disclosure 全流程；
- 无关题型插件；
- 无关 Question 的 Evidence Gate 细节；
- Hugging Face Research Lane 的完整协议；
- 历史比赛复盘全文；
- 大型论文/Atlas corpus。

只有当前 Task 明确需要某条规则时，才通过 Task Capsule 带入最小必要摘录。

## 4. Task Capsule

FYQ 为每个 Codex Block 生成自包含 Capsule。推荐结构：

```text
TASK_<ID>/
├── 00_START_HERE.md
├── TASK.md
├── SOURCE_AUTHORITY.json
├── MATH_CONTRACT.md               # 适用时
├── ALLOWED_WRITE_PATHS.txt
├── FORBIDDEN_PATHS.txt
├── VERIFY_REQUIREMENTS.md
├── REQUIRED_DELIVERABLES.md
├── RELEVANT_GATE_EXCERPT.md        # 只带当前任务必要 Gate
└── SHA256SUMS.txt                  # 正式 Authority Bundle 适用时
```

### 4.1 Capsule 最小自描述要求

`TASK.md` 必须回答：

- 当前唯一目标；
- 当前角色 / Consumer；
- 推荐执行器；
- 执行资源要求级别；
- 为什么使用该资源；
- 允许/禁止修改；
- 输入与 Source of Truth；
- 验收标准；
- 失败与升级条件；
- Required Deliverables。

Codex 不需要自行遍历完整数模仓库寻找这些约束。

## 5. 执行资源词汇修订

接受 CYQ Review 对 `REQUIRED / PREFERRED / SUFFICIENT` 与 Evidence Sufficiency 混淆风险的意见。

v2.1.6 建议正式改为：

- `MUST_USE`
- `PREFER`
- `ALLOWED`

字段名使用：

`执行资源要求级别`

旧 PR #11 中：

- `REQUIRED` → `MUST_USE`
- `PREFERRED` → `PREFER`
- `SUFFICIENT` → `ALLOWED`

旧 Task/Handoff 可保留历史原值，不回写旧证据；新生成任务统一使用新词汇。

协议开头必须写死：这些值只描述执行资源路由强度，不表示 Evidence Sufficiency、Mathematical Review 结论、Gate 状态或模型质量等级。

## 6. 数学裁决角色硬绑定

接受 CYQ Review 的角色边界修正。

任何正式：

- `Mathematical Review`
- `Mathematical PASS`
- `Mathematical Veto`
- `P0 REOPEN` 数学裁决

必须同时满足：

`ACTIVE_ROLE=XXT_MATHEMATICAL`

`GPT_EXECUTION / CODEX_SOL / CODEX_ASTRA` 只描述执行资源，永远不能单独构成 reviewer identity。

若当前执行窗口不是 XXT role，即使完成独立复算，也只能输出 technical finding / review input，不得发布 Mathematical PASS/Veto。

## 7. Astra / Sol / GPT Execution 路由

### `CODEX_ASTRA`

用于核心算法、正式数学路径、复杂状态机、跨核心模块、material surrogate/fidelity 风险和 P0 修复。

### `CODEX_SOL`

用于数学与接口已经冻结后的工程实现：runner、validator、sweep harness、tests、path fix、provenance、CLI、batch execution 等。

### `GPT_EXECUTION`

用于无需长期修改真实仓库的读取、运行、复算、Review input、Handoff、打包与结果分析。

### 7.1 自动升级

以下任一触发：

`EXECUTION_ESCALATION = CODEX_ASTRA`

- 连续两轮 minimal fix 仍未解决根因；
- 触及 objective / hard constraints / unit / accounting；
- solver 与 independent recomputation 冲突；
- surrogate 可能 materially 改变正式结果；
- 动态 replay 出现无法解释 violation；
- Sol 出现 patch-on-patch；
- 任务从照规格实现变为重设计算法；
- 多核心模块共同修改。

### 7.2 Astra unavailable

废弃“Frozen Blocks”表述，统一使用：

`spec-frozen bounded implementation blocks`

中文：`规格冻结的小型实现块`

其含义仅表示数学规格、接口和写入边界已经冻结，不表示模块达到 `FROZEN / G3 Freeze`。

若 `CODEX_ASTRA / MUST_USE` 临时不可用：

1. 能等待则等待；
2. 不能等待时拆成规格冻结的小型实现块；
3. 使用 Sol 逐块实现；
4. 保留原 route；
5. 记录 `ACTUAL_EXECUTOR=CODEX_SOL` 与降级原因；
6. 强制 TDD；
7. 强制 independent replay / recomputation；
8. 数学关键路径必须回到 `ACTIVE_ROLE=XXT_MATHEMATICAL` Review；
9. Evidence / Mathematical / Freeze Gate 不降低。

## 8. 中文任务书与两档可读性模式

接受 CYQ Review 对顶部信息密度的修正。

### `ROUTE_COMPACT`

仅允许用于低风险 `ALLOWED` 任务，例如 review input、打包、运行既有脚本、简单 path fix。

```text
【执行资源路由｜COMPACT】
推荐执行器：GPT_EXECUTION
执行资源要求级别：ALLOWED
选择原因：一句话
升级触发：……
```

### `ROUTE_FULL`

以下任一情况必须使用：

- `MUST_USE` 或 `PREFER`；
- 需要修改真实仓库；
- 触及核心算法、状态机或正式数学路径；
- 存在 executor failover；
- 失败可能改变正式结果或 claim。

```text
【执行资源路由｜FULL】
推荐执行器：CODEX_ASTRA / CODEX_SOL / GPT_EXECUTION
执行资源要求级别：MUST_USE / PREFER / ALLOWED
选择原因：……
是否允许降级：YES / NO
降级条件：……
升级触发：……
```

面向团队的正文继续默认简体中文。文件名、路径、branch、commit、SHA、class/function/variable、command、schema、enum/status code 保持原文。

## 9. 去重规则

接受 CYQ Review 的 Skill 膨胀问题。

Canonical ownership 固定为：

- Shared Core：只保留 invariant 与 authority boundary；
- `07_AI协作/05_执行资源路由协议.md`：唯一完整 execution-routing 判定源；
- Prompt / Task template：只保留结构字段，不复制矩阵；
- FYQ Profile：只规定 FYQ 必须输出 route，并链接 canonical protocol；
- Platform switch：只写“资源不等于角色”与 fallback 入口；
- Codex Execution Kernel：只保留 Codex 执行硬约束，不复制 Full Skill。

禁止在 5 个以上文件重复完整典型任务矩阵、升级条件和 fallback 细节。

## 10. Codex Marketplace 定位

Marketplace 是可选分发层，不是比赛依赖。

```text
Marketplace available
→ 安装 Codex Execution Kernel

Marketplace unavailable
→ repo-level AGENTS.md / Execution Kernel + Task Capsule
→ 比赛继续
```

完整 Full Skill 不通过 marketplace 注入 Codex。

### 10.1 Marketplace root

如果实现 GitHub marketplace，repository root 使用：

`.agents/plugins/marketplace.json`

Codex 导入时 repository URL 指向仓库，Path 留空；只有 marketplace 位于子目录时才填写 Path。

插件本体只分发 execution kernel / task-capsule support，不分发三角色完整控制面。

## 11. 行为测试要求

接受 CYQ Review，新增行为级 contract tests；token-presence tests 只作为最低层。

至少覆盖：

1. `Mathematical Review` 且 `ACTIVE_ROLE != XXT_MATHEMATICAL` → 不得产生 Mathematical PASS/Veto；
2. `CODEX_ASTRA / MUST_USE` 降级到 Sol → 必须保留原 route、记录实际 executor、TDD、independent replay、XXT Review；
3. `CODEX_SOL` 执行中触及 objective/hard constraint/unit/accounting → 必须返回 `EXECUTION_ESCALATION = CODEX_ASTRA`；
4. `ROUTE_COMPACT` 只能用于低风险 `ALLOWED`；
5. Codex Task Capsule 不得默认加载 CYQ Paper Profile、无关 Question 或完整 Runtime Lite；
6. marketplace 缺失时，AGENTS + Capsule fallback 仍可执行；
7. Execution Kernel 中不得出现 `G3_FREEZE=PASS` 自授逻辑。

Skill 修改继续执行 RED → GREEN → regression → Runtime validation。

## 12. 与 PR #11 的关系

PR #11 的 CYQ review 当前为 `CHANGES_REQUESTED`，该结论成立。

由于：

- `main` 已经推进到 v2.1.5；
- PR #11 原目标版本与 main 冲突；
- 新设计改变 Codex 消费架构；
- PR #11 当前 mergeability 已受 main 演进影响；

建议 PR #11 转回 Draft，作为原始 TDD/Review 历史保留。正式实现应从最新 main 建立新的 v2.1.6 branch/PR，避免在旧 base 上继续堆叠并制造 merge conflict。

## 13. 成功标准

v2.1.6 完成后：

1. GPT 三角色仍加载 Full Skill；
2. Codex 不需要加载 Full Skill；
3. 每个 Codex 任务收到自包含 Capsule；
4. Astra/Sol/GPT route 在任务生成时已明确；
5. Mathematical authority 必须绑定 XXT role；
6. Team Task 默认中文并支持 compact/full 两档；
7. Marketplace 挂掉不影响比赛执行；
8. 执行路由规则只有一个 canonical 完整来源；
9. 新行为 tests 与旧 Runtime tests 全部通过；
10. 合并前由 XXT 或 CYQ 对最终新 HEAD 再做一次独立 Review。
