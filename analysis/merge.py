"""merge.py — compose the post-adjudication rows: every BORDERLINE row of the
mechanically scored table (score_table.py output) is resolved by its verdict
of record (data/verdicts.jsonl) through the SAME mechanical chain as parsed
rows (key-matching via `scorer._keys_match`, never restated).

This is a standalone re-implementation of the study's original merge step
(whose lane-dispatch code is not published). The adjudication verdicts are
INPUTS here: LLM judgments of the registered lane, published as a table; they
cannot be derived from the other public files. What this step reproduces is
everything downstream of them.

Composition (registration §9 / corrected-pass amendment, rules 1-2):
  * target row:  FLAG -> CATCH iff the row's §9 scored text key-matches the
                 item's defect keys, else NON-CATCH; NONE and NEITHER -> NON-CATCH.
  * off-family / clean row:  NEITHER -> SILENT; NONE -> NO-FLAG;
                 FLAG on an allowed family whose text key-matches -> HIT-ALT;
                 otherwise FA, with `key_matched_wrong_family` recorded.
The match scope is the row's `scored_text` (the §9 text the adjudicator was
shown; the original pipeline's `presented_block` equals it on all 1,804 rows).

Usage:
  python analysis/merge.py --scored OUT/scored-rows.raw.jsonl \
      --verdicts data/verdicts.jsonl --out OUT/scored-rows.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from scorer import _keys_match  # noqa: E402

ROOT = _HERE.parent


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def load_items(items_dir: Path) -> dict[str, dict]:
    items = {}
    for p in sorted(items_dir.glob("*.json")):
        it = json.loads(p.read_text())
        items[it["id"]] = it
    return items


def compose(row: dict, adjudicated: dict, items: dict[str, dict]) -> dict:
    verdict = adjudicated["verdict"]
    text = row.get("scored_text")
    keys = items[row["item"]].get("defect_keys") or []
    new = {k: v for k, v in row.items() if k != "presented_block"}
    new["adjudicated"] = adjudicated
    if row["role"] == "target":
        if verdict == "FLAG":
            hit = _keys_match(text, keys)
            new["status"], new["hit"] = ("CATCH" if hit else "NON-CATCH"), hit
        else:  # NONE and NEITHER both fail the catch
            new["status"], new["hit"] = "NON-CATCH", False
    else:  # off_family and clean share the off-family composition
        if verdict == "NEITHER":
            new["status"] = "SILENT"
        elif verdict == "NONE":
            new["status"] = "NO-FLAG"
        elif row["family"] in (row.get("allowed_families") or []) and \
                _keys_match(text, keys):
            new["status"] = "HIT-ALT"
        else:
            new["status"] = "FA"
            new["key_matched_wrong_family"] = _keys_match(text, keys)
    return new


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scored", type=Path, required=True,
                    help="mechanically scored rows (score_table.py output)")
    ap.add_argument("--verdicts", type=Path, default=ROOT / "data/verdicts.jsonl")
    ap.add_argument("--items-dir", type=Path, default=ROOT / "materials/items")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    items = load_items(args.items_dir)
    verdicts = {}
    for v in read_jsonl(args.verdicts):
        key = (v["tier"], v["arm"], v["item"], v["rep"], v["family"])
        if key in verdicts:
            raise SystemExit(f"REFUSE: duplicate verdict for {key}")
        verdicts[key] = v["adjudicated"]

    out_rows, unresolved, used = [], [], set()
    for row in read_jsonl(args.scored):
        if row["status"] != "BORDERLINE":
            out_rows.append({k: v for k, v in row.items() if k != "presented_block"})
            continue
        key = (row["tier"], row["arm"], row["item"], row["rep"], row["family"])
        adj = verdicts.get(key)
        if adj is None:
            unresolved.append(key)
            continue
        if row.get("presented_block") not in (None, row.get("scored_text")):
            raise SystemExit(f"REFUSE: presented text differs from scored text at {key}")
        used.add(key)
        out_rows.append(compose(row, adj, items))
    if unresolved:
        raise SystemExit(f"REFUSE: {len(unresolved)} BORDERLINE rows have no verdict "
                         f"(first: {unresolved[0]})")
    unused = set(verdicts) - used
    if unused:
        raise SystemExit(f"REFUSE: {len(unused)} verdicts match no BORDERLINE row "
                         f"(first: {sorted(unused)[0]})")
    with args.out.open("w") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"merged {len(used)} adjudicated rows into {len(out_rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
