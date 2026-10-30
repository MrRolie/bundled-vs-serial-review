"""score_table.py — the full §9 scored table: every (tier, arm, item,
rep, question-family) row through the REAL scorer (answer_parser/scorer
only; this file adds row plumbing, never scoring logic).

Row source per arm: P = the bundle text scored per family; S = the
record's own single family; Sq = each turn's own text per its family.
Target rows ride `score_target_question`; off-family and clean rows ride
`score_off_family_question` with the §5.3 allowances from the certified
key table (allowed_family_keys stays the registered default —
item_defect_keys — no per-allowed-family key lists exist; disclosed).
Instrument-failure records are refused loudly if present (the completed
batches carry none; a future partial file must never silently score).
Denominators are COUNTED from emitted rows, never derived.

CORRECTED PASS (registration/amendments/2026-08-27-corrected-scoring-pass.md;
wired 2026-08-27): every
registered-chain row is overlaid by `presence.compose_with_presence` —
permissive PRESENCE (authored from live weak-tier shapes) routes strict-
MISSING ∧ ¬loose-PARSED rows whose text EXISTS to the BORDERLINE lane instead
of mechanical NON-CATCH/SILENT, and every BORDERLINE row's `presented_block`
is §9's scored text (P: the family's own segment; S/Sq: the whole turn) —
never a parser fragment. Rows also carry `route`, `presence`, `scored_text`.
The pinned parser is untouched; PARSED rows keep their disposition and
`raw_block` byte-for-byte.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from answer_parser import FAMILIES  # noqa: E402
from presence import compose_with_presence  # noqa: E402
from scorer import (  # noqa: E402
    is_instrument_failure,
    score_off_family_question,
    score_target_question,
    sq_turn_text,
    trial_text,
)

ROOT = _HERE.parent
ITEMS_DIRS = (ROOT / "materials/items",)
TIERS = ("claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5")


def load_items() -> dict[str, dict]:
    items = {}
    for d in ITEMS_DIRS:
        for p in sorted(d.glob("*.json")):
            it = json.loads(p.read_text())
            items[it["id"]] = it
    return items


def load_allowances(key_table_path: Path) -> dict[str, list[str]]:
    kt = json.loads(key_table_path.read_text())
    return {r["item_id"]: r["allowed_families"] for r in kt["table"]}


def score_one(text: str | None, family: str, item: dict,
              allowed: list[str]) -> dict:
    if item["defect_class"] == family:
        row = score_target_question(text, family, item["defect_keys"])
        row["role"] = "target"
    else:
        row = score_off_family_question(
            text, family,
            item_defect_keys=item.get("defect_keys") or [],
            allowed_families=allowed)
        row["role"] = "off_family" if item["defect_class"] != "clean" else "clean"
    return row

def rows_for_record(rec: dict, items: dict[str, dict],
                    allowances: dict[str, list[str]], tier: str) -> list[dict]:
    if is_instrument_failure(rec):
        raise SystemExit(
            f"REFUSE: instrument-failure record in a scored batch "
            f"(item={rec.get('item')}, arm={rec.get('arm')}, rep={rec.get('rep')}) "
            "— failures are unreliability-denominator rows, never scored")
    item = items[rec["item"]]
    allowed = allowances.get(rec["item"], [])
    out = []
    if rec["arm"] == "P":
        text = trial_text(rec)
        fams = FAMILIES
        texts = {f: text for f in fams}
    elif rec["arm"] == "S":
        fams = (rec["family"],)
        texts = {rec["family"]: trial_text(rec)}
    else:  # Sq
        fams = tuple(t["family"] for t in rec["turns"])
        texts = {f: sq_turn_text(rec, f) for f in fams}
    for fam in fams:
        row = score_one(texts[fam], fam, item, allowed)
        # corrected pass: permissive PRESENCE + §9 scored-text overlay —
        # strict-MISSING ∧ ¬loose-PARSED rows whose text exists ride the
        # BORDERLINE lane; every BORDERLINE row presents §9's text (P: the
        # family's segment; S/Sq: the whole turn), never a parser fragment.
        # presence.compose_with_presence owns the rule (tested there).
        row = compose_with_presence(row, arm=rec["arm"], text=texts[fam])
        out.append({
            "tier": tier, "arm": rec["arm"], "item": rec["item"],
            "rep": rec["rep"], "item_class": item["item_class"],
            "defect_class": item["defect_class"],
            "allowed_families": allowed, **row,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path,
                    default=ROOT / "data/dispatches")
    ap.add_argument("--key-table", type=Path,
                    default=ROOT / "data/frozen/audit-key-table.json")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    items = load_items()
    allowances = load_allowances(args.key_table)
    rows = []
    for tier in TIERS:
        path = args.data_dir / f"{tier}.jsonl"
        for ln in path.read_text().splitlines():
            if not ln.strip():
                continue
            rows.extend(rows_for_record(json.loads(ln), items, allowances, tier))
    with args.out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    by = Counter((r["tier"].split("-")[1], r["arm"], r["role"], r["status"])
                 for r in rows)
    print(f"{len(rows)} scored rows")
    for k in sorted(by):
        print(" ", k, by[k])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
