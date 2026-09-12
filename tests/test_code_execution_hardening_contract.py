from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = _load_module("build_runtime_skill", ROOT / "tools" / "build_runtime_skill.py")
VALIDATOR = _load_module(
    "validate_code_execution_runtime",
    ROOT / "tools" / "validate_code_execution_runtime.py",
)


class CodeExecutionHardeningTests(unittest.TestCase):
    def test_code_execution_gate_has_full_chain(self):
        text = (ROOT / "03_建模与代码" / "06_代码执行与复现Gate.md").read_text(encoding="utf-8")
        for token in (
            "CODE-EXEC-001",
            "CODE-STRUCT-001",
            "CODE-SMOKE-001",
            "CODE-SCALE-001",
            "CODE-TIME-001",
            "CODE-VALIDATE-001",
            "CODE-OUTPUT-001",
            "CODE-REPLAY-001",
            "CODE-SEAL-001",
            "CODE-CHANGESET-001",
            "CODE-NO-SOFTPASS-001",
            "CODE EXECUTION PASS",
        ):
            self.assertIn(token, text)

    def test_manifest_runtime_is_self_contained_for_code_execution(self):
        manifest = json.loads(
            (ROOT / "skills" / "cumcm-rigorous-workflow" / "manifest.json").read_text(encoding="utf-8")
        )
        required = set(manifest["runtime_required_paths"])
        for rel in (
            "README.md",
            "VERSION.md",
            "03_建模与代码/01_最低可行主线_MVP.md",
            "03_建模与代码/02_实验循环.md",
            "03_建模与代码/03_约束优先.md",
            "03_建模与代码/04_场景与敏感性.md",
            "03_建模与代码/05_参数选择协议.md",
            "03_建模与代码/06_代码执行与复现Gate.md",
            "04_验收冻结/01_独立验收协议.md",
            "04_验收冻结/02_冻结包规范.md",
            "04_验收冻结/03_干净环境复现.md",
            "04_验收冻结/04_结果来源链.md",
            "04_验收冻结/05_模型证据充分性Gate.md",
            "07_AI协作/01_AI_Codex工作协议.md",
        ):
            self.assertIn(rel, required)
        self.assertGreater(manifest.get("max_runtime_file_bytes", 0), 0)
        forbidden = set(manifest["forbidden_binary_extensions"])
        for suffix in (".pdf", ".zip", ".docx", ".pptx", ".xlsx", ".webp"):
            self.assertIn(suffix, forbidden)

    def test_builder_emits_seal_and_runtime_validator_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runtime"
            BUILDER.build(ROOT, target)
            self.assertTrue((target / "RUNTIME_BUILD_MANIFEST.json").exists())
            self.assertTrue((target / "SHA256SUMS.txt").exists())
            self.assertEqual(VALIDATOR.validate(target), [])

    def test_missing_required_runtime_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runtime"
            BUILDER.build(ROOT, target)
            (target / "README.md").unlink()
            errors = VALIDATOR.validate(target)
            self.assertTrue(any("required runtime path missing: README.md" in x for x in errors), errors)

    def test_forbidden_binary_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runtime"
            BUILDER.build(ROOT, target)
            (target / "accidental.xlsx").write_bytes(b"not-really-xlsx")
            errors = VALIDATOR.validate(target)
            self.assertTrue(any("forbidden runtime binary: accidental.xlsx" in x for x in errors), errors)

    def test_corrupted_runtime_file_breaks_seal(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runtime"
            BUILDER.build(ROOT, target)
            path = target / "README.md"
            path.write_text(path.read_text(encoding="utf-8") + "\ncorruption\n", encoding="utf-8")
            errors = VALIDATOR.validate(target)
            self.assertTrue(
                any("sha256 mismatch: README.md" in x.lower() for x in errors),
                errors,
            )


if __name__ == "__main__":
    unittest.main()
