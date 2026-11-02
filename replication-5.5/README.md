# The same question on the 5.5 generation: a pre-registered replication, with a plain review added

Does asking a reviewer **all five defect families in one bundled prompt** stay
cheaper per real bug caught than asking **one family per dispatch**
(serialized) when the models change? This folder is the public extract of a
pre-registered replication of the study in this repository, run on Claude
Haiku 5.5, Claude Sonnet 5.5 and Claude Opus 5.5. It used the same 80-item
bank, the same bundled and serialized prompts (byte for byte), and the same
scoring rules and judge. It adds a third shape the original did not have: a
**plain review** that asks no family questions at all.

It is descriptive: nothing was tested, and intervals are reported, not gated.
The registration, the result, the independent recount and the disclosures are
here. The replication's dispatch records, model responses and scored rows are
not published (see [Limits](#limits)).

Built with Claude Code under my direction (Mikael Hillman-Pépin).

## The result

**Bundling stayed cheaper per true catch at every 5.5 tier.** Per true catch,
the serialized arm costs **2.43× the bundled review at Haiku 5.5** (95 % CI
2.07–2.87), **3.57× at Sonnet 5.5** (2.97–4.37) and **3.00× at Opus 5.5**
(2.58–3.48). Every interval lies wholly above 1, so under the registered verb
rule the bundled review is "still cheaper" at every tier. Count only the
serialized arm's output tokens (all its input free) against the bundled arm's
full bill, and bundling still wins 1.80× / 2.14× / 1.85×, each interval above 1.
Remove thinking tokens from both bills and the ratios are 2.55 / 3.50 / 2.97.

**Catches were close between the two shapes within each tier.** Bundled /
serialized true catches: 95 / 94 at Haiku 5.5, 60 / 54 at Sonnet 5.5, 94 / 90
at Opus 5.5. The serialized arm makes five calls where the bundled arm makes
one, and the extra calls did not buy extra catches.

**Haiku 5.5's serialized reviewers flagged clean code far more often.** The
share of reviews of a clean item that raised any flag, serialized vs bundled:
multi-file **0.567 vs 0.133**, single-function **0.500 vs 0.067** (difference
+0.433 in both; 95 % CI [+0.200, +0.667] and [+0.167, +0.667]). Off-family
flags on defective items also rose (0.127 vs 0.054 multi-file, 0.062 vs 0.003
single-function). At Sonnet 5.5 and Opus 5.5, false alarms were zero or near
zero in both shapes.

**The plain review caught less than the bundled review at Haiku 5.5 and Opus
5.5, and about the same at Sonnet 5.5.** Per-item catch rates on defective
items, plain vs bundled, on matched items: **0.46 vs 0.53** at Haiku 5.5 (60
items), **0.57 vs 0.57** at Sonnet 5.5 (33 items), **0.43 vs 0.65** at Opus 5.5
(36 items). The plain review is scored by its own rule (a BUG verdict plus a
defect key anywhere in the answer, instead of a flag on the asked family), so
this sets two instruments side by side rather than measuring one; plain rates
are given to two decimals because the registration left their aggregation
ambiguous ([disclosure 1](recount/RECOUNT.md#the-four-disclosures)).

**Next to the original.** The original study measured 2.97 / 2.14 / 2.24
(output-only 2.65 / 1.26 / 1.55) at Haiku 4.5 / Sonnet 5 / Opus 5. The bundled
review was cheaper per true catch there too. The larger ratios at Sonnet and
Opus this time are **not** claimed as a trend: the transport, the effort
setting, thinking, caching and the cost meter all changed between the runs
([What changed](#what-changed-from-the-original)), and dollar levels are not
compared across tiers or generations.

**A clean run.** 4,088 dispatches (3,836 main, 168 + 84 bridge), with no
truncated, failed, refused or empty answers in the main tiers (one refusal in
the bridge) and no halts in the run of record (one $0 halt before any record;
Amendment A2). Computed API spend was **$37.70**, under a $150 hard cap. An independent recount, fresh code written from the registration and its
frozen rules, agreed on all 5,840 scored rows and on 523 of 526 compared
figures; the other 3 were its first reading of an ambiguous plain-review rule,
and its second reading matches ([`recount/RECOUNT.md`](recount/RECOUNT.md)).

## The tables

Tiers are `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`. **P** is
the bundled review (one dispatch, all five family questions), **S** the
serialized arm (five dispatches, one family question each), **plain** the
plain review. "mf" is multi-file items, "sf" single-function items.

### Dollars per true catch, S over P, three ways

A true catch is a flag on the item's target family whose text contains one of
the item's curated defect keys. Dollars are usage × the pinned list prices
([Method](#method-in-brief)), summed over every dispatch of the arm, clean
items and off-target questions included.

| Tier | P $ | P true catches | P $ per catch | S $ | S true catches | S $ per catch |
|---|---|---|---|---|---|---|
| haiku-5-5 | 0.3416 | 95 | 0.0036 | 0.8227 | 94 | 0.0088 |
| sonnet-5-5 | 1.6582 | 60 | 0.0276 | 5.3277 | 54 | 0.0987 |
| opus-5-5 | 5.2128 | 94 | 0.0555 | 14.9485 | 90 | 0.1661 |

| Tier | (a) realized [95 % CI] | (b) thinking removed [95 % CI] | (c) S output only [95 % CI] | verb, (a) / (c) |
|---|---|---|---|---|
| haiku-5-5 | **2.43** [2.07, 2.87] | 2.55 [2.18, 3.00] | 1.80 [1.53, 2.13] | still cheaper / still cheaper |
| sonnet-5-5 | **3.57** [2.97, 4.37] | 3.50 [2.93, 4.29] | 2.14 [1.78, 2.61] | still cheaper / still cheaper |
| opus-5-5 | **3.00** [2.58, 3.48] | 2.97 [2.56, 3.46] | 1.85 [1.60, 2.14] | still cheaper / still cheaper |

- **(a) realized:** every output token billed, thinking included.
- **(b) thinking removed:** thinking tokens taken off both bills. The API
  reported thinking tokens as a separate usage field, so this read uses that
  field. It sits outside the verb rule.
- **(c) output-only bound:** S priced at its output tokens only (input free),
  against P realized.
- **Verb rule (registered):** "still cheaper" when the 95 % CI lies wholly
  above 1, "now more expensive" when wholly below 1, otherwise "not resolved".
- **Bootstrap:** per tier, items resampled within the defective and clean
  strata, one shared `numpy.random.default_rng(1512)` draw paired across arms,
  10,000 draws, percentile 95 % CI. Zero undefined draws at every tier.
- **Complete-unit co-read:** a unit is an (item, repetition) whose P dispatch
  and five S dispatches all ended clean. All 240 / 132 / 176 units were
  complete, so the co-read equals (a).
- No cell reached the 5 % exclusion gate; nothing is withheld.

### Catch rates on defective items

Per item, averaged over repetitions, on the items that pass inclusion in both
arms of each pair; n is the number of items in the pair. P and S are scored by
the original rules and plain by its own rule, so nothing is pooled. P and S
rates are printed as the report prints them (three decimals); plain rates to
two.

| Tier | P vs S: n | P | S | P vs plain: n | P | plain | S vs plain: n | S | plain |
|---|---|---|---|---|---|---|---|---|---|
| haiku-5-5 | 60 | 0.528 | 0.522 | 60 | 0.528 | 0.46 | 60 | 0.522 | 0.46 |
| sonnet-5-5 | 36 | 0.556 | 0.500 | 33 | 0.566 | 0.57 | 33 | 0.515 | 0.57 |
| opus-5-5 | 36 | 0.653 | 0.625 | 36 | 0.653 | 0.43 | 36 | 0.625 | 0.43 |

### The plain review

The registered rate (strict) counts a parsed BUG verdict with at least one
defect key in the answer (fenced code removed), over parseable answers. An item
enters only if at least half its repetitions (rounded up) parsed. In the same
row: the loose-parser rate, and the rate with unparseable answers counted as
misses (as a missing answer is no catch in P and S). The loose rate becomes
co-primary only if more than 10 % of a cell's answers are strict-unparseable.

| Tier | strict | items | loose | items | unparseable as miss | unparseable answers | loose co-primary |
|---|---|---|---|---|---|---|---|
| haiku-5-5 | 0.46 | 60 | 0.46 | 60 | 0.46 | 0 of 240 | no |
| sonnet-5-5 | 0.57 | 33 | 0.62 | 36 | 0.53 | 12 of 132 | no |
| opus-5-5 | 0.43 | 36 | 0.43 | 36 | 0.43 | 0 of 176 | no |

The registration defines dollars per true catch for P and S only. **A plain
dollars-per-catch figure was not registered and is not printed here**
([disclosure 2](recount/RECOUNT.md#the-four-disclosures)); plain spend per cell
is in the counts table below.

### Extraction co-reads

The original study's two extraction brackets, carried unchanged: **V2** widens
the bundled answer's key-matching scope to the whole response; **V3** refuses a
serialized answer that carries no marker for the asked family. V1 is the
registered reading. In brackets: P / S true catches.

| Tier | V1 S/P | V2 S/P | V3 S/P | V2 catch rate P / S | V3 catch rate P / S |
|---|---|---|---|---|---|
| haiku-5-5 | 2.43 (95 / 94) | 2.59 (101 / 94) | 2.54 (95 / 90) | 0.561 / 0.522 | 0.528 / 0.500 |
| sonnet-5-5 | 3.57 (60 / 54) | 3.69 (62 / 54) | 3.57 (60 / 54) | 0.574 / 0.500 | 0.556 / 0.500 |
| opus-5-5 | 3.00 (94 / 90) | 3.06 (96 / 90) | 3.00 (94 / 90) | 0.667 / 0.625 | 0.653 / 0.625 |

The registration also asked for these co-reads beside the false alarms; the
report did not print them. The recount computed them at Haiku 5.5 (pooled over
mf and sf): V3 lowers S off-family false alarms from 67 to 61 of 708 and S
clean-item any-flag from 32/60 to 28/60; V2 raises P key-matched-wrong-family
flags from 3 to 10 of 708. The recount did not re-run the bound check under V2
or V3 ([disclosure 4](recount/RECOUNT.md#the-four-disclosures)).

### False alarms, after the clean-item pair check

Three classes, as in the original, each split mf / sf and never pooled:
**clean, any flag** (share of reviews of a clean item that raised at least one
flag); **off-family** (flags on a non-target family question of a defective
item); **key matched, wrong family** (an off-family flag whose text contains
the item's defect key).

Before false alarms are read, the **clean-item pair check** looks at every
(clean item, family) pair that drew a flag and asks a checker model whether the
flagged defect is real; a pair it confirms as real would leave the false-alarm
count. It checked 17 of 17 such pairs in the main tiers and found every one
not real, so no pair was removed (see disclosure 3 for its scope).

The stamp is the original registration's adoption bound, carried as a
descriptive label (nothing is gated on it here): **OUT-OF-BOUND** when S − P
exceeds 0.15 absolute, or S exceeds twice P when P > 0, with the 95 % CI not
spanning 0.15; **IN-BOUND** otherwise; UNRESOLVED when the CI spans 0.15. The
two Haiku 5.5 off-family stamps are ratio-clause breaches at small rates (the
difference is below 0.15).

| Tier | class | split | S | P | S − P [95 % CI] | items | stamp |
|---|---|---|---|---|---|---|---|
| haiku-5-5 | clean, any flag | mf | 0.567 | 0.133 | +0.433 [+0.200, +0.667] | 10 | OUT-OF-BOUND |
| haiku-5-5 | clean, any flag | sf | 0.500 | 0.067 | +0.433 [+0.167, +0.667] | 10 | OUT-OF-BOUND |
| haiku-5-5 | off-family | mf | 0.127 | 0.054 | +0.073 [+0.037, +0.112] | 30 | OUT-OF-BOUND |
| haiku-5-5 | off-family | sf | 0.062 | 0.003 | +0.059 [+0.023, +0.104] | 30 | OUT-OF-BOUND |
| haiku-5-5 | key matched, wrong family | mf | 0.008 | 0.008 | +0.000 [−0.008, +0.008] | 30 | IN-BOUND |
| haiku-5-5 | key matched, wrong family | sf | 0.014 | 0.000 | +0.014 [0.000, +0.036] | 30 | IN-BOUND |
| sonnet-5-5 | clean, any flag | mf | 0.000 | 0.000 | 0.000 | 4 | IN-BOUND |
| sonnet-5-5 | clean, any flag | sf | 0.000 | 0.000 | 0.000 | 4 | IN-BOUND |
| sonnet-5-5 | off-family | mf | 0.013 | 0.000 | +0.013 [0.000, +0.041] | 19 | IN-BOUND |
| sonnet-5-5 | off-family | sf | 0.005 | 0.000 | +0.005 [0.000, +0.015] | 17 | IN-BOUND |
| sonnet-5-5 | key matched, wrong family | mf | 0.000 | 0.000 | 0.000 | 19 | IN-BOUND |
| sonnet-5-5 | key matched, wrong family | sf | 0.000 | 0.000 | 0.000 | 17 | IN-BOUND |
| opus-5-5 | clean, any flag | mf | 0.000 | 0.000 | 0.000 | 4 | IN-BOUND |
| opus-5-5 | clean, any flag | sf | 0.000 | 0.000 | 0.000 | 4 | IN-BOUND |
| opus-5-5 | off-family | mf | 0.017 | 0.010 | +0.007 [0.000, +0.017] | 19 | IN-BOUND |
| opus-5-5 | off-family | sf | 0.000 | 0.000 | 0.000 | 17 | IN-BOUND |
| opus-5-5 | key matched, wrong family | mf | 0.000 | 0.000 | 0.000 | 19 | IN-BOUND |
| opus-5-5 | key matched, wrong family | sf | 0.000 | 0.000 | 0.000 | 17 | IN-BOUND |

The plain review's false alarms, on its own scale (a parsed BUG verdict on a
clean item, over parseable answers):

| Tier | mf | sf |
|---|---|---|
| haiku-5-5 | 17 / 30 (0.567) | 2 / 30 (0.067) |
| sonnet-5-5 | 0 / 10 | 0 / 12 |
| opus-5-5 | 0 / 16 | 0 / 16 |

### Counts per tier × arm

TRUNCATED (hit max_tokens), FAILED, REFUSED and NO-TEXT count dispatches;
UNRESOLVED counts rows the adjudication lane could not resolve. P-MISSING is
the number of bundled rows scored missing while the bundle had text (each one
is read before any figure is computed). Thinking is the mean thinking tokens per
dispatch. Every cell had zero worst-case spend bookings and zero spend on
excluded dispatches, and none was gated.

| Tier | arm | dispatches | TRUNC / FAILED / REFUSED / NO-TEXT / UNRESOLVED | P-MISSING | thinking per dispatch | usage $ |
|---|---|---|---|---|---|---|
| haiku-5-5 | P | 240 | 0 / 0 / 0 / 0 / 0 | 0 | 1,747 | 0.3416 |
| haiku-5-5 | S | 1,200 | 0 / 0 / 0 / 0 / 0 | | 816 | 0.8227 |
| haiku-5-5 | plain | 240 | 0 / 0 / 0 / 0 / 0 | | 1,280 | 0.2079 |
| sonnet-5-5 | P | 132 | 0 / 0 / 0 / 0 / 0 | 0 | 367 | 1.6582 |
| sonnet-5-5 | S | 660 | 0 / 0 / 0 / 0 / 0 | | 246 | 5.3277 |
| sonnet-5-5 | plain | 132 | 0 / 0 / 0 / 0 / 0 | | 190 | 0.8452 |
| opus-5-5 | P | 176 | 0 / 0 / 0 / 0 / 0 | 0 | 435 | 5.2128 |
| opus-5-5 | S | 880 | 0 / 0 / 0 / 0 / 0 | | 254 | 14.9485 |
| opus-5-5 | plain | 176 | 0 / 0 / 0 / 0 / 0 | | 364 | 2.7676 |

### Side by side with the original

| Original tier | S/P (original) | output-only (original) | true catches P / S (original) |
|---|---|---|---|
| claude-haiku-4-5-20251001 | 2.97 | 2.65 | 105 / 120 |
| claude-sonnet-5 | 2.14 | 1.26 | 80 / 75 |
| claude-opus-5 | 2.24 | 1.55 | 68 / 75 |

Levels are not compared across generations, and the C44 subset's levels are by
construction (it was selected for an Opus 5 bundled catch rate near 0.5).

### The bridge (instrument context; descriptive, no tolerance)

Two original models re-run on the new transport, on a seeded slice of items,
beside the original records for the same item, repetition and family. Haiku
4.5: 9 defective + 3 clean items, repetitions 0–1. Opus 5: 9 defective + 3
clean items from C44, repetition 0. It bounds how much of a difference between
generations could be the harness; it cannot attribute the rest to the model.

| Model | arm | catch rate new / original | output tokens per dispatch new / original | $ per catch new / original |
|---|---|---|---|---|
| claude-haiku-4-5-20251001 | P | 0.556 / 0.611 | 369 / 8,547 | 0.0081 / 0.1014 |
| claude-haiku-4-5-20251001 | S | 0.611 / 0.722 | 194 / 5,737 | 0.0238 / 0.2937 |
| claude-haiku-4-5-20251001 | plain | 0.778 / 0.674 (calibration) | | |
| claude-opus-5 | P | 0.333 / 0.556 | 1,484 / 1,773 | 0.1891 / 0.1439 |
| claude-opus-5 | S | 0.667 / 0.778 | 665 / 761 | 0.2467 / 0.2489 |

The original's $ per catch is the original CLI's cost figure. The Haiku 4.5
bridge runs without thinking (its API default), while the original CLI's Haiku
calls thought heavily under a setting that was not recorded, so the two token
counts are not like for like. On 9 defective items, new and original differ by
one or two true catches per row.

| Model | arm | dispatches | TRUNC / FAILED / REFUSED / NO-TEXT / UNRESOLVED | usage $ |
|---|---|---|---|---|
| claude-haiku-4-5-20251001 | P | 24 | 0 / 0 / 0 / 0 / 0 | 0.08 |
| claude-haiku-4-5-20251001 | S | 120 | 0 / 0 / 0 / 0 / 0 | 0.26 |
| claude-haiku-4-5-20251001 | plain | 24 | 0 / 0 / 0 / 0 / 0 | 0.04 |
| claude-opus-5 | P | 12 | 0 / 0 / 0 / 0 / 0 | 0.57 |
| claude-opus-5 | S | 60 | 0 / 0 / 1 / 0 / 0 | 1.48 |
| claude-opus-5 | plain | 12 | 0 / 0 / 0 / 0 / 0 | 0.44 |

The one refusal was on a clean item (`clean-mf-04`, repetition 0, the sign
question).

### The adjudication lane

Answers that are present but off-format go to a blinded adjudication lane that
rules FLAG / NONE / NEITHER only; whether a FLAG is a catch stays the
mechanical key match. 422 rows were routed, in 71 batches, all returned. A
second fresh reader re-read a 15 % sample (63 rows): 62 agreed, and the one
disagreement went to a third, governing reader, who resolved it. In a 10 %
arm-guess sample (42 rows) the reader guessed the arm correctly 5 times and
declined to guess 33 times, so there is no sign the lane could tell the arms
apart. Zero rows were left unresolved.

### Spend

Computed from usage at the pinned list prices; the provider console was not
read.

| Component | $ |
|---|---|
| preflight (15 dispatches, one lane batch, one pair-check call) | 0.3105 |
| sizing batch (40 Haiku 5.5 bundled dispatches) | 0.0648 |
| main run (main tiers and bridge) | 35.0027 |
| adjudication lane | 1.8927 |
| clean-item pair check | 0.4255 |
| **total** | **37.6962** |

The pre-run projection for the main run was $101; it came in at $35.00, so the
projection over-shot by about 2.9×. The recount made no API calls.

## Method in brief

- **Same bank, same cells.** The 80 items in `../materials/items/`. Haiku 5.5
  ran all 80 (60 defective, 20 clean) × 3 repetitions; Sonnet 5.5 the 44-item
  subset C44 (36 defective, 8 clean) × 3; Opus 5.5 C44 × 4, as the original ran
  its three tiers. 3,836 main dispatches. The item files, question texts,
  briefing, key table, C44 list and adjudication charges are byte-identical to
  the files in this repository (checked by SHA-256 when this extract was
  built).
- **Same prompts for P and S.** The original assembly, byte for byte: system
  prompt "You are a helpful assistant."; the briefing, the item, then either
  the five family questions in their keyed order (P) or the line "You are asked
  about family ⟨f⟩ only." and one question (S). `../analysis/payloads.py` is
  that assembly.
- **The plain review** is the open-search protocol the bank was calibrated
  with ([Appendix A](../methods/BANK-CALIBRATION.md)): one free review per item,
  no family questions. The registration renders its exact system prompt.
- **Transport.** The raw Messages API, streaming, no tools, no prompt-cache
  markers, no sampling parameters, 8 workers, `max_tokens` 64,000. The served
  model was asserted on every response (4,088 of 4,088 matched).
- **Effort and thinking.** Effort `high` on every 5.5 tier and on Opus 5,
  thinking at each model's default (adaptive). Thinking bills as output, so it
  is in the realized cost. The Haiku 4.5 bridge takes no effort parameter and
  ran without thinking.
- **Scoring.** The original study's corrected-pass rules
  ([amendment](../registration/amendments/2026-08-27-corrected-scoring-pass.md)):
  the permissive presence grammar, the scored text per arm, the V2/V3
  co-reads, the false-alarm classes and the clean-item pair check. The same
  judge as the original, `claude-opus-5` (effort high), rules the adjudication
  lane; here it is not one of the models under test.
- **Cost.** Usage × pinned list prices per million tokens, input / output:
  Haiku 5.5 $0.10 / $0.50, Sonnet 5.5 $2 / $10, Opus 5.5 $4 / $20, Haiku 4.5
  $1 / $5, Opus 5 $5 / $25. No cache tokens appeared.
- **Order.** All units (tier, arm, item, repetition), main and bridge, in one
  sorted list shuffled with `random.Random(1512)`, so a spending halt would have
  left every cell sampled roughly in proportion.
- **Spend control.** Before every attempt, retries included, its worst case was
  reserved and the halt re-checked (main run halts at $145 including the
  projected lane cost; lane and pair check at $149). No halt fired in the run of
  record (one $0 halt before any record; Amendment A2).
- **Zero-spend reproduction gate.** Before any paid call, the new analysis path
  run on this repository's public dispatch tables and verdicts had to reproduce
  the original's 2.97 / 2.14 / 2.24, output-only 2.65 / 1.26 / 1.55 and true
  catches 105 / 120, 80 / 75, 68 / 75, and the calibration records' Haiku 4.5
  plain rate 0.579. It did.
- **Registration** locked on 2026-11-01, before the first paid call; two dated
  amendments before the first record. See
  [`registration/preregistration.md`](registration/preregistration.md).

## What changed from the original

| | Original | Replication |
|---|---|---|
| Models | Haiku 4.5, Sonnet 5, Opus 5 | Haiku 5.5, Sonnet 5.5, Opus 5.5, plus a bridge slice on Haiku 4.5 and Opus 5 |
| Transport | Claude Code CLI 2.1.212 (`--bare`, no tools) | raw Messages API, streaming |
| Effort | the CLI's default, not recorded | `high`, pinned |
| Thinking | the CLI's, not recorded (Haiku 4.5 thought heavily) | each model's adaptive default, billed as output, reported separately |
| Shapes | P, S, Sq (one question per turn) | P, S, plain; Sq not run |
| Tests | one Holm family of four tests, an equivalence band | none; descriptive, with a verb rule on the CIs |
| Cost meter | the CLI's computed total | usage × pinned list prices |
| Caching | the premium tiers read cache | none appeared |
| Adjudicator | `claude-opus-5`, also a subject | `claude-opus-5`, not a subject; lane run over the raw API |
| Bank | private when run | public since 2026-10-31 |

## Limits

- **Descriptive, nothing tested.** Intervals are reported, not gated; the verb
  rule is the only reading attached to them.
- **Ratios compare arms within a tier.** Dollar levels are not compared across
  tiers or generations (prices differ), and C44's levels are by construction.
- **Not a trend.** The larger Sonnet and Opus ratios relative to the original
  are not a claimed trend. Transport, effort, thinking, caching and the cost
  meter all changed. On the same original models, the new harness (with
  thinking off, for Haiku 4.5) moved token counts a great deal and catch rates
  by one or two catches on very small samples; the bridge cannot isolate the
  model.
- **No data here.** The replication's dispatch records, responses, scored rows
  and run records are not published, so its figures cannot be re-derived from
  this repository. They rest on the report of record and the independent
  recount.
- **Lock-before-data is attested only by private history** (registration
  header).
- **One effort level.** Other effort settings were not measured.
- **The plain review is a different instrument**: its own scoring rule, a
  one-sentence explanation that limits key matching, and false alarms on its
  own scale. Its dollars per catch were not registered; this summary does not
  print them, and the recount's disclosure 2 quotes the Sonnet 5.5 figure only
  to explain why.
- **Shared scorer.** The recount used the same frozen scoring modules as the
  run for P and S, so agreement on mechanically scored rows is partly by
  construction; those modules were certified by the original study's recount.
  What the recount did not verify is listed in
  [`recount/RECOUNT.md`](recount/RECOUNT.md).
- **Lane blinding rests on scrubbing protocol labels**; response shape is not
  scrubbed (as in the original). In the arm-guess check the reader was right 5
  times in 42 and declined 33 times.
- **The bank is public** (since 2026-10-31); the registration states that the
  5.5 models' training cutoffs predate that.
- Findings are about this synthetic bank, these models, effort `high`, and this
  harness. Family-cued questions make P and S catch rates incomparable to
  open-search review in absolute terms.
- Four disclosures raised at close are in
  [`recount/RECOUNT.md`](recount/RECOUNT.md#the-four-disclosures).

## In this folder

| Path | What |
|---|---|
| `README.md` | This summary |
| `registration/preregistration.md` | The locked registration, public rendering, with its two amendments |
| `recount/RECOUNT.md` | The independent recount's method and verdict, and the four disclosures |

Text in this folder is licensed CC BY 4.0, as the rest of the repository's
text ([`../LICENSE-CC-BY-4.0.txt`](../LICENSE-CC-BY-4.0.txt)).

Built with Claude Code under my direction (Mikael Hillman-Pépin).
