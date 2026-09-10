from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = ROOT / "SKILL.md"
PROTOCOL = ROOT / "00_总览" / "05_赛时加速与流程保真协议.md"
QUICK_REDLINE = ROOT / "00_总览" / "06_正赛技术红线速查.md"
MANIFEST = ROOT / "skills" / "cumcm-rigorous-workflow" / "manifest.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TimePressureEvidenceIntegrityContractTests(unittest.TestCase):
    def test_time_pressure_protocol_is_runtime_reachable(self):
        self.assertTrue(PROTOCOL.exists())
        dispatcher = read(DISPATCHER)
        self.assertIn("05_赛时加速与流程保真协议.md", dispatcher)
        self.assertIn("加速", dispatcher)
        self.assertTrue("赶时间" in dispatcher or "时间压力" in dispatcher)

        manifest = json.loads(read(MANIFEST))
        rel = "00_总览/05_赛时加速与流程保真协议.md"
        self.assertIn(rel, manifest["canonical_sources"])
        self.assertIn(rel, manifest["runtime_include"])

    def test_acceleration_never_waives_mandatory_evidence(self):
        protocol = read(PROTOCOL)
        for token in [
            "时间压力",
            "数据横向比较",
            "参数证据",
            "hard constraint",
            "independent recomputation",
            "Mathematical Review",
            "Evidence Gate",
            "Freeze",
        ]:
            self.assertIn(token, protocol)

        self.assertIn("加速只能改变", protocol)
        self.assertIn("不得降低", protocol)
        self.assertIn("降低 Claim", protocol)
        self.assertIn("MISSING_EVIDENCE", protocol)

    def test_representative_value_cannot_be_selected_casually_under_deadline(self):
        protocol = read(PROTOCOL)
        for token in [
            "代表值",
            "候选总体",
            "横向",
            "异常值",
            "选择规则",
            "合理替代值",
            "正式模型",
            "论文",
        ]:
            self.assertIn(token, protocol)

        self.assertIn("时间有限", protocol)
        self.assertIn("不得", protocol)

    def test_competition_redline_quick_reference_is_runtime_reachable(self):
        self.assertTrue(QUICK_REDLINE.exists())
        dispatcher = read(DISPATCHER)
        self.assertIn("06_正赛技术红线速查.md", dispatcher)
        for trigger in ["新 Question", "路线冻结", "正式结果验收", "Paper Handoff"]:
            self.assertIn(trigger, dispatcher)

        manifest = json.loads(read(MANIFEST))
        rel = "00_总览/06_正赛技术红线速查.md"
        self.assertIn(rel, manifest["canonical_sources"])
        self.assertIn(rel, manifest["runtime_include"])

    def test_competition_redline_quick_reference_covers_cross_problem_failure_modes(self):
        quick = read(QUICK_REDLINE)
        for token in [
            "预测模型",
            "预测区间",
            "顺序敏感",
            "exact anchor",
            "动态约束",
            "参数证据",
            "surrogate",
            "不可行",
            "Mathematical Review",
            "Evidence Gate",
        ]:
            self.assertIn(token, quick)

        self.assertIn("03_建模与代码/05_参数选择协议.md", quick)
        self.assertIn("04_验收冻结/05_模型证据充分性Gate.md", quick)
        self.assertIn("不得替代", quick)

    def test_competition_redline_quick_reference_does_not_hardcode_training_case_values(self):
        quick = read(QUICK_REDLINE)
        for forbidden in [
            "rho=0.20",
            "rho = 0.20",
            "RegionA",
            "RollingMean-336",
            "150-task",
            "72h",
        ]:
            self.assertNotIn(forbidden, quick)


if __name__ == "__main__":
    unittest.main()
