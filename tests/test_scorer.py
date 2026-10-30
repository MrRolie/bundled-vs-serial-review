"""test_scorer.py — per-question scoring primitives.

Analysis-helper test file: plain pytest over `scorer.py`. Mirrors
`test_answer_parser.py`'s per-property style; the parser's own golden-master
vectors are NOT re-tested here (that file owns them) -- these tests
exercise the §5.2/§5.3/§8/§10/§11.4 composition this file adds ON TOP of
the parser.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "analysis"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import scorer as sc  # noqa: E402

# ------------------------------------------------- record contract, on the public tables
# The trial runner built TWO record shapes (single-dispatch P/S; Sq session
# with per-turn completion fields). The original suite pinned the contract
# against records the runner itself built; the runner is not published, so
# here it is pinned against every record of the published dispatch tables,
# plus fail-safe negatives (a missing completion field must read as failure).
_ROOT = Path(__file__).resolve().parent.parent
_TIERS = ("claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5")


def _dispatches():
    recs = []
    for t in _TIERS:
        p = _ROOT / "data/dispatches" / f"{t}.jsonl"
        assert p.exists(), f"public dispatch table missing: {p}"
        recs += [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]
    return recs


class TestRecordContractOnPublicDispatchTables:
    def test_every_record_is_clean_and_yields_its_text(self):
        recs = _dispatches()
        assert len(recs) == 3660
        n_turns = 0
        for r in recs:
            assert not sc.is_instrument_failure(r), (r["item"], r["arm"], r["rep"])
            if r["arm"] == "Sq":
                assert len(r["turns"]) == 5
                for t in r["turns"]:
                    assert sc.sq_turn_text(r, t["family"]) == t["result"]
                    n_turns += 1
                with pytest.raises(ValueError):
                    sc.trial_text(r)
            else:
                assert sc.trial_text(r) == r["result"]
        assert n_turns == (240 + 132) * 5

    @pytest.mark.parametrize("field", ["rc", "is_error", "subtype", "stop_reason"])
    def test_missing_completion_field_reads_as_failure(self, field):
        rec = next(r for r in _dispatches() if r["arm"] == "P")
        bad = {k: v for k, v in rec.items() if k != field}
        assert sc.is_instrument_failure(bad)
        with pytest.raises(ValueError):
            sc.trial_text(bad)

    def test_sq_session_without_is_error_reads_as_failure(self):
        rec = next(r for r in _dispatches() if r["arm"] == "Sq")
        bad = {k: v for k, v in rec.items() if k != "is_error"}
        assert sc.is_instrument_failure(bad)


class TestFamilyHit:
    def test_flag_with_key_match_hits(self):
        entry = {"verdict": "FLAG", "raw_block": "Q-boundary: FLAG — off-by-one at line 40"}
        assert sc.family_hit(entry, ["off-by-one"]) is True

    def test_flag_without_key_match_misses(self):
        entry = {"verdict": "FLAG", "raw_block": "Q-boundary: FLAG — wrong comparator"}
        assert sc.family_hit(entry, ["off-by-one"]) is False

    def test_none_verdict_never_hits_even_with_a_key_present(self):
        """§5.2: "verdict-only is measured DEAD" -- and the converse also
        never applies: a NONE verdict is not a hit no matter what text a
        (nonexistent, since NONE carries no mechanism) block would contain."""
        entry = {"verdict": "NONE", "raw_block": "Q-boundary: NONE — off-by-one"}
        assert sc.family_hit(entry, ["off-by-one"]) is False

    def test_key_match_is_case_insensitive_any_of_tuple(self):
        entry = {"verdict": "FLAG", "raw_block": "Q-sign: FLAG — Delta Was Negated"}
        assert sc.family_hit(entry, ["nonexistent-key", "delta was negated"]) is True


# --------------------------------------------------------- clean_any_flag / flag_count
class TestCleanAnyFlagAndFlagCount:
    def test_any_family_flag_trips_the_clean_side(self):
        entries = {
            "boundary": {"verdict": "NONE"}, "sign": {"verdict": "FLAG"},
            "units": {"verdict": "NONE"}, "comparison": {"verdict": "NONE"},
            "exception": {"verdict": "NONE"},
        }
        assert sc.clean_any_flag(entries) is True
        assert sc.flag_count(entries) == 1

    def test_all_none_never_flags(self):
        entries = {f: {"verdict": "NONE"} for f in sc.FAMILIES}
        assert sc.clean_any_flag(entries) is False
        assert sc.flag_count(entries) == 0

    def test_malformed_or_missing_entries_never_count_as_a_flag(self):
        """A MALFORMED/MISSING entry carries `verdict: None` from the
        parser -- neither should ever be silently read as a FLAG."""
        entries = {
            "boundary": {"verdict": None, "status": "MALFORMED"},
            "sign": {"verdict": None, "status": "MISSING"},
            "units": {"verdict": "FLAG"},
            "comparison": {"verdict": "NONE"},
            "exception": {"verdict": "NONE"},
        }
        assert sc.flag_count(entries) == 1
        assert sc.clean_any_flag(entries) is True   # the one real FLAG still counts


class TestOffFamilyDenominator:
    def test_no_allowance_is_the_full_four(self):
        assert sc.off_family_denominator([]) == 4

    def test_two_allowances_shrink_by_two(self):
        assert sc.off_family_denominator(["sign", "units"]) == 2

    def test_duplicate_allowances_count_once(self):
        assert sc.off_family_denominator(["sign", "sign"]) == 3

    def test_more_than_four_allowances_refused(self):
        with pytest.raises(ValueError):
            sc.off_family_denominator(["boundary", "comparison", "exception", "sign", "units"])


# --------------------------------------------------- score_target_question (§8/§9)
class TestScoreTargetQuestion:
    def test_parsed_flag_with_key_match_is_catch(self):
        text = "```\nQ-boundary: FLAG — off-by-one in the loop bound\n```"
        row = sc.score_target_question(text, "boundary", ["off-by-one"])
        assert row["status"] == "CATCH"
        assert row["hit"] is True
        assert row["parser_strict_status"] == "PARSED"

    def test_parsed_flag_without_key_match_is_non_catch(self):
        text = "```\nQ-boundary: FLAG — wrong comparator entirely\n```"
        row = sc.score_target_question(text, "boundary", ["off-by-one"])
        assert row["status"] == "NON-CATCH"
        assert row["hit"] is False

    def test_parsed_none_is_non_catch(self):
        text = "```\nQ-boundary: NONE\n```"
        row = sc.score_target_question(text, "boundary", ["off-by-one"])
        assert row["status"] == "NON-CATCH"
        assert row["hit"] is False

    def test_missing_block_is_non_catch_mechanically_never_borderline(self):
        """§8: "in deployment, no answer is no answer" -- MISSING scores
        NON-CATCH directly, never routed to a human."""
        row = sc.score_target_question("no fenced answer anywhere", "boundary", ["off-by-one"])
        assert row["status"] == "NON-CATCH"
        assert row["hit"] is False
        assert row["parser_strict_status"] == "MISSING"

    def test_malformed_present_block_is_borderline_unconditionally(self):
        """§8/§10: a strict-MALFORMED block routes to BORDERLINE even when
        it carries no recoverable verdict at all under either variant."""
        text = "```\nQ-boundary: MAYBE — some garbled verdict token\n```"
        row = sc.score_target_question(text, "boundary", ["off-by-one"])
        assert row["status"] == "BORDERLINE"
        assert row["hit"] is None
        assert row["parser_strict_status"] == "MALFORMED"

    def test_malformed_under_strict_but_loose_recoverable_still_borderlines(self):
        """The load-bearing composition rule (§8/§10, confirmed in
        design review): loose recovering a clean verdict from a strict-MALFORMED
        block does NOT let the row skip BORDERLINE -- loose is a co-read,
        never a fallback that resolves the row on its own. Wrong-case
        family word is strict-MALFORMED (exact-case grammar) but
        loose-PARSED (case-insensitive)."""
        text = "```\nQ-Boundary: FLAG — off-by-one in the loop bound\n```"
        row = sc.score_target_question(text, "boundary", ["off-by-one"])
        assert row["parser_strict_status"] == "MALFORMED"
        assert row["parser_loose_status"] == "PARSED"
        assert row["status"] == "BORDERLINE"          # strict still governs the primary read
        assert row["co_read_loose_status"] == "CATCH"  # loose WOULD have caught it
        assert row["co_read_divergence"] is True

    def test_strict_missing_but_loose_recovers_an_unfenced_answer_borderlines_never_non_catch(self):
        """Finding 3(b) (repair-set review, design ruling): strict finds NO
        fenced attempt at all for this family (plain MISSING), but loose
        -- which also scans unfenced text (answer_parser finding 3(b)) --
        recovers a well-formed answer sitting outside any fence. Text
        manifestly exists, just never fenced, so this routes to
        BORDERLINE exactly like a strict-MALFORMED block, NEVER the
        mechanical NON-CATCH a plain MISSING would otherwise compose."""
        text = "Q-boundary: FLAG — off-by-one in the loop bound"   # never fenced at all
        row = sc.score_target_question(text, "boundary", ["off-by-one"])
        assert row["parser_strict_status"] == "MISSING"
        assert row["parser_loose_status"] == "PARSED"
        assert row["status"] == "BORDERLINE"
        assert row["hit"] is None
        assert row["co_read_loose_status"] == "CATCH"   # loose WOULD have caught it
        assert row["co_read_divergence"] is True

    def test_strict_missing_and_loose_also_missing_still_non_catches(self):
        """The fallback fires ONLY on strict-MISSING + loose-PARSED --
        when neither variant finds any attempt anywhere (loose's WIDER
        scan still finds nothing), MISSING stays mechanical NON-CATCH."""
        row = sc.score_target_question("no fenced answer anywhere", "boundary", ["off-by-one"])
        assert row["parser_strict_status"] == "MISSING"
        assert row["parser_loose_status"] == "MISSING"
        assert row["status"] == "NON-CATCH"
        assert row["hit"] is False

    def test_unknown_family_refused(self):
        with pytest.raises(ValueError):
            sc.score_target_question("anything", "not-a-family", [])


# ---------------------------------------------- score_off_family_question (§5.3/§11.4)
class TestScoreOffFamilyQuestion:
    def test_missing_is_silent(self):
        row = sc.score_off_family_question("nothing fenced", "sign", item_defect_keys=["off-by-one"])
        assert row["status"] == "SILENT"

    def test_strict_missing_but_loose_recovers_an_unfenced_answer_borderlines_never_silent(self):
        """`_compose_off_family_primary`'s mirror of the same finding-3(b)
        fallback -- never the mechanical SILENT a plain MISSING would
        otherwise compose."""
        text = "Q-sign: NONE"   # never fenced at all
        row = sc.score_off_family_question(text, "sign", item_defect_keys=["off-by-one"])
        assert row["parser_strict_status"] == "MISSING"
        assert row["parser_loose_status"] == "PARSED"
        assert row["status"] == "BORDERLINE"

    def test_malformed_is_borderline(self):
        text = "```\nQ-sign: HUH — garbled\n```"
        row = sc.score_off_family_question(text, "sign", item_defect_keys=["off-by-one"])
        assert row["status"] == "BORDERLINE"

    def test_parsed_none_is_no_flag(self):
        text = "```\nQ-sign: NONE\n```"
        row = sc.score_off_family_question(text, "sign", item_defect_keys=["off-by-one"])
        assert row["status"] == "NO-FLAG"

    def test_flag_on_an_allowed_family_matching_its_keys_is_hit_alt_never_fa(self):
        """§5.3: an off-family FLAG matching keys on an ALLOWED family
        scores HIT-ALT, co-reported, never FA."""
        text = "```\nQ-sign: FLAG — off-by-one in the loop bound\n```"
        row = sc.score_off_family_question(
            text, "sign", item_defect_keys=["off-by-one"], allowed_families=["sign"],
        )
        assert row["status"] == "HIT-ALT"

    def test_flag_matching_real_keys_but_family_not_allowed_is_fa_with_wrong_family_flag(self):
        """§11.4 class 2 (off-family FA) AND class 3 (key-matched-but-
        wrong-family) simultaneously: the family is NOT in the allowed
        set, so it is an FA regardless of textual key match -- but the
        match is flagged for class 3's subset count."""
        text = "```\nQ-sign: FLAG — off-by-one in the loop bound\n```"
        row = sc.score_off_family_question(
            text, "sign", item_defect_keys=["off-by-one"], allowed_families=[],
        )
        assert row["status"] == "FA"
        assert row["key_matched_wrong_family"] is True

    def test_flag_with_no_key_match_and_not_allowed_is_plain_fa(self):
        text = "```\nQ-sign: FLAG — entirely unrelated observation\n```"
        row = sc.score_off_family_question(
            text, "sign", item_defect_keys=["off-by-one"], allowed_families=[],
        )
        assert row["status"] == "FA"
        assert row["key_matched_wrong_family"] is False

    def test_allowed_family_membership_alone_is_not_enough_keys_must_still_match(self):
        """Being on the allowed-families list does not itself grant
        HIT-ALT -- the FLAG must still key-match (default: the item's own
        `defect_keys`, build-time note 3) for that allowed family."""
        text = "```\nQ-sign: FLAG — a completely unrelated remark\n```"
        row = sc.score_off_family_question(
            text, "sign", item_defect_keys=["off-by-one"], allowed_families=["sign"],
        )
        assert row["status"] == "FA"

    def test_allowed_family_keys_override_is_honoured_when_supplied(self):
        text = "```\nQ-sign: FLAG — inverted delta application\n```"
        row = sc.score_off_family_question(
            text, "sign", item_defect_keys=["off-by-one"], allowed_families=["sign"],
            allowed_family_keys={"sign": ["inverted delta"]},
        )
        assert row["status"] == "HIT-ALT"


# ------------------------------------------------------------------- wilson_ci
class TestWilsonCi:
    def test_zero_trials_refused(self):
        with pytest.raises(ValueError):
            sc.wilson_ci(0, 0)

    def test_bounds_are_ordered_and_within_unit_interval(self):
        lo, hi = sc.wilson_ci(5, 10)
        assert 0.0 <= lo < 0.5 < hi <= 1.0

    def test_all_successes_upper_bound_below_one(self):
        lo, hi = sc.wilson_ci(10, 10)
        assert hi < 1.0 and hi > 0.9


# ------------------------------------------------------- format_noncompliance
class TestFormatNoncompliance:
    def test_rate_and_stamp_below_threshold(self):
        rows = (
            [{"parser_strict_status": "PARSED"}] * 8
            + [{"parser_strict_status": "MISSING"}] * 1
            + [{"parser_strict_status": "MALFORMED"}] * 1
        )
        r = sc.format_noncompliance(rows)
        assert r["rate"] == pytest.approx(0.2)
        assert r["format_degraded"] is False

    def test_stamp_fires_above_25_percent(self):
        rows = (
            [{"parser_strict_status": "PARSED"}] * 7
            + [{"parser_strict_status": "MALFORMED"}] * 3
        )
        r = sc.format_noncompliance(rows)
        assert r["rate"] == pytest.approx(0.3)
        assert r["format_degraded"] is True

    def test_instrument_failure_rows_excluded_from_the_denominator(self):
        """§10: format-noncompliance and instrument-failure are DIFFERENT
        limbs with different cause-owners; an instrument-failure row must
        never dilute (or inflate) the subject-format rate."""
        rows = (
            [{"parser_strict_status": "PARSED"}] * 3
            + [{"parser_strict_status": "MALFORMED"}] * 1
            + [{"parser_strict_status": "MISSING", "is_instrument_failure": True}] * 5
        )
        r = sc.format_noncompliance(rows)
        assert r["total"] == 4
        assert r["rate"] == pytest.approx(0.25)
        assert r["format_degraded"] is False   # 0.25 is not STRICTLY above the threshold

    def test_empty_cell_refused(self):
        with pytest.raises(SystemExit):
            sc.format_noncompliance([])


# ------------------------------------------------------------- unreliability
class TestUnreliability:
    def test_below_threshold_reads_reliable(self):
        attempts = [{"is_error": False, "rc": 0, "subtype": "success", "stop_reason": "end_turn"}] * 9
        attempts += [{"failure": "TimeoutExpired"}]
        r = sc.unreliability(attempts)
        assert r["rate"] == pytest.approx(0.1)
        assert r["unreliable"] is False   # 0.10 is not STRICTLY above threshold

    def test_above_threshold_trips_c_b_unrel(self):
        attempts = [{"is_error": False, "rc": 0, "subtype": "success", "stop_reason": "end_turn"}] * 8
        attempts += [{"failure": "TimeoutExpired"}] * 2
        r = sc.unreliability(attempts)
        assert r["rate"] == pytest.approx(0.2)
        assert r["unreliable"] is True

    def test_empty_cell_refused(self):
        with pytest.raises(SystemExit):
            sc.unreliability([])


# --------------------------------------------------------- is_instrument_failure
class TestIsInstrumentFailure:
    def test_clean_success_record_is_not_a_failure(self):
        rec = {"is_error": False, "rc": 0, "subtype": "success", "stop_reason": "end_turn"}
        assert sc.is_instrument_failure(rec) is False

    @pytest.mark.parametrize("missing_field", ["is_error", "rc", "subtype", "stop_reason"])
    def test_any_missing_completion_field_fails_safe(self, missing_field):
        rec = {"is_error": False, "rc": 0, "subtype": "success", "stop_reason": "end_turn"}
        del rec[missing_field]
        assert sc.is_instrument_failure(rec) is True

    def test_api_error_status_present_is_a_failure_even_if_other_fields_look_clean(self):
        rec = {"is_error": False, "rc": 0, "subtype": "success", "stop_reason": "end_turn",
               "api_error_status": 429}
        assert sc.is_instrument_failure(rec) is True

    def test_terminal_reason_api_error_is_a_failure(self):
        rec = {"is_error": False, "rc": 0, "subtype": "success", "stop_reason": "end_turn",
               "terminal_reason": "api_error"}
        assert sc.is_instrument_failure(rec) is True

    def test_trial_text_raises_on_a_failed_record(self):
        with pytest.raises(ValueError):
            sc.trial_text({"failure": "TimeoutExpired"})

    def test_trial_text_returns_result_on_a_clean_record(self):
        rec = {"is_error": False, "rc": 0, "subtype": "success", "stop_reason": "end_turn",
               "result": "```\nQ-units: NONE\n```"}
        assert sc.trial_text(rec) == "```\nQ-units: NONE\n```"


# ------------------------------------------------------------------ fa_bound_check
class TestFaBoundCheck:
    def test_in_bound_when_difference_small_and_ci_does_not_span(self):
        hi = [(1, 100)] * 4    # fa_hi ~= 0.01
        lo = [(0, 100)] * 4    # fa_lo == 0
        r = sc.fa_bound_check(hi, lo)
        assert r["diff"] == pytest.approx(0.01)
        assert r["state"] == "IN-BOUND"

    def test_out_of_bound_when_difference_exceeds_015_and_ci_confirms(self):
        hi = [(60, 100)] * 8
        lo = [(0, 100)] * 8
        r = sc.fa_bound_check(hi, lo)
        assert r["diff"] > 0.15
        assert r["state"] == "OUT-OF-BOUND"

    def test_empty_arm_refused(self):
        with pytest.raises(SystemExit):
            sc.fa_bound_check([], [(0, 10)])

    def test_ratio_clause_breach_with_absolute_bound_satisfied_is_out_of_bound(self):
        """Finding 5 (repair-set review): a class can satisfy the ABSOLUTE
        bound (diff <= 0.15) while breaching the RATIO clause
        (fa_hi > 2*fa_lo, fa_lo > 0) -- the confirmed empirical bug
        (fa_hi=0.25, fa_lo=0.11, diff=0.14) fell through the old
        three-branch logic to UNRESOLVED because the OUT-OF-BOUND branch
        only ever fired on `not in_abs`. fa_hi=0.10, fa_lo=0.02 here:
        diff=0.08<=0.15 (absolute bound satisfied) but 0.10 > 2*0.02=0.04
        (ratio breached); large n keeps the bootstrap CI tight and well
        clear of the 0.15 bound, so the state must resolve to
        OUT-OF-BOUND, never UNRESOLVED."""
        hi = [(25, 250)] * 4   # fa_hi = 100/1000 = 0.10
        lo = [(5, 250)] * 4    # fa_lo = 20/1000 = 0.02
        r = sc.fa_bound_check(hi, lo)
        assert r["diff"] == pytest.approx(0.08)
        assert r["diff"] <= r["bound"]           # absolute bound satisfied
        assert r["ratio_clause"] is False        # ratio clause breached
        assert not (r["ci95"][0] <= r["bound"] <= r["ci95"][1])   # CI does not span
        assert r["state"] == "OUT-OF-BOUND"

    def test_review_confirmed_example_is_out_of_bound_not_unresolved(self):
        """The review's own confirmed-empirical example: fa_hi=0.25,
        fa_lo=0.11 (diff=0.14, ratio breached: 0.25 > 2*0.11=0.22)."""
        r = sc.fa_bound_check([(25, 100)], [(11, 100)])
        assert r["state"] == "OUT-OF-BOUND"


# --------------------------------------------------------------- apply_j4_exclusion
class TestApplyJ4Exclusion:
    def test_falsified_items_leave_every_survivor_list(self):
        r = sc.apply_j4_exclusion(["cl-01", "cl-02", "cl-03", "cl-04"], ["cl-02"])
        assert r["survivors"] == ["cl-01", "cl-03", "cl-04"]
        assert r["falsified_count"] == 1
        assert r["low_power"] is True   # 3 < CLEANFAIL_MIN_SURVIVORS (4)

    def test_no_falsifications_all_survive(self):
        r = sc.apply_j4_exclusion(["cl-01", "cl-02", "cl-03", "cl-04"], [])
        assert r["survivors"] == ["cl-01", "cl-02", "cl-03", "cl-04"]
        assert r["low_power"] is False


def test_keyword_rederivation_recount_entry_point():
    """§9's registered recount surface: containment only, never a verdict."""
    from scorer import keyword_rederivation
    r = keyword_rederivation("the loop bound uses <= n where < n is right", ["<= n", "off-by-one"])
    assert r["any_match"] is True and r["matched_keys"] == ["<= n"]
    assert keyword_rederivation(None, ["x"]) == {"any_match": False, "matched_keys": []}
