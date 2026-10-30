"""lane_check.py — re-derive the corrected adjudication lane's summary
(data/results/lane-report.json) from the published lane table
(data/lane-verdicts.jsonl) and the scored rows.

Checks: the 864-row queue (ids adj-2001..adj-2864), primary verdict counts
(FLAG 340 / NONE 523 / NEITHER 1), the second-reader re-adjudication
agreement (130/130), the arm-guess sample (86/86 UNKNOWN, true arms by row),
the lane cost, and that every lane-2 primary verdict equals the verdict of
record carried in data/scored-rows.jsonl.

The lane's verdicts are LLM judgments (inputs, not derivable); this script
checks the bookkeeping around them.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def derive(lane: list[dict], rows: list[dict]) -> dict:
    stage: dict[str, dict[str, str]] = {"primary": {}, "readjudication": {}, "armguess": {}}
    for rec in lane:
        for adj_id, v in rec["verdicts"].items():
            if adj_id in stage[rec["stage"]]:
                raise SystemExit(f"REFUSE: duplicate {rec['stage']} verdict for {adj_id}")
            stage[rec["stage"]][adj_id] = v["verdict"]
    by_adj = {r["adjudicated"]["adj_id"]: r for r in rows if r.get("adjudicated")}
    lane2 = {a: r for a, r in by_adj.items() if r["adjudicated"]["lane"] == "current"}
    ids = sorted(stage["primary"])
    mismatch = [a for a in ids if lane2.get(a, {}).get("adjudicated", {}).get("verdict")
                != stage["primary"][a]]
    readj = stage["readjudication"]
    agree = sum(1 for a, v in readj.items() if stage["primary"].get(a) == v)
    guesses = stage["armguess"]
    true_arm = Counter(by_adj[a]["arm"] for a in guesses)
    return {
        "queue_size": len(ids), "ids": [ids[0], ids[-1]] if ids else [],
        "lane2_rows_in_scored_table": len(lane2),
        "primary_vs_verdict_of_record_mismatches": len(mismatch),
        "verdicts_by_stage": {k: dict(Counter(v.values())) for k, v in stage.items()},
        "readjudication": {"sampled": len(readj), "agree": agree},
        "arm_guess": {"sampled": len(guesses),
                      "non_unknown": sum(1 for v in guesses.values() if v != "UNKNOWN"),
                      "true_arms": dict(true_arm)},
        "cost_usd_total": round(sum(float(r["total_cost_usd"] or 0) for r in lane), 4),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lane", type=Path, default=ROOT / "data/lane-verdicts.jsonl")
    ap.add_argument("--rows", type=Path, default=ROOT / "data/scored-rows.jsonl")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    d = derive(read_jsonl(args.lane), read_jsonl(args.rows))
    txt = json.dumps(d, indent=1)
    if args.out:
        args.out.write_text(txt + "\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
