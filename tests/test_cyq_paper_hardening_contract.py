from pathlib import Path
import csv
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "cumcm-rigorous-workflow"


class CyqPaperHardeningContractTests(unittest.TestCase):
    def test_cyq_technical_facts_are_read_only(self):
        text = (SKILL_DIR / "profiles" / "CYQ_PAPER.md").read_text(encoding="utf-8")
        for token in (
            "技术事实只读",
            "不得自行修改",
            "数学模型",
            "正式数字",
            "冻结参数",
            "单位",
            "技术口径",
            "reopen request",
        ):
            self.assertIn(token, text)

    def test_paper_handoff_is_self_describing_for_paper_lead(self):
        text = (ROOT / "templates" / "Paper_Handoff模板.md").read_text(encoding="utf-8")
        for token in (
            "关键参数",
            "参数来源",
            "为什么选",
            "扫描区间",
            "稳定区间",
            "迭代与收敛事实",
            "每轮关键指标",
            "接受/拒绝原因",
            "不同场景收敛差异",
            "核心指标语义",
            "定义/计算式",
            "统计范围",
            "好坏方向",
            "正式值",
        ):
            self.assertIn(token, text)

    def test_figure_registry_has_window_provenance(self):
        header = next(csv.reader([(ROOT / "templates" / "Figure_Registry模板.csv").read_text(encoding="utf-8").strip()]))
        for field in ("type", "time_scope", "window_rule", "selection_reason"):
            self.assertIn(field, header)

    def test_ai_disclosure_is_blocking_gate(self):
        core = (SKILL_DIR / "core" / "SHARED_CORE.md").read_text(encoding="utf-8")
        for token in (
            "CORE-AI-DISCLOSURE-001",
            "adopted=yes",
            "human_verification",
            "team_decision",
            "human_changes",
            "paper_location",
            "artifact",
            "Gate FAIL",
        ):
            self.assertIn(token, core)

        gates = json.loads((ROOT / "templates" / "gates.json").read_text(encoding="utf-8"))
        all_checks = {item for checks in gates.get("gates", {}).values() for item in checks}
        self.assertIn("ai_disclosure_gate_pass", all_checks)


if __name__ == "__main__":
    unittest.main()
