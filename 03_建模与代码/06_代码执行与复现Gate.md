# 代码执行与复现 Gate v1.0

本 Gate 用于所有会产生正式数值、策略、预测、仿真轨迹、优化结果、图表数据或提交文件的代码任务。它把“代码能运行”升级为“模型—代码—数据—验证—导出可追溯且可复现”。

适用范围包括：Python / MATLAB / R / Julia / C++ 求解脚本，LP/MILP/CP-SAT/NLP solver，预测与仿真 runner，数据处理、结果导出、绘图脚本，以及由 ChatGPT、Codex、Claude Code 等 Agent 辅助执行的代码修改。

核心优先级：

```text
题意与数学口径正确
> hard constraints 可行
> 输入/时间边界正确
> 独立可复算
> clean replay 可复现
> 指标优化与运行速度
```

---

## CODE-EXEC-001 执行前先冻结 Execution Contract

任何正式运行前至少记录：

- `source_commit / code_version`；
- 输入文件、Sheet、字段、时间范围及 SHA256 / manifest；
- 配置文件与 materially relevant 参数；
- 随机种子或场景生成规则（适用时）；
- solver / package / Python 等关键依赖版本；
- 输出 schema、单位、粒度和官方模板映射；
- 本轮唯一实验目标；
- 允许修改范围与禁止修改范围；
- Required Gate 与停止条件。

如果上游 Frozen Input、模型口径或时间信息集尚未确定，允许开发 mock / runner，但不得生成“正式结果”。

---

## CODE-STRUCT-001 模型、验证器、导出和绘图分离

正式代码应尽量保持以下职责分离：

```text
load / prepare
→ model / solver
→ validator
→ export
→ plot
→ paper / submission consumer
```

`config` 独立保存会影响结果的参数。

要求：

- solver 不得把“自己求出来”当作“自己验证正确”；
- validator 应从冻结输出重新读取并复算关键公式；
- export 不得重新优化或偷偷改变指标口径；
- plot 只能消费正式输出或明确的 paper metrics，不得从旧缓存/聊天数字拼图；
- 提交模板写入后必须 readback，再独立复算关键总量。

若项目规模很小，可合并文件，但职责与数据流仍必须能够清楚区分。

---

## CODE-SMOKE-001 静态读代码不等于“能跑”

在正式大规模运行前必须实际执行代表性 smoke test。

至少检查：

1. 能从声明的入口读取真实或冻结样例输入；
2. 程序正常退出；
3. 输出行数 / shape / schema 正确；
4. 无 NaN / Inf / 非法类型；
5. 核心 hard constraint 与 accounting 可复算；
6. 时间索引、边界时段、单位没有错位；
7. 输出目录不会覆盖 Frozen Source of Truth。

只做静态代码审查，不得写 `RUNNABLE PASS`。

---

## CODE-SCALE-001 全量运行前做规模与预算检查

从小样升级到全量前记录：

- 样本 / 时段 / 场景 / 变量 / 整数变量 / 约束规模；
- 单次 pilot runtime；
- 粗略全量 runtime / memory 估计；
- solver 时限、MIP gap 或迭代上限；
- checkpoint / resume 策略（长任务适用）；
- 超预算时的停止规则。

若全量不可承受，必须返回明确 blocker，再通过有依据的降维、场景缩减、算法加速或等价变换处理。**不得为了跑完而静默修改数学模型、删约束、降低信息因果要求或更换指标口径。**

---

## CODE-TIME-001 时间、因果与数据边界必须逐项审计

只要涉及时间序列、滚动预测、在线决策、滚动优化或历史场景，必须显式检查：

- canonical timestamp / slot mapping；
- decision time；
- 训练与历史样本最大可用时间；
- `target_ts < / <= decision_time` 的正式规则；
- lag / rolling / expanding window 是否越界；
- 当天 actual、未来价格、未来需求等是否被提前读取；
- 训练 / 验证 / 最终评估是否存在时间泄漏。

边界点必须至少有一个人工可核查 case。只按“自然日”切片而不检查真实 timestamp，不得通过因果 Gate。

---

## CODE-VALIDATE-001 正式结果必须独立复算

正式结果至少完成：

- objective / loss / cost 独立重算；
- 2–3 个核心指标独立重算；
- hard constraints 全量或全过程 replay；
- 动态状态（SOC、库存、轨迹等）逐时检查 `max_violation` 与位置；
- solver status、runtime、gap / bound（适用时）；
- fallback / exception / infeasible / timeout 次数；
- 结果总行数、日期/对象覆盖范围和缺失情况。

独立验收继续服从 `04_验收冻结/01_独立验收协议.md`。头条数字优先采用信息隔离式红队复算；第二个 Agent 仅阅读主代码后认可，不等同于独立复算。

---

## CODE-OUTPUT-001 正式输出必须可直接消费

任何要交给下一问、论文、图表或官方模板的输出，必须声明：

- source file；
- 字段及单位；
- 行 / 列粒度；
- 日期 / 时段 / 场景范围；
- 版本 / hash；
- consumer；
- 缺失、fallback 与失败行为。

正式数字来源链必须满足：

```text
Official / Frozen Input
→ Frozen Code + Config
→ Frozen Output
→ Independently Recomputed Metrics
→ Figure / Table / Submission File
→ Paper Claim
```

禁止“聊天里的数字 → 论文”“截图里的数字 → 表格”“旧 CSV → 新图”。

---

## CODE-REPLAY-001 Freeze 前必须 clean replay

Freeze 前必须从干净目录执行一次真实复现：

1. 只放最终交付包 / 声明依赖；
2. 不访问原开发目录；
3. 从官方输入或 manifest 指定输入运行；
4. 删除缓存后仍能运行；
5. 重新生成最终输出；
6. 对关键输出比较 hash 或核心指标；
7. README / RUN 命令与实际一致。

不得依赖：绝对路径、旧 checkpoint、未声明 CSV、IDE 临时环境、聊天附件路径或开发机缓存。

详细规则见 `04_验收冻结/03_干净环境复现.md`。

---

## CODE-SEAL-001 Runtime / 交付包要有版本与文件封印

面向 Agent 的 Runtime Lite、冻结代码包或正式交付包应尽量记录：

- source commit / version；
- manifest SHA256；
- 关键文件 SHA256；
- 输入 provenance；
- build / generation command；
- 禁止进入运行包的大型 corpus / 二进制规则。

Runtime Lite 应是自包含的：dispatcher / AGENTS 中要求“必须读取”的运行时规则，必须真实存在于 Runtime；不能出现“规则要求读取，但打包时没带进去”的悬空引用。

---

## CODE-CHANGESET-001 改代码后主动检查影响传播

若代码、配置、输入、模型或 accounting 改变，先判断是否会影响：

- 旧 Mathematical PASS；
- baseline / challenger 排名；
- 下游接口；
- Frozen Output；
- paper metrics；
- Figure Registry；
- result*.xlsx / submission file；
- 摘要、表格和正文 Claim。

material change 必须执行 `04_验收冻结/04_结果来源链.md` 的换版影响清单和 stale-value check。不得只替换一个最终数字。

---

## CODE-NO-SOFTPASS-001 失败不能因为赶时间自动转正

以下任一项存在时，不得标记正式 PASS / Freeze：

- 输入来源或时间边界不明；
- hard constraint violation 未解释；
- validator 与 solver 共用同一错误实现且没有独立复算；
- clean replay 失败；
- 关键结果不可追溯；
- runtime / checkpoint 超时后改口径“凑出结果”；
- 输出模板无法 readback 或与原始结果不一致；
- 修改后旧 Gate 已失效但未重验。

允许任务状态为 `BLOCKED`、`FAIL / REOPEN` 或 `PASS WITH NON-MODEL PATCH`，不允许把工程进度伪装成科学完成。

---

## Gate 结论

只允许以下结论：

- `CODE EXECUTION PASS`：Execution Contract、smoke、正式运行、独立复算、输出追溯和 clean replay 全部满足；
- `PASS WITH NON-MODEL PATCH`：仅存在不改变模型、结果口径和正式数字的工程补丁，补丁后已重跑必要验证；
- `FAIL / REOPEN`：输入、模型实现、约束、因果、结果、复现或来源链存在实质问题；
- `BLOCKED`：缺上游 Frozen Input / 环境 / solver / 关键规则，不能继续产生正式结果。

`CODE EXECUTION PASS` 不能替代 Mathematical PASS、Evidence Gate 或 Paper PASS；它只证明当前代码执行链可追溯、可复算、可复现。
