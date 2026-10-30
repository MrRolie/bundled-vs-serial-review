# Appendix A — how the bank was calibrated (the bank-calibration study)

The serialization × tier study reuses an 80-item code-review bank built and
calibrated by an earlier, separately pre-registered study (locked 2026-07-17;
its registration is not published). This appendix reports that calibration:
the numbers, not the build history. Per-item tables are in
`appendix/bank-calibration/`.

## The bank

- **80 items**: 60 defective (12 per defect family: boundary, comparison,
  exception, sign, units; half multi-file, half single-function) and 20 clean
  (10 multi-file, 10 single-function). Files: `materials/items/`.
- **Synthetic.** Every item was written by a model (`author_model` in the
  manifests: claude-sonnet-5) and certified by a separate checker model
  (claude-opus-4-8) plus a blind review. The bank was authored in two cohorts.
  The 20-item pilot's authoring prompt asked for "ordinary, sincere, realistic
  code ... Pick any plausible domain you like"; the 60-item main cohort assigned
  each item a neutral application area from a fixed list (warehouse inventory,
  recipe scaling, tide prediction, flight standby, and so on) and added a
  "naming-resistance" lever (defects easy to notice but hard to name
  precisely). Some items are finance-flavored: pilot items model tax lots per
  security, cache FX rates, amortize a loan, and price invoices. The pilot was
  written on 2026-07-18 on the subscription-authenticated setup. As
  `methods/HARNESS-STERILITY.md` §2 enumerates for that setup, it passed the CLI's
  scaffolding and the account email to the model; that was not measured on the
  2026-07-18 calls themselves. They are invented code with seeded defects, not code from any real
  system.
- **Ground truth is mechanical.** Each defective item carries curated
  `defect_keys`; a catch is a FLAG verdict whose text contains at least one key
  (case-insensitive substring). Clean items are certified clean.

## The calibration (weakest tier, 2,400 draws)

80 items × n = 30 draws = **2,400 trials** at `claude-haiku-4-5-20251001`,
2026-07-28/29, one regime throughout (frozen CLI 2.1.212, `--bare`, no tools,
metered API key). Zero instrument errors, zero unplaceable items. Open-search
review (one free review per item, not family-cued).

| Registered criterion | Result | Threshold | Verdict |
|---|---|---|---|
| H-A1 interior mass: hit rate in [10 %, 90 %) | **33 / 60** | ≥ 30 | passes (marginal) |
| H-A2 target-band mass: hit rate in [40 %, 80 %] | **21 / 60** | ≥ 15 | passes |

Stratified bootstrap (2,000 reps, seed 1512): H-A1 share 0.550, 95 % CI
[0.483, 0.600] = **[29, 36] of 60 against a threshold of 30** — the interval
contains the threshold, so the pass is not robust to trial-level noise and is
reported as marginal. H-A2 0.350 [0.267, 0.400] = [16, 24] vs 15.

| floor < 10 % | hard [10, 40) | medium [40, 65) | easy [65, 90) | ceiling ≥ 90 % | unplaceable |
|---|---|---|---|---|---|
| 11 | 7 | 12 | 14 | 16 | 0 |

Robustness: a loose parser reproduces every bin exactly; an explanation-scoped
key matcher moves one item (ceiling → easy), giving 34 / 22 — both criteria pass
under all three readings. Three items sit exactly on registered edges
(27/30 = 0.90 is ceiling; two at 24/30 = 0.80 are in the closed band).

**False alarms on the 20 clean items, never pooled across item classes:**
multi-file 0.480 (Wilson 95 % CI [0.423, 0.537], 142/296); single-function
0.140 ([0.105, 0.184], 42/300). Nearly half of all reviews of a clean multi-file
item reported a bug that is not there.

**Detection is saturated; naming is not.** The verdict-only BUG rate on
defective items has median 1.000 (49 of 60 items at exactly 1.00), while the
named-vs-verdict gap has median 0.283. All discriminative power lives in the
key match, which is why the serialization × tier study has no verdict-only
endpoint.

**Structural covariates do not predict difficulty** (exploratory): Spearman ρ
for cue directness +0.135, distractor count −0.115, files spanned +0.073,
locality hops +0.017 (all p > 0.3).

**Cost**: $0.03702 per haiku trial (8.1× the registered estimate); the
2,400-trial batch cost $88.85.

**Independent recount**: fresh code from the registered rules, raw records:
EXACT agreement on H-A1, H-A2, every bin, all 60 per-item rates, per-class false
alarms and both robustness variants.

## Strong tiers (20-item subsample, n = 10 per item)

A deterministic 20-item "hardest" subsample, at two stronger models:

| Tier | Interior | Bins floor / hard / medium / easy / ceiling | Clean-item FA (sf / mf) |
|---|---|---|---|
| haiku (n = 30, all 60) | 33 / 60 | 11 / 7 / 12 / 14 / 16 | 0.14 / 0.48 |
| claude-opus-4-8 (n = 10) | 14 / 20 | 4 / 8 / 5 / 1 / 2 | 0.00 / 0.10 |
| claude-fable-5 (n = 10) | 13 / 20 | 2 / 4 / 4 / 5 / 5 | 0.00 / 0.00 |

H-A3 (off-ceiling mass at the top tier, threshold 5 interior): **fires**
(13/20 at claude-fable-5). The bank is not at ceiling for the strongest models.
The false-alarm structure is tier-graded and vanishes at the top. Strong-tier
passes ran 4–8× below cache-cold cost projections (prompt caching across
same-item draws).

**Cost of the calibration phase: ≈ $140.77 in all** — pilot $12.49, a
pre-batch step $7.42, the 2,400-trial batch with its gates $91.90, opus-4-8
$9.99, fable-5 $18.78, small probes and gates ≈ $0.19. The lab's budget
ledger recorded $128.10 for this phase: the four steps after the pilot
($7.42 + $91.90 + $9.99 + $18.78 = $128.09); the pilot and the small probes
were accounted separately. Not included: the model calls that authored the
bank (claude-sonnet-5) and certified it (claude-opus-4-8), which were not
itemized.

## How the serialization × tier study uses it

The bank's grades are instrument data only. The serialization study re-measures
its own baselines; no calibration hit rate enters any of its endpoints. The
study's family-cued questions hint the search space, so its absolute catch
rates are not comparable to these open-search rates. Its common item subset
(C44) was selected from a separate cued-format calibration probe at opus-5,
not from these bins.

## Files

- `appendix/bank-calibration/placement-defective.csv` — per defective item:
  class, family, haiku hit rate / parseable draws / bin / verdict-only rate,
  and hits / parseable / bin at opus-4-8 and fable-5 where the item is in the
  subsample.
- `appendix/bank-calibration/calibration-summary.json` — bin counts,
  per-class clean false alarms, the strong-tier subsample and clean wing, H-A3.
- `materials/manifest.jsonl` (the 20-item pilot cohort),
  `materials/manifest_s5.jsonl` (the 60-item main cohort; `s5` and the
  `cohort: "s5"` field are its internal batch label) — authoring and
  certification metadata per item (the `*_sha256` fields hash authoring and
  review transcripts that are not published). These are **redacted copies**:
  each record's build-history object (internal batch and rule codes,
  unpublished dispatch ids) was removed, so they do not hash-match the frozen
  private files. The item files themselves are byte-identical to the frozen
  ones.
