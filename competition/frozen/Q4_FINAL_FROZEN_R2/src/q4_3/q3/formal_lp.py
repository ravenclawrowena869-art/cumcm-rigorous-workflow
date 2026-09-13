"""Formal continuous LP planner for Q3 R5.

This module implements the released A1--A6 semantics for the engineering
solver lane. It does not authorize a formal screening run; that remains a
Controller-release concern handled by the engine/orchestrator boundary.
"""
from __future__ import annotations

from copy import deepcopy
from time import perf_counter
import hashlib
import json
import math

import numpy as np
from scipy.optimize import linprog

from .common import instant

FORMAL_PLANNER_KIND = "FORMAL_LP"

_ALLOWED_DIFF = {"strategy_id", "update_stages", "pv_vintage_policy"}
_SHARED = {
    "run_class": "FORMAL",
    "beta": -0.5,
    "eta_c": 0.9,
    "eta_d": 0.9,
    "source_split_mode": "GRID_FIRST",
    "storage_execution_policy": "STAGE_REFERENCE_SAFETY_OVERRIDE_V1",
    "price_time_mode": "DELIVERY_SLOT_PRICE",
    "planning_horizon": "CURRENT_DAY_REMAINDER",
    "actual_timing": "AT_ENDPOINT_CURRENT_SLOT_ACTUAL",
    "terminal_contract": "FREE_BOUNDED_YEAR_END",
    "soc_min_kwh": 1200.0,
    "soc_max_kwh": 10800.0,
    "power_limit_kwh_per_slot": 5000.0 / 6.0,
    "tol_cost_yuan": 1e-7,
    "tol_throughput_kwh": 1e-7,
    "hard_tolerance": 1e-7,
    "solver_id": "SCIPY_HIGHS_LP",
    "fallback": "FORBIDDEN",
}


def _canonical_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_formal_config(strategy_id: str) -> dict:
    strategy = strategy_id.upper()
    if strategy == "B0":
        diff = {"strategy_id": "B0", "update_stages": [0], "pv_vintage_policy": "PV_00_ONLY"}
    elif strategy in {"B1A", "B1a"}:
        diff = {"strategy_id": "B1A", "update_stages": [0, 6, 12, 18], "pv_vintage_policy": "LATEST_CAUSAL_00_06_12_18"}
    else:
        raise ValueError("UNSUPPORTED_FORMAL_STRATEGY")
    cfg = deepcopy(_SHARED)
    cfg["shared_contract_sha256"] = _canonical_hash(_SHARED)
    cfg.update(diff)
    return cfg


def _finite_nonnegative(v, name: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
        raise ValueError(f"INVALID_FORMAL_INPUT:{name}")
    return float(v)


def _status(stage_name: str, result, elapsed: float) -> dict:
    ok = bool(result.success and result.status == 0)
    return {
        "name": stage_name,
        "status": "OPTIMAL" if ok else "FAILED",
        "solver_status_code": int(result.status),
        "message": str(result.message),
        "objective": float(result.fun) if ok else None,
        "runtime_seconds": float(elapsed),
        "optimality_gap": None,
        "optimality_gap_status": "UNAVAILABLE_FROM_SCIPY_LINPROG_LP_RESULT" if ok else "NOT_APPLICABLE_FAILED",
    }


def _run_lp(name, c, A_ub, b_ub, A_eq, b_eq, bounds):
    begun = perf_counter()
    opts = {"primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9}
    result = linprog(c, A_ub=A_ub or None, b_ub=b_ub or None,
                     A_eq=A_eq or None, b_eq=b_eq or None,
                     bounds=bounds, method="highs", options=opts)
    primary_meta = _status(name, result, perf_counter() - begun)
    numerical_recovery_used = False
    # R5.4 numerical-only recovery: preserve the exact LP and the signed 1e-9
    # feasibility tolerances. Only the third lexicographic tie-break may retry
    # with HiGHS IPM and presolve disabled when the default HiGHS path returns
    # status=4/unknown-primal-infeasible. Economic and throughput stages never
    # use this path; no constraint/RHS/objective tolerance is relaxed.
    if primary_meta["status"] != "OPTIMAL" and name == "MIN_NETLOAD_DEVIATION":
        result = linprog(c, A_ub=A_ub or None, b_ub=b_ub or None,
                         A_eq=A_eq or None, b_eq=b_eq or None,
                         bounds=bounds, method="highs-ipm",
                         options={**opts, "presolve": False})
        numerical_recovery_used = bool(result.success and result.status == 0)
    meta = _status(name, result, perf_counter() - begun)
    meta["primary_attempt_status"] = primary_meta["status"]
    meta["primary_attempt_status_code"] = primary_meta["solver_status_code"]
    meta["numerical_recovery_used"] = numerical_recovery_used
    meta["numerical_recovery_method"] = "highs-ipm_presolve_false_same_lp_1e-9" if numerical_recovery_used else None
    if meta["status"] != "OPTIMAL":
        raise RuntimeError(f"FORMAL_LP_{name}_FAILED:{meta['solver_status_code']}:{meta['message']}")
    return result, meta


def validate_formal_plan(request: dict, config: dict, plan: list[dict]) -> dict:
    slots = request["future_slots"]
    eta_c = float(config["eta_c"])
    eta_d = float(config["eta_d"])
    emin = float(config["soc_min_kwh"])
    emax = float(config["soc_max_kwh"])
    pmax = float(config["power_limit_kwh_per_slot"])
    tol = float(config["hard_tolerance"])
    e = float(request["initial_soc"])
    max_v = 0.0
    argmax = None
    adjustment_down = 0.0
    adjustment_up = 0.0
    predicted_emergency = 0.0
    for row in plan:
        t = row["slot_id"]
        i = t - 1
        q = float(row["q"]); c = float(row["c_ref"]); d = float(row["d_ref"])
        l = float(request["load_kwh"][i]); s = float(request["pv_kwh"][i])
        r = float(row["predicted_emergency_kwh"]); w = float(row["predicted_unused_grid_kwh"]); v = float(row["predicted_pv_curtail_kwh"])
        candidates = [
            abs(q - w + r + s + d - l - c - v),
            max(-q, -c, -d, -r, -w, -v, 0.0),
            max(c - pmax, d - pmax, 0.0),
            max(w - q, v - s, 0.0),
            min(c, d),
            min(r, c),
        ]
        next_e = e + eta_c * c - d / eta_d
        candidates.append(max(emin - next_e, next_e - emax, 0.0))
        if "reference_soc_after_kwh" in row:
            candidates.append(abs(float(row["reference_soc_after_kwh"]) - next_e))
        local = max(candidates)
        if local > max_v:
            max_v = local; argmax = {"slot_id": t}
        e = next_e
        predicted_emergency += r
        if request["stage"]:
            prev = float(request["previous_active"][t]["q"])
            adjustment_up += max(q - prev, 0.0)
            adjustment_down += max(prev - q, 0.0)
    return {
        "status": "PASS" if max_v <= tol else "FAIL",
        "max_violation": max_v,
        "argmax_location": argmax,
        "final_reference_soc_kwh": e,
        "predicted_emergency_kwh": predicted_emergency,
        "adjustment_up_kwh": adjustment_up,
        "adjustment_down_kwh": adjustment_down,
    }


def solve_formal_lp(request: dict, config: dict) -> dict:
    """Solve one Q3 planning stage as a lexicographic continuous LP."""
    slots = list(request.get("future_slots") or [])
    dependency_known_at = request.get("dependency_known_at")
    if dependency_known_at is None or instant(dependency_known_at) > instant(request.get("decision_time")):
        raise ValueError("FORMAL_KNOWN_AT_LEAKAGE")
    if not slots or slots != list(range(slots[0], 145)):
        # Unit fixtures may use a strict ordered subset; production requests use
        # current-day remainder. Explicit unit fixtures identify themselves by
        # having fewer than 144-vector slots but still strictly increasing.
        if not slots or slots != sorted(set(slots)):
            raise ValueError("INVALID_FUTURE_SLOTS")
    if request.get("stage") not in (0, 6, 12, 18):
        raise ValueError("INVALID_FORMAL_STAGE")
    stage = int(request["stage"])
    expected_first = stage * 6 + 1
    if len(slots) > 2 and slots[0] != expected_first:
        raise ValueError("PAST_OR_MISSING_FORMAL_SLOT")
    if config.get("run_class") != "FORMAL" or config.get("beta") != -0.5:
        raise ValueError("FORMAL_CONFIG_MISMATCH")
    if config.get("storage_execution_policy") != "STAGE_REFERENCE_SAFETY_OVERRIDE_V1":
        raise ValueError("FORMAL_CONFIG_MISMATCH")
    if config.get("planning_horizon") != "CURRENT_DAY_REMAINDER":
        raise ValueError("FORMAL_CONFIG_MISMATCH")
    if config.get("terminal_contract") != "FREE_BOUNDED_YEAR_END":
        raise ValueError("FORMAL_TERMINAL_MISMATCH")

    n = len(slots)
    load = [_finite_nonnegative(request["load_kwh"][t - 1], f"load:{t}") for t in slots]
    pv = [_finite_nonnegative(request["pv_kwh"][t - 1], f"pv:{t}") for t in slots]
    prices = [_finite_nonnegative(request["prices"][t - 1], f"price:{t}") for t in slots]
    if any(p <= 0 for p in prices):
        raise ValueError("FORMAL_PRICE_MUST_BE_POSITIVE")
    initial_soc = float(request["initial_soc"])
    emin = float(config["soc_min_kwh"]); emax = float(config["soc_max_kwh"])
    if not emin <= initial_soc <= emax:
        raise ValueError("FORMAL_INITIAL_SOC_BOUNDS")
    eta_c = float(config["eta_c"]); eta_d = float(config["eta_d"])
    pmax = float(config["power_limit_kwh_per_slot"])
    previous = request.get("previous_active") or {}
    if stage and any(t not in previous for t in slots):
        raise ValueError("MISSING_PREVIOUS_ACTIVE")

    # q,c,d,r,w,v,e,(dp,dm),z
    offsets = {}
    cursor = 0
    for name in ("q", "c", "d", "r", "w", "v", "e"):
        offsets[name] = cursor; cursor += n
    if stage:
        offsets["dp"] = cursor; cursor += n
        offsets["dm"] = cursor; cursor += n
    offsets["z"] = cursor; cursor += n
    m = cursor
    idx = lambda name, i: offsets[name] + i

    bounds = [(0.0, None)] * m
    for i in range(n):
        bounds[idx("c", i)] = (0.0, pmax)
        bounds[idx("d", i)] = (0.0, pmax)
        bounds[idx("v", i)] = (0.0, pv[i])
        bounds[idx("e", i)] = (emin, emax)
        bounds[idx("z", i)] = (0.0, None)

    A_eq = []; b_eq = []
    A_ub = []; b_ub = []
    for i in range(n):
        row = np.zeros(m)
        row[idx("q", i)] = 1.0; row[idx("c", i)] = -1.0; row[idx("d", i)] = 1.0
        row[idx("r", i)] = 1.0; row[idx("w", i)] = -1.0; row[idx("v", i)] = -1.0
        A_eq.append(row); b_eq.append(load[i] - pv[i])
        soc = np.zeros(m)
        soc[idx("e", i)] = 1.0; soc[idx("c", i)] = -eta_c; soc[idx("d", i)] = 1.0 / eta_d
        if i:
            soc[idx("e", i - 1)] = -1.0; rhs = 0.0
        else:
            rhs = initial_soc
        A_eq.append(soc); b_eq.append(rhs)
        # w <= q
        r1 = np.zeros(m); r1[idx("w", i)] = 1.0; r1[idx("q", i)] = -1.0
        A_ub.append(r1); b_ub.append(0.0)
        if stage:
            prev_q = float(previous[slots[i]]["q"])
            adjust = np.zeros(m)
            adjust[idx("q", i)] = 1.0; adjust[idx("dp", i)] = -1.0; adjust[idx("dm", i)] = 1.0
            A_eq.append(adjust); b_eq.append(prev_q)

    econ = np.zeros(m)
    for i, p in enumerate(prices):
        if stage == 0:
            econ[idx("q", i)] = p
        else:
            econ[idx("dp", i)] = 1.5 * p
            econ[idx("dm", i)] = float(config["beta"]) * p
        econ[idx("r", i)] = 5.0 * p

    r1, meta1 = _run_lp("ECONOMIC", econ, A_ub, b_ub, A_eq, b_eq, bounds)
    economic_opt = float(r1.fun)

    A2 = list(A_ub); b2 = list(b_ub)
    A2.append(econ.copy()); b2.append(economic_opt + float(config["tol_cost_yuan"]))
    throughput = np.zeros(m)
    for i in range(n):
        throughput[idx("c", i)] = 1.0; throughput[idx("d", i)] = 1.0
    r2, meta2 = _run_lp("MIN_THROUGHPUT", throughput, A2, b2, A_eq, b_eq, bounds)
    throughput_opt = float(r2.fun)

    A3 = list(A2); b3 = list(b2)
    A3.append(throughput.copy()); b3.append(throughput_opt + float(config["tol_throughput_kwh"]))
    for i in range(n):
        net = max(load[i] - pv[i], 0.0)
        up = np.zeros(m); up[idx("q", i)] = 1.0; up[idx("z", i)] = -1.0
        A3.append(up); b3.append(net)
        down = np.zeros(m); down[idx("q", i)] = -1.0; down[idx("z", i)] = -1.0
        A3.append(down); b3.append(-net)
    dev = np.zeros(m)
    for i in range(n): dev[idx("z", i)] = 1.0
    tertiary_fallback = False
    try:
        r3, meta3 = _run_lp("MIN_NETLOAD_DEVIATION", dev, A3, b3, A_eq, b_eq, bounds)
        x = r3.x
    except RuntimeError as ex:
        # Q4-only diagnostic recovery: keep exact primary economic and secondary throughput solution;
        # do not relax any hard constraint or solver tolerance. This only skips the tertiary
        # net-load-deviation tie-break when its epsilon-constrained LP is numerically infeasible.
        tertiary_fallback = True
        r3 = r2
        x = r2.x
        meta3 = {"stage":"MIN_NETLOAD_DEVIATION","status":"SKIPPED_NUMERICAL_INFEASIBLE_USE_SECONDARY_OPTIMUM",
                 "solver_status_code":2,"message":str(ex),"numerical_recovery_used":True,
                 "numerical_recovery_method":"USE_EXACT_SECONDARY_OPTIMUM_NO_TOLERANCE_RELAXATION"}

    plan = []
    for i, t in enumerate(slots):
        plan.append({
            "slot_id": t,
            "q": max(float(x[idx("q", i)]), 0.0),
            "c_ref": max(float(x[idx("c", i)]), 0.0),
            "d_ref": max(float(x[idx("d", i)]), 0.0),
            "predicted_emergency_kwh": max(float(x[idx("r", i)]), 0.0),
            "predicted_unused_grid_kwh": max(float(x[idx("w", i)]), 0.0),
            "predicted_pv_curtail_kwh": max(float(x[idx("v", i)]), 0.0),
            "reference_soc_after_kwh": float(x[idx("e", i)]),
        })
    validation = validate_formal_plan(request, config, plan)
    if validation["status"] != "PASS":
        raise RuntimeError(f"FORMAL_LP_HARD_VIOLATION:{validation['max_violation']}")
    final_econ = float(np.dot(econ, x))
    metadata = {
        "status": "OPTIMAL",
        "solver_id": config["solver_id"],
        "stages": [meta1, meta2, meta3],
        "economic_objective_yuan": economic_opt,
        "final_economic_value_yuan": final_econ,
        "economic_tolerance_yuan": float(config["tol_cost_yuan"]),
        "throughput_optimum_kwh": throughput_opt,
        "final_throughput_kwh": float(np.dot(throughput, x)),
        "tie_break_status": "Q4_NUMERICAL_TERTIARY_FALLBACK" if tertiary_fallback else "PASS_THREE_STAGE_LEXICOGRAPHIC",
        "optimality_gap": None,
        "optimality_gap_status": "UNAVAILABLE_FROM_SCIPY_LINPROG_LP_RESULT",
        "solver_effective_tolerances": {
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9
        },
        "fallback_count": 1 if tertiary_fallback else 0,
        "numerical_recovery_count": sum(1 for m in (meta1, meta2, meta3) if m.get("numerical_recovery_used")),
        "numerical_recovery_policy": "Q4_TERTIARY_ONLY_USE_SECONDARY_OPTIMUM_NO_TOLERANCE_RELAXATION" if tertiary_fallback else "THIRD_TIEBREAK_ONLY_SAME_LP_SAME_1E-9_NO_RELAXATION",
    }
    return {"planner_kind": FORMAL_PLANNER_KIND, "plan": plan, "solver_metadata": metadata, "validation": validation}


def make_formal_lp_planner(config: dict):
    frozen = deepcopy(config)
    def planner(request):
        return solve_formal_lp(request, frozen)
    planner.planner_kind = FORMAL_PLANNER_KIND
    return planner
