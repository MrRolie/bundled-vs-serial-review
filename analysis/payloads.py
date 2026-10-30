"""payloads.py — rebuild the exact prompt every subject dispatch received, from the
frozen public materials, and check it against the hashes recorded per dispatch.

The trial runner is not published; this module restates its payload assembly
(registration §4.2, §7, §16) so the treatment under study, the prompt SHAPE, can be
inspected and replicated byte for byte.

Assembly (components join with one blank line, "\\n\\n"):
  briefing   materials/overlay/briefing.md, trailing newlines stripped. Identical
             in every arm; it carries the five-family partition and the answer
             schema.
  stimulus   the item's files, each rendered as "--- <path> ---" followed by a
             fenced python block of the file content (trailing whitespace
             stripped); files joined with one blank line.
  question   materials/overlay/questions.json[family], trailing newlines stripped.
             Byte-identical across arms.
  note       "You are asked about family <family> only." (the §4.2 continuation);
             precedes the question block in S and in every Sq turn, never in P.

  P   (one dispatch)    briefing, stimulus, the five questions in the recorded
                        `question_order`
  S   (one dispatch per briefing, stimulus, note, question (`family`)
       family)
  Sq  (one session,     turn 1: briefing, stimulus, note, question of turn_order[0];
       five turns)      turns 2-5: note, question only (the session already holds
                        the briefing and stimulus)

Orders are keyed derivations (§7): random.Random("1512:P:<item>:<rep>") and
random.Random("1512:Sq:<item>:<rep>") shuffle the sorted family list. The check
re-derives them and compares with the recorded orders.

Each payload is sent as the user message; the system prompt is the constant
"You are a helpful assistant." Hashes are SHA-256 of the UTF-8 text.

Usage (from the repository root):
  python analysis/payloads.py                       # check every record
  python analysis/payloads.py --render claude-opus-5 sf-comparison-01 S 1 --family comparison
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("boundary", "comparison", "exception", "sign", "units")
SEED = 1512
SEP = "\n\n"
NOTE = "You are asked about family {family} only."
SYSTEM_PROMPT = "You are a helpful assistant."


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def load_overlay(root: Path = ROOT) -> tuple[str, dict[str, str]]:
    briefing = (root / "materials/overlay/briefing.md").read_text().rstrip("\n")
    raw = json.loads((root / "materials/overlay/questions.json").read_text())
    if sorted(raw) != sorted(FAMILIES):
        raise ValueError(f"questions.json carries {sorted(raw)}, expected {FAMILIES}")
    return briefing, {f: raw[f].rstrip("\n") for f in FAMILIES}


def load_items(root: Path = ROOT) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text())
            for p in sorted((root / "materials/items").glob("*.json"))}


def render_stimulus(item: dict) -> str:
    files = item.get("files") or ()
    if not files:
        raise ValueError(f"item {item.get('id')!r} has no files")
    return "\n\n".join(f"--- {f['path']} ---\n```python\n{f['content'].rstrip()}\n```"
                       for f in files)


def keyed_order(arm: str, item_id: str, rep: int) -> list[str]:
    fams = sorted(FAMILIES)
    random.Random(f"{SEED}:{arm}:{item_id}:{rep}").shuffle(fams)
    return fams


def assemble(rec: dict, briefing: str, questions: dict[str, str], stimulus: str) -> list[str]:
    """The payload(s) of one dispatch record: one for P and S, five (per turn) for Sq."""
    arm = rec["arm"]
    if arm == "P":
        return [SEP.join([briefing, stimulus] + [questions[f] for f in rec["question_order"]])]
    if arm == "S":
        fam = rec["family"]
        return [SEP.join([briefing, stimulus, NOTE.format(family=fam), questions[fam]])]
    if arm == "Sq":
        order = rec["turn_order"]
        first = SEP.join([briefing, stimulus, NOTE.format(family=order[0]), questions[order[0]]])
        return [first] + [SEP.join([NOTE.format(family=f), questions[f]]) for f in order[1:]]
    raise ValueError(f"unknown arm {arm!r}")


def dispatch_files(root: Path = ROOT) -> list[Path]:
    return sorted((root / "data/dispatches").glob("*.jsonl"))


def check(root: Path = ROOT) -> dict:
    """Rebuild every payload in every dispatch table (trials and grouped-order
    probes) and compare stimulus, question-block (charge), payload and keyed-order
    hashes with the recorded ones. Returns counts and the first mismatches."""
    briefing, questions = load_overlay(root)
    items = load_items(root)
    stim_cache: dict[str, str] = {}
    out = {"records": 0, "payloads": 0, "records_matching": 0, "keyed_orders": 0,
           "keyed_orders_matching": 0, "mismatches": []}
    for path in dispatch_files(root):
        for ln in path.read_text().splitlines():
            if not ln.strip():
                continue
            rec = json.loads(ln)
            item_id = rec["item"]
            if item_id not in stim_cache:
                stim_cache[item_id] = render_stimulus(items[item_id])
            stim = stim_cache[item_id]
            payloads = assemble(rec, briefing, questions, stim)
            problems = []
            if sha256(stim) != rec["stimulus_sha256"]:
                problems.append("stimulus_sha256")
            for fam, h in rec["charge_sha256s"].items():
                if sha256(questions[fam]) != h:
                    problems.append(f"charge_sha256s.{fam}")
            if [sha256(p) for p in payloads] != rec["payload_sha256s"]:
                problems.append("payload_sha256s")
            if rec["arm"] == "Sq" and "turns" in rec:
                if [t["payload_sha256"] for t in rec["turns"]] != rec["payload_sha256s"]:
                    problems.append("turns[].payload_sha256")
            for arm, key in (("P", "question_order"), ("Sq", "turn_order")):
                if rec["arm"] == arm and key in rec:
                    out["keyed_orders"] += 1
                    if keyed_order(arm, item_id, rec["rep"]) == rec[key]:
                        out["keyed_orders_matching"] += 1
                    else:
                        problems.append(key)
            out["records"] += 1
            out["payloads"] += len(payloads)
            if problems:
                if len(out["mismatches"]) < 10:
                    out["mismatches"].append(
                        f"{path.name} {rec['arm']} {item_id} rep {rec['rep']}"
                        f" {rec.get('family', '')}: {', '.join(problems)}")
            else:
                out["records_matching"] += 1
    return out


def render(root: Path, tier: str, item_id: str, arm: str, rep: int,
           family: str | None) -> list[tuple[str, str]]:
    briefing, questions = load_overlay(root)
    stim = render_stimulus(load_items(root)[item_id])
    path = root / "data/dispatches" / f"{tier}.jsonl"
    for ln in path.read_text().splitlines():
        rec = json.loads(ln)
        if (rec["item"], rec["arm"], rec["rep"]) == (item_id, arm, rep) and \
                (arm != "S" or rec["family"] == family):
            return [(sha256(p), p) for p in assemble(rec, briefing, questions, stim)]
    raise SystemExit(f"no {arm} record for {item_id} rep {rep} {family or ''} at {tier}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--render", nargs=4, metavar=("TIER", "ITEM", "ARM", "REP"))
    ap.add_argument("--family", help="for --render with arm S")
    args = ap.parse_args(argv)
    if args.render:
        tier, item_id, arm, rep = args.render
        for i, (h, p) in enumerate(render(ROOT, tier, item_id, arm, int(rep), args.family), 1):
            print(f"===== payload {i}  sha256 {h}\n{p}")
        return 0
    r = check(ROOT)
    print(f"records {r['records']}, payloads {r['payloads']}: "
          f"{r['records_matching']}/{r['records']} records match every recorded hash; "
          f"keyed orders {r['keyed_orders_matching']}/{r['keyed_orders']}")
    for m in r["mismatches"]:
        print("  MISMATCH", m)
    ok = r["records"] > 0 and r["records_matching"] == r["records"] \
        and r["keyed_orders_matching"] == r["keyed_orders"]
    print("RESULT:", "every payload reproduces its recorded hash" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
