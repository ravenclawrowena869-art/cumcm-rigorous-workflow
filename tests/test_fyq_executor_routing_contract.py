from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "skills" / "cumcm-rigorous-workflow" / "profiles" / "FYQ_TECHNICAL_ORCHESTRATOR.md"


class FYQExecutorRoutingContractTests(unittest.TestCase):
    def test_profile_routes_by_semantic_risk_not_model_brand(self):
        text = PROFILE.read_text(encoding="utf-8")
        for token in (
            "FYQ-EXECUTOR-ROUTING-001",
            "数学语义风险",
            "普通执行窗口 / Coding Agent",
            "XXT Mathematical Review",
            "立即停止工程继续执行",
        ):
            self.assertIn(token, text)

    def test_engineering_closeout_does_not_require_strongest_model(self):
        text = PROFILE.read_text(encoding="utf-8")
        self.assertIn("writer、validator、打包、图表或冻结规格下的工程实现", text)
        self.assertIn("不得机械要求使用最强模型", text)


if __name__ == "__main__":
    unittest.main()
