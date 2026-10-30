"""descriptives.py — §11.3's registered descriptive/exploratory reads
(CI only, labeled; never Holm'd). Parsing rides answer_parser,
contrasts ride stats, composed statuses come from the final rows —
this file adds joins and counting only.

Reads emitted (each labeled with its registered clause):
  * catch decomposition — unconditional (the primary, deployment-real)
    vs conditional-on-well-formed (strict-PARSED target rows only);
  * S−Sq at haiku and sonnet — LABELED the compound
    (repetition − self-anchoring), never "the repetition component" (D-1);
  * Sq−P at sonnet (CI only);
  * the sonnet−opus gradient leg: (S−P)_sonnet − (S−P)_opus over C44,
    shared item draw;
  * turn-1 anchor check — Sq target-question rows WHERE the target
    family was turn 1 (the recorded turn order), vs S (instrument
    check, n stated);
  * within-P position-in-bundle slope — target catch rate by the target
    question's position in the recorded bundle order;
  * per-item FLAG-count distribution per arm×tier (the
    allocation/satisficing signature): FLAG verdicts per response —
    strict verdict, else loose, else the adjudicated verdict;
  * HIT-ALT rates (§5.3);
  * per-family heterogeneity — scoped to HAIKU (D-11);
  * within-P and within-Sq conditional error correlation,
    operationalization stated in the output: mean pairwise Pearson phi
    between question-level error indicators (target NON-CATCH / off FA)
    within a response, against the between-response baseline.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parent
for _p in (str(_HERE), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from answer_parser import FAMILIES, parse_response  # noqa: E402
from scorer import sq_turn_text, trial_text  # noqa: E402
from stats import bootstrap_contrast, bootstrap_delta  # noqa: E402
from endpoints import (  # noqa: E402
    TIER_HAIKU,
    TIER_OPUS,
    TIER_SONNET,
    read_jsonl,
    target_pairs,
)

TIERS = (TIER_HAIKU, TIER_SONNET, TIER_OPUS)


# ---------------------------------------------------------------- verdicts
def row_verdict(row: Mapping, texts: Mapping[tuple, str]) -> str | None:
    """FLAG/NONE/None per question-row: strict verdict, else loose, else
    the adjudicated verdict (NEITHER → None)."""
    adj = row.get("adjudicated")
    if adj:
        return adj["verdict"] if adj["verdict"] in ("FLAG", "NONE") else None
    text = texts[(row["tier"], row["arm"], row["item"], row["rep"])] \
        if row["arm"] != "Sq" else texts[
            (row["tier"], row["arm"], row["item"], row["rep"], row["family"])]
    for variant in ("strict", "loose"):
        entry = parse_response(text, [row["family"]], variant=variant)[row["family"]]
        if entry["status"] == "PARSED":
            return entry["verdict"]
    return None


def load_texts(data_dir: Path) -> dict:
    texts = {}
    for tier in TIERS:
        for rec in read_jsonl(data_dir / f"{tier}.jsonl"):
            if rec["arm"] == "Sq":
                for t in rec["turns"]:
                    texts[(tier, "Sq", rec["item"], rec["rep"], t["family"])] = \
                        sq_turn_text(rec, t["family"])
            else:
                texts[(tier, rec["arm"], rec["item"], rec["rep"])] = trial_text(rec)
    return texts


# ---------------------------------------------------------------- orders
RANDOMIZATION_SEED = 1512  # registration §7


def keyed_question_order(item_id: str, rep: int) -> tuple[str, ...]:
    """Within-P question order — the trial runner's KEYED DERIVATION (§7),
    reproduced verbatim: `random.Random(f"1512:P:{item_id}:{rep}")` shuffles
    the sorted family list. The realized order is ALSO recorded per P
    dispatch (`question_order` in data/dispatches/); tests/test_descriptives
    asserts the two agree on every P record."""
    import random
    fams = sorted(FAMILIES)
    random.Random(f"{RANDOMIZATION_SEED}:P:{item_id}:{rep}").shuffle(fams)
    return tuple(fams)


def recorded_orders(data_dir: Path) -> tuple[dict, dict]:
    """(P bundle order, Sq turn order) from the RECORDS: Sq turn order is
    recorded per record; P bundle order is re-derived via the runner's
    keyed function (deterministic, regime-pinned) and VERIFIED against
    the response's block order where parseable."""
    p_order, sq_order = {}, {}
    for tier in TIERS:
        for rec in read_jsonl(data_dir / f"{tier}.jsonl"):
            if rec["arm"] == "P":
                p_order[(tier, rec["item"], rec["rep"])] = \
                    keyed_question_order(rec["item"], rec["rep"])
            elif rec["arm"] == "Sq":
                sq_order[(tier, rec["item"], rec["rep"])] = \
                    tuple(t["family"] for t in rec["turns"])
    return p_order, sq_order


def _phi_within(err_by_resp: Sequence[Sequence[int]]) -> float | None:
    """Mean pairwise phi between error indicators within responses."""
    pairs_x, pairs_y = [], []
    for errs in err_by_resp:
        for i in range(len(errs)):
            for j in range(i + 1, len(errs)):
                pairs_x.append(errs[i])
                pairs_y.append(errs[j])
    if len(pairs_x) < 10 or len(set(pairs_x)) < 2 or len(set(pairs_y)) < 2:
        return None
    return float(np.corrcoef(pairs_x, pairs_y)[0, 1])


def main(argv_in: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--final", type=Path, required=True)
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data/dispatches")
    ap.add_argument("--key-table", type=Path,
                    default=ROOT / "data/frozen/audit-key-table.json")
    ap.add_argument("--c44", type=Path,
                    default=ROOT / "data/frozen/c44-selection.json")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--costs", type=Path, default=None,
                    help="costs table for the equal-dollars read (default "
                         "data/results/costs.json). CORRECTED PASS: pass the "
                         "costs file of the SAME table as --final — the 08-27 "
                         "v2 run first read the superseded costs.json here "
                         "(haiku 91-catch denominators), caught before re-issue")
    args = ap.parse_args(argv_in)

    rows = read_jsonl(args.final)
    surviving = sorted(r["item_id"] for r in
                       json.loads(args.key_table.read_text())["table"])
    c44_def = json.loads(args.c44.read_text())["defective"]
    texts = load_texts(args.data_dir)
    p_order, sq_order = recorded_orders(args.data_dir)

    out: dict = {"labels": "§11.3 descriptive/exploratory — CI only, never Holm'd"}

    # --- catch decomposition (unconditional vs conditional-on-well-formed)
    decomp = {}
    for tier in TIERS:
        for arm in ("P", "S", "Sq"):
            t = [r for r in rows if r["tier"] == tier and r["arm"] == arm
                 and r["role"] == "target"]
            if not t:
                continue
            wf = [r for r in t if r["parser_strict_status"] == "PARSED"]
            decomp[f"{tier}/{arm}"] = {
                "unconditional": {"catches": sum(r["status"] == "CATCH" for r in t),
                                  "n": len(t)},
                "conditional_on_well_formed": {
                    "catches": sum(r["status"] == "CATCH" for r in wf),
                    "n": len(wf)},
            }
    out["catch_decomposition"] = decomp

    # --- registered two-arm contrasts (CI only)
    def delta(tier, hi, lo, pool):
        return bootstrap_delta(target_pairs(rows, tier, hi, pool),
                               target_pairs(rows, tier, lo, pool))
    out["s_minus_sq"] = {
        "label": "the COMPOUND (repetition − self-anchoring), never 'the "
                 "repetition component' (D-1)",
        "haiku": delta(TIER_HAIKU, "S", "Sq", surviving),
        "sonnet": delta(TIER_SONNET, "S", "Sq", c44_def),
    }
    out["sq_minus_p_sonnet"] = delta(TIER_SONNET, "Sq", "P", c44_def)
    out["gradient_sonnet_minus_opus"] = {
        "label": "(S−P)_sonnet − (S−P)_opus over C44, shared item draw",
        **bootstrap_contrast([
            (1.0, target_pairs(rows, TIER_SONNET, "S", c44_def)),
            (-1.0, target_pairs(rows, TIER_SONNET, "P", c44_def)),
            (-1.0, target_pairs(rows, TIER_OPUS, "S", c44_def)),
            (1.0, target_pairs(rows, TIER_OPUS, "P", c44_def)),
        ])}

    # --- turn-1 anchor check (instrument check, n stated)
    anchor = {}
    for tier in (TIER_HAIKU, TIER_SONNET):
        t1 = [r for r in rows if r["tier"] == tier and r["arm"] == "Sq"
              and r["role"] == "target"
              and sq_order[(tier, r["item"], r["rep"])][0] == r["family"]]
        s_rows = [r for r in rows if r["tier"] == tier and r["arm"] == "S"
                  and r["role"] == "target"]
        anchor[tier] = {
            "sq_target_at_turn1": {"catches": sum(r["status"] == "CATCH" for r in t1),
                                   "n": len(t1)},
            "s_all": {"catches": sum(r["status"] == "CATCH" for r in s_rows),
                      "n": len(s_rows)},
        }
    out["turn1_anchor_check"] = anchor

    # --- within-P position-in-bundle slope
    slope = {}
    for tier in TIERS:
        by_pos: dict[int, list[int]] = defaultdict(list)
        for r in rows:
            if r["tier"] == tier and r["arm"] == "P" and r["role"] == "target":
                pos = p_order[(tier, r["item"], r["rep"])].index(r["family"]) + 1
                by_pos[pos].append(1 if r["status"] == "CATCH" else 0)
        slope[tier] = {p: {"catches": sum(v), "n": len(v)}
                       for p, v in sorted(by_pos.items())}
    out["p_position_slope"] = slope

    # --- FLAG-count distribution per arm×tier (allocation signature)
    dist = {}
    for tier in TIERS:
        for arm in ("P", "S", "Sq"):
            per_resp: dict[tuple, int] = defaultdict(int)
            seen = set()
            for r in rows:
                if r["tier"] != tier or r["arm"] != arm:
                    continue
                key = (r["item"], r["rep"])
                seen.add(key)
                if row_verdict(r, texts) == "FLAG":
                    per_resp[key] += 1
            if seen:
                c = Counter(per_resp.get(k, 0) for k in seen)
                dist[f"{tier}/{arm}"] = {str(k): c[k] for k in sorted(c)}
    out["flag_count_distribution"] = {
        "note": "FLAG verdicts per (item, rep) response set across its five "
                "question-rows (S: five dispatches; Sq: five turns); verdict = "
                "strict, else loose, else adjudicated",
        "cells": dist}

    # --- HIT-ALT rates
    out["hit_alt"] = {
        f"{tier}/{arm}": sum(1 for r in rows if r["tier"] == tier
                             and r["arm"] == arm and r["status"] == "HIT-ALT")
        for tier in TIERS for arm in ("P", "S", "Sq")}

    # --- per-family heterogeneity, HAIKU ONLY (D-11)
    het = {}
    for fam in FAMILIES:
        pool = [i for i in surviving if i.split("-")[1] == fam]
        if not pool:
            continue
        het[fam] = {
            arm: {"catches": sum(r["status"] == "CATCH" for r in rows
                                 if r["tier"] == TIER_HAIKU and r["arm"] == arm
                                 and r["role"] == "target" and r["item"] in pool),
                  "n": sum(1 for r in rows
                           if r["tier"] == TIER_HAIKU and r["arm"] == arm
                           and r["role"] == "target" and r["item"] in pool)}
            for arm in ("P", "S", "Sq")}
    out["haiku_family_heterogeneity"] = het

    # --- within-response conditional error correlation (P and Sq)
    corr = {}
    for tier in TIERS:
        for arm in ("P", "Sq"):
            errs_by_resp = []
            by_resp: dict[tuple, list[int]] = defaultdict(list)
            for r in rows:
                if r["tier"] != tier or r["arm"] != arm:
                    continue
                if r["role"] == "target":
                    err = 1 if r["status"] != "CATCH" else 0
                elif r["role"] in ("off_family", "clean"):
                    err = 1 if r["status"] == "FA" else 0
                else:
                    continue
                by_resp[(r["item"], r["rep"])].append(err)
            errs_by_resp = [v for v in by_resp.values() if len(v) == 5]
            phi = _phi_within(errs_by_resp)
            if phi is not None:
                corr[f"{tier}/{arm}"] = round(phi, 4)
    out["within_response_error_phi"] = {
        "operationalization": "mean pairwise Pearson phi between question-level "
                              "error indicators (target non-catch / off-family or "
                              "clean FA) within a five-question response set",
        "cells": corr}

    # --- equal-dollars read (§11.3: Δcatch/Δ$ vs the same dollars on more
    # P reps) — S's marginal catches per marginal dollar over P, against
    # P's own average catches per dollar (what the SAME extra spend buys
    # as additional P reps; catches counted per rep, linear in reps)
    costs_path = args.costs or (ROOT / "data/results/costs.json")
    if costs_path.exists():
        ctab = json.loads(costs_path.read_text())["table"]
        eq = {}
        for tier in TIERS:
            p_, s_ = ctab.get(f"{tier}/P"), ctab.get(f"{tier}/S")
            if not (p_ and s_):
                continue
            d_cost = s_["realized_usd"] - p_["realized_usd"]
            d_catch = s_["true_catches"] - p_["true_catches"]
            eq[tier] = {
                "delta_catch_per_delta_usd_S_over_P":
                    round(d_catch / d_cost, 4) if d_cost else None,
                "p_catches_per_usd": round(
                    p_["true_catches"] / p_["realized_usd"], 4),
                "note": "same Δ$ spent on more P reps buys "
                        f"~{d_cost * p_['true_catches'] / p_['realized_usd']:.1f} "
                        "additional catches (linear in reps)",
            }
        out["equal_dollars_read"] = eq
        out["equal_dollars_read_costs_source"] = costs_path.name

    # --- output-token DESCRIPTIVE ASSOCIATION (§6, D-2 labeling: output
    # tokens are post-treatment; conditioning on a mediator identifies no
    # direct effect — this describes co-movement only, no cell keys on it)
    assoc = {}
    for tier in TIERS:
        for arm in ("S", "P"):
            xs, ys = [], []
            for rec in read_jsonl(args.data_dir / f"{tier}.jsonl"):
                if rec["arm"] != arm:
                    continue
                if arm == "S" and rec.get("family"):
                    tgt = [r for r in rows if r["tier"] == tier and r["arm"] == "S"
                           and r["item"] == rec["item"] and r["rep"] == rec["rep"]
                           and r["family"] == rec["family"] and r["role"] == "target"]
                elif arm == "P":
                    tgt = [r for r in rows if r["tier"] == tier and r["arm"] == "P"
                           and r["item"] == rec["item"] and r["rep"] == rec["rep"]
                           and r["role"] == "target"]
                else:
                    tgt = []
                if len(tgt) == 1:
                    xs.append(rec["output_tokens"])
                    ys.append(1 if tgt[0]["status"] == "CATCH" else 0)
            if len(xs) > 10 and len(set(ys)) > 1:
                assoc[f"{tier}/{arm}"] = {
                    "point_biserial_r": round(float(np.corrcoef(xs, ys)[0, 1]), 4),
                    "n": len(xs),
                    "mean_output_tokens": round(float(np.mean(xs)), 1)}
    out["output_token_association"] = {
        "label": "DESCRIPTIVE ASSOCIATION only (D-2): output tokens are "
                 "post-treatment; no cell keys on this read",
        "cells": assoc}

    args.out.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"wrote {args.out}")
    dec_h = decomp.get(f"{TIER_HAIKU}/P", {})
    print("haiku/P decomposition:", dec_h)
    print("S−Sq haiku:", round(out["s_minus_sq"]["haiku"]["delta"], 3),
          "| gradient:", round(out["gradient_sonnet_minus_opus"]["delta"], 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
