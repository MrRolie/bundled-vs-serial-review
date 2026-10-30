"""reproduce.py — re-run the whole analysis chain from the public files and
compare every product against the artifact of record.

Chain (each step is a script in this directory):
  1. score_table.py  dispatch tables + frozen key table + 80 items -> mechanically
                     scored rows (BORDERLINE rows await a verdict)
  2. merge.py        + data/verdicts.jsonl (the adjudication verdicts, an INPUT)
                     -> post-adjudication rows; compared with data/scored-rows.jsonl
  3. endpoints.py    -> Holm family, member states, cells, stamps, FA co-read
  4. costs.py        -> economics co-axis ($ and $/true-catch per arm x tier),
                     plus the output-only bound cited in the README (checked
                     against the cited 2.65 / 1.26 / 1.55 to the printed digits)
  5. coreads.py      -> extraction co-reads V1/V2/V3 (+ legacy lines)
  6. descriptives.py -> registered descriptive reads
  7. lane_check.py   -> lane bookkeeping (queue, 130/130, 86/86, cost)
  8. mc_stability.py -> 40-seed sweep (and, unless --skip-large, the 1e6-draw p's)
  9. payloads.py     -> every dispatch's exact prompt rebuilt from the frozen
                     materials; compared with the recorded SHA-256s

Each product is compared with the artifact of record in data/results/ as
parsed JSON (exact equality, every key and every digit). Then the headline
numbers are printed as expected vs got.

Usage:  python analysis/reproduce.py [--out DIR] [--skip-large]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
RES = DATA / "results"
H, S, O = "claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5"
# Cited in README.md (The result; Costs) and results/RESULTS.md (the cache note):
# S output-only $ per true catch / P realized $ per true catch, two decimals.
CITED_OUTPUT_ONLY = {H: "2.65", S: "1.26", O: "1.55"}


def run(script: str, *args: str) -> None:
    cmd = [sys.executable, "-B", str(HERE / script), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"FAILED: {script}")


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]


def diff_paths(a, b, path="$", out=None, limit=10):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}.{k}: present in only one side")
            else:
                diff_paths(a[k], b[k], f"{path}.{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff_paths(x, y, f"{path}[{i}]", out, limit)
    elif a != b:
        out.append(f"{path}: {str(a)[:60]} != {str(b)[:60]}")
    return out


def compare(name: str, got_path: Path, ref_path: Path, report: list) -> dict:
    got, ref = json.loads(got_path.read_text()), json.loads(ref_path.read_text())
    d = diff_paths(got, ref)
    report.append((name, "IDENTICAL" if not d else "DIFFERS", d))
    return got


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--skip-large", action="store_true",
                    help="skip the two 1e6-draw blocks of the MC sensitivity")
    args = ap.parse_args(argv)
    out = args.out or Path(tempfile.mkdtemp(prefix="reproduce-"))
    out.mkdir(parents=True, exist_ok=True)
    report: list = []

    sys.path.insert(0, str(HERE))
    import payloads  # noqa: E402
    pc = payloads.check(ROOT)
    pc_ok = (pc["records"] > 0 and pc["records_matching"] == pc["records"]
             and pc["keyed_orders_matching"] == pc["keyed_orders"])
    report.append(("payload hashes (data/dispatches)", "IDENTICAL" if pc_ok else "DIFFERS",
                   [f"{pc['records_matching']}/{pc['records']} records, {pc['payloads']} payloads, "
                    f"keyed orders {pc['keyed_orders_matching']}/{pc['keyed_orders']}"]
                   + pc["mismatches"]))

    run("score_table.py", "--out", str(out / "scored-rows.raw.jsonl"))
    run("merge.py", "--scored", str(out / "scored-rows.raw.jsonl"),
        "--out", str(out / "scored-rows.jsonl"))
    got_rows = read_jsonl(out / "scored-rows.jsonl")
    ref_rows = read_jsonl(DATA / "scored-rows.jsonl")
    same = sum(1 for a, b in zip(got_rows, ref_rows) if a == b)
    report.append(("scored-rows.jsonl", "IDENTICAL" if (same == len(ref_rows) == len(got_rows))
                   else "DIFFERS", [f"{same}/{len(ref_rows)} rows equal (got {len(got_rows)})"]))
    final = str(out / "scored-rows.jsonl")
    fals = str(DATA / "frozen/j4-falsified-cleans.json")

    run("endpoints.py", "--final", final, "--falsified-cleans", fals,
        "--out", str(out / "endpoints.json"))
    ep = compare("endpoints.json", out / "endpoints.json", RES / "endpoints.json", report)
    run("costs.py", "--final", final, "--out", str(out / "costs.json"),
        "--bounds-out", str(out / "cost-bounds.json"))
    co = compare("costs.json", out / "costs.json", RES / "costs.json", report)
    oob = json.loads((out / "cost-bounds.json").read_text())["output_only_bound"]
    got_oo = {t: (f"{oob[t]['ratio']:.2f}" if oob.get(t) else None) for t in (H, S, O)}
    report.append((f"output-only bound vs the cited {' / '.join(CITED_OUTPUT_ONLY[t] for t in (H, S, O))}"
                   " (no artifact; checked to the printed digits)",
                   "MATCHES" if got_oo == CITED_OUTPUT_ONLY else "DIFFERS",
                   [f"got {got_oo[H]} / {got_oo[S]} / {got_oo[O]}"]))
    run("coreads.py", "--final", final, "--falsified-cleans", fals,
        "--out", str(out / "coreads.json"))
    cr = compare("coreads.json", out / "coreads.json", RES / "coreads.json", report)
    run("descriptives.py", "--final", final, "--costs", str(out / "costs.json"),
        "--out", str(out / "descriptives.json"))
    compare("descriptives.json", out / "descriptives.json", RES / "descriptives.json", report)
    run("lane_check.py", "--rows", final, "--out", str(out / "lane-check.json"))
    lane = json.loads((out / "lane-check.json").read_text())
    ref_lane = json.loads((RES / "lane-report.json").read_text())
    lane_ok = (lane["queue_size"] == ref_lane["queue_size"]
               and lane["ids"] == ref_lane["ids"]
               and lane["verdicts_by_stage"] == ref_lane["verdicts_by_stage"]
               and lane["readjudication"]["agree"] == ref_lane["readjudication"]["agree"]
               and lane["readjudication"]["sampled"] == ref_lane["readjudication"]["sampled"]
               and lane["arm_guess"]["sampled"] == ref_lane["arm_guess"]["sampled"]
               and lane["arm_guess"]["true_arms"] == {k: v["n"] for k, v in
                                                      ref_lane["arm_guess"]["by_true_arm"].items()}
               and lane["primary_vs_verdict_of_record_mismatches"] == 0
               and round(lane["cost_usd_total"], 2) == round(ref_lane["cost_usd_total"], 2))
    report.append(("lane-report.json (bookkeeping fields)", "IDENTICAL" if lane_ok else "DIFFERS", []))

    mc_args = ["--final", final, "--out", str(out / "mc-stability.json")]
    if args.skip_large:
        mc_args.append("--skip-large")
    run("mc_stability.py", *mc_args)
    mc = json.loads((out / "mc-stability.json").read_text())
    ref_mc = json.loads((RES / "mc-stability.json").read_text())
    keys = [k for k in ref_mc if k in mc]
    d = diff_paths({k: mc[k] for k in keys}, {k: ref_mc[k] for k in keys})
    skipped = sorted(set(ref_mc) - set(mc))
    report.append(("mc-stability.json" + (f" (skipped: {', '.join(skipped)})" if skipped else ""),
                   "IDENTICAL" if not d else "DIFFERS", d))

    print(f"products written to {out}\n")
    print("ARTIFACT COMPARISON (parsed JSON, exact; MATCHES = a cited figure "
          "with no artifact, checked to its printed digits)")
    for name, verdict, detail in report:
        print(f"  {verdict:9s} {name}")
        for line in detail[:10]:
            if verdict != "IDENTICAL" or "rows equal" in line or "payloads" in line:
                print(f"            {line}")

    b = ep["boots"]
    tab = co["table"]

    def ratio(t):
        return tab[f"{t}/S"]["usd_per_true_catch"]["realized"] / \
            tab[f"{t}/P"]["usd_per_true_catch"]["realized"]

    fa_h = ep["fa_co_read"]["classes"][H]["class2_off_family_fa"]["mf"]
    fa_hs = ep["fa_co_read"]["classes"][H]["class2_off_family_fa"]["sf"]
    sw = mc["seed_sweep_10k"]
    v2 = cr["results"]["V2_p_maximal_key_scope"]
    v3 = cr["results"]["V3_label_respecting_punitive"]

    def fmt_d(x):
        return f"{x['delta']:+.3f} [{x['ci95'][0]:+.3f}, {x['ci95'][1]:+.3f}] p {x['p_one_sided']:.4f}"

    def fmt_v(v):
        return (f"{v['deltas']['H-B1']:+.3f} [{v['ci95']['H-B1'][0]:+.3f}, "
                f"{v['ci95']['H-B1'][1]:+.3f}] p {v['p_one_sided']['H-B1']} -> {v['composite_cell']}")

    print("\nHEADLINES (expected = the published results; got = this run)")
    rows = [
        ("H-B1 haiku S-P", "+0.083 [+0.017, +0.150] p 0.0111 F", fmt_d(b["H-B1"]) + " "
         + ep["member_states"]["H-B1"]),
        ("H-B2 sonnet S-P", "-0.046 [-0.157, +0.065] p 0.814 N", fmt_d(b["H-B2"]) + " "
         + ep["member_states"]["H-B2"]),
        ("H-B3 interaction", "+0.025 [-0.079, +0.132] p 0.322 N", fmt_d(b["H-B3"]) + " "
         + ep["member_states"]["H-B3"]),
        ("H-B4 haiku Sq-P", "+0.094 [+0.011, +0.183] p 0.0169 N", fmt_d(b["H-B4"]) + " "
         + ep["member_states"]["H-B4"]),
        ("composite / band", "C-B2 / C-B-TTFLAT", f"{ep['composite_cell']} / {ep['band_read']['cell']}"),
        ("opus S-P (C44), 90% CI", "+0.049 [-0.028, +0.125]",
         f"{ep['band_read']['delta']:+.3f} [{ep['band_read']['ci90'][0]:+.3f}, "
         f"{ep['band_read']['ci90'][1]:+.3f}]"),
        ("S/P $ per true catch", "3.0x / 2.1x / 2.2x (2.97/2.14/2.24)",
         f"{ratio(H):.2f} / {ratio(S):.2f} / {ratio(O):.2f}"),
        ("S output-only / P $ per catch", "2.65x / 1.26x / 1.55x",
         f"{oob[H]['ratio']:.3f} / {oob[S]['ratio']:.3f} / {oob[O]['ratio']:.3f}"),
        ("haiku off-family FA mf", "0.285 vs 0.054, +0.232 [+0.181, +0.283]",
         f"{fa_h['fa_hi']:.3f} vs {fa_h['fa_lo']:.3f}, {fa_h['delta']:+.3f} "
         f"[{fa_h['ci95'][0]:+.3f}, {fa_h['ci95'][1]:+.3f}]"),
        ("haiku off-family FA sf", "0.294 vs 0.054, +0.240 [+0.185, +0.296]",
         f"{fa_hs['fa_hi']:.3f} vs {fa_hs['fa_lo']:.3f}, {fa_hs['delta']:+.3f} "
         f"[{fa_hs['ci95'][0]:+.3f}, {fa_hs['ci95'][1]:+.3f}]"),
        ("V2 H-B1 (extraction co-read)", "+0.067 [0.000, +0.133] p 0.0354 -> C-B5", fmt_v(v2)),
        ("V3 H-B1 (extraction co-read)", "+0.017 [-0.056, +0.089] p 0.357 -> C-B5", fmt_v(v3)),
        ("seed sweep 40 x 10k", "H-B1 33/40, H-B4 17/40",
         f"H-B1 {sw['H-B1_fires']}/40, H-B4 {sw['H-B4_fires']}/40"),
    ]
    if "p_one_sided_seed1512" in mc:
        p = mc["p_one_sided_seed1512"]
        rows.append(("1e6 draws, seed 1512", "H-B1 0.011446, H-B4 0.016236",
                     f"H-B1 {p['H-B1']}, H-B4 {p['H-B4']}"))
    w = max(len(r[0]) for r in rows)
    for name, exp, got in rows:
        print(f"  {name:<{w}}  expected {exp}\n  {'':<{w}}  got      {got}")
    bad = [r for r in report if r[1] not in ("IDENTICAL", "MATCHES")]
    print("\nRESULT:", "every product reproduces its artifact of record" if not bad
          else f"{len(bad)} product(s) differ")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
