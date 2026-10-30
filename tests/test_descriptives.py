"""The within-P question order is a keyed derivation (registration §7); the
analysis re-derives it (`descriptives.keyed_question_order`) and the trial
records also carry the realized order. They must agree on every P dispatch."""
import json
from pathlib import Path

from descriptives import keyed_question_order

ROOT = Path(__file__).resolve().parents[1]
TIERS = ("claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5")


def test_keyed_question_order_matches_every_recorded_p_order():
    n = 0
    for t in TIERS:
        for ln in (ROOT / "data/dispatches" / f"{t}.jsonl").read_text().splitlines():
            r = json.loads(ln)
            if r["arm"] != "P":
                continue
            assert tuple(r["question_order"]) == keyed_question_order(r["item"], r["rep"]), \
                (t, r["item"], r["rep"])
            n += 1
    assert n == 240 + 132 + 176


def test_sq_turn_order_is_the_recorded_turn_sequence():
    for t in TIERS[:2]:
        for ln in (ROOT / "data/dispatches" / f"{t}.jsonl").read_text().splitlines():
            r = json.loads(ln)
            if r["arm"] == "Sq":
                assert [x["family"] for x in r["turns"]] == r["turn_order"]
