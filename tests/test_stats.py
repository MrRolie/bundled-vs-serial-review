"""test_stats.py — the graduated bootstrap/Holm primitives.

Plain pytest over `stats.py` (`test_answer_parser.py`'s style carried).

The build-step directionality check (§9, registered) lives in
`test_bootstrap_delta_reports_one_sided_p_not_the_parents_two_sided_formula`:
a fixed dataset whose `p_one_sided` was computed ONCE against this exact
implementation (deterministic RNG, so re-running reproduces it bit-for-bit)
and is asserted as a HARDCODED literal — the golden-master convention. The
dataset is chosen so `le0` (the underlying one-sided fraction) sits well
inside (0, 0.5): only there does the parent's literal two-sided formula
(`2 * min(le0, ge0)`) produce a VISIBLY DIFFERENT number from the one-sided
read (an extreme-separation dataset would drive both toward the same
floored value and the test would pass even if the code silently reverted
to computing the parent's formula — the exact failure mode this test
exists to catch).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "analysis"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from stats import bootstrap_contrast, bootstrap_delta, bootstrap_interaction, holm  # noqa: E402


# --------------------------------------------------------------- point estimate
def test_bootstrap_delta_point_estimate_is_the_plain_pooled_difference():
    """delta = pooled(hi) - pooled(lo), unaffected by resampling (a sanity
    check independent of any RNG behaviour)."""
    hi = [(2, 3), (3, 3)]   # pooled 5/6
    lo = [(1, 3), (1, 3)]   # pooled 2/6
    r = bootstrap_delta(hi, lo)
    assert r["delta"] == pytest.approx(5 / 6 - 2 / 6)


def test_bootstrap_interaction_point_estimate_matches_the_registered_formula():
    """H-B3 = [catch_S - catch_P]_haiku - [catch_S - catch_P]_opus (§11.1).
    The point estimate is additive regardless of shared vs. independent
    draws (only the CI/variance differ, tested below) -- this pins the
    SIGN and TERM ORDER: (S_h - P_h) - (S_o - P_o), never e.g. (P_h - S_h)
    or a swapped haiku/opus role."""
    s_h = [(3, 3), (2, 3)]
    p_h = [(1, 3), (1, 3)]
    s_o = [(2, 3), (2, 3)]
    p_o = [(2, 3), (2, 3)]
    r = bootstrap_interaction(s_h, p_h, s_o, p_o)
    expected = (5 / 6 - 2 / 6) - (4 / 6 - 4 / 6)
    assert r["delta"] == pytest.approx(expected)


# ------------------------------------------------------- shared item-index draw
def test_bootstrap_interaction_uses_one_shared_draw_across_all_four_legs():
    """The load-bearing structural property (§4.4/§11.1: H-B3's haiku and
    opus legs review the SAME C44 items -- `referee_sim.hb3_interaction_dist`
    draws ONE item-index resample for all four arrays). Constructed so the
    per-item interaction contribution (a_i - b_i, where a_i = s_h[i]/n -
    p_h[i]/n and b_i = s_o[i]/n - p_o[i]/n) is the SAME CONSTANT for every
    item (a_i - b_i == 1/3 for all i here) despite a_i and b_i each varying
    across items. Under a SHARED draw, every bootstrap replicate reduces to
    exactly that constant (pooling a constant over any nonempty multiset of
    items reproduces the constant) -- a near-zero-width CI. Under
    INDEPENDENT per-leg draws, mismatched item indices between the haiku
    and opus legs would generally NOT cancel to the constant, and the CI
    would have real width. This is the exact bug a naive "call the two-arm
    delta twice and subtract" implementation would introduce (flagged in
    review): it would resample haiku's items and opus's items
    independently, corrupting the shared-item-pool contract invisibly."""
    n = 3
    s_h = [1, 2, 3, 2]
    p_h = [0, 0, 0, 0]
    s_o = [0, 1, 2, 1]     # s_o[i] = s_h[i] - 1 for every i, n unchanged
    p_o = [0, 0, 0, 0]
    r = bootstrap_interaction(
        [(c, n) for c in s_h], [(c, n) for c in p_h],
        [(c, n) for c in s_o], [(c, n) for c in p_o],
    )
    assert r["delta"] == pytest.approx(1 / 3)
    width = r["ci95"][1] - r["ci95"][0]
    assert width < 1e-9, (
        f"CI width {width} is not near-zero; the shared item-index draw "
        "invariant is not holding (an independent-per-leg draw would mix "
        "items across the haiku/opus legs and break the pointwise-constant "
        "construction)"
    )


# --------------------------------------------------------- misalignment refusal
def test_bootstrap_contrast_refuses_mismatched_item_counts_across_terms():
    """A silent join mismatch would pair item i at one tier/arm with item j
    at another -- refused loudly (SystemExit, mirroring the parent
    `bootstrap_delta`'s own misalignment refusal), not
    silently truncated or zero-padded."""
    with pytest.raises(SystemExit):
        bootstrap_contrast([(1.0, [(1, 3), (2, 3)]), (-1.0, [(1, 3)])])


def test_bootstrap_contrast_refuses_no_terms():
    with pytest.raises(SystemExit):
        bootstrap_contrast([])


# --------------------------------------------------- one-sided directionality
def test_bootstrap_delta_reports_one_sided_p_not_the_parents_two_sided_formula():
    """The registered §9/§11.1 directionality check, as a golden vector.
    `hi`/`lo` are chosen (6 items, r=3 each) so the underlying one-sided
    fraction sits inside (0, 0.5), where the parent's literal
    `min(1, 2*min(le0, ge0))` formula gives a NUMBER TWICE AS LARGE as the
    registered one-sided read -- exactly the divergence an unwary
    graduation (inheriting the parent's two-sided line unchanged)
    would produce. Every figure below was computed ONCE against this exact
    implementation (seed=1512, n_boot=10,000, deterministic) and is
    asserted bit-for-bit; a later change to the resampling mechanics
    (a "fix" that reorders draws, changes the RNG call shape, or reverts
    to the two-sided formula) would change these numbers and trip this
    test."""
    hi = [(2, 3), (2, 3), (1, 3), (2, 3), (3, 3), (1, 3)]
    lo = [(1, 3), (1, 3), (2, 3), (1, 3), (1, 3), (2, 3)]
    r = bootstrap_delta(hi, lo)

    assert r["delta"] == pytest.approx(0.16666666666666674)
    assert r["ci95"] == pytest.approx((-0.11111111111111116, 0.4444444444444445))
    assert r["ci90"] == pytest.approx((-0.11111111111111116, 0.3888888888888889))
    assert r["p_one_sided"] == pytest.approx(0.1844)
    assert r["p_two_sided_sensitivity"] == pytest.approx(0.3688)

    # The discriminating assertion: the registered one-sided read is HALF
    # the parent's two-sided sensitivity formula here, never equal to it --
    # a silent revert to the parent's formula would make this fail.
    assert r["p_two_sided_sensitivity"] == pytest.approx(2 * r["p_one_sided"])
    assert r["p_one_sided"] != r["p_two_sided_sensitivity"]


def test_p_one_sided_is_floored_never_exactly_zero():
    """§9/referee_sim's floor convention: a 10k-resample Monte Carlo
    cannot distinguish "impossible" from "one in ten thousand" -- an
    extreme, unambiguous separation still reports `1/n_boot`, never a bare
    0.0 that would misread as certainty."""
    hi = [(3, 3)] * 8   # every trial a catch
    lo = [(0, 3)] * 8   # every trial a miss
    r = bootstrap_delta(hi, lo, n_boot=5_000)
    assert r["p_one_sided"] == pytest.approx(1 / 5_000)


# ------------------------------------------------------------------------ holm
def test_holm_voided_member_keeps_its_slot_and_never_fires():
    """§11.1: "a voided member keeps its slot" -- m stays the FULL family
    size even though one member is None, and the None member never fires."""
    fires = holm({"H-B1": 0.01, "H-B2": None, "H-B3": 0.2})
    assert fires == {"H-B1": True, "H-B2": False, "H-B3": False}


def test_holm_sequential_stepdown_stops_at_first_failure():
    """Classical Holm: once a sorted p-value fails its step's threshold,
    every subsequent (larger) p-value also fails, regardless of its OWN
    nominal threshold being laxer."""
    # alpha=0.05, m=3: thresholds are 0.0167, 0.025, 0.05 in step order.
    fires = holm({"A": 0.01, "B": 0.03, "C": 0.04}, alpha=0.05)
    assert fires["A"] is True          # 0.01 <= 0.05/3
    assert fires["B"] is False         # 0.03 > 0.05/2 -- stop
    assert fires["C"] is False         # never reached


def test_holm_all_fire_when_every_p_clears_its_step():
    fires = holm({"A": 0.001, "B": 0.01, "C": 0.02}, alpha=0.05)
    assert fires == {"A": True, "B": True, "C": True}
