from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HuggingFaceResearchLaneContractTest(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_hf_protocol_exists_and_is_conditional(self):
        text = self.read("02_开赛与拆题/05_HuggingFace研究资产协议.md")
        self.assertIn("HF Research Lane", text)
        self.assertIn("条件触发", text)
        self.assertIn("不得作为默认必经步骤", text)
        self.assertIn("HF_UNAVAILABLE", text)

    def test_shared_core_has_hf_authority_and_data_safety(self):
        text = self.read("skills/cumcm-rigorous-workflow/core/SHARED_CORE.md")
        self.assertIn("CORE-HF-001", text)
        self.assertIn("Hugging Face", text)
        self.assertIn("不得替代本题验证", text)
        self.assertIn("未经明确批准", text)
        self.assertIn("上传", text)

    def test_external_metrics_cannot_replace_local_benchmark(self):
        text = self.read("04_验收冻结/05_模型证据充分性Gate.md")
        self.assertIn("Model Card", text)
        self.assertIn("Dataset Card", text)
        self.assertIn("本题", text)
        self.assertIn("benchmark", text.lower())

    def test_model_selection_requires_asset_provenance(self):
        text = self.read("02_开赛与拆题/02_模型选择协议.md")
        for token in ["repo_id", "revision", "license", "hardware", "local benchmark"]:
            self.assertIn(token, text)

    def test_source_index_routes_hf_assets(self):
        text = self.read("skills/cumcm-rigorous-workflow/references/SOURCE_INDEX.md")
        for token in ["Hugging Face Papers", "Models", "Datasets", "Spaces"]:
            self.assertIn(token, text)

    def test_dispatcher_mentions_hf_trigger(self):
        text = self.read("SKILL.md")
        self.assertIn("HF Research Lane", text)
        self.assertIn("预训练模型", text)
        self.assertIn("外部公开数据", text)

    def test_runtime_manifest_includes_hf_protocol(self):
        manifest = json.loads(self.read("skills/cumcm-rigorous-workflow/manifest.json"))
        rel = "02_开赛与拆题/05_HuggingFace研究资产协议.md"
        self.assertIn(rel, manifest["canonical_sources"])
        self.assertIn(rel, manifest["runtime_include"])
        self.assertEqual(manifest["version"], "2.1.4")


if __name__ == "__main__":
    unittest.main()
