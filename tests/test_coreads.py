"""Unit vectors for the corrected-pass co-reads (corrected-pass amendment, rule 4):
V2 P-maximal key scope and V3 label-respecting punitive, each pinned in
its registered DIRECTION (V2 only adds catches / moves FA→HIT-ALT; V3 only
removes permissive-route recoveries), plus the legacy NONE-scope keying fix.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "analysis"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from coreads import (  # noqa: E402
    _key,
    flag_verdict,
    none_scope_rows,
    v2_p_maximal_rows,
    v3_label_respecting_rows,
)

T = "claude-haiku-4-5-20251001"
ITEMS = {"sf-units-01": {"id": "sf-units-01", "defect_keys": ["timeout_ms", "seconds"]},
         "clean-sf-02": {"id": "clean-sf-02", "defect_keys": []},
         "mf-sign-02": {"id": "mf-sign-02", "defect_keys": ["-="]}}


def _row(**kw):
    base = {"tier": T, "arm": "P", "item": "sf-units-01", "rep": 0, "family": "units",
            "role": "target", "status": "NON-CATCH", "hit": False, "route": "strict-parsed",
            "allowed_families": [], "parser_strict_status": "PARSED",
            "parser_loose_status": "PARSED"}
    base.update(kw)
    return base


class TestV2PMaximal:
    BUNDLE = ("```\nQ-units: FLAG — worker_health.py compares elapsed against the timeout\n```\n"
              "```\nQ-sign: NONE — fine\n```\n"
              "Summary: elapsed is in seconds while timeout_ms is milliseconds.")

    def test_flag_without_block_key_becomes_catch_from_bundle(self):
        r = _row()   # mechanical FLAG whose block lacks the keys; keys sit in the summary
        texts = {_key(r): self.BUNDLE}
        out, n = v2_p_maximal_rows([r], texts, ITEMS)
        assert n == 1 and out[0]["status"] == "CATCH" and out[0]["hit"] is True
        assert r["status"] == "NON-CATCH"            # input untouched

    def test_none_verdict_never_becomes_catch(self):
        bundle = "```\nQ-units: NONE — all consistent\n```\nseconds vs timeout_ms noted elsewhere"
        r = _row()
        out, n = v2_p_maximal_rows([r], {_key(r): bundle}, ITEMS)
        assert n == 0 and out[0]["status"] == "NON-CATCH"

    def test_adjudicated_flag_uses_lane_verdict(self):
        r = _row(route="permissive-present", parser_strict_status="MISSING",
                 parser_loose_status="MISSING",
                 adjudicated={"adj_id": "adj-2001", "verdict": "FLAG", "lane": "current"})
        bundle = "## Q-units\nFLAG — compares elapsed to the timeout\n## Q-sign\nNONE\nnote: timeout_ms is ms"
        out, n = v2_p_maximal_rows([r], {_key(r): bundle}, ITEMS)
        assert n == 1 and out[0]["status"] == "CATCH"

    def test_off_family_fa_to_hit_alt_only_when_allowed(self):
        fa = _row(role="off_family", family="sign", status="FA", allowed_families=["sign"])
        fa.pop("hit")
        bundle = "```\nQ-sign: FLAG — wrong direction\n```\n... the comparison uses timeout_ms"
        out, n = v2_p_maximal_rows([fa], {_key(fa): bundle}, ITEMS)
        assert n == 1 and out[0]["status"] == "HIT-ALT"
        fa2 = dict(fa, allowed_families=[])
        out2, n2 = v2_p_maximal_rows([fa2], {_key(fa2): bundle}, ITEMS)
        assert out2[0]["status"] == "FA" and out2[0]["key_matched_wrong_family"] is True and n2 == 1

    def test_s_and_sq_rows_untouched(self):
        r = _row(arm="S")
        out, n = v2_p_maximal_rows([r], {_key(r): self.BUNDLE}, ITEMS)
        assert n == 0 and out[0] == r

    def test_clean_item_has_no_keys_so_nothing_moves(self):
        r = _row(item="clean-sf-02", role="clean", status="FA")
        r.pop("hit")
        bundle = "```\nQ-units: FLAG — something\n```"
        out, n = v2_p_maximal_rows([r], {_key(r): bundle}, ITEMS)
        assert n == 0 and out[0]["status"] == "FA"


class TestV3LabelRespecting:
    def test_unlabeled_permissive_target_catch_is_removed(self):
        r = _row(arm="Sq", status="CATCH", hit=True, route="permissive-present",
                 adjudicated={"adj_id": "adj-2100", "verdict": "FLAG", "lane": "current"})
        turn = "FLAG — irrigation_scheduler.py, the sign is inverted (-=)."
        out, n = v3_label_respecting_rows([r], {_key(r): turn})
        assert n == 1 and out[0]["status"] == "NON-CATCH" and out[0]["hit"] is False

    def test_wrong_family_label_counts_as_unlabeled(self):
        r = _row(arm="S", role="clean", item="clean-sf-02", status="FA", route="permissive-present")
        r.pop("hit")
        turn = "Q-comparison: NO-DEFECT-comparison\nall comparisons fine"
        out, n = v3_label_respecting_rows([r], {_key(r): turn})
        assert n == 1 and out[0]["status"] == "SILENT"

    def test_labeled_permissive_row_kept(self):
        r = _row(arm="S", status="CATCH", hit=True, route="permissive-present")
        turn = "# Q-units\nFLAG — elapsed seconds vs timeout_ms"
        out, n = v3_label_respecting_rows([r], {_key(r): turn})
        assert n == 0 and out[0]["status"] == "CATCH"

    def test_p_rows_and_other_routes_untouched(self):
        p = _row(arm="P", status="CATCH", hit=True, route="permissive-present")
        s = _row(arm="S", status="CATCH", hit=True, route="loose-parsed")
        out, n = v3_label_respecting_rows([p, s], {_key(p): "FLAG — x", _key(s): "FLAG — y"})
        assert n == 0 and out == [p, s]

    def test_already_silent_unlabeled_row_not_counted(self):
        r = _row(arm="S", role="off_family", family="sign", status="SILENT",
                 route="permissive-present")
        r.pop("hit")
        out, n = v3_label_respecting_rows([r], {_key(r): "nothing labeled"})
        assert n == 0 and out[0]["status"] == "SILENT"


class TestLegacyAndHelpers:
    def test_none_scope_reads_the_rows_own_family_text(self):
        # two S rows of one item×rep, different families — the fixed keying
        # reads each turn, not the last-loaded one
        a = _row(arm="S", family="units", role="off_family", status="SILENT",
                 parser_strict_status="MISSING", route="missing")
        b = _row(arm="S", family="sign", role="off_family", status="SILENT",
                 parser_strict_status="MISSING", route="missing")
        for r in (a, b):
            r.pop("hit")
        texts = {_key(a): "no defect in units (NO-DEFECT-units)", _key(b): "hmm"}
        out, n = none_scope_rows([a, b], texts)
        assert n == 1 and out[0]["status"] == "NO-FLAG" and out[1]["status"] == "SILENT"

    def test_flag_verdict_prefers_lane(self):
        r = _row(adjudicated={"adj_id": "adj-2001", "verdict": "NONE", "lane": "retained"})
        assert flag_verdict(r, "```\nQ-units: FLAG — x\n```") == "NONE"
        assert flag_verdict(_row(), "```\nQ-units: FLAG — x\n```") == "FLAG"
        assert flag_verdict(_row(), "prose only") is None
