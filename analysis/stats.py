"""stats.py — the graduated bootstrap/Holm primitives.

Analysis-helper file: never trial-time, no regime hash, freely fixable.

**Graduated from** an earlier study's endpoint script (`bootstrap_delta`
+ `holm`), generalized and re-derived for this study, NOT imported (the
parent's own version stays untouched — "the parent is never edited"). Two semantic
deltas from the parent, both registered requirements, both load-bearing:

1. **Directionality (§11.1 "ALL members directional").** The parent computes
   ONE p-value, `p_two_sided = min(1, 2*min(le0, ge0))`, built for its own
   two-sided Holm family. This study's Holm family (H-B1..H-B4) is one-sided by
   registration — the referee simulation's own build-step note (§9,
   `referee_sim.onesided_pboot`) flags this exact fork as the thing an
   unwary graduation could get wrong: inheriting the parent's two-sided line
   unchanged would make every H-Bn p-value exactly 2x too large relative to
   the registered one-sided convention, which is optimistic in the WRONG
   direction for a Holm step-down (a p that is too generous under-detects,
   but a silently-doubled p under a one-sided registration is the OPPOSITE
   error — it makes firing HARDER than the registered test requires, not
   easier, so the failure mode this graduation must not reproduce is a
   quietly under-powered study, not an inflated one). `p_one_sided` here is
   `max(fraction(draws <= 0), 1/n_boot)` — the floor (never report an exact
   `p=0`, since a 10k-resample Monte Carlo cannot distinguish "impossible"
   from "one in ten thousand") is carried from `referee_sim.py`'s
   convention; the un-floored parent does not floor its p at all — disclosed
   here rather than silently adopted. `p_two_sided_sensitivity` is ALSO
   returned (the parent's exact formula) as a robustness sensitivity co-read
   only — never the primary read, never fed to `holm()` by this module.
2. **The tier-interaction estimator needs a SHARED item draw across four
   count arrays, not two.** H-B3 is `[catch_S - catch_P]_haiku -
   [catch_S - catch_P]_opus`, both legs over the SAME C44 items (§4.4,
   §11.1) — the referee sim's `hb3_interaction_dist` draws ONE item-index
   resample and applies it to all four (S_haiku, P_haiku, S_opus, P_opus)
   arrays together, because the two tiers reviewing the same physical items
   are correlated draws, not independent ones (a shared per-item difficulty
   effect, disclosed in the sim as the realistic-correlation assumption).
   Calling a plain two-arm delta function twice (once per tier) and
   subtracting the two results would resample haiku's items and opus's
   items INDEPENDENTLY, inflating the interaction's variance relative to
   every §11.5 number of record (H-B3 HW ~= 0.17 at r3, Holm power 0.51 @
   delta_int=0.20) — those were computed under the shared draw. `holm()`
   itself needed NO change (it is already a generic step-down over named
   p-values; the H-B1..H-B4 naming is a CALLER concern) beyond dropping
   the parent's fixed m=3 in favour of `len(p_values)`, which the parent's
   own code already does (`m = len(p_values)` — the docstring's "m=3" was
   descriptive of the parent study's family, not a hardcoded constant).

The unifying primitive is `bootstrap_contrast`: a LINEAR COMBINATION of
per-item (successes, n) pair arrays under ONE shared item-index draw. A
plain two-arm delta (`bootstrap_delta`, used for H-B1/H-B2/H-B4 and every
§11.3 descriptive CI-only contrast) is the two-term case
`[(+1, hi_pairs), (-1, lo_pairs)]`; the interaction (`bootstrap_interaction`,
H-B3) is the four-term case `[(+1, S_h), (-1, P_h), (-1, S_o), (+1, P_o)]`.
Every term's per-item pairs must be aligned item-for-item (position i in
every term's list is the SAME physical item) — misalignment is refused
loudly (SystemExit, mirroring the parent's own misalignment refusal)
because a silent join mismatch would pair item i at one tier/arm with item
j at another, corrupting the "same C44 pool" registration invisibly.

**The 90% CI variant** (§11.2's TOST band read, pre-lock A-11/D-14: the
90% convention narrows the interval ~16% versus the parent's bare 95% and
is what the referee re-simulation's C-B-TTFLAT reach numbers (0.87 r3 /
0.68 r2 / 0.95 r4) are computed against) rides EVERY returned dict as
`ci90` alongside the 95% `ci95` the parent always returned — both are
always computed (cheap: same draws, different percentiles) so a caller
never has to remember which endpoint needs which band. §12's R/N states
read the UNADJUSTED two-sided 95% CI (`ci95`, D-6); §11.2's band cells
read `ci90`; §11.1's Holm firing reads `p_one_sided` only.
"""
from __future__ import annotations

import sys
from typing import Mapping, Sequence

import numpy as np

SEED = 1512
N_BOOT = 10_000
ALPHA = 0.05

PctPair = tuple[int, int]  # (successes, n) for one item


def _per_item_arrays(terms: Sequence[tuple[float, Sequence[PctPair]]]) -> tuple[
    list[float], list[np.ndarray], list[np.ndarray]
]:
    """Validate and unpack `terms` into (signs, per-term successes arrays,
    per-term n arrays), refusing on any length mismatch across terms — the
    shared-draw contract requires every term to name the SAME n_items in
    the SAME order (position i is one physical item across every term)."""
    if not terms:
        raise SystemExit("bootstrap_contrast: no terms supplied; refusing a vacuous contrast")
    lengths = {len(pairs) for _, pairs in terms}
    if len(lengths) != 1:
        raise SystemExit(
            f"bootstrap_contrast: terms carry mismatched item counts {sorted(lengths)}; "
            "every term must align item-for-item (position i is the SAME physical item "
            "across every term) — a silent join mismatch would corrupt the shared C44 pool"
        )
    n_items = lengths.pop()
    if n_items == 0:
        raise SystemExit("bootstrap_contrast: zero items in every term; refusing")
    signs = [float(s) for s, _ in terms]
    succ = [np.array([c for c, _ in pairs], dtype=float) for _, pairs in terms]
    ns = [np.array([n for _, n in pairs], dtype=float) for _, pairs in terms]
    return signs, succ, ns


def bootstrap_contrast(
    terms: Sequence[tuple[float, Sequence[PctPair]]],
    *, n_boot: int = N_BOOT, seed: int = SEED,
) -> dict:
    """Item-stratified (cluster) bootstrap of `sum(sign * pooled_rate(term))`
    over ONE shared item-index draw per replicate (§4.4/§11.1's "same C44
    subset" requirement — see module docstring point 2). `terms` is a
    sequence of `(sign, per_item_pairs)`; `per_item_pairs` is
    `[(successes, n), ...]` one entry per item, aligned by position across
    every term.

    Returns `delta` (point estimate), `ci95`/`ci90` (two-sided percentile
    bands on the SAME draws), `p_one_sided` (the registered §11.1 read:
    `max(fraction(draws <= 0), 1/n_boot)` — floored per the referee-sim
    convention, disclosed in the module docstring), and
    `p_two_sided_sensitivity` (the parent's literal formula,
    sensitivity co-read only).
    """
    signs, succ, ns = _per_item_arrays(terms)
    n_items = len(succ[0])
    point = sum(s * (c.sum() / n.sum()) for s, c, n in zip(signs, succ, ns))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_items, size=(n_boot, n_items))
    draws = np.zeros(n_boot)
    for s, c, n in zip(signs, succ, ns):
        draws = draws + s * (c[idx].sum(axis=1) / np.maximum(n[idx].sum(axis=1), 1))
    le0 = float((draws <= 0).mean())
    ge0 = float((draws >= 0).mean())
    floor = 1.0 / n_boot
    p_one_sided = max(le0, floor)
    p_two_sided = min(1.0, 2 * min(le0, ge0))
    ci95 = tuple(float(x) for x in np.percentile(draws, [2.5, 97.5]))
    ci90 = tuple(float(x) for x in np.percentile(draws, [5.0, 95.0]))
    return {
        "delta": float(point), "n_items": n_items,
        "ci95": ci95, "ci90": ci90,
        "p_one_sided": p_one_sided, "p_two_sided_sensitivity": p_two_sided,
        "n_boot": n_boot, "seed": seed,
    }


def bootstrap_delta(
    hi_pairs: Sequence[PctPair], lo_pairs: Sequence[PctPair],
    *, n_boot: int = N_BOOT, seed: int = SEED,
) -> dict:
    """Two-arm delta `pooled(hi) - pooled(lo)`, item-paired. Covers H-B1,
    H-B2, H-B4, and every §11.3 descriptive CI-only two-arm contrast
    (S-Sq, Sq-P, sonnet-opus gradient, etc.) — the two-term case of
    `bootstrap_contrast`."""
    return bootstrap_contrast([(1.0, hi_pairs), (-1.0, lo_pairs)], n_boot=n_boot, seed=seed)


def bootstrap_interaction(
    s_haiku: Sequence[PctPair], p_haiku: Sequence[PctPair],
    s_opus: Sequence[PctPair], p_opus: Sequence[PctPair],
    *, n_boot: int = N_BOOT, seed: int = SEED,
) -> dict:
    """H-B3: `[catch_S - catch_P]_haiku - [catch_S - catch_P]_opus`, all
    four arrays drawn under ONE shared item-index resample (module
    docstring point 2 — mirrors `referee_sim.hb3_interaction_dist`
    exactly). All four sequences must be the SAME C44 items in the SAME
    order (§4.4/§11.1); `bootstrap_contrast` refuses on any length
    mismatch."""
    return bootstrap_contrast(
        [(1.0, s_haiku), (-1.0, p_haiku), (-1.0, s_opus), (1.0, p_opus)],
        n_boot=n_boot, seed=seed,
    )


def holm(p_values: Mapping[str, float | None], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm step-down over the registered Holm family (§11.1: "a voided
    member keeps its slot"). Graduated UNCHANGED in logic from
    the parent's `holm` — `m = len(p_values)` was already dynamic there
    (the parent docstring's "m=3" names the parent's own family size, not a
    hardcoded constant); a voided member is passed as `None`, keeps its
    slot in `m`, and never fires. Caller decides which p (one-sided,
    per `bootstrap_contrast`'s `p_one_sided`) feeds this — this function is
    agnostic to sidedness, exactly as the parent's was."""
    m = len(p_values)
    live = sorted(((k, p) for k, p in p_values.items() if p is not None),
                  key=lambda kv: kv[1])
    fires: dict[str, bool] = {k: False for k in p_values}
    step = 0
    for k, p in live:
        if p <= alpha / (m - step):
            fires[k] = True
            step += 1
        else:
            break
    return fires


def main() -> int:  # pragma: no cover - manual smoke entry, no CLI surface registered
    print("stats: analysis-helper module, no CLI. Import bootstrap_delta / "
          "bootstrap_interaction / holm.", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
