from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "cumcm-rigorous-workflow"


class PerTurnSkillInvocationContractTests(unittest.TestCase):
    def test_dispatcher_requires_per_turn_skill_invocation(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for token in (
            "每次回答前",
            "先调用一次本 Skill",
            "ACTIVE_ROLE",
            "Shared Core",
        ):
            self.assertIn(token, text)

    def test_shared_core_has_per_turn_invocation_rule(self):
        text = (SKILL_DIR / "core" / "SHARED_CORE.md").read_text(encoding="utf-8")
        for token in (
            "CORE-INVOKE-001",
            "每次回答前",
            "先调用一次本 Skill",
            "不得以已在上一轮读取过为由跳过",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
