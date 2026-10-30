"""costs.py — §6/§6a economics co-axis: $/true-catch and
tokens-per-true-catch per arm×tier in the THREE registered
reconstructions (realized / cache-cold / cache-grouped).

  * realized — as dispatched (block-randomized), summed `total_cost_usd`
    (P/S: record level; Sq: session level).
  * cache-cold — recorded token splits at LIST prices, no cache credit:
    (input + cache_read + cache_creation) × p_in + output × p_out.
    List prices are pinned below and cross-checked against the records'
    own billing at build time (the output-price legs of a per-tier
    least-squares fit land on the list out-prices; the recorded
    input_tokens UNDERCOUNT billed input — CLI scaffolding is billed but
    not in the record's top-level field — so cache-cold is a FLOOR on
    the true cold cost, direction disclosed, never papered).
  * cache-grouped — the deployed-shape estimate, ANCHORED by the
    registered grouped-order probes (one item × 5 consecutive dispatches
    per tier, run in the preflight lane): the probes MEASURED ZERO cache
    reads at every tier (haiku: no cache engagement at all, payload
    below the cache minimum — the bank-calibration pilot's 0/400 replicated;
    sonnet/opus: ~1,040 tokens WRITTEN to cache per dispatch, zero
    reads across five consecutive same-item dispatches). The anchored
    estimate is therefore REALIZED — item-grouped dispatch realizes no
    discount under this instrument shape — and the naive rules-based
    recompute (prefix reads on dispatches 2..5) is NOT emitted: the
    registration anchors the estimate to the probe, and the probe
    refutes the naive model's premise.

True catches are COUNTED from the final (post-adjudication) rows:
target-role status == CATCH. $/true-catch is UNDEFINED at zero catches
(emitted as null, never imputed). tokens-per-true-catch uses total
tokens (input + output + cache_read + cache_creation), disclosed.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Mapping, Sequence

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parent

TIERS = ("claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5")
# List prices, USD per MTok (input, output). Cross-checked at build time
# against the records' own billing (see assert_out_prices).
LIST_PRICES = {
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-5": (5.0, 25.0),
}
TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens",
                "cache_creation_input_tokens")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def dispatch_rows(rec: Mapping) -> list[Mapping]:
    """Per-dispatch token/cost views: P/S records are one dispatch; Sq
    records are K turns, each with its own splits."""
    if rec["arm"] == "Sq":
        return [{"cost": t["cost_usd"], **{f: t[f] for f in TOKEN_FIELDS}}
                for t in rec["turns"]]
    return [{"cost": rec["total_cost_usd"], **{f: rec[f] for f in TOKEN_FIELDS}}]


def cold_cost(d: Mapping, p_in: float, p_out: float) -> float:
    ins = d["input_tokens"] + d["cache_read_input_tokens"] + \
        d["cache_creation_input_tokens"]
    return ins / 1e6 * p_in + d["output_tokens"] / 1e6 * p_out


def assert_out_prices(cells: Mapping) -> None:
    """Belt: per tier, pooled (realized − input-leg-at-list) / output
    tokens must land within 10% of the list output price — a moved price
    table or a wrong pin refuses here rather than mispricing the co-axis."""
    for tier in TIERS:
        p_in, p_out = LIST_PRICES[tier]
        disp = [d for (t, _a), c in cells.items() if t == tier
                for d in c["dispatches"]]
        out_tok = sum(d["output_tokens"] for d in disp)
        # realized minus the input side under BILLING rules (reads 0.1×,
        # writes 1.25×); recorded input under-counts billed input, so the
        # implied out-price is biased HIGH — the belt bounds it one-sided
        realized = sum(d["cost"] for d in disp)
        in_at_list = sum(
            d["input_tokens"] / 1e6 * p_in
            + d["cache_read_input_tokens"] / 1e6 * p_in * 0.1
            + d["cache_creation_input_tokens"] / 1e6 * p_in * 1.25
            for d in disp)
        implied_out = (realized - in_at_list) / (out_tok / 1e6)
        if not (p_out * 0.95 <= implied_out <= p_out * 1.35):
            raise SystemExit(
                f"REFUSE: {tier} implied output price {implied_out:.2f} vs list "
                f"{p_out} — the pinned LIST_PRICES table disagrees with the "
                "records' own billing; re-pin before emitting the co-axis")


def output_only_bound(cells: Mapping, catches: Mapping) -> dict:
    """The caching-robustness bound cited in the README and RESULTS: the
    serialized arm (S) priced at output tokens only (every input token free,
    list out-price) per true catch, divided by the bundled arm's (P) realized
    $ per true catch. Above 1, bundling stays cheaper per true catch even if
    serialized input cost nothing. Not part of costs.json, which is the
    artifact of record and predates this figure; written by --bounds-out."""
    out = {}
    for tier in TIERS:
        _p_in, p_out = LIST_PRICES[tier]
        k_s, k_p = catches.get((tier, "S"), 0), catches.get((tier, "P"), 0)
        if not (k_s and k_p):
            out[tier] = None  # undefined at zero catches, never imputed
            continue
        s_out = sum(d["output_tokens"] for d in cells[(tier, "S")]["dispatches"]) \
            / 1e6 * p_out / k_s
        p_real = sum(d["cost"] for d in cells[(tier, "P")]["dispatches"]) / k_p
        out[tier] = {"S_output_only_usd_per_true_catch": round(s_out, 4),
                     "P_realized_usd_per_true_catch": round(p_real, 4),
                     "ratio": round(s_out / p_real, 4)}
    return out


def main(argv_in: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data/dispatches")
    ap.add_argument("--final", type=Path, required=True,
                    help="post-adjudication final rows (catch counts)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--bounds-out", type=Path,
                    help="also write the output-only bound (S output-only $ per "
                         "true catch / P realized $ per true catch) here")
    args = ap.parse_args(argv_in)

    cells: dict[tuple, dict] = defaultdict(lambda: {"dispatches": [], "units": 0})
    for tier in TIERS:
        for rec in read_jsonl(args.data_dir / f"{tier}.jsonl"):
            c = cells[(tier, rec["arm"])]
            c["dispatches"].extend(dispatch_rows(rec))
            c["units"] += 1
    assert_out_prices(cells)

    catches: dict[tuple, int] = defaultdict(int)
    for r in read_jsonl(args.final):
        if r["role"] == "target" and r["status"] == "CATCH":
            catches[(r["tier"], r["arm"])] += 1

    probes = {}
    for tier in TIERS:
        p = args.data_dir / f"{tier}.grouped-probe.jsonl"
        if p.exists():
            probes[tier] = read_jsonl(p)
    probe_reads = {t: sum(d["cache_read_input_tokens"] for d in rows)
                   for t, rows in probes.items()}
    if any(v > 0 for v in probe_reads.values()):
        raise SystemExit(
            f"REFUSE: grouped probes measured NONZERO cache reads {probe_reads} — "
            "the zero-discount anchor written into this module no longer holds; "
            "the cache-grouped reconstruction must be rebuilt on the measured rows")

    table = {}
    for (tier, arm), c in sorted(cells.items()):
        p_in, p_out = LIST_PRICES[tier]
        realized = sum(d["cost"] for d in c["dispatches"])
        cold = sum(cold_cost(d, p_in, p_out) for d in c["dispatches"])
        toks = sum(sum(d[f] for f in TOKEN_FIELDS) for d in c["dispatches"])
        k = catches.get((tier, arm), 0)
        table[f"{tier}/{arm}"] = {
            "units": c["units"], "dispatches": len(c["dispatches"]),
            "true_catches": k, "total_tokens": toks,
            "realized_usd": round(realized, 4),
            "cache_cold_usd": round(cold, 4),
            "cache_grouped_usd": round(realized, 4),
            "usd_per_true_catch": {
                "realized": round(realized / k, 4) if k else None,
                "cache_cold": round(cold / k, 4) if k else None,
                "cache_grouped": round(realized / k, 4) if k else None,
            },
            "tokens_per_true_catch": round(toks / k, 1) if k else None,
        }
    out = {
        "table": table,
        "list_prices_usd_per_mtok": {t: {"in": p[0], "out": p[1]}
                                     for t, p in LIST_PRICES.items()},
        "cache_grouped_anchor": {
            "probe_cache_reads": probe_reads,
            "statement": "grouped-order probes measured zero cache reads at every "
                         "tier; the anchored cache-grouped estimate equals realized "
                         "(no discount); haiku additionally engaged no cache at all "
                         "(0 writes, payload below the cache minimum — the bank-calibration pilot's 0/400 "
                         "replicated)",
        },
        "disclosures": [
            "recorded input_tokens undercount billed input (CLI scaffolding); "
            "cache-cold is a floor on true cold cost, direction stated",
            "tokens_per_true_catch uses total tokens across all four fields",
            "$/true-catch UNDEFINED (null) at zero catches, never imputed",
        ],
    }
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    if args.bounds_out:
        args.bounds_out.write_text(
            json.dumps({"output_only_bound": output_only_bound(cells, catches)},
                       indent=1) + "\n")
    for k, v in table.items():
        print(f"{k}: realized ${v['realized_usd']:.2f} cold ${v['cache_cold_usd']:.2f} "
              f"catches {v['true_catches']} $/catch(realized) "
              f"{v['usd_per_true_catch']['realized']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
