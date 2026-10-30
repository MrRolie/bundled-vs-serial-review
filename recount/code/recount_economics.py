"""recount_economics.py — the independent recount's step A9: blind recount of the
economics co-axis (registration §6 / §6a / §11.3) from the per-dispatch trial records +
the recount's own V1 statuses (recount/recount-rows.jsonl).

Fresh code. Written WITHOUT opening the original analysis's costs/descriptives artifacts
or its costs.py / descriptives.py (the blind list for A9).

PUBLIC RE-RUN: this copy reads the public dispatch tables (data/dispatches/), which keep
every field it uses except two bookkeeping fields of the grouped-order probes (`lane`,
`regime.n_per_cell`), reported as null here. Run from the repository root:
    python recount/code/recount_economics.py OUT.json
and compare OUT.json with recount/recount-economics.json (identical except those two
probe fields).

Definitions (from rules text; every choice is stated below and in methods/RECOUNT.md; the
recount's private blind-pass notes are not published):
  cell            = tier x arm.  Units: P and Sq = one record per item x rep (a bundle /
                    a 5-turn session); S = one record per (item, rep, family) question.
  dispatches      = P: 1/record; S: 1/record; Sq: 5/record (turns).
  realized USD    = sum of the record's `total_cost_usd` (P, S: the dispatch's figure;
                    Sq: the session figure, which equals the sum of per-turn `cost_usd`
                    on every session — asserted below).  This is the CLI-computed figure
                    (§16: "the JSONL cost total is a floor — the key console is the
                    meter of record").
  token fields    = input_tokens, cache_creation_input_tokens, cache_read_input_tokens,
                    output_tokens (Sq: summed over turns).
  cache-cold USD  = (input + cache_creation + cache_read) * p_in + output * p_out  (§6a ii:
                    "token splits at list prices, no cache credit"), computed under TWO
                    price tables because the prereg pins none:
                      LIST  = provider list per the claude-api reference (cached 2026-06-24):
                              haiku 1/5, sonnet-5 2/10, opus-5 5/25 ($/MTok in/out)
                      CLI   = the table the frozen CLI 2.1.212 demonstrably used to compute
                              `total_cost_usd` (fit below): haiku 1/5, sonnet-5 3/15, opus-5 5/25
                    Cache multipliers for the realized-fit check: write 1.25x, read 0.1x.
  true catches    = recount V1 CATCH rows with role == target in the cell (recount-rows.jsonl);
                    denominator pool = the audit-surviving defective items (haiku 60 items x r3
                    = 180 target rows; C44 defective 36 x r3 = 108 at sonnet; 36 x r4 = 144 at opus).
  $/true-catch    = cell USD / cell true catches (whole-cell numerator: every dispatch the arm
                    made, clean items included — a reviewer pays for clean code too).
                    Secondary: defective-items-only numerator.
  equal-dollars   = per tier, S vs P (and Sq vs P): dUSD = USD_S - USD_P; dC = C_S - C_P;
                    P catches/$ = C_P / USD_P; extra P reps the same dUSD buys = dUSD / (USD_P / r_P);
                    catches bought = dUSD * C_P / USD_P (LINEAR in reps, per §6 wording).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]  # repository root
DATA = ROOT / "data" / "dispatches"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("recount-economics.rerun.json")

TIERS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
}
PRICE_LIST = {"haiku": (1.0, 5.0), "sonnet": (2.0, 10.0), "opus": (5.0, 25.0)}   # $/MTok in, out
PRICE_CLI = {"haiku": (1.0, 5.0), "sonnet": (3.0, 15.0), "opus": (5.0, 25.0)}
CW_MULT, CR_MULT = 1.25, 0.10
TOK = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]


def realized_formula(u: dict, pin: float, pout: float) -> float:
    """What the CLI would compute from the unit's token fields at (pin, pout) with cache multipliers."""
    return (u["input_tokens"] * pin + u["cache_creation_input_tokens"] * CW_MULT * pin
            + u["cache_read_input_tokens"] * CR_MULT * pin + u["output_tokens"] * pout) / 1e6


def cache_cold(tok: dict, pin: float, pout: float) -> float:
    return ((tok["input_tokens"] + tok["cache_creation_input_tokens"] + tok["cache_read_input_tokens"]) * pin
            + tok["output_tokens"] * pout) / 1e6


def load_cells() -> tuple[dict, dict]:
    cells: dict[tuple[str, str], dict] = {}
    checks: dict[str, dict] = {}
    for tier, model in TIERS.items():
        recs = read_jsonl(DATA / f"{model}.jsonl")
        assert all(r["model_id"] == model for r in recs)
        assert not any(r.get("is_error") for r in recs)
        assert len(recs) == len({(r["arm"], r["item"], r["rep"], r.get("family")) for r in recs}), "duplicate keys"
        sq_gap, sq_turns, sq_turn_err = 0.0, Counter(), 0
        fit_resid: dict[str, list[float]] = defaultdict(list)
        single_served: dict[str, list[float]] = defaultdict(list)
        pin_c, pout_c = PRICE_CLI[tier]
        for r in recs:
            arm = r["arm"]
            c = cells.setdefault((tier, arm), {"tier": tier, "arm": arm, "model_id": model, "records": 0,
                                               "dispatches": 0, "realized_usd": 0.0,
                                               "tokens": {k: 0 for k in TOK}, "items": set(),
                                               "per_item": defaultdict(float), "reps": set()})
            c["records"] += 1
            c["items"].add(r["item"]); c["reps"].add(r["rep"])
            c["realized_usd"] += r["total_cost_usd"]
            c["per_item"][r["item"]] += r["total_cost_usd"]
            if arm == "Sq":
                turns = r["turns"]
                sq_turns[len(turns)] += 1
                sq_turn_err += sum(1 for t in turns if t.get("is_error") or t.get("rc") != 0)
                sq_gap = max(sq_gap, abs(r["total_cost_usd"] - sum(t["cost_usd"] for t in turns)))
                c["dispatches"] += len(turns)
                for t in turns:
                    for k in TOK:
                        c["tokens"][k] += t[k]
                    fit_resid[arm].append(t["cost_usd"] - realized_formula(t, pin_c, pout_c))
                    if len(t.get("served_models") or []) == 1:
                        single_served[arm].append(t["cost_usd"] - realized_formula(t, pin_c, pout_c))
            else:
                c["dispatches"] += 1
                for k in TOK:
                    c["tokens"][k] += r[k]
                res = r["total_cost_usd"] - realized_formula(r, pin_c, pout_c)
                fit_resid[arm].append(res)
                if len(r.get("served_models") or []) == 1:
                    single_served[arm].append(res)
        # price-table validation: residual of the CLI table vs recorded; list table for contrast
        pin_l, pout_l = PRICE_LIST[tier]
        alt = defaultdict(list)
        for r in recs:
            units = r["turns"] if r["arm"] == "Sq" else [r]
            for u in units:
                cost = u["cost_usd"] if r["arm"] == "Sq" else u["total_cost_usd"]
                alt[r["arm"]].append(cost - realized_formula(u, pin_l, pout_l))
        checks[tier] = {
            "n_records": len(recs),
            "sq_sessions_by_turn_count": dict(sq_turns),
            "sq_turn_errors": sq_turn_err,
            "sq_max_abs_gap_session_total_vs_sum_turn_cost": sq_gap,
            "cli_table_used": {"in_per_mtok": pin_c, "out_per_mtok": pout_c, "cw_mult": CW_MULT, "cr_mult": CR_MULT},
            "cli_table_residual_usd_per_dispatch": {
                a: {"n": len(v), "mean": float(np.mean(v)), "median": float(np.median(v)), "sd": float(np.std(v)),
                    "min": float(np.min(v)), "max": float(np.max(v)), "sum": float(np.sum(v))}
                for a, v in fit_resid.items()},
            "single_served_model_units_residual": {
                a: {"n": len(v), "max_abs": float(np.max(np.abs(v))) if v else None} for a, v in single_served.items()},
            "list_table": {"in_per_mtok": pin_l, "out_per_mtok": pout_l},
            "list_table_residual_usd_per_dispatch": {
                a: {"mean": float(np.mean(v)), "sd": float(np.std(v)), "min": float(np.min(v)), "max": float(np.max(v))}
                for a, v in alt.items()},
        }
    return cells, checks


def load_catches() -> dict[tuple[str, str], dict]:
    rows = read_jsonl(ROOT / "recount" / "recount-rows.jsonl")
    out: dict[tuple[str, str], dict] = {}
    for r in rows:
        k = (r["tier"], r["arm"])
        d = out.setdefault(k, {"target_rows": 0, "catches_v1": 0, "catches_v2": 0, "catches_v3": 0,
                               "target_items": set(), "rows": 0})
        d["rows"] += 1
        if r["role"] == "target":
            d["target_rows"] += 1
            d["target_items"].add(r["item"])
            for v in ("v1", "v2", "v3"):
                d[f"catches_{v}"] += int(r[f"status_{v}"] == "CATCH")
    return out


def main() -> int:
    cells, checks = load_cells()
    catches = load_catches()
    rep_count = {"haiku": 3, "sonnet": 3, "opus": 4}
    table = {}
    for (tier, arm), c in sorted(cells.items()):
        k = f"{tier}/{arm}"
        cat = catches[(tier, arm)]
        r = rep_count[tier]
        assert c["reps"] == set(range(r)), (tier, arm, c["reps"])
        target_items = cat["target_items"]
        usd_def_only = sum(v for it, v in c["per_item"].items() if it in target_items)
        tok = c["tokens"]
        tot_tokens = sum(tok.values())
        C = cat["catches_v1"]
        pin_l, pout_l = PRICE_LIST[tier]; pin_c, pout_c = PRICE_CLI[tier]
        cc_list = cache_cold(tok, pin_l, pout_l); cc_cli = cache_cold(tok, pin_c, pout_c)
        helper_overhead = checks[tier]["cli_table_residual_usd_per_dispatch"][arm]["sum"]
        table[k] = {
            "tier": tier, "arm": arm, "model_id": c["model_id"],
            "units_records": c["records"], "dispatches": c["dispatches"],
            "unit_kind": {"P": "item x rep bundle (1 dispatch)", "S": "per-question dispatch",
                          "Sq": "item x rep session (5 turns = 5 dispatches)"}[arm],
            "item_reps": c["records"] if arm != "S" else c["records"] // 5,
            "items_in_cell": len(c["items"]), "target_items": len(target_items), "reps": r,
            "realized_usd": c["realized_usd"],
            "realized_usd_defective_items_only": usd_def_only,
            "realized_usd_per_dispatch": c["realized_usd"] / c["dispatches"],
            "realized_usd_per_item_rep": c["realized_usd"] / (c["records"] if arm != "S" else c["records"] // 5),
            "tokens": tok, "tokens_total": tot_tokens,
            "target_rows": cat["target_rows"],
            "true_catches_v1": C, "true_catches_v2": cat["catches_v2"], "true_catches_v3": cat["catches_v3"],
            "catch_rate_v1": C / cat["target_rows"],
            "usd_per_true_catch_realized": c["realized_usd"] / C if C else None,
            "usd_per_true_catch_realized_defective_only": usd_def_only / C if C else None,
            "tokens_per_true_catch": tot_tokens / C if C else None,
            "output_tokens_per_true_catch": tok["output_tokens"] / C if C else None,
            "cache_cold_usd_LIST": cc_list, "usd_per_true_catch_cache_cold_LIST": cc_list / C if C else None,
            "cache_cold_usd_CLI": cc_cli, "usd_per_true_catch_cache_cold_CLI": cc_cli / C if C else None,
            "cache_cold_over_realized_LIST": cc_list / c["realized_usd"],
            "cache_cold_over_realized_CLI": cc_cli / c["realized_usd"],
            "helper_call_overhead_usd_sum": helper_overhead,
            "helper_call_overhead_share_of_realized": helper_overhead / c["realized_usd"],
        }
    # LIST-repriced realized: subject-model part rescaled by (list/cli) with the helper overhead kept as recorded
    for k, row in table.items():
        tier = row["tier"]
        pin_l, pout_l = PRICE_LIST[tier]; pin_c, pout_c = PRICE_CLI[tier]
        subject_part = row["realized_usd"] - row["helper_call_overhead_usd_sum"]
        scale = pin_l / pin_c  # same ratio for out (2/3 at sonnet; 1 elsewhere)
        assert abs(pout_l / pout_c - scale) < 1e-12
        row["realized_usd_LIST_repriced"] = subject_part * scale + row["helper_call_overhead_usd_sum"]
        row["usd_per_true_catch_realized_LIST_repriced"] = (row["realized_usd_LIST_repriced"] / row["true_catches_v1"]
                                                            if row["true_catches_v1"] else None)

    # equal-dollars reads
    eq = {}
    for tier in TIERS:
        P = table[f"{tier}/P"]
        for arm in ("S", "Sq"):
            if f"{tier}/{arm}" not in table:
                continue
            A = table[f"{tier}/{arm}"]
            for basis, key in (("realized", "realized_usd"), ("realized_LIST_repriced", "realized_usd_LIST_repriced"),
                               ("cache_cold_LIST", "cache_cold_usd_LIST"), ("cache_cold_CLI", "cache_cold_usd_CLI")):
                dusd = A[key] - P[key]
                dC = A["true_catches_v1"] - P["true_catches_v1"]
                p_cpd = P["true_catches_v1"] / P[key]
                p_per_rep = P[key] / P["reps"]
                eq[f"{tier}/{arm}-vs-P/{basis}"] = {
                    "tier": tier, "arm": arm, "basis": basis,
                    "usd_P": P[key], "usd_arm": A[key], "marginal_usd_arm_over_P": dusd,
                    "catches_P": P["true_catches_v1"], "catches_arm": A["true_catches_v1"], "marginal_catches": dC,
                    "arm_marginal_catches_per_marginal_usd": dC / dusd if dusd else None,
                    "P_catches_per_usd": p_cpd, "arm_catches_per_usd": A["true_catches_v1"] / A[key],
                    "P_usd_per_rep": p_per_rep, "P_catches_per_rep": P["true_catches_v1"] / P["reps"],
                    "extra_P_reps_same_usd": dusd / p_per_rep,
                    "catches_same_usd_buys_as_P_reps_linear": dusd * p_cpd,
                    "arm_marginal_catches_minus_P_reps_catches": dC - dusd * p_cpd,
                    "usd_ratio_arm_over_P": A[key] / P[key],
                }

    # grouped-order probe anchors (raw; cache-grouped reconstruction NOT performed here)
    probes = {}
    for tier, model in TIERS.items():
        pr = read_jsonl(DATA / f"{model}.grouped-probe.jsonl")
        probes[tier] = {"n": len(pr), "items": sorted({r["item"] for r in pr}), "lane": None,
                        "sum_usd": sum(r["total_cost_usd"] for r in pr),
                        "mean_usd_per_dispatch": sum(r["total_cost_usd"] for r in pr) / len(pr),
                        "cache_read_tokens_total": sum(r["cache_read_input_tokens"] for r in pr),
                        "cache_creation_tokens_total": sum(r["cache_creation_input_tokens"] for r in pr),
                        "regime_n_per_cell": None}

    totals = {"realized_usd_all_cells": sum(r["realized_usd"] for r in table.values()),
              "realized_usd_by_tier": {t: sum(r["realized_usd"] for r in table.values() if r["tier"] == t) for t in TIERS},
              "records_all": sum(r["units_records"] for r in table.values()),
              "dispatches_all": sum(r["dispatches"] for r in table.values()),
              "true_catches_v1_all": sum(r["true_catches_v1"] for r in table.values())}
    out = {"meta": {"module": "recount_economics.py", "phase": "A (blind)", "date": "2026-08-28",
                    "price_tables": {"LIST": PRICE_LIST, "CLI_implied": PRICE_CLI, "cache_write_mult": CW_MULT,
                                     "cache_read_mult": CR_MULT},
                    "inputs": ["per-dispatch trial records (public subset: data/dispatches/)",
                               "grouped-order probe records (data/dispatches/)",
                               "recount/recount-rows.jsonl (the recount V1 statuses)"],
                    "not_opened": ["costs-v2.json", "costs.json", "descriptives-v2.json",
                                   "analysis/costs.py", "analysis/descriptives.py"]},
           "instrument_checks": checks, "cells": table, "equal_dollars": eq, "grouped_probe_anchors": probes,
           "totals": totals}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    # console summary
    print(f"wrote {OUT}")
    for k, r in table.items():
        print(f"{k:12s} rec={r['units_records']:5d} disp={r['dispatches']:5d} USD={r['realized_usd']:8.4f} "
              f"C={r['true_catches_v1']:3d}/{r['target_rows']} $/C={r['usd_per_true_catch_realized']:.4f} "
              f"cold_LIST={r['cache_cold_usd_LIST']:8.4f} cold_CLI={r['cache_cold_usd_CLI']:8.4f} "
              f"helper={r['helper_call_overhead_usd_sum']:.4f} ({r['helper_call_overhead_share_of_realized']:.3f})")
    for k, e in eq.items():
        if e["basis"] == "realized":
            print(f"{k:32s} dUSD={e['marginal_usd_arm_over_P']:8.4f} dC={e['marginal_catches']:4d} "
                  f"dC/d$={e['arm_marginal_catches_per_marginal_usd'] if e['arm_marginal_catches_per_marginal_usd'] is not None else float('nan'):8.3f} "
                  f"P C/$={e['P_catches_per_usd']:7.3f} extraPreps={e['extra_P_reps_same_usd']:6.2f} "
                  f"Pbuys={e['catches_same_usd_buys_as_P_reps_linear']:7.2f} net={e['arm_marginal_catches_minus_P_reps_catches']:7.2f}")
    print(json.dumps(totals, indent=1))
    for t, c in checks.items():
        print(t, "sq gap", c["sq_max_abs_gap_session_total_vs_sum_turn_cost"], "turns", c["sq_sessions_by_turn_count"],
              "resid(CLI table):", {a: (round(v["mean"], 6), round(v["min"], 6), round(v["max"], 6)) for a, v in c["cli_table_residual_usd_per_dispatch"].items()},
              "single-served max|res|:", {a: v["max_abs"] for a, v in c["single_served_model_units_residual"].items()})
    for t, p in probes.items():
        print("probe", t, p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
