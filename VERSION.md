# Version 2.2.0 — Multi-Agent Validation + Code Execution Hardening

## v2.2.0 增量升级

本次升级吸收外部数模自动化流水线中经过实践验证的**工程机制**，但不引入其特定模型、API、并发参数、评分阈值或科学 Gate 软放行规则；同时补齐代码执行链与 Runtime Lite 的工程闭环。

- 新增 `07_AI协作/05_多Agent验证流水线与回流协议.md`：把多 Agent 定位为执行编排层，而不是新的科学裁决层；
- 新增 `ORCH-STATE-001`：执行状态与科学验证状态分离，允许无依赖任务继续，但 FAIL 不得因重试/超时/预算耗尽自动转 PASS；
- 新增 `ORCH-REDTEAM-001`：头条数字优先进行信息隔离式红队复算，禁止把“第二个 Agent 阅读原代码后认可”直接称为独立复算；
- 独立验收增加“同声明口径复算 → 独立口径挑战”，将数值错误和定义/口径差异分开；
- 随机、Monte Carlo、仿真和合成输入必须冻结 generation method、seed/config 与 SHA256，先做同输入复算再做鲁棒性挑战；
- 模型选择协议增加 `MODEL-TOURNAMENT-001`：复杂问可用 baseline + 1–3 个候选做统一小样原型，先资格筛查、后同口径比较，结束后收敛为主模型 + 最多一个备选；
- 新增 checkpoint/resume 规则：恢复前核对 source commit、input manifest/hash 与 materially 影响结果的配置，禁止利用旧 checkpoint 绕过 Gate；
- 结果来源链增加 `CHANGESET-001`：正式数字变更必须建立换版影响清单，并按 Frozen Output → Paper Metrics → 下游 → 图表 → 正文 → 摘要 → stale-value check 传播；
- 新增返工台账、变化守卫、结构守卫、生产者—消费者契约核对与工作流 dry-run 场景；
- 明确 `ORCH-NO-SOFTPASS-001`：红队未复算、hard constraint 未通过、关键指标不可追溯、Agent 失败或预算耗尽均不得自动科学放行；
- 新增 `templates/红队独立复算报告模板.md` 与 `templates/结果换版影响清单模板.md`；
- Runtime manifest / Source Index 同步纳入状态机、模型选择、独立验收、结果来源链、多 Agent 协议和新模板；
- 新增 `03_建模与代码/06_代码执行与复现Gate.md`：冻结 Execution Contract，分离 solver/validator/export/plot，要求真实 smoke test、规模预算、时间因果审计、独立复算、官方输出 readback、clean replay 与换版影响传播；
- Runtime Lite 改为代码执行自包含：加入 `README.md`、`VERSION.md`、MVP/实验循环/约束优先/敏感性、接口、冻结包、clean replay、AI/Codex 等运行时必需规则，消除“规则要求读取但 Runtime 未携带”的悬空引用；
- Runtime builder 新增 `RUNTIME_BUILD_MANIFEST.json` 与 `SHA256SUMS.txt`，记录 source commit、Skill version、源 manifest SHA256、文件大小和文件哈希；
- Runtime binary policy 扩展到常见图片、压缩包、Office、数组/列式数据文件，并增加单文件大小上限，避免把大型 corpus 或比赛数据误打进 Skill；
- 新增 `tools/validate_code_execution_runtime.py` 与负面 contract tests：缺 required path、加入禁用二进制、篡改已封印文件时必须 FAIL；CI 同时验证 canonical repo 与 built Runtime Lite。

### 与既有严格规则的冲突处理

本次明确采用更严格方案：

```text
流程可以降级继续 ≠ 科学结论可以降级转正
```

如果某模块验证失败，自动化系统可以继续执行不依赖该模块的工作，但该模块仍保持 `FAIL / REOPEN` 或 `MATHEMATICAL_P0`，不得进入 `FROZEN`。最终 Submission Gate 的 hard blockers 仍必须全部清零。

## v2.1.6 增量升级

- 新增 `CORE-GIT-WRITE-001 Repository Write Gate`；
- 任何创建、修改、删除 Skill / Workflow / Gate / Profile / Template / README / VERSION 或其他团队正式文件的 GitHub 写操作，必须先读取 `06_协作与交接/06_三GPT协作与Skill共同维护.md`；
- 默认写入路径强制为 `non-main branch → commit → PR → required review → merge`；
- 明确“用户同意修改内容”不等于“授权直接写 main”，也不等于“授权 merge”；
- 除非用户明确要求直接改 main / 不用 PR / 直接 merge，否则所有 create / update / delete 都必须显式指定非 main branch，禁止依赖 API 默认分支行为；
- PR 创建后默认停在 Review 状态，不得自行 merge；
- Shared Core、canonical Gate / Workflow / Profile 等正式文件继续执行原 Review Ownership。

## v2.1.5 增量升级

- 明确外部资料参考边界：允许使用公开论文、教材、算法、标准、公开数据和开源实现形成候选思路与技术先验；
- 禁止把他人的完整解题思路、整套模型结构、代码、文字、图表或结果直接照搬为本队成果；
- 借鉴外部模型后必须回到本题 Question Contract，重新确定变量、目标、hard constraints、参数与求解流程，并在本题数据与评价口径下独立求解和验证；
- 经典模型和通用算法无需为了“看起来不同”而刻意改名或改结构，原创性重点放在本题化建模、独立分析、证据与验证；
- Final Submission Gate 升级到 v2.2：新增 `submission_mirror/`，要求从最终提交镜像执行 clean replay；
- 新增 Identity Lint，检查论文、附录、代码、README、数据、图表、文件名、目录名和绝对路径中的身份信息；
- 新增 MD5 Seal 状态机：`MD5_SUBMITTED → SEALED → EXACT_FILE_UPLOAD`，封存后禁止直接修改，任何修改都必须重新生成候选文件并重新提交 MD5。

## v2.1.2 增量升级

- 将逐问正式求解章节的开头从“重复问题概述”收敛为大标题下短导语；
- 当前文已有“问题分析”时，禁止再设置“本问目标与难点”等重复小节；
- 短导语统一采用“任务概括 → 核心难点 → 模型选择 → 应用依据”的四步结构；
- 导语不得提前塞入变量、公式、算法步骤、正式数字或未冻结结果；
- 逐问正文推荐顺序调整为“短导语 → 建模依据 → 模型建立 → 求解算法与伪代码 → 结果及证据 → 本问小结”；
- 篇幅紧张时允许删除单独本问小结，但禁止删除结果解释；
- dispatcher、Paper Pipeline、contract tests 与 runtime validator 同步升级。

## v2.1 核心升级

- 新增根目录 `SKILL.md`，允许将仓库作为可安装的数模工作流 Skill 使用；
- 新增模型证据充分性 Gate，要求基线、最优值锚点、稳定性、敏感性、鲁棒性和不可行诊断；
- 新增逐问写作与算法呈现 Gate，强制场景化模型引出和题目特定伪代码/流程；
- AI 在缺少真实步骤、实验或冻结来源时必须阻断定稿；
- Paper Handoff、AI Prompt、Submission Gate 与复盘清单同步升级。

## v2.0 保留架构

v2.0 从“流程规范”升级为“三条长期并行生产线”。

### 1. 重构三人分工
- CYQ：Paper Lead
- FYQ：Technical Lead
- XXT：Mathematical Lead

Leader 不再默认兼任模型总控。

### 2. 论文提前
第一次路线评审后正式启动 Paper Pipeline，
不再等模型全部完成。

### 3. Interface First + Mock
消除“上游未出结果 → 下游无法开发”的串行等待。

### 4. Blocked Rule
允许任务 blocked，不允许成员纯等待。

### 5. 工具容灾
工具故障优先切换工具，不再通过 FYQ/XXT 角色互换解决。

新增：
- 双 Coding Agent
- Failover Runbook
- 设备容灾
- 人员 Deputy
- 赛前故障演练

### 6. 三重验收
- Technical PASS
- Mathematical PASS
- Paper PASS

### 7. Visualization 一级化
新增 Figure Registry 与独立 Visualization Pipeline。

### 8. A/B/C 泛化
新增：
- 数据驱动型
- 运筹优化型
- 机理数值型
三个题型插件。

## 兼容性

保留 v1.0 中：
- Gate
- Freeze
- clean replay
- Source of Truth
- AI Prompt
- Submission Gate
- 2026 华数杯复盘

并对协作、时间线、论文、图表、容灾进行了结构级重写。
