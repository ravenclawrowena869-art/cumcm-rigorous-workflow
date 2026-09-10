from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MultiAgentValidationContractTests(unittest.TestCase):
    def test_dispatcher_routes_multi_agent_work(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for token in (
            "05_多Agent验证流水线与回流协议.md",
            "01_独立验收协议.md",
            "04_结果来源链.md",
            "流程继续不等于科学放行",
        ):
            self.assertIn(token, text)

    def test_model_selection_has_qualified_mini_tournament(self):
        text = (ROOT / "02_开赛与拆题" / "02_模型选择协议.md").read_text(encoding="utf-8")
        for token in (
            "MODEL-TOURNAMENT-001",
            "参赛前资格门",
            "baseline + 1–3 个真正相关候选",
            "不允许用最终测试集反复选模",
            "正式主模型仍需经过完整数据",
        ):
            self.assertIn(token, text)

    def test_redteam_is_information_isolated_and_never_soft_passes(self):
        text = (ROOT / "04_验收冻结" / "01_独立验收协议.md").read_text(encoding="utf-8")
        for token in (
            "REDTEAM-ISOLATION-001",
            "REDTEAM-DEFINITION-001",
            "REDTEAM-FROZEN-INPUT-001",
            "REDTEAM-FAIL-001",
            "主求解代码",
            "同声明口径复算",
            "独立口径挑战",
            "FAIL / REOPEN",
            "不能因为“自动流水线还要继续”而改成 PASS",
        ):
            self.assertIn(token, text)

    def test_execution_state_cannot_override_validation_state(self):
        text = (ROOT / "00_总览" / "03_状态机与冻结规则.md").read_text(encoding="utf-8")
        for token in (
            "STATE-SEPARATION-001",
            "execution_status",
            "validation_status",
            "CONTINUING",
            "FAIL_REOPEN",
            "不得进入 `FROZEN`",
            "STATE-CHECKPOINT-001",
            "source_commit",
            "input_manifest_hash",
        ):
            self.assertIn(token, text)

    def test_result_changes_propagate_to_all_consumers(self):
        text = (ROOT / "04_验收冻结" / "04_结果来源链.md").read_text(encoding="utf-8")
        for token in (
            "CHANGESET-001",
            "CHANGESET-STALE-001",
            "FROZEN-INPUT-001",
            "affected_questions",
            "affected_tables",
            "affected_figures",
            "affected_abstract_claims",
            "旧值残留检查",
        ):
            self.assertIn(token, text)

    def test_orchestration_protocol_keeps_science_gates_authoritative(self):
        text = (ROOT / "07_AI协作" / "05_多Agent验证流水线与回流协议.md").read_text(encoding="utf-8")
        for token in (
            "执行编排层",
            "ORCH-STATE-001",
            "ORCH-REDTEAM-001",
            "ORCH-TOURNAMENT-001",
            "ORCH-CHECKPOINT-001",
            "ORCH-CHANGESET-001",
            "ORCH-LEDGER-001",
            "ORCH-GUARD-001",
            "ORCH-DRYRUN-001",
            "ORCH-CONTRACT-001",
            "ORCH-NO-SOFTPASS-001",
            "红队不一致",
            "旧值残留",
            "不得自动 PASS",
        ):
            self.assertIn(token, text)

    def test_runtime_manifest_packages_new_protocols_and_templates(self):
        manifest = json.loads(
            (ROOT / "skills" / "cumcm-rigorous-workflow" / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], "2.2.0")
        required = {
            "00_总览/03_状态机与冻结规则.md",
            "02_开赛与拆题/02_模型选择协议.md",
            "04_验收冻结/01_独立验收协议.md",
            "04_验收冻结/04_结果来源链.md",
            "07_AI协作/05_多Agent验证流水线与回流协议.md",
            "templates/红队独立复算报告模板.md",
            "templates/结果换版影响清单模板.md",
        }
        self.assertTrue(required.issubset(set(manifest["canonical_sources"])))
        self.assertTrue(required.issubset(set(manifest["runtime_include"])))
        for rel in required:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_templates_keep_validation_and_change_propagation_explicit(self):
        redteam = (ROOT / "templates" / "红队独立复算报告模板.md").read_text(encoding="utf-8")
        changeset = (ROOT / "templates" / "结果换版影响清单模板.md").read_text(encoding="utf-8")
        for token in ("信息隔离声明", "同声明口径复算", "独立口径挑战", "FAIL / REOPEN"):
            self.assertIn(token, redteam)
        for token in ("换版基本信息", "影响传播", "旧值残留检查", "Paper Check"):
            self.assertIn(token, changeset)


if __name__ == "__main__":
    unittest.main()
