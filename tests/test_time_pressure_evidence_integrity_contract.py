from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = ROOT / "SKILL.md"
PROTOCOL = ROOT / "00_总览" / "05_赛时加速与流程保真协议.md"
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
