"""endpoints.py — §11/§12 primary record: Holm family, guards, member
states, band read, composite cell, qualifiers, stamps, FA co-read.

Bootstraps/Holm ride `stats` (the registered graduation);
cell composition and FA bound checks ride `scorer`'s helpers; this
file adds pool plumbing and the §12 enumeration, never statistics.
Denominators are COUNTED from final rows, never derived.

Registered reads implemented here (verbatim sources in the lock):
  * §11.1 — H-B1 (haiku S−P, surviving defective bank), H-B2 (sonnet
    S−P, C44's 36), H-B3 (shared-draw interaction, both legs over C44's
    36), H-B4 (haiku Sq−P, surviving bank); Holm m=4, one-sided,
    α=0.05; a voided member keeps its slot.
  * §12 guards — pooled target catch > 0.85 or < 0.15 in ANY arm of a
    contrast, on the endpoint's own pool; fired guard → state G.
  * §12 member states, precedence V > G > R > F > N; R on the
    UNADJUSTED two-sided 95% CI (D-6).
  * §11.2 band read — Δ_opus5 90% CI vs B_eq = [−0.20, +0.20]:
    TTFLAT ⊆ band / TTLIVE excludes 0 / TTSPAN neither; an opus guard
    voids the band read.
  * §12 composite cell — keyed on the (H-B1, H-B3) pair ONLY, the
    25-pair enumeration mapped exactly; H-B2/H-B4 recorded as
    qualifiers.
  * Stamps — INVERSE-AT-TIER (per-tier S−P ci95 < 0), FORMAT-DEGRADED
    (strict noncompliance > 25% per arm×tier cell), the
    criterion-shift (criterion-vs-competence) stamp, FA stamps per §11.4 class×tier (FACON /
    FAUNRES forms), CLEANFAIL modifier via J.4 survivors.
  * §11.4 FA classes, each split mf/sf, never pooled across classes:
    (1) clean any-FLAG rate; (2) off-family FA on defective items
    (allowed families leave the denominator per the frozen key table);
    (3) key-matched-but-wrong-family. Adoption bound per
    `scorer.fa_bound_check` (S vs P).

Counting rulings, disclosed (build-time, before the record is read):
  * class-2/3 denominators COUNT scored off-family rows on non-allowed
    families (structurally (4−|allowed|)×reps here — zero instrument
    failures); SILENT rows stay in the denominator (a silent row is an
    FA opportunity not taken) — the §9 "not FA, not counted" clause is
    read as "not counted AS FA".
  * clean any-FLAG unit is the (item, rep) observation: FLAG = any FA
    across that rep's five question rows (P: five blocks; S: five
    dispatches; Sq: five turns).
  * J.4 falsified cleans arrive via --falsified-cleans (a JSON list
    from the keying-checker lane); absent file = no verified real
    findings YET — the flag records whether the checker lane ran.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Mapping, Sequence

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scorer import (  # noqa: E402
    apply_j4_exclusion,
    fa_bound_check,
    format_noncompliance,
)
from stats import bootstrap_delta, bootstrap_interaction, holm  # noqa: E402

ROOT = _HERE.parent
TIER_HAIKU = "claude-haiku-4-5-20251001"
TIER_SONNET = "claude-sonnet-5"
TIER_OPUS = "claude-opus-5"
GUARD_HI, GUARD_LO = 0.85, 0.15
B_EQ = (-0.20, 0.20)
SESOI = 0.10

# §12's 25-pair enumeration, exact.
_CELL_MAP: dict[tuple[str, str], str] = {}
for _pair, _cell in (
    ((("F", "F"),), "C-B1"),
    ((("F", "N"), ("F", "G"), ("F", "V")), "C-B2"),
    ((("F", "R"),), "C-B3"),
    ((("N", "F"), ("R", "F"), ("V", "F"), ("G", "F")), "C-B4"),
    ((("N", "N"), ("N", "G"), ("N", "V"), ("G", "N"), ("G", "G"), ("G", "V"),
      ("V", "N"), ("V", "G"), ("V", "V")), "C-B5"),
    ((("R", "N"), ("R", "R"), ("R", "G"), ("R", "V"), ("N", "R"), ("V", "R"),
      ("G", "R")), "C-B6"),
):
    for _p_ in _pair:
        _CELL_MAP[_p_] = _cell
assert len(_CELL_MAP) == 25


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


# ------------------------------------------------------------------ pools
def target_pairs(rows: Sequence[Mapping], tier: str, arm: str,
                 pool: Sequence[str]) -> list[tuple[int, int]]:
    """Per-item (catches, n) over target rows, aligned to sorted(pool).
    Refuses an empty item cell — an absent item is reported, never a 0."""
    per: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        if r["tier"] == tier and r["arm"] == arm and r["role"] == "target":
            per[r["item"]].append(1 if r["status"] == "CATCH" else 0)
    out = []
    for item in sorted(pool):
        obs = per.get(item)
        if not obs:
            raise SystemExit(
                f"REFUSE: no target rows for {item} at {tier}/{arm} — the pool "
                "and the final rows disagree; denominators are counted, not assumed")
        out.append((sum(obs), len(obs)))
    return out


def pooled_rate(pairs: Sequence[tuple[int, int]]) -> float:
    return sum(c for c, _ in pairs) / sum(n for _, n in pairs)


def guard_state(pairs_by_arm: Mapping[str, Sequence[tuple[int, int]]]) -> dict:
    fired = {}
    for arm, pairs in pairs_by_arm.items():
        rate = pooled_rate(pairs)
        if rate > GUARD_HI or rate < GUARD_LO:
            fired[arm] = rate
    return {"fired": bool(fired), "arms": fired,
            "rates": {a: pooled_rate(p) for a, p in pairs_by_arm.items()}}


def member_state(boot: Mapping, holm_fired: bool, guard: Mapping,
                 *, voided: bool = False) -> str:
    """§12 precedence V > G > R > F > N."""
    if voided:
        return "V"
    if guard["fired"]:
        return "G"
    if boot["ci95"][1] < 0:
        return "R"
    if holm_fired:
        return "F"
    return "N"


# ------------------------------------------------------------------ FA side
def _rep_index(rows: Sequence[Mapping]) -> dict:
    by = defaultdict(list)
    for r in rows:
        by[(r["tier"], r["arm"], r["item"], r["rep"])].append(r)
    return by


def clean_anyflag_pairs(rows, tier, arm, clean_items) -> list[tuple[int, int]]:
    """Class 1: per clean item, (reps with ≥1 FA across the five question
    rows, total reps)."""
    by_rep = _rep_index([r for r in rows if r["tier"] == tier and r["arm"] == arm
                         and r["item"] in set(clean_items)])
    per_item: dict[str, list[int]] = defaultdict(list)
    for (t, a, item, rep), rws in sorted(by_rep.items()):
        per_item[item].append(1 if any(r["status"] == "FA" for r in rws) else 0)
    out = []
    for item in sorted(clean_items):
        obs = per_item.get(item)
        if not obs:
            raise SystemExit(f"REFUSE: no rows for clean item {item} at {tier}/{arm}")
        out.append((sum(obs), len(obs)))
    return out


def off_family_pairs(rows, tier, arm, pool, *, numerator: str) -> list[tuple[int, int]]:
    """Classes 2/3 over defective items: numerator='fa' counts status FA;
    numerator='kmwf' counts key_matched_wrong_family. Denominator: scored
    off-family rows on NON-allowed families (counted)."""
    per: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        if (r["tier"] == tier and r["arm"] == arm and r["role"] == "off_family"
                and r["item"] in set(pool)
                and r["family"] not in (r.get("allowed_families") or [])):
            if numerator == "fa":
                hit = r["status"] == "FA"
            else:
                hit = bool(r.get("key_matched_wrong_family"))
            per[r["item"]].append(1 if hit else 0)
    out = []
    for item in sorted(pool):
        obs = per.get(item)
        if not obs:
            raise SystemExit(f"REFUSE: no off-family rows for {item} at {tier}/{arm}")
        out.append((sum(obs), len(obs)))
    return out


def fa_class_read(rows, tier, arms: tuple[str, str], items_by_class: Mapping[str, list],
                  pairs_fn, **kw) -> dict:
    """One FA class at one tier, split mf/sf, S-vs-P bound check per split."""
    out = {}
    hi, lo = arms
    for split, items in items_by_class.items():
        if not items:
            out[split] = {"state": "UNDECIDABLE", "reason": "no items in split"}
            continue
        hi_pairs = pairs_fn(rows, tier, hi, items, **kw)
        lo_pairs = pairs_fn(rows, tier, lo, items, **kw)
        chk = fa_bound_check(hi_pairs, lo_pairs)
        chk["n_items"] = len(items)
        out[split] = chk
    return out


# ------------------------------------------------------------------ driver
def main(argv_in: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--final", type=Path, required=True)
    ap.add_argument("--key-table", type=Path,
                    default=ROOT / "data/frozen/audit-key-table.json")
    ap.add_argument("--c44", type=Path,
                    default=ROOT / "data/frozen/c44-selection.json")
    ap.add_argument("--falsified-cleans", type=Path, default=None,
                    help="J.4 keying-checker output: JSON list of clean item ids "
                         "with verified real findings")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv_in)

    rows = read_jsonl(args.final)
    unresolved = [r for r in rows if r["status"] == "BORDERLINE"]
    if unresolved:
        raise SystemExit(f"REFUSE: {len(unresolved)} BORDERLINE rows remain — "
                         "run the adjudication merge first")
    kt = json.loads(args.key_table.read_text())
    surviving = sorted(r["item_id"] for r in kt["table"])
    c44 = json.loads(args.c44.read_text())
    c44_def, c44_clean = c44["defective"], c44["clean"]
    items_meta = {}
    for d in (ROOT / "materials/items",):
        for p in d.glob("*.json"):
            it = json.loads(p.read_text())
            items_meta[it["id"]] = it

    # ---- primary contrasts on their registered pools
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
    # Holm consumes every non-void member's one-sided p (m = 4 always;
    # G members keep their slot but issue no reading, so their p is
    # passed as None: "a fired guard issues no reading")
    p_in = {k: (None if guards[k]["fired"] else boots[k]["p_one_sided"])
            for k in boots}
    fired = holm(p_in)
    states = {k: member_state(boots[k], fired[k], guards[k]) for k in boots}

    # ---- band read (§11.2) — voided by an opus guard
    opus_guard = guard_state({"S": h3_So, "P": h3_Po})
    band_boot = bootstrap_delta(h3_So, h3_Po)
    if opus_guard["fired"]:
        band = {"cell": "VOIDED", "reason": "opus guard fired (ceiling != flat)",
                "guard": opus_guard, **band_boot}
    else:
        lo, hi = band_boot["ci90"]
        if B_EQ[0] <= lo and hi <= B_EQ[1]:
            cell = "C-B-TTFLAT"
        elif lo > 0 or hi < 0:
            cell = "C-B-TTLIVE"
        else:
            cell = "C-B-TTSPAN"
        band = {"cell": cell, "band": B_EQ, **band_boot}

    # ---- composite cell (§12) — keyed on (H-B1, H-B3) ONLY
    composite = _CELL_MAP[(states["H-B1"], states["H-B3"])]
    sub_read = None
    if composite == "C-B5":
        if states["H-B1"] == "N":
            ub = boots["H-B1"]["ci95"][1]
            sub_read = ("RITUAL-at-haiku" if ub < SESOI else "INCONCLUSIVE")
        elif states["H-B1"] in ("G", "V"):
            sub_read = "HEADLINE-UNMEASURED"

    # ---- stamps
    inverse_at_tier = {}
    for tier, (s_p, p_p) in {
        TIER_HAIKU: (hb1_S, hb1_P), TIER_SONNET: (hb2_S, hb2_P),
        TIER_OPUS: (h3_So, h3_Po),
    }.items():
        b = bootstrap_delta(s_p, p_p)
        inverse_at_tier[tier] = {"stamped": b["ci95"][1] < 0, "ci95": b["ci95"],
                                 "delta": b["delta"]}

    fmt = {}
    for tier in (TIER_HAIKU, TIER_SONNET, TIER_OPUS):
        for arm in ("P", "S", "Sq"):
            cell_rows = [r for r in rows if r["tier"] == tier and r["arm"] == arm]
            if cell_rows:
                fmt[f"{tier}/{arm}"] = format_noncompliance(cell_rows)

    # ---- FA co-read (§11.4): classes 1-3, each mf/sf, S vs P, per tier
    falsified = (json.loads(args.falsified_cleans.read_text())
                 if args.falsified_cleans else [])
    all_cleans = sorted(i for i, m in items_meta.items()
                        if m["defect_class"] == "clean")
    fa = {"j4": None, "falsified_cleans": falsified,
          "j4_checker_ran": args.falsified_cleans is not None, "classes": {}}
    for tier in (TIER_HAIKU, TIER_SONNET, TIER_OPUS):
        cleans_here = all_cleans if tier == TIER_HAIKU else c44_clean
        j4 = apply_j4_exclusion(cleans_here, falsified)
        def _split(ids):
            return {"mf": [i for i in ids if items_meta[i]["item_class"] == "multi_file"],
                    "sf": [i for i in ids if items_meta[i]["item_class"] != "multi_file"]}
        def_pool = surviving if tier == TIER_HAIKU else c44_def
        tier_read = {
            "j4_survivors": j4,
            "class1_clean_anyflag": fa_class_read(
                rows, tier, ("S", "P"), _split(j4["survivors"]), clean_anyflag_pairs),
            "class2_off_family_fa": fa_class_read(
                rows, tier, ("S", "P"), _split(def_pool), off_family_pairs,
                numerator="fa"),
            "class3_key_matched_wrong_family": fa_class_read(
                rows, tier, ("S", "P"), _split(def_pool), off_family_pairs,
                numerator="kmwf"),
        }
        fa["classes"][tier] = tier_read

    # criterion-shift stamp: S raises hits AND any FA class at a tier, both
    # CIs above 0
    crit = {}
    for tier, (s_p, p_p) in {
        TIER_HAIKU: (hb1_S, hb1_P), TIER_SONNET: (hb2_S, hb2_P),
        TIER_OPUS: (h3_So, h3_Po),
    }.items():
        hits_up = bootstrap_delta(s_p, p_p)["ci95"][0] > 0
        fa_up = any(
            isinstance(cls.get(split), dict) and "ci95" in cls[split]
            and cls[split]["ci95"][0] > 0
            for cls_name, cls in fa["classes"][tier].items()
            if cls_name.startswith("class")
            for split in ("mf", "sf"))
        crit[tier] = {"stamped": hits_up and fa_up,
                     "hits_ci_above_0": hits_up, "any_fa_ci_above_0": fa_up}

    result = {
        "pools": {"surviving_defective": len(surviving), "c44_defective": len(c44_def),
                  "c44_clean": len(c44_clean)},
        "boots": boots, "guards": guards, "holm_input": p_in,
        "holm_fired": fired, "member_states": states,
        "band_read": band, "composite_cell": composite, "c_b5_sub_read": sub_read,
        "qualifiers": {"H-B2": states["H-B2"], "H-B4": states["H-B4"]},
        "stamps": {"inverse_at_tier": inverse_at_tier,
                   "format_noncompliance": fmt, "criterion_shift_stamp": crit},
        "fa_co_read": fa,
    }
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    print(f"composite cell: {composite}"
          + (f" (sub-read {sub_read})" if sub_read else ""))
    print(f"states: {states} | band: {band['cell']}")
    print(f"deltas: " + ", ".join(f"{k}={boots[k]['delta']:+.3f} "
                                  f"p={p_in[k] if p_in[k] else 'G'}" for k in boots))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
