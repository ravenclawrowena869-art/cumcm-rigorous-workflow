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

    def test_shared_core_has_math_authority_and_freeze_prerequisite(self):
        text = (SKILL_DIR / "core" / "SHARED_CORE.md").read_text(encoding="utf-8")
        for token in (
            "CORE-AUTH-001",
            "CORE-MATH-AUTH-001",
            "CORE-FREEZE-001",
            "CORE-FREEZE-002",
            "CORE-DYNAMIC-001",
            "CORE-EVIDENCE-001",
            "CORE-COLLAB-001",
            "material surrogate fidelity",
            "G3_FREEZE",
            "G2_VALIDATION=PASS",
        ):
            self.assertIn(token, text)

    def test_xxt_profile_keeps_formal_veto(self):
        text = (SKILL_DIR / "profiles" / "XXT_MATHEMATICAL.md").read_text(encoding="utf-8")
        for token in (
            "Mathematical Veto",
            "P0 REOPEN",
            "目标函数",
            "hard constraint",
            "单位、量纲",
            "accounting",
            "surrogate / proxy",
            "全过程 replay",
            "仅适用于 authority 明确指定保留主线",
        ):
            self.assertIn(token, text)

    def test_fyq_cannot_bypass_mathematical_pass(self):
        text = (SKILL_DIR / "profiles" / "FYQ_TECHNICAL_ORCHESTRATOR.md").read_text(encoding="utf-8")
        for token in (
            "统一技术路线权",
            "mathematical_pass=true",
            "G2_VALIDATION=PASS",
            "旧 Mathematical PASS 失效",
        ):
            self.assertIn(token, text)

    def test_evidence_gate_requires_dynamic_replay_and_surrogate_p0(self):
        text = (ROOT / "04_验收冻结" / "05_模型证据充分性Gate.md").read_text(encoding="utf-8")
        for token in (
            "动态、状态空间与路径依赖模型",
            "只检查最终状态，不得 Mathematical PASS",
            "MATHEMATICAL_P0",
            "强 baseline 本身只能支持 COMPETITIVE",
            "不为形式完整机械增加大型 exact 求解",
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

    def test_project_state_has_three_agent_bindings_and_math_provenance(self):
        text = (ROOT / "templates" / "project_state模板.yaml").read_text(encoding="utf-8")
        for token in (
            "agent_bindings:",
            "FYQ_TECHNICAL_ORCHESTRATOR",
            "XXT_MATHEMATICAL",
            "CYQ_PAPER",
            "authoritative_handoff:",
            "evidence_gate_status:",
            "mathematical_review_status:",
            "mathematical_review_artifact:",
            "mathematical_review_commit:",
            "mathematical_veto_clear:",
            "dynamic_constraint_replay_status:",
            "surrogate_replay_status:",
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

    def test_gates_are_v21_and_freeze_depends_on_validation(self):
        data = json.loads((ROOT / "templates" / "gates.json").read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "2.1")
        self.assertEqual(data["gate_dependencies"]["G3_freeze"], ["G2_validation"])
        all_checks = {item for checks in data.get("gates", {}).values() for item in checks}
        for token in (
            "evidence_sufficiency_pass",
            "robustness_plan_resolved",
            "task_specific_algorithm_pass",
            "ai_use_ledger_checked",
            "pdf_layout_checked",
            "mathematical_veto_clear",
            "dynamic_constraints_full_replay_or_not_applicable",
            "surrogate_full_replay_or_not_applicable",
            "g2_validation_pass",
            "current_mathematical_review_matches_source_of_truth",
        ):
            self.assertIn(token, all_checks)

    def test_collaboration_governance_has_four_handoff_directions(self):
        text = (ROOT / "06_协作与交接" / "06_三GPT协作与Skill共同维护.md").read_text(encoding="utf-8")
        for token in ("FYQ GPT → XXT GPT", "XXT GPT → FYQ GPT", "FYQ / XXT GPT → CYQ GPT", "CYQ GPT → FYQ / XXT GPT"):
            self.assertIn(token, text)

    def test_runtime_manifest_includes_execution_routing_protocol(self):
        manifest = json.loads((SKILL_DIR / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "2.1.5")
        rel = "07_AI协作/05_执行资源路由协议.md"
        self.assertIn(rel, manifest["canonical_sources"])
        self.assertIn(rel, manifest["runtime_include"])

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
                "07_AI协作/05_执行资源路由协议.md",
                "templates/Paper_Handoff模板.md",
                "templates/任务单模板.md",
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
