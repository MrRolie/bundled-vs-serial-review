"""check_agreement.py — the public row-level agreement check between the
independent recount's output (recount/recount-rows.jsonl) and the scored table
of record (data/scored-rows.jsonl).

For every one of the 7,340 question-rows it compares: the V1 status, the hit
flag (target rows), key-matched-wrong-family (FA rows), and, on the 1,804
adjudicated rows, the verdict of record and the lane label. The recount's
statuses for the two registered extraction co-reads (V2, V3) are summarized
beside the scored table's co-read relabel counts.

Usage:  python recount/check_agreement.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE = {"RETAINED": "retained", "RELANE": "current", "NEWLANE": "current"}


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]


def main() -> int:
    rec = {r["key"]: r for r in read_jsonl(ROOT / "recount/recount-rows.jsonl")}
    rows = read_jsonl(ROOT / "data/scored-rows.jsonl")
    n = len(rows)
    st = hit = kmwf = 0
    adj = adj_same = lane_same = 0
    missing = 0
    for r in rows:
        key = f"{r['tier']}|{r['arm']}|{r['item']}|{r['rep']}|{r['family']}"
        x = rec.get(key)
        if x is None:
            missing += 1
            continue
        st += x["status_v1"] == r["status"]
        hit += bool(x["hit_v1"]) == bool(r.get("hit"))
        kmwf += bool(x["kmwf_v1"]) == bool(r.get("key_matched_wrong_family"))
        if r.get("adjudicated"):
            adj += 1
            adj_same += x["verdict"] == r["adjudicated"]["verdict"]
            lane_same += LANE.get(x["route"]) == r["adjudicated"]["lane"]
    print(f"rows in scored table: {n}; rows in recount: {len(rec)}; unmatched keys: {missing}")
    print(f"V1 status agree:                   {st}/{n}")
    print(f"hit agree:                         {hit}/{n}")
    print(f"key-matched-wrong-family agree:    {kmwf}/{n}")
    print(f"verdict of record agree:           {adj_same}/{adj}")
    print(f"lane label agree:                  {lane_same}/{adj}")
    print("recount status counts V1/V2/V3:")
    for v in ("v1", "v2", "v3"):
        print(f"  {v}: {dict(sorted(Counter(x['status_' + v] for x in rec.values()).items()))}")
    ok = missing == 0 and st == hit == kmwf == n and adj_same == lane_same == adj
    print("AGREE on every row" if ok else "DISAGREEMENT — see counts above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
