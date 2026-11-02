# Pre-registration: the bundled-vs-serialized cost result on the 5.5 generation, with a plain-review arm (LOCKED v1.0, 2026-11-01)

> **Public rendering of the locked registration.** The registration was locked
> on 2026-11-01 at 20:29 -0500, before the first paid call. The first call
> attempt (21:54 -0500) was rejected by the API at $0 (Amendment A2), and the
> first paid call, a preflight dispatch, completed at 22:24 -0500. Two dated
> amendments followed the lock, both before the first record: A1 (21:53 -0500)
> and A2 (22:23 -0500; its heading date, 2026-11-02, is the UTC date). The
> order of events is attested only by the history of the private repository
> the study ran in, which is not published; the SHA-256 of the locked file is
> `831b34935125b96a4134b2539ee765ab85f15c8fa9302f6aa9cc52750a1b7fed`, so the
> claim can be checked if that history is published.
>
> This copy does not hash-match, by design. It keeps every number, rule,
> threshold, seed and registered decision. It replaces internal names (study
> codes, reviewer and role names, file paths, workflow and commit identifiers)
> with descriptive words or with the public file that holds the same bytes, and
> it drops account and credential detail. Section 13 (how the pre-lock review
> findings were folded) is condensed. Editorial insertions are marked
> `[Editor's note: ...]`. "The original study" is the study in this repository;
> "the calibration study" is the bank-calibration study of
> [Appendix A](../../methods/BANK-CALIBRATION.md).

**Status:** LOCKED v1.0, 2026-11-01. It folds two independent pre-lock reads and
a confirm read of the v0.2 draft (§13). Changes after this commit are dated
amendments appended at the end; any change after primary record #1 that touches
the frozen run configuration is illegal. No paid call happens before the §9.1
reproduction (golden-master) gate.

**Authority:**
- Approved by the study owner on 2026-11-01 with a cap of $150. The scope
  follows a private cost estimate.
- **The cap is a hard stop:** at $150 of computed spend, stop, report, and spend
  nothing more without a new approval.
- Any public extract or post goes through the owner's publishing review.

**Correction to the estimate's design line.** The estimate said "Haiku 60 items
× 4 reps". The original ran Haiku on all 80 items (60 defective, 20 clean) × 3
reps, and Sonnet/Opus on C44 (36 defective, 8 clean) × 3 and × 4. Its dispatch
counts and cost base were right.

## 1. Question

On the 5.5 models, is a bundled reviewer (P, all five defect-family questions in
one call) still cheaper per true catch than serialized reviewers (S, one family
question per call)? And how do both compare with a plain review that asks no
family questions?

Descriptive throughout (the lab's standing rule for follow-up studies). Nothing
is tested; intervals are reported, not gated.

## 2. Subjects (pinned ids; served model asserted on every response)

- **Main:** `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`.
- **Bridge (§6):** `claude-haiku-4-5-20251001`, `claude-opus-5`.
- **Adjudicator (§7):** `claude-opus-5`.

All were listed as served by the Models API on 2026-11-01. A response whose
`model` differs from the pinned id is FAILED and halts the run.

## 3. Materials (frozen; a sha256 manifest of every file below is committed at lock)

[Editor's note: the manifest was generated at build, after the lock commit, and
checked equal to the files at lock; see Amendment A1 item 4. The public files
named below hold the same bytes as the frozen private ones.]

- **Items:** the 80 frozen items of the original study, the bytes this
  repository republished (`materials/items/`: the 20-item pilot cohort and the
  60-item main cohort). Item sets per tier are the original's: Haiku all 80;
  Sonnet and Opus C44 (`data/frozen/c44-selection.json`).
- **P and S payloads:** the original assembly, byte-for-byte.
  - System prompt: "You are a helpful assistant."
  - User turn: briefing + stimulus + (the five questions in keyed order for P |
    the family note + one question for S), joined by the original separator.
    Overlay: `materials/overlay/briefing.md` and `materials/overlay/questions.json`.
  - Assembly code: this repository's `analysis/payloads.py` (`render_stimulus`,
    `keyed_order`, `assemble`), at this repository's public commit `6ec874a`.
- **Plain payload:** the calibration study's protocol, byte-for-byte.
  - System prompt: the calibration briefing, its sha256 recorded. [Editor's
    note: its text is
    `You are a code reviewer. Review the code for correctness defects.` /
    `Respond in exactly this format:` / `VERDICT: BUG or CLEAN` /
    `LOCATION: <file>:<line> or NONE` / `EXPLANATION: <one sentence>`, one
    line each.]
  - User turn: the calibration study's subject payload for the item. [Editor's
    note: "Review this code.", a blank line, then each file as `--- path ---`
    followed by a fenced Python block.]
  - This is the shape the original sent through the CLI's `--system-prompt`
    plus stdin.
- **Keys:** the frozen key table and allowances of the original corrected pass
  (`data/frozen/audit-key-table.json`).
- **Lane materials:** `materials/rubrics/` (the adjudication charge, system
  text, arm-guess addendum) and the clean-item pair-check charge
  (`materials/rubrics/j4-checker-charge.md`).

## 4. Cells and units

| Tier | Items | Reps | P | S | Plain |
|---|---|---|---|---|---|
| haiku-5-5 | 80 | 3 (0-2) | 240 | 1,200 | 240 |
| sonnet-5-5 | C44 | 3 (0-2) | 132 | 660 | 132 |
| opus-5-5 | C44 | 4 (0-3) | 176 | 880 | 176 |

That is **3,836 main dispatches**. Sq is not run.

**Order:**
- A unit is (tier, arm, item, rep). An S unit carries its five family
  dispatches, sent together.
- Units are sorted lexicographically, then shuffled with
  `random.Random(1512).shuffle`.
- A cap halt therefore leaves every cell sampled roughly in proportion.

## 5. Instrument

- **Transport:** raw Anthropic Messages API on the run's API key,
  `anthropic-version: 2023-06-01`, following the lab's existing raw-API
  instrument pattern.
  - Request body keys exactly `{model, max_tokens, system, messages,
    output_config, stream}` with `stream: true`; the Haiku 4.5 bridge omits
    `output_config`.
  - A mid-stream `event: error` on an HTTP 200 is classified like the matching
    HTTP error (overloaded → retryable, rate-limit or account-balance → limit,
    anything else → FAILED).
  - No tools, no `cache_control`, no sampling parameters.
  - **Streaming**, so usage arrives on long calls.
  - **Concurrency:** 8 workers.
  - Batch API not used: the hard-stop spend control and the proportional halt
    need synchronous calls.
- **Thinking and effort:**
  - All 5.5 tiers and Opus 5 run at `output_config.effort = "high"`, with
    thinking at each model's default (adaptive; Opus 5.5 cannot disable it) and
    display at its default.
  - Why one level: thinking bills as output on every call, so it taxes S (5×
    the calls) more than P; one shared level keeps that tax comparable across
    tiers.
  - Why `high`: it is Sonnet 5.5's default and Opus 5's API default. The
    original CLI's effort was not recorded, and this is disclosed.
  - Haiku 4.5 takes no effort parameter and runs without thinking, its API
    default.
- **max_tokens:** 64,000 on every subject call (the Haiku 4.5 maximum; the 5.5
  models and Opus 5 allow more).
  - A `stop_reason` of `max_tokens` marks the record TRUNCATED.
  - TRUNCATED is sized before record #1 by the §9.2 sizing batch, never by a
    configuration change after it.
- **Error partition (carried verbatim from the lab's earlier raw-API study):**
  - A **limit** halts the run and is never retried: HTTP 429, or any
    account-limit marker in the body whatever the status (balance, billing,
    quota). Halting is monotone.
  - **Retryable**, up to 3 attempts with backoff: 5xx/529, network errors,
    timeouts.
  - Any other non-200 response is FAILED.
  - **Other outcomes:** `stop_reason: refusal` → REFUSED; 200 with no text
    block → NO-TEXT, which scores MISSING (as in the original); served-model
    mismatch → FAILED + halt.
- **Record adapter (frozen at lock).** It maps a raw response to the fields the
  frozen scorers read:
  - `rc=0`, `is_error=False`, `subtype="success"` iff HTTP 200 with a Messages
    body;
  - `stop_reason` passed through;
  - `result` = the text blocks joined in order with "\n\n";
  - `total_cost_usd` = the usage-based cost (usage × pinned prices). A response
    that carries no usage has `total_cost_usd` = 0 in the record; any worst-case
    booking for it lives only in the cap accounting (§9.4).

  TRUNCATED, FAILED and REFUSED records are flagged terminal, and the scorers
  never see them as answers. Tier ids and prices are parameters. Scoring logic
  is unchanged; only this record plumbing is new.
- **Recorded per dispatch:**
  - request-body and payload sha256;
  - served model, `stop_reason`, the full `usage`;
  - text blocks and thinking-block shape;
  - attempt count, wall time;
  - computed cost.

## 6. Bridge (instrument context, descriptive only; no tolerance, no gate)

- **Haiku 4.5** (transport + thinking-off; the original CLI's Haiku calls
  thought heavily, setting unrecorded, so this leg differs from the original in
  thinking as well as transport).
  - Items: 12 = `rng=random.Random(1512)`; `rng.sample(sorted(defective80), 9)`
    then `rng.sample(sorted(clean80), 3)`.
  - Reps 0-1, P/S/plain: 24 / 120 / 24 dispatches.
- **Opus 5** (transport, the original top-tier model at effort high).
  - Items: 12 from C44 by the same rng continued: 9 defective + 3 clean. Rep 0,
    P/S/plain: 12 / 60 / 12.
- **Read:** catch rates, tokens per dispatch and $ per true catch, beside the
  original records for the same (item, rep, family); plain beside the
  calibration rates on the same items (Haiku only).
- **What it measures:** it bounds how much of a 4.5/5 → 5.5 difference could be
  the harness (CLI scaffolding, transport, the CLI's unrecorded defaults). It
  cannot attribute the remainder to the model alone.
- Item ids are recorded before preflight. Bridge units join the §4 shuffle: one
  sorted list of main + bridge units, one `random.Random(1512).shuffle`.

## 7. Scoring

- **P and S:** the original corrected-pass scorer, through the adapter.
  - **Rules of the 2026-08-27 amendment carried**
    ([`registration/amendments/2026-08-27-corrected-scoring-pass.md`](../../registration/amendments/2026-08-27-corrected-scoring-pass.md),
    §2): 1 (scored text per §9 of the original), 2 (presence grammar; retention
    is moot), 4 (V2/V3 extraction co-reads, printed beside the S/P ratio and
    catch rates), 5 only for the merge into post-adjudication rows and the FA
    classes (its Holm and hypothesis-test endpoint chain is not carried), and 6
    (the clean-item pair check on clean-item FLAGs before FA is read, NOT-REAL
    default). Rule 7's disclosures are carried where they apply (whole-turn
    presented blocks). Rule 8 (re-issue procedure) is replaced by §9.6-9.7.
  - **Rule 3 (lane):** carried as the original's 15% re-adjudication by a second
    fresh reader, with a third, governing reader on disagreement, plus the 10%
    arm-guess check.
  - **Not carried:** Holm, the original's primary hypothesis and its band read,
    retention, Sq.
- **P-presence audit (before any endpoint is computed):**
  - Per cell, count P rows scored MISSING while the bundle text is non-empty,
    and read every one.
  - If a family is answered in a shape outside the presence grammar, a dated
    amendment routes such rows to BORDERLINE before endpoints. That is the
    original's path for weak-tier shape drift.
  - The P-MISSING count per cell is printed either way.
- **Adjudication lane:** the original lane's assembly, as of the corrected-pass
  rules, transported over the raw API instead of the CLI:
  - item-grouped batches, seed 1512, protocol labels stripped, mechanical scrub,
    a blinding assertion;
  - the charge's one-line-per-entry format and parse;
  - 15% re-read, 10% arm guess.

  The adjudicator is `claude-opus-5`, effort high, adaptive thinking, max_tokens
  16,000, with batches in a seeded order interleaved across tiers and arms.
  - A batch whose call fails after retries, or whose verdict lines do not parse,
    leaves its rows UNRESOLVED. That is counted, never a miss.
  - The merge step accepts UNRESOLVED as a terminal non-verdict, so the row
    counts in neither the catch numerator nor the catch-rate denominator.
  - Disclosed: the lane transport changed; the judge is not a subject model.
  - **Clean-item pair check** [Editor's note: the original's keying checker,
    which checks every flag on a clean item against the diff]: `claude-opus-5`
    with the lane's parameters, the frozen pair-check charge, run after the
    lane under the lane's spend control (§9.5), a term in the projection. A
    pair-check call that fails leaves its FA pair standing (NOT-REAL default)
    and is counted.
  - **Lane batch order and concurrency:** batch ids shuffled with
    `random.Random(1512)`; 4 workers.
- **Plain:** the calibration study's frozen rule, through the adapter.
  - **Primary:** a parsed BUG verdict and at least one key (case-insensitive
    substring) in the fenced-code-stripped response; rate = hits / parseable,
    strict parser.
  - **Item inclusion:** an item enters only with parseable ≥ ceil(reps/2), the
    calibration's floor.
  - **Printed in the same row:**
    - the loose-parser rate;
    - the rate with unparseable counted as a miss (mirroring P/S, where a
      missing answer is no catch);
    - the unparseable count.

    If strict-unparseable exceeds 10% of a cell, the loose rate is co-primary.
  - The one-sentence EXPLANATION limits key matching versus the free-text family
    answers. Disclosed.
  - **False alarms (clean items):** a parsed BUG verdict on a clean item.

## 8. What prints (per tier; descriptive)

**Estimand ($ per true catch), per tier and arm:**
- **Numerator:** the sum of usage-based cost over every dispatch of the arm that
  returned usage, all items including clean, as in the original `costs.py`.
  TRUNCATED, REFUSED and NO-TEXT dispatches stay in the numerator: they were
  paid for and yielded nothing. Worst-case bookings for attempts without usage
  (§9.4) are NOT in the numerator; they print as a separate line per cell. An
  error response (4xx/5xx/529 with an error body) books $0.
- **Denominator:** the count of target-family CATCH rows.
- **Co-read:** complete units only. A complete unit is an (item, rep) whose P
  dispatch and all five S dispatches are terminal-clean (no TRUNCATED, FAILED,
  REFUSED or UNRESOLVED).
- Also printed: the spend on excluded dispatches and the incomplete-unit count.

**Bootstrap:** per tier, resample items (stratified defective / clean) with one
shared `numpy.random.default_rng(1512)` draw, paired across P, S and plain.
10,000 draws, percentile 95% CI. The ratio per draw is (ΣS$/ΣS catches) /
(ΣP$/ΣP catches). Draws with zero catches in either arm are undefined: counted,
and if more than 1% are undefined, no CI prints.

**Prints:**
1. **S/P $ per true catch, three ways:**
   - **(a) realized:** all output tokens, thinking included;
   - **(b) visible-output accounting:** thinking tokens removed from the bill,
     an estimate per the §9.2 method, outside the verb rule;
   - **(c) output-only bound:** S priced at output tokens only, against P
     realized.
2. **Catch rates, P vs S vs plain** on defective items. Per item averaged over
   reps, matched on items that pass inclusion in every arm compared; n(items)
   printed per pair. Scoring rules differ and the table says so; nothing is
   pooled.
3. **False alarms:** off-target FA for S vs P as in the original (off-family on
   defective items, FA on clean items, after the clean-item pair check); plain
   FA on its own scale. V2/V3 co-reads beside.
4. **Side by side with the original figures** (S/P 2.97 / 2.14 / 2.24;
   output-only 2.65 / 1.26 / 1.55; catch counts), with the bridge as context.
   Comparing levels across generations is not claimed, and C44's levels are by
   construction.
5. **Counts per tier × arm:**
   - TRUNCATED, FAILED, REFUSED, NO-TEXT, UNRESOLVED;
   - P-MISSING;
   - thinking tokens per dispatch;
   - spend by component.

**Cell gate:** if the combined exclusion share (TRUNCATED + FAILED + REFUSED +
UNRESOLVED-on-target) of a tier × arm exceeds 5%, that cell's $ and catch
figures print as counts only. A ratio needing that cell is withheld.

**Verb rule (read (a), and the same for (c)):**
- "still cheaper": the 95% CI lies wholly above 1;
- "now more expensive": the CI lies wholly below 1;
- otherwise "not resolved at this sample size (CI [lo, hi])".

## 9. Run sequence and gates

1. **Lock**, plus the frozen build (adapter, runner, lane transport, analysis)
   at one commit.

   **Golden-master gate, zero spend:** the new analysis path (adapter + scorers
   + estimand code), run on the original study's public dispatch tables and
   verdicts, must reproduce S/P 2.97 / 2.14 / 2.24, output-only 2.65 / 1.26 /
   1.55, and the true-catch counts P/S 105/120, 80/75, 68/75. Run on the
   calibration records, it must reproduce Haiku 4.5 plain 0.579 on the 60
   items. Any mismatch refuses the run. The public records already carry CLI
   fields, so the golden master does not exercise the adapter or the spend
   pricing; those are pinned by a test against hand-computed fixtures. The
   build's tests never reach a live call.
2. **Preflight:** one live dispatch per (tier, arm), 15 calls (3 main tiers + 2
   bridge models, × 3 arms), plus one lane batch and one pair-check call.
   - Units: the longest-stimulus defective item of the tier's set, rep 0. Lane
     batch: its routed rows, or a fixed fixture batch if none route.
   - Counted against the cap; excluded from the data.
   - **Accept path:**
     - served model equal to the pinned id;
     - `stop_reason` `end_turn`;
     - a non-empty text block;
     - usage present;
     - request-body sha equal to the frozen assembly's;
     - the adapter output scored by the frozen scorers without error.
   - **Thinking-token method fixed here:**
     - If `usage` reports thinking output separately, that field is used.
     - Otherwise: thinking = `output_tokens` minus `count_tokens` (per model,
       free) of the visible text rendered as one user message, minus that
       rendering's overhead, measured on a one-character text with that
       character's count subtracted.
     - Recorded before any main dispatch.

   [Editor's note: the API reported thinking tokens as a separate usage field,
   so that field was used.]

   **Sizing batch (before record #1; excluded from the data; counted against the
   cap; about $1):** 40 Haiku-5.5 P dispatches on the first 40 items of the
   sorted Haiku set, rep 0.
   - TRUNCATED at 2 or more of 40 (5%): stop, and register a raised max_tokens
     by dated amendment before record #1.
   - **P-presence checkpoint:** the frozen presence grammar runs on these 40
     bundles and on the preflight P responses of every tier. Any P row scored
     MISSING with non-empty text is read; a shape outside the grammar is routed
     by dated amendment here, before record #1.
   - The preflight S unit is one dispatch (the first family in keyed order). The
     bridge preflight uses the longest-stimulus defective item of its own drawn
     set.
3. **Projection gate:**
   - **Projection:** the spent preflight and sizing batch, plus per (tier, arm)
     the larger of (the original token profile scaled by the preflight/original
     output ratio) and (the preflight dispatch cost × 1.5), times the unit count,
     at pinned prices. The plain cells, which have no original token profile at
     Sonnet and Opus, use the second term only. Plus the bridge, plus the lane
     (the original routed share per tier × the preflight lane cost per row ×
     1.35 for the re-read, the third reader and the arm guess, floor $5), plus
     the pair check ($2).
   - **Threshold:** if the projection exceeds $140, the shrink order applies one
     step at a time:
     1. Bridge Haiku reps 0-1 → rep 0.
     2. Opus-5.5 reps 0-3 → 0-2.
     3. Haiku-5.5 reps 0-2 → 0-1.
     4. Sonnet-5.5 reps 0-2 → 0-1.

     If it still does not fit: stop and report.
   - Recorded before the first main dispatch.
4. **Main run (seeded order, 8 workers).**
   - **Fail-safe spend control:** before EVERY attempt, retries included, its
     worst case is reserved (input bound × in-price + 64,000 × out-price) and
     the halt is re-checked. Usage replaces the reservation on completion. An
     error response books $0. Only an attempt where generation may have
     happened without usage arriving (timeout or dropped connection after the
     send, or a stream cut after `message_start`) books its worst case, in the
     cap accounting only.
   - **Online routing:** the score table and presence layer run online (free),
     so routed rows are known as they land.
   - **Halt:** before an attempt if spent + reserved + (routed rows so far ×
     lane cost per row × 1.35) + $2 (pair check) ≥ $145. Every dispatched row
     then stays adjudicable within the cap.
   - **On halt:** the reason is recorded, and the data so far is the result,
     marked INCOMPLETE.
   - **Resume rule:** a halt on HTTP 429 or a STOP file is resumable on the same
     configuration, continuing the seeded order, after at least 10 minutes. An
     account-balance, billing or quota halt, a served-model mismatch, or a cap
     halt is terminal: report, and spend nothing more without a new approval.
   - A STOP file is polled between dispatches. No name-matched process kills.
5. **Adjudication lane, then the pair check,** under the same spend control:
   reserve and re-check before every attempt; halt if spent + reserved ≥ $149.
6. **Independent recount:** a fresh-context agent writes fresh code from this
   file and the frozen rules. Rows must agree on status and verdict, and every
   printed figure is reproduced. It makes no paid API call.
7. **Report:** plain language first, then the tables. Any public extract goes
   through the owner's publishing review.

## 10. Prices (pinned, USD per MTok, input / output; the provider's API price table as cached 2026-10-06)

| Model | Input | Output |
|---|---|---|
| haiku-5-5 | $0.10 | $0.50 (prompts ≤ 100K; every prompt in this bank is far below) |
| sonnet-5-5 | $2 | $10 |
| opus-5-5 | $4 | $20 |
| haiku-4-5 | $1 | $5 |
| opus-5 | $5 | $25 |

Thinking bills as output. Cache tokens are not expected; if they appear, cache
creation is priced at 2× input and cache reads at 1× input (conservative), and
the appearance is disclosed. Cost of record is the run's own computed figure;
the console is not read, and that is disclosed.

## 11. Fairness handlings

- **Prices:** a ratio within a tier is comparable; absolute and cross-tier
  dollars are not.
- **Thinking:** effort is pinned; thinking is reported separately; read (b).
- **Instrument:** the bridge (§6); no CLI scaffolding on the new transport.
- **Caching:** none on the new harness, while the original's premium tiers read
  cache. Read (c) does not depend on caching.
- **Public bank:** public since 2026-10-31; the 5.5 training cutoffs predate
  that.
- **Selection:** C44 levels are by construction; within-tier contrasts only.
- **Plain scoring:** its own rule, matched items, false alarms on their own
  scale.

## 12. Disclosures fixed now

- The lane transport changed.
- The judge is claude-opus-5, not a subject.
- The plain format floor was measured on Haiku 4.5 under CLI 2.1.212, which
  thought heavily (median 5,970 output tokens for 328 visible characters in the
  2,400 calibration trials). The original CLI's thinking setting is not
  recorded, so the Haiku 4.5 bridge (thinking off) is not the original's
  thinking setting.
- Cost of record is computed at list prices.
- The bank is public.
- No Sq arm.
- Effort `high` is a choice; other effort levels are not measured, and the
  original CLI's effort and Haiku thinking setting are unrecorded.
- Batch API not used.
- The bridge bounds harness effects but cannot isolate the model.

## 13. Fold of the pre-lock reads (condensed)

Before lock, the v0.1 draft was read by two independent AI agents (one the
lab's standing examiner agent, one given no framing), and the v0.2 draft got a
confirm read from the first. Every finding marked fold-required was folded:

| Topic | Folded where |
|---|---|
| estimand definition and the cost of excluded calls | §8 |
| which corrected-pass rules carry and which drop; the lane pinned | §7 |
| 429 handling, retries vs halts, concurrency | §5 |
| silent spend on timeouts; streaming; reserving every attempt, retries included | §5, §9.4, §9.5 |
| the record adapter and the golden master, and what the golden master covers | §5, §9.1 |
| the verb rule | §8 |
| lane cost inside the main halt; the lane preflight; the UNRESOLVED rule | §7, §8, §9.2, §9.4 |
| one combined exclusion gate | §8 |
| the plain parse floor and item inclusion | §7 |
| seeds, request-body keys, the bootstrap | §4, §5, §6, §8 |
| cache pricing | §10 |
| item and overlay paths | §3 |
| bridge thinking, the bridge relabel and the Opus 5 slice | §6, §12 |
| truncation sized before record #1 (max_tokens 64,000, sizing batch) | §5, §9.2 |
| worst-case bookings kept out of the headline cost | §5, §8, §9.4 |
| the pair check pinned and budgeted | §7, §9.2-9.4 |
| P-presence audit rows checked before record #1 | §7, §9.2 |
| thinking-overhead method; preflight units; projection basis; unit count 3,836 | §4, §9.2, §9.3 |
| Batch API disclosure; no-text and effort wording | §5, §12 |

**Not adopted, with reasons:**
- Complete units as the PRIMARY estimand: kept as a co-read. The primary keeps
  the original `costs.py` definition (every billed dispatch over all catches) so
  the side-by-side with 2.97 / 2.14 / 2.24 is like for like.
- "Any UNRESOLVED row on target withholds the $ figure": replaced by the
  combined 5% exclusion gate, one rule for every exclusion class.
- Dropping bridge shrink step 1: kept; the Haiku bridge is the cheapest leg to
  shrink.
- A closing reconciliation against the provider console: not adopted; the
  console is not readable by the agent running the study. The cap is enforced
  on computed list-price cost with reservations, and that is disclosed.

## Amendment A1 (2026-11-01, before record #1; from the build review)

No paid call has been made. Each item defines something the locked text left
open, or makes a rule more fail-safe.
1. **§8 cell gate:** the combined exclusion share is the larger of two ratios:
   (TRUNCATED + FAILED + REFUSED dispatches) / dispatches, and (target rows
   TRUNCATED / FAILED / REFUSED / UNRESOLVED) / target rows.
2. **§5 / §9.4 transport halts:** a subject dispatch whose retries are exhausted
   HALTS the run, resumable on the same configuration, and writes no dispatch
   record. The same applies to an HTTP 401/403/404, and to 3 consecutive
   dispatches without a usable response. This replaces §5's "FAILED and
   excluded" for exhausted retries: an instrument failure then stops the run
   instead of thinning a cell. A timeout raised in the connect or send phase
   (the request never reached the server) books $0.
3. **§9.4:** a main cap halt ends main. The lane and the pair check still run
   under the $149 lane threshold, with no resume wait.
4. **§3:** the materials manifest was generated at build and verified equal to
   the files at the lock commit (104/104). Committed with the build.

## Amendment A2 (2026-11-02, before record #1): API key replaced after a $0 halt

- **What happened:** the first preflight attempt was rejected by the API on the
  account's credit balance, on every call. The run halted as registered
  (terminal, $0 spent, no records).
- **Applied:** the run's API key was replaced. The halted spend record is
  archived unchanged, and the run chain restarted from the golden-master gate on
  a fresh spend record. The credential is not part of the frozen configuration,
  and the instrument is unchanged. Cost of record stays the run's own computed
  figure.

[Editor's note: the private amendment also records account and credential
details, and a same-day correction to one of them; both are omitted here.
Neither changes the method.]
