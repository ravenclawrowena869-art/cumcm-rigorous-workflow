# Execution Routing & Chinese Taskbooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `CODEX_ASTRA / CODEX_SOL / GPT_EXECUTION` 三档执行资源路由和中文任务书约束固化进 `cumcm-rigorous-workflow` v2.1.5，并让 Runtime Lite、Prompt、任务模板和 FYQ 分发行为同时受 contract tests 约束。

**Architecture:** 采用“Shared Core 只放硬不变量、独立协议承载完整判定矩阵、FYQ Profile 负责分发、Prompt/Task 模板负责结构落地、manifest/validator 负责 Runtime Lite 约束”的分层方案。执行器是可替换资源，不改变 FYQ/XXT/CYQ 权限；任务语言规则只约束面向团队的人类可读正文，代码标识符保持原文。

**Tech Stack:** Markdown Skill/Workflow 文档、Python `unittest` contract tests、JSON Runtime manifest、GitHub Actions、Python 3.12。

**Spec:** `docs/superpowers/specs/2026-09-10-execution-routing-and-zh-taskbooks-design.md`

## Global Constraints

- 目标版本：`v2.1.5`。
- 正式 Task / Prompt 必须包含：`推荐执行器 / 执行级别 / 选择原因 / 是否允许降级 / 降级条件 / 升级触发 / 任务语言`。
- 执行器只允许：`CODEX_ASTRA / CODEX_SOL / GPT_EXECUTION`。
- 执行级别只允许：`REQUIRED / PREFERRED / SUFFICIENT`。
- 面向 FYQ / XXT / CYQ 的 Task、Authority 摘要、Handoff、Controller routing、Missing Evidence 默认使用简体中文。
- 文件名、路径、branch、commit、SHA、class/function/variable/enum/status code、命令、schema 字段、测试名保持原始英文。
- Astra 是高风险实现资源，不取得 Mathematical Veto、Freeze、Source of Truth 或角色权限。
- `ASTRA_REQUIRED` 不可用时允许 Block 化降级到 Sol，但 TDD、independent replay、XXT Review 与 Evidence Gate 不得降低。
- GitHub main 仍是唯一正式 Skill Source of Truth；本分支在 PR merge 前只是 proposed v2.1.5。

---

### Task 1: 建立 RED contract tests

**Files:**
- Create: `tests/test_execution_routing_contract.py`
- Modify: `tests/test_runtime_skill_contract.py`

**Interfaces:**
- Consumes: 现有 canonical 文档路径和 Runtime manifest。
- Produces: 对 v2.1.5 执行路由、中文任务书、Runtime Lite include/version 的静态 contract。

- [ ] **Step 1: 新建失败测试，锁定三档路由、中文 Task 结构和降级规则**

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExecutionRoutingContractTests(unittest.TestCase):
    def test_shared_core_has_execution_routing_invariants(self):
        text = (ROOT / "skills/cumcm-rigorous-workflow/core/SHARED_CORE.md").read_text(encoding="utf-8")
        for token in (
            "CORE-EXEC-ROUTING-001",
            "CORE-TASK-LANG-001",
            "CODEX_ASTRA",
            "CODEX_SOL",
            "GPT_EXECUTION",
            "执行器不改变角色权限",
        ):
            self.assertIn(token, text)

    def test_execution_routing_protocol_has_three_tiers_and_escalation(self):
        text = (ROOT / "07_AI协作/05_执行资源路由协议.md").read_text(encoding="utf-8")
        for token in (
            "CODEX_ASTRA",
            "CODEX_SOL",
            "GPT_EXECUTION",
            "REQUIRED",
            "PREFERRED",
            "SUFFICIENT",
            "EXECUTION_ESCALATION = CODEX_ASTRA",
            "连续两轮 minimal fix",
            "ASTRA_REQUIRED",
            "不得降低 Evidence Gate",
        ):
            self.assertIn(token, text)

    def test_task_template_has_required_route_fields_and_zh_rule(self):
        text = (ROOT / "templates/任务单模板.md").read_text(encoding="utf-8")
        for token in (
            "【执行资源路由】",
            "推荐执行器：",
            "执行级别：",
            "选择原因：",
            "是否允许降级：",
            "降级条件：",
            "升级触发：",
            "【任务语言】",
            "中文",
        ):
            self.assertIn(token, text)

    def test_prompt_template_routes_before_task_body(self):
        text = (ROOT / "07_AI协作/02_AI_Prompt模板.md").read_text(encoding="utf-8")
        route_pos = text.index("【执行资源路由】")
        goal_pos = text.index("【本轮唯一目标】")
        self.assertLess(route_pos, goal_pos)
        for token in ("CODEX_ASTRA", "CODEX_SOL", "GPT_EXECUTION", "代码标识符、路径、命令保持原文"):
            self.assertIn(token, text)

    def test_fyq_profile_must_emit_execution_route(self):
        text = (ROOT / "skills/cumcm-rigorous-workflow/profiles/FYQ_TECHNICAL_ORCHESTRATOR.md").read_text(encoding="utf-8")
        for token in ("执行资源路由", "推荐执行器", "执行级别", "降级条件", "升级触发"):
            self.assertIn(token, text)

    def test_astra_is_resource_not_authority(self):
        text = (ROOT / "07_AI协作/04_平台无关Skill与Agent切换.md").read_text(encoding="utf-8")
        for token in ("能力档是资源，不是角色", "CODEX_ASTRA", "不改变 FYQ / XXT / CYQ", "Mathematical Gate"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 扩展 Runtime contract，要求 v2.1.5 manifest 与新协议进入 Runtime Lite**

在 `tests/test_runtime_skill_contract.py` 中加入：

```python
def test_runtime_manifest_includes_execution_routing_protocol(self):
    manifest = json.loads((SKILL_DIR / "manifest.json").read_text(encoding="utf-8"))
    self.assertEqual(manifest["version"], "2.1.5")
    rel = "07_AI协作/05_执行资源路由协议.md"
    self.assertIn(rel, manifest["canonical_sources"])
    self.assertIn(rel, manifest["runtime_include"])
```

并在 runtime build smoke 的 `for rel in (...)` 中增加：

```python
"07_AI协作/05_执行资源路由协议.md",
"templates/任务单模板.md",
```

- [ ] **Step 3: 提交 RED 测试，不修改生产文档**

```bash
git add tests/test_execution_routing_contract.py tests/test_runtime_skill_contract.py
git commit -m "test: define execution routing and Chinese taskbook contract"
```

- [ ] **Step 4: 在 Draft PR 上运行 CI 并确认 RED 原因正确**

Run: GitHub Actions `validate-runtime-skill`

Expected: FAIL，至少因为以下缺失而失败：
- `07_AI协作/05_执行资源路由协议.md` 不存在；
- Task/Prompt 缺执行路由字段；
- manifest version 仍为 `2.1.4`；
- FYQ Profile 未强制 execution route。

不得把语法错误、import error 或无关旧测试失败当作有效 RED。

---

### Task 2: 实现 canonical 执行资源路由与中文任务书规则

**Files:**
- Modify: `SKILL.md`
- Modify: `skills/cumcm-rigorous-workflow/core/SHARED_CORE.md`
- Modify: `skills/cumcm-rigorous-workflow/profiles/FYQ_TECHNICAL_ORCHESTRATOR.md`
- Modify: `07_AI协作/01_AI_Codex工作协议.md`
- Modify: `07_AI协作/02_AI_Prompt模板.md`
- Modify: `07_AI协作/04_平台无关Skill与Agent切换.md`
- Create: `07_AI协作/05_执行资源路由协议.md`
- Modify: `templates/任务单模板.md`

**Interfaces:**
- Consumes: v2.1.5 approved spec。
- Produces: 全仓库唯一的 execution route vocabulary 与 Task 结构。

- [ ] **Step 1: 在 Shared Core 写最小硬不变量**

新增两节，内容必须表达：

```markdown
## CORE-EXEC-ROUTING-001 执行资源必须显式路由
正式 Task / Prompt 必须写明推荐执行器、执行级别、理由、降级与升级条件。
执行器只改变执行资源，不改变角色、Authority、Source of Truth、Mathematical Gate、Evidence Gate 或 Freeze 条件。
完整判定见 `07_AI协作/05_执行资源路由协议.md`。

## CORE-TASK-LANG-001 团队任务书默认中文
面向团队成员的 Task / Authority 摘要 / Handoff / Controller routing / Missing Evidence 默认简体中文；代码标识符、路径、命令、schema、Git/SHA/status code 保持原文。
```

- [ ] **Step 2: 新建完整执行资源路由协议**

`07_AI协作/05_执行资源路由协议.md` 至少包含：
- 三档定义和典型任务矩阵；
- 风险驱动决策树；
- Astra `REQUIRED/PREFERRED` 规则；
- Sol `SUFFICIENT` 规则；
- GPT execution `SUFFICIENT` 规则；
- `EXECUTION_ESCALATION = CODEX_ASTRA` 的全部触发项；
- Astra 不可用的 Block 化降级；
- 资源不改变角色权限；
- 任务书中文规范；
- 比赛时 30 秒快速路由检查表。

- [ ] **Step 3: 把路由写入 Dispatcher 与 FYQ Profile**

`SKILL.md` 必须告诉调用者：生成正式 Task / Prompt 时加载 `07_AI协作/05_执行资源路由协议.md`。

FYQ Profile 必须新增固定输出字段：

```text
【执行资源路由】
推荐执行器：...
执行级别：...
选择原因：...
是否允许降级：...
降级条件：...
升级触发：...
```

- [ ] **Step 4: 升级 AI/Codex 协议与平台切换协议**

`01_AI_Codex工作协议.md` 将现有“AI 最适合”扩展为三档资源使用边界，并明确核心数学实现优先 Astra、冻结规格工程实现用 Sol、读取/复算/Review 用 GPT execution。

`04_平台无关Skill与Agent切换.md` 新增“能力档是资源，不是角色”，并固定 Astra unavailable 的 failover。

- [ ] **Step 5: 升级 Prompt 与任务单模板**

`02_AI_Prompt模板.md` 的通用复杂任务模板在 `【ACTIVE_ROLE】` 后、任务正文前加入执行资源路由与任务语言段。

`templates/任务单模板.md` 顶部加入同样字段。

默认中文规则写成正向结构要求，不用模糊的“尽量中文”。

- [ ] **Step 6: 运行新增 contract tests**

Run:

```bash
python -m unittest tests.test_execution_routing_contract -v
```

Expected: PASS。

- [ ] **Step 7: 提交 canonical docs 实现**

```bash
git add SKILL.md skills/cumcm-rigorous-workflow/core/SHARED_CORE.md \
  skills/cumcm-rigorous-workflow/profiles/FYQ_TECHNICAL_ORCHESTRATOR.md \
  07_AI协作/01_AI_Codex工作协议.md 07_AI协作/02_AI_Prompt模板.md \
  07_AI协作/04_平台无关Skill与Agent切换.md 07_AI协作/05_执行资源路由协议.md \
  templates/任务单模板.md
git commit -m "feat: add execution resource routing and Chinese taskbooks"
```

---

### Task 3: Runtime Lite 与 validator 升级到 v2.1.5

**Files:**
- Modify: `skills/cumcm-rigorous-workflow/manifest.json`
- Modify: `tools/validate_runtime_skill.py`
- Test: `tests/test_runtime_skill_contract.py`

**Interfaces:**
- Consumes: Task 2 新增协议和模板字段。
- Produces: canonical/runtime-built 两种模式下都可强制验证 execution routing。

- [ ] **Step 1: 将 manifest 版本升到 2.1.5 并加入协议**

在 `canonical_sources` 和 `runtime_include` 都加入：

```json
"07_AI协作/05_执行资源路由协议.md"
```

确保 `templates/任务单模板.md` 仍在 runtime include。

- [ ] **Step 2: 更新 validator 的版本与关键 token**

`tools/validate_runtime_skill.py`：
- manifest version expected：`2.1.5`；
- dispatcher 必须含 `执行资源路由`；
- Shared Core 必须含 `CORE-EXEC-ROUTING-001` 与 `CORE-TASK-LANG-001`；
- FYQ Profile 必须含 `推荐执行器 / 执行级别 / 降级条件 / 升级触发`；
- 新协议必须含三档执行器和 `ASTRA_REQUIRED` failover；
- Task/Prompt 模板必须含七个路由/语言字段。

- [ ] **Step 3: 运行 canonical validator**

```bash
python tools/validate_runtime_skill.py
```

Expected: `PASS: runtime skill contract`。

- [ ] **Step 4: 运行全部 unit contract tests**

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: 全部 PASS。

- [ ] **Step 5: 构建并验证 Runtime Lite**

```bash
python tools/build_runtime_skill.py
python tools/validate_runtime_skill.py dist/cumcm-rigorous-workflow-runtime-lite
```

Expected: build success + runtime validation PASS。

- [ ] **Step 6: 提交 Runtime 约束升级**

```bash
git add skills/cumcm-rigorous-workflow/manifest.json tools/validate_runtime_skill.py tests/test_runtime_skill_contract.py
git commit -m "chore: validate execution routing in runtime lite"
```

---

### Task 4: Pressure examples、全文一致性与最终验证

**Files:**
- Modify if needed: `07_AI协作/05_执行资源路由协议.md`
- Modify if needed: `07_AI协作/02_AI_Prompt模板.md`
- Modify if needed: `templates/任务单模板.md`
- No new production subsystem.

**Interfaces:**
- Consumes: 完整 v2.1.5 proposed branch。
- Produces: 可交独立角色 Review 的 PR。

- [ ] **Step 1: 用六个设计 pressure cases 人工核对路由结果**

Expected matrix：

```text
复杂 MILP / controller 首次实现            → CODEX_ASTRA / REQUIRED or PREFERRED
CSV runner / path portability fix          → CODEX_SOL / SUFFICIENT
ZIP integrity / independent review         → GPT_EXECUTION / SUFFICIENT
Sol 中发现 hard-constraint 风险            → EXECUTION_ESCALATION = CODEX_ASTRA
正式团队 Task                              → 中文正文 + 英文代码标识符
ASTRA_REQUIRED 但 Astra unavailable        → Block 化 Sol fallback + Gate 不降低
```

- [ ] **Step 2: 检查无 authority 漂移**

确认任何新增文档都没有写出：
- Astra 可以替代 XXT Mathematical Review；
- Astra 可自动 Freeze；
- Sol/GPT 因资源低档而降低测试；
- 所有任务默认 Astra；
- 自动消耗高性能额度却不在 Task 中提示。

- [ ] **Step 3: 最终 CI 验证**

Run through PR GitHub Actions：
- Unit contract tests；
- canonical validator；
- Runtime Lite build；
- built Runtime Lite validator；
- forbidden binary scan。

Expected: all green。

- [ ] **Step 4: 更新 PR 描述并请求跨角色 Review**

PR body 必须写明：
- RED evidence；
- GREEN evidence；
- 三档路由定义；
- 中文任务书硬规则；
- Astra unavailable fallback；
- Shared Core 改动需要至少一名 XXT/CYQ 独立 Review；
- merge 前不得宣称 v2.1.5 已成为团队正式规则。

---

## Self-Review

- Spec coverage：执行器三档、级别、理由、降级、升级、中文正文、Astra failover、角色边界、Runtime Lite、tests 全部有对应 Task。
- Placeholder scan：无 `TBD/TODO/implement later`。
- Interface consistency：全计划统一使用 `CODEX_ASTRA / CODEX_SOL / GPT_EXECUTION` 与 `REQUIRED / PREFERRED / SUFFICIENT`；所有 Task 结构字段与设计一致。
- Scope：只修改 Skill/Prompt/Task/Runtime contract，不改变当前数模题目的模型、Q4/Three-Point Source of Truth 或比赛实验。
