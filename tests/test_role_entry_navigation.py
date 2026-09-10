from pathlib import Path
import importlib.util
import json
import re
import shutil
import tempfile
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('skills/cumcm-rigorous-workflow')
ENTRIES = {
    'controller': 'FYQ_TECHNICAL_ORCHESTRATOR',
    'modeling': 'XXT_MATHEMATICAL',
    'paper': 'CYQ_PAPER',
}


def local_links(path):
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if not target.startswith(('https://', 'http://', '#')):
            yield (path.parent / unquote(target.split('#')[0])).resolve()


def navigation_files(root):
    return [root / 'SKILL.md',
            *sorted((root / SKILL / 'roles').glob('*/ROLE.md')),
            root / SKILL / 'profiles/CYQ_PAPER.md',
            *sorted((root / '05_论文与图表').glob('*.md'))]


class RoleEntryNavigationTests(unittest.TestCase):
    def test_validator_rejects_mismatched_release(self):
        spec = importlib.util.spec_from_file_location('runtime_validator', ROOT / 'tools/validate_runtime_skill.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'source'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.git', 'dist', '__pycache__'))
            path = target / SKILL / 'manifest.json'
            manifest = json.loads(path.read_text(encoding='utf-8'))
            manifest['version'] = '0.0.0'
            path.write_text(json.dumps(manifest), encoding='utf-8')
            self.assertIn('manifest version must match dispatcher release', module.validate(target))

    def test_validator_rejects_mismatched_version_heading(self):
        spec = importlib.util.spec_from_file_location('runtime_validator', ROOT / 'tools/validate_runtime_skill.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'source'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.git', 'dist', '__pycache__'))
            path = target / 'VERSION.md'
            path.write_text('# Version 0.0.0 — stale release\n', encoding='utf-8')
            self.assertIn('VERSION.md must match dispatcher release', module.validate(target))

    def assert_navigation(self, root):
        resolved = root.resolve()
        for file in navigation_files(root):
            for target in local_links(file):
                with self.subTest(file=str(file.relative_to(root)), target=str(target)):
                    self.assertTrue(target.is_relative_to(resolved), 'link escapes package')
                    self.assertTrue(target.is_file(), 'missing link target')

    def test_entries_link_to_existing_authoritative_profiles(self):
        dispatcher_links = set(local_links(ROOT / 'SKILL.md'))
        for folder, role in ENTRIES.items():
            entry = ROOT / SKILL / 'roles' / folder / 'ROLE.md'
            self.assertIn(entry.resolve(), dispatcher_links)
            self.assertIn((ROOT / SKILL / 'profiles' / f'{role}.md').resolve(),
                          set(local_links(entry)))
        self.assertEqual(list((ROOT / SKILL / 'roles').rglob('SKILL.md')), [])

    def test_source_navigation_targets_exist(self):
        self.assert_navigation(ROOT)

    def test_build_includes_new_navigation_and_old_profile_bytes(self):
        spec = importlib.util.spec_from_file_location('runtime_builder', ROOT / 'tools/build_runtime_skill.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            target = module.build(ROOT, Path(directory) / 'runtime')
            self.assert_navigation(target)
            manifest = json.loads((ROOT / SKILL / 'manifest.json').read_text(encoding='utf-8'))
            for path in manifest['canonical_sources']:
                self.assertTrue((ROOT / path).is_file())
            for folder, role in ENTRIES.items():
                for relative in [SKILL / 'roles' / folder / 'ROLE.md',
                                 SKILL / 'profiles' / f'{role}.md']:
                    self.assertEqual((ROOT / relative).read_bytes(), (target / relative).read_bytes())
            for name in ['06_动态论文框架.md', '07_表达参考.md']:
                self.assertEqual((ROOT / '05_论文与图表' / name).read_bytes(),
                                 (target / '05_论文与图表' / name).read_bytes())
            self.assertEqual(len(list(target.rglob('SKILL.md'))), 1)

    def test_paper_waiting_scenario_routes_to_framework_figures_and_evidence_return(self):
        entry = (ROOT / SKILL / 'roles' / 'paper' / 'ROLE.md').read_text(encoding='utf-8')
        framework = (ROOT / '05_论文与图表' / '06_动态论文框架.md').read_text(encoding='utf-8')
        figures = (ROOT / '05_论文与图表' / '02_图表工作流.md').read_text(encoding='utf-8')

        for token in ('动态论文框架', '图表工作流', '模型证据 Gate'):
            self.assertIn(token, entry)
        for token in ('模型未定或存在实质缺陷', '不自行启动全量求解', '不强制固定文件数量'):
            self.assertIn(token, framework)
        for token in ('不是每类图都必须出现', '真实改善和代价', '算法在预算内没找到解'):
            self.assertIn(token, figures)


if __name__ == '__main__':
    unittest.main()
