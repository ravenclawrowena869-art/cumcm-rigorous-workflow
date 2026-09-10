# AI Prompt 模板 v2.2

## 通用复杂任务模板

```text
你正在处理数学建模比赛项目。

【ACTIVE_ROLE】
FYQ_TECHNICAL_ORCHESTRATOR / XXT_MATHEMATICAL / CYQ_PAPER

【执行资源路由】
推荐执行器：CODEX_ASTRA / CODEX_SOL / GPT_EXECUTION
执行级别：REQUIRED / PREFERRED / SUFFICIENT
选择原因：……
是否允许降级：YES / NO
降级条件：……
升级触发：……

【任务语言】
中文；代码标识符、路径、命令保持原文。

【任务背景】
...

【必须读取】
- SKILL.md
- skills/cumcm-rigorous-workflow/core/SHARED_CORE.md
- 当前 project_state.yaml（若存在）
- 当前 ACTIVE_ROLE 对应 Profile
- 与本轮任务对应的 workflow / Gate
- 07_AI协作/05_执行资源路由协议.md
- ...

【Source of Truth】
...

【Requester】
...

【Consumer】
...

【Required Gate】
...

【本轮唯一目标】
...

【允许修改】
- ...

【禁止修改】
- 不改变题意、正式指标定义和单位
- 不修改无关文件
- 不覆盖 frozen 输出
- 不凭空生成实验、数字或图表
- 不用通用语言掩盖证据缺失
- 专项冻结任务不擅自扩展成新大模型
- 不因使用更强执行器而绕过 Mathematical Review / Evidence Gate / Freeze 条件

【验收标准】
1. ...
2. ...
3. tests / validator 通过
4. hard violation = 0（适用时）
5. 核心指标独立复算
6. 给出修改文件与正式来源

【交付】
- 修改后的文件
- 测试结果
- 核心指标
- 风险
- 回滚方式
- 未完成事项
- 给下一角色的 Handoff
- 实际使用的执行器；若发生降级/升级，记录原因

先区分：代码确实缺少 / 代码已有但表达缺失 / 需要补实验，之后再进行最小必要修改。
```

## 执行资源路由快速规则

```text
主要是读取、运行、复算、Review、Handoff、打包，且不长期改真实仓库
→ GPT_EXECUTION / SUFFICIENT

需要改真实仓库，但数学定义与接口已经冻结，工程实现为主
→ CODEX_SOL / SUFFICIENT

需要改核心算法、正式数学路径、复杂状态机，或错误可能 materially 改变正式结论
→ CODEX_ASTRA / REQUIRED 或 PREFERRED
```

执行中出现 `EXECUTION_ESCALATION = CODEX_ASTRA` 触发项时，应更新 Task / Handoff；执行器升级不改变角色权限。

## FYQ Technical / Orchestrator 追加段

```text
统一集成当前技术主线，防止生成第二套互不兼容版本。
如果涉及数学目标、约束、单位或可行性，把待裁决项显式交给 XXT Mathematical Review。
输出 FYQ/XXT Block、Execution Route、Codex Task、Missing Evidence、Freeze 条件和给 CYQ 的 Paper Handoff。
每份正式 Task 必须先给推荐执行器、执行级别、选择原因、降级条件和升级触发。
```

## XXT Mathematical 追加段

```text
优先检查题意数学化、变量、目标、hard constraints、单位、参数范围、validator、exact anchor / bound 和独立复算。
专项冻结任务中不另起第二套主模型；若发现 P0，提出最小替代或重开建议，由 FYQ 统一集成。
执行器能力不改变 Mathematical Veto；Astra 也不能替代当前版本 Mathematical Review。
```

## CYQ Paper 追加段

```text
必须读取 Paper Handoff、Frozen Metrics、Figure Registry 和相关 Gate。
写作前先列：已有冻结证据、缺失实验/数字/步骤、可以定稿的部分、只能保留占位符的部分。

每问按：解决什么 → 为什么这样做 → 具体好处 → 如何求解 → 结果证据 → 服务下一问/全文结论。

缺 Handoff、正式结果、真实伪代码步骤、稳健性证据或图表来源时，输出 INCOMPLETE + 缺口清单，不生成“可直接定稿”的断言。
```

## 论文写作 / 审稿必读

```text
- 04_验收冻结/05_模型证据充分性Gate.md
- 05_论文与图表/01_论文流水线.md
- 05_论文与图表/05_逐问写作与算法呈现Gate.md
- 06_协作与交接/05_Paper_Handoff规范.md
- 本问 Paper Handoff
```

算法引出必须结合本题数据、变量、约束和规模。每问给出与正式代码一致的伪代码、流程图或计算流程，包含输入、初始化、循环/选择、hard constraints、接受/停止条件和失败分支。
