# Proposal — Legacy Archive Authority Replacement During 2026 CUMCM

状态：`PROPOSAL_ONLY / NOT_CANONICAL`

作者角色：`FYQ_TECHNICAL_ORCHESTRATOR`

日期：2026-09-11

## 1. 背景

项目用户原始规则要求数学建模任务联合读取：

1. `write-update-math-modeling-paper-complete.zip`
2. `math-modeling-master-workflow-v2.2.0.zip`
3. `cumcm-rigorous-workflow-main (1).zip`

当前 2026 CUMCM 正赛环境可以定位：

- `math-modeling-master-workflow-v2.2.0.zip`

当前 Project / Library / controller runtime 无法定位 exact：

- `write-update-math-modeling-paper-complete.zip`
- `cumcm-rigorous-workflow-main (1).zip`

用户本人也确认目前手上没有这两个 exact ZIP。

因此不能继续把“找回两个本地文件名完全一致的 ZIP”作为无限期主线 blocker，也不能假装已经读取它们。

## 2. 关于“它们是否已经被拆进当前 Skill”的证据

### 2.1 `cumcm-rigorous-workflow-main (1).zip`

当前 canonical workflow 本身明确：

- 团队正式规则只认 GitHub main；
- Runtime Skill 由 GitHub canonical workflow 驱动；
- `SOURCE_INDEX.md` 把 `README.md`、Evidence Gate、论文流水线、图表工作流、逐问写作 Gate、Paper Handoff、AI Use Ledger、Final Submission Gate 等列为 canonical workflow；
- Runtime Lite 只保留执行规则与索引，大型全文语料外置。

因此 `cumcm-rigorous-workflow-main (1).zip` 很可能只是某次下载 GitHub repo 时产生的本地 ZIP 快照；`(1)` 也符合浏览器/系统重复下载时的本地重命名习惯。

但在没有旧 ZIP bytes / hash 的情况下，不能声称“当前 main 与旧 ZIP byte-identical”。

推荐 provenance 标记：

`LIKELY_REPOSITORY_SNAPSHOT / BYTE_IDENTITY_NOT_PROVEN`

### 2.2 `write-update-math-modeling-paper-complete.zip`

当前 GitHub history 提供了“旧 Paper Skill/规则被吸收进 canonical workflow”的直接线索：

- `v2.1: add model evidence and paper-writing gates`：把 paper-writing、handoff、submission 等规则集成到 canonical workflow；
- `v2.1.2: harden per-question paper section intros` 的 commit message 明确写有：`Integrate the Paper Craft short-intro rule into the canonical per-question writing gate`；
- current `SOURCE_INDEX.md` 已把论文流水线、逐问写作 Gate、图表 workflow、Paper Handoff、AI Use Ledger 列为 canonical sources。

这些证据支持：旧的 Paper Craft / 写作 Skill 内容至少有一部分已经被拆分、重构并吸收到当前 `cumcm-rigorous-workflow`。

但当前 repo 搜不到 exact 文件名 `write-update-math-modeling-paper-complete.zip`，也没有旧 ZIP hash，所以不能证明：

- 该 ZIP 就是上述 Paper Craft 的唯一来源；
- 当前 canonical 已完整覆盖旧 ZIP 的每一条规则；
- 当前文件与旧 ZIP 内容等价。

推荐 provenance 标记：

`LIKELY_PARTIALLY_ABSORBED / FULL_EQUIVALENCE_NOT_PROVEN`

## 3. 正赛期间建议的 authority 替代方案

### A. `cumcm-rigorous-workflow-main (1).zip`

正式替代为：

`canonical GitHub main + pinned commit SHA`

每个关键 Gate / Freeze 记录本轮使用的 commit SHA。

若需要离线快照，可以从对应 commit 下载 ZIP，但文件名不是 authority；commit SHA 才是。

### B. `write-update-math-modeling-paper-complete.zip`

在 legacy archive 不可获得期间，正式论文规范由当前 canonical 中以下文件联合承担：

- `05_论文与图表/01_论文流水线.md`
- `05_论文与图表/02_图表工作流.md`
- `05_论文与图表/05_逐问写作与算法呈现Gate.md`
- `06_协作与交接/05_Paper_Handoff规范.md`
- `07_AI协作/03_AI使用记录.md`
- `08_提交终检/01_FINAL_SUBMISSION_GATE.md`
- 对应 `CYQ_PAPER` Profile 与 Shared Core

旧 ZIP 若日后找回：

1. 记录 SHA256；
2. 与 current canonical 做 diff / coverage audit；
3. 发现 canonical 缺失且仍有价值的规则时，再走 branch → PR → review 合入；
4. 不以旧 ZIP 自动覆盖已经验证过的 current canonical rule。

### C. `math-modeling-master-workflow-v2.2.0.zip`

继续作为当前可读取的 legacy/master workflow supplement 使用；直到其规则全部被正式迁移或明确 supersede 前，不取消它的参考地位。

## 4. 正赛行为原则

- 缺失 legacy archive 必须如实记录 `SOURCE_LIMITATION`；
- 不得声称已经读取不存在的文件；
- source limitation 本身不自动否定已经通过独立数学/数值验证的 evidence；
- 但 Freeze / final submission 必须说明本轮实际 authority 来源；
- 如果 legacy archive 后续找回且发现 P0 级规则冲突，按当前 Source of Truth 重新 Review；
- 正赛期间优先使用可验证、版本化、多人共享的 canonical source，不追逐无法定位的本地文件名。

## 5. 对当前 2026 CUMCM Q1 的处理

Q1 Blind Red Team 已把两个 exact ZIP 的缺失写入 `SOURCE_LIMITATIONS.md`，并未伪称联合复读完成。

建议：

- 保留 Red Team 数值 evidence；
- 把 legacy source gap 改记为 provenance / authority limitation；
- Q1 Final Freeze 使用当前 canonical pinned commit + `math-modeling-master-workflow-v2.2.0.zip` + 官方材料 + 当前 Task/Handoff/Gate 做最终 conformance audit；
- 不再要求用户必须找回无法证明存在于其设备上的两个 exact ZIP 才能推进正赛。

## 6. 本 Proposal 不做什么

本文件当前只是 Proposal：

- 不修改 Shared Core；
- 不删除旧用户规则；
- 不宣称旧 ZIP 已完全被 current Skill 覆盖；
- 不自动授权任何模块 Freeze；
- 不改变 Mathematical / Evidence / Paper Gate。

建议 Review Ownership：

- FYQ：authority / execution integration；
- CYQ：paper-workflow coverage；
- XXT：确认替代方案不会弱化数学 Gate。

三角色审过后，再决定是否需要把最小规则升级进 canonical Shared Core / README / Source Index。
