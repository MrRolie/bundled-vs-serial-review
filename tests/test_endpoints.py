"""§11/§12 endpoints driver — cell enumeration, precedence, guards, pools."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "analysis"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import endpoints as ep  # noqa: E402


def test_cell_map_is_the_registered_partition():
    assert len(ep._CELL_MAP) == 25
    from collections import Counter
    counts = Counter(ep._CELL_MAP.values())
    assert counts == {"C-B1": 1, "C-B2": 3, "C-B3": 1, "C-B4": 4,
                      "C-B5": 9, "C-B6": 7}
    assert ep._CELL_MAP[("F", "F")] == "C-B1"
    assert ep._CELL_MAP[("R", "F")] == "C-B4"   # (R,F) lives in C-B4, not C-B6
    assert ep._CELL_MAP[("N", "R")] == "C-B6"


def test_member_state_precedence_v_g_r_f_n():
    boot_neg = {"ci95": (-0.5, -0.1)}
    boot_pos = {"ci95": (0.1, 0.5)}
    g_fired = {"fired": True, "arms": {"S": 0.9}}
    g_quiet = {"fired": False, "arms": {}}
    assert ep.member_state(boot_neg, True, g_fired, voided=True) == "V"
    assert ep.member_state(boot_neg, True, g_fired) == "G"       # G beats R and F
    assert ep.member_state(boot_neg, True, g_quiet) == "R"       # R beats F
    assert ep.member_state(boot_pos, True, g_quiet) == "F"
    assert ep.member_state(boot_pos, False, g_quiet) == "N"


def test_guard_fires_on_either_side():
    hi = [(9, 10)] * 5   # 0.9 > 0.85
    lo = [(1, 10)] * 5   # 0.1 < 0.15
    mid = [(5, 10)] * 5
    assert ep.guard_state({"S": hi, "P": mid})["fired"]
    assert ep.guard_state({"S": mid, "P": lo})["fired"]
    assert not ep.guard_state({"S": mid, "P": mid})["fired"]


def test_target_pairs_counts_and_refuses_missing_item():
    rows = [
        {"tier": "t", "arm": "S", "role": "target", "item": "a", "status": "CATCH"},
        {"tier": "t", "arm": "S", "role": "target", "item": "a", "status": "NON-CATCH"},
        {"tier": "t", "arm": "S", "role": "target", "item": "b", "status": "CATCH"},
    ]
    assert ep.target_pairs(rows, "t", "S", ["a", "b"]) == [(1, 2), (1, 1)]
    with pytest.raises(SystemExit, match="no target rows"):
        ep.target_pairs(rows, "t", "S", ["a", "b", "c"])


def test_clean_anyflag_unit_is_item_rep():
    rows = []
    for rep in (1, 2):
        for fam in ("boundary", "comparison"):
            rows.append({"tier": "t", "arm": "P", "role": "clean", "item": "cl-1",
                         "rep": rep, "family": fam,
                         "status": "FA" if (rep == 1 and fam == "boundary") else "NO-FLAG"})
    pairs = ep.clean_anyflag_pairs(rows, "t", "P", ["cl-1"])
    assert pairs == [(1, 2)]  # rep 1 flagged (one FA among its rows), rep 2 not


def test_off_family_pairs_excludes_allowed_families_from_denominator():
    rows = [
        {"tier": "t", "arm": "S", "role": "off_family", "item": "d", "rep": 1,
         "family": "sign", "status": "FA", "allowed_families": ["units"],
         "key_matched_wrong_family": True},
        {"tier": "t", "arm": "S", "role": "off_family", "item": "d", "rep": 1,
         "family": "units", "status": "HIT-ALT", "allowed_families": ["units"]},
        {"tier": "t", "arm": "S", "role": "off_family", "item": "d", "rep": 1,
         "family": "comparison", "status": "SILENT", "allowed_families": ["units"]},
    ]
    fa_pairs = ep.off_family_pairs(rows, "t", "S", ["d"], numerator="fa")
    assert fa_pairs == [(1, 2)]  # units row out of denominator; SILENT stays in
    km = ep.off_family_pairs(rows, "t", "S", ["d"], numerator="kmwf")
    assert km == [(1, 2)]


def test_holm_none_slot_kept():
    from stats import holm
    fires = holm({"H-B1": 0.001, "H-B2": None, "H-B3": 0.02, "H-B4": 0.04})
    # m=4 (the None slot is KEPT): 0.001 <= .05/4 fires; 0.02 > .05/3 stops —
    # with m=3 (slot dropped) 0.02 <= .05/2 WOULD fire, so this vector pins
    # the slot-kept behavior specifically
    assert fires == {"H-B1": True, "H-B2": False, "H-B3": False, "H-B4": False}
