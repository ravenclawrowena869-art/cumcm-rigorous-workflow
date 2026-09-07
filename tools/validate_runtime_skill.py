from __future__ import annotations

import json
import sys
from pathlib import Path

ROLE_IDS = (
    "FYQ_TECHNICAL_ORCHESTRATOR",
    "XXT_MATHEMATICAL",
    "CYQ_PAPER",
)
FORBIDDEN_BINARY = {".pdf", ".png", ".jpg", ".jpeg"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill_dir = root / "skills" / "cumcm-rigorous-workflow"
    profile_dir = skill_dir / "profiles"
    expected = {f"{role}.md" for role in ROLE_IDS}
    actual = {p.name for p in profile_dir.glob("*.md")} if profile_dir.exists() else set()
    if actual != expected:
        errors.append(f"profiles mismatch: expected={sorted(expected)} actual={sorted(actual)}")

    dispatcher = _read(root / "SKILL.md")
    for token in ("ACTIVE_ROLE", *ROLE_IDS):
        if token not in dispatcher:
            errors.append(f"dispatcher missing token: {token}")

    bad = [str(p.relative_to(root)) for p in skill_dir.rglob("*") if p.is_file() and p.suffix.lower() in FORBIDDEN_BINARY] if skill_dir.exists() else []
    if bad:
        errors.append(f"runtime skill contains forbidden binary corpus: {bad}")

    if ".cumcm-agent.local.yaml" not in _read(root / ".gitignore"):
        errors.append(".gitignore missing .cumcm-agent.local.yaml")

    state = _read(root / "templates" / "project_state模板.yaml")
    for token in ("agent_bindings:", *ROLE_IDS):
        if token not in state:
            errors.append(f"project_state missing token: {token}")

    paper_profile = _read(profile_dir / "CYQ_PAPER.md")
    for token in ("INCOMPLETE", "缺口清单", "可直接定稿"):
        if token not in paper_profile:
            errors.append(f"CYQ profile missing blocking token: {token}")

    manifest_path = skill_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if tuple(manifest.get("roles", [])) != ROLE_IDS:
                errors.append("manifest roles do not match canonical role order")
        except json.JSONDecodeError as exc:
            errors.append(f"manifest invalid json: {exc}")
    else:
        errors.append("runtime manifest missing")

    return errors


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for item in errors:
            print(f"FAIL: {item}")
        return 1
    print("PASS: runtime skill contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
