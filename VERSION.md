# Version 2.2.1 — Role Entry Navigation and Paper Framework

## v2.2.1 审查修订

- 新增 `TECH_DIRECTION_STABLE` JIT Gate：只有 Question Contract、主模型方向、核心变量、目标与 hard constraints、information set、baseline/challenger、指标和验证方向稳定，且无结构性 Mathematical P0 时，才展开逐问题目化方法骨架；该 Gate 不等于 Mathematical PASS、Evidence PASS 或 Freeze。
- 将论文交接拆为 `Pre-Paper Brief` 与 `Formal Paper Handoff`：前者只支持方法骨架和证据需求，后者在 Validation PASS 与 FROZEN 后承载正式数字、结果、优势、稳健性、推荐和摘要结论。
- 将“显著提高精度”“避免陷入局部最优”等强句从表达素材移至高风险反例，避免先写结论、后找证据。
- 本版本号预留给 PR #14 的 v2.2.0 之后；PR #14 未合并、rebase 与联合来源核验未完成前，本 PR 继续保持 Draft，不构成团队发布。

## v2.2.0 原始提案

## v2.2.0 增量升级

- 在同一 Skill 内新增 controller/modeling/paper 三个角色入口；保留 Shared Core、Profile、workflow 与旧路径，不复制三份公共规则。
- 保留 FYQ 技术总控、XXT 数学裁决、CYQ 技术事实只读边界；不把角色文件夹当作权限或独立 Skill。
- 新增动态论文框架：按问判断模型成熟度、保留已认可结构、提前规定图表与证据需求，不以润色替代模型修正。
- 扩充原逐问概述规则：可预告图表要回答的问题；论证功能不等于固定句数、标题或句式。
- 新增可完全不用的表达参考；候选强表达不等于已验证主张。
- 图表工作流补入算法先于效果、分指标对比、收益与代价、参数可比性，以及求解失败/子问题不可行/联合不可行的区分。
- Runtime manifest 纳入新增文件，检查角色导航和打包后的引用可达性；不更改比赛模型、结果、Gate 状态或角色 ID。
- 仍按非 main 分支、PR 和所需 Review 发布；本节不代表自动授权合并。

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
