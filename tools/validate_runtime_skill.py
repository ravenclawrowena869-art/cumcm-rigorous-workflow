from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

ROLE_IDS = (
    "FYQ_TECHNICAL_ORCHESTRATOR",
    "XXT_MATHEMATICAL",
    "CYQ_PAPER",
)
FORBIDDEN_BINARY = {".pdf", ".png", ".jpg", ".jpeg"}
LEDGER_FIELDS = [
    "time",
    "tool_model",
    "stage",
    "prompt_summary",
    "ai_response_summary",
    "human_verification",
    "team_decision",
    "adopted",
    "human_changes",
    "paper_location",
    "artifact",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _require_tokens(errors: list[str], label: str, text: str, tokens: tuple[str, ...]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{label} missing token: {token}")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    skill_dir = root / "skills" / "cumcm-rigorous-workflow"
    profile_dir = skill_dir / "profiles"

    # Repository-maintenance checks and Runtime Lite checks overlap, but a built
    # Runtime Lite deliberately does not include repo-only files such as
    # .gitignore or tools/. Detect canonical-repo mode by the validator source
    # itself rather than requiring those maintenance files inside the runtime.
    canonical_repo_mode = (root / "tools" / "validate_runtime_skill.py").exists()

    expected_profiles = {f"{role}.md" for role in ROLE_IDS}
    actual_profiles = {p.name for p in profile_dir.glob("*.md")} if profile_dir.exists() else set()
    if actual_profiles != expected_profiles:
        errors.append(
            f"profiles mismatch: expected={sorted(expected_profiles)} actual={sorted(actual_profiles)}"
        )

    dispatcher = _read(root / "SKILL.md")
    _require_tokens(
        errors,
        "dispatcher",
        dispatcher,
        ("ACTIVE_ROLE", *ROLE_IDS, "role-neutral read-only", "SHARED_CORE.md"),
    )

    shared_core = _read(skill_dir / "core" / "SHARED_CORE.md")
    _require_tokens(
        errors,
        "shared core",
        shared_core,
        ("CORE-AUTH-001", "CORE-FREEZE-001", "CORE-EVIDENCE-001", "CORE-COLLAB-001"),
    )

    bad = [
        str(p.relative_to(root))
        for p in skill_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in FORBIDDEN_BINARY
    ] if skill_dir.exists() else []
    if bad:
        errors.append(f"runtime skill contains forbidden binary corpus: {bad}")

    if canonical_repo_mode:
        gitignore = _read(root / ".gitignore")
        _require_tokens(errors, ".gitignore", gitignore, (".cumcm-agent.local.yaml", "dist/"))

    state = _read(root / "templates" / "project_state模板.yaml")
    _require_tokens(
        errors,
        "project_state",
        state,
        ("agent_bindings:", *ROLE_IDS, "authoritative_handoff:", "evidence_gate_status:"),
    )

    paper_profile = _read(profile_dir / "CYQ_PAPER.md")
    _require_tokens(errors, "CYQ profile", paper_profile, ("INCOMPLETE", "缺口清单", "可直接定稿"))

    handoff = _read(root / "templates" / "Paper_Handoff模板.md")
    _require_tokens(
        errors,
        "Paper Handoff template",
        handoff,
        ("本问合同", "本问中心逻辑", "求解与伪代码包", "验证证据", "自然语言初稿", "正式来源", "论文禁区"),
    )

    collaboration = _read(root / "06_协作与交接" / "06_三GPT协作与Skill共同维护.md")
    _require_tokens(
        errors,
        "collaboration governance",
        collaboration,
        ("FYQ GPT → XXT GPT", "XXT GPT → FYQ GPT", "FYQ / XXT GPT → CYQ GPT", "CYQ GPT → FYQ / XXT GPT"),
    )

    ledger_text = _read(root / "templates" / "AI使用记录模板.csv").strip()
    if ledger_text:
        try:
            fields = next(csv.reader(io.StringIO(ledger_text)))
            if fields != LEDGER_FIELDS:
                errors.append(f"AI ledger fields mismatch: {fields}")
        except (csv.Error, StopIteration) as exc:
            errors.append(f"AI ledger invalid csv: {exc}")
    else:
        errors.append("AI ledger template missing or empty")

    gates_path = root / "templates" / "gates.json"
    if gates_path.exists():
        try:
            gates = json.loads(gates_path.read_text(encoding="utf-8"))
            if gates.get("version") != "2.1":
                errors.append("gates.json version must be 2.1")
            all_checks = {item for checks in gates.get("gates", {}).values() for item in checks}
            for token in (
                "evidence_sufficiency_pass",
                "robustness_plan_resolved",
                "task_specific_algorithm_pass",
                "ai_use_ledger_checked",
                "pdf_layout_checked",
            ):
                if token not in all_checks:
                    errors.append(f"gates.json missing check: {token}")
        except json.JSONDecodeError as exc:
            errors.append(f"gates.json invalid json: {exc}")
    else:
        errors.append("gates.json missing")

    manifest_path = skill_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if tuple(manifest.get("roles", [])) != ROLE_IDS:
                errors.append("manifest roles do not match canonical role order")
            if manifest.get("version") != "2.1":
                errors.append("manifest version must be 2.1")
            forbidden = {x.lower() for x in manifest.get("forbidden_binary_extensions", [])}
            if forbidden != FORBIDDEN_BINARY:
                errors.append("manifest forbidden binary extensions mismatch")
            for rel in manifest.get("runtime_include", []):
                if not (root / rel).exists():
                    errors.append(f"manifest runtime include missing: {rel}")
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
