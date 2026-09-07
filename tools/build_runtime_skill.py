from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


DEFAULT_TARGET = Path("dist/cumcm-rigorous-workflow-runtime-lite")


def build(root: Path, target: Path) -> Path:
    root = root.resolve()
    target = target if target.is_absolute() else (root / target)
    manifest_path = root / "skills" / "cumcm-rigorous-workflow" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"runtime manifest missing: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    include_paths = manifest.get("runtime_include", [])
    forbidden = {x.lower() for x in manifest.get("forbidden_binary_extensions", [])}
    if not include_paths:
        raise ValueError("manifest runtime_include is empty")

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    for rel_text in include_paths:
        rel = Path(rel_text)
        src = root / rel
        if not src.exists():
            raise FileNotFoundError(f"canonical runtime include missing: {rel_text}")
        dst = target / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    bad = [p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in forbidden]
    if bad:
        formatted = ", ".join(str(p.relative_to(target)) for p in bad)
        raise RuntimeError(f"forbidden corpus binary copied into runtime: {formatted}")

    return target


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    built = build(root, target)
    count = sum(1 for p in built.rglob("*") if p.is_file())
    print(f"PASS: built runtime skill at {built} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
