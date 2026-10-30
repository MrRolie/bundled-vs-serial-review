"""mc_stability.py — the NON-registered Monte-Carlo stability sensitivity
behind the "Fragility (b)" paragraph of results/RESULTS.md.

The registered instrument is the item-cluster bootstrap at n_boot = 10,000,
seed 1512 (registration §11 preamble); its verdict stands. Two Holm members
sit within Monte-Carlo noise of their thresholds, so this script reports,
descriptively:

  * the four Holm-family p values (and Holm firings) at n_boot = 1,000,000,
    seed 1512, plus H-B1/H-B4 at seed 7;
  * a sweep of 40 alternative seeds (1..40) at the registered n_boot = 10,000:
    how often H-B1 and H-B4 fire under Holm, their p ranges, and the joint
    (H-B1, H-B4) state counts.

It uses only the registered primitives (`stats.bootstrap_delta`,
`stats.bootstrap_interaction`, `stats.holm`) on the registered pools (the
audit-surviving 60 defective items for H-B1/H-B4, C44's 36 for H-B2/H-B3).

The artifact of record (data/results/mc-stability.json) was produced ad hoc
at the time, with no committed producer; this script is the published
producer and is checked against that artifact by reproduce.py.

Usage:
  python analysis/mc_stability.py --final data/scored-rows.jsonl --out OUT.json
      [--skip-large]   # skip the two 1e6-draw blocks (takes ~1 min otherwise)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from endpoints import TIER_HAIKU, TIER_OPUS, TIER_SONNET, read_jsonl, target_pairs  # noqa: E402
from stats import bootstrap_delta, bootstrap_interaction, holm  # noqa: E402

ROOT = _HERE.parent


def pools(rows, key_table: Path, c44_path: Path) -> dict:
    surv = sorted(r["item_id"] for r in json.loads(key_table.read_text())["table"])
    c44 = json.loads(c44_path.read_text())["defective"]
    tp = target_pairs
    return dict(
        b1S=tp(rows, TIER_HAIKU, "S", surv), b1P=tp(rows, TIER_HAIKU, "P", surv),
        b4=tp(rows, TIER_HAIKU, "Sq", surv),
        b2S=tp(rows, TIER_SONNET, "S", c44), b2P=tp(rows, TIER_SONNET, "P", c44),
        hS=tp(rows, TIER_HAIKU, "S", c44), hP=tp(rows, TIER_HAIKU, "P", c44),
        oS=tp(rows, TIER_OPUS, "S", c44), oP=tp(rows, TIER_OPUS, "P", c44))


def family_p(a: dict, *, seed: int, n_boot: int, members=("H-B1", "H-B2", "H-B3", "H-B4")) -> dict:
    out = {}
    if "H-B1" in members:
        out["H-B1"] = bootstrap_delta(a["b1S"], a["b1P"], seed=seed, n_boot=n_boot)["p_one_sided"]
    if "H-B2" in members:
        out["H-B2"] = bootstrap_delta(a["b2S"], a["b2P"], seed=seed, n_boot=n_boot)["p_one_sided"]
    if "H-B3" in members:
        out["H-B3"] = bootstrap_interaction(a["hS"], a["hP"], a["oS"], a["oP"],
                                            seed=seed, n_boot=n_boot)["p_one_sided"]
    if "H-B4" in members:
        out["H-B4"] = bootstrap_delta(a["b4"], a["b1P"], seed=seed, n_boot=n_boot)["p_one_sided"]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--final", type=Path, default=ROOT / "data/scored-rows.jsonl")
    ap.add_argument("--key-table", type=Path, default=ROOT / "data/frozen/audit-key-table.json")
    ap.add_argument("--c44", type=Path, default=ROOT / "data/frozen/c44-selection.json")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n-boot-large", type=int, default=1_000_000)
    ap.add_argument("--skip-large", action="store_true")
    args = ap.parse_args(argv)

    a = pools(read_jsonl(args.final), args.key_table, args.c44)
    out: dict = {"note": "non-registered MC-stability sensitivity (descriptive): "
                         "registered instrument is n_boot=10,000 seed 1512"}
    if not args.skip_large:
        p = family_p(a, seed=1512, n_boot=args.n_boot_large)
        out["n_boot"] = args.n_boot_large
        out["p_one_sided_seed1512"] = {k: round(v, 6) for k, v in p.items()}
        out["holm_fired_seed1512"] = holm(p)
        p7 = family_p(a, seed=7, n_boot=args.n_boot_large, members=("H-B1", "H-B4"))
        out["p_seed7"] = {k: round(v, 6) for k, v in p7.items()}

    f1 = f4 = 0
    joint: dict[str, int] = {}
    r1, r4 = [], []
    for seed in range(1, 41):
        p = family_p(a, seed=seed, n_boot=10_000)
        h = holm(p)
        f1 += h["H-B1"]
        f4 += h["H-B4"]
        r1.append(p["H-B1"])
        r4.append(p["H-B4"])
        k = f"({'F' if h['H-B1'] else 'N'},{'F' if h['H-B4'] else 'N'})"
        joint[k] = joint.get(k, 0) + 1
    out["seed_sweep_10k"] = {
        "seeds": "1..40", "H-B1_fires": f1, "H-B4_fires": f4, "joint": joint,
        "H-B1_p_range": [round(min(r1), 4), round(max(r1), 4)],
        "H-B4_p_range": [round(min(r4), 4), round(max(r4), 4)],
    }
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    s = out["seed_sweep_10k"]
    print(f"seed sweep (10k x 40): H-B1 fires {s['H-B1_fires']}/40 "
          f"p {s['H-B1_p_range']}; H-B4 fires {s['H-B4_fires']}/40 p {s['H-B4_p_range']}; "
          f"joint {s['joint']}")
    if "p_one_sided_seed1512" in out:
        print(f"1e6 draws seed 1512: {out['p_one_sided_seed1512']}; seed 7: {out['p_seed7']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
