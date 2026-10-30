"""Golden vectors for presence — authored from LIVE weakest-tier rows
(the residual inventory of 2026-08-27: 471 strict-MISSING ∧ ¬loose-PARSED
rows), never from imagined shapes. Positives recover text; NEGATIVES pin that a
genuinely absent answer stays MISSING — a recovery-only suite cannot fail
in the direction that matters.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "analysis"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from presence import (  # noqa: E402
    MARKER_RE,
    compose_with_presence,
    marker_family,
    normalize_for_retention,
    p_segment,
    scored_text,
    turn_text,
)
from scorer import score_off_family_question, score_target_question  # noqa: E402


# ----------------------------------------------------------- live P bundles
# haiku P sf-units-01 rep1: `## Q-<F>` headings, verdict fenced WITHOUT a head
P_HEADING = """# Code Review: Defect Analysis

## Q-units
```
FLAG — worker_health.py, find_stale_workers() function, line "if elapsed > timeout_ms:".
The variable 'elapsed' is returned from seconds_since() and is expressed in seconds.
```

## Q-comparison
```
NO-DEFECT-comparison
```

## Q-exception
```
NO-DEFECT-exception
```

## Q-boundary
```
NO-DEFECT-boundary
```

## Q-sign
```
NO-DEFECT-sign
```"""

# haiku P sf-sign-03 rep1: unfenced hybrids + a head-only `Q-sign:` line
P_HEAD_ONLY = """Q-boundary: NO-DEFECT-boundary

Q-comparison: NO-DEFECT-comparison

Q-exception: NO-DEFECT-exception

Q-sign:
```
FLAG — hold_desk.py, cancel_hold method, line `hold.position += 1`

The code incorrectly increments position instead, moving them later in the queue.
Should be `hold.position -= 1`.
```

Q-units: NO-DEFECT-units"""

# haiku P sf-comparison-06 rep1: bold heads
P_BOLD = """# Code Review Analysis

**Q-boundary:** NO-DEFECT-boundary

**Q-exception:** FLAG — shuffle_queue.py, line 63 (`random.choice(pool)`). Mechanism: empty pool raises IndexError.

**Q-comparison:** NO-DEFECT-comparison

**Q-units:** NO-DEFECT-units

**Q-sign:** NO-DEFECT-sign"""

# opus P mf-sign-06 rep3 (abridged): four fenced blocks, NO units block anywhere
P_TRUE_MISSING = """```
Q-boundary: NONE — The edges check out: `seats_left <= 0` before append fills exactly `available_seats` rows.
```

```
Q-comparison: NONE — Each decision relates the intended operands in the intended direction.
```

```
Q-exception: NONE — No failure case is mishandled; there are no try/except blocks to over-broaden.
```

```
Q-sign: FLAG — standby_priority.py, `compute_priority_score`, the line `score -= passenger.prior_denied_boardings * PRIOR_BUMP_WEIGHT`. The operator should be `+=`.
```"""


class TestMarkerGrammar:
    @pytest.mark.parametrize("line,fam", [
        ("Q-units: NO-DEFECT-units", "units"),
        ("## Q-units", "units"),
        ("## Q-sign:", "sign"),
        ("# Q-exception", "exception"),
        ("**Q-boundary:** NO-DEFECT-boundary", "boundary"),
        ("Q-sign:", "sign"),
        ("1. Q-comparison: NONE", "comparison"),
        ("- NO-DEFECT-units", "units"),
        ("**NO-DEFECT-sign**", "sign"),
        ("FLAG-exception: Unhandled failure case in trail_maintenance_scheduler.py", "exception"),
        ("> q-UNITS: flag — mixed", "units"),
        ("```Q-units: NONE", "units"),
    ])
    def test_live_shapes_are_markers(self, line, fam):
        assert marker_family(line) == fam

    @pytest.mark.parametrize("line", [
        "Q-significance: FLAG — note",          # finding-6 poisoning: never family `sign`
        "NO-DEFECT-signage",
        "FLAG — irrigation_scheduler.py, `_effective_delivery_rate`",  # bare verdict, no family
        "The units look consistent to me.",     # family word in prose is not a marker
        "Units: fine",                          # heading without the registered prefix
        "",
    ])
    def test_non_markers(self, line):
        assert marker_family(line) is None
        assert MARKER_RE.match(line.strip()) is None


class TestPSegment:
    def test_heading_shape_recovers_fenced_verdict_under_it(self):
        seg = p_segment(P_HEADING, "units")
        assert seg["present"] and seg["marker_line"] == "## Q-units"
        assert seg["text"].startswith("## Q-units")
        assert "FLAG — worker_health.py" in seg["text"]
        assert "Q-comparison" not in seg["text"]           # ends at the next family
        assert not seg["text"].endswith("```")             # dangling fence trimmed

    def test_head_only_line_recovers_the_block_that_follows(self):
        seg = p_segment(P_HEAD_ONLY, "sign")
        assert seg["present"] and "hold.position -= 1" in seg["text"]
        assert "Q-units" not in seg["text"]

    def test_unfenced_hybrid_is_present_and_bounded(self):
        seg = p_segment(P_HEAD_ONLY, "boundary")
        assert seg["text"] == "Q-boundary: NO-DEFECT-boundary"

    def test_bold_heads(self):
        seg = p_segment(P_BOLD, "exception")
        assert seg["present"] and "IndexError" in seg["text"]
        assert "Q-comparison" not in seg["text"]
        assert p_segment(P_BOLD, "sign")["text"] == "**Q-sign:** NO-DEFECT-sign"   # last family runs to EOF

    def test_true_missing_stays_missing(self):
        seg = p_segment(P_TRUE_MISSING, "units")
        assert seg == {"present": False, "text": None, "marker_line": None,
                       "start": None, "end": None}
        assert p_segment(P_TRUE_MISSING, "sign")["present"]

    def test_empty_and_none(self):
        assert p_segment("", "units")["present"] is False
        assert p_segment(None, "units")["present"] is False

    def test_same_family_repeat_stays_in_segment(self):
        txt = "Q-units: FLAG — ms vs s\nmore detail\nNO-DEFECT-units\nQ-sign: NONE"
        seg = p_segment(txt, "units")
        assert seg["text"] == "Q-units: FLAG — ms vs s\nmore detail\nNO-DEFECT-units"

    def test_unknown_family_refused(self):
        with pytest.raises(ValueError):
            p_segment("Q-units: NONE", "significance")


class TestTurnText:
    def test_wrong_label_turn_is_present(self):
        t = "Q-comparison: NO-DEFECT-comparison\n\nI reviewed all comparisons in the code."
        assert turn_text(t) == {"present": True, "text": t, "marker_line": None}

    def test_label_less_flag_prose_is_present(self):
        t = "FLAG — irrigation_scheduler.py, `_effective_delivery_rate`; the sign is inverted."
        assert turn_text(t)["present"]

    def test_empty_turn_is_missing(self):
        assert turn_text("   \n") == {"present": False, "text": None, "marker_line": None}
        assert turn_text(None)["present"] is False

    def test_scored_text_dispatch(self):
        assert scored_text("S", "NO-DEFECT-comparison", "exception")["present"]
        assert scored_text("Sq", "", "units")["present"] is False
        assert scored_text("P", P_TRUE_MISSING, "units")["present"] is False
        with pytest.raises(ValueError):
            scored_text("X", "text", "units")


class TestRetentionNormalization:
    def test_fence_lines_and_whitespace_are_immaterial(self):
        a = "Q-boundary: NO-DEFECT-boundary"
        b = "Q-boundary: NO-DEFECT-boundary\n```\n\n```"
        assert normalize_for_retention(a) == normalize_for_retention(b)
        assert normalize_for_retention("```python\nx\n```") == "x"

    def test_extra_prose_breaks_equality(self):
        a = "Q-boundary: NO-DEFECT-boundary"
        b = "Q-boundary: NO-DEFECT-boundary\n```\n\nBoundary conditions are handled correctly."
        assert normalize_for_retention(a) != normalize_for_retention(b)

    def test_none_is_empty(self):
        assert normalize_for_retention(None) == ""


class TestComposeWithPresence:
    KEYS = ["timeout_ms", "seconds"]

    def test_unfenced_hybrid_rides_borderline(self):
        # the 71-row shape: strict MISSING (unfenced), loose MALFORMED (hybrid)
        txt = "Q-units: NO-DEFECT-units"
        row = score_target_question(txt, "units", self.KEYS)
        assert (row["parser_strict_status"], row["parser_loose_status"]) == ("MISSING", "MALFORMED")
        assert row["status"] == "NON-CATCH"                  # registered chain, unchanged
        new = compose_with_presence(row, arm="P", text=txt)
        assert new["status"] == "BORDERLINE" and new["hit"] is None
        assert new["route"] == "permissive-present"
        assert new["presented_block"] == new["scored_text"] == txt
        assert row["status"] == "NON-CATCH"                  # input row not mutated

    def test_heading_shape_target_rides_borderline_with_full_segment(self):
        row = score_target_question(P_HEADING, "units", self.KEYS)
        assert row["status"] == "NON-CATCH" and row["parser_strict_status"] == "MISSING"
        new = compose_with_presence(row, arm="P", text=P_HEADING)
        assert new["status"] == "BORDERLINE"
        assert "FLAG — worker_health.py" in new["presented_block"]
        assert new["presence_marker"] == "## Q-units"

    def test_true_missing_stays_non_catch(self):
        row = score_off_family_question(P_TRUE_MISSING, "units", item_defect_keys=["-="])
        assert row["status"] == "SILENT"
        new = compose_with_presence(row, arm="P", text=P_TRUE_MISSING)
        assert new["status"] == "SILENT" and new["route"] == "missing"
        assert new["presence"] == "MISSING" and new["scored_text"] is None
        assert "presented_block" not in new

    def test_s_turn_without_family_token_rides_borderline(self):
        txt = "FLAG — calorie_budget.py, compute_todays_allowance(), line: allowance -= yesterday_balance"
        row = score_target_question(txt, "sign", ["-="])
        assert row["status"] == "NON-CATCH"
        new = compose_with_presence(row, arm="Sq", text=txt)
        assert new["status"] == "BORDERLINE" and new["presented_block"] == txt

    def test_strict_parsed_row_untouched(self):
        txt = "```\nQ-units: FLAG — ms compared to s in find_stale_workers, timeout_ms\n```\nextra prose"
        row = score_target_question(txt, "units", self.KEYS)
        assert row["status"] == "CATCH"
        new = compose_with_presence(row, arm="S", text=txt)
        assert new["status"] == "CATCH" and new["route"] == "strict-parsed"
        assert new["scored_text"] == row["raw_block"]
        assert "presented_block" not in new

    def test_strict_malformed_presents_whole_turn_for_s(self):
        txt = "```\nQ-sign: NO-DEFECT-sign\n```\n\nI have carefully reviewed all arithmetic operations."
        row = score_target_question(txt, "sign", ["-="])
        assert row["status"] == "BORDERLINE" and row["parser_strict_status"] == "MALFORMED"
        new = compose_with_presence(row, arm="S", text=txt)
        assert new["route"] == "strict-malformed"
        assert new["presented_block"] == txt.strip()
        # the OLD lane saw only the strict chunk — retention must NOT hold here
        assert normalize_for_retention(row["raw_block"]) != normalize_for_retention(new["presented_block"])

    def test_loose_parsed_presents_segment_for_p(self):
        txt = "Q-units: NONE — all ms\n\nQ-sign: FLAG — wrong operator"
        row = score_target_question(txt, "units", self.KEYS)
        assert row["status"] == "BORDERLINE" and row["parser_loose_status"] == "PARSED"
        new = compose_with_presence(row, arm="P", text=txt)
        assert new["route"] == "loose-parsed" and new["presented_block"] == "Q-units: NONE — all ms"

    def test_unexpected_status_refused(self):
        row = score_target_question("Q-units: NO-DEFECT-units", "units", self.KEYS)
        row["status"] = "CATCH"      # a registered-chain row can never say this here
        with pytest.raises(ValueError):
            compose_with_presence(row, arm="P", text="Q-units: NO-DEFECT-units")


# --------------------------------------------------------- live-table check
_TIERS = ("claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5")
DISPATCHES = Path(__file__).resolve().parents[1] / "data" / "dispatches"


def test_live_residual_recovery_is_470_of_471():
    """The first recount's finding, pinned on the PUBLIC dispatch tables (no
    skip: absent data fails loudly). Every dispatch is re-scored through the
    registered chain + presence overlay (`score_table.rows_for_record`); of
    the strict-MISSING ∧ ¬loose-PARSED rows, exactly 471 exist, 470 carry
    text (→ BORDERLINE via the permissive route) and exactly 1 (opus P
    mf-sign-06 rep 3 / units) has no text at all."""
    import score_table as st
    for t in _TIERS:
        assert (DISPATCHES / f"{t}.jsonl").exists(), f"missing public table {t}"
    items = {}
    for p in sorted((Path(__file__).resolve().parents[1] / "materials" / "items").glob("*.json")):
        it = json.loads(p.read_text())
        items[it["id"]] = it
    allowances = st.load_allowances(
        Path(__file__).resolve().parents[1] / "data" / "frozen" / "audit-key-table.json")
    resid, present, missing = 0, 0, []
    for t in _TIERS:
        for ln in (DISPATCHES / f"{t}.jsonl").read_text().splitlines():
            if not ln.strip():
                continue
            for row in st.rows_for_record(json.loads(ln), items, allowances, t):
                if row["parser_strict_status"] != "MISSING" or row["parser_loose_status"] == "PARSED":
                    continue
                resid += 1
                if row["route"] == "permissive-present":
                    assert row["status"] == "BORDERLINE"
                    present += 1
                else:
                    missing.append((row["tier"], row["arm"], row["item"], row["rep"],
                                    row["family"], row["route"]))
    assert resid == 471
    assert present == 470
    assert missing == [("claude-opus-5", "P", "mf-sign-06", 3, "units", "missing")]
