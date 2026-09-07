from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "cumcm-rigorous-workflow"


class RuntimeSkillContractTests(unittest.TestCase):
    def test_three_role_profiles_exist(self):
        expected = {
            "FYQ_TECHNICAL_ORCHESTRATOR.md",
            "XXT_MATHEMATICAL.md",
            "CYQ_PAPER.md",
        }
        profile_dir = SKILL_DIR / "profiles"
        actual = {p.name for p in profile_dir.glob("*.md")} if profile_dir.exists() else set()
        self.assertEqual(actual, expected)

    def test_dispatcher_mentions_all_roles_and_active_role(self):
        path = ROOT / "SKILL.md"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for token in (
            "ACTIVE_ROLE",
            "FYQ_TECHNICAL_ORCHESTRATOR",
            "XXT_MATHEMATICAL",
            "CYQ_PAPER",
        ):
            self.assertIn(token, text)

    def test_runtime_skill_contains_no_large_corpus_binary(self):
        forbidden = {".pdf", ".png", ".jpg", ".jpeg"}
        bad = [p for p in SKILL_DIR.rglob("*") if p.is_file() and p.suffix.lower() in forbidden] if SKILL_DIR.exists() else []
        self.assertEqual(bad, [])

    def test_local_role_binding_is_ignored(self):
        path = ROOT / ".gitignore"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        self.assertIn(".cumcm-agent.local.yaml", text)

    def test_project_state_has_three_agent_bindings(self):
        path = ROOT / "templates" / "project_state模板.yaml"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for token in ("agent_bindings:", "FYQ_TECHNICAL_ORCHESTRATOR", "XXT_MATHEMATICAL", "CYQ_PAPER"):
            self.assertIn(token, text)

    def test_paper_profile_blocks_unsupported_final_prose(self):
        path = SKILL_DIR / "profiles" / "CYQ_PAPER.md"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        self.assertIn("INCOMPLETE", text)
        self.assertIn("缺口清单", text)
        self.assertIn("可直接定稿", text)


if __name__ == "__main__":
    unittest.main()
