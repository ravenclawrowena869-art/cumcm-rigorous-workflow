from pathlib import Path
import csv
import json
import subprocess
import sys
import tempfile
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
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for token in (
            "ACTIVE_ROLE",
            "FYQ_TECHNICAL_ORCHESTRATOR",
            "XXT_MATHEMATICAL",
            "CYQ_PAPER",
            "role-neutral read-only",
        ):
            self.assertIn(token, text)

    def test_shared_core_has_non_overridable_rule_ids(self):
        text = (SKILL_DIR / "core" / "SHARED_CORE.md").read_text(encoding="utf-8")
        for token in (
            "CORE-AUTH-001",
            "CORE-FREEZE-001",
            "CORE-EVIDENCE-001",
            "CORE-COLLAB-001",
        ):
            self.assertIn(token, text)

    def test_runtime_skill_contains_no_large_corpus_binary(self):
        forbidden = {".pdf", ".png", ".jpg", ".jpeg"}
        bad = [p for p in SKILL_DIR.rglob("*") if p.is_file() and p.suffix.lower() in forbidden]
        self.assertEqual(bad, [])

    def test_local_role_binding_is_ignored(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".cumcm-agent.local.yaml", text)
        self.assertIn("dist/", text)

    def test_project_state_has_three_agent_bindings(self):
        text = (ROOT / "templates" / "project_state模板.yaml").read_text(encoding="utf-8")
        for token in (
            "agent_bindings:",
            "FYQ_TECHNICAL_ORCHESTRATOR",
            "XXT_MATHEMATICAL",
            "CYQ_PAPER",
            "authoritative_handoff:",
            "evidence_gate_status:",
        ):
            self.assertIn(token, text)

    def test_paper_profile_blocks_unsupported_final_prose(self):
        text = (SKILL_DIR / "profiles" / "CYQ_PAPER.md").read_text(encoding="utf-8")
        self.assertIn("INCOMPLETE", text)
        self.assertIn("缺口清单", text)
        self.assertIn("可直接定稿", text)

    def test_paper_handoff_template_has_required_sections(self):
        text = (ROOT / "templates" / "Paper_Handoff模板.md").read_text(encoding="utf-8")
        for token in (
            "本问合同",
            "本问中心逻辑",
            "求解与伪代码包",
            "验证证据",
            "自然语言初稿",
            "正式来源",
            "论文禁区",
        ):
            self.assertIn(token, text)

    def test_ai_ledger_has_v21_fields(self):
        row = next(csv.reader([(ROOT / "templates" / "AI使用记录模板.csv").read_text(encoding="utf-8").strip()]))
        self.assertEqual(
            row,
            [
                "time",
                "tool_model",
                "stage",
                "prompt_summary",
                "ai_response_summary",
                "human_verification",
                "team_decision",
                "adopted",
                "human_changes",
                "paper_location",
                "artifact",
            ],
        )

    def test_gates_are_v21_and_include_new_checks(self):
        data = json.loads((ROOT / "templates" / "gates.json").read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "2.1")
        all_checks = {item for checks in data["gates"].values() for item in checks}
        for token in (
            "evidence_sufficiency_pass",
            "robustness_plan_resolved",
            "task_specific_algorithm_pass",
            "ai_use_ledger_checked",
            "pdf_layout_checked",
        ):
            self.assertIn(token, all_checks)

    def test_collaboration_governance_has_four_handoff_directions(self):
        text = (ROOT / "06_协作与交接" / "06_三GPT协作与Skill共同维护.md").read_text(encoding="utf-8")
        for token in ("FYQ GPT → XXT GPT", "XXT GPT → FYQ GPT", "FYQ / XXT GPT → CYQ GPT", "CYQ GPT → FYQ / XXT GPT"):
            self.assertIn(token, text)

    def test_runtime_builder_produces_lite_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runtime"
            build = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_runtime_skill.py"), str(target)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(build.returncode, 0, msg=build.stdout + build.stderr)
            for rel in (
                "SKILL.md",
                "skills/cumcm-rigorous-workflow/core/SHARED_CORE.md",
                "skills/cumcm-rigorous-workflow/profiles/FYQ_TECHNICAL_ORCHESTRATOR.md",
                "skills/cumcm-rigorous-workflow/profiles/XXT_MATHEMATICAL.md",
                "skills/cumcm-rigorous-workflow/profiles/CYQ_PAPER.md",
                "04_验收冻结/05_模型证据充分性Gate.md",
                "templates/Paper_Handoff模板.md",
            ):
                self.assertTrue((target / rel).exists(), rel)
            forbidden = {".pdf", ".png", ".jpg", ".jpeg"}
            bad = [p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in forbidden]
            self.assertEqual(bad, [])

            validate = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "validate_runtime_skill.py"), str(target)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, msg=validate.stdout + validate.stderr)


if __name__ == "__main__":
    unittest.main()
