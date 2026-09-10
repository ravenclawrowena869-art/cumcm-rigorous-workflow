from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = ROOT / "SKILL.md"
PROTOCOL = ROOT / "00_总览" / "05_赛时加速与流程保真协议.md"
QUICK_REDLINE = ROOT / "00_总览" / "06_正赛技术红线速查.md"
MANIFEST = ROOT / "skills" / "cumcm-rigorous-workflow" / "manifest.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_time_pressure_protocol_is_runtime_reachable():
    assert PROTOCOL.exists()
    dispatcher = read(DISPATCHER)
    assert "05_赛时加速与流程保真协议.md" in dispatcher
    assert "加速" in dispatcher
    assert "赶时间" in dispatcher or "时间压力" in dispatcher

    manifest = json.loads(read(MANIFEST))
    rel = "00_总览/05_赛时加速与流程保真协议.md"
    assert rel in manifest["canonical_sources"]
    assert rel in manifest["runtime_include"]


def test_acceleration_never_waives_mandatory_evidence():
    protocol = read(PROTOCOL)
    for token in [
        "时间压力",
        "数据横向比较",
        "参数证据",
        "hard constraint",
        "independent recomputation",
        "Mathematical Review",
        "Evidence Gate",
        "Freeze",
    ]:
        assert token in protocol

    assert "加速只能改变" in protocol
    assert "不得降低" in protocol
    assert "降低 Claim" in protocol
    assert "MISSING_EVIDENCE" in protocol


def test_representative_value_cannot_be_selected_casually_under_deadline():
    protocol = read(PROTOCOL)
    for token in [
        "代表值",
        "候选总体",
        "横向",
        "异常值",
        "选择规则",
        "合理替代值",
        "正式模型",
        "论文",
    ]:
        assert token in protocol

    assert "时间有限" in protocol
    assert "不得" in protocol


def test_competition_redline_quick_reference_is_runtime_reachable():
    assert QUICK_REDLINE.exists()
    dispatcher = read(DISPATCHER)
    assert "06_正赛技术红线速查.md" in dispatcher
    for trigger in ["新 Question", "路线冻结", "正式结果验收", "Paper Handoff"]:
        assert trigger in dispatcher

    manifest = json.loads(read(MANIFEST))
    rel = "00_总览/06_正赛技术红线速查.md"
    assert rel in manifest["canonical_sources"]
    assert rel in manifest["runtime_include"]


def test_competition_redline_quick_reference_covers_cross_problem_failure_modes():
    quick = read(QUICK_REDLINE)
    for token in [
        "预测模型",
        "预测区间",
        "顺序敏感",
        "exact anchor",
        "动态约束",
        "参数证据",
        "surrogate",
        "不可行",
        "Mathematical Review",
        "Evidence Gate",
    ]:
        assert token in quick

    assert "03_建模与代码/05_参数选择协议.md" in quick
    assert "04_验收冻结/05_模型证据充分性Gate.md" in quick
    assert "不得替代" in quick


def test_competition_redline_quick_reference_does_not_hardcode_training_case_values():
    quick = read(QUICK_REDLINE)
    for forbidden in [
        "rho=0.20",
        "rho = 0.20",
        "RegionA",
        "RollingMean-336",
        "150-task",
        "72h",
    ]:
        assert forbidden not in quick
