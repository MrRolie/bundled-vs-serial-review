# One review question per dispatch, or all of them in one? A pre-registered measurement across three model tiers

When AI agents review code, does asking a reviewer **one family of defects per
dispatch** (serialized) catch more defects than asking **all five families in one
bundled prompt**, and does the answer change with the model tier?

This repository is the public extract of a pre-registered study that measured it
on Claude Haiku 4.5, Claude Sonnet 5 and Claude Opus 5: the registration, the
80-item code-review bank, the exact prompts (rebuilt byte for byte from the
frozen materials and checked against every recorded hash), every model response
that was scored, the scored table, the analysis code, an independent recount,
and the results. The analysis chain reproduces every number it computes from the
files here (see [Re-running it](#re-running-it)).

Built with Claude Code under my direction (Mikael Hillman-Pépin).

## The result

**Robust: bundling wins on cost per true catch at every tier, under the
registered reading and both extraction brackets.** Serializing costs **3.0× more
per true catch at haiku, 2.1× at sonnet and 2.2× at opus** (2.97 / 2.14 / 2.24;
3.05 / 2.17 / 2.28 and 3.30 / 2.14 / 2.24 under the two extraction brackets,
which were registered after the data, see [The limit](#the-limit); 2.93 / 2.00 /
2.18 with the CLI's own helper-call cost removed; these three sets come from
`recount/recount-economics.json`, re-run with
`python recount/code/recount_economics.py OUT.json`). The ratios are point
estimates, but the margin is wide: the serialized arm spends 3.4× / 2.0× / 2.5×
the dollars of the bundled arm, so even at the upper end of each serialized-minus-
bundled catch interval (95 %, with the bundled arm at its observed rate) bundling
stays cheaper per true catch, by at least 1.8× (at sonnet). And with every
serialized input token priced at zero (output tokens only), bundling still wins
2.65× / 1.26× / 1.55× (`analysis/costs.py --bounds-out`, checked by
`analysis/reproduce.py`).

The extra catches are few in distinct defects. The bundled arm's 3–4
repetitions per item already found 48 of 60, 35 of 36 and 30 of 36 distinct
defective items at haiku, sonnet and opus, so more bundled repetitions could add
at most 12 / 1 / 6 new ones. The serialized arm found 53 / 32 / 29 (+5 / −3 / −1)
at 3.4× / 2.0× / 2.5× the dollars. (The registered equal-dollars read is linear
in repetitions and counts re-catches: the serialized arm's extra dollars would
buy up to roughly 251 / 81 / 100 more bundled catch events against its marginal
+15 / −5 / +7. It overstates what extra repetitions can find.)

**Robust: serialized haiku reviewers raise off-target false alarms about 5×
more.** Off-family false-alarm rate, serialized vs bundled: multi-file items
**0.285 vs 0.054** (Δ +0.232, 95 % CI [+0.181, +0.283]), single-function items
0.294 vs 0.054 (Δ +0.240 [+0.185, +0.296]); both CIs lie entirely above the
registered 0.15 adoption bound under the registered reading and the first
bracket (V2). Under the second bracket (V3) the single-function CI stays above
it, and the multi-file lower bound lands exactly on 0.15 (UNRESOLVED). The
roughly 5× ratio holds under all three (V3: 0.251 vs 0.054 multi-file, 0.277 vs
0.054 single-function). Serialization raises the willingness to flag more than
it raises discrimination.

**Top tier flat; mid tier null.** At opus, serialized minus bundled catch rate
is +0.049, 90 % CI [−0.028, +0.125], inside the registered ±0.20 equivalence band
(no finer claim). At sonnet it is −0.046 [−0.157, +0.065], null. The predicted
tier interaction (gap shrinking as models get stronger) is not supported:
+0.025 [−0.079, +0.132], p 0.322. The registered power for an interaction of
0.20 at opus r = 4 was ≈ 0.59, so this null does not rule out an interaction of
that size.

**The registered primary fires on the registered instrument and is fragile.**
At haiku, serialized minus bundled catch rate is **+0.083, 95 % CI [+0.017,
+0.150], one-sided p 0.0111**, which survives Holm correction (adjusted 0.0444)
on the registered bootstrap (10,000 draws, seed 1512). But:

- across 40 alternative seeds at the same 10,000 draws it fires on **33 of 40**
  (p 0.0098–0.0139 against a Holm threshold of 0.0125); at 1,000,000 draws
  p = 0.011446 and it fires;
- under the two **extraction brackets** (registered post-data, 2026-08-27) it
  does not fire: widening the bundled arm's key-matching scope to the whole
  response gives +0.067 [0.000, +0.133], p 0.035; refusing serialized answers
  that do not name the asked family gives +0.017 [−0.056, +0.089], p 0.357;
- under a within-item reading of the bootstrap it fires comfortably
  (p 0.0057). That reading resamples repetitions within each item and holds the
  item set fixed, so it says nothing beyond these 60 items and always gives
  smaller p values; it is the less conservative reading. The item-cluster
  reading is the one to generalize from.

So the haiku serialization benefit is declared under the registered reading
and unresolved under either bracket. The economic conclusion does not depend on
it: in every one of these readings the bundled shape is cheaper per true catch.
The fourth Holm member (haiku one-question-per-turn vs bundled, +0.094
[+0.011, +0.183], p 0.0169 vs a step threshold of 0.016667) misses by 0.0002,
fires on 17/40 seeds and at 1e6 draws, and reverses under the stricter
bracket; it carries no weight.

Full results with every stamp, co-read and disclosure:
[`results/RESULTS.md`](results/RESULTS.md).

## Design

| | |
|---|---|
| **Models** (full resolved ids) | `claude-haiku-4-5-20251001`, `claude-sonnet-5`, `claude-opus-5`. The registration's conditional fourth tier (`claude-fable-5`) would run only if the interaction test fired (gate G-FAB, registration §13); it did not, so that wing was not run. |
| **Dispatch shapes** | **P** bundled: one dispatch, the briefing + the diff + all five family questions (order randomized per trial). **S** serialized: five dispatches, the briefing + the diff + one question each, fresh context. **Sq** sequential turns: one session, five turns, one question per turn (briefing and diff at turn 1). |
| **Questions** | One per defect family: boundary, comparison, exception, sign, units. Byte-identical across arms; every briefing states the five-family partition. In S and in every Sq turn the question is preceded by the line "You are asked about family ⟨f⟩ only." Texts: `materials/overlay/questions.json`, `materials/overlay/briefing.md`. |
| **Exact prompts** | Rebuilt byte for byte by `analysis/payloads.py` from the frozen materials (components joined by a blank line; each file rendered as `--- path ---` plus a fenced block). All 5,163 payloads (5,148 trial invocations + 15 grouped-order probes) match their recorded SHA-256 in `data/dispatches/`, and the randomized orders re-derive from their registered keys (920/920). `python analysis/payloads.py --render TIER ITEM ARM REP [--family F]` prints any one. |
| **Bank** | 80 synthetic items: 60 defective (12 per family, half multi-file), 20 clean (`materials/items/`). Calibrated off-ceiling by an earlier study ([Appendix A](methods/BANK-CALIBRATION.md)). |
| **n** | haiku: all 80 items × 3 reps × P/S/Sq (240 P, 1,200 S, 240 Sq sessions). sonnet: the 44-item common subset C44 (36 defective + 8 clean) × 3 reps × P/S/Sq. opus: C44 × 4 reps × P/S (amended from 3 before any opus trial). 3,660 trial records, 5,148 model invocations, **7,340 question-rows**, zero instrument failures. |
| **Instrument** | Claude Code CLI 2.1.212 (frozen copy), `--bare --tools "" --strict-mcp-config`, metered API key, sterile working directory, system prompt the constant "You are a helpful assistant.", default effort. |
| **Scoring** | A catch is a FLAG on the target family whose text contains one of the item's curated defect keys. Answers that are present but off-format go to a blinded adjudication lane that resolves FLAG / NONE / NEITHER only; the key match stays mechanical. 1,805 of 7,340 rows reached that route (1,804 verdicts; 1 row had no answer at all). The adjudicator was claude-opus-5 throughout. 15 % second-reader check (130/130 agreement on the corrected lane), 10 % arm-guess check (86/86 declined to guess). |
| **Tests** | One Holm family (m = 4, one-sided, α = 0.05): H-B1 haiku S−P, H-B2 sonnet S−P, H-B3 tier interaction haiku vs opus on C44, H-B4 haiku Sq−P. Item-cluster bootstrap, 10,000 draws, seed 1512. Top-tier flatness is an equivalence band read (90 % CI within ±0.20), not a test. False alarms co-reported in three classes, split by item class, never pooled. |
| **Result cells** | The registration maps outcomes to named cells, keyed on the (H-B1, H-B3) pair. **C-B2** (H-B1 fires, H-B3 does not): serialization benefit real at the weakest tier, tier gradient unresolved; per-tier $/true-catch governs any adoption text. **C-B5** (neither fires): the null family. **C-B-TTFLAT** (band cell): top tier flat, the opus 90 % CI inside ±0.20. |
| **Who ran it** | AI agents, each in a fresh context: the study pipeline (built and run with Claude Code), the item-exclusivity audit readers, the adjudication lanes, the pre-lock review and both recounts. "Independent" in this repository means separate code and context, not a separate person or team. |

## Costs

| Tier | Arm | Dispatches | True catches | Realized $ | $ per true catch |
|---|---|---|---|---|---|
| haiku | P | 240 | 105 | 11.22 | **0.107** |
| haiku | S | 1,200 | 120 | 38.05 | 0.317 |
| haiku | Sq | 1,200 (240 sessions) | 122 | 34.45 | 0.282 |
| sonnet | P | 132 | 80 | 4.86 | **0.061** |
| sonnet | S | 660 | 75 | 9.75 | 0.130 |
| sonnet | Sq | 660 (132 sessions) | 70 | 7.15 | 0.102 |
| opus | P | 176 | 68 | 10.19 | **0.150** |
| opus | S | 880 | 75 | 25.20 | 0.336 |

Cost is the CLI's `total_cost_usd` (whole-cell numerator: clean items and
off-target questions are priced in). **This is a departure:** the registration
names the API-key console as the meter of record and the CLI total as a floor;
the console was not read, so every $ figure here is the CLI-computed total. Rows
are priced at the CLI-billed table (per MTok in/out: haiku $1/$5, sonnet $3/$15,
opus $5/$25); a provider reference lists sonnet-5 at $2/$10. At $2/$10 sonnet
stays the cheapest tier per true catch and the ratios barely move (S/P 2.21×,
from `recount/recount-economics.json`).

Caching: the registered grouped-order probe (one item, five questions, per
tier) read no cache, so prompts that differ only in their final question did not
share a cached prefix in this harness. The main run did read cache at the
premium tiers (224 of 660 sonnet and 340 of 880 opus serialized dispatches),
each time on a prompt byte-identical to the same item and question in another
repetition; that discount is already in the realized cost. The conclusion does
not depend on caching: even with every serialized input token free, bundling
stays cheaper per true catch (2.65× / 1.26× / 1.55×, above).

`data/results/costs.json` carries a disclosure string saying recorded input
tokens undercount billed input; it is superseded by the recount's correction
(D4 in `methods/RECOUNT.md`): the gap is the CLI's own helper call, not an
undercount. The artifact is kept byte-stable because the reproduction compares
against it. Per-arm table: `data/cost-per-arm.csv`.

**Spend.** Subject calls $140.87 (haiku $83.72, sonnet $21.76, opus $35.39; sum
of the public dispatch table) + adjudication lane 1 $5.79 + lane 2 $6.20 + the
keying checker (J.4) $0.95 for its first run on the superseded table + $0.58
for the re-run = **$154.39**. That is not the study's total cost: it excludes
the opus calibration probe ($9.89), preflights (~$1), leak-gate legs, the
audit, framer and checker lanes, and the recounts. Calibrating the bank cost
≈ $140.77 (Appendix A); the model calls that authored and certified it are not
included.

## Re-running it

Requirements: Python and numpy (tested with Python 3.12.3 and numpy 2.4.3 and
2.5.1; results were identical); pytest for the tests.

```
pip install -r requirements.txt
python analysis/reproduce.py              # whole chain, ~30 s; add --skip-large to skip the 1e6-draw blocks
pytest tests                              # 237 tests, incl. the end-to-end reproduction
python recount/check_agreement.py         # independent recount vs the scored table, row by row
python analysis/payloads.py               # every prompt rebuilt and checked against its recorded hash
```

`reproduce.py` re-runs the chain from the public files and compares each product
with the artifact of record in `data/results/` as parsed JSON (every key, every
digit): the payload hashes (3,675/3,675 records), scored rows (7,340/7,340
equal), `endpoints.json`, `costs.json`, `coreads.json`, `descriptives.json`,
`mc-stability.json` (including the 1e6-draw p values), and the lane
bookkeeping. All are **IDENTICAL** on the published files. Headline numbers,
expected vs got (the got column is the script's own output):

| Number | Expected (published) | Got (re-run) |
|---|---|---|
| payload hashes | every recorded SHA-256 | 3675/3675 records, 5163 payloads, keyed orders 920/920 |
| haiku S−P (H-B1) | +0.083 [+0.017, +0.150], p 0.0111, fires | +0.083 [+0.017, +0.150] p 0.0111 F |
| sonnet S−P (H-B2) | −0.046 [−0.157, +0.065], p 0.814 | -0.046 [-0.157, +0.065] p 0.8140 N |
| interaction (H-B3) | +0.025 [−0.079, +0.132], p 0.322 | +0.025 [-0.079, +0.132] p 0.3219 N |
| haiku Sq−P (H-B4) | +0.094 [+0.011, +0.183], p 0.0169 | +0.094 [+0.011, +0.183] p 0.0169 N |
| opus S−P, 90 % CI | +0.049 [−0.028, +0.125], flat | +0.049 [-0.028, +0.125]; band cell C-B-TTFLAT |
| composite cell | C-B2 | C-B2 |
| S/P $ per true catch | 3.0× / 2.1× / 2.2× | 2.97 / 2.14 / 2.24 |
| haiku off-family FA, multi-file | 0.285 vs 0.054, +0.232 [+0.181, +0.283] | 0.285 vs 0.054, +0.232 [+0.181, +0.283] |
| haiku off-family FA, single-function | 0.294 vs 0.054, +0.240 [+0.185, +0.296] | 0.294 vs 0.054, +0.240 [+0.185, +0.296] |
| extraction bracket V2, H-B1 | +0.067 [0.000, +0.133], p 0.0354 | +0.067 [+0.000, +0.133] p 0.0354 -> C-B5 |
| extraction bracket V3, H-B1 | +0.017 [−0.056, +0.089], p 0.357 | +0.017 [-0.056, +0.089] p 0.3573 -> C-B5 |
| seed sweep, 40 × 10k | H-B1 33/40, H-B4 17/40 | H-B1 33/40, H-B4 17/40 (joint (F,N) 16 / (N,N) 7 / (F,F) 17 in `mc-stability.json`) |
| 1e6 draws, seed 1512 | H-B1 0.011446, H-B4 0.016236 | H-B1 0.011446, H-B4 0.016236 |

The interaction's point estimate is 0.02546; `results/RESULTS.md` prints it as
+0.026 (rounded from a 4-decimal value, with an editor's note) and this README
as +0.025.

**What is not reproducible from these files, and why.**

- The **adjudication verdicts** (1,804 rows) are LLM judgments. They are
  published as an input table (`data/verdicts.jsonl`); everything downstream of
  them reproduces, but the verdicts themselves cannot be derived.
- The **retention decision** (940 earlier verdicts kept because the text each
  adjudicator saw equals the corrected text) needs the text shown to the first
  lane, which is lane input and stays private. The retained verdicts are in the
  table, marked `lane: retained`.
- The **recount's own code** (`recount/code/recount_v2.py`) reads those private
  lane files; it is published as reference. Its row output is published and
  checked (`recount/check_agreement.py`). The recount's economics code re-runs
  here.
- The recount's own **seed sweep** (24/30, 13/30) and **within-item bootstrap**
  (p 0.0057 / 0.0022), lane-1 figures ($5.79, 200/200, arm-guess 39.7 %), the
  first keying-checker run ($0.95, on the superseded table), and the first
  recount's figures (978 rows) are cited, not recomputed.

## What is in this repository

| Path | What |
|---|---|
| `registration/preregistration.md` | The locked registration (rev 2.4), redacted; see its header for what changed |
| `registration/amendments/` | Four dated amendments: family definitions, simulation values, opus r = 4, the corrected scoring pass |
| `registration/LOCK-ATTESTATION.md` | Private commit hashes and dates for every step, and the hashes of the unredacted locked files |
| `results/RESULTS.md` | The certified results, redacted |
| `methods/RECOUNT.md` | The independent recount as a methods note |
| `methods/BANK-CALIBRATION.md`, `methods/HARNESS-STERILITY.md` | Appendices A and B |
| `materials/items/` | The 80 frozen items (files, family, defect keys, covariates) |
| `materials/manifest*.jsonl` | Authoring and certification metadata per item: `manifest.jsonl` the 20-item pilot cohort, `manifest_s5.jsonl` the 60-item main cohort (`s5` is its internal batch label). `*_sha256` fields hash unpublished authoring transcripts. Redacted copies: each record's build-history object was removed, so they do not hash-match the frozen private files (the item files do match). |
| `materials/overlay/` | The frozen question texts, briefing, item lists (bank, C44, probe), the charge term list, structural covariates |
| `materials/rubrics/` | The adjudicator charge, system text, arm-guess addendum and keying-checker charge |
| `data/dispatches/<model>.jsonl` | One record per trial: arm, item, rep, family, question/turn order, the model's response text (`result`), completion fields, token counts, cost, served models, manipulation checks, payload hashes; Sq records carry per-turn `turns[]`. Plus the grouped-order cost probes. |
| `data/scored-rows.jsonl` | The scored table of record: one row per (tier, arm, item, rep, family question), status, hit, route, parser statuses, the scored text, and the adjudication verdict where there was one |
| `data/compact-rows.csv` | The same rows, compact: status, hit, FA class, verdict, dispatch cost (a P dispatch's cost repeats on its five rows; Sq cost is per turn) |
| `data/verdicts.jsonl`, `data/lane-verdicts.jsonl` | Adjudication verdicts of record; the corrected lane's per-stage verdicts and cost |
| `data/j4-verdicts.jsonl` | The keying checker (registration J.4): every FLAG on a clean item is checked against the diff to confirm the flagged defect is not real (26/26 NOT-REAL) |
| `data/frozen/` | The frozen key table, C44 selection with its trace, audit dispositions, shortcut-gate scores, J.4 exclusions (none) |
| `data/results/` | The analysis artifacts of record |
| `data/design/` | The pre-lock referee simulation's power values |
| `analysis/` | Parser, presence layer, scorer, statistics, endpoint chain, merge, Monte-Carlo sensitivity, payload reconstruction, reproduction driver, referee simulation, shortcut-gate responders |
| `recount/` | The recount's row output, summaries, code, and the agreement check |
| `appendix/bank-calibration/` | Per-item calibration placements behind Appendix A |
| `tests/` | Unit tests, golden-master parser vectors, and the end-to-end reproduction test |

**Not included:** raw trial files and CLI event streams, session identifiers,
stderr, adjudication lane inputs and batch maps, the trial runner (its prompt
assembly is restated in `analysis/payloads.py`, which rebuilds every payload),
the first (superseded) results table, decision ledgers, build logs, workflow
journals and agent transcripts.

**About the items.** All 80 are synthetic code written by a model; none comes
from a real codebase. Some are finance-flavored (one item models tax lots per
security; others cache FX rates, amortize a loan, price invoices). Those four
are pilot items, whose prompt left the domain open; the pilot was written on
2026-07-18 on the subscription-authenticated setup, which still passed the
CLI's scaffolding and the account email to the model
([Appendix B §2](methods/HARNESS-STERILITY.md)). A few main-cohort items also
bill or convert currency inside their assigned areas (subscription invoicing,
membership renewals, auction bids). A search for finance words therefore finds
hits, in the items and in the responses that discuss them; that vocabulary is
the stimulus, not data about anyone.

## Disclosures

- **The lock froze an empty referent.** The registration froze "the five family
  definitions" but contained no definition text. A dated amendment three minutes
  after the lock adopted the bank's own certification definitions verbatim,
  before anything consumed them.
- **Opus ran at r = 4, not the locked r = 3**, by a dated amendment before any
  opus trial, after preflights showed the upgrade cost ~$16 instead of the
  ~$130 placeholder.
- **The first results table was wrong and was superseded.** The first
  independent recount found 978 text-present rows scored as missing (one
  direction only, concentrated at haiku and in the serialized arms). A corrected
  scoring pass was registered as dated rules before its adjudication lane
  produced any verdict, and re-recounted. See [`methods/RECOUNT.md`](methods/RECOUNT.md).
- **Timing, stated exactly.** The corrected-pass rules were committed six seconds
  before the first corrected-lane verdict was written; that preflight dispatch was
  probably already in flight. Likewise the adjudicator charge text was committed
  after all trials and 24 seconds before the first lane-1 verdict.
- **The primary is fragile** (seed, extraction brackets, bootstrap unit), as
  above. H-B4 spans fires / null / reversed across legitimate readings and
  carries no weight.
- **"Item-stratified cluster bootstrap" admits two readings**; both implementers
  resampled items, and the within-item reading would fire both haiku members.
- **C44 was selected for opus-bundled interiority (≈ 0.5)**, so opus-P's 0.472
  level is by construction; only within-tier contrasts and the interaction are
  design-clean, not cross-tier levels.
- **Three false-alarm OUT-OF-BOUND stamps are ratio-clause breaches at small
  rates** (sonnet off-family single-function, opus off-family multi-file, haiku
  key-matched-wrong-family single-function); the registration gives the ratio
  clause no resolution signal.
- **The adjudicated rows are mostly haiku responses**: 1,602 of the 1,805 rows
  that reached the adjudication route. The adjudicator was claude-opus-5
  throughout. Arm-blinding was partial: labels were scrubbed, response shape
  was not.
- **The adjudicator was also a subject.** claude-opus-5 is one of the three
  tiers under test; 203 of the 1,805 routed rows are sonnet or opus answers
  (201 sonnet, 2 opus; one opus row had no answer, so 202 got a verdict).
  Exposure is limited: it ruled only FLAG / NONE / NEITHER, and whether a FLAG
  is a catch stays the mechanical key match.
- **The registration's ~18K-token scaffolding sentence is contradicted by the
  records** (Appendix B); the public copy carries an editor's note.
- Findings are about this bank, these three models, this CLI version and this
  harness shape. Family-cued questions make absolute catch rates incomparable to
  open-search review.

## The limit

**Lock-before-data is attested only by private commit hashes and dates.** The
registration was locked at commit `7bbe83e` on 2026-08-17 and the first trial
records were committed at `0bdfde6` on 2026-08-22; both are commits in a private
repository whose history is not published. An outside reader cannot verify the
order of events unless that history is published.
[`registration/LOCK-ATTESTATION.md`](registration/LOCK-ATTESTATION.md) lists every
step with its commit and time, and the hashes of the unredacted locked files, so
the claims can be checked if it is.

**The scoring rules of record were written after the data.** The extraction
rules every number of record is computed under (the corrected scoring pass:
its permissive presence grammar, §9's scored text per arm, and the V2/V3
brackets) were written on 2026-08-27. That is after all trial data (2026-08-22)
and after a first, defective table that read haiku S−P = 0.000 and was
superseded. They implement the registration's §8 routing (present-but-malformed
answers go to adjudication rather than scoring as missing), and the presence
grammar was authored from the live residual rows. They predate every
corrected-lane verdict and every corrected endpoint. They are attested only by
a private ledger commit (`ad9be8a`), whose file hash is listed in
`LOCK-ATTESTATION.md`; the public text is a restatement
(`registration/amendments/2026-08-27-corrected-scoring-pass.md`). Under them the
primary moved from 0.000 (superseded) to +0.083 (fires); the bundling-is-cheaper
conclusion holds under both tables.

## Appendix B in brief: the harness put things in front of the model

Before the bank was built, the lab checked whether its CLI harness delivered
only the intended prompt. It did not. With the subject's working directory
inside the user's home directory, the CLI's context-file discovery walked up the
directory tree and loaded the user's private global instruction file into every
call: a three-probe leak test failed 3/3 while a positive control confirmed the
test could see leaks. Moving the directory out of the home directory fixed that
channel, but a syscall-level enumeration with canaries then found more on the
subscription-authenticated instrument: the account's email address reached the
model (the leak criterion was blind to it), recent git commit subjects were
injected from any repository working directory even with all tools disabled,
account app connectors attached on every call, and each call carried
**18,237 cached input tokens of harness scaffolding against a 9-token prompt**.
This study ran with `--bare`, a metered API key, no tools, no MCP servers, a
working directory outside home and outside any repository, and per-call init
assertions; its records show a median of ≈ 1.2K (haiku) / 1.5K (sonnet,
opus) input tokens per single-question dispatch, cache fields included, and a
maximum of 4,635 (4,936 for any bundled dispatch), so that scaffolding was not
present. Details:
[`methods/HARNESS-STERILITY.md`](methods/HARNESS-STERILITY.md).

## Licences, name, attribution

- **Code** (`analysis/`, `recount/code/`, `recount/check_agreement.py`, `tests/`):
  MIT, see [`LICENSE`](LICENSE).
- **Materials, data and text** (`materials/`, `data/`, `recount/*.json*`,
  `appendix/`, `registration/`, `results/`, `methods/`, this README): Creative
  Commons Attribution 4.0 International, see
  [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt), offered to the extent
  copyright subsists. Model-written items, answers and verdicts may carry no
  copyright; where none subsists, treat them as public domain.

Built with Claude Code under my direction (Mikael Hillman-Pépin).
