"""test_zc.py -- the three degenerate responders + the J gate.

Plain pytest over `zc.py`. Every J vector below is hand-traced against the module's
keyword tables / policy tables BEFORE running (mirrors the parser/scorer
builders' precedent: implementation-derived golden masters are treated as a
defect in this codebase) -- the by-hand arithmetic for each is written into the
test's own docstring or inline comments so the trace is checkable without
re-running anything.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "analysis"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import zc as zc  # noqa: E402
from answer_parser import parse_response  # noqa: E402
from scorer import score_target_question  # noqa: E402


# ============================================================ item plumbing
class TestItemTextAndKeyTable:
    def test_item_text_prefers_explicit_text_field(self):
        item = {"text": "the diff", "files": [{"path": "x.py", "content": "def f(): pass"}]}
        assert zc._item_text(item) == "the diff"

    def test_item_text_falls_back_to_files_with_injected_path_marker(self):
        item = {"files": [{"path": "a.py", "content": "def f(): pass"}]}
        text = zc._item_text(item)
        assert "--- a.py ---" in text
        assert "def f(): pass" in text

    def test_build_key_table_excludes_stimulus_text(self):
        items = [{"item_id": "i1", "item_class": zc.MF, "defect_class": "boundary",
                  "defect_keys": ["k"], "text": "irrelevant"}]
        table = zc.build_key_table(items)
        assert table == {"i1": {"item_class": zc.MF, "defect_class": "boundary",
                                 "defect_keys": ("k",), "allowed_families": ()}}
        assert "text" not in table["i1"]

    def test_build_responses_maps_item_id_to_formatted_text(self):
        items = [{"item_id": "i1", "item_class": zc.MF, "defect_class": "clean",
                  "defect_keys": [], "text": "no keywords here"}]
        responses = zc.build_responses(items, zc.zc2_response_text)
        assert set(responses) == {"i1"}
        assert "Q-boundary: FLAG" in responses["i1"]


# ============================================================ response grammar
class TestFormattedResponsesParseCleanly:
    """Every responder's output must parse PARSED (never MALFORMED/MISSING)
    under the real strict grammar -- a formatting bug here would silently
    corrupt every J number downstream."""

    @pytest.mark.parametrize("text, expect_family", [
        (zc.zc1_response_text({"text": "def compute_bound(values, window):\n    return values[:-1]\n"}),
         "boundary"),
        (zc.zc2_response_text({}), "boundary"),
        (zc.zc3_response_text({"text": "def compute_bound(values, window):\n    return values[:-1]\n"},
                               family_selection="keyword"), "boundary"),
        (zc.zc3_response_text({}, family_selection="base_rate"), "boundary"),
    ])
    def test_all_five_blocks_parse_and_only_the_selected_family_flags(self, text, expect_family):
        parsed = parse_response(text, list(zc.FAMILIES), variant="strict")
        for fam, entry in parsed.items():
            assert entry["status"] == "PARSED", f"{fam}: {entry}"
            if fam == expect_family:
                assert entry["verdict"] == "FLAG"
                assert entry["mechanism"]
            else:
                assert entry["verdict"] == "NONE"

    def test_zc1_none_selection_flags_nothing(self):
        text = zc.zc1_response_text({"text": "def helper(x):\n    return x\n"})
        parsed = parse_response(text, list(zc.FAMILIES), variant="strict")
        assert all(e["verdict"] == "NONE" for e in parsed.values())


# ============================================================ ZC-1
class TestZC1KeywordSelection:
    def test_selects_family_with_most_keyword_hits(self):
        """def line: 'def compute_bound(values, window):' contains
        'bound' (substring of compute_bound) and 'window' -- both are
        boundary keywords, count=2; every other family's keyword list has
        zero hits in this line. Comments are never scanned (content-blind:
        only def/class signature lines, hunk headers, path markers)."""
        text = "def compute_bound(values, window):\n    return values[:-1]  # off by one\n"
        family, counts = zc.zc1_select_family(text)
        assert family == "boundary"
        assert counts["boundary"] == 2
        assert counts["comparison"] == counts["exception"] == counts["sign"] == counts["units"] == 0

    def test_ties_break_on_canonical_family_order(self):
        """'def compare_and_flip(x):' hits 'compare' (comparison) once and
        'flip' (sign) once -- a genuine 1-1 tie. FAMILIES order is
        (boundary, comparison, exception, sign, units); comparison precedes
        sign, so comparison wins the tie."""
        text = "def compare_and_flip(x):\n    return x\n"
        family, counts = zc.zc1_select_family(text)
        assert counts["comparison"] == counts["sign"] == 1
        assert counts["boundary"] == counts["exception"] == counts["units"] == 0
        assert family == "comparison"

    def test_zero_signal_selects_no_family(self):
        text = "def helper(x):\n    return x\n"
        family, counts = zc.zc1_select_family(text)
        assert family is None
        assert all(v == 0 for v in counts.values())

    def test_comments_and_docstrings_are_never_scanned(self):
        """Content-blind means structural surface only. A comment naming a
        family word must NOT move the selection -- only def/class lines,
        hunk headers, and path markers are in the scan pool."""
        text = "def helper(x):\n    # this function has a sign error\n    return x\n"
        family, counts = zc.zc1_select_family(text)
        assert family is None, "a comment must never contribute to a content-blind scan"


# ============================================================ ZC-2
class TestZC2StructuralNullJ:
    """Any diff-blind constant per-family policy is Youden-degenerate: since
    the policy never reads the item, P(FLAG | target) == P(FLAG | non-target)
    for every family, so TPR == FPR and J == 0 EVERYWHERE. Asserted directly
    against `compute_j` (not merely reasoned about) over a full 5-family +
    clean bank, both item classes."""

    @staticmethod
    def _bank():
        items = []
        for item_class in zc.ITEM_CLASSES:
            for fam in zc.FAMILIES:
                items.append({"item_id": f"{item_class}-{fam}", "item_class": item_class,
                               "defect_class": fam, "defect_keys": ["irrelevant"],
                               "text": "def helper(x):\n    return x\n"})
            items.append({"item_id": f"{item_class}-clean", "item_class": item_class,
                           "defect_class": "clean", "defect_keys": [],
                           "text": "def helper(x):\n    return x\n"})
        return items

    def test_j_is_exactly_zero_for_every_stratum(self):
        items = self._bank()
        key_table = zc.build_key_table(items)
        responses = zc.build_responses(items, zc.zc2_response_text)
        for fam in zc.FAMILIES:
            for item_class in zc.ITEM_CLASSES:
                row = zc.compute_j(fam, item_class, responses, key_table, layer="verdict")
                assert row["j"] == 0.0, row
                assert row["tpr"] == row["fpr"], row

    def test_boundary_is_the_nonvacuous_illustration(self):
        """ZC2_POLICY flags exactly 'boundary' always -- so the boundary
        stratum's TPR and FPR both land at a real 1.0 (not 0/0), still
        cancelling to J=0."""
        items = self._bank()
        key_table = zc.build_key_table(items)
        responses = zc.build_responses(items, zc.zc2_response_text)
        row = zc.compute_j("boundary", zc.MF, responses, key_table, layer="verdict")
        assert row["tpr"] == 1.0
        assert row["fpr"] == 1.0
        assert row["j"] == 0.0

    def test_response_text_is_item_independent(self):
        a = zc.zc2_response_text({"item_id": "a", "text": "anything at all"})
        b = zc.zc2_response_text({"item_id": "b", "text": "def sign_bound_except(): pass"})
        assert a == b


# ============================================================ ZC-3 / A-5 hazard
class TestZC3CompositeAndA5Hazard:
    def test_keyword_variant_delegates_family_selection_to_zc1(self):
        text = "def compute_bound(values, window):\n    return values[:-1]\n"
        resp = zc.zc3_response_text({"text": text}, family_selection="keyword")
        parsed = parse_response(resp, list(zc.FAMILIES), variant="strict")
        assert parsed["boundary"]["verdict"] == "FLAG"
        assert parsed["boundary"]["mechanism"] == zc.ZC3_GENERIC_MECHANISM["boundary"]

    def test_base_rate_variant_ignores_content_and_always_selects_boundary(self):
        resp = zc.zc3_response_text({"text": "def do_exception_thing(): pass"}, family_selection="base_rate")
        parsed = parse_response(resp, list(zc.FAMILIES), variant="strict")
        assert parsed["boundary"]["verdict"] == "FLAG"
        assert parsed["exception"]["verdict"] == "NONE"

    def test_unknown_family_selection_raises(self):
        with pytest.raises(ValueError):
            zc.zc3_response_text({}, family_selection="bogus")

    def test_A5_hazard_generic_mechanism_legitimately_matches_real_curated_keys(self):
        """The A-5 hazard, demonstrated with the REAL bank's own curated
        keys (`materials/manifest.jsonl`, item mf-boundary-01), not a
        contrived list -- and with an item whose OWN surface text carries
        ZERO boundary keywords, so this is isolated from ZC-1's keyword
        selection entirely (only ZC3's FIXED generic mechanism string is
        under test here, via the base_rate family-selection path).
        ZC3_GENERIC_MECHANISM['boundary'] = 'off by one in the loop bound;
        the range excludes the last element' contains BOTH 'off by one' AND
        'excludes the last' verbatim -- two of mf-boundary-01's real
        defect_keys -- so the through-scorer requirement correctly reports
        a CATCH even though nothing about this responder read the item."""
        real_defect_keys = ["last reading", "off by one", "excludes the last", "drops the last",
                             "elements", "the last element", "last (most recent) reading"]
        item = {"text": "def helper(x):\n    return x\n"}  # zero boundary keyword signal
        assert zc.zc1_select_family(item["text"])[0] is None, "isolate: no keyword signal present"
        resp = zc.zc3_response_text(item, family_selection="base_rate")
        row = score_target_question(resp, "boundary", real_defect_keys)
        assert row["status"] == "CATCH"
        assert row["hit"] is True

    def test_published_j_is_the_better_of_the_two_variants(self):
        """A wired-in case where keyword selection wins: item text carries
        real boundary keyword signal AND the item's OWN curated keys match
        ZC3's generic mechanism string, so the keyword variant catches while
        the base_rate variant (fixed to 'boundary' too, here, so it ALSO
        catches on this specific item) ties it -- gate-level tests below
        cover a case where they diverge across a stratum."""
        text = "def compute_bound(values, window):\n    return values[:-1]\n"
        item = {"item_id": "t", "item_class": zc.MF, "defect_class": "boundary",
                "defect_keys": ["off by one"], "text": text}
        key_table = zc.build_key_table([item])
        nontarget = {"item_id": "n", "item_class": zc.MF, "defect_class": "clean",
                     "defect_keys": [], "text": "def helper(x):\n    return x\n"}
        key_table.update(zc.build_key_table([nontarget]))
        resp_kw = zc.build_responses([item, nontarget],
                                      lambda it: zc.zc3_response_text(it, family_selection="keyword"))
        row_kw = zc.compute_j("boundary", zc.MF, resp_kw, key_table, layer="keyed")
        assert row_kw["j"] == 1.0  # tpr=1 (catch), fpr=0 (clean item never flagged)


# ============================================================ compute_j
class TestComputeJ:
    """Hand-traced fixture (module docstring reproduces the reasoning):

    t1: boundary, keys=["off by one"];  response FLAG boundary, mech "off by one bug"
    t2: boundary, keys=["nomatch-key"]; response FLAG boundary, mech "off by one bug"
    n1: sign,     keys=["x"];           response NONE everywhere
    n2: clean,    keys=[];              response FLAG boundary, mech "unrelated text"

    KEYED layer: t1 mechanism contains "off by one" -> CATCH; t2's OWN keys
    don't match the same mechanism text -> NON-CATCH. tpr = 1/2 = 0.5.
    n1 NONE -> not FA; n2 FLAG on a clean item -> FA regardless of keys
    (scorer: any FLAG not in allowed_families is FA). fpr = 1/2 = 0.5.
    j_keyed = 0.5 - 0.5 = 0.0.

    VERDICT layer ignores key match entirely: t1 and t2 BOTH verdict==FLAG
    -> tpr = 2/2 = 1.0. n1/n2 unchanged (verdict layer only cares about the
    raw verdict, and n1/n2's verdicts don't depend on keys either) ->
    fpr = 1/2 = 0.5. j_verdict = 1.0 - 0.5 = 0.5. The two layers diverge
    on the SAME underlying responses -- exactly the property the
    shortcut-gate amendment (A-5) exists to catch."""

    @staticmethod
    def _fixture():
        items = [
            {"item_id": "t1", "item_class": zc.MF, "defect_class": "boundary",
             "defect_keys": ["off by one"]},
            {"item_id": "t2", "item_class": zc.MF, "defect_class": "boundary",
             "defect_keys": ["nomatch-key"]},
            {"item_id": "n1", "item_class": zc.MF, "defect_class": "sign",
             "defect_keys": ["x"]},
            {"item_id": "n2", "item_class": zc.MF, "defect_class": "clean",
             "defect_keys": []},
        ]
        key_table = zc.build_key_table(items)
        responses = {
            "t1": zc._format_response("boundary", "off by one bug"),
            "t2": zc._format_response("boundary", "off by one bug"),
            "n1": zc._format_response(None, None),
            "n2": zc._format_response("boundary", "unrelated text"),
        }
        return key_table, responses

    def test_keyed_layer(self):
        key_table, responses = self._fixture()
        row = zc.compute_j("boundary", zc.MF, responses, key_table, layer="keyed")
        assert row == {"family": "boundary", "item_class": zc.MF, "layer": "keyed",
                        "tpr": 0.5, "fpr": 0.5, "j": 0.0,
                        "hits": 1, "n_target": 2, "false_alarms": 1, "n_nontarget": 2}

    def test_verdict_layer_diverges_on_the_same_responses(self):
        key_table, responses = self._fixture()
        row = zc.compute_j("boundary", zc.MF, responses, key_table, layer="verdict")
        assert row["tpr"] == 1.0
        assert row["fpr"] == 0.5
        assert row["j"] == 0.5

    def test_empty_target_population_refuses(self):
        key_table = {"n1": {"item_class": zc.MF, "defect_class": "clean",
                             "defect_keys": (), "allowed_families": ()}}
        responses = {"n1": zc._format_response(None, None)}
        with pytest.raises(SystemExit):
            zc.compute_j("boundary", zc.MF, responses, key_table, layer="verdict")

    def test_empty_nontarget_population_refuses(self):
        key_table = {"t1": {"item_class": zc.MF, "defect_class": "boundary",
                             "defect_keys": ("k",), "allowed_families": ()}}
        responses = {"t1": zc._format_response("boundary", "k")}
        with pytest.raises(SystemExit):
            zc.compute_j("boundary", zc.MF, responses, key_table, layer="verdict")

    def test_unknown_family_rejected(self):
        key_table, responses = self._fixture()
        with pytest.raises(ValueError):
            zc.compute_j("not-a-family", zc.MF, responses, key_table, layer="verdict")

    def test_unknown_layer_rejected(self):
        key_table, responses = self._fixture()
        with pytest.raises(ValueError):
            zc.compute_j("boundary", zc.MF, responses, key_table, layer="bogus")


# ============================================================ zc_gate
class TestZCGate:
    """Hand-traced 12-item bank, both item classes: one item per family +
    one clean item, per item class. 'boundary' items carry real keyword
    signal (def line hits 'bound'+'window') AND a curated key ('off by one')
    that ZC3's fixed boundary mechanism string legitimately matches; every
    other family's item is fully neutral (no keyword signal, mismatched
    key) so ZC1/ZC3-keyword never select them and ZC2/ZC3-base_rate (both
    fixed to 'boundary' only) never touch them either.

    Traced outcome per stratum (boundary/mf and boundary/sf):
      zc1_verdict: target FLAGged (selected via keyword signal) -> tpr=1;
        no neutral item ever gets flagged 'boundary' (they select None) ->
        fpr=0 -> j=1.0.
      zc1_keyed: target's ZC1 mechanism ('keyword match in identifiers:
        bound, window') does NOT contain 'off by one' -> NON-CATCH -> tpr=0
        -> j=0 (fpr=0 too, from the same no-neutral-flag argument).
      zc2_verdict: structurally null (proven above) -> j=0.
      zc3_published: keyword variant's mechanism IS the fixed generic
        string, which DOES contain 'off by one' -> CATCH -> tpr=1; no
        neutral item ever gets flagged 'boundary' under the keyword variant
        -> fpr=0 -> j=1.0 (already >= the base_rate variant, so it wins
        'the better of the two').
    max(1.0, 0, 0, 1.0) = 1.0 >= 0.8 -> CLEARS.

    Every other family/item_class stratum: target is neutral (no keyword
    signal, key mismatch) -> every responder's tpr=0 there; nontarget never
    gets flagged for that family either (ZC1/ZC3-keyword see no signal;
    ZC2/ZC3-base_rate only ever flag 'boundary', never this family) ->
    fpr=0 -> j=0 everywhere -> does NOT clear."""

    @staticmethod
    def _bank(*, boundary_signal: bool):
        items = []
        for item_class in zc.ITEM_CLASSES:
            for fam in zc.FAMILIES:
                if fam == "boundary" and boundary_signal:
                    text = "def compute_bound(values, window):\n    return values[:-1]\n"
                    keys = ["off by one"]
                else:
                    text = "def process_alpha(x):\n    return x\n"
                    keys = ["unmatched-key-xyz"]
                items.append({"item_id": f"{item_class}-{fam}", "item_class": item_class,
                              "defect_class": fam, "defect_keys": keys, "text": text})
            items.append({"item_id": f"{item_class}-clean", "item_class": item_class,
                          "defect_class": "clean", "defect_keys": [],
                          "text": "def process_alpha(x):\n    return x\n"})
        return items

    def test_boundary_strata_clear_others_do_not(self):
        result = zc.zc_gate(self._bank(boundary_signal=True))
        assert result["locks"] is False
        cleared_keys = {(c["family"], c["item_class"]) for c in result["cleared"]}
        assert cleared_keys == {("boundary", zc.MF), ("boundary", zc.SF)}
        for c in result["cleared"]:
            assert c["j"] == pytest.approx(1.0)
        # every non-boundary stratum: max J across all four registered
        # responders is exactly 0.0 (no signal reaches them from any side).
        for fam in zc.FAMILIES:
            if fam == "boundary":
                continue
            for item_class in zc.ITEM_CLASSES:
                row = result["results"][(fam, item_class)]
                assert max(v["j"] for v in row.values()) == 0.0, (fam, item_class, row)

    def test_fully_neutral_bank_locks(self):
        result = zc.zc_gate(self._bank(boundary_signal=False))
        assert result["cleared"] == []
        assert result["locks"] is True

    def test_gate_reports_source_and_threshold(self):
        result = zc.zc_gate(self._bank(boundary_signal=True), threshold=0.9)
        assert result["threshold"] == 0.9
        for c in result["cleared"]:
            assert c["source"] in ("zc1_verdict", "zc1_keyed", "zc2_verdict", "zc3_published")
