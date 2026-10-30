#!/usr/bin/env python
"""recount_v2.py — the independent recount of the CORRECTED chain, Phase A (blind),
fresh code. REFERENCE ONLY in this extract: it is published so the recount's method can be
read, not re-run. Its inputs include the private trial records and the adjudication lanes'
input/mapping files, which are not published (see methods/RECOUNT.md). Its row-level output
is published (recount/recount-rows.jsonl) and checked against the scored table by
recount/check_agreement.py.

Derived from RULES TEXT ONLY: registration 2026-08-17 §8/§9/§11/§12 (+ dated amendments)
and the corrected-pass rules 1-8 (registration/amendments/2026-08-27-corrected-scoring-
pass.md). No module of the original analysis (analysis/) is imported or read. Inputs (paths
as they were in the private repository):

  trials-*.jsonl                        immutable trial records (the texts)
  items (80)                            frozen items (defect_keys, classes)
  data/audit-key-table.json             allowances / FA denominators
  data/c44-selection.json               C44 pool of record
  data/final-rows.jsonl                 08-22 merged table: pinned strict/loose
                                        statuses (registered instrument, taken as
                                        given), lane-1 verdicts + presented blocks
                                        (the retention SOURCE), mechanical rows
                                        (byte-pinned by rule 1 — copied)
  data/adjudication-results.jsonl       lane 1 (verdict records)
  data/adjudication-results-v2.jsonl    lane 2 (verdict records)
  data/scored-rows-v2.jsonl.adjmapping.json   adj-2xxx -> row key (lane-2 keying)
  data/scored-rows-v2.jsonl.adjretained.json  the ORIGINAL retention decision — compared
                                        against the recount's AFTER it is frozen, never copied
  data/scored-rows-v2.jsonl.adjbatches.json   lane-2 INPUT text (what judges saw) —
                                        compared against the recount's extraction AFTER freeze
  data/j4-verdicts-v2.jsonl             J.4 checker verdicts of record

Writes: blind-pass.json (published as recount/recount-summary.json) and the row file
(published as recount/recount-rows.jsonl).
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

# Private-repository layout at the time of the recount (reference only; see docstring).
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = DATA / "recount-v2"
MAT = ROOT / "materials"

FAMILIES = ["boundary", "comparison", "exception", "sign", "units"]
TIER_ID = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
}
ID_TIER = {v: k for k, v in TIER_ID.items()}
SEED = 1512
B_REG = 10_000
ALPHA = 0.05
M_HOLM = 4
SESOI = 0.10
BAND = 0.20
GUARD_HI, GUARD_LO = 0.85, 0.15
FA_BOUND = 0.15

# --------------------------------------------------------------------------
# §9 text per arm (ruling 1) — extraction
# --------------------------------------------------------------------------
_FAM_ALT = "|".join(FAMILIES)
# live-shape family marker at line start after decoration (#, **, bullets,
# numbering, blockquote, backticks).  Case-insensitive; family name must not
# continue as a word (Q-signature is not Q-sign).
_MARK = re.compile(r"(?i)^(?:Q-|NO-DEFECT-|FLAG-|NONE-)(" + _FAM_ALT + r")(?![a-z])")
_DECOR = re.compile(r"^[\s#*_>+`\-]+")
_NUMBERING = re.compile(r"^\d+[.)]\s*")
# V3 'anywhere' marker for the asked family (inline, not line-start)
_INLINE_MARK = {
    f: re.compile(r"(?i)(?:Q-|NO-DEFECT-|FLAG-|NONE-)" + f + r"(?![a-z])") for f in FAMILIES
}
_FENCE_ONLY = re.compile(r"^\s*`{3,}[\w+-]*\s*$")


def line_marker(line: str):
    s = line
    prev = None
    while prev != s:
        prev = s
        s = _DECOR.sub("", s)
        s = _NUMBERING.sub("", s)
    m = _MARK.match(s)
    return m.group(1).lower() if m else None


def p_segment(bundle: str, family: str):
    """P: from the family's FIRST live-shape marker to the next DIFFERENT-family
    marker (same-family markers do not close), else end of text.  None = MISSING."""
    lines = (bundle or "").split("\n")
    marks = [line_marker(l) for l in lines]
    start = next((i for i, m in enumerate(marks) if m == family), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if marks[i] and marks[i] != family), len(lines))
    seg = "\n".join(lines[start:end]).strip()
    return seg or None


def normalize_for_retention(t: str | None) -> str:
    lines = [l for l in (t or "").split("\n") if not _FENCE_ONLY.match(l)]
    return re.sub(r"\s+", " ", "\n".join(lines)).strip()


def key_matched(text: str | None, keys) -> list:
    """Mechanical key containment, case-insensitive (calibrated: reproduces the
    committed table's mechanical layer 914/914 target rows, 353/353 FA rows)."""
    t = (text or "").lower()
    return [k for k in keys if k.lower() in t]


def mech_verdict(raw_block: str | None):
    first = (raw_block or "").strip().split("\n")[0]
    m = re.match(r"^\s*Q-(\w+)\s*:\s*(FLAG|NONE)\b", first)
    if m:
        return m.group(2)
    if re.search(r"NO-DEFECT-\w+", first):
        return "NONE"
    return None


def sha(t: str | None) -> str | None:
    return None if t is None else hashlib.sha256(t.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------
def load_jsonl(p):
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


def load_items():
    items = {}
    for d in [MAT / "items"]:
        for p in sorted(d.glob("*.json")):
            j = json.load(open(p))
            items[j["id"]] = {
                "defect_class": j["defect_class"],
                "item_class": j["item_class"],
                "defect_keys": list(j["defect_keys"]),
            }
    return items


def load_trials():
    tr = {}
    for tid in TIER_ID.values():
        for t in load_jsonl(DATA / f"trials-{tid}.jsonl"):
            k = (t["model_id"], t["arm"], t["item"], t["rep"], t.get("family"))
            assert k not in tr, k
            tr[k] = t
    return tr


def lane_verdicts(path):
    """verdict of record per adj id: tiebreak stage (R3) governs where present,
    else primary.  Also returns R1-vs-R2 disagreement list and arm-guess values."""
    prim, readj, tie, guess = {}, {}, {}, {}
    stages = collections.Counter()
    for rec in load_jsonl(path):
        stages[(rec["stage"], rec["reader"])] += 1
        for aid, v in rec["verdicts"].items():
            if rec["stage"] == "primary":
                assert aid not in prim, aid
                prim[aid] = v["verdict"]
            elif rec["stage"] == "readjudication":
                readj[aid] = v["verdict"]
            elif rec["stage"] == "armguess":
                guess[aid] = v["verdict"]
            else:  # any tiebreak / R3 stage
                tie[aid] = v["verdict"]
    disagree = [(a, prim.get(a), readj[a]) for a in readj if prim.get(a) != readj[a]]
    of_record = dict(prim)
    for a, v in tie.items():
        of_record[a] = v
    return {
        "of_record": of_record,
        "primary": prim,
        "readj": readj,
        "tiebreak": tie,
        "disagree": disagree,
        "armguess": guess,
        "stages": {f"{s}/{r}": n for (s, r), n in stages.items()},
    }


# --------------------------------------------------------------------------
# bootstrap machinery (item-cluster, vectorised)
# --------------------------------------------------------------------------
def cluster_stat(arrs, idx):
    """arrs: list of (sign, sums, counts) — statistic = Σ sign * (Σsums[idx]/Σcounts[idx])."""
    out = 0.0
    for sign, s, n in arrs:
        out = out + sign * (s[idx].sum(axis=1) / n[idx].sum(axis=1))
    return out


def boot(arrs, n_items, B, seed, chunk=100_000):
    rng = np.random.default_rng(seed)
    res = np.empty(B)
    done = 0
    while done < B:
        m = min(chunk, B - done)
        idx = rng.integers(0, n_items, size=(m, n_items))
        res[done : done + m] = cluster_stat(arrs, idx)
        done += m
    return res


def point(arrs):
    out = 0.0
    for sign, s, n in arrs:
        out += sign * (s.sum() / n.sum())
    return out


def within_item_boot(arrs, B, seed):
    """Sensitivity reading of 'item-stratified': resample reps WITHIN each item
    (all items kept) = binomial draw per item per arm."""
    rng = np.random.default_rng(seed)
    res = np.zeros(B)
    for sign, s, n in arrs:
        p = s / n
        draws = rng.binomial(n.astype(int)[None, :].repeat(B, 0), p[None, :].repeat(B, 0))
        res += sign * (draws.sum(axis=1) / n.sum())
    return res


def summarize(deltas, est, alpha_ci=0.05):
    lo, hi = np.percentile(deltas, [100 * alpha_ci / 2, 100 * (1 - alpha_ci / 2)])
    p_le0 = float(np.mean(deltas <= 0))
    return {
        "estimate": float(est),
        "ci95": [float(lo), float(hi)],
        "ci90": [float(x) for x in np.percentile(deltas, [5, 95])],
        "p_one_sided_le0": p_le0,
        "p_one_sided_plus1": float((np.sum(deltas <= 0) + 1) / (len(deltas) + 1)),
        "B": int(len(deltas)),
    }


def holm(pvals: dict, m=M_HOLM, alpha=ALPHA):
    """Step-down Holm over the testable members; m fixed (voided members keep slots)."""
    order = sorted(pvals.items(), key=lambda kv: kv[1])
    fired = {}
    steps = []
    stop = False
    for rank, (name, p) in enumerate(order):
        thr = alpha / (m - rank)
        ok = (not stop) and (p <= thr)
        steps.append({"member": name, "p": p, "threshold": thr, "fires": ok})
        fired[name] = ok
        if not ok:
            stop = True
    return fired, steps


COMPOSITE = {}
for pair, cell in [
    (("F", "F"), "C-B1"),
    (("F", "N"), "C-B2"), (("F", "G"), "C-B2"), (("F", "V"), "C-B2"),
    (("F", "R"), "C-B3"),
    (("N", "F"), "C-B4"), (("R", "F"), "C-B4"), (("V", "F"), "C-B4"), (("G", "F"), "C-B4"),
    (("N", "N"), "C-B5"), (("N", "G"), "C-B5"), (("N", "V"), "C-B5"), (("G", "N"), "C-B5"),
    (("G", "G"), "C-B5"), (("G", "V"), "C-B5"), (("V", "N"), "C-B5"), (("V", "G"), "C-B5"), (("V", "V"), "C-B5"),
    (("R", "N"), "C-B6"), (("R", "R"), "C-B6"), (("R", "G"), "C-B6"), (("R", "V"), "C-B6"),
    (("N", "R"), "C-B6"), (("V", "R"), "C-B6"), (("G", "R"), "C-B6"),
]:
    COMPOSITE[pair] = cell
assert len(COMPOSITE) == 25


# --------------------------------------------------------------------------
# self-tests that can fail
# --------------------------------------------------------------------------
def selftests(trials):
    # 1. synthetic bundle: markers under #, **, numbering; missing family -> None
    bundle = (
        "# Review\n\n## Q-sign: NO-DEFECT-sign\nprose\n\n**Q-boundary:**\n```\nFLAG — off by one\n```\n"
        "more\n1. Q-units: NONE — fine\n- NO-DEFECT-comparison\n"
    )
    assert p_segment(bundle, "sign") == "## Q-sign: NO-DEFECT-sign\nprose"
    assert p_segment(bundle, "boundary") == "**Q-boundary:**\n```\nFLAG — off by one\n```\nmore"
    assert p_segment(bundle, "units") == "1. Q-units: NONE — fine"
    assert p_segment(bundle, "comparison") == "- NO-DEFECT-comparison"
    assert p_segment(bundle, "exception") is None, "no-marker family must be MISSING"
    assert p_segment("Q-signature: fine", "sign") is None, "Q-signature must not match sign"
    assert line_marker("The Q-units answer is above") is None, "inline mention is not a marker"
    # 2. the known-MISSING row (opus P mf-sign-06 rep3 / units) must be MISSING
    t = trials[(TIER_ID["opus"], "P", "mf-sign-06", 3, None)]
    assert p_segment(t["result"], "units") is None, "known-MISSING row scored PRESENT"
    assert p_segment(t["result"], "sign") is not None
    # 3. normalize drops fence-only lines, collapses whitespace
    assert normalize_for_retention("```\nA  b\n```\n\n c") == "A b c"
    assert normalize_for_retention("```python\nx\n```") == "x"
    # 4. retention comparator re-lanes on mutation (not a mute detector)
    assert normalize_for_retention("Q-x: NONE") == normalize_for_retention("```\nQ-x:   NONE\n```")
    assert normalize_for_retention("Q-x: NONE") != normalize_for_retention("Q-x: NONE\nextra prose")
    # 5. Holm golden vector
    fired, steps = holm({"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.2})
    assert fired == {"a": True, "b": False, "c": False, "d": False}, steps
    fired, _ = holm({"a": 0.01, "b": 0.016, "c": 0.024, "d": 0.049})
    assert all(fired.values())
    # 6. key match is case-insensitive containment
    assert key_matched("The LAST Element is dropped", ["the last element", "zzz"]) == ["the last element"]
    # 7. bootstrap p on a degenerate positive effect is 0, on a null ~0.5
    s = np.array([3, 3, 3, 3]); n = np.array([3, 3, 3, 3]); z = np.zeros(4)
    d = boot([(1, s, n), (-1, z, n)], 4, 2000, 1)
    assert float(np.mean(d <= 0)) == 0.0
    print("selftests: PASS")


# --------------------------------------------------------------------------
# main recount
# --------------------------------------------------------------------------
def main():
    items = load_items()
    kt = json.load(open(DATA / "audit-key-table.json"))
    allowed = {r["item_id"]: list(r["allowed_families"]) for r in kt["table"]}
    fa_den = {r["item_id"]: r["fa_denominator"] for r in kt["table"]}
    assert kt["summary"]["dropped"] == 0 and kt["summary"]["surviving"] == 60
    c44 = json.load(open(DATA / "c44-selection.json"))
    c44_def = list(c44["defective"]); c44_clean = list(c44["clean"])
    assert len(c44_def) == 36 and len(c44_clean) == 8
    bank_def = sorted(i for i, d in items.items() if d["defect_class"] != "clean")
    bank_clean = sorted(i for i, d in items.items() if d["defect_class"] == "clean")
    assert len(bank_def) == 60 and len(bank_clean) == 20

    trials = load_trials()
    selftests(trials)

    final = load_jsonl(DATA / "final-rows.jsonl")
    assert len(final) == 7340
    lane1 = lane_verdicts(DATA / "adjudication-results.jsonl")
    lane2 = lane_verdicts(DATA / "adjudication-results-v2.jsonl")
    map2 = json.load(open(DATA / "scored-rows-v2.jsonl.adjmapping.json"))
    key2 = {}
    for aid, m in map2["entries"].items():
        k = (m["tier"], m["arm"], m["item"], m["rep"], m["family"])
        assert k not in key2, ("duplicate lane-2 key", k)
        key2[k] = aid

    # ---------------- per-row derivation (frozen BEFORE any comparison with the original) ----
    rows = []
    for r in final:
        tier, arm, item, rep, fam = r["tier"], r["arm"], r["item"], r["rep"], r["family"]
        key = (tier, arm, item, rep, fam)
        t = trials[(tier, arm, item, rep, fam if arm == "S" else None)]
        bundle = None
        if arm == "S":
            ctext = t["result"] or ""
            present = bool(ctext.strip())
        elif arm == "Sq":
            turns = [x for x in t["turns"] if x["family"] == fam]
            assert len(turns) == 1
            ctext = turns[0]["result"] or ""
            present = bool(ctext.strip())
        else:
            bundle = t["result"] or ""
            ctext = p_segment(bundle, fam)
            present = ctext is not None
        strict, loose = r["parser_strict_status"], r["parser_loose_status"]
        residual = strict == "MISSING" and loose != "PARSED"
        row = {
            "key": "|".join(map(str, key)), "tier": ID_TIER[tier], "arm": arm, "item": item, "rep": rep,
            "family": fam, "role": r["role"], "item_class": r["item_class"],
            "strict": strict, "loose": loose, "residual": residual,
            "present": present, "ctext_sha": sha(ctext), "ctext_len": None if ctext is None else len(ctext),
            "old_status": r["status"],
        }
        if strict == "PARSED":
            route = "MECH"
            verdict = mech_verdict(r["raw_block"])
            text = r["raw_block"]
        elif r.get("adjudicated"):
            old_pb = r["presented_block"]
            same = present and normalize_for_retention(old_pb) == normalize_for_retention(ctext)
            route = "RETAINED" if same else "RELANE"
            row["lane1_adj_id"] = r["adjudicated"]["adj_id"]
            row["lane1_verdict"] = r["adjudicated"]["verdict"]
            row["lane1_verdict_file"] = lane1["of_record"].get(r["adjudicated"]["adj_id"])
            row["extraction_gap"] = not present  # lane-1 row that the recount P rule cannot locate
            verdict = r["adjudicated"]["verdict"] if same else None
            text = ctext
        else:
            assert residual
            route = "NEWLANE" if present else "MISSING"
            verdict = None
            text = ctext
        row["route"] = route
        row["text"] = text
        row["bundle"] = bundle
        row["verdict"] = verdict
        rows.append(row)

    # ---------------- A1 presence ----------------
    res_rows = [x for x in rows if x["residual"]]
    a1 = {
        "residual_rows": len(res_rows),
        "present": sum(x["present"] for x in res_rows),
        "missing": sum(not x["present"] for x in res_rows),
        "missing_rows": [x["key"] for x in res_rows if not x["present"]],
        "present_by_arm": dict(collections.Counter(x["arm"] for x in res_rows if x["present"])),
        "present_by_tier": dict(collections.Counter(x["tier"] for x in res_rows if x["present"])),
        "present_by_role": dict(collections.Counter(x["role"] for x in res_rows if x["present"])),
        "lane1_rows_my_extraction_missing": [x["key"] for x in rows if x.get("extraction_gap")],
        "note": "S/Sq present iff whole turn non-empty; P present iff a segment opens at a line-start "
                "live-shape marker (Q-/NO-DEFECT-/FLAG-/NONE-<f>, case-insensitive, under #/**/bullets/numbering)",
    }

    # ---------------- A2 retention ----------------
    l1rows = [x for x in rows if x["route"] in ("RETAINED", "RELANE")]
    ret = [x for x in l1rows if x["route"] == "RETAINED"]
    rel = [x for x in l1rows if x["route"] == "RELANE"]
    a2 = {
        "lane1_rows": len(l1rows),
        "retained": len(ret), "relaned": len(rel),
        "retained_verdicts": dict(collections.Counter(x["verdict"] for x in ret)),
        "relaned_by_arm": dict(collections.Counter(x["arm"] for x in rel)),
        "relaned_by_tier": dict(collections.Counter(x["tier"] for x in rel)),
        "relaned_by_role": dict(collections.Counter(x["role"] for x in rel)),
        "relaned_old_lane1_verdicts": dict(collections.Counter(x["lane1_verdict"] for x in rel)),
        "retained_by_arm": dict(collections.Counter(x["arm"] for x in ret)),
        "lane1_table_vs_file_verdict_mismatch": [x["key"] for x in l1rows if x["lane1_verdict"] != x["lane1_verdict_file"]],
        "lane1_R1_R2_disagreements": len(lane1["disagree"]), "lane1_stages": lane1["stages"],
    }
    queue = rel + [x for x in rows if x["route"] == "NEWLANE"]
    a2["queue"] = {
        "total": len(queue),
        "by_arm": dict(collections.Counter(x["arm"] for x in queue)),
        "by_role": dict(collections.Counter(x["role"] for x in queue)),
        "by_tier": dict(collections.Counter(x["tier"] for x in queue)),
        "newly_present_by_tier": dict(collections.Counter(x["tier"] for x in rows if x["route"] == "NEWLANE")),
    }

    # original retention decision — COMPARED after the recount's is frozen (not copied)
    adjret = json.load(open(DATA / "scored-rows-v2.jsonl.adjretained.json"))
    orig_ret = set(adjret["entries"].keys())
    rec_ret = set(x["key"] for x in ret)
    a2["original_retained_file"] = {
        "n": adjret["n_retained"],
        "recount_minus_original": sorted(rec_ret - orig_ret),
        "original_minus_recount": sorted(orig_ret - rec_ret),
    }
    # adj-1182: the one lane-1 row whose batch text != presented_block (scrub) — both ways
    b1 = json.load(open(DATA / "scored-rows.jsonl.adjbatches.json"))["batches"]
    txt1 = {e["adjudication_id"]: e["text"] for lst in b1.values() for e in lst}
    flips = []
    for x in l1rows:
        aid = x["lane1_adj_id"]
        same_batch = x["present"] and normalize_for_retention(txt1[aid]) == normalize_for_retention(x["text"])
        if same_batch != (x["route"] == "RETAINED"):
            flips.append({"key": x["key"], "adj_id": aid, "route_presented_block": x["route"], "batch_text_same": same_batch})
    a2["retention_by_batch_text_flips"] = flips

    # ---------------- A3 lane-2 coverage ----------------
    gaps = {"my_queue_without_lane2_id": [], "my_queue_without_verdict": [], "lane2_ids_not_in_my_queue": [],
            "lane2_verdict_of_record_source": "primary R1 (no tiebreak/R3 stage present)" if not lane2["tiebreak"] else "tiebreak where present"}
    myq = set(x["key"] for x in queue)
    for x in queue:
        k = tuple(x["key"].split("|")); k = (k[0], k[1], k[2], int(k[3]), k[4])
        aid = key2.get(k)
        if aid is None:
            gaps["my_queue_without_lane2_id"].append(x["key"])
            x["lane2_adj_id"] = None
            continue
        x["lane2_adj_id"] = aid
        v = lane2["of_record"].get(aid)
        if v is None:
            gaps["my_queue_without_verdict"].append(x["key"])
        x["verdict"] = v
    for k, aid in key2.items():
        kk = "|".join(map(str, k))
        if kk not in myq:
            gaps["lane2_ids_not_in_my_queue"].append({"adj_id": aid, "key": kk})
    # composition fallback for gaps (explicit, flagged)
    for x in queue:
        if x.get("lane2_adj_id") is None or x["verdict"] is None:
            x["gap_fallback"] = True
            if x["route"] == "RELANE":
                x["verdict"] = x["lane1_verdict"]
            else:
                x["verdict"] = None
    a3 = {
        "lane2_ids": len(key2), "lane2_stages": lane2["stages"],
        "lane2_R1_R2_disagreements": len(lane2["disagree"]),
        "lane2_armguess_values": dict(collections.Counter(lane2["armguess"].values())),
        "lane1_armguess_values": dict(collections.Counter(lane1["armguess"].values())),
        "gaps": gaps, "n_gap_fallback_rows": sum(1 for x in queue if x.get("gap_fallback")),
        "lane2_verdicts_of_record": dict(collections.Counter(lane2["of_record"].values())),
    }
    # lane-2 INPUT text check: what the judges saw vs the recount §9 text (normalized)
    b2 = json.load(open(DATA / "scored-rows-v2.jsonl.adjbatches.json"))
    txt2 = {e["adjudication_id"]: e["text"] for lst in b2["batches"].values() for e in lst}
    same_n = diff = raw_same = 0; diffs = []
    for x in queue:
        aid = x.get("lane2_adj_id")
        if aid is None:
            continue
        orig_t = txt2[aid]
        if orig_t == (x["text"] or ""):
            raw_same += 1
        if normalize_for_retention(orig_t) == normalize_for_retention(x["text"]):
            same_n += 1
        else:
            diff += 1
            if len(diffs) < 25:
                diffs.append({"key": x["key"], "adj_id": aid, "original_len": len(orig_t), "recount_len": len(x["text"] or ""),
                              "original_head": orig_t[:160], "recount_head": (x["text"] or "")[:160]})
    a3["lane2_input_text_vs_recount"] = {"normalized_equal": same_n, "normalized_differ": diff, "raw_equal": raw_same,
                                      "examples": diffs, "original_queue_size": b2["queue_size"]}

    # ---------------- A4 composition (V1) + A6 variants ----------------
    def compose(role, verdict, text, keys, fam, allow):
        km = key_matched(text, keys)
        if role == "target":
            st = "CATCH" if (verdict == "FLAG" and km) else "NON-CATCH"
            return st, bool(km), None
        if verdict == "FLAG":
            if role == "clean":
                return "FA", None, False
            if fam in allow and km:
                return "HIT-ALT", None, None
            return "FA", None, bool(km)
        if verdict == "NONE":
            return "NO-FLAG", None, None
        return "SILENT", None, None  # missing / NEITHER / no verdict

    old_by_key = {"|".join(map(str, (r["tier"], r["arm"], r["item"], r["rep"], r["family"]))): r for r in final}
    mech_recomp_mismatch = []
    for x in rows:
        keys = items[x["item"]]["defect_keys"]; allow = allowed.get(x["item"], [])
        st, hit, kmwf = compose(x["role"], x["verdict"], x["text"], keys, x["family"], allow)
        if x["route"] == "MECH":
            # ruling 1 byte-pins mechanical rows to the committed table: COPY, and
            # report the recount recomputation as an agreement check only
            o = old_by_key[x["key"]]
            x["mech_recomputed_status"] = st
            if st != o["status"]:
                mech_recomp_mismatch.append(x["key"])
            st = o["status"]
            hit = o.get("hit") if x["role"] == "target" else None
            kmwf = o.get("key_matched_wrong_family") if st == "FA" else None
        x["status_v1"] = st; x["hit_v1"] = hit; x["kmwf_v1"] = kmwf
        # V2: P FLAG rows key-match over the WHOLE bundle
        if x["arm"] == "P" and x["verdict"] == "FLAG":
            st2, hit2, kmwf2 = compose(x["role"], x["verdict"], x["bundle"], keys, x["family"], allow)
        else:
            st2, hit2, kmwf2 = st, hit, kmwf
        x["status_v2"] = st2; x["hit_v2"] = hit2; x["kmwf_v2"] = kmwf2
        # V3: permissive-route (NEWLANE) S/Sq rows PRESENT only with an asked-family marker anywhere
        v3_missing = (x["route"] == "NEWLANE" and x["arm"] in ("S", "Sq")
                      and not _INLINE_MARK[x["family"]].search(x["text"] or ""))
        x["v3_demoted"] = v3_missing
        if v3_missing:
            st3, hit3, kmwf3 = compose(x["role"], None, None, keys, x["family"], allow)
        else:
            st3, hit3, kmwf3 = st, hit, kmwf
        x["status_v3"] = st3; x["hit_v3"] = hit3; x["kmwf_v3"] = kmwf3

    # mechanical rows must equal the committed table (ruling 1 byte-pin) — check, then report
    a4 = {
        "mech_rows": sum(1 for x in rows if x["route"] == "MECH"),
        "mech_recomputed_status_mismatch_vs_committed": mech_recomp_mismatch,
        "routes": dict(collections.Counter(x["route"] for x in rows)),
        "status_v1": dict(collections.Counter(x["status_v1"] for x in rows)),
        "status_v2": dict(collections.Counter(x["status_v2"] for x in rows)),
        "status_v3": dict(collections.Counter(x["status_v3"] for x in rows)),
        "old_status": dict(collections.Counter(x["old_status"] for x in rows)),
        "v3_demoted_rows": sum(1 for x in rows if x["v3_demoted"]),
        "v3_demoted_by_role": dict(collections.Counter(x["role"] for x in rows if x["v3_demoted"])),
        "v3_demoted_lane_verdicts": dict(collections.Counter(x["verdict"] for x in rows if x["v3_demoted"])),
        "v2_changed_rows": [x["key"] for x in rows if x["status_v2"] != x["status_v1"] or x["kmwf_v2"] != x["kmwf_v1"]],
        "neither_rows": [x["key"] for x in rows if x["verdict"] == "NEITHER"],
    }
    table = collections.Counter()
    for x in rows:
        table[(x["tier"], x["arm"], x["role"], x["status_v1"])] += 1
    a4["status_x_arm_x_tier_x_role_v1"] = {f"{t}|{a}|{ro}|{s}": n for (t, a, ro, s), n in sorted(table.items())}
    tr_ = collections.Counter()
    for x in rows:
        tr_[(x["tier"], x["arm"], x["route"])] += 1
    a4["route_x_arm_x_tier"] = {f"{t}|{a}|{r}": n for (t, a, r), n in sorted(tr_.items())}
    # status transitions old -> V1 for the 471 residual + 394 relaned
    trans = collections.Counter((x["old_status"], x["status_v1"]) for x in rows if x["route"] in ("NEWLANE", "RELANE", "MISSING"))
    a4["transitions_old_to_v1_on_touched_rows"] = {f"{o}->{n}": c for (o, n), c in sorted(trans.items())}

    # J.4: clean (item,family) pairs with >=1 FLAG under V1 vs the checker file
    j4 = load_jsonl(DATA / "j4-verdicts-v2.jsonl")
    j4_pairs = {(j["item"], j["family"]) for j in j4}
    my_pairs = collections.Counter((x["item"], x["family"]) for x in rows if x["role"] == "clean" and x["status_v1"] == "FA")
    a4["j4"] = {
        "checker_pairs": len(j4_pairs), "checker_verdicts": dict(collections.Counter(j["verdict"] for j in j4)),
        "my_clean_flag_pairs": len(my_pairs),
        "flag_pairs_not_checked": sorted([f"{i}|{f}|n_flags={n}" for (i, f), n in my_pairs.items() if (i, f) not in j4_pairs]),
        "checked_pairs_with_no_flag_now": sorted([f"{i}|{f}" for (i, f) in j4_pairs if (i, f) not in my_pairs]),
        "clean_sf_02_units_rows": [
            {"key": x["key"], "route": x["route"], "verdict": x["verdict"], "status_v1": x["status_v1"], "old_status": x["old_status"]}
            for x in rows if x["item"] == "clean-sf-02" and x["family"] == "units"
        ],
        "falsified_cleans_of_record": json.load(open(DATA / "j4-falsified-cleans-v2.json")),
    }

    # ---------------- A7 keyword re-derivation ----------------
    lane_flag_targets = [x for x in rows if x["role"] == "target" and x["route"] in ("RETAINED", "RELANE", "NEWLANE") and x["verdict"] == "FLAG"]
    a7 = {
        "target_rows_lane_verdict_FLAG": len(lane_flag_targets),
        "key_matched": sum(1 for x in lane_flag_targets if x["hit_v1"]),
        "not_matched": sum(1 for x in lane_flag_targets if not x["hit_v1"]),
        "by_route": {r: [sum(1 for x in lane_flag_targets if x["route"] == r), sum(1 for x in lane_flag_targets if x["route"] == r and x["hit_v1"])] for r in ("RETAINED", "RELANE", "NEWLANE")},
        "by_tier_arm": {f"{t}|{a}": [sum(1 for x in lane_flag_targets if x["tier"] == t and x["arm"] == a), sum(1 for x in lane_flag_targets if x["tier"] == t and x["arm"] == a and x["hit_v1"])] for t in TIER_ID for a in ("P", "S", "Sq")},
        "not_matched_rows": [x["key"] for x in lane_flag_targets if not x["hit_v1"]][:60],
    }

    # ---------------- A5 endpoints (per variant) ----------------
    def endpoints(variant: str, B=B_REG, seed=SEED, want_full=True):
        hk, sk = f"hit_{variant}", f"status_{variant}"

        # pre-index target rows
        tgt = collections.defaultdict(lambda: [0, 0])
        for x in rows:
            if x["role"] == "target":
                c = tgt[(x["tier"], x["arm"], x["item"])]
                c[0] += 1 if x[hk] else 0; c[1] += 1

        def arrs_for(tier, arm, pool):
            s = np.array([tgt[(tier, arm, it)][0] for it in pool], dtype=float)
            n = np.array([tgt[(tier, arm, it)][1] for it in pool], dtype=float)
            assert (n > 0).all(), (tier, arm, "empty item in pool")
            return s, n

        def contrast(tier, a1, a2, pool):
            s1, n1 = arrs_for(tier, a1, pool); s2, n2 = arrs_for(tier, a2, pool)
            return [(1, s1, n1), (-1, s2, n2)]

        members = {
            "H-B1": ("haiku", "S", "P", bank_def),
            "H-B2": ("sonnet", "S", "P", c44_def),
            "H-B4": ("haiku", "Sq", "P", bank_def),
        }
        out = {"members": {}, "descriptive": {}}
        pvals = {}
        for name, (tier, a1, a2, pool) in members.items():
            arrs = contrast(tier, a1, a2, pool)
            d = boot(arrs, len(pool), B, seed)
            rec = summarize(d, point(arrs))
            rec["pool_n_items"] = len(pool)
            rec["rates"] = {a1: float(arrs[0][1].sum() / arrs[0][2].sum()), a2: float(arrs[1][1].sum() / arrs[1][2].sum())}
            rec["n_obs"] = {a1: int(arrs[0][2].sum()), a2: int(arrs[1][2].sum())}
            rec["guard"] = [a for a, rt in rec["rates"].items() if rt > GUARD_HI or rt < GUARD_LO]
            if want_full:
                rec["p_within_item_variant"] = float(np.mean(within_item_boot(arrs, B, seed) <= 0))
            out["members"][name] = rec
            pvals[name] = rec["p_one_sided_le0"]
        # H-B3 interaction on C44, one item draw drives both tiers
        hS, hSn = arrs_for("haiku", "S", c44_def); hP, hPn = arrs_for("haiku", "P", c44_def)
        oS, oSn = arrs_for("opus", "S", c44_def); oP, oPn = arrs_for("opus", "P", c44_def)
        arrs3 = [(1, hS, hSn), (-1, hP, hPn), (-1, oS, oSn), (1, oP, oPn)]
        d3 = boot(arrs3, len(c44_def), B, seed)
        rec = summarize(d3, point(arrs3))
        rec["pool_n_items"] = len(c44_def)
        rec["legs"] = {"haiku_S-P_on_C44": float(hS.sum() / hSn.sum() - hP.sum() / hPn.sum()),
                       "opus_S-P_on_C44": float(oS.sum() / oSn.sum() - oP.sum() / oPn.sum())}
        rec["rates"] = {"haiku_S": float(hS.sum() / hSn.sum()), "haiku_P": float(hP.sum() / hPn.sum()),
                        "opus_S": float(oS.sum() / oSn.sum()), "opus_P": float(oP.sum() / oPn.sum())}
        rec["n_obs"] = {"haiku_S": int(hSn.sum()), "haiku_P": int(hPn.sum()), "opus_S": int(oSn.sum()), "opus_P": int(oPn.sum())}
        rec["guard"] = [a for a, rt in rec["rates"].items() if rt > GUARD_HI or rt < GUARD_LO]
        if want_full:
            rec["p_within_item_variant"] = float(np.mean(within_item_boot(arrs3, B, seed) <= 0))
        out["members"]["H-B3"] = rec
        pvals["H-B3"] = rec["p_one_sided_le0"]

        # states: V > G > R > F > N
        testable = {k: v for k, v in pvals.items() if not out["members"][k]["guard"]}
        fired, steps = holm(testable)
        states = {}
        for name, rec in out["members"].items():
            if rec["guard"]:
                st = "G"
            elif rec["ci95"][1] < 0:
                st = "R"
            elif fired.get(name):
                st = "F"
            else:
                st = "N"
            states[name] = st
        out["holm"] = {"steps": steps, "fired": fired, "m": M_HOLM, "alpha": ALPHA}
        out["states"] = states
        pair = (states["H-B1"], states["H-B3"])
        out["composite_cell"] = COMPOSITE[pair]
        out["composite_pair"] = list(pair)
        if out["composite_cell"] == "C-B5":
            if states["H-B1"] == "N":
                ub = out["members"]["H-B1"]["ci95"][1]
                out["c_b5_subread"] = "RITUAL (H-B1=N, 95% upper < +0.10)" if ub < SESOI else "INCONCLUSIVE (H-B1=N, 95% upper >= +0.10)"
            else:
                out["c_b5_subread"] = "headline unmeasured (H-B1 in {G,V})"
        out["qualifiers"] = {"H-B2": states["H-B2"], "H-B4": states["H-B4"]}

        # band read at opus (TOST 90% CI, ±0.20), TTFLAT-first precedence
        arrsO = contrast("opus", "S", "P", c44_def)
        dO = boot(arrsO, len(c44_def), B, seed)
        recO = summarize(dO, point(arrsO))
        recO["rates"] = {"S": float(arrsO[0][1].sum() / arrsO[0][2].sum()), "P": float(arrsO[1][1].sum() / arrsO[1][2].sum())}
        recO["guard"] = [a for a, rt in recO["rates"].items() if rt > GUARD_HI or rt < GUARD_LO]
        lo90, hi90 = recO["ci90"]
        flat = lo90 >= -BAND and hi90 <= BAND
        live = lo90 > 0 or hi90 < 0
        if recO["guard"] or states["H-B3"] == "V":
            band = "VOID (opus guard / H-B3 void)"
        elif flat:
            band = "C-B-TTFLAT"
        elif live:
            band = "C-B-TTLIVE(+)" if lo90 > 0 else "C-B-TTLIVE(-)"
        else:
            band = "C-B-TTSPAN"
        recO["band_cell"] = band
        recO["flat_condition"] = flat; recO["live_condition"] = live
        out["band_opus"] = recO
        out["g_fab"] = bool(fired.get("H-B3")) and band == "C-B-TTLIVE(+)"

        # INVERSE-AT-TIER stamps + per-tier S-P (sonnet on C44, haiku on bank)
        tier_sp = {}
        for tier, pool in [("haiku", bank_def), ("sonnet", c44_def), ("opus", c44_def)]:
            arrs = contrast(tier, "S", "P", pool)
            d = boot(arrs, len(pool), B, seed)
            r_ = summarize(d, point(arrs))
            r_["inverse_at_tier"] = r_["ci95"][1] < 0
            tier_sp[tier] = r_
        out["tier_S_minus_P"] = tier_sp
        out["inverse_at_tier_stamps"] = [t for t, r_ in tier_sp.items() if r_["inverse_at_tier"]]

        # descriptive CI-only reads
        for name, (tier, a1, a2, pool) in {
            "S-Sq_haiku": ("haiku", "S", "Sq", bank_def),
            "S-Sq_sonnet": ("sonnet", "S", "Sq", c44_def),
            "Sq-P_sonnet": ("sonnet", "Sq", "P", c44_def),
            "haiku_S-P_on_C44": ("haiku", "S", "P", c44_def),
        }.items():
            arrs = contrast(tier, a1, a2, pool)
            d = boot(arrs, len(pool), B, seed)
            out["descriptive"][name] = summarize(d, point(arrs))

        # ---------- FA co-read (§11.4) ----------
        fa = {}
        for tier, def_pool, clean_pool in [("haiku", bank_def, bank_clean), ("sonnet", c44_def, c44_clean), ("opus", c44_def, c44_clean)]:
            arms = ["P", "S", "Sq"] if tier != "opus" else ["P", "S"]
            fa[tier] = {}
            for cls in ["multi_file", "single_function"]:
                cl = [i for i in clean_pool if items[i]["item_class"] == cls]
                df = [i for i in def_pool if items[i]["item_class"] == cls]
                # per (arm,item): class1 any-FLAG per item-rep ; class2/3 numerators + denominators
                c1 = collections.defaultdict(lambda: [0, 0]); c1row = collections.defaultdict(lambda: [0, 0])
                c2 = collections.defaultdict(lambda: [0, 0]); c2incl = collections.defaultdict(lambda: [0, 0]); c3 = collections.defaultdict(lambda: [0, 0])
                reps_seen = collections.defaultdict(set)
                for x in rows:
                    if x["tier"] != tier or x["item_class"] != cls:
                        continue
                    if x["role"] == "clean" and x["item"] in cl:
                        k = (x["arm"], x["item"])
                        reps_seen[k].add(x["rep"])
                        c1row[k][0] += 1 if x[sk] == "FA" else 0; c1row[k][1] += 1
                    elif x["role"] == "off_family" and x["item"] in df:
                        k = (x["arm"], x["item"])
                        is_fa = x[sk] == "FA"
                        if x["family"] in allowed.get(x["item"], []):
                            c2incl[k][0] += 1 if is_fa else 0; c2incl[k][1] += 1
                        else:
                            c2[k][0] += 1 if is_fa else 0; c2[k][1] += 1
                            c2incl[k][0] += 1 if is_fa else 0; c2incl[k][1] += 1
                            c3[k][0] += 1 if (is_fa and x.get(f"kmwf_{variant}")) else 0; c3[k][1] += 1
                # class-1 item-rep any-FLAG
                anyflag = collections.defaultdict(lambda: [0, 0])
                for x in rows:
                    if x["tier"] == tier and x["role"] == "clean" and x["item"] in cl:
                        k = (x["arm"], x["item"], x["rep"])
                        anyflag[k][0] = max(anyflag[k][0], 1 if x[sk] == "FA" else 0); anyflag[k][1] = 1
                for (a, it, rp), (f_, _) in anyflag.items():
                    c1[(a, it)][0] += f_; c1[(a, it)][1] += 1

                def rate_and_diff(counts, pool, a1="S", a2="P"):
                    s1 = np.array([counts[(a1, it)][0] for it in pool], float); n1 = np.array([counts[(a1, it)][1] for it in pool], float)
                    s2 = np.array([counts[(a2, it)][0] for it in pool], float); n2 = np.array([counts[(a2, it)][1] for it in pool], float)
                    if not (n1 > 0).all() or not (n2 > 0).all():
                        return {"undefined": True}
                    arrs = [(1, s1, n1), (-1, s2, n2)]
                    d = boot(arrs, len(pool), B, seed)
                    r_ = summarize(d, point(arrs))
                    r_["rate"] = {a1: float(s1.sum() / n1.sum()), a2: float(s2.sum() / n2.sum())}
                    r_["n"] = {a1: int(n1.sum()), a2: int(n2.sum())}
                    r_["all_zero"] = bool(s1.sum() == 0 and s2.sum() == 0)
                    lo, hi = r_["ci95"]
                    r_["bound_point_ok"] = r_["estimate"] <= FA_BOUND and (r_["rate"][a2] == 0 or r_["rate"][a1] <= 2 * r_["rate"][a2])
                    r_["bound_state"] = "IN-BOUND" if hi <= FA_BOUND else ("OUT-OF-BOUND(FACON)" if lo > FA_BOUND else "FAUNRES")
                    r_["s_raises_fa"] = lo > 0
                    r_["n_clusters"] = len(pool)
                    return r_

                fa[tier][cls] = {
                    "class1_clean_anyflag_itemrep": rate_and_diff(c1, cl),
                    "class1_clean_flag_rowlevel": rate_and_diff(c1row, cl),
                    "class2_offfamily_fa_nonallowed": rate_and_diff(c2, df),
                    "class2_offfamily_fa_inclusive_allowed": rate_and_diff(c2incl, df),
                    "class3_keymatched_wrong_family": rate_and_diff(c3, df),
                }
                if "Sq" in arms:
                    fa[tier][cls]["class1_Sq_minus_P"] = rate_and_diff(c1, cl, "Sq", "P")
                    fa[tier][cls]["class2_Sq_minus_P"] = rate_and_diff(c2, df, "Sq", "P")
        out["fa"] = fa
        # criterion-shift stamp per tier: S raises hits (CI>0) AND any FA class S-P CI>0
        crit = {}
        for tier in ["haiku", "sonnet", "opus"]:
            hits_up = tier_sp[tier]["ci95"][0] > 0
            fa_up = [f"{cls}/{c}" for cls in fa[tier] for c, r_ in fa[tier][cls].items()
                     if c in ("class1_clean_anyflag_itemrep", "class2_offfamily_fa_nonallowed", "class3_keymatched_wrong_family")
                     and not r_.get("undefined") and r_["s_raises_fa"]]
            crit[tier] = {"hits_ci_above_0": hits_up, "fa_classes_ci_above_0": fa_up, "stamp": bool(hits_up and fa_up)}
        out["crit"] = crit
        fa_stamps = []
        for tier in fa:
            for cls in fa[tier]:
                for c in ("class1_clean_anyflag_itemrep", "class2_offfamily_fa_nonallowed", "class3_keymatched_wrong_family"):
                    r_ = fa[tier][cls][c]
                    if not r_.get("undefined") and r_["bound_state"] != "IN-BOUND":
                        fa_stamps.append(f"{tier}/{cls}/{c}: {r_['bound_state']}")
        out["fa_stamps"] = fa_stamps
        return out

    ep_v1 = endpoints("v1")
    ep_v2 = endpoints("v2")
    ep_v3 = endpoints("v3")

    # format-noncompliance per arm×tier under the PINNED strict grammar (+ the recount presence-based recovery)
    fmt = {}
    cells = collections.defaultdict(list)
    for x in rows:
        cells[(x["tier"], x["arm"])].append(x)
    for (tier, arm), grp in sorted(cells.items()):
        n = len(grp); nc = sum(1 for x in grp if x["strict"] != "PARSED")
        miss = sum(1 for x in grp if x["route"] == "MISSING")
        fmt[f"{tier}|{arm}"] = {
            "rows": n, "strict_noncompliant": nc, "rate_strict": nc / n, "format_degraded_stamp": nc / n > 0.25,
            "text_missing_by_presence_rule": miss, "rate_missing": miss / n,
            "noncompliant_with_text_present": nc - miss,
            "conditional_on_well_formed_target_catch": None,
        }
        tg = [x for x in grp if x["role"] == "target"]
        wf = [x for x in tg if x["strict"] == "PARSED"]
        fmt[f"{tier}|{arm}"]["target_catch_unconditional"] = (sum(1 for x in tg if x["hit_v1"]) / len(tg)) if tg else None
        fmt[f"{tier}|{arm}"]["conditional_on_well_formed_target_catch"] = (sum(1 for x in wf if x["hit_v1"]) / len(wf)) if wf else None

    # ---------------- A8 Holm decision + MC sensitivity ----------------
    def mc_sweep(variant, seeds, B):
        rec = {"seeds": list(seeds), "B": B, "per_member": {}, "cells": collections.Counter(), "bands": collections.Counter()}
        per = collections.defaultdict(list)
        for sd in seeds:
            e = endpoints(variant, B=B, seed=sd, want_full=False)
            rec["cells"][e["composite_cell"]] += 1
            rec["bands"][e["band_opus"]["band_cell"]] += 1
            thr = {s["member"]: s["threshold"] for s in e["holm"]["steps"]}
            for m_, r_ in e["members"].items():
                per[m_].append({"seed": sd, "p": r_["p_one_sided_le0"], "state": e["states"][m_], "holm_threshold": thr.get(m_), "fires": e["states"][m_] == "F"})
        for m_, lst in per.items():
            ps = [z["p"] for z in lst]
            rec["per_member"][m_] = {"fire_frequency": sum(z["fires"] for z in lst) / len(lst), "p_min": min(ps), "p_max": max(ps),
                                     "p_mean": float(np.mean(ps)), "states": dict(collections.Counter(z["state"] for z in lst)),
                                     "thresholds_faced": dict(collections.Counter(str(z["holm_threshold"]) for z in lst)), "runs": lst}
        rec["cells"] = dict(rec["cells"]); rec["bands"] = dict(rec["bands"])
        return rec

    seeds = [SEED] + list(range(1, 30))
    a8 = {"holm_v1": ep_v1["holm"], "mc_10k_seed_sweep_v1": mc_sweep("v1", seeds, B_REG)}
    big = endpoints("v1", B=1_000_000, seed=SEED, want_full=False)
    a8["mc_1e6_v1"] = {"members": {m_: {"p": r_["p_one_sided_le0"], "ci95": r_["ci95"], "estimate": r_["estimate"], "state": big["states"][m_]} for m_, r_ in big["members"].items()},
                       "holm": big["holm"], "composite_cell": big["composite_cell"], "band": big["band_opus"]["band_cell"], "band_ci90": big["band_opus"]["ci90"]}

    # ---------------- write ----------------
    out = {
        "meta": {
            "phase": "A (blind)", "seed": SEED, "B": B_REG, "alpha": ALPHA, "m": M_HOLM,
            "inputs": "see module docstring", "rows": len(rows),
            "presence_rule": a1["note"],
            "retention_rule": "retain iff normalize(presented_block [lane-1 adjudicator-seen text]) == normalize(recount §9 text); normalize = drop fence-only lines, collapse whitespace",
            "bootstrap": "item-cluster resample with replacement (cluster=item; H-B3 one draw drives both tiers), 10k draws, numpy default_rng(1512); p = frac(delta* <= 0); percentile CIs",
            "fa_class1_unit": "clean item-rep any-FLAG (row-level co-reported)",
            "fa_class2_numerator": "FA rows on NON-allowed families / Σ(4-|allowed|) (inclusive variant co-reported)",
            "neither_composition": "NEITHER composes as no-assertion (SILENT / NON-CATCH)",
            "band_precedence": "TTFLAT-first (flat and live can co-hold); both conditions reported",
        },
        "A1_presence": a1, "A2_retention": a2, "A3_lane2_coverage": a3, "A4_composition": a4,
        "A5_endpoints_v1": ep_v1, "A6_coreads": {"v2": ep_v2, "v3": ep_v3,
            "moves": {
                "states_v1": ep_v1["states"], "states_v2": ep_v2["states"], "states_v3": ep_v3["states"],
                "cell_v1": ep_v1["composite_cell"], "cell_v2": ep_v2["composite_cell"], "cell_v3": ep_v3["composite_cell"],
                "band_v1": ep_v1["band_opus"]["band_cell"], "band_v2": ep_v2["band_opus"]["band_cell"], "band_v3": ep_v3["band_opus"]["band_cell"],
                "fa_stamps_v1": ep_v1["fa_stamps"], "fa_stamps_v2": ep_v2["fa_stamps"], "fa_stamps_v3": ep_v3["fa_stamps"],
                "criterion_shift_stamp_v1": {t: w["stamp"] for t, w in ep_v1["crit"].items()}, "criterion_shift_stamp_v2": {t: w["stamp"] for t, w in ep_v2["crit"].items()}, "criterion_shift_stamp_v3": {t: w["stamp"] for t, w in ep_v3["crit"].items()},
            }},
        "A5_format_noncompliance": fmt, "A7_keyword_rederivation": a7, "A8_holm_mc": a8,
    }
    OUT.mkdir(exist_ok=True)
    with open(OUT / "blind-pass.json", "w") as f:
        json.dump(out, f, indent=1, default=str)
    with open(OUT / "recount-rows.jsonl", "w") as f:
        for x in rows:
            y = {k: v for k, v in x.items() if k not in ("text", "bundle")}
            y["text_sha"] = sha(x["text"])
            f.write(json.dumps(y) + "\n")
    print("wrote", OUT / "blind-pass.json", "and recount-rows.jsonl")
    return out


if __name__ == "__main__":
    o = main()
    # terse console summary
    print("A1", {k: o["A1_presence"][k] for k in ("residual_rows", "present", "missing", "missing_rows")})
    print("A2", {k: o["A2_retention"][k] for k in ("retained", "relaned", "retained_verdicts")}, o["A2_retention"]["queue"])
    print("A3 gaps", {k: (len(v) if isinstance(v, list) else v) for k, v in o["A3_lane2_coverage"]["gaps"].items()}, o["A3_lane2_coverage"]["lane2_input_text_vs_recount"]["normalized_equal"], o["A3_lane2_coverage"]["lane2_input_text_vs_recount"]["normalized_differ"])
    print("A4 status v1", o["A4_composition"]["status_v1"])
    for m_, r in o["A5_endpoints_v1"]["members"].items():
        print(m_, round(r["estimate"], 4), r["ci95"], "p", r["p_one_sided_le0"], "guard", r["guard"])
    print("states", o["A5_endpoints_v1"]["states"], "cell", o["A5_endpoints_v1"]["composite_cell"], o["A5_endpoints_v1"].get("c_b5_subread"), "band", o["A5_endpoints_v1"]["band_opus"]["band_cell"])
    print("moves", o["A6_coreads"]["moves"])
    print("A7", {k: o["A7_keyword_rederivation"][k] for k in ("target_rows_lane_verdict_FLAG", "key_matched", "not_matched")})
