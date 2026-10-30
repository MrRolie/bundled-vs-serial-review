"""coreads.py — the §9 robustness co-reads for the CORRECTED pass
(registration/amendments/2026-08-27-corrected-scoring-pass.md, rule 4,
pre-registered before any corrected endpoint was computed): conclusions shown invariant across variants that
PERTURB EXTRACTION, or the divergence disclosed.

The published co-read (08-22) ran two variants — loose-primary and
NONE-scope — that both sat DOWNSTREAM of the primary's extraction, so they
could not fail on the extraction defect the recount found (a check that
cannot fail is not a check). The registered co-reads are now:

  V1  PRIMARY — the corrected pass as merged (`route`, `scored_text`,
      `presented_block`, `adjudicated.lane` on every row).
  V2  P-MAXIMAL KEY SCOPE — for every P row whose VERDICT is FLAG
      (mechanical strict parse or adjudicated), key-matching widens from
      the family's block/segment to the WHOLE bundle. S/Sq rows are
      unchanged (their scored text already is the whole turn). Direction:
      can only ADD target catches, move off-family FA → HIT-ALT (allowed
      family), or set `key_matched_wrong_family`.
  V3  LABEL-RESPECTING PUNITIVE — a permissive-route S/Sq row counts as
      PRESENT only if its turn carries a live-shape marker for the ASKED
      family anywhere (`presence.marker_family`); otherwise it composes
      as MISSING (target → NON-CATCH, off-family/clean → SILENT) regardless
      of the lane verdict. P rows are unchanged (a P segment requires the
      family's own marker by construction). Direction: can only REMOVE
      catches/FAs the permissive route recovered.

Legacy lines (kept for continuity, perturb nothing upstream of the lane):
loose-primary (recorded `co_read_loose_status`) and NONE-scope. The
published NONE-scope implementation keyed S records by (tier, arm, item,
rep) — colliding across the five per-family S records of one item×rep, so
its S rows read the wrong turn — FIXED here (texts keyed by family for
every arm) and disclosed; it changed no published conclusion because the
variant is structurally invariant on the Holm family.

Every variant is scored with the SAME endpoint chain as the primary
(`endpoints` helpers + `stats`): H-B1..H-B4 deltas, one-sided p's,
Holm firings, member states, composite cell, C-B5 sub-read, and the §11.4
FA class reads (mf/sf, S vs P, per tier). Divergence is DISCLOSED, never
averaged.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from endpoints import (  # noqa: E402
    _CELL_MAP,
    SESOI,
    TIER_HAIKU,
    TIER_OPUS,
    TIER_SONNET,
    clean_anyflag_pairs,
    fa_class_read,
    guard_state,
    member_state,
    off_family_pairs,
    read_jsonl,
    target_pairs,
)
from answer_parser import parse_response  # noqa: E402
from presence import marker_family  # noqa: E402
from scorer import _keys_match, apply_j4_exclusion, sq_turn_text, trial_text  # noqa: E402
from stats import bootstrap_delta, bootstrap_interaction, holm  # noqa: E402

ROOT = _HERE.parent
FAMILIES = ("boundary", "comparison", "exception", "sign", "units")
_NO_DEFECT_RE = {fam: re.compile(rf"\bNO-DEFECT-{fam}\b", re.IGNORECASE) for fam in FAMILIES}
TIERS = (TIER_HAIKU, TIER_SONNET, TIER_OPUS)


# ------------------------------------------------------------------ texts
def _key(r: Mapping) -> tuple:
    return (r["tier"], r["arm"], r["item"], r["rep"], r["family"])


def load_texts(data_dir: Path) -> dict[tuple, str]:
    """§9 text per (tier, arm, item, rep, family): P = the bundle under each
    family key; S = that record's own family; Sq = the turn's own text."""
    texts: dict[tuple, str] = {}
    for tier in TIERS:
        for rec in read_jsonl(data_dir / f"{tier}.jsonl"):
            if rec["arm"] == "Sq":
                for t in rec["turns"]:
                    texts[(tier, "Sq", rec["item"], rec["rep"], t["family"])] = \
                        sq_turn_text(rec, t["family"])
            elif rec["arm"] == "S":
                texts[(tier, "S", rec["item"], rec["rep"], rec["family"])] = trial_text(rec)
            else:
                text = trial_text(rec)
                for fam in FAMILIES:
                    texts[(tier, "P", rec["item"], rec["rep"], fam)] = text
    return texts


def load_items() -> dict[str, dict]:
    items = {}
    for d in (ROOT / "materials/items",):
        for p in d.glob("*.json"):
            it = json.loads(p.read_text())
            items[it["id"]] = it
    return items


# --------------------------------------------------------------- variants
def flag_verdict(row: Mapping, text: str) -> str | None:
    """The row's resolved VERDICT: the lane's where adjudicated, else the
    strict parse of §9's text (the mechanical chain's own verdict source)."""
    adj = row.get("adjudicated")
    if adj:
        return adj.get("verdict")
    return parse_response(text, [row["family"]], variant="strict")[row["family"]].get("verdict")


def v2_p_maximal_rows(rows: Sequence[Mapping], texts: Mapping[tuple, str],
                      items: Mapping[str, dict]) -> tuple[list[dict], int]:
    out, relabeled = [], 0
    for r in rows:
        n = dict(r)
        if r["arm"] == "P":
            bundle = texts[_key(r)]
            keys = items[r["item"]].get("defect_keys") or []
            if keys and flag_verdict(r, bundle) == "FLAG":
                if r["role"] == "target":
                    if r["status"] == "NON-CATCH" and _keys_match(bundle, keys):
                        n["status"], n["hit"] = "CATCH", True
                        relabeled += 1
                else:
                    if r["status"] == "FA":
                        allowed = r.get("allowed_families") or []
                        if r["family"] in allowed and _keys_match(bundle, keys):
                            n["status"] = "HIT-ALT"
                            n.pop("key_matched_wrong_family", None)
                            relabeled += 1
                        else:
                            kmwf = _keys_match(bundle, keys)
                            if kmwf != bool(r.get("key_matched_wrong_family")):
                                n["key_matched_wrong_family"] = kmwf
                                relabeled += 1
        out.append(n)
    return out, relabeled


def v3_label_respecting_rows(rows: Sequence[Mapping],
                             texts: Mapping[tuple, str]) -> tuple[list[dict], int]:
    out, relabeled = [], 0
    for r in rows:
        n = dict(r)
        if r.get("route") == "permissive-present" and r["arm"] in ("S", "Sq"):
            turn = texts[_key(r)]
            labeled = any(marker_family(ln) == r["family"] for ln in turn.splitlines())
            if not labeled:
                if r["role"] == "target":
                    n["status"], n["hit"] = "NON-CATCH", False
                else:
                    n["status"] = "SILENT"
                    n.pop("key_matched_wrong_family", None)
                if n["status"] != r["status"] or n.get("hit") != r.get("hit"):
                    relabeled += 1
        out.append(n)
    return out, relabeled


def loose_variant_rows(rows: Sequence[Mapping]) -> tuple[list[dict], int]:
    out, relabeled = [], 0
    for r in rows:
        n = dict(r)
        if not r.get("adjudicated") and r.get("co_read_loose_status") \
                and r["co_read_loose_status"] != r["status"]:
            n["status"] = r["co_read_loose_status"]
            relabeled += 1
        out.append(n)
    return out, relabeled


def none_scope_rows(rows: Sequence[Mapping], texts: Mapping[tuple, str]) -> tuple[list[dict], int]:
    out, relabeled = [], 0
    for r in rows:
        n = dict(r)
        if r["status"] in ("NON-CATCH", "SILENT") and not r.get("adjudicated") \
                and r.get("parser_strict_status") == "MISSING":
            if _NO_DEFECT_RE[r["family"]].search(texts[_key(r)] or ""):
                relabeled += 1
                if r["status"] == "SILENT":
                    n["status"] = "NO-FLAG"
        out.append(n)
    return out, relabeled


# -------------------------------------------------------------- endpoints
def endpoints_under(rows: Sequence[Mapping], surviving, c44_def) -> dict:
    hb1_S = target_pairs(rows, TIER_HAIKU, "S", surviving)
    hb1_P = target_pairs(rows, TIER_HAIKU, "P", surviving)
    hb4_Sq = target_pairs(rows, TIER_HAIKU, "Sq", surviving)
    hb2_S = target_pairs(rows, TIER_SONNET, "S", c44_def)
    hb2_P = target_pairs(rows, TIER_SONNET, "P", c44_def)
    h3_Sh = target_pairs(rows, TIER_HAIKU, "S", c44_def)
    h3_Ph = target_pairs(rows, TIER_HAIKU, "P", c44_def)
    h3_So = target_pairs(rows, TIER_OPUS, "S", c44_def)
    h3_Po = target_pairs(rows, TIER_OPUS, "P", c44_def)
    boots = {
        "H-B1": bootstrap_delta(hb1_S, hb1_P),
        "H-B2": bootstrap_delta(hb2_S, hb2_P),
        "H-B3": bootstrap_interaction(h3_Sh, h3_Ph, h3_So, h3_Po),
        "H-B4": bootstrap_delta(hb4_Sq, hb1_P),
    }
    guards = {
        "H-B1": guard_state({"S": hb1_S, "P": hb1_P}),
        "H-B2": guard_state({"S": hb2_S, "P": hb2_P}),
        "H-B3": guard_state({"S_haiku": h3_Sh, "P_haiku": h3_Ph,
                             "S_opus": h3_So, "P_opus": h3_Po}),
        "H-B4": guard_state({"Sq": hb4_Sq, "P": hb1_P}),
    }
    p_in = {k: (None if guards[k]["fired"] else boots[k]["p_one_sided"]) for k in boots}
    fired = holm(p_in)
    states = {k: member_state(boots[k], fired[k], guards[k]) for k in boots}
    composite = _CELL_MAP[(states["H-B1"], states["H-B3"])]
    sub_read = None
    if composite == "C-B5":
        if states["H-B1"] == "N":
            sub_read = "RITUAL-at-haiku" if boots["H-B1"]["ci95"][1] < SESOI else "INCONCLUSIVE"
        elif states["H-B1"] in ("G", "V"):
            sub_read = "HEADLINE-UNMEASURED"
    # per-tier S-vs-P hits CI lower bound > 0 — the hits leg of the criterion-shift stamp
    # (endpoints computes the same three deltas; the opus leg is the
    # C44 S-vs-P delta at opus, not an H-B member)
    hits_up = {TIER_HAIKU: boots["H-B1"]["ci95"][0] > 0,
               TIER_SONNET: boots["H-B2"]["ci95"][0] > 0,
               TIER_OPUS: bootstrap_delta(h3_So, h3_Po)["ci95"][0] > 0}
    return {
        "deltas": {k: round(boots[k]["delta"], 4) for k in boots},
        "ci95": {k: [round(x, 4) for x in boots[k]["ci95"]] for k in boots},
        "p_one_sided": {k: p_in[k] for k in boots},
        "holm_fired": fired, "member_states": states,
        "composite_cell": composite, "c_b5_sub_read": sub_read,
        "hits_ci_above_0": hits_up,
        "pooled_rates": {"H-B1": guards["H-B1"]["rates"], "H-B4": guards["H-B4"]["rates"],
                         "H-B2": guards["H-B2"]["rates"], "H-B3": guards["H-B3"]["rates"]},
    }


def fa_under(rows: Sequence[Mapping], surviving, c44_def, c44_clean,
             items_meta: Mapping[str, dict], falsified: Sequence[str]) -> dict:
    all_cleans = sorted(i for i, m in items_meta.items() if m["defect_class"] == "clean")
    out = {}
    for tier in TIERS:
        cleans_here = all_cleans if tier == TIER_HAIKU else c44_clean
        j4 = apply_j4_exclusion(cleans_here, falsified)

        def _split(ids):
            return {"mf": [i for i in ids if items_meta[i]["item_class"] == "multi_file"],
                    "sf": [i for i in ids if items_meta[i]["item_class"] != "multi_file"]}
        def_pool = surviving if tier == TIER_HAIKU else c44_def
        out[tier] = {
            "class1_clean_anyflag": fa_class_read(
                rows, tier, ("S", "P"), _split(j4["survivors"]), clean_anyflag_pairs),
            "class2_off_family_fa": fa_class_read(
                rows, tier, ("S", "P"), _split(def_pool), off_family_pairs, numerator="fa"),
            "class3_key_matched_wrong_family": fa_class_read(
                rows, tier, ("S", "P"), _split(def_pool), off_family_pairs, numerator="kmwf"),
        }
    return out


def criterion_shift_under(ep: Mapping, fa: Mapping) -> dict:
    """Criterion-shift stamp per tier under a variant: S raises hits (CI lower
    bound > 0) AND any FA class/split CI lower bound > 0 — the same rule
    `endpoints` stamps on the primary, so the stamp's variant-stability
    is reported rather than assumed."""
    out = {}
    for tier, classes in fa.items():
        fa_up = any(isinstance(v, dict) and "ci95" in v and v["ci95"][0] > 0
                    for cls_name, cls in classes.items() if cls_name.startswith("class")
                    for v in cls.values())
        hits = bool(ep["hits_ci_above_0"].get(tier, False))
        out[tier] = {"stamped": hits and fa_up, "hits_ci_above_0": hits,
                     "any_fa_ci_above_0": fa_up}
    return out


def fa_states(fa: Mapping) -> dict:
    """The comparable skeleton of an FA read: per tier/class/split, the
    bound-check state (whatever `fa_bound_check` names it) — used for the
    divergence comparison so CI noise in the 4th decimal is not 'divergence'."""
    return {tier: {cls: {split: (v.get("state") if isinstance(v, dict) else None)
                         for split, v in classes.items()}
                   for cls, classes in per_tier.items()}
            for tier, per_tier in fa.items()}


def main(argv_in: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--final", type=Path, required=True)
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data/dispatches")
    ap.add_argument("--key-table", type=Path,
                    default=ROOT / "data/frozen/audit-key-table.json")
    ap.add_argument("--c44", type=Path,
                    default=ROOT / "data/frozen/c44-selection.json")
    ap.add_argument("--falsified-cleans", type=Path, default=None)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv_in)

    rows = read_jsonl(args.final)
    if any(r["status"] == "BORDERLINE" for r in rows):
        raise SystemExit("REFUSE: BORDERLINE rows remain — merge the lane first")
    surviving = sorted(r["item_id"] for r in json.loads(args.key_table.read_text())["table"])
    c44 = json.loads(args.c44.read_text())
    c44_def, c44_clean = c44["defective"], c44["clean"]
    falsified = json.loads(args.falsified_cleans.read_text()) if args.falsified_cleans else []
    texts = load_texts(args.data_dir)
    items = load_items()

    variants = {"V1_primary": (rows, 0)}
    variants["V2_p_maximal_key_scope"] = v2_p_maximal_rows(rows, texts, items)
    variants["V3_label_respecting_punitive"] = v3_label_respecting_rows(rows, texts)
    variants["legacy_loose_primary"] = loose_variant_rows(rows)
    variants["legacy_none_scope"] = none_scope_rows(rows, texts)

    results = {}
    for name, (vrows, relabeled) in variants.items():
        ep = endpoints_under(vrows, surviving, c44_def)
        fa = fa_under(vrows, surviving, c44_def, c44_clean, items, falsified)
        results[name] = {"relabeled_rows": relabeled, **ep, "fa": fa,
                         "criterion_shift_stamp": criterion_shift_under(ep, fa)}

    primary = results["V1_primary"]
    divergences = []
    for name, var in results.items():
        if name == "V1_primary":
            continue
        for k in ("member_states", "composite_cell", "holm_fired", "c_b5_sub_read", "criterion_shift_stamp"):
            if var[k] != primary[k]:
                divergences.append({"variant": name, "field": k,
                                    "primary": primary[k], "variant_value": var[k]})
        if fa_states(var["fa"]) != fa_states(primary["fa"]):
            divergences.append({"variant": name, "field": "fa_states",
                                "primary": fa_states(primary["fa"]),
                                "variant_value": fa_states(var["fa"])})
    registered = ("V2_p_maximal_key_scope", "V3_label_respecting_punitive")
    reg_div = [d for d in divergences if d["variant"] in registered]
    out = {
        "registered_variants": list(registered),
        "results": results,
        "divergences": divergences,
        "conclusion": ("INVARIANT across the registered extraction-perturbing variants "
                       "(member states, Holm firings, composite cell, C-B5 sub-read, "
                       "FA bound states)" if not reg_div
                       else "DIVERGENT on a registered variant — disclosed above"),
        "disclosure": ("legacy NONE-scope S-record keying collision fixed in this "
                       "version (texts keyed by family for every arm)"),
    }
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    for name, var in results.items():
        print(f"{name}: relabeled {var['relabeled_rows']:4d} | states {var['member_states']} "
              f"| {var['composite_cell']}"
              + (f" ({var['c_b5_sub_read']})" if var["c_b5_sub_read"] else ""))
    print(out["conclusion"])
    for d in divergences:
        print("DIVERGENCE:", json.dumps(d)[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
