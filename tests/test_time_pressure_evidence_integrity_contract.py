from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "skills" / "cumcm-rigorous-workflow" / "core" / "SHARED_CORE.md"
DISPATCHER = ROOT / "SKILL.md"
EVIDENCE = ROOT / "04_验收冻结" / "05_模型证据充分性Gate.md"
PARAMETER = ROOT / "03_建模与代码" / "05_参数选择协议.md"
PROTOCOL = ROOT / "00_总览" / "05_赛时加速与流程保真协议.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_time_pressure_never_waives_mandatory_evidence():
    core = read(CORE)
    assert "CORE-ACCEL-001" in core
    assert "时间压力" in core
    assert "不能降低" in core or "不得降低" in core
    for token in [
        "数据横向比较",
        "参数证据",
        "hard constraint",
        "independent recomputation",
        "Mathematical Review",
        "Evidence Gate",
    ]:
        assert token in core


def test_acceleration_has_fail_closed_canonical_protocol_and_dispatch_trigger():
    assert PROTOCOL.exists()
    protocol = read(PROTOCOL)
    dispatcher = read(DISPATCHER)
    assert "加速" in dispatcher and "05_赛时加速与流程保真协议.md" in dispatcher
    assert "加速只能改变" in protocol
    assert "降低 Claim" in protocol
    assert "MISSING_EVIDENCE" in protocol
    assert "时间有限" in protocol


def test_representative_single_value_requires_comparison_before_formal_use():
    evidence = read(EVIDENCE)
    parameter = read(PARAMETER)
    for doc in (evidence, parameter):
        assert "代表值" in doc
        assert "横向" in doc
        assert "单值" in doc
    assert "不得以时间压力" in parameter or "不得以\"时间有限\"" in parameter
    assert "FAIL / ADD EXPERIMENT" in parameter
