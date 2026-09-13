"""Independent validator for the R5.4 formal 334-day annual lane.

This module intentionally does not import ``engine`` or ``ledger``.  It replays
serialized run evidence, recomputes accounting, state transitions, chronology,
and formal solver metadata from first principles.
"""
from __future__ import annotations

import math
from datetime import timedelta

from .common import digest, instant, start


def validate_formal_run(result: dict) -> dict:
    checks = []
    failures = []
    hard_max = 0.0
    hard_argmax = None
    known_at_violation = 0.0
    past_mutation_count = 0
    accounting_residual = 0.0
    stage_soc_residual = 0.0

    def check(name: str, ok: bool, *, value=None, tolerance=None, detail=None, argmax=None):
        nonlocal hard_max, hard_argmax
        status = "PASS" if ok else "FAIL"
        item = {"check": name, "status": status}
        if value is not None:
            item["max_violation"] = float(value)
        if tolerance is not None:
            item["tolerance"] = float(tolerance)
        if detail is not None:
            item["detail"] = detail
        if argmax is not None:
            item["argmax_location"] = argmax
        checks.append(item)
        if not ok:
            failures.append(item)
        if value is not None and math.isfinite(float(value)) and float(value) > hard_max:
            hard_max = float(value)
            hard_argmax = argmax or {"check": name}

    try:
        cfg = result["config"]
        trace = result["trace"]
        events = result["events"]
        calls = result["stage_calls"]
        source = result["source_inputs"]
        day = result["date"]
        strategy = cfg.get("strategy_id")
        expected_stages = [0] if strategy == "B0" else [0, 6, 12, 18] if strategy in ("B1A", "B1B") else [0, 6, 12] if strategy == "B1B_NO18" else None
        check("AUTH_SCOPE_FORMAL", result.get("scope") == "FORMAL_SCREENING")
        check("AUTH_FORMAL_RESULT", result.get("formal_result") is True)
        check("CONFIG_RUN_CLASS", cfg.get("run_class") == "FORMAL")
        check("CONFIG_STRATEGY", expected_stages is not None)
        check("CONFIG_STAGE_SET", result.get("update_stages") == expected_stages == cfg.get("update_stages"))
        check("CONFIG_TERMINAL", cfg.get("terminal_contract") == "FREE_BOUNDED_YEAR_END")
        check("CONFIG_NO_FALLBACK", cfg.get("fallback") == "FORBIDDEN")
        check("TRACE_144", len(trace) == 144 and [r.get("slot_id") for r in trace] == list(range(1, 145)))
        check("EVENT_CALL_COUNT", len(events) == len(calls) == len(expected_stages or []))
        initial_soc_value = float(result["initial_soc"])
        check("INITIAL_SOC_ANNUAL_BOUNDS", 1200.0 - 1e-12 <= initial_soc_value <= 10800.0 + 1e-12,
              value=max(1200.0 - initial_soc_value, initial_soc_value - 10800.0, 0.0), tolerance=1e-12)
        check("PRICE_144", len(source["prices"]) == 144)
        check("ACTUAL_144", len(source["actual_rows"]) == 144)
        check("LOAD_144", len(source["load_forecast"]["values"]) == 144)

        beta = float(cfg["beta"])
        eta_c = float(cfg["eta_c"])
        eta_d = float(cfg["eta_d"])
        emin = float(cfg["soc_min_kwh"])
        emax = float(cfg["soc_max_kwh"])
        pmax = float(cfg["power_limit_kwh_per_slot"])
        tol = float(cfg.get("hard_tolerance", 1e-7))

        active = {}
        states_at_stage = {}
        base_cost = 0.0
        adjustment_cost = 0.0
        adjustment_up_kwh = 0.0
        adjustment_down_kwh = 0.0
        adjustment_up_cost = 0.0
        adjustment_down_credit = 0.0
        solver_runtime = 0.0

        for idx, stage in enumerate(expected_stages or []):
            event = events[idx]
            call = calls[idx]
            decision = start(day) + timedelta(hours=stage)
            expected_slots = list(range(stage * 6 + 1, 145))
            rows = event.get("rows", [])
            check(f"STAGE_{stage:02d}_IDENTITY", event.get("stage") == call.get("stage") == stage)
            check(f"STAGE_{stage:02d}_FUTURE_ONLY", [r.get("slot_id") for r in rows] == expected_slots)
            check(f"STAGE_{stage:02d}_REQUEST_FUTURE", call.get("request", {}).get("future_slots") == expected_slots)
            prefix_expected = digest(trace[: stage * 6])
            prefix_actual = call.get("executed_prefix_hash")
            prefix_ok = prefix_expected == prefix_actual
            if not prefix_ok:
                past_mutation_count += 1
            check(f"STAGE_{stage:02d}_PAST_IMMUTABLE", prefix_ok, detail=None if prefix_ok else {
                "expected_prefix_hash": prefix_expected, "actual_prefix_hash": prefix_actual
            })

            state_expected = float(result["initial_soc"]) if stage == 0 else float(trace[stage * 6 - 1]["e_after"])
            state_resid = max(abs(float(call.get("initial_soc")) - state_expected),
                              abs(float(call.get("request", {}).get("initial_soc")) - state_expected))
            stage_soc_residual = max(stage_soc_residual, state_resid)
            check(f"STAGE_{stage:02d}_SOC_CONTINUITY", state_resid <= tol,
                  value=state_resid, tolerance=tol, argmax={"date": day, "stage": stage})

            req = call["request"]
            dep = instant(req["dependency_known_at"])
            dec = instant(req["decision_time"])
            leakage = max((dep - dec).total_seconds(), 0.0)
            known_at_violation = max(known_at_violation, leakage)
            check(f"STAGE_{stage:02d}_KNOWN_AT", leakage == 0.0,
                  value=leakage, tolerance=0.0, argmax={"date": day, "stage": stage})
            check(f"STAGE_{stage:02d}_DECISION_TIME", dec == decision)
            check(f"STAGE_{stage:02d}_PLANNER_KIND", call.get("planner_kind") == "FORMAL_LP")
            check(f"STAGE_{stage:02d}_SOLVER_STATUS", call.get("solver_status") == "OPTIMAL")
            meta = call.get("solver_metadata") or {}
            check(f"STAGE_{stage:02d}_META_STATUS", meta.get("status") == "OPTIMAL")
            check(f"STAGE_{stage:02d}_GAP_UNAVAILABLE",
                  meta.get("optimality_gap") is None and meta.get("optimality_gap_status") == "UNAVAILABLE_FROM_SCIPY_LINPROG_LP_RESULT")
            eff = meta.get("solver_effective_tolerances") or {}
            check(f"STAGE_{stage:02d}_SOLVER_TOLERANCE",
                  eff.get("primal_feasibility_tolerance") == 1e-9 and eff.get("dual_feasibility_tolerance") == 1e-9)
            check(f"STAGE_{stage:02d}_NO_FALLBACK", meta.get("fallback_count") == 0)
            check(f"STAGE_{stage:02d}_TIEBREAK", meta.get("tie_break_status") == "PASS_THREE_STAGE_LEXICOGRAPHIC")
            solver_runtime += float(call.get("runtime_seconds", 0.0))
            planner_val = call.get("planner_validation") or {}
            pv = source["pv_forecasts"].get(stage, source["pv_forecasts"].get(str(stage)))
            check(f"STAGE_{stage:02d}_PLANNER_VALIDATION", planner_val.get("status") == "PASS")
            pv_leak = max((instant(pv["known_at"]) - decision).total_seconds(), 0.0)
            load_leak = max((instant(source["load_forecast"]["known_at"]) - decision).total_seconds(), 0.0)
            known_at_violation = max(known_at_violation, pv_leak, load_leak)
            check(f"STAGE_{stage:02d}_SOURCE_KNOWN_AT", max(pv_leak, load_leak) == 0.0,
                  value=max(pv_leak, load_leak), tolerance=0.0, argmax={"date": day, "stage": stage})

            saved_prev = {int(k): v for k, v in req.get("previous_active", {}).items()}
            if stage == 0:
                check("B0_OR_BASE_PREVIOUS_EMPTY", saved_prev == {})
            else:
                prev_match = all(t in active and t in saved_prev and abs(float(active[t]["q"]) - float(saved_prev[t]["q"])) <= 1e-12
                                 for t in expected_slots)
                check(f"STAGE_{stage:02d}_PREVIOUS_ACTIVE", prev_match)

            for row in rows:
                t = int(row["slot_id"])
                p = float(source["prices"][t - 1])
                q = float(row["new_active_q"])
                ledger_fee = float(row["fee_delta"])
                if stage == 0:
                    expected_fee = p * q
                    base_cost += expected_fee
                    check(f"LEDGER_BASE_DELTA_NULL_{t}", row.get("previous_active_q") is None and row.get("delta_plus") is None and row.get("delta_minus") is None)
                else:
                    prev_q = float(active[t]["q"])
                    plus = max(q - prev_q, 0.0)
                    minus = max(prev_q - q, 0.0)
                    expected_fee = p * (1.5 * plus + beta * minus)
                    adjustment_cost += expected_fee
                    adjustment_up_kwh += plus
                    adjustment_down_kwh += minus
                    adjustment_up_cost += 1.5 * p * plus
                    adjustment_down_credit += -beta * p * minus
                    check(f"LEDGER_PREVIOUS_{stage}_{t}", abs(float(row["previous_active_q"]) - prev_q) <= tol)
                    check(f"LEDGER_DELTA_{stage}_{t}", max(abs(float(row["delta_plus"]) - plus), abs(float(row["delta_minus"]) - minus)) <= tol)
                fee_resid = abs(ledger_fee - expected_fee)
                accounting_residual = max(accounting_residual, fee_resid)
                check(f"LEDGER_FEE_{stage}_{t}", fee_resid <= max(1e-6, 1e-10 * abs(expected_fee)),
                      value=fee_resid, tolerance=max(1e-6, 1e-10 * abs(expected_fee)))
                active[t] = {
                    "q": q,
                    "c_ref": float(row["c_ref"]),
                    "d_ref": float(row["d_ref"]),
                    "base_q": float(row["base_q"]),
                    "event_id": event["event_id"],
                }
            states_at_stage[stage] = {k: dict(v) for k, v in active.items()}

        e = float(result["initial_soc"])
        parent = result["initial_state_hash"]
        emergency_cost = 0.0
        emergency_energy = 0.0
        soc_min = e
        soc_max = e
        trace_hard_max = 0.0
        trace_hard_argmax = None
        fallback_count = 0
        stage_list = expected_stages or []
        for row, actual in zip(trace, source["actual_rows"]):
            t = int(row["slot_id"])
            stage = max(h for h in stage_list if h * 6 < t)
            ref = states_at_stage[stage][t]
            p = float(source["prices"][t - 1])
            l = float(row["actual_L"])
            s = float(row["actual_S"])
            q = float(row["q"])
            c = float(row["c"])
            d = float(row["d"])
            r = float(row["r"])
            w = float(row["w"])
            v = float(row["v"])
            end = start(day) + timedelta(minutes=10 * t)
            check(f"TRACE_TIME_{t}", row["delivery_end"] == end.isoformat() and row["actual_available_at"] == end.isoformat())
            check(f"TRACE_ACTUAL_SOURCE_{t}", abs(l - float(actual["load_kwh"])) <= tol and abs(s - float(actual["pv_kwh"])) <= tol)
            check(f"TRACE_ACTIVE_REF_{t}", abs(q - ref["q"]) <= tol and abs(float(row["c_ref"]) - ref["c_ref"]) <= tol and abs(float(row["d_ref"]) - ref["d_ref"]) <= tol)
            if row.get("fallback_reason") is not None:
                fallback_count += 1

            balance = q + s - l
            c_expected = min(ref["c_ref"], balance, pmax, max((emax - e) / eta_c, 0.0)) if balance >= 0 else 0.0
            d_expected = min(ref["d_ref"], -balance, pmax, max(eta_d * (e - emin), 0.0)) if balance < 0 else 0.0
            r_expected = max(l + c - q - s - d, 0.0)
            unused = max(q + s + d - l - c, 0.0)
            w_expected = min(q, unused)
            v_expected = unused - w_expected
            next_e = e + eta_c * c - d / eta_d
            residuals = {
                "safety": max(abs(c - c_expected), abs(d - d_expected)),
                "balance_kwh": abs(q - w + r + s + d - l - c - v),
                "emergency": abs(r - r_expected),
                "split": max(abs(w - w_expected), abs(v - v_expected)),
                "soc_recursion": abs(float(row["e_after"]) - next_e),
                "soc_continuity": abs(float(row["e_before"]) - e),
                "soc_bounds": max(emin - next_e, next_e - emax, 0.0),
                "simultaneous_cd": min(c, d),
                "emergency_charge_overlap": min(r, c),
                "parent_hash": 0.0 if row.get("parent_state_hash") == parent else float("inf"),
            }
            local = max(v for v in residuals.values() if math.isfinite(v))
            if local > trace_hard_max:
                trace_hard_max = local
                trace_hard_argmax = {"date": day, "slot": t, "stage": stage, "components": residuals}
            check(f"TRACE_HARD_{t}", all((math.isfinite(x) and x <= tol) for x in residuals.values()),
                  value=local, tolerance=tol, argmax={"date": day, "slot": t, "stage": stage})
            em_expected = 5.0 * p * r
            em_resid = abs(float(row["cost_emergency"]) - em_expected)
            accounting_residual = max(accounting_residual, em_resid)
            check(f"TRACE_EMERGENCY_COST_{t}", em_resid <= max(1e-6, 1e-10 * abs(em_expected)),
                  value=em_resid, tolerance=max(1e-6, 1e-10 * abs(em_expected)))
            emergency_cost += em_expected
            emergency_energy += r
            e = next_e
            soc_min = min(soc_min, e)
            soc_max = max(soc_max, e)
            parent = digest(row)

        final_resid = abs(e - float(result["final_soc"]))
        check("FINAL_SOC", final_resid <= tol, value=final_resid, tolerance=tol)
        check("FINAL_STATE_HASH", parent == result["final_state_hash"])
        check("NO_FALLBACK_TRACE", fallback_count == 0, detail={"fallback_count": fallback_count} if fallback_count else None)
        if strategy == "B0":
            check("B0_INTRADAY_ADJUSTMENT_ZERO", adjustment_up_kwh == 0.0 and adjustment_down_kwh == 0.0)

        total_cost = math.fsum([base_cost, adjustment_cost, emergency_cost])
        cash_tolerance = max(1e-6, 1e-10 * abs(total_cost))
        hard_max = max(hard_max, trace_hard_max, stage_soc_residual)
        if trace_hard_max >= hard_max:
            hard_argmax = trace_hard_argmax
        status = "PASS" if not failures else "FAIL"
        metrics = {
            "base_planned_cost_yuan": base_cost,
            "adjustment_cost_yuan": adjustment_cost,
            "adjustment_up_kwh": adjustment_up_kwh,
            "adjustment_up_cost_yuan": adjustment_up_cost,
            "adjustment_down_kwh": adjustment_down_kwh,
            "adjustment_down_credit_yuan": adjustment_down_credit,
            "intraday_adjustment_kwh": adjustment_up_kwh + adjustment_down_kwh,
            "emergency_cost_yuan": emergency_cost,
            "emergency_energy_kwh": emergency_energy,
            "total_cost_yuan": total_cost,
            "terminal_soc_kwh": e,
            "soc_min_kwh": soc_min,
            "soc_max_kwh": soc_max,
            "hard_violation_max": hard_max,
            "hard_violation_argmax": hard_argmax,
            "known_at_violation_seconds": known_at_violation,
            "past_mutation_count": past_mutation_count,
            "accounting_residual_yuan": accounting_residual,
            "stage_soc_continuity_residual_kwh": stage_soc_residual,
            "cash_tolerance_yuan": cash_tolerance,
            "solver_runtime_seconds": solver_runtime,
            "wall_runtime_seconds": float(result.get("runtime_seconds", 0.0)),
            "fallback_count": fallback_count,
        }
    except Exception as exc:
        checks.append({"check": "VALIDATOR_EXCEPTION", "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"})
        failures.append(checks[-1])
        status = "FAIL"
        metrics = {
            "hard_violation_max": float("inf"),
            "known_at_violation_seconds": float("inf"),
            "past_mutation_count": past_mutation_count,
            "accounting_residual_yuan": float("inf"),
        }

    return {
        "schema": "Q3_FORMAL334_INDEPENDENT_DAY_VALIDATOR_R5_4_V1",
        "status": status,
        "date": result.get("date") if isinstance(result, dict) else None,
        "strategy": (result.get("config") or {}).get("strategy_id") if isinstance(result, dict) else None,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "metrics": metrics,
    }
