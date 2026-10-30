"""referee_sim.py — pre-lock referee simulation for the registration's
§11.5 / §11.4.

Independently checks (never edits) the draft's PLANNING arithmetic at
`registration/preregistration.md`:
  - §11.5 CI half-widths and Holm-m=4 power for H-B1 / H-B2 / H-B3.
  - §11.2 C-B-TTFLAT reach probability (Delta_opus5 CI subset of [-0.20,+0.20]
    under a true zero effect) at r=3, r=2 (rev1), and r=2/3/4 at the 90% CI
    convention (rev2).
  - §11.4 FA-rate-difference precision on 8 clean clusters (4 mf + 4 sf).
  - REV 2 (prereg commit fa4cf1e): the C44 allocation (36 defective + 8
    clean common pool) -- see the "REV 2" section below.

Method: Monte-Carlo simulation of the REGISTERED estimator — item-stratified
cluster bootstrap, cluster = item (graduating the `bootstrap_delta` /
`holm` shape of an earlier study's endpoint script: one-sided bootstrap
p = fraction of draws <= 0; Holm step-down compares sorted p-values to
alpha/(m-step)). This is a NESTED Monte Carlo: for each of N_SIM simulated
datasets (drawn from a specified true data-generating process), we run an
N_BOOT-resample item-cluster bootstrap to get that dataset's CI / p-value,
then average/aggregate over the N_SIM outer reps.

REPRODUCIBILITY FIX (this revision): every individually-reported number is
now drawn from its OWN content-addressed RNG stream, keyed by a descriptive
label via `_reseed(label)` — NOT by shared advancing global state. This
replaces an earlier design (module-global `rng`, advanced continuously
across every call in execution order) that had a real, CONFIRMED bug: the
locked prereg text (§11.5) quotes commit 6b83068's rev-1 numbers verbatim
(H-B3 power 0.36/0.55, TTFLAT reach 0.513/0.189) as "baseline of record,"
but a LATER commit (145ce82) that only ADDED an H-B2 power sweep to
task2_power() silently changed task3_ttflat_reach()'s numbers too (0.513 ->
0.5205, 0.189 -> 0.1995) even though task3's own code never changed --
because both drew from one continuously-advancing global stream, and
task2's extra sweep consumed more draws before task3 ran. Content-addressed
per-label seeding makes every reported number invariant to unrelated edits
anywhere else in the file, present or future: computing (or not computing)
some other quantity can never perturb this one.

DISCLOSED modeling choices (apply to rev 1 and rev 2 alike):

  1. Registered: 10k bootstrap resamples PER DATASET. Run here at the FULL
     registered N_BOOT=10,000, with N_SIM=2,000 outer Monte-Carlo reps per
     named quantity (tightens the outer Monte-Carlo error on the reported
     power/probability figures; runtime is cheap enough that no reduction
     was needed).
  2. Item-difficulty heterogeneity: a shared per-item random effect on the
     PROBABILITY scale (not logit), e_i ~ Normal(0, sigma_item), SD chosen
     at 0.20 (midpoint of the registered 0.15-0.25 range). The same e_i is
     added to both arms' true rate for that item (paired design: a hard
     item is hard in both arms), which is what makes the paired/clustered
     bootstrap narrower than an unpaired two-sample bootstrap would be.
  3. H-B3 (tier interaction): the haiku-leg and opus-leg are two SEPARATE
     tiers reviewing the SAME common-pool items, so the simulation gives
     them a SHARED item-difficulty draw e_i (same physical items =>
     correlated difficulty across tiers) and resamples items ONCE per
     bootstrap replicate, applying that draw to both legs simultaneously.
     This is the realistic-correlation assumption; disclosed, not
     registered.
  4. Holm-power joint scenario: the Holm family has m=4 members (H-B1,
     H-B2, H-B3, H-B4). Powering one focal member requires assuming
     SOMETHING about the other three. We hold the three non-focal members
     at a TRUE NULL (delta=0) — a conservative floor on genuine Holm power
     (real co-occurring effects elsewhere could only raise power further
     via the sequential step-down; Holm is uniformly at least as powerful
     as Bonferroni-alpha/m for any single member; verified analytically:
     P(a null one-sided p < alpha/4) ~= 1.25%, so the nulls essentially
     never unlock a laxer Holm step, and focal power sits ~= its
     Bonferroni-alpha/m floor). H-B1 and H-B4 are treated as approximately
     independent draws (separate item-effect realizations) for
     tractability, though both would in reality ride the same haiku bank;
     disclosed, not registered.
  5. FA precision (Task 4): no item-level heterogeneity is modeled for the
     4-item mf/sf classes — at these low base rates (0.02-0.10) with only 4
     clusters, between-item heterogeneity is a second-order detail relative
     to the raw small-n binomial noise that already dominates. See the
     task4_fa_precision docstring for a degenerate-CI artifact caught in
     review and how it's reported (median/p10/p90 half-width, the
     degenerate-dataset fraction, and the two numbers that actually answer
     "can the bound be separated").
  6. §11.1 states "ALL members directional," which the one-sided p-value
     (fraction of bootstrap draws <= 0) matches directly. The PARENT file
     this study's code graduates from (an earlier study's endpoints) instead computes
     a two-sided p for its own (two-sided) Holm family. Primary power reads
     here use the one-sided convention per §11.1; a two-sided sensitivity
     sweep is reported alongside for H-B1/H-B3 (rev 1 only) in case the
     graduated analysis code inherits the parent's two-sided line unchanged.
  7. Task-3/rev2-TTFLAT reach probabilities are computed at p_base=0.5,
     well inside the 0.85/0.15 guard band — i.e. conditional on "the opus
     guards are silent," matching §11.2's own framing.

REV 2 (prereg commit fa4cf1e, rev 2.1): common pool C44 = 36 defective + 8
clean (both H-B3 legs over the SAME 36 items, §4.4); opus r=3 registered /
r=2 floor / r=4 flagged lock option (~+$130, §4.4); H-B1/H-B4 UNCHANGED
(haiku, <=60 surviving items x r3); the C-B-TTFLAT band read moves from a
95% CI to a 90% CI (TOST at the conventional alpha=0.05, §11.2) at the same
+/-0.20 band. Same modeling choices as rev 1 throughout. Rev 1's numbers are
QUOTED VERBATIM in the locked prereg text (§11.5) as "baseline of record" —
run with `--rev2-only` to compute/merge ONLY the rev-2 block into the
existing results JSON without recomputing the rev1_* keys at all
(merge-never-shrink; and, per the content-addressed seeding above, a rev1
recompute would in any case reproduce bit-identical numbers, but
--rev2-only avoids even the appearance of touching quoted figures).

Run: `python analysis/referee_sim.py [--rev2-only] [--out PATH]`
Output (of record): data/design/referee-sim-results.json
"""
from __future__ import annotations

import argparse
import json
import time
import zlib
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "data" / "design" / "referee-sim-results.json"

SEED = 20260817           # referee-sim seed; distinct from the trial seed 1512
N_BOOT = 10_000            # per-dataset bootstrap resamples (registered value)
N_SIM = 2_000               # outer Monte-Carlo reps per named quantity
N_SIM_SENS = 500            # outer reps for secondary sensitivity sweeps only
ALPHA = 0.05
M_HOLM = 4
SIGMA_ITEM = 0.20          # item-difficulty random-effect SD, probability scale
EPS = 1e-3                 # clip guard for probabilities

rng = np.random.default_rng(SEED)  # reseeded per named quantity; see _reseed


def _reseed(label: str) -> None:
    """Reset the shared RNG to an INDEPENDENT stream keyed only by `label`
    (via a CRC32 digest folded in beside the module SEED) — content-
    addressed, not order-addressed. Call this once immediately before the
    N_SIM outer-rep loop for each individually-reported quantity. This is
    what makes every number in this file invariant to unrelated code
    elsewhere: adding, removing, or reordering some OTHER computation can
    never change this one's random draws (the bug this fixes: see module
    docstring)."""
    global rng
    rng = np.random.default_rng([SEED, zlib.crc32(label.encode())])


# --------------------------------------------------------------------------
# Core estimator: item-stratified cluster bootstrap (graduated from an earlier study)
# --------------------------------------------------------------------------

def gen_item_effects(n_items: int, sigma: float) -> np.ndarray:
    return rng.normal(0.0, sigma, size=n_items)


def gen_binom_counts(p: np.ndarray, r: int) -> np.ndarray:
    p = np.clip(p, EPS, 1 - EPS)
    return rng.binomial(r, p)


def cluster_bootstrap_delta_dist(succ_p: np.ndarray, succ_s: np.ndarray,
                                  r: int, n_items: int, n_boot: int) -> np.ndarray:
    idx = rng.integers(0, n_items, size=(n_boot, n_items))
    bp = succ_p[idx].sum(axis=1) / (n_items * r)
    bs = succ_s[idx].sum(axis=1) / (n_items * r)
    return bs - bp


def ci_halfwidth(dist: np.ndarray) -> tuple[float, float, float]:
    lo, hi = np.percentile(dist, [2.5, 97.5])
    return float(lo), float(hi), float((hi - lo) / 2.0)


def onesided_pboot(dist: np.ndarray) -> float:
    """One-sided bootstrap p for H1: delta > 0 (parent convention: fraction <= 0).
    This is the operationalization implied by §11.1's "ALL members
    directional" -- but the PARENT file computes its
    Holm inputs as p_two_sided = min(1, 2*min(le0, ge0)) for what it calls
    a two-sided family. If the graduated analysis code inherits that
    two-sided line unchanged rather than adapting it for directionality,
    every power number below is optimistic. See twosided_pboot + the
    *_twosided_sensitivity entries for the exposure this creates."""
    p = float((dist <= 0.0).mean())
    return max(p, 1.0 / len(dist))


def twosided_pboot(dist: np.ndarray) -> float:
    """The parent's literal p_two_sided = min(1, 2*min(le0, ge0)) -- sensitivity
    check only, disclosed above; NOT what §11.1 registers."""
    le0 = float((dist <= 0.0).mean())
    ge0 = float((dist >= 0.0).mean())
    p = min(1.0, 2 * min(le0, ge0))
    return max(p, 1.0 / len(dist))


def holm_reject(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    m = len(pvals)
    order = np.argsort(pvals)
    reject = np.zeros(m, dtype=bool)
    for rank, i in enumerate(order):
        thresh = alpha / (m - rank)
        if pvals[i] <= thresh:
            reject[i] = True
        else:
            break
    return reject


def gen_test_dist(n_items: int, r: int, p_base: float, delta: float,
                   n_boot: int = N_BOOT) -> np.ndarray:
    e = gen_item_effects(n_items, SIGMA_ITEM)
    p_p = p_base + e
    p_s = p_base + delta + e
    succ_p = gen_binom_counts(p_p, r)
    succ_s = gen_binom_counts(p_s, r)
    return cluster_bootstrap_delta_dist(succ_p, succ_s, r, n_items, n_boot)


def simulate_hb3_dataset(delta_haiku: float, delta_opus: float, opus_r: int,
                          p_base: float = 0.5, n_items: int = 24):
    """Shared item-effect draw across the haiku-leg (r=3) and the opus leg
    (opus_r), reflecting the same n_items physical items reviewed by both
    tiers. Returns per-item success counts for both legs."""
    e = gen_item_effects(n_items, SIGMA_ITEM)
    succ_p_h = gen_binom_counts(p_base + e, 3)
    succ_s_h = gen_binom_counts(p_base + delta_haiku + e, 3)
    succ_p_o = gen_binom_counts(p_base + e, opus_r)
    succ_s_o = gen_binom_counts(p_base + delta_opus + e, opus_r)
    return succ_p_h, succ_s_h, succ_p_o, succ_s_o


def hb3_interaction_dist(succ_p_h, succ_s_h, succ_p_o, succ_s_o,
                          opus_r: int, n_items: int = 24, n_boot: int = N_BOOT):
    idx = rng.integers(0, n_items, size=(n_boot, n_items))
    bp_h = succ_p_h[idx].sum(axis=1) / (n_items * 3)
    bs_h = succ_s_h[idx].sum(axis=1) / (n_items * 3)
    bp_o = succ_p_o[idx].sum(axis=1) / (n_items * opus_r)
    bs_o = succ_s_o[idx].sum(axis=1) / (n_items * opus_r)
    return (bs_h - bp_h) - (bs_o - bp_o)


# --------------------------------------------------------------------------
# Task 1: CI half-widths across p_true in {0.3, 0.5, 0.7}, delta = 0 (sizing)
# --------------------------------------------------------------------------

def task1_halfwidths() -> dict:
    results: dict = {}
    settings = [
        ("haiku_Delta_n60_r3", 60, 3),
        ("sonnet_Delta_n24_r3", 24, 3),
        ("opus_Delta_n24_r3", 24, 3),
        ("opus_Delta_n24_r2", 24, 2),
    ]
    for name, n_items, r in settings:
        hw_by_p = {}
        for p_true in (0.3, 0.5, 0.7):
            _reseed(f"task1:{name}:{p_true}")
            hws = []
            for _ in range(N_SIM):
                e = gen_item_effects(n_items, SIGMA_ITEM)
                succ_p = gen_binom_counts(p_true + e, r)
                succ_s = gen_binom_counts(p_true + e, r)  # delta = 0
                dist = cluster_bootstrap_delta_dist(succ_p, succ_s, r, n_items, N_BOOT)
                hws.append(ci_halfwidth(dist)[2])
            hw_by_p[str(p_true)] = float(np.mean(hws))
        results[name] = hw_by_p

    for opus_r, tag in ((3, "HB3_interaction_opusR3"), (2, "HB3_interaction_opusR2")):
        hw_by_p = {}
        for p_true in (0.3, 0.5, 0.7):
            _reseed(f"task1:{tag}:{p_true}")
            hws = []
            for _ in range(N_SIM):
                legs = simulate_hb3_dataset(0.0, 0.0, opus_r, p_base=p_true)
                dist = hb3_interaction_dist(*legs, opus_r=opus_r)
                hws.append(ci_halfwidth(dist)[2])
            hw_by_p[str(p_true)] = float(np.mean(hws))
        results[tag] = hw_by_p
    return results


# --------------------------------------------------------------------------
# Task 2: Power at the Holm m=4 operating point
#
# Family index: 0=H-B1 (haiku), 1=H-B2 (sonnet), 2=H-B3 (interaction),
# 3=H-B4 (haiku Sq-P, simulated as an independent draw on the same shape as
# H-B1 -- disclosed simplification, see module docstring point 4).
# --------------------------------------------------------------------------

def _family_pvalues(p_func, delta_hb1: float, delta_hb2: float,
                     delta_int_haiku: float, delta_int_opus: float,
                     delta_hb4: float, label: str) -> np.ndarray:
    _reseed(f"{label}:hb1")
    p_hb1 = p_func(gen_test_dist(60, 3, 0.5, delta_hb1))
    _reseed(f"{label}:hb2")
    p_hb2 = p_func(gen_test_dist(24, 3, 0.5, delta_hb2))
    _reseed(f"{label}:hb3")
    legs = simulate_hb3_dataset(delta_int_haiku, delta_int_opus, 3)
    p_hb3 = p_func(hb3_interaction_dist(*legs, opus_r=3))
    _reseed(f"{label}:hb4")
    p_hb4 = p_func(gen_test_dist(60, 3, 0.5, delta_hb4))
    return np.array([p_hb1, p_hb2, p_hb3, p_hb4])


def _power_sweep(p_func, focal: str, deltas: tuple[float, ...], n_sim: int,
                 sweep_label: str) -> dict:
    focal_idx = {"HB1": 0, "HB2": 1, "HB3": 2}[focal]
    out = {}
    for d in deltas:
        label = f"{sweep_label}:{focal}:{d}"
        rejects = []
        for i in range(n_sim):
            # each rep needs its own draw; reseed the FAMILY once per rep
            # (label includes the rep index) so every (sweep, delta, rep)
            # triple is independently content-addressed.
            rep_label = f"{label}:rep{i}"
            if focal == "HB1":
                pvals = _family_pvalues(p_func, d, 0.0, 0.0, 0.0, 0.0, rep_label)
            elif focal == "HB2":
                pvals = _family_pvalues(p_func, 0.0, d, 0.0, 0.0, 0.0, rep_label)
            else:  # HB3 -- haiku leg carries delta, opus leg flat
                pvals = _family_pvalues(p_func, 0.0, 0.0, d, 0.0, 0.0, rep_label)
            rejects.append(bool(holm_reject(pvals)[focal_idx]))
        out[str(d)] = float(np.mean(rejects))
    return out


def task2_power() -> dict:
    results: dict = {
        # primary reads: one-sided p, per §11.1 "ALL members directional"
        "HB1_onesided": _power_sweep(onesided_pboot, "HB1", (0.10, 0.15, 0.20), N_SIM, "task2:1s"),
        "HB2_onesided": _power_sweep(onesided_pboot, "HB2", (0.15, 0.20, 0.25), N_SIM, "task2:1s"),
        "HB3_onesided": _power_sweep(onesided_pboot, "HB3", (0.15, 0.20, 0.25), N_SIM, "task2:1s"),
        # sensitivity: the parent's literal two-sided p, in case the graduated
        # code inherits it unchanged instead of adapting for directionality
        "HB1_twosided_sensitivity": _power_sweep(twosided_pboot, "HB1", (0.10, 0.15, 0.20), N_SIM_SENS, "task2:2s"),
        "HB3_twosided_sensitivity": _power_sweep(twosided_pboot, "HB3", (0.15, 0.20, 0.25), N_SIM_SENS, "task2:2s"),
    }
    return results


# --------------------------------------------------------------------------
# Task 3: C-B-TTFLAT reach probability under a TRUE zero effect at opus
# (95% CI, rev-1 form)
# --------------------------------------------------------------------------

def task3_ttflat_reach() -> dict:
    results = {}
    for r in (3, 2):
        _reseed(f"task3:r{r}")
        n_items = 24
        inside = []
        for _ in range(N_SIM):
            e = gen_item_effects(n_items, SIGMA_ITEM)
            succ_p = gen_binom_counts(0.5 + e, r)
            succ_s = gen_binom_counts(0.5 + e, r)  # true delta = 0
            dist = cluster_bootstrap_delta_dist(succ_p, succ_s, r, n_items, N_BOOT)
            lo, hi, _ = ci_halfwidth(dist)
            inside.append(lo >= -0.20 and hi <= 0.20)
        results[f"r{r}"] = float(np.mean(inside))
    return results


# --------------------------------------------------------------------------
# Task 4: FA-rate-difference precision, 4-item classes (mf, sf identical
# under this model -- no class-specific heterogeneity assumed; disclosed).
#
# CAUGHT BY ADVISOR REVIEW: at n=4 items x r=3 and these low base rates, a
# large share of simulated datasets have ZERO successes in BOTH arms (e.g.
# P(both-arms-all-zero) ~= 0.62 at rate=0.02: (1-0.02)^3=0.941 chance a
# single item is zero-succ, 0.941^4=0.785 chance all 4 items in one arm are
# zero-succ, 0.785^2~=0.62 chance BOTH arms are). Every bootstrap resample
# of an all-zero dataset is exactly [0,0], so the naive MEAN half-width is
# a mixture of exact-zero and non-degenerate datasets and is not
# interpretable as "typical precision." Reported here instead: the fraction
# of degenerate datasets, and the median/10th/90th percentile half-width
# computed over ALL datasets (so the degenerate mass is visible, not
# averaged away) -- plus the two quantities that actually answer "can the
# bound be separated": under a TRUE zero difference, the fraction of
# datasets whose CI upper bound < 0.15 (correctly resolves in-bound); under
# a TRUE 0.20 gap (a genuine breach, 0.05 past the registered bound), the
# fraction whose CI lower bound > 0.15 (correctly resolves as a breach).
# --------------------------------------------------------------------------

def task4_fa_precision() -> dict:
    results = {}
    n_items, r = 4, 3
    breach_delta = 0.20
    for rate in (0.02, 0.05, 0.10):
        _reseed(f"task4:null:{rate}")
        hws, degenerate, resolved_inbound = [], [], []
        for _ in range(N_SIM):
            p_arm = np.full(n_items, rate)
            succ_p = gen_binom_counts(p_arm, r)
            succ_s = gen_binom_counts(p_arm, r)  # true diff = 0
            dist = cluster_bootstrap_delta_dist(succ_p, succ_s, r, n_items, N_BOOT)
            lo, hi, hw = ci_halfwidth(dist)
            hws.append(hw)
            degenerate.append(bool(succ_p.sum() == 0 and succ_s.sum() == 0))
            resolved_inbound.append(bool(hi < 0.15))

        _reseed(f"task4:breach:{rate}")
        breach_detect = []
        for _ in range(N_SIM):
            p_p = np.full(n_items, rate)
            p_s = np.full(n_items, min(rate + breach_delta, 1.0 - EPS))
            succ_p = gen_binom_counts(p_p, r)
            succ_s = gen_binom_counts(p_s, r)
            dist = cluster_bootstrap_delta_dist(succ_p, succ_s, r, n_items, N_BOOT)
            lo, _, _ = ci_halfwidth(dist)
            breach_detect.append(bool(lo > 0.15))

        hws = np.array(hws)
        results[str(rate)] = {
            "median_hw": float(np.median(hws)),
            "p10_hw": float(np.percentile(hws, 10)),
            "p90_hw": float(np.percentile(hws, 90)),
            "frac_degenerate_both_arms_zero": float(np.mean(degenerate)),
            "frac_resolved_inbound_true_delta0": float(np.mean(resolved_inbound)),
            "frac_correctly_flags_breach_true_delta0.20_over_bound": float(np.mean(breach_detect)),
        }
    return results


# ============================================================================
# REV 2 (prereg commit fa4cf1e, rev 2.1): common pool C44 = 36 defective + 8
# clean (both H-B3 legs over the same 36 items, §4.4); opus r=3 registered /
# r=2 floor / r=4 flagged lock option (≈+$130, §4.4); H-B1/H-B4 UNCHANGED
# (haiku, <=60 surviving items x r3); the C-B-TTFLAT band read moves from a
# 95% CI to a 90% CI (TOST at the conventional alpha=0.05, §11.2) at the same
# +/-0.20 band. Same modeling choices as rev 1 (item-effect SD=0.20, shared
# across arms and, for H-B3, across the haiku/opus legs on the same items;
# one-sided primary p, non-focal Holm members held at true null).
# ============================================================================

REV2_N_ITEMS = 36


def rev2_ci_halfwidths() -> dict:
    results: dict = {}
    settings = [
        ("sonnet_Delta_n36_r3", 36, 3),
        ("opus_Delta_n36_r3", 36, 3),
        ("opus_Delta_n36_r2", 36, 2),
        ("opus_Delta_n36_r4", 36, 4),  # extra: the lock-option rep count
    ]
    for name, n_items, r in settings:
        hw_by_p = {}
        for p_true in (0.3, 0.5, 0.7):
            _reseed(f"rev2:ci:{name}:{p_true}")
            hws = []
            for _ in range(N_SIM):
                e = gen_item_effects(n_items, SIGMA_ITEM)
                succ_p = gen_binom_counts(p_true + e, r)
                succ_s = gen_binom_counts(p_true + e, r)  # delta = 0 (sizing)
                dist = cluster_bootstrap_delta_dist(succ_p, succ_s, r, n_items, N_BOOT)
                hws.append(ci_halfwidth(dist)[2])
            hw_by_p[str(p_true)] = float(np.mean(hws))
        results[name] = hw_by_p

    for opus_r, tag in ((2, "HB3_interaction_n36_opusR2"),
                         (3, "HB3_interaction_n36_opusR3"),
                         (4, "HB3_interaction_n36_opusR4")):
        hw_by_p = {}
        for p_true in (0.3, 0.5, 0.7):
            _reseed(f"rev2:ci:{tag}:{p_true}")
            hws = []
            for _ in range(N_SIM):
                legs = simulate_hb3_dataset(0.0, 0.0, opus_r, p_base=p_true, n_items=36)
                dist = hb3_interaction_dist(*legs, opus_r=opus_r, n_items=36)
                hws.append(ci_halfwidth(dist)[2])
            hw_by_p[str(p_true)] = float(np.mean(hws))
        results[tag] = hw_by_p
    return results


def _family_pvalues_rev2(p_func, delta_hb1: float, delta_hb2: float,
                          delta_int_haiku: float, delta_int_opus: float,
                          delta_hb4: float, opus_r: int, label: str,
                          n_items_common: int = 36) -> np.ndarray:
    """Rev-2 joint Holm family: H-B2 and both H-B3 legs ride C44 (36 items);
    H-B1/H-B4 stay on the (unchanged) haiku shape (n=60, r=3)."""
    _reseed(f"{label}:hb1")
    p_hb1 = p_func(gen_test_dist(60, 3, 0.5, delta_hb1))
    _reseed(f"{label}:hb2")
    p_hb2 = p_func(gen_test_dist(n_items_common, 3, 0.5, delta_hb2))
    _reseed(f"{label}:hb3")
    legs = simulate_hb3_dataset(delta_int_haiku, delta_int_opus, opus_r,
                                 n_items=n_items_common)
    p_hb3 = p_func(hb3_interaction_dist(*legs, opus_r=opus_r, n_items=n_items_common))
    _reseed(f"{label}:hb4")
    p_hb4 = p_func(gen_test_dist(60, 3, 0.5, delta_hb4))
    return np.array([p_hb1, p_hb2, p_hb3, p_hb4])


def _power_sweep_rev2(p_func, focal: str, deltas: tuple[float, ...],
                       opus_r: int, n_sim: int, sweep_label: str) -> dict:
    focal_idx = {"HB2": 1, "HB3": 2}[focal]
    out = {}
    for d in deltas:
        label = f"{sweep_label}:{focal}:opusR{opus_r}:{d}"
        rejects = []
        for i in range(n_sim):
            rep_label = f"{label}:rep{i}"
            if focal == "HB2":
                pvals = _family_pvalues_rev2(p_func, 0.0, d, 0.0, 0.0, 0.0, opus_r, rep_label)
            else:  # HB3 -- haiku leg carries delta_int, opus leg flat
                pvals = _family_pvalues_rev2(p_func, 0.0, 0.0, d, 0.0, 0.0, opus_r, rep_label)
            rejects.append(bool(holm_reject(pvals)[focal_idx]))
        out[str(d)] = float(np.mean(rejects))
    return out


def rev2_power() -> dict:
    return {
        # H-B2's non-focal H-B3 slot uses the registered opus r=3.
        "HB2_onesided_r3": _power_sweep_rev2(onesided_pboot, "HB2", (0.15, 0.20, 0.25),
                                              opus_r=3, n_sim=N_SIM, sweep_label="rev2:pow"),
        "HB3_onesided_opusR3": _power_sweep_rev2(onesided_pboot, "HB3", (0.15, 0.20, 0.25),
                                                  opus_r=3, n_sim=N_SIM, sweep_label="rev2:pow"),
        "HB3_onesided_opusR4": _power_sweep_rev2(onesided_pboot, "HB3", (0.15, 0.20, 0.25),
                                                  opus_r=4, n_sim=N_SIM, sweep_label="rev2:pow"),
    }


def rev2_ttflat_reach_90ci() -> dict:
    """§11.2 rev 2: band read moved to the 90% CI (TOST @ alpha=0.05),
    same +/-0.20 band, now over C44's 36 items."""
    results = {}
    for r in (2, 3, 4):
        _reseed(f"rev2:ttflat:r{r}")
        n_items = 36
        inside = []
        for _ in range(N_SIM):
            e = gen_item_effects(n_items, SIGMA_ITEM)
            succ_p = gen_binom_counts(0.5 + e, r)
            succ_s = gen_binom_counts(0.5 + e, r)  # true delta = 0
            dist = cluster_bootstrap_delta_dist(succ_p, succ_s, r, n_items, N_BOOT)
            lo, hi = np.percentile(dist, [5.0, 95.0])  # 90% CI
            inside.append(bool(lo >= -0.20 and hi <= 0.20))
        results[f"r{r}"] = float(np.mean(inside))
    return results


# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rev2-only", action="store_true",
        help="Compute only the rev-2 (C44, 36-item) block and MERGE it into "
             "the existing results JSON, without recomputing the rev1_* "
             "keys -- those numbers are already quoted verbatim in the "
             "locked prereg text (§11.5) as the rev-1 baseline of record "
             "(merge-never-shrink). With the content-addressed reseeding "
             "above a full recompute would in any case reproduce them "
             "bit-identically, but --rev2-only avoids even the appearance "
             "of touching quoted figures.")
    parser.add_argument("--out", type=Path, default=None,
                        help="write here instead of the results file of record")
    args = parser.parse_args()
    global OUT_PATH
    if args.out is not None:
        OUT_PATH = args.out
    t0 = time.time()

    if args.rev2_only:
        if not OUT_PATH.exists():
            raise SystemExit(f"--rev2-only requires an existing {OUT_PATH} "
                              f"to merge into; none found.")
        out = json.loads(OUT_PATH.read_text())
    else:
        out = {
            "meta": {
                "seed": SEED, "n_boot": N_BOOT, "n_sim": N_SIM,
                "sigma_item": SIGMA_ITEM, "alpha": ALPHA, "m_holm": M_HOLM,
                "note": "nested Monte Carlo; N_BOOT=10,000 (full registered "
                        "per-dataset bootstrap count) x N_SIM=2,000 outer "
                        "reps; every named quantity independently "
                        "content-addressed-seeded (see _reseed)",
            },
            "task1_ci_halfwidths": task1_halfwidths(),
            "task2_holm_power": task2_power(),
            "task3_ttflat_reach_probability": task3_ttflat_reach(),
            "task4_fa_precision_halfwidth": task4_fa_precision(),
        }

    out["rev2"] = {
        "meta": {
            "prereg_commit": "fa4cf1e", "pool": "C44 (36 defective + 8 clean)",
            "seed": SEED, "n_boot": N_BOOT, "n_sim": N_SIM,
            "sigma_item": SIGMA_ITEM, "alpha": ALPHA, "m_holm": M_HOLM,
            "note": "H-B1/H-B4 unchanged (haiku n=60, r=3); H-B2 and both "
                    "H-B3 legs now ride C44's 36 items; opus r=3 registered "
                    "/ r=2 floor / r=4 flagged lock option; TTFLAT band read "
                    "now the 90% CI (TOST @ alpha=0.05), same +/-0.20 band.",
        },
        "ci_halfwidths_n36": rev2_ci_halfwidths(),
        "holm_power_n36": rev2_power(),
        "ttflat_reach_90ci_n36": rev2_ttflat_reach_90ci(),
    }
    out["rev2"]["meta"]["runtime_sec_rev2_block"] = round(time.time() - t0, 1)
    if not args.rev2_only:
        out["runtime_sec"] = round(time.time() - t0, 1)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["rev2"] if args.rev2_only else out, indent=2))


if __name__ == "__main__":
    main()
