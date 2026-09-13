"""Explicit candidate point-power interpolation, without choosing a primary mode.

Only the selected vintage supplies future hourly points. An explicitly supplied
earlier vintage may supply its exact issue-boundary point in PREVIOUS mode.
Targets are ten-minute right endpoints; kWh = interpolated kW / 6.
Neither utility authorizes actual scheduling or an interpretation of hour means.
"""
from bisect import bisect_left
from datetime import datetime, timedelta, timezone
import math

TZ = timezone(timedelta(hours=8))
PREVIOUS_LEGAL_VINTAGE = "PREVIOUS_LEGAL_VINTAGE"
FIRST_POINT_CONSTANT = "FIRST_POINT_CONSTANT"
POINT_POWER = "POINT_POWER"


def _invalid(reason):
    raise ValueError(f"INPUT_INVALID: {reason}")


def _instant(value, field):
    try:
        parsed = datetime.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    if parsed is None or parsed.utcoffset() is None:
        _invalid(f"{field} requires a timezone-aware ISO timestamp")
    return parsed.astimezone(TZ)


def _identifier(value, field):
    if not isinstance(value, str) or not value.strip():
        _invalid(f"{field} is missing or malformed")
    return value


def _checked(vintage, decision):
    """Validate a complete selected vintage; never silently drop bad anchors."""
    if not isinstance(vintage, dict):
        _invalid("vintage must be a dict")
    issue = _instant(vintage.get("issue_time"), "issue_time")
    known = _instant(vintage.get("known_at"), "known_at")
    if not issue <= known <= decision:
        _invalid("vintage issue/known_at is future or chronologically invalid")
    identity = _identifier(vintage.get("vintage_id"), "vintage_id")
    raw = vintage.get("anchors")
    if not isinstance(raw, list) or not raw:
        _invalid("missing anchors")
    anchors = []
    ids = set()
    for anchor in raw:
        if not isinstance(anchor, dict):
            _invalid("anchor must be a dict")
        target = _instant(anchor.get("target_time"), "anchor target_time")
        available = _instant(anchor.get("known_at"), "anchor known_at")
        if not issue <= available <= decision:
            _invalid("anchor known_at is future or before issue")
        anchor_id = _identifier(anchor.get("anchor_id"), "anchor_id")
        if anchor_id in ids:
            _invalid("duplicate anchor_id")
        ids.add(anchor_id)
        power = anchor.get("pv_kw")
        if isinstance(power, bool) or not isinstance(power, (int, float)) or not math.isfinite(power) or power < 0:
            _invalid("anchor power must be present, numeric, finite and nonnegative")
        if anchors:
            if target - anchors[-1]["target"] != timedelta(hours=1):
                _invalid("missing/duplicate/nonchronological hourly anchor")
        elif target not in (issue, issue + timedelta(hours=1)):
            _invalid("first anchor must be at issue or issue + one hour")
        anchors.append({"target": target, "power": float(power), "id": anchor_id,
                        "known": max(known, available)})
    return issue, known, identity, anchors


def interpolate(vintage, targets, decision_time, *, boundary_mode,
                quantity_semantics, previous_vintage=None) -> list[dict]:
    """Return causal point-power interpolation with dependency weights/provenance.

    Both configuration keywords are mandatory. Explicit null/empty selections
    raise HOLD; unsupported choices raise INPUT_INVALID. Missing old issue-time
    support raises MISSING_BOUNDARY only when a requested endpoint needs it.
    FIRST_POINT_CONSTANT has no dependency on ``previous_vintage`` and ignores it.
    PREVIOUS_LEGAL_VINTAGE validates any supplied previous vintage as earlier and
    legally known, and uses only its exact current-issue point as left support.
    Targets are strictly increasing, after issue and no later than the last
    selected anchor. There is no right extrapolation or future-vintage lookup.
    """
    if boundary_mode in (None, "") or quantity_semantics in (None, ""):
        raise ValueError("HOLD: boundary_mode and quantity_semantics must be explicitly selected")
    if boundary_mode not in (PREVIOUS_LEGAL_VINTAGE, FIRST_POINT_CONSTANT):
        _invalid("unsupported boundary_mode")
    if quantity_semantics != POINT_POWER:
        _invalid("only explicitly configured POINT_POWER is implemented")
    decision = _instant(decision_time, "decision_time")
    issue, known, identity, anchors = _checked(vintage, decision)
    old_anchors = []
    if boundary_mode == PREVIOUS_LEGAL_VINTAGE and previous_vintage is not None:
        old_issue, _, old_identity, old_anchors = _checked(previous_vintage, decision)
        if old_issue >= issue or old_identity == identity:
            _invalid("previous vintage must be earlier and distinct")
    if not isinstance(targets, list):
        _invalid("targets must be a list")
    endpoints = [_instant(value, "target_time") for value in targets]
    previous_endpoint = issue
    for endpoint in endpoints:
        if endpoint <= previous_endpoint or endpoint > anchors[-1]["target"]:
            _invalid("target timeline is duplicate, reversed or outside the selected horizon")
        if endpoint.minute % 10 or endpoint.second or endpoint.microsecond:
            _invalid("target must be a ten-minute slot endpoint")
        previous_endpoint = endpoint
    support = list(anchors)
    if endpoints and endpoints[0] < anchors[0]["target"] and boundary_mode == PREVIOUS_LEGAL_VINTAGE:
        boundary = next((a for a in old_anchors if a["target"] == issue), None)
        if boundary is None:
            raise ValueError("MISSING_BOUNDARY: no legal old vintage anchor at current issue time")
        if boundary["id"] in {a["id"] for a in anchors}:
            _invalid("old/current anchor IDs collide")
        support.insert(0, boundary)
    times = [a["target"] for a in support]
    result = []
    for endpoint in endpoints:
        index = bisect_left(times, endpoint)
        if index == 0 or times[index] == endpoint:
            left = right = support[index]
            left_weight, right_weight = 1.0, 0.0
        else:
            left, right = support[index - 1], support[index]
            right_weight = (endpoint - left["target"]) / (right["target"] - left["target"])
            left_weight = 1.0 - right_weight
        power = left_weight * left["power"] + right_weight * right["power"]
        result.append({
            "target_time": endpoint.isoformat(), "pv_kw": power, "pv_kwh": power / 6,
            "left_anchor_id": left["id"], "right_anchor_id": right["id"],
            "left_weight": left_weight, "right_weight": right_weight,
            "known_at": max(known, left["known"], right["known"]).isoformat(),
            "boundary_mode": boundary_mode, "vintage_id": identity,
        })
    return result
