from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


GATE_PATH = Path("03_建模与代码/06_代码执行与复现Gate.md")
BUILD_MANIFEST = Path("RUNTIME_BUILD_MANIFEST.json")
SHA_FILE = Path("SHA256SUMS.txt")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _covered_by_runtime_include(rel: str, include_paths: list[str]) -> bool:
    p = Path(rel)
    for inc_text in include_paths:
        inc = Path(inc_text)
        if p == inc:
            return True
        try:
            p.relative_to(inc)
            return True
        except ValueError:
            pass
    return False


def _verify_sha_file(root: Path, errors: list[str]) -> None:
    sha_path = root / SHA_FILE
    if not sha_path.exists():
        errors.append("runtime seal missing SHA256SUMS.txt")
        return
    for line_no, raw in enumerate(sha_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        if "  " not in raw:
            errors.append(f"SHA256SUMS malformed line {line_no}")
            continue
        expected, rel = raw.split("  ", 1)
        path = root / rel
        if not path.exists():
            errors.append(f"SHA256SUMS missing file: {rel}")
            continue
        actual = _sha256(path)
        if actual != expected:
            errors.append(f"SHA256 mismatch: {rel}")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    manifest_path = root / "skills" / "cumcm-rigorous-workflow" / "manifest.json"
    if not manifest_path.exists():
        return ["runtime manifest missing"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"runtime manifest invalid json: {exc}"]

    include_paths = [str(x) for x in manifest.get("runtime_include", [])]
    required_paths = [str(x) for x in manifest.get("runtime_required_paths", [])]
    forbidden = {str(x).lower() for x in manifest.get("forbidden_binary_extensions", [])}
    max_file_bytes = int(manifest.get("max_runtime_file_bytes", 0) or 0)

    if not required_paths:
        errors.append("manifest runtime_required_paths is empty")

    for rel in required_paths:
        if not _covered_by_runtime_include(rel, include_paths):
            errors.append(f"required runtime path not covered by runtime_include: {rel}")
        if not (root / rel).exists():
            errors.append(f"required runtime path missing: {rel}")

    gate = root / GATE_PATH
    if not gate.exists():
        errors.append(f"code execution gate missing: {GATE_PATH.as_posix()}")
    else:
        text = gate.read_text(encoding="utf-8")
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
            "FAIL / REOPEN",
        ):
            if token not in text:
                errors.append(f"code execution gate missing token: {token}")

    canonical_repo_mode = (root / "tools" / "build_runtime_skill.py").exists()
    if canonical_repo_mode:
        # Full repositories may legitimately contain competition data and binaries.
        # The builder, not the source repository, is responsible for filtering Runtime Lite.
        return errors

    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in forbidden:
            errors.append(f"forbidden runtime binary: {rel}")
        if max_file_bytes > 0 and path.stat().st_size > max_file_bytes:
            errors.append(
                f"runtime file exceeds max_runtime_file_bytes={max_file_bytes}: "
                f"{rel}={path.stat().st_size}"
            )

    build_manifest_path = root / BUILD_MANIFEST
    if not build_manifest_path.exists():
        errors.append("runtime seal missing RUNTIME_BUILD_MANIFEST.json")
    else:
        try:
            build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
            if build_manifest.get("skill_version") != manifest.get("version"):
                errors.append("build manifest skill_version does not match runtime manifest")
            if not str(build_manifest.get("source_commit", "")).strip():
                errors.append("build manifest source_commit missing")
            if not str(build_manifest.get("source_manifest_sha256", "")).strip():
                errors.append("build manifest source_manifest_sha256 missing")
            records = build_manifest.get("files", [])
            if not isinstance(records, list) or not records:
                errors.append("build manifest files is empty")
            else:
                for record in records:
                    rel = str(record.get("path", ""))
                    path = root / rel
                    if not rel or not path.exists():
                        errors.append(f"build manifest file missing: {rel}")
                        continue
                    if _sha256(path) != record.get("sha256"):
                        errors.append(f"build manifest sha256 mismatch: {rel}")
                    if path.stat().st_size != record.get("bytes"):
                        errors.append(f"build manifest byte-size mismatch: {rel}")
        except json.JSONDecodeError as exc:
            errors.append(f"build manifest invalid json: {exc}")

    _verify_sha_file(root, errors)
    return errors


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for item in errors:
            print(f"FAIL: {item}")
        return 1
    print("PASS: code execution/runtime closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
