from __future__ import annotations

import csv
import io
import json
import re
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
FIGURE_REQUIRED_FIELDS = {
    "type",
    "time_scope",
    "window_rule",
    "selection_reason",
}


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
        ("ACTIVE_ROLE", *ROLE_IDS, "role-neutral read-only", "SHARED_CORE.md", "逐问短导语", "05_参数选择协议.md"),
    )

    shared_core = _read(skill_dir / "core" / "SHARED_CORE.md")
    _require_tokens(
        errors,
        "shared core",
        shared_core,
        (
            "CORE-AUTH-001",
            "CORE-MATH-AUTH-001",
            "CORE-PAPER-AUTH-001",
            "CORE-FREEZE-001",
            "CORE-FREEZE-002",
            "CORE-DYNAMIC-001",
            "CORE-EVIDENCE-001",
            "CORE-PARAM-001",
            "CORE-AI-DISCLOSURE-001",
            "CORE-COLLAB-001",
            "material surrogate fidelity",
            "G3_FREEZE",
            "G2_VALIDATION=PASS",
            "AI Disclosure Gate FAIL",
        ),
    )

    parameter_protocol = _read(root / "03_建模与代码" / "05_参数选择协议.md")
    _require_tokens(
        errors,
        "parameter selection protocol",
        parameter_protocol,
        (
            "先判断参数的数学身份",
            "参数依据的优先级",
            "文献优先寻找，但不是机械硬要求",
            "粗扫的作用只是探索响应曲线",
            "自适应",
            "Parameter Evidence Gate",
        ),
    )

    xxt_profile = _read(profile_dir / "XXT_MATHEMATICAL.md")
    _require_tokens(
        errors,
        "XXT profile",
        xxt_profile,
        (
            "Mathematical Veto",
            "P0 REOPEN",
            "目标函数",
            "hard constraint",
            "单位、量纲",
            "accounting",
            "surrogate / proxy",
            "全过程 replay",
        ),
    )

    fyq_profile = _read(profile_dir / "FYQ_TECHNICAL_ORCHESTRATOR.md")
    _require_tokens(
        errors,
        "FYQ profile",
        fyq_profile,
        (
            "统一技术路线权",
            "mathematical_pass=true",
            "G2_VALIDATION=PASS",
            "旧 Mathematical PASS 失效",
        ),
    )

    evidence_gate = _read(root / "04_验收冻结" / "05_模型证据充分性Gate.md")
    _require_tokens(
        errors,
        "evidence gate",
        evidence_gate,
        (
            "动态、状态空间与路径依赖模型",
            "只检查最终状态，不得 Mathematical PASS",
            "MATHEMATICAL_P0",
            "强 baseline 本身只能支持 COMPETITIVE",
            "Parameter Evidence",
        ),
    )

    paper_gate = _read(root / "05_论文与图表" / "05_逐问写作与算法呈现Gate.md")
    _require_tokens(
        errors,
        "paper writing gate",
        paper_gate,
        (
            "前文已经设置“问题分析”",
            "大标题下短导语",
            "任务概括 → 核心难点 → 模型选择 → 应用依据",
            "不得提前写入未冻结结果",
            "由前述核心难点自然推出",
            "求解算法与伪代码",
            "结果及证据",
            "不能删掉结果解释",
            "为哪个具体决策、比较或判断提供依据",
        ),
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
        (
            "agent_bindings:",
            *ROLE_IDS,
            "authoritative_handoff:",
            "technical_direction_status:",
            "technical_direction_artifact:",
            "pre_paper_brief:",
            "evidence_gate_status:",
            "mathematical_review_status:",
            "mathematical_review_artifact:",
            "mathematical_review_commit:",
            "mathematical_veto_clear:",
            "dynamic_constraint_replay_status:",
            "surrogate_replay_status:",
            "formal_paper_handoff_status:",
        ),
    )

    paper_profile = _read(profile_dir / "CYQ_PAPER.md")
    _require_tokens(
        errors,
        "CYQ profile",
        paper_profile,
        (
            "INCOMPLETE",
            "缺口清单",
            "可直接定稿",
            "技术事实只读",
            "不得自行修改",
            "reopen request",
        ),
    )

    handoff = _read(root / "templates" / "Paper_Handoff模板.md")
    _require_tokens(
        errors,
        "Paper Handoff template",
        handoff,
        (
            "本问合同",
            "本问中心逻辑",
            "关键参数",
            "求解与伪代码包",
            "迭代与收敛事实",
            "核心指标语义",
            "验证证据",
            "自然语言初稿",
            "正式来源",
            "论文禁区",
            "Formal Paper Handoff",
            "Validation PASS",
            "FROZEN",
        ),
    )

    pre_paper = _read(root / "templates" / "Pre_Paper_Brief模板.md")
    _require_tokens(
        errors,
        "Pre-Paper Brief template",
        pre_paper,
        (
            "Pre-Paper Brief",
            "TECH_DIRECTION_STABLE",
            "未冻结声明",
            "已稳定的技术方向",
            "图表与证据需求",
            "待补与禁止定稿",
        ),
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

    figure_text = _read(root / "templates" / "Figure_Registry模板.csv").strip()
    if figure_text:
        try:
            fields = next(csv.reader(io.StringIO(figure_text)))
            missing = sorted(FIGURE_REQUIRED_FIELDS - set(fields))
            if missing:
                errors.append(f"Figure Registry missing fields: {missing}")
        except (csv.Error, StopIteration) as exc:
            errors.append(f"Figure Registry invalid csv: {exc}")
    else:
        errors.append("Figure Registry template missing or empty")

    ai_record = _read(root / "07_AI协作" / "03_AI使用记录.md")
    _require_tokens(
        errors,
        "AI disclosure workflow",
        ai_record,
        (
            "AI Disclosure 阻断 Gate",
            "adopted=yes",
            "human_verification",
            "team_decision",
            "human_changes",
            "paper_location",
            "artifact",
            "AI Disclosure Gate FAIL",
        ),
    )

    gates_path = root / "templates" / "gates.json"
    if gates_path.exists():
        try:
            gates = json.loads(gates_path.read_text(encoding="utf-8"))
            if gates.get("version") != "2.1":
                errors.append("gates.json schema version must be 2.1")

            deps = gates.get("gate_dependencies", {})
            if deps.get("G3_freeze") != ["G2_validation"]:
                errors.append("G3_freeze must depend on G2_validation")

            all_checks = {item for checks in gates.get("gates", {}).values() for item in checks}
            for token in (
                "evidence_sufficiency_pass",
                "robustness_plan_resolved",
                "task_specific_algorithm_pass",
                "ai_use_ledger_checked",
                "ai_disclosure_gate_pass",
                "pdf_layout_checked",
                "mathematical_veto_clear",
                "dynamic_constraints_full_replay_or_not_applicable",
                "surrogate_full_replay_or_not_applicable",
                "g2_validation_pass",
                "current_mathematical_review_matches_source_of_truth",
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
            release = re.search(r"^# CUMCM Rigorous Workflow v(\d+\.\d+\.\d+) Dispatcher$", dispatcher, re.M)
            if release is None or manifest.get("version") != release.group(1):
                errors.append("manifest version must match dispatcher release")
            if canonical_repo_mode and release is not None:
                version_heading = _read(root / "VERSION.md").splitlines()[:1]
                if not version_heading or not version_heading[0].startswith(f"# Version {release.group(1)} —"):
                    errors.append("VERSION.md must match dispatcher release")
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
