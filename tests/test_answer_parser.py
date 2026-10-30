"""test_answer_parser.py — the multi-answer parser.

Tested here as a plain Python module. Two test surfaces:

  * targeted unit tests for each parser property (per-property style);
  * a parametrized replay of EVERY row in
    `tests/fixtures/golden-masters.jsonl` — every §9 golden-master
    category (prose prefix; standalone NONE not censoring siblings;
    numbered pseudo-entries; Sq-turn recap preceding a real block) plus
    the extra robustness vectors this component authored, each carrying
    its own expected STRICT and LOOSE output (the robustness co-read pinned
    as data, not just as code paths).

`tests/fixtures/` holds FIXTURE vectors for THIS test only — explicitly NOT
the frozen study materials. Nothing here is frozen.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "analysis"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from answer_parser import FAMILIES, parse_response  # noqa: E402

GOLDENS = Path(__file__).resolve().parent / "fixtures/golden-masters.jsonl"


def _load_goldens() -> list[dict]:
    rows = [json.loads(ln) for ln in GOLDENS.read_text().splitlines() if ln.strip()]
    assert rows, f"no golden-master vectors found at {GOLDENS}"
    return rows


GOLDEN_ROWS = _load_goldens()
_SECTION9_CATEGORIES = {
    "prose prefix before a block",
    "a standalone NONE inside a bundled response that must not censor sibling blocks",
    "numbered pseudo-entries",
    "Sq-turn recaps of earlier answers preceding a real block",
}


# --------------------------------------------------------------- fixture file


def test_golden_master_file_covers_every_registered_section9_category():
    covered = {row["section9_category"] for row in GOLDEN_ROWS if row.get("section9_category")}
    missing = _SECTION9_CATEGORIES - covered
    assert not missing, f"§9 golden-master categories with no fixture row: {missing}"


@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=[r["id"] for r in GOLDEN_ROWS])
def test_golden_master_vector_strict(row):
    got = parse_response(row["text"], row["expected_families"], variant="strict")
    assert got == row["expected_strict"]


@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=[r["id"] for r in GOLDEN_ROWS])
def test_golden_master_vector_loose(row):
    got = parse_response(row["text"], row["expected_families"], variant="loose")
    assert got == row["expected_loose"]


def test_golden_master_ids_are_unique():
    ids = [row["id"] for row in GOLDEN_ROWS]
    assert len(ids) == len(set(ids))


# ------------------------------------------------------------- basic shapes


def test_p_arm_shape_five_well_formed_blocks_all_parse():
    text = "\n".join(
        f"```\nQ-{fam}: NONE\n```" for fam in FAMILIES
    )
    got = parse_response(text, list(FAMILIES), variant="strict")
    assert all(v["status"] == "PARSED" and v["verdict"] == "NONE" for v in got.values())


def test_s_arm_shape_single_family_expected():
    text = "```\nQ-sign: NONE\n```\n"
    got = parse_response(text, ["sign"], variant="strict")
    assert set(got) == {"sign"}
    assert got["sign"]["status"] == "PARSED"


def test_missing_is_returned_for_every_requested_family_with_no_block_at_all():
    got = parse_response("no fenced content whatsoever", list(FAMILIES), variant="strict")
    assert all(v == {"status": "MISSING", "verdict": None, "mechanism": None,
                     "raw_block": None, "occurrences": 0} for v in got.values())


def test_result_keys_are_exactly_the_requested_families_in_request_order():
    got = parse_response("", ["units", "boundary"], variant="strict")
    assert list(got.keys()) == ["units", "boundary"]


def test_a_family_absent_from_expected_families_is_never_returned_even_if_present():
    text = "```\nQ-boundary: FLAG — off-by-one\n```\n```\nQ-sign: NONE\n```\n"
    got = parse_response(text, ["boundary"], variant="strict")
    assert set(got) == {"boundary"}


def test_unknown_family_name_refuses():
    with pytest.raises(ValueError, match="unknown family"):
        parse_response("```\nQ-boundary: NONE\n```\n", ["not-a-family"], variant="strict")


def test_unknown_variant_name_refuses():
    with pytest.raises(ValueError, match="unknown parser variant"):
        parse_response("```\nQ-boundary: NONE\n```\n", ["boundary"], variant="lax")


def test_none_text_input_is_missing_not_a_crash():
    got = parse_response(None, ["boundary"], variant="strict")
    assert got["boundary"]["status"] == "MISSING"


# ---------------------------------------------------------- FLAG / mechanism


def test_flag_requires_a_mechanism_bare_flag_is_malformed():
    got = parse_response("```\nQ-boundary: FLAG\n```\n", ["boundary"], variant="strict")
    assert got["boundary"]["status"] == "MALFORMED"


def test_none_never_requires_a_mechanism():
    got = parse_response("```\nQ-boundary: NONE\n```\n", ["boundary"], variant="strict")
    assert got["boundary"] == {"status": "PARSED", "verdict": "NONE", "mechanism": None,
                              "raw_block": "Q-boundary: NONE", "occurrences": 1}


def test_none_with_a_stated_mechanism_still_parses():
    text = "```\nQ-boundary: NONE — no off-by-one found in the range check\n```\n"
    got = parse_response(text, ["boundary"], variant="strict")
    assert got["boundary"]["status"] == "PARSED"
    assert got["boundary"]["verdict"] == "NONE"
    assert got["boundary"]["mechanism"] == "no off-by-one found in the range check"


def test_flag_mechanism_may_come_entirely_from_continuation_lines_no_dash():
    text = "```\nQ-exception: FLAG\nthe handler swallows every exception silently\n```\n"
    got = parse_response(text, ["exception"], variant="strict")
    assert got["exception"]["status"] == "PARSED"
    assert got["exception"]["mechanism"] == "the handler swallows every exception silently"


def test_flag_mechanism_joins_inline_and_continuation_with_one_space():
    text = "```\nQ-units: FLAG — seconds vs milliseconds,\nnever converted before comparison\n```\n"
    got = parse_response(text, ["units"], variant="strict")
    assert got["units"]["mechanism"] == "seconds vs milliseconds, never converted before comparison"


# ------------------------------------------------------- fence / block scoping


def test_prose_outside_any_fence_is_never_scanned_for_a_verdict():
    # A family mentioned only in unfenced prose (never inside a ``` block)
    # must not satisfy that family — only a fenced block counts (§5.2).
    text = "I think Q-boundary: FLAG describes it well, but here's my real answer:\n"
    got = parse_response(text, ["boundary"], variant="strict")
    assert got["boundary"]["status"] == "MISSING"


def test_a_malformed_or_unattributable_block_never_affects_sibling_families():
    text = ("```\nQ-boundary: FLAG — off-by-one\n```\n"
           "```\nNONE\n```\n"
           "```\nQ-sign: NONE\n```\n")
    got = parse_response(text, ["boundary", "comparison", "sign"], variant="strict")
    assert got["boundary"]["status"] == "PARSED"
    assert got["comparison"]["status"] == "MISSING"  # the bare NONE names no family
    assert got["sign"]["status"] == "PARSED"


def test_presence_regex_word_boundary_stops_a_longer_word_poisoning_a_real_sibling():
    # Finding 6 (repair-set review): without a word boundary right after
    # the family alternation, "Q-significance:" matched as family "sign"
    # (a bare PREFIX match), and its raw_block collided with the REAL
    # "Q-sign: NONE" answer inside `_reconcile_occurrences`'s disagreement
    # branch, destroying a clean PARSED verdict into MALFORMED. A poisoning
    # line for a name that ISN'T one of the five families must never be
    # attributed to any family at all.
    text = "```\nQ-significance: FLAG — note\nQ-sign: NONE\n```\n"
    got = parse_response(text, ["sign"], variant="strict")
    assert got["sign"] == {"status": "PARSED", "verdict": "NONE", "mechanism": None,
                           "raw_block": "Q-sign: NONE", "occurrences": 1}
    loose = parse_response(text, ["sign"], variant="loose")
    assert loose["sign"]["status"] == "PARSED" and loose["sign"]["verdict"] == "NONE"


def test_two_families_inside_one_fence_still_split_and_parse_independently():
    text = "```\nQ-boundary: NONE\nQ-comparison: FLAG — swapped operands\n```\n"
    got = parse_response(text, ["boundary", "comparison"], variant="strict")
    assert got["boundary"]["status"] == "PARSED" and got["boundary"]["verdict"] == "NONE"
    assert got["comparison"]["status"] == "PARSED" and got["comparison"]["verdict"] == "FLAG"


def test_repeated_family_with_agreeing_verdicts_keeps_the_first_occurrence():
    # Both occurrences agree (FLAG both times) -- no ambiguity to judge,
    # so the first occurrence's fields are kept, tagged with the count.
    text = ("```\nQ-boundary: FLAG — first mechanism\n```\n"
           "```\nQ-boundary: FLAG — restated mechanism\n```\n")
    got = parse_response(text, ["boundary"], variant="strict")
    assert got["boundary"]["status"] == "PARSED"
    assert got["boundary"]["verdict"] == "FLAG"
    assert got["boundary"]["mechanism"] == "first mechanism"
    assert got["boundary"]["occurrences"] == 2


def test_repeated_family_with_conflicting_verdicts_is_malformed_never_arbitrarily_picked():
    # A first-occurrence-wins rule would silently discard the demonstrated
    # FLAG catch as NONE (or vice versa) -- neither variant may pick a
    # side; the conflict surfaces as MALFORMED with both raw blocks kept.
    text = ("```\nQ-boundary: FLAG — first mechanism\n```\n"
           "```\nQ-boundary: NONE\n```\n")
    got = parse_response(text, ["boundary"], variant="strict")
    assert got["boundary"]["status"] == "MALFORMED"
    assert got["boundary"]["verdict"] is None
    assert got["boundary"]["occurrences"] == 2
    assert "Q-boundary: FLAG — first mechanism" in got["boundary"]["raw_block"]
    assert "Q-boundary: NONE" in got["boundary"]["raw_block"]


def test_occurrences_field_is_zero_for_missing_and_one_for_a_single_answer():
    text = "```\nQ-boundary: NONE\n```\n"
    got = parse_response(text, ["boundary", "sign"], variant="strict")
    assert got["boundary"]["occurrences"] == 1
    assert got["sign"]["occurrences"] == 0


# --------------------------------------------------------------- strict vs loose


def test_strict_requires_a_properly_closed_fence_loose_tolerates_truncation():
    # Text plainly exists (presence is fence-closure-independent in BOTH
    # variants) -- strict's fence-closure requirement makes this MALFORMED,
    # never the invisible MISSING (§8: MISSING is reserved for no text at
    # all, not for text that fails one grammar rule).
    text = "```\nQ-units: FLAG — bytes vs kilobytes\n"  # never closed
    strict = parse_response(text, ["units"], variant="strict")
    loose = parse_response(text, ["units"], variant="loose")
    assert strict["units"]["status"] == "MALFORMED"
    assert loose["units"]["status"] == "PARSED"
    assert loose["units"]["verdict"] == "FLAG"


def test_strict_rejects_leading_list_numbering_loose_tolerates_it():
    # Presence detection is numbering-tolerant in BOTH variants (a numbered
    # entry is manifestly text, never invisible); strict's byte-exact head
    # grammar still refuses the leading number, so the disposition is
    # MALFORMED, not MISSING.
    text = "```\n1. Q-sign: FLAG — inverted delta\n```\n"
    strict = parse_response(text, ["sign"], variant="strict")
    loose = parse_response(text, ["sign"], variant="loose")
    assert strict["sign"]["status"] == "MALFORMED"
    assert loose["sign"]["status"] == "PARSED"
    assert loose["sign"]["mechanism"] == "inverted delta"


def test_strict_is_case_sensitive_loose_is_not():
    text = "```\nq-comparison: none\n```\n"
    strict = parse_response(text, ["comparison"], variant="strict")
    loose = parse_response(text, ["comparison"], variant="loose")
    assert strict["comparison"]["status"] == "MALFORMED"
    assert loose["comparison"]["status"] == "PARSED"
    assert loose["comparison"]["verdict"] == "NONE"


def test_strict_requires_the_registered_em_dash_loose_accepts_hyphen_variants():
    text = "```\nQ-sign: FLAG - a plain hyphen instead of the registered em-dash\n```\n"
    strict = parse_response(text, ["sign"], variant="strict")
    loose = parse_response(text, ["sign"], variant="loose")
    assert strict["sign"]["status"] == "MALFORMED"
    assert loose["sign"]["status"] == "PARSED"


def test_loose_still_refuses_a_garbled_verdict_token_never_widens_the_field_set():
    # Presence locates the tag (text exists for this question); neither
    # variant's HEAD grammar accepts "MAYBE" as a verdict word, so both
    # report MALFORMED (present, ungradeable) -- never MISSING (which would
    # falsely claim no text exists) and never a silently invented FLAG/NONE.
    text = "```\nQ-boundary: MAYBE — not sure\n```\n"
    strict = parse_response(text, ["boundary"], variant="strict")
    loose = parse_response(text, ["boundary"], variant="loose")
    assert strict["boundary"]["status"] == "MALFORMED"
    assert loose["boundary"]["status"] == "MALFORMED"


def test_loose_never_leaves_stray_separator_punctuation_in_the_mechanism():
    # A dangling end-of-line dash with the mechanism on the next line must
    # not glue a leftover '-'/'—' onto the captured mechanism text.
    text = "```\nQ-exception: FLAG —\nthe handler swallows every exception\n```\n"
    loose = parse_response(text, ["exception"], variant="loose")
    assert loose["exception"]["status"] == "PARSED"
    mechanism = loose["exception"]["mechanism"]
    assert mechanism == "the handler swallows every exception"
    assert not mechanism.startswith("-") and not mechanism.startswith("–") \
        and not mechanism.startswith("—")


# --------------------------------------------------------------- NO-DEFECT-<family>


def test_no_defect_token_wrong_case_is_strict_malformed_loose_parsed():
    # Finding 3(a): the NO-DEFECT grammar carries the SAME strict/loose
    # case discipline as the Q-<family> grammar -- strict wants the
    # byte-exact registered token.
    text = "```\nno-defect-boundary\n```\n"
    strict = parse_response(text, ["boundary"], variant="strict")
    loose = parse_response(text, ["boundary"], variant="loose")
    assert strict["boundary"]["status"] == "MALFORMED"
    assert loose["boundary"]["status"] == "PARSED"
    assert loose["boundary"]["verdict"] == "NONE"


def test_no_defect_token_trailing_content_is_strict_malformed():
    # Strict wants the bare token alone on its line (the registered
    # instruction's own output, nothing appended); loose tolerates it via
    # its word-bounded, non-anchored grammar.
    text = "```\nNO-DEFECT-boundary and nothing else was found\n```\n"
    strict = parse_response(text, ["boundary"], variant="strict")
    loose = parse_response(text, ["boundary"], variant="loose")
    assert strict["boundary"]["status"] == "MALFORMED"
    assert loose["boundary"]["status"] == "PARSED"


def test_no_defect_token_never_censors_a_sibling_familys_real_answer():
    text = "```\nNO-DEFECT-boundary\nQ-sign: FLAG — inverted delta\n```\n"
    got = parse_response(text, ["boundary", "sign"], variant="strict")
    assert got["boundary"]["status"] == "PARSED" and got["boundary"]["verdict"] == "NONE"
    assert got["sign"]["status"] == "PARSED" and got["sign"]["verdict"] == "FLAG"


# ------------------------------------------------------- determinism / safety


@pytest.mark.parametrize("variant", ["strict", "loose"])
def test_no_catastrophic_backtracking_on_a_long_adversarial_line(variant):
    # A long run of dash-like/whitespace characters right after the verdict
    # token, with no terminating structure — bounded quantifiers only, so
    # this must return promptly rather than hang.
    text = "```\nQ-boundary: FLAG " + ("- " * 5000) + "\n```\n"
    got = parse_response(text, ["boundary"], variant=variant)
    assert got["boundary"]["status"] in ("PARSED", "MALFORMED")


def test_raw_block_is_none_only_for_missing_never_for_malformed():
    got = parse_response("```\nQ-boundary: FLAG\n```\n", ["boundary"], variant="strict")
    assert got["boundary"]["status"] == "MALFORMED"
    assert got["boundary"]["raw_block"] is not None


@pytest.mark.parametrize("variant", ["strict", "loose"])
def test_status_is_always_one_of_the_three_registered_values(variant):
    for row in GOLDEN_ROWS:
        got = parse_response(row["text"], row["expected_families"], variant=variant)
        for v in got.values():
            assert v["status"] in ("PARSED", "MISSING", "MALFORMED")
