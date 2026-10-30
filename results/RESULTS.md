# Serialization × tier — RESULTS

> **Public copy.** The certified results of record (private, last revised
> 2026-08-28). Internal names, file paths and role names were replaced by
> descriptive words and public paths; editorial insertions are marked
> `[Editor's note: ...]` or `[ed.: ...]`. No number of record was changed;
> where the certified text overstates what its own artifacts show, an
> `[ed.: correction ...]` note says so in place (four places: the FA co-read
> under V3, twice; the cache reading; the equal-dollars read). The numbers
> the analysis chain computes (Holm family, cells, stamps, FA co-read,
> extraction co-reads, economics, descriptives, the Monte-Carlo sensitivity
> including the 1e6-draw p values, and the lane-2 bookkeeping) are recomputed
> from the public files by `analysis/reproduce.py`. Numbers that come from
> private inputs (lane-1 figures, the retention-magnitude split, the first
> recount's figures, the recount's own seed sweep and within-item bootstrap)
> are cited, not recomputed; the README lists which is which. "The analyst"
> is the AI agent that ran the study pipeline (built and run with Claude
> Code); "the recount" is a separate AI agent working from fresh code and
> context. Its numbered check layers are A1–A9 (A9: the economics recount).
> "Belt" means a runtime assertion (the blinding check `assert_blinded`, or
> the price-table check); "FAUNRES-form" is the registration's FA-UNRESOLVED
> stamp (§11.4).

> **CERTIFIED — RECOUNT-AGREES.** Independent re-recount of the corrected chain
> (blind-first, 2026-08-28: blind pass 5920136, report 099c5c1;
> economics A9 blind 021eaa8 / report 59a2b33 — see `methods/RECOUNT.md`): 7,340/7,340 rows
> identical on status / hit / key-matched-wrong-family / verdict of record /
> lane label; every Δ, CI and p reproduced to the last printed digit (10k and
> 1e6); member states, composite, band, stamps, V2/V3 co-reads, FA classes,
> J.4, economics (8/8 cells) all AGREE. Two recount divergences classified as
> a recount under-read of the two-clause FA bound (D1) and a counting
> convention (D2); two economics disclosure corrections (D3 price-table
> label, D4 residual mechanism) are folded below. **Every number here is
> citable, and the fragility disclosures travel with the verdict** — with
> one bookkeeping exception the recount names (§8.5): the lane/J.4
> instrument costs ($5.79 / $6.20 / $0.95) are analyst-counted, not recounted.
> History: the 08-22 issue was superseded by the first recount
> (RECOUNT-DIVERGES, 978 text-present rows scored MISSING — `methods/RECOUNT.md`;
> the superseded issue is private commit 6fb13a7). This issue is computed from
> the corrected pass pre-registered 2026-08-27 (rules 1–8,
> `registration/amendments/2026-08-27-corrected-scoring-pass.md`, private
> commit ad9be8a) and executed at 7e9d89e. [Editor's note: the original line
> said the rules were registered "BEFORE the first lane-2 dispatch". The
> records show the rules commit at 23:41:42 and the first lane-2 verdict
> written at 23:41:48; the rules predate every lane-2 verdict and every
> corrected endpoint, but the first (preflight) dispatch was probably already
> in flight. See the amendment's timing note.]
> [ed.: "pre-registered" here means before the corrected lane's verdicts, not
> before the data. The rules were written 2026-08-27, after all trial data and
> after the first, superseded table; see README §The limit.]

Registration: `registration/preregistration.md`
(rev 2.4, LOCKED @ 7bbe83e) + amendments `2026-08-17-family-definitions.md`,
`2026-08-17-sim-of-record.md`, `2026-08-22-opus-r4.md`
(opus n 3→4, before any opus trial) and `2026-08-27-corrected-scoring-pass.md`.
Freeze: d76feb1. Trials commits: haiku 0bdfde6 (1,680 records),
sonnet e13bd4c (924), opus d658edd (1,056) — 3,660 records, **zero
instrument failures** (§10 unreliability limb 0% in every cell; absence
reported, not inferred). Realized subject spend $140.87; adjudication
lane 1 $5.79 + lane 2 $6.20; J.4 checker $0.95 + $0.58; ceiling $1,050.
Registered instrument for every interval and p below: item-stratified
cluster bootstrap, cluster = item, **10,000 resamples, seed 1512**
(registration §11 preamble — both pinned in the registration, not code
constants); one-sided p, ≤0 convention; Holm m = 4, α = 0.05.

**Recount status: RECOUNT-AGREES — certified 2026-08-28 (re-recount 099c5c1 + economics A9 59a2b33).**

## Verdict of record (registered cells, §12)

**Composite cell C-B2**, keyed (H-B1 = **F**, H-B3 = N): *benefit real at
the weakest tier; tier gradient unresolved; per-tier $/true-catch governs
any charter text; no interaction claim.*

**Band cell C-B-TTFLAT** — Δ_opus5 (S−P over C44) = +0.049, 90% CI
[−0.028, +0.125] ⊆ ±0.20: top tier measured flat at the ±0.20 grain (no
finer claim); **bundling legal at the top.** Opus guards silent.

**Qualifiers (recorded inside the fired cell, never cell-splitting):**
H-B2 = N (mid-tier null). H-B4 = **N** — Sq−P = +0.094, one-sided p
0.0169 against its Holm step-2 threshold 0.016667: misses by 0.0002 under
the registered instrument, and the registered instrument is the verdict of
record in both directions (see "Fragility" — the same qualifier reads F at
1e6 draws and R under V3).

**What the cell text does with the fragility below.** C-B2 routes every
adoption sentence to per-tier $/true-catch, and P wins that axis at every
tier under every extraction variant (3.0× haiku, 2.1× sonnet, 2.2× opus).
The alternative cell the co-reads reach, C-B5, issues no adoption either.
**The cell flip C-B2 ↔ C-B5 therefore changes no adoption text**: bundled
dispatch is the charter reading either way; what moves is only whether a
haiku-tier serialization benefit is *declared* (+0.083, F) or *unresolved*
(N). That is the honest grain of this study's primary.

## Fragility — measured, disclosed beside the verdict, never a re-decision

Two independent axes were pre-registered or pre-declared as descriptive,
and both move the primary. [ed.: "pre-registered" and "registered" in this
section, including the co-reads in (a), mean before the corrected lane's
verdicts, not before the data; see the note under the header and README
§The limit.] The seeded 10k run remains the verdict of
record; nothing here upgrades or demotes a member.

**(a) Extraction latitude — registered co-reads (`data/results/coreads.json`,
definitions in the corrected-pass amendment, rule 4, fixed before the lane's
verdicts existed):**

| Variant | rows relabeled | H-B1 (Δ, 95% CI, p) | H-B4 | States | Cell |
|---|---|---|---|---|---|
| V1 primary (§9 text per arm) | 0 | +0.083 [+0.017, +0.150] 0.0111 | +0.094 [+0.011, +0.183] 0.0169 | F,N,N,N | **C-B2** |
| V2 P-maximal key scope | 33 | +0.067 [0.000, +0.133] 0.0354 | +0.078 [−0.006, +0.167] 0.0423 | N,N,N,N | C-B5 (INCONCLUSIVE) |
| V3 label-respecting punitive | 171 | +0.017 [−0.056, +0.089] 0.357 | −0.239 [−0.339, −0.144] 1.000 | N,N,N,**R** | C-B5 (RITUAL-at-haiku) |
| legacy loose-primary | 38 | = V1 | = V1 | F,N,N,N | C-B2 |
| legacy NONE-scope | 0 | = V1 | = V1 | F,N,N,N | C-B2 |

V2 widens P's keying surface to the whole bundle (P catches 105 → 108 at
haiku) and the H-B1 lower bound lands on exactly 0.000. V3 removes every
permissive-route S/Sq recovery whose turn carries no asked-family marker
(haiku Sq target catches: 60 unlabeled vs 17 labeled) and reverses H-B4.
The registered extraction is V1; V2 and V3 bracket it in opposite
directions, and **the C-B2 firing rides on extraction latitude** — the
benefit is real under the registered reading and unresolved under either
bracket. FA-state moves under the brackets: V2 haiku class-3 sf OUT→IN;
V3 haiku class-1 sf and class-2 mf OUT→UNRESOLVED — every other FA state
(including both haiku class-2 OUT-OF-BOUND states) holds. [ed.: correction:
the parenthetical contradicts the sentence before it. Of the two haiku class-2
OUT-OF-BOUND states, only single-function holds under V3; multi-file is the
class-2 mf OUT→UNRESOLVED move just named (0.251 vs 0.054, 95% CI [0.150,
0.246], lower bound exactly on the bound). Both hold under V2.]

**(b) Monte-Carlo — non-registered sensitivity (`data/results/mc-stability.json`, producer `analysis/mc_stability.py`):**
the registered draw count is 10k, and two members sit within MC noise of
their Holm thresholds. Forty alternative 10k seeds: H-B1 fires 33/40 (p
range 0.0098–0.0139 vs 0.0125); H-B4 fires 17/40 (0.0141–0.0189 vs
0.016667); joint states (F,N) 16 / (N,N) 7 / (F,F) 17. At 1e6 draws, seed
1512: H-B1 p 0.01145, H-B4 p 0.01624 — both under threshold. This is
disclosed as descriptive only: H-B1 stays F and H-B4 stays N on the
registered instrument, exactly as V2/V3 do not demote C-B2. **H-B4 spans
{F, N, R}** across the 1e6-draw run, the registered run and V3 — the same
"parse-latitude-fragile N/R/F" the 08-22 recount recorded from the other
side; the qualifier is unresolvable at this design's grain and carries no
weight in any downstream text.

**(c) Resampling-unit reading — surfaced by the 08-28 re-recount:** §11's
"item-stratified cluster bootstrap, cluster = item" was read by both
implementers (the original analysis and the independent recount) as cluster-resampling
ITEMS; under the alternative WITHIN-item reading (resample reps within
each item) both H-B1 and H-B4 fire comfortably (p 0.0057 / 0.0022). The
verdict of record stays on the item-cluster reading both derived; the
registration's wording admits the other, and the ambiguity is
decision-relevant for H-B4. Recorded for the next registration, not
re-decided here.

## Holm family (m = 4, one-sided, α = 0.05; H-B1 fired; no guard fired)

| Member | Contrast (pool) | Δ | 95% CI | p (1-sided) | Holm adj | State |
|---|---|---|---|---|---|---|
| H-B1 | haiku S−P (surviving 60) | **+0.083** | [+0.017, +0.150] | 0.0111 | 0.0444 | **F** |
| H-B2 | sonnet S−P (C44 36) | −0.046 | [−0.157, +0.065] | 0.814 | — | N |
| H-B3 | (S−P)_haiku − (S−P)_opus (C44 36, shared draw) | +0.026 [ed.: the point estimate is 0.02546, i.e. +0.025 at three decimals as printed elsewhere in this repository; this table printed +0.026 after rounding a 4-decimal value] | [−0.079, +0.132] | 0.322 | — | N |
| H-B4 | haiku Sq−P (surviving 60) | +0.094 | [+0.011, +0.183] | 0.0169 | (step-2 thr 0.0167) | N |

Raw target catches (denominators counted, never derived): haiku S 120/180,
P 105/180, Sq 122/180; sonnet P 80/108, S 75/108, Sq 70/108; opus P
68/144, S 75/144. Pooled rates (guard check, all interior): haiku P/S/Sq
.583/.667/.678 · sonnet .741/.694/.648 · opus P/S .472/.521.

## Stamps and co-statements (all registered)

- **FORMAT-DEGRADED** still stamps all three haiku cells — the stamp is
  defined on the PINNED strict grammar (regime pin closed at record #1;
  parser untouched): noncompliance 57.7% (P), 31.9% (S), 43.9% (Sq); every
  other cell ≤ 15.5%. **Co-stated, as the recount required:** under the
  08-22 recount's live-shape grammar the same cells read 0.3% / 4.5% /
  13.3% (that recount's figure, attributed — not re-derived on 08-28),
  and the corrected lane RECOVERED the noncompliant rows rather than
  scoring them absent — haiku P 692 noncompliant rows → NONE 624 / FLAG 67
  / NEITHER 1; S 383 → 250 / 133; Sq 527 → 327 / 200; **zero true-missing
  rows at haiku** (the study's one true-missing row is opus P
  mf-sign-06 rep 3, units). The stamp measures the pinned grammar's
  strictness against haiku's answer shapes, not answer absence; the
  catch readings survive stamped (§8/§12).
- **H-B4 named-bias co-statement (§9 iii)**: arm-blinding is partial —
  structural tells survive any token scrub. Measured scrub pressure, lane
  2: 3 tokens across 864 presented texts (lane 1: 1 across 1,334). The
  corrected pass adds a disclosed **shape-blinding asymmetry**: S/Sq rows
  present their whole turn while P rows present a family segment
  (corrected-pass amendment, rule 7a) — V3 is the registered bracket on it.
- **INVERSE-AT-TIER**: no tier stamped (no S−P 95% CI entirely below 0;
  sonnet [−0.157, +0.065]).
- **Criterion-shift stamp** (criterion vs competence): **fires at haiku under the registered
  reading** — hits CI above 0 ([+0.017, +0.150]) AND class-2 FA CIs above
  0 (both splits). Stated in two parts because the two legs differ in
  robustness: the HITS leg is V1-only (V2 lower bound 0.000, V3 CI spans
  0 → the stamp does not fire under either bracket); the FA leg (some FA
  class CI above 0) holds under **every** variant at **every** tier
  (`data/results/coreads.json` → `criterion_shift_stamp`). The registered stamp is the primary's; the
  robust finding is the FA-side multiplication below.
- **CLEANFAIL**: not triggered — J.4 removed zero cleans.

## FA co-read (§11.4 — C-B2 routes adoption to $/true-catch, so these stamp the charter reading as qualifiers, never a cell)

**The substantive FA finding, robust across V1/V2/V3: serialization
multiplies false alarms at haiku ~5× for a +0.08 catch gain.** Off-family
FA (class 2, S vs P): mf 0.285 vs 0.054 (Δ +0.232, 95% CI [+0.181,
+0.283]) and sf 0.294 vs 0.054 (Δ +0.240, [+0.185, +0.296]) — both
**OUT-OF-BOUND** on the absolute clause (CI entirely above the 0.15
bound), both splits, under every variant. [ed.: correction: both splits under
V1 and V2; under V3 single-function stays OUT-OF-BOUND (0.277 vs 0.054) and
multi-file is UNRESOLVED (0.251 vs 0.054, CI [0.150, 0.246]) —
`data/results/coreads.json`. The ~5× multiplication holds under all three.]
Clean any-FLAG (class 1): sf
0.667 vs 0.367 **OUT-OF-BOUND** (Δ +0.300, [+0.167, +0.433]); mf 0.767
vs 0.433 UNRESOLVED (Δ +0.333, [+0.100, +0.600] spans the bound; n = 10
clean mf items). Key-matched wrong-family (class 3): mf 0.048 vs 0.000
IN-BOUND; sf 0.045 vs 0.003 OUT-OF-BOUND — a **ratio-clause** breach at
a small base (absolute Δ 0.042, well inside 0.15; FA_S > 2·FA_P fires).
Read with the hits: S raises willingness to flag more than it raises
discrimination — the criterion-shift shape, now with a measured hit
component beside it.

Premium tiers: FAUNRES-form states dominate as the registration predicted
at lock (pre-lock A-11.3: 4 clean clusters per class cannot separate the
bound). The two premium OUT-OF-BOUND class-2 states are **ratio-clause
breaches at small rates** (sonnet sf 0.035 vs 0.010; opus mf 0.093 vs
0.030) — absolute differences 0.025 and 0.063, both inside the 0.15
absolute bound. Read them as small-base multiplications, not large
absolute effects. **Registered-reading caveat (re-recount D1):** the
registration supplies no resolution signal for the RATIO clause — the
scorer gates both clauses with the one CI it has (on the absolute
difference), so these three ratio-only OUT-OF-BOUND stamps (with haiku
class-3 sf, P base 1/354) are point-estimate stamps with no separability
test; a stricter reader labels them FAUNRES-form. Adoption text is
unchanged either way (C-B2 routes to $/true-catch); the clause's CI
treatment is registered before the next FA co-read.

**J.4 (§10)**: all 26 distinct (clean item, family) flag pairs in the
corrected table checker-verified against the diffs: **26/26 NOT-REAL** (12
verdicts seeded from pairs whose claimed-findings set was byte-identical
to the 08-22 table, 14 re-run, $0.58; `data/j4-verdicts.jsonl`).
The clean certifications stand; zero items leave the FA cells. The one
new pair the recount named (clean-sf-02, units) produced NO FA row: the
lane of record ruled that turn NEITHER ("opens with FLAG but concludes
sound; contradictory") → SILENT — a disclosed divergence from the recount
parser's FLAG reading, resolved by the registered lane, not by the analyst.

## Economics co-axis (§6/§6a, three reconstructions; `data/results/costs.json`)

$/true-catch (realized · cache-cold · cache-grouped — grouped-order probes
measured ZERO cache reads at every tier, so cache-grouped = realized,
probe-anchored; haiku engaged no cache at all, the bank-calibration pilot's 0/400 replicated):
[ed.: correction: the probe is one item × five questions per tier. "No cache at
all" holds for the haiku probe (no cache writes either), not for the haiku main
run: most Sq turns 3–5 (639 of 720) read the resumed session's cache, and 2 of
1,200 haiku S dispatches read cache. At the premium tiers 224/660 sonnet-S and 340/880
opus-S dispatches read cache, each on a payload byte-identical to the same item
and question in another rep; that discount is inside the realized figures.
Caching does not carry the conclusion: with every S input token priced at zero
(output tokens only), P still wins per true catch 2.65× / 1.26× / 1.55×.]

| Cell | realized | cold | catches | $/catch (realized) |
|---|---|---|---|---|
| haiku P | $11.22 | $10.68 | 105 | **$0.107** |
| haiku S | $38.05 | $35.73 | 120 | $0.317 |
| haiku Sq | $34.45 | $40.39 | 122 | $0.282 |
| sonnet P | $4.86 | $4.36 | 80 | **$0.061** |
| sonnet S | $9.75 | $9.21 | 75 | $0.130 |
| sonnet Sq | $7.15 | $10.72 | 70 | $0.102 |
| opus P | $10.19 | $9.35 | 68 | **$0.150** |
| opus S | $25.20 | $25.13 | 75 | $0.336 |

**Equal-dollars read (§11.3)**: the marginal dollars S spends over P
($26.83 haiku, $4.89 sonnet, $15.01 opus), spent instead on more P reps,
buy ~251 (haiku), ~81 (sonnet), ~100 (opus) additional catches versus S's
marginal +15 / −5 / +7. Bundled dispatch dominates the serialized shape at
every measured operating point, under every extraction variant
(recount-verified S/P $/true-catch: 2.97 / 2.14 / 2.24 under V1; 3.05 /
2.17 / 2.28 under V2; 3.30 / 2.14 / 2.24 under V3). The "linear in reps"
column is an UPPER bound on what extra P reps buy (re-catches of an
already-caught defect are counted; the deployment quantity is concave and
item-bounded) — P dominates on it either way. [ed.: correction of scale: the
upper bound is loose by an order of magnitude. Counted in distinct defective
items, P's reps already found 48/60, 35/36 and 30/36, so extra P reps can add at
most 12 / 1 / 6; S found 53 / 32 / 29 (+5 / −3 / −1 over P).]

**Residual disclosure (mechanism corrected by the recount, D4):** the gap
between realized cost and the token-formula cost is the CLI's haiku HELPER
call on each session's first invocation — $6.97 of $140.87 (4.9%: haiku
$3.31, sonnet $1.70, opus $1.96), present on 1,845 of 1,848 sonnet/opus
P+S records and exactly $0 on the 532 units whose `served_models` lists
the subject alone — NOT an unmeasured scaffolding undercount (the subject
token fields fully account for the subject's billing). Because it is
per-dispatch it loads on S (6.6% / 18.6% / 8.1% of the S−P marginal
dollars); removing it entirely leaves P winning 2.93× / 2.00× / 2.18×.
Cache-cold is a floor under the CLI-billed table. [ed.: the disclosure string
inside `data/results/costs.json` still reads "recorded input_tokens undercount
billed input (CLI scaffolding)"; this paragraph supersedes it. The artifact is
kept byte-stable because the reproduction compares against it.]

**Price-table disclosure (D3):** rows are priced at the CLI-billed table
(haiku $1/$5, sonnet $3/$15, opus $5/$25 per Mtok in/out); the belt
validates that pin against the CLI's own billing, not against the
provider's published list, and the registration pins no table. A provider
reference cached before the trials lists sonnet-5 at $2/$10; console
per-model billing is unverified. If the console billed 2/10, sonnet
SUBJECT spend is overstated 1.5× (P $0.042, S $0.092, Sq $0.069 per
catch; S/P 2.21×) — sonnet stays the cheapest tier per true catch and no
sentence in this document moves.

**Cross-tier caveat (selection):** C44 was selected for opus-P
interiority ≈ 0.5 (§4.4), so opus-P's 0.472 *level* is by construction
and cross-tier LEVEL comparisons are confounded; only the S−P contrasts
and the interaction are design-clean.

## Descriptives (§11.3, CI-only, labeled; `data/results/descriptives.json`)

- Catch decomposition, haiku P: unconditional 105/180 = 0.583 vs
  conditional-on-well-formed 80/130 = 0.615; haiku S 120/180 = 0.667 vs
  83/120 = 0.692 — the format channel carries signal in the same
  direction in both arms; the primary stays the deployment-real
  unconditional read.
- S−Sq: haiku −0.011 [−0.094, +0.072], sonnet +0.046 [−0.056, +0.148] —
  **labeled the compound (repetition − self-anchoring), never "the
  repetition component"** (D-1). The 08-22 haiku +0.256 was the instrument
  artifact; the corrected compound is null at both tiers.
- Sq−P sonnet: −0.093 [−0.204, +0.019] (CI only). Sonnet−opus gradient
  leg: −0.095 [−0.236, +0.049].
- Turn-1 anchor check (instrument check): haiku Sq target-at-turn-1
  22/35 vs S 120/180; sonnet 18/23 vs 75/108.
- Output-token association (D-2, descriptive only): |r| ≤ 0.15 in every
  cell (largest haiku S −0.149) — S's catches do not co-move with longer
  answers.
- HIT-ALT: 4 total (haiku S 1, haiku Sq 1, sonnet S 1, sonnet Sq 1).
  FLAG-count distributions, within-P position slope, per-family
  heterogeneity (haiku-scoped, D-11), within-response error phi are in the
  artifact.

## Adjudication lane (§9; the instrument behind 1,804 of 7,340 rows)

Verdict-resolution reading (recorded at build time, before any verdict
was read): adjudicators resolve FLAG/NONE/NEITHER only; the catch unit
stays mechanical (§5.2 hit = FLAG ∧ keys_matched on the row's §9 text) so
arm contrasts never measure a reader rubric; keys withheld from readers;
NEITHER composes as the MISSING disposition.

**Corrected-pass composition (corrected-pass amendment, rules 1–3):** of the
7,340 question-rows, 5,535 strict-PARSED; 1,805 reached the BORDERLINE
lane — 940 verdicts RETAINED from lane 1 (presented text byte-equal under
the registered normalization; FLAG 81 / NONE 859), 394 RE-LANED (text
changed), 470 NEWLY PRESENT (scored MISSING on 08-22; recovered by the
permissive presence rule: 471 candidates, 470 present), 1 true-missing.
**Retention magnitude (re-recount Q3):** of the 940 retained verdicts,
459 are byte-equal and 481 are retained ONLY because the registered
normalization drops fence-only lines and collapses whitespace (475 P, 4
S, 2 Sq); under byte-equality the lane-2 queue would have been 1,345, not
864. The rule was registered before dispatch (ruling 2) and the recount
found no retained row whose normalized-equal text differs in content; one
lane-1 row (adj-1182) was retained on `presented_block` equality while
the text the adjudicator saw carried a scrub token — immaterial
(clean-item FLAG either way), disclosed.
**Lane 2:** 864 rows (adj-2001..adj-2864, ids non-colliding with lane 1),
80 blind batches, verdicts FLAG 340 / NONE 523 / NEITHER 1. **Second-reader
re-adjudication 130/130 agreement, zero tie-breaks. Arm-guess: 86/86
UNKNOWN** (true arms P 27 / S 31 / Sq 28) — the reader declined every
guess; reported against chance, NEVER read as "blinding verified" (§9 iv;
lane 1 guessed 63/133 and was 39.7% correct among those). Scrub belt 3
tokens placed, belt refused nothing post-build. Cost $6.20 (primary $3.27,
second reader $1.02, arm-guess $1.91). Adjudicator claude-opus-5 sterile metered
(frozen CLI 2.1.212; served_models also lists haiku from the CLI's own
scaffolding calls, never from a verdict). Lane 1 (1,334 rows, second reader 200/200,
$5.79) stands as the source of the 940 retained verdicts.

**P judging surface (re-recount Q1/Q2):** a P segment runs to the next
different-family marker, so the LAST family's segment absorbs any
bundle-level closing prose — on the 242 P lane-2 rows, 17 segments
mention another family by name; all 17 were judged NONE on an explicit
`NO-DEFECT-<f>` assertion (P lane-2 verdicts NONE 204 / FLAG 37 / NEITHER
1). Of the 199 S/Sq turns without an asked-family marker, ZERO carry a
marker for any other family — they are bare answers to the only question
asked, not answers to a different one. V3 brackets the S/Sq label risk
decisively; nothing brackets the P segment's length (the bracket is
one-sided). A P-minimal co-read (marker line + first block) can only
REMOVE P catches, i.e. can only raise H-B1 — it is the non-threatening
side and was not run; recommended as an analysis-only addition.

Disclosures carried from rule 7: (a) shape-blinding asymmetry (above);
(b) lane cost re-sized after retention (queue 864, not 1,334); (c) tier
concentration — 1,602 of the 1,805 lane rows are haiku, so every lane
property (including 86/86 UNKNOWN) is predominantly a haiku-shape
property.

## Robustness and recount

Registered extraction co-reads: **DIVERGENT** — V2 and V3 both reach C-B5
(table above); the 08-22 "INVARIANT" line is retracted for cause (those
variants shared the primary's extraction — a check that could not fail).
Legacy loose-primary (38 rows) and NONE-scope (0 rows, keying collision
fixed) match V1. Recount surface: `analysis/scorer.py` `keyword_rederivation`
(keyword-only re-derivation entry point, §9); presence layer
`analysis/presence.py` with 42 live-vector tests including the 470/471 pin.
**Instrument note:** the first corrected descriptives artifact
read the superseded costs table for the equal-dollars line (a hardcoded
path; haiku 91-catch denominators) — caught by the analyst reading its own
numbers before this issue, fixed with an explicit `--costs` argument and
a recorded `equal_dollars_read_costs_source`; the recount confirms the
shipped descriptives are consistent with the shipped costs table.

**Independent re-recount (an independent agent, blind-first, 2026-08-28): RECOUNT-AGREES.**
Fresh code from rules text + raw artifacts reproduced every row (7,340/7,340)
and every printed digit; exact p agreement is algorithmic identity under the
registered seed (both implementations arrive at the same draw from §11's
text), so the recount's MC independence comes from its own seed sweep
(H-B1 24/30, H-B4 13/30; 1e6 identical to six digits). Divergences: D1 FA
bound-state labels on three ratio-only cells (the recount under-read the
two-clause bound; the registered reading stands, caveat above); D2 V3
"relabeled" 171 vs 199 (status-changed vs demoted-including-no-ops; same
consequential set); D3/D4 economics disclosure corrections (folded above).
Blindness caveat the recount states itself: the 08-27 rule text carried
the presence and retention counts, so A1/A2 were verification-against-a-
known-target; A3–A9 were blind. Methods note:
`methods/RECOUNT.md`; row-level output `recount/recount-rows.jsonl`.

## What this study does NOT claim (§19/§20)

No claim finer than ±0.20 on top-tier flatness; no cross-tier level
claims (C44 selection); no interaction claim (H-B3 N); no mechanism
identification — the H-B4 qualifier spans F/N/R across legitimate
readings and carries no weight; the haiku serialization benefit is
declared only under the registered extraction and is unresolved under
both registered brackets; the FA multiplications at premium tiers are
small-base ratio effects with no registered separability test for the
ratio clause; no claim about provider-billed sonnet cost (CLI table;
console per-model billing unverified); no bracket on the P judging
surface's length (V3 is one-sided); findings are about THIS bank, THESE
tiers, THIS harness shape (sterile `--bare`, frozen CLI 2.1.212).
