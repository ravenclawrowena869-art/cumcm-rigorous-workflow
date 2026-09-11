from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "cumcm-rigorous-workflow"


class ParallelFirstWaveTaskContractTests(unittest.TestCase):
    def test_shared_core_requires_three_parallel_taskbooks(self):
        text = (SKILL_DIR / "core" / "SHARED_CORE.md").read_text(encoding="utf-8")
        for token in (
            "CORE-PARALLEL-001",
            "三份独立任务书",
            "FYQ",
            "XXT",
            "CYQ",
            "同一个 Frozen Snapshot",
            "允许 Integration 阶段有依赖",
            "不允许人的启动阶段有依赖",
        ):
            self.assertIn(token, text)

    def test_task_spec_requires_parallel_start_and_decoupling(self):
        text = (ROOT / "06_协作与交接" / "02_任务单规范.md").read_text(encoding="utf-8")
        for token in (
            "PARALLEL_START",
            "DEPENDENCY_DECOUPLING",
            "INTERFACE / MOCK",
            "INTEGRATION_STEP",
            "SECONDARY_QUEUE",
        ):
            self.assertIn(token, text)

    def test_fyq_profile_requires_three_taskbooks_per_wave(self):
        text = (SKILL_DIR / "profiles" / "FYQ_TECHNICAL_ORCHESTRATOR.md").read_text(encoding="utf-8")
        for token in (
            "每个 Wave",
            "FYQ TASK",
            "XXT TASK",
            "CYQ TASK",
            "同时发出",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
