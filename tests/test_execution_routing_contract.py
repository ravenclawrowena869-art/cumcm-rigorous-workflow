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
        for token in (
            "CODEX_ASTRA",
            "CODEX_SOL",
            "GPT_EXECUTION",
            "代码标识符、路径、命令保持原文",
        ):
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
