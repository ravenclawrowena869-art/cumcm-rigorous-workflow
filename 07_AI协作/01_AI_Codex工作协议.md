# AI / Codex 工作协议 v2.2

AI 最适合：
- 代码生成；
- 小范围修补；
- 测试补充；
- 独立审查；
- 文献初筛；
- 结果解释；
- 论文润色；
- 图表脚本；
- 打包与复现检查。

AI 最危险的地方：
- 自行改变题意；
- 为了“更好”改指标口径；
- 在旧版本继续叠补丁；
- 编造尚未运行的结果；
- 用错误数据源画出“很漂亮”的图；
- 把模型思考过程写成 AI 味正文。

## 1. 三档执行资源

### `CODEX_ASTRA`

用于核心算法、正式数学路径、复杂状态机、多模块耦合和高风险 P0 修复。典型包括 LP/MILP/CP-SAT、复杂 scheduler/controller、exact anchor、surrogate/full-model、多路径 fixed/adaptive controller 等首次或实质性实现。

通常标记 `REQUIRED` 或 `PREFERRED`。

### `CODEX_SOL`

用于数学定义和接口已经冻结后的工程实现，包括 data loader、runner、sweep harness、validator、tests、provenance、path fix、CLI、batch runner、日志和导出。

通常标记 `SUFFICIENT`。

### `GPT_EXECUTION`

用于不需要长期修改真实代码仓库的读取、运行、复算、审查、统计、Handoff、Figure Registry、文献初筛、打包和下一 Wave 任务书生成。

通常标记 `SUFFICIENT`。

详细判定、升级和降级见：

`07_AI协作/05_执行资源路由协议.md`

## 2. 每次给 AI 的指令至少包含

1. 背景；
2. 输入文件；
3. 明确目标；
4. 允许修改范围；
5. 禁止修改项；
6. 验收标准；
7. 输出格式；
8. 测试；
9. 风险；
10. 回滚；
11. 执行资源路由；
12. 任务语言。

正式 Task / Prompt 顶部必须写：

```text
【执行资源路由】
推荐执行器：CODEX_ASTRA / CODEX_SOL / GPT_EXECUTION
执行级别：REQUIRED / PREFERRED / SUFFICIENT
选择原因：……
是否允许降级：YES / NO
降级条件：……
升级触发：……

【任务语言】
中文；代码标识符、路径、命令保持原文。
```

## 3. 推荐流程

```text
先分析
  ↓
列问题
  ↓
冻结执行资源路由
  ↓
提出最小修改方案
  ↓
修改
  ↓
测试
  ↓
复算
  ↓
列风险
  ↓
决定是否接受
```

不要直接说“帮我修好”。

## 4. 升级与 failover

出现 objective / hard constraint / unit / accounting 风险、solver 与 independent recomputation 矛盾、material surrogate 风险、无法解释的动态 violation、跨核心模块修改、两轮 minimal fix 仍未解决根因等情况时，标记：

`EXECUTION_ESCALATION = CODEX_ASTRA`

如果 `ASTRA_REQUIRED` 但 Astra 临时不可用，先尝试等待；无法等待时，把任务拆成更小 Frozen Blocks，再由 Sol 逐 Block 实现，并强制 TDD、independent replay 与 XXT Review。

任何降级都不得降低 Mathematical Gate、Evidence Gate 或 Freeze 条件。

## 5. 权限边界

Astra、Sol、GPT execution 都只是执行资源。它们不能因为性能更强而取得 FYQ / XXT / CYQ 之外的角色权限，也不能替代官方 Authority、Frozen Source of Truth、XXT Mathematical Review 或 FYQ Freeze 管理。
