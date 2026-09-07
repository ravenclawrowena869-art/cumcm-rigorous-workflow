# 三 GPT 协作与 Skill 共同维护 v2.1

## 1. 单一正式源

FYQ、XXT、CYQ 三套 GPT 共用同一个 `cumcm-rigorous-workflow`。团队正式规则只认 GitHub main；个人聊天、临时 Prompt 和个人 ZIP 只能作为 Proposal。

## 2. 四类正式 Handoff

### FYQ GPT → XXT GPT：Mathematical Review Request

必须包含：
- 当前模块与版本；
- Source of Truth；
- 公式到实现的映射；
- 目标、约束、单位与关键参数；
- constraint audit；
- 候选结果与异常；
- 待数学裁决项；
- required Gate 与验收标准。

### XXT GPT → FYQ GPT：MODEL_SPEC / Mathematical Review

必须包含：
- 变量、参数、单位；
- 目标函数；
- hard constraints；
- 参数范围与来源；
- validator specification；
- exact anchor / bound / adequacy；
- 数学 Review 状态；
- 若 P0，给出最小重开理由。

### FYQ / XXT GPT → CYQ GPT：Paper Handoff

必须包含：
- 本问合同；
- 为什么选当前模型；
- 核心数学；
- 本题专属求解过程；
- baseline、稳定性、敏感性、鲁棒性；
- Frozen Metrics；
- Figure Registry；
- 正式来源；
- 论文禁区；
- 可供 CYQ 继续人工修改的自然中文初稿。

### CYQ GPT → FYQ / XXT GPT：Evidence Gap Return

必须包含：
- 缺实验/数字/图表；
- 发现的口径冲突；
- 摘要需要的正式指标；
- 缺失的伪代码步骤；
- 需要解释的异常、边界、不可行情景；
- consumer deadline / priority。

## 3. Branch 规范

推荐：

- `fyq/<topic>`
- `xxt/<topic>`
- `cyq/<topic>`
- `shared/<topic>`

任何人都可修改任何目录，但需遵守 Review Ownership。

## 4. Review Ownership

- Shared Core：至少一名其他角色 Review；
- 数学 Gate / MODEL_SPEC：XXT 主审，FYQ 复核实现接口；
- Freeze / interface / code / runtime builder：FYQ 主审；
- Paper / Figure / AI disclosure / prose：CYQ 主审；
- 跨角色 Handoff：输出方与消费方各审一次。

专项冻结任务中，如果 authority 明确只允许最小修复，Review 不能借机扩大范围。

## 5. PR 必填字段

每个 Skill / Workflow PR 至少写：

- Why
- Changed Rules
- Affected Profiles
- Behavior Change
- Backward Compatibility
- Evidence / Source
- Validation
- Migration Notes

如果规则来自比赛复盘、老师批注或评委反馈，应注明来源性质，避免把单次案例写成无条件全局规律。

## 6. Rule ID

重要共享规则使用稳定 ID，例如：

- `CORE-AUTH-001`
- `CORE-FREEZE-001`
- `MATH-OPT-001`
- `PAPER-PROSE-001`
- `AI-DISCLOSURE-001`

修改同一规则时更新原 Rule，不重复追加近义条目。

## 7. Canonical 与 Proposal

正式规则位于 canonical workflow、`skills/.../core` 与 `skills/.../profiles`。

实验性建议先放：

`proposals/<author>/<topic>.md`

通过 Review 后再进入正式规则。

## 8. 冲突处理

三套 GPT 发生结论冲突时，不以“谁的 GPT 更强”裁决。先回到 authority：

官方材料 → project_state → Frozen Source of Truth → canonical Gate → 当前 Task/Handoff。

数学冲突由 XXT 给 Mathematical Review，工程/版本冲突由 FYQ 统一集成，论文表达冲突由 CYQ 在不改变事实的前提下裁决。
