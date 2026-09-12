from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_TARGET = Path("dist/cumcm-rigorous-workflow-runtime-lite")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _source_commit(root: Path) -> str:
    env_sha = os.environ.get("GITHUB_SHA", "").strip()
    if env_sha:
        return env_sha
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout.strip()
    except OSError:
        pass
    return "UNKNOWN"


def _iter_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file())


def build(root: Path, target: Path) -> Path:
    root = root.resolve()
    target = target if target.is_absolute() else (root / target)
    manifest_path = root / "skills" / "cumcm-rigorous-workflow" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"runtime manifest missing: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    include_paths = manifest.get("runtime_include", [])
    forbidden = {
        str(x).lower()
        for key in ("forbidden_binary_extensions", "additional_forbidden_binary_extensions")
        for x in manifest.get(key, [])
    }
    max_file_bytes = int(manifest.get("max_runtime_file_bytes", 0) or 0)
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

    copied_files = _iter_files(target)
    bad_ext = [p for p in copied_files if p.suffix.lower() in forbidden]
    if bad_ext:
        formatted = ", ".join(str(p.relative_to(target)) for p in bad_ext)
        raise RuntimeError(f"forbidden corpus binary copied into runtime: {formatted}")

    if max_file_bytes > 0:
        oversized = [p for p in copied_files if p.stat().st_size > max_file_bytes]
        if oversized:
            formatted = ", ".join(
                f"{p.relative_to(target)}={p.stat().st_size}" for p in oversized
            )
            raise RuntimeError(
                f"runtime file exceeds max_runtime_file_bytes={max_file_bytes}: {formatted}"
            )

    source_manifest_sha256 = _sha256(manifest_path)
    file_records = [
        {
            "path": p.relative_to(target).as_posix(),
            "sha256": _sha256(p),
            "bytes": p.stat().st_size,
        }
        for p in copied_files
    ]
    build_manifest = {
        "name": manifest.get("name"),
        "skill_version": manifest.get("version"),
        "source_commit": _source_commit(root),
        "source_manifest_sha256": source_manifest_sha256,
        "runtime_file_count": len(file_records),
        "files": file_records,
    }
    build_manifest_path = target / "RUNTIME_BUILD_MANIFEST.json"
    build_manifest_path.write_text(
        json.dumps(build_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    sealed_files = copied_files + [build_manifest_path]
    sha_lines = [
        f"{_sha256(p)}  {p.relative_to(target).as_posix()}"
        for p in sorted(sealed_files)
    ]
    (target / "SHA256SUMS.txt").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

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
