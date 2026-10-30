# Pre-registration — serialization × tier: does one-question-per-dispatch beat the K-question bundle, and does the gap shrink up the tier ladder?

> **Public copy of the locked registration.** The lock is private commit
> `7bbe83e` (2026-08-17 15:03 -0400). The locked file's git blob is
> `d1c70fc2b64dca750e3eb1ec75c4d0e833e4d283` and its SHA-256 is
> `a88aa5472a9f6acc17bc4874e6e6d50ed4271620b81b947d31906c66567f02f4`; the file
> is byte-identical at the head of the private repository. This copy does not
> hash-match, by design: internal names were replaced by descriptive words
> (study codes, internal rule numbers, role names, file paths), each content
> removal is marked `[redacted: internal reference]` with a note of what kind
> of content was removed, and editorial insertions are marked `[Editor's note:
> ...]`. Those substitutions in a few places required rewording the sentence
> around them (§2, §6, §15, §17); in §4.4 two synonyms for selection slots now
> read "slots", and the budget table's abbreviations are spelled out. No number,
> rule, threshold or registered decision was changed. "The analyst" is the AI agent that ran
> the study pipeline (built and run with Claude Code); "Phase A" is the bank-calibration study and "Phase B"
> this study. Dated amendments are in `amendments/`; the hashes are listed in
> `LOCK-ATTESTATION.md`.

**STATUS: LOCKED rev 2.4 — locked 2026-08-17: r=3 allocation,
ceiling $1,050, frozen-CLI transport; the r=4 option was surfaced with
its power numbers and DECLINED at lock; an independent pre-lock review
returned LOCKABLE at 4b4ddfd after a three-round review (19 blockers
closed; full disposition map §22b; the review document itself is not
published).** From this commit the registration text and the five family
definitions are FROZEN; changes ride dated amendments only. Build →
selftest → gates → preflight → record #1, in that order (§21). No
material is authored and no trial runs before lock.

Synthesized from three independent design sketches under a three-judge
panel (§22a) and revised under the independent pre-lock review (§22b).
[redacted: internal reference] (study id, repository paths, and the internal routing of
results).

## 1. Question

On the frozen 80-item bank (built and calibrated by the bank-calibration study), does a reviewer asked ONE family-directed
review question per dispatch (serialized, fresh context each) catch more
key-matched defects than the same reviewer asked all K questions in ONE
dispatch (bundled) — and does that gap shrink as model class rises, per a
salience-budget prior recorded at design time (§2)? Treatment is dispatch topology only;
question texts, stimulus bytes, taxonomy knowledge (§4.2), scorer, and
instrument are held fixed. A third shape (one question per turn, same
resumed session) decomposes the mechanism confirmatorily.

## 2. Motivation and design prior (priors are design inputs, never evidence)

[redacted: internal reference] — this section quoted a private design note and a
design prior verbatim; it is withheld from the public copy. In substance,
the prior predicted: K review questions BUNDLED in one dispatch (P) vs one
per dispatch (S), at matched total tokens, gives S − P > 0 with a TIER
INTERACTION (the gap grows as model class shrinks, ≈ 0 at the top tier) —
an "effective salience budget" that shrinks with model class (behavioral
capacity only, no interpretability commitment).

**The decision this buys:** reviewer-fleet topology commonly assumes S > P
unmeasured. If the tier interaction is real, decomposed dispatch pays
exactly at cheap tiers and bundling is legal at the top; if refuted,
decomposition is priced ritual. The prior's "matched total tokens"
phrasing is departed from — §6 carries the departure, a second registered
departure (from the design sketches' convergence), and both defenses.

## 3. Scope narrowings and framing disclosures (disclosed, never absorbed)

- **Factorial narrowing.** The registered Phase-B factorial
  (an internal research program) is tier × encoding × family. This opening
  study is NARROWED to **tier × serialization**: encoding is pinned (the
  frozen bank-calibration briefing + this study's frozen question overlay, one level);
  family is pinned same-family (the `gemini` CLI is dead — `UNSUPPORTED_CLIENT`,
  verified 2026-07-16; a DeepSeek serialization arm would confound family
  with transport/parser). Encoding×serialization and the family axis stay
  queued (§18). Disclosed overlap, not synthesized: the P-arm bundle is
  structurally the "checklist" pole of the encoding axis — this study
  measures topology at fixed question text; encoding stays a later factor, and a later
  encoding study must not double-count this study as independent evidence.
- **Top-tier choice.** This task class (diff + directed question, no
  execution) is document-derivable; Opus-5 is therefore the registered top
  tier, and claude-fable-5 enters only via the named conditional gate
  G-FAB (§13). [redacted: internal reference] (an internal policy study cited here).
- [redacted: internal reference] (the internal practice-guidance surfaces this study was
  designed to inform).
- **Corpus discipline:** all trials post-date 2026-07-24, so the lab's
  date-partition rule is satisfied by construction; asserted per batch.

## 4. Design

### 4.1 Subject tiers and regime pins

Three metered tiers + one conditional wing. All subject batches pin **full
resolved model ids, never aliases** (aliases lag deployment), asserted per
batch via `modelUsage`, never self-report. The literal resolved id strings
are pre-record-#1 constants set at lock ([editor's note: recorded as
`claude-haiku-4-5-20251001`, `claude-sonnet-5`, `claude-opus-5`]).

- **haiku (dense):** the measured weakest tier (grade landscape 33/60
  interior, methods/BANK-CALIBRATION.md) — where the prior predicts the largest
  gap. Runs the FULL 80-item bank.
- **sonnet-5 (dense):** the fleet's workhorse tier and the chartering
  decision's main consumer; richest measured cost rows. Runs the common
  subset (§4.4).
- **opus-5 (sparse, HARD FLOOR r≥2 per arm on the common subset):** the
  top-tier anchor for the interaction — the interaction cell is the study's
  reason to exist; **the ceiling bends before this floor does** (§17). No
  invented cost anchor exists or is permitted for this tier: the registered
  pre-batch probe REPLACES the estimate (measured-budget rule). The
  vintage-flagged opus-4-8 strong-tier calibration row is refused as an
  anchor across the vintage partition (a design-note constraint).
- **fable-5 (conditional wing only):** runs iff gate G-FAB fires (§13);
  sparse, sequential, priced at gate time with its own probe.

Instrument pins (the regime, one-way door at record #1; per-tier output
files, one regime per file): a frozen copy of Claude Code CLI 2.1.212
— **re-registered at THIS lock**, `--version` asserted on the invoked
binary, never the auto-updating symlink; **the graduated invocation flags
`--bare --tools "" --strict-mcp-config`** —
`--tools ""` is what makes §4.2's "the stimulus is read once" enforceable
and keeps the git-cwd channel shut, so the flags pin beside the CLI version;
a dedicated metered API key (metered auth — which also kills the OAuth
residue channel; the CLI-scaffolding residue disposition is carried in
§16); resolved model ids; `runner_commit`.

### 4.2 Arms — three dispatch shapes, equalized taxonomy knowledge

Question texts, stimulus bytes, per-question answer schema, briefing, and
**taxonomy knowledge** are identical across arms (parity gate, §16). Every
arm's briefing states the five-family partition explicitly: *"this diff is
under review for five defect families (boundary, comparison, exception,
sign, units)"* — arm S/Sq dispatches continue *"you are asked about family
f only"*. Without this, P subjects know a five-family response set exists
while S subjects do not — a response-set-structure difference that acts on
both scored sides (pre-lock review A-4): allocation behavior on the hit
side, multi-family flagging asymmetry on the FA side. Equalizing the
briefing removes the information asymmetry; the RESIDUAL behavioral channel
(a P subject may satisfice within its single dispatch — flag once and
NONE the rest — where S faces five independent decisions) is intrinsic to
the bundle topology, named as a scope limit in §19, and priced by a
registered descriptive read: **the per-item FLAG-count distribution per
arm** (§11.3), the direct signature of allocation/satisficing behavior.

The arms differ ONLY in dispatch topology:

- **Arm P (bundled):** one dispatch = stimulus + all K=5 question blocks,
  question order randomized per trial (§7). The stimulus is read once; K
  questions compete for one context.
- **Arm S (serialized):** K dispatches = stimulus + ONE question block each,
  fresh sterile context per dispatch. Each question gets the whole budget —
  which physically includes a fresh full read of the stimulus. Position
  taken (§6): the fresh read is part of the deployed treatment, not a
  confound to be matched away.
- **Arm Sq (sequential-turn):** ONE session, K turns via `--resume` — turn k
  = question k only (turn order randomized per session, §7); the stimulus is
  presented at turn 1 and read once. An earlier study's two-request
  resume machinery, generalized to K turns.

**Sq self-anchoring channel, disclosed by name (never silently folded into
"serialized"):** a resumed session carries the model's OWN prior answers in
context across turns — a THIRD mechanism channel, qualitatively distinct
from P's simultaneous bundle competition and from S's fresh-context
repetition. A COMPLETE guard is impossible inside the P/S/Sq triangle (the
fourth cell — one read, sequential, not self-anchored — cannot exist in a
resumed session), so the channel carries three registered instruments:

1. **The turn-1 anchor check (named guard):** Sq turn order is randomized,
   so the TARGET question lands at turn 1 in ≈1/5 of sessions — and a
   target answered at turn 1 has no prior answers in context, making it
   structurally an S dispatch on the same stimulus. **Sq(target@turn-1) vs
   S is a registered instrument check** (haiku ≈36 target obs, sonnet ≈21;
   n stated, thin, and read as a check, never a test): agreement localizes
   the self-anchoring channel to turns ≥2; disagreement says the Sq
   instrument differs from S for reasons unrelated to sequencing.
2. Within-Sq turn-position slope + cross-turn conditional error propagation
   (registered exploratory, §11.3).
3. Cell-level naming: every Sq contrast is read as (one-at-a-time
   presentation + self-anchoring) vs its comparator (§12 qualifiers, §19).

**Mechanism decomposition is CONFIRMATORY:** Sq−P (bundle-competition side,
self-anchoring disclosed) rides the Holm family at haiku (H-B4, §11.1);
S−Sq is a registered descriptive CI-only co-read at both dense tiers —
**labeled correctly: S−Sq = (fresh-context repetition) − (self-anchoring),
a compound with the self-anchoring channel entering at opposite sign, not a
clean "repetition component"** (pre-lock D-1). Sq runs at both dense tiers;
the confirmatory member sits at haiku. The Sq arms are **LAST in the
registered cut order** (§17). **Contested-provenance record (pre-lock
D-13):** the judge panel split 1–1 on Sq's containment (J2: confirmatory,
cut last; J3: exploratory, haiku-only, cut first — cost-shaped, the Sq arms
are ~29% of core requests on placeholder pricing). The analyst adopted J2; the
contest is recorded here because the cut order is where it re-litigates
under budget pressure, and cutting Sq voids H-B4 (slot kept), never
re-reads it.

### 4.3 K, the family taxonomy, and what freezes when

**K = 5.** One question per defect family of the bank (`boundary`, `comparison`,
`exception`, `sign`, `units`) — the bank's own complete partition, exactly
balanced 12-per-class over the 60 defective items. Per-question ground truth
exists mechanically (§5.2). K is fixed by the taxonomy, not chosen by power —
disclosed as a reuse constraint; it sits inside the deployed range of
per-mandate discriminating claims (an earlier study's review cards: 4–13
claims, median 9).

**The five one-line family DEFINITIONS freeze AT LOCK** (they are design —
the bank's own hypothesis-neutral taxonomy — not stimulus-contaminated
material). The QUESTION TEXTS that embed them are authored blinded
POST-lock (§5.4) and freeze at the freeze commit. This ordering is what
makes §5.3's audit well-posed (pre-lock A-9): the audit rules against the
locked definitions, not against question texts it cannot see.

### 4.4 Common item subset (the interaction rides ONE pool) — C44, selection rule REGISTERED

**The tier-interaction endpoint (H-B3) is computed over ONE registered item
subset common to every tier it compares. No per-tier pools.**

**Common subset C44: 36 defective + 8 clean (4 clean-mf, 4 clean-sf).**
Sized up from rev 1's 24 defective on the referee simulation (§11.5): at 24
items H-B3 carries 0.36 power at δ_int=0.20 / 0.55 at 0.25 — near-chance on
the study's reason to exist; at 36 items (an analyst option-pricing wrapper over
the referee's committed generators, referee-confirmed pre-lock)
power rises to ≈0.49 / ≈0.74 at opus r=3, and the opus r=4 upgrade
(≈0.59 / ≈0.80, ≈+$130 placeholder) is flagged as a lock-time
option.

**Selection algorithm (registered; deterministic given the probe record):**

1. Candidate pool: the audit-surviving defective items (§5.3).
2. Interiority score per item: score = |catch_rate − 0.5| from the
   **cued-format Opus-5 calibration probe at r = 3** (§4.4a), lower = more
   interior. (Re-review R-1: at r=1 every item scores exactly 0.5 — a
   constant key that silently degenerates selection to the tie-break; r=3
   attains {0, ⅓, ⅔, 1} → scores {0.5, 0.167}, a real interior/extreme
   split.) The probe is a SUBJECT-DISPATCH lane and runs INSIDE the
   study's sterile envelope, after the leak-gate SET (final-verify R-3;
   §21 steps 4–5).
3. Strata: the 10 cells of (5 families × mf/sf). Per-stratum quota: 3
   (=30), plus 6 remainder slots.
4. Within each stratum, rank by (interiority score ascending, then item id
   lexicographic ascending) and take the top 3. If a stratum has <3
   surviving items, its shortfall moves to the remainder pool.
5. Remainder slots fill from the not-yet-selected items ranked bank-wide by
   the same (score, id) key.
6. Clean side: 4 clean-mf + 4 clean-sf by item id lexicographic order (no
   difficulty signal exists or is needed for cleans).
7. If the surviving pool cannot fill 36 defective (<36 survive the audit)
   the subset is the full surviving pool, disclosed; below 20, C-B-BANKFAIL
   (§12).

The 44 item ids + the full selection trace commit at freeze and are the
list of record.

**4.4a The calibration probe runs in the DEPLOYED CUED FORMAT at r = 3**
(pre-lock A-3; rep count per re-review R-1 — r=1 cannot discriminate):
Opus-5, r=3 over the audit-surviving defective items (≤180 dispatches),
each item presented in arm-P format with the frozen question overlay — the
regime the strata must describe, WHICH INCLUDES THE ENVELOPE (re-review
R-3): the probe runs inside the study's sterile config dir, on the frozen
binary, the metered key, and the pinned model id, AFTER the leak-gate SET
passes — a probe outside the envelope measures a different regime and
miscalibrates C44 undetectably. The probe DOUBLES as the opus-P pricing
pass and is preflight-gated: its FIRST dispatch is the opus-P single live preflight
through the runner's real accept path (`--max-dispatches 1`); only after
that live accept does the remainder fan out; its realized per-dispatch
cost replaces the opus-P placeholder before the ceiling re-price (§17). §19's non-comparability rule (cued ≠ open-search)
is thereby honored instead of violated: Phase-A open-search bins are NOT
used for off-ceiling calibration; they remain strata labels only
(within-grade contrasts, lock-condition 4). The probe is **INSTRUMENT
data — endpoint-excluded** (lock-condition 2, §14); it informs selection
but never enters an endpoint. Because the probe is cued-format arm-P, it
also functions as the opus preflight's pricing companion; its per-item
catches are recorded and sealed with the selection trace. Timing: after
overlay authoring + checker + audit, before C44 selection and freeze (§21).

### 4.5 n-allocation (unbalanced by measured cost; fixed n at lock)

| tier | items | arms | reps r | dispatches (P / S / Sq-sessions) |
|---|---|---|---|---|
| haiku | full bank 80 (60 def + 20 clean) | P, S, Sq | 3 | 240 / 1,200 / 240 (=1,200 turns) |
| sonnet-5 | C44 (36 def + 8 clean) | P, S, Sq | 3 | 132 / 660 / 132 (=660 turns) |
| opus-5 | C44 | P, S | 3 registered; cut floor r=2 (§17) | 132 / 660 / — |
| fable-5 (iff G-FAB) | C44 defective 36 | P, S | 1 | 36 / 180 / — |

Target-question observations per arm (defective items, the primary
denominators — all stated over the AUDIT-SURVIVING pool, §5.3): haiku
≤180 (surviving×3, 180 iff 60 survive); sonnet/opus-5 108 at r=3 / opus 72
at r=2. Metered core ≈ 4,884 requests. Per-cell n fixed at lock; the
registered cut order (§17) is the only pre-record-#1 adjustment path;
resume fills missing keys only, up to registered n.

## 5. Task bank and materials freeze

### 5.1 Bank choice

**The bank-calibration study's 80-item frozen bank** (`materials/manifest.jsonl`
@ `e9c6c55` + `materials/manifest_s5.jsonl` @ `5f5e032`, private commits) + a NEW frozen
family-question overlay. No new per-item card authoring lane this study.
[Editor's note: the public manifests are redacted copies — each record's
build-history object was removed — so they do not hash-match those commits.
The 80 item files in `materials/items/` are byte-identical to the frozen
ones. `manifest_s5.jsonl` and its `cohort: "s5"` field name the 60-item main
authoring cohort; `manifest.jsonl` is the 20-item pilot cohort.]
Rejected alternatives:

- *An earlier study's 15 in-band mined items:* **burned** — unblinded by
  another study 2026-08-17; the burn rider's temporal mitigation expired
  unexercised.
- *That earlier study's unburned remainder (39):* difficulty-extreme by construction, cards
  never freeze-pinned, stage-2 catch rates already measured (stratifiable,
  not blind supply) — named as the SUCCESSOR bank, not built here (§18).
- *New bank:* measured keying cost ≈$6.27/candidate lane-only, $295/net-item
  full-cycle — the dearest path; the cheapest bank that answers the question
  already exists.
- *Hybrid:* two key regimes = two parsers = the recount surface doubled,
  for no power gain.

**Construct-validity compromise, stated (not a free reuse win):** the
bank does not natively decompose per-question — one `defect_keys` list is
one question. The overlay imposes a CLASS-LEVEL decomposition (family
lenses), coarser than the
item-specific "series of questions" the design prior imagined. The
item-specific decomposition exists (an earlier study's discrimination
appendices) and is registered as the follow-on bank (§18). Family-cued
questions also hint the search space in ALL arms symmetrically — the arm
contrasts are clean, but absolute catch rates are not comparable to
Phase-A open-search rates (§19).

### 5.2 What a question physically is

Question q_f, byte-identical across arms and items: *"Does this diff contain
a defect of family f — ⟨one-line frozen family definition⟩? If YES, name the
file, location, and mechanism in free text. If NO, output NO-DEFECT-f."*
Answer schema, identical in every arm: one fenced block per question,
`Q-<family>: FLAG|NONE — <mechanism>`. No per-arm token caps; the schema
text is identity, not token forcing (§6). Taxonomy-knowledge equalization
rides the briefing (§4.2).

**Per-question ground truth — mechanical:** for a defective item, the
target-family question keys TRUE, scored by the item's curated +
decoy-reharvest-enriched `defect_keys` (the bank-calibration study's
validated placement-hit instrument); off-family questions key FALSE subject to the §5.3 audit; clean
items key FALSE on all five. **Per-question hit = FLAG verdict ∧
`keys_matched` non-empty.** Verdict-only is measured DEAD at the weakest
tier (bank calibration: verdict-only median 1.000, 49/60 items at 1.00) — no verdict-only
endpoint exists anywhere in this registration.

### 5.3 Pre-freeze single-family key-exclusivity audit (registered, with a certification rule)

The single-TRUE/four-FALSE key design is UNVERIFIED on the bank — some of
the 60 defective items may be legitimately describable under >1 family (the
mf-sign-01 key list and an earlier study's NO-MATCH-as-different-real-defect
class are the warning datapoints). **Every defective item is audited pre-freeze
against the LOCKED family definitions (§4.3) by a blinded audit lane.**

**Certification rule (the lab's clean-certification pattern; pre-lock A-6):**
EXCLUSIVE is the permissive disposition (it makes off-family FLAGs
FA-eligible) and is certified like CLEAN is: **three blinded readers per
item, EXCLUSIVE only on unanimity.** Any reader producing a credible
second-family description (family named + mechanism sentence tied to the
diff) forces MULTI-FAMILY ALLOWANCE naming that family. Readers who rule
neither (item defective but family-unassignable under the locked
definitions) vote DROPPED; **DROPPED is the disposition on 2-of-3 DROPPED
votes; a 1-1-1 or otherwise unresolved split routes to a SECOND
fresh-context panel (round 2 of a FIXED two-round maximum) whose majority
governs — the analyst never rules an item** (lock-condition 1: fixed trigger,
fixed round count; blinding preserved through the graduated blinding
linter, §5.4). Dispositions, reader records, and rounds commit with the key
table:

- **EXCLUSIVE** — unanimous; off-family FLAGs are FA-eligible.
- **MULTI-FAMILY ALLOWANCE** — the key table marks named additional
  families TRUE-ALLOWED; an off-family FLAG matching keys on an allowed
  family scores HIT-ALT (co-reported), never FA. **Each allowance shrinks
  that item's off-family FA denominator (4 − |allowed|), stated per item in
  the key table and consumed by §11.4's denominators** (pre-lock D-7).
- **DROPPED** — item leaves the study pool pre-freeze, disclosed with count.

**Every defective-item endpoint denominator is the SURVIVING pool** (H-B1
is registered over the audit-surviving bank, not a fixed 60 — pre-lock
D-5/A-6), with §11.5's resolution co-stated at the BANKFAIL floor. If drops
leave <50 defective items bank-wide or <20 in C44's candidate strata, cell
**C-B-BANKFAIL** fires: the bank does not lock (§12).

### 5.4 Blinded lanes and framer isolation

The overlay author (question-framer), the audit lane, and the adversarial
checker are blinded per the frozen-materials rule: never shown the treatments, the hypotheses,
or — **registered explicitly — the measured-grade table or the
structural-covariate manifest** (the leak is closed at the framer stage).
An adversarial checker pass (blinded) verifies no question text leaks its
own answer or any item-specific token. **The graduated blinding linter (from
the bank-calibration study) runs on every lane payload** (lock-condition 1's "blinding preserved
through the linter" — carried verbatim in §14). Lanes tier per the standing
tiering rule: checked-downstream lanes ride sonnet; terminating verdict
lanes ride the session model.

### 5.5 Shortcut gates (the shortcut-gate amendment — scored at the REAL scorer's layer, with the LOCK CONSEQUENCE)

Three degenerate responders are registered here by DESIGN + consequence
rule; scores are computed and PUBLISHED at FREEZE, before trial #1 (they
consume the overlay question texts and key table, which are authored
blinded POST-lock per the frozen-materials rule — a score "at lock" is impossible by
construction).

- **ZC-1 (content-blind keyword responder):** FLAGs the family whose
  keywords appear in diff hunk headers/identifiers; never reads semantics.
  Scored at the verdict layer AND through the real scorer.
- **ZC-2 (template-targeted responder):** keyed on the FIXED family-question
  template itself — base-rate play on the 1-of-5 target structure and the
  3:1 defective:clean ratio; fixed per-family FLAG/NONE policy; never reads
  the diff. Scored at the verdict layer.
- **ZC-3 (composite responder — the strongest the authors can build;
  pre-lock A-5 + re-review N-e):** COMPOSES the shortcut surfaces: family
  selection by ZC-1's keyword policy (with ZC-2's base-rate policy as a
  registered variant, the better of the two published), PLUS the author's
  best family-generic mechanism string per family ("off-by-one in the loop
  bound" for every boundary question, etc.), scored **through the real
  scorer** (FLAG ∧ `keys_matched` against the curated key lists) — the
  shortcut-gate amendment demands the BEST zero-comprehension heuristic's score against
  the set AS SCORED, and the primary endpoint's layer is key-match, not
  verdict. A flag-all-five policy is not used (its FA load suppresses J
  and reads the gate weaker than the bank is). "Shortcut-resistant by
  construction" is exactly the claim this measures instead of asserts.

**Lock consequence:** any item class (mf/sf × defective/clean, per question
family) cleared at **J ≥ 0.8** by ANY registered responder at its scored
layer is re-authored or dropped in **ONE replacement round** (fixed trigger:
the J threshold; fixed round count: one; blinding preserved through the
linter — lock-condition 1); a class still cleared after the round →
**the bank does not lock** (C-B-BANKFAIL). A class cleared by a degenerate
responder measures a shortcut, not the construct.

### 5.6 Structural-covariate manifest (carried Phase-A graft)

The structural-covariate manifest is committed alongside the measured-grade
table used for strata, under the study materials, so structure↔difficulty
stays recomputable — **labeled exploratory** (covariates are strata
decoration, never difficulty levers; a design-note constraint).

### 5.7 Freeze contents

One freeze commit, before trial #1, hash on every trial record: (1) the 5
question texts (embedding the definitions frozen at lock); (2) the
item×question key table incl. audit dispositions + per-item FA denominators;
(3) the audit certification record (readers, rounds, votes); (4) the C44
item-id list + full selection trace + the cued calibration probe record;
(5) the structural-covariate manifest; (6) ZC-1/ZC-2/ZC-3 code + published
scores + any replacement-round record; (7) golden-master scoring vectors
(§9). Trial-time scripts freeze with the study; analysis helpers live in
separate non-frozen files.

## 6. The matching rule — NATURAL SHAPE, cost as a measured co-axis

**Rule:** primary endpoints ride NATURAL-SHAPE dispatches — no artificial
token forcing between arms. Question texts, stimulus, and answer schema are
identical; output length is unconstrained beyond identical schema
instructions; per-trial `total_cost_usd` + full token totals (input, output,
**cache-read, cache-write — required fields in every record**, §16)
ride EVERY record; **$/true-catch per arm×tier appears in the primary
tables** as the measured economics co-axis, in the three registered
reconstructions of §11.3 (realized / cache-cold / cache-grouped — §6a).

**TWO registered departures, disclosed in the same form:**

1. **From the design prior's letter** ("matched total tokens").
2. **From the design sketches' unanimous convergence** (pre-lock A-14/2.1,
   disclosed here as the review requires): all three independent sketches
   converged on *matched per-question output budget*, and judge J2
   instructed "adopt as-is." The analyst REVERSED that convergence. The
   sketches' rule holds answer opportunity constant; the analyst's objection
   stands registered: a cap is itself an artificial operating point, and at
   weak tiers it converts truncation artifacts into fake treatment effects.
   The registration locks this choice knowing it overrides a 3-of-3 convergence
   plus an explicit judge instruction — that is the disclosure. The
   replacement instrument is weaker than rev 1 claimed (next paragraph),
   which is disclosed rather than papered.

**Rationale (registered):** the chartering-economics decision deploys each
shape at its NATURAL operating point — nothing in production matches tokens,
and the token difference is constitutive of the treatment (S's K fresh
stimulus reads ARE the whole-budget-per-question manipulation; equalizing
them deletes it). Mechanism identification comes from the Sq arm; the
**output-token covariate read is registered as a DESCRIPTIVE ASSOCIATION
only** (pre-lock D-2): output tokens are post-treatment, and conditioning
on a mediator does not identify a direct effect — the read describes
whether S's catches co-move with longer answers; it does not price the
"S just wrote more" alternative, and no cell keys on it.

**Alternatives analysis (design rationale, carried from the sketches):**

- *Equal-tokens:* S's input repetition is structural — enforcement requires
  padding P or truncating S, both artifacts; and tokens ≠ dollars under
  caching (measured: premium passes 4–8× BELOW cache-cold projections in
  the bank-calibration study; an earlier study's $-premium 1.196× vs
  token-premium ~28%).
  Rejected.
- *Equal-dollars:* $ is an outcome; matching on an outcome distorts the
  contrast and forces unequal n (power confounded with arm). Answered
  instead by a registered exploratory read: Δcatch/Δ$ vs the same dollars
  on more P reps. Rejected as a constraint, carried as a read.
- *Matched per-question output budget (the sketches' convergent rule):*
  holds answer opportunity constant; rejected per departure 2 above, with
  the truncation-artifact objection registered and the reversal disclosed.

### 6a. The cache-grouping reconstruction (pre-lock A-10)

Arm S's five same-item dispatches share a cacheable prefix (briefing +
stimulus); arm P has no intra-item prefix reuse. §7's block randomization
scatters same-item calls beyond cache TTL — an ordering chosen to kill the
arm×time confound, which then DECIDES the realized cache discount. A
deployed S fleet would group by item and realize whatever discount exists.
The chartering number must not be an artifact of the randomization, so
**three reconstructions are registered for the economics co-axis:**
(i) **realized** (as dispatched, block-randomized); (ii) **cache-cold**
(from token splits at list prices, no cache credit); (iii) **cache-grouped**
(deployed-shape estimate: recomputed from recorded token splits under the
provider's published caching rules for item-grouped dispatch, ANCHORED by a
registered **grouped-order S probe** — one item × 5 questions dispatched
consecutively per tier, measured cost recorded — run in the preflight lane).
The known facts both ways are stated at lock: the bank-calibration pilot
measured 0/400 cached (item payloads median ≈887 tokens vs the 4,096-token
cache minimum), while the bank-calibration strong-tier passes measured a
real same-item-draw discount on premium passes; whether the CLI system-prompt contribution clears the
minimum under `--bare` is exactly what the probe measures.

## 7. Trials (fixed n, no peeking, no optional stopping)

Batch-level dispatch order: block-randomized across arms × items, seed 1512
(house seed; NEVER arm-blocked — arm×time confound), resume-stable (the
complete key list is shuffled once under `random.Random(1512)`, filled keys
skipped in place — the parent runner's derivation).
**Within-trial orderings are KEYED DERIVATIONS, not stream consumption**
(pre-lock A-12): within-P question order =
`random.Random(f"1512:P:{item_id}:{rep}")`; within-Sq turn order =
`random.Random(f"1512:Sq:{item_id}:{rep}")` — resume-stable by construction
and re-derivable from (seed, key) by an independent recount; the
realized order is ALSO recorded per record and the recount asserts
equality. Sequential fixed-n per tier; ceiling-guarded batches
(`--ceiling-usd` per batch); single-writer sink with O_EXCL lock; STOP-file
halt; no name-matched process kills. All committed outcomes are
publishable; a null is a result at full prominence.

## 8. Manipulation checks (dispositions registered; subject non-compliance is DATA, never a re-draw)

- **MC-P1 (P bundle integrity):** the P response contains 5 parseable answer
  blocks. **Format failure is a SUBJECT-BORNE outcome, not instrument noise
  (pre-lock A-14): a bundled reviewer that cannot emit five well-formed
  answers is exhibiting a real cost of bundling, and the design measures it
  instead of discarding it.** Disposition, registered: a block that is
  MISSING entirely (no text for that question) scores NON-CATCH for that
  question-row — in deployment, no answer is no answer; a block that is
  PRESENT but fails the strict grammar goes through the loose parse and
  then the BORDERLINE lane (text exists; it gets judged). Both count into
  the **format-noncompliance endpoint**: per-arm×tier noncompliance rate +
  the arm-differential contrast (§11.3) — a P-side deficit is read as a
  measured bundling cost in the chartering economics, co-stated with a
  catch-rate decomposition (unconditional, the primary, deployment-real;
  and conditional-on-well-formed, descriptive). Subject format failure
  NEVER feeds C-B-UNREL (§10) — it cannot take down the family; at
  noncompliance > 25% in an arm×tier cell that cell's readings carry a
  registered **FORMAT-DEGRADED stamp** (the catch measurement is stated as
  format-dominated; readings survive stamped).
- **MC-S1 (S/Sq single-answer integrity):** mirror for single-question
  responses.
- **MC-Q1 (charge integrity):** every dispatch carries its frozen question
  block(s) byte-exact (sha256 asserted); zero item-specific tokens in any
  charge (term-list grep). Violation = INSTRUMENT failure (builder/runner
  own payloads).
- **MC-SQ1 (session integrity, Sq):** each turn resumes the recorded session
  id; turn-k payload contains question k only (payload sha256 per turn);
  turn-(k−1) completion timestamp precedes turn-k issue. Violation =
  INSTRUMENT failure.
- Instrument-class failures (timeout / credit / session-limit /
  `api_error_status`) partition by cause owner and are never item verdicts
  (§16).

## 9. Scoring

- **Scored text:** per question, the matching answer block of the arm's
  response (P: the block for that family; S: the single response; Sq: the
  block from that question's turn — turn text only, never the session
  transcript). Registered here, removing the analysis-time degree of
  freedom. Sq rows are scored on the turn text AS EMITTED (deployed
  behavior): a Sq answer that names its defect only by reference to a prior
  turn scores on what the turn text itself contains.
- **Mechanical scorer first:** per-question key-match (FLAG ∧ `keys_matched`
  non-empty against `defect_keys`, HIT-ALT per §5.3 allowances) — an
  extension of the bank-calibration study's validated placement-hit scorer. Mechanical
  text-containment is NOT trusted beyond the curated key lists (the
  mechanical-residue channel measured degenerate in an earlier study: 0/52).
- **BORDERLINE lane, arm-blinded (an earlier study's scheme carried; scrub REDESIGNED
  per pre-lock A-8):** trials group BY ITEM (card/keys load once per
  batch); within each item batch, rows are shuffled (seed 1512) and
  stripped of arm labels. **Scrub design:** (i) scrub families are SCOPED —
  they fire only OUTSIDE backticked code spans (the remedy from an earlier
  study's scrub false-positive finding, adopted in its recorded sense: that
  finding's actual lesson is that scrubs false-positive on
  subject-domain text and destroy mechanism-bearing material; the rev-1
  citation inverted this and is corrected here); (ii) the registered
  families cover turn-reference and cross-question tells INCLUDING ordinal
  and soft variants ("earlier in this session", "as I said", "turn N",
  "Q3 of 5", "(3/5)", "as above", "per my earlier note", "again",
  "revisiting", "as in Q-⟨family⟩"), replaced by a NEUTRAL inline token
  (never a bracketed "[scrubbed]" that advertises censorship — the
  aggravator that finding named); (iii) **arm-blinding is registered as PARTIAL**: structural
  tells (restatement/quotation volume differs between fresh-read rows and
  bundle/turn≥2 rows) survive any token scrub, and scrub false-positives
  land asymmetrically on Sq rows — both carried as a NAMED BIAS DIRECTION
  on H-B4 (a scrub-induced miss scores against Sq), co-stated wherever
  H-B4 is read; (iv) the belt (`assert_blinded`) runs on the presented
  file; the 10% arm-guess check runs as request 2 of the same resumed
  session (an earlier study's arm-guess protocol), accuracy reported against chance, null accuracy NEVER
  read as "blinding verified". Rubric frozen at lock; adjudication only
  after ALL trials complete; 15% re-adjudication by a fresh reader;
  disagreements route to a second fresh reader whose verdict governs — the
  analyst never breaks ties.
- **Golden-master gate at freeze:** regression vectors for the multi-answer
  shapes — prose prefix before a block; a standalone `NONE` inside a bundled
  response that must not censor sibling blocks; numbered pseudo-entries;
  Sq-turn recaps of earlier answers preceding a real block. PASS required to
  freeze.
- **Recount commitments:** parser-robustness co-reads (strict/loose scoring
  variants AND the NONE-search scoping variant) — conclusions shown
  invariant or the divergence disclosed; a keyword-only re-derivation entry
  point exposed for recounts; independent recount (fresh code, raw records)
  before any result is cited; final-table denominators COUNTED,
  never derived from interim figures. **Directionality check registered for
  the build step:** the graduated parent bootstrap (an earlier study's
  endpoint script) computes two-sided p; this study's family is one-sided
  directional — the fork's selftest
  asserts the one-sided adaptation on a golden vector (referee-sim flag).
- **Fold:** merge-never-shrink, an earlier study's fold guard copied verbatim (seeds from the
  existing file; refuses a resolution-count shrink without `--rebuild`).

## 10. Exclusions and validity

Every question-row is SCORED (missing block → NON-CATCH; malformed-but-
present → loose parse → BORDERLINE — §8); format-noncompliance is an
ENDPOINT, counted per cell and reported. **The two §10 limbs have different
cause-owners and different dispositions (pre-lock A-13 + A-14): SUBJECT
format failure feeds the format-noncompliance endpoint and, above 25% in a
cell, the FORMAT-DEGRADED stamp — it never voids a cell or blocks the
family. INSTRUMENT failure alone triggers unreliability: per arm×tier
cell, instrument-failure ATTEMPT records ÷ total attempt records (final
rows + instrument-failure attempts, retained with billed cost, consuming
no key) > 10% → C-B-UNREL,** reported as such, never imputed, and blocks
every cell that consumes it (the resume/halt machinery exists to prevent
this state; if it fires anyway, consuming members take the state-G
"unreliable" disposition, stated). J.4 rule
carried verbatim for cleans: a keying-checker-verified real finding on a
clean item is never an FA; the item leaves every FA cell; denominators
recompute, disclosed; survivors <4 in a clean class → that class's FA read
reports low-power per the carried rule.

## 11. Hypotheses, endpoints, tests

Definitions: catch = per-question placement-hit (§5.2) on the TARGET
question of defective items; unit = item-rep target-question observation;
denominators = the audit-surviving pool (§5.3); all bootstraps
**item-stratified cluster bootstrap, cluster = item, 10k resamples,
registered seed 1512** (graduating an earlier study's endpoint script —
with the one-sided adaptation, §9); 95% CIs on directional members; the §11.2 band read uses
its own registered interval.

### 11.1 Primary family — ONE Holm family, α = 0.05, m = 4, ALL members directional (one-sided); a voided member keeps its slot

- **H-B1:** catch_S − catch_P > 0 at **haiku**, over the surviving
  defective bank (≤60 items).
- **H-B2:** catch_S − catch_P > 0 at **sonnet-5**, over C44's 36 defective.
- **H-B3 (tier interaction — the chartering payload):**
  [catch_S − catch_P]_haiku − [catch_S − catch_P]_opus-5 > 0, **both legs
  computed over the SAME C44 36-defective subset** (§4.4).
- **H-B4 (mechanism decomposition, confirmatory):** catch_Sq − catch_P > 0
  at **haiku**, over the surviving defective bank — the bundle-competition
  side, read with the self-anchoring channel and the §9 partial-blinding
  bias direction co-stated.

**There is NO Holm member for the top-tier-flat prediction** — it is an
equivalence claim and lives in the §11.2 band read.

### 11.2 Top-tier band read (interpretation, never a test) — TOST at the conventional α

Registered equivalence band **B_eq = [−0.20, +0.20]** on Δ_opus5 =
[catch_S − catch_P]_opus-5 over C44's 36 defective. **Registered choice
(pre-lock A-11/D-14, made visibly):** the band read uses the **90% CI**
(TOST at α = 0.05, the standard equivalence convention). Rev 1's 95%-CI
form was TOST at α = 0.025/side; the referee simulation showed it reaches
only 0.513 under a TRUE flat at r=3 (24 items) — a coin-flip instrument.
The 90% convention narrows the interval ≈16% and, with C44's 36 items,
materially raises reach at zero added spend; the referee re-simulation
(§23) states the rev-2 reach number of record. Exactly one fires whenever
the opus guards are silent:

- **C-B-TTFLAT:** Δ_opus5 90% CI ⊆ B_eq — top tier measured flat (at the
  ±0.20 grain; no finer claim); bundling legal at the top.
- **C-B-TTLIVE:** Δ_opus5 90% CI excludes 0 (sign read in the cell) — the
  top tier has NOT reached the asymptote; G-FAB-eligible when positive.
- **C-B-TTSPAN:** neither — top-tier read UNDECIDED; no flat claim, no live
  claim.

### 11.3 Descriptive / exploratory (CI only, labeled; never Holm'd)

S−Sq at haiku and sonnet — **labeled as the compound (repetition −
self-anchoring), never "the repetition component"** (D-1); Sq−P at sonnet
(CI only); the sonnet−opus gradient leg; **the turn-1 anchor check
(Sq(target@turn-1) vs S, §4.2 — an instrument check with stated n)**;
within-P position-in-bundle slope; within-P and within-Sq conditional error
correlation; **the per-item FLAG-count distribution per arm (§4.2 — the
allocation/satisficing signature)**; per-family heterogeneity — **scoped to
haiku** (at C44 the premium tiers carry ≈7 items/family; uninterpretable —
D-11); **the format-noncompliance endpoint (§8): per-arm×tier rate,
arm-differential contrast (a P deficit = a measured bundling cost, priced
into the chartering read), and the catch decomposition
(unconditional primary vs conditional-on-well-formed)**; the output-token DESCRIPTIVE ASSOCIATION (§6, D-2 labeling);
economy — **$/true-catch and tokens-per-true-catch per arm×tier in the
three registered reconstructions (realized / cache-cold / cache-grouped,
§6a)** (primary-table co-axis; UNDEFINED at zero catches, never imputed);
the equal-dollars read (Δcatch/Δ$ vs more P reps); HIT-ALT rates (§5.3).

### 11.4 FA co-read (false-alarm co-report rule — co-reported with every primary read; NEVER pooled across item classes)

FA classes, each per arm×tier, **each split mf/sf**:

1. **Clean-item any-FLAG rate** — clean-mf and clean-sf separately.
2. **Off-family FLAG on defective items** (excluding §5.3 HIT-ALT
   allowances; **per-item denominator = 4 − |allowed families|, from the
   frozen key table** — D-7) — mf and sf separately.
3. **Key-matched-but-wrong-family rate** — mf and sf separately.

**Adoption bound (registered):** on every class above, FA_S − FA_P ≤ 0.15
absolute (ratio clause FA_S ≤ 2×FA_P only when FA_P > 0 — zero-cell rule).
**FA states are QUALIFIER STAMPS, never routing cells** (§12; pre-lock
A-1(e)): any class out of bound stamps the fired composite cell
PROPOSED-CONSTRAINED (C-B-FACON form: adoption only with paired
adversarial-verify triage, noise cost published); a class whose CI cannot
separate the bound stamps FA-UNRESOLVED (C-B-FAUNRES form: adoption
blocked, catch results publish alone). **Stated at registration (pre-lock
A-11.3): at the premium tiers the FA classes carry 4 clean clusters each —
the referee simulation shows the bound is NOT separable there at plausible
rates (FA-difference HW 0.114 at base 0.05, 0.176 at 0.10, vs the 0.15
bound), and enlarging the clean wing does not rescue it (analyst option
pricing: breach detection 0.11→0.13 from 4→8 cleans/class). FAUNRES is
therefore the EXPECTED premium-tier FA state by design; the POWERED FA
surface is haiku (20 cleans), and premium-tier adoption reads ride haiku's
FA stamp plus the premium tiers' descriptive FA rates, disclosed.**
Criterion-vs-competence co-stamp (the criterion-shift stamp): if S raises hits AND any FA class
together at a tier (both CIs above 0), every composite reading at that tier
carries "criterion shift, not competence — no discrimination claim". **The
FA side has no floor guard; a floored FA side (all-zero everywhere) passes
the bound trivially AND silences the criterion-shift stamp — stated, and the all-zero
case is itself reported** (D-8).

### 11.5 Honest resolution — referee-simulated values OF RECORD (rev 1 planning prose corrected)

The referee simulation (`analysis/referee_sim.py`,
`data/design/referee-sim-results.json`; reviewed sound at pre-lock)
REPLACES rev 1's planning arithmetic. Its rev-1-allocation numbers, now the
baseline of record: haiku Δ HW ≈ 0.093; sonnet/opus HW ≈ 0.145 (r3) /
0.177 (r2) at 24 items; H-B3 HW ≈ 0.204 (r3-leg) / 0.230 (r2); **H-B3 Holm
power 0.36 at δ_int=0.20 and 0.55 at 0.25; C-B-TTFLAT (95% form) reach
0.513 (r3) / 0.189 (r2) under a TRUE flat.** Those two lines are why rev 2
(a) enlarges the common pool to 36 defective and (b) moves the band read
to the 90% TOST convention (§11.2). **The referee re-simulation of the
rev-2 allocation has run (10k bootstrap × 2k sims, C44, seed 20260817;
`data/design/referee-sim-results.json` rev2 block) and its numbers
are OF RECORD, triple-confirmed (referee / analyst wrapper / independent
recount all within Monte-Carlo error):**

- **H-B3 Holm power (36 items, opus r3): 0.31 @ δ_int=0.15 · 0.51 @ 0.20 ·
  0.71 @ 0.25.** At the r=4 lock option: 0.36 / 0.58 / 0.79.
- **H-B2 (sonnet, 36 items, r3): 0.55 @ 0.15 · 0.82 @ 0.20 · 0.95 @ 0.25.**
- **C-B-TTFLAT reach under a TRUE flat (90% CI): 0.87 at r3 · 0.68 at the
  r2 floor · 0.96 at r4.**
- Interaction CI half-width ≈ 0.17 (r3) / 0.19 (r2); Δ_opus half-width
  ≈ 0.12 (r3) / 0.15 (r2) / 0.10 (r4).

**GO/NO-GO, stated in those words: H-B3 — the study's reason to exist —
is a coin flip at δ_int = 0.20 (0.51) and adequately powered only at
δ_int ≈ 0.25 (0.71; 0.79 at r=4). The registration locks knowing that.** Corrected
reachability statement (A-11.1): TTFLAT reach requires |Δ̂| ≤ 0.20 − HW,
not merely HW < 0.20 — the criterion rev 1 stated was necessary, nowhere
near sufficient. H-B1/H-B4 resolve effects of δ ≈ 0.15 (power ≈0.78 at
0.15, ≈0.42 at 0.10 — "resolves δ≈0.12" was optimistic and is withdrawn).
The design cannot establish top-tier-flat tighter than ±0.20; a tighter
band is a different (priced) registration.

## 12. Interpretation cells (rebuilt; coverage proven by enumeration)

**Member states.** Each Holm member resolves to exactly one state:
**F** (fires after Holm, one-sided) · **N** (null: does not fire, and its
two-sided 95% CI does not lie entirely below 0) · **R** (reversed: two-sided
95% CI entirely below 0 — read on the UNADJUSTED CI, stated per D-6) ·
**V** (void: the member's arm/leg was cut or not run — §15 Batch override or
§17 cut order for H-B4; a declined-top-up opus cut for H-B3 (D-12)) ·
**G** (guard-voided: a 0.85/0.15 guard fired on an arm of that member's
contrast at its tier, on ITS registered pool — see Guards below).
**State precedence, explicit (re-review N-a): V > G > R > F > N** — a
member whose arm was cut is V regardless of anything else; a fired guard
makes it G even where the test would also fire or reverse (a guard-fired
contrast issues no reading, so G must dominate F/R); R is read before F by
construction (a one-sided member cannot fire while its CI sits below 0). A
member consuming an UNREL cell takes **state G** (not merely its
disposition).

**Guards (any-arm, endpoint-scoped, on the endpoint's own pool — pre-lock
A-1(d)):** pooled target-question catch > 0.85 or < 0.15 in any arm of a
contrast, evaluated per endpoint: H-B1/H-B4 on the haiku surviving-bank
pool; H-B3's haiku leg on the C44 pool at haiku; H-B3's opus leg and the
band read on the C44 pool at opus; H-B2 on the C44 pool at sonnet. A fired
guard sets that member's state to G (slot kept, m stays 4), publishes full
descriptives + direction, and **no proposal issues from a guard-fired
contrast**; an opus guard additionally voids the band read (ceiling ≠ flat,
stated in the cell).

**Composite keying (pre-lock A-1): cells key on the (H-B1, H-B3) pair
ONLY — 5 × 5 = 25 pairs, each mapped to exactly one cell below, enumerated;
H-B2 and H-B4 states are RECORDED QUALIFIERS inside whichever cell fires
(they never split cells).** Qualifier semantics, fixed: H-B4=F → "mechanism
consistent with bundle competition (self-anchoring + partial-blinding bias
co-stated)"; H-B4=N → "gap not attributable to bundle competition; the
S−Sq compound is cited"; H-B4=R → "Sq measurably worse than P — sequencing
harm noted, decomposition published"; H-B4=V/G → "mechanism unmeasured".
H-B2 qualifiers mirror (mid-tier confirmation / null / reversal / unmeasured).

| Cell | (H-B1, H-B3) pairs | Reading / disposition |
|---|---|---|
| C-B1 | (F, F) | Tier-scaled serialization benefit. Decomposed dispatch PROPOSED for cheap tiers, $/true-catch table (3 reconstructions) beside it; top-tier chartering per the band cell; mechanism per the H-B4 qualifier. |
| C-B2 | (F, N) · (F, G) · (F, V) | Benefit real at the weakest tier; tier gradient unresolved (N) or unmeasured (G/V — stated which). Per-tier $/true-catch governs any charter text; no interaction claim. |
| C-B3 | (F, R) | Gap grows WITH tier — the salience-budget form refuted in sign. Registered warning cell; no adoption; replication gated on a new registration. |
| C-B4 | (N, F) · (R, F) · (V, F) · (G, F) | Interaction fires with no (or reversed/unmeasured) haiku main effect — anomaly; no adoption; full decomposition published; replication under a new registration. |
| C-B5 | (N, N) · (N, G) · (N, V) · (G, N) · (G, G) · (G, V) · (V, N) · (V, G) · (V, V) | Null/unmeasured family. Sub-read, registered: if H-B1=N and the upper bound of its two-sided 95% CI < +0.10 (SESOI) → serialization priced RITUAL at the weakest tier (the K× dispatch cost never gets paid AT THAT TIER; any H-B2 qualifier is read beside it); if H-B1=N with upper bound ≥ +0.10 → INCONCLUSIVE, carries unpriced; if H-B1∈{G,V} → the study's headline is unmeasured, stated. Publishable at full prominence in every sub-read. |
| C-B6 | (R, N) · (R, R) · (R, G) · (R, V) · (N, R) · (V, R) · (G, R) | A reversal is present with no firing H-B3-with-firing-H-B1 pattern (H-B1 reversed, or H-B3 reversed while H-B1 ∈ {N, V, G} — the (R, F) pair lives in C-B4) — bundling wins somewhere. Registered warning cell; no adoption anywhere; replication gate before any guidance text; decomposition published. |

(25 pairs: C-B1 covers 1, C-B2 3, C-B3 1, C-B4 4, C-B5 9, C-B6 7 — total
25, each pair exactly once. The enumeration commits with the lock.)

**Stamps (qualify the fired cell; never re-route — pre-lock A-1(b)(e)):**

- **INVERSE-AT-TIER stamp:** any tier where catch_S − catch_P's two-sided
  CI lies entirely below 0 stamps the fired cell "no adoption at ⟨tier⟩ +
  replication gate before guidance text there" — an adoption proposal from
  C-B1/C-B2 cannot include a stamped tier. (Resolves rev 1's C-B1×C-B9
  contradiction: the top-tier inverse now qualifies the proposal instead of
  being silently pre-empted.)
- **FA stamps** (§11.4): FACON-form / FAUNRES-form per class×tier, on the
  fired cell's adoption clause only.
- **Criterion-shift stamp** (§11.4).

**Band cells** C-B-TTFLAT / C-B-TTLIVE / C-B-TTSPAN (§11.2) fire beside the
composite cell whenever the opus guards are silent and H-B3 ∉ {V}; an opus
guard or opus cut voids the band read (stated). TTLIVE(+) feeds G-FAB.

**FORMAT-DEGRADED stamp** (§8/§10): subject format-noncompliance > 25% in
an arm×tier cell stamps that cell's readings format-dominated — readings
survive stamped; the family never collapses on a subject-behavior signal.

The **CLEANFAIL stamp** (taxonomy per re-review N-f — it modifies FA
stamps, routes nothing): J.4 removals leaving <4 cleans in a class make
that class's FA read UNDECIDABLE; its stamp becomes FAUNRES-form; the
clean-supply failure is itself reported.

**Degenerate cells:** C-B-UNREL⟨arm×tier⟩ (§10's INSTRUMENT-failure
trigger only; never imputed; blocks consumers — a member consuming an
UNREL cell takes state G, "unreliable" stated); C-B-BANKFAIL (§5.3 audit
floor or a §5.5 class surviving its replacement round: the bank does not
lock, the study does not launch, the failure is published).

**Precedence (registered):** C-B-BANKFAIL → member-state resolution
(guards/void/UNREL feeding states) → composite cell by the (H-B1, H-B3)
map → stamps and band cells attach. A row cannot land in two composite
cells (the map is a partition); stamps attach without routing.

## 13. Conditional replication gate G-FAB (named gate; running it un-fired is model-shopping)

**G-FAB fires iff H-B3 fires after Holm AND C-B-TTLIVE fires with Δ_opus5's
90% CI entirely above 0.** Wing **R-B1:** fable-5 (full resolved id — the
deployed-reviewer construct), arms P+S, r=1, over C44's 36 defective items
(36 + 180 dispatches), sequential, sparse. Priced at gate time by its own
probe (the bank-calibration fable-5 cost row is informative only, refused
as an anchor);
runs under the reserved wing allocation (§17). Contributes a descriptive
extension of the tier gradient; never enters the Holm family.

## 14. Carried commitments (Phase-A lock conditions and standing rules)

- **Lock-condition 1, stated verbatim (pre-lock A-7):** *"replacement
  rounds deterministic — fixed trigger, fixed round count, blinding
  preserved through the linter."* Implemented at both replacement surfaces:
  §5.3's audit (fixed two-round maximum, panel-majority disposition, the
  graduated blinding linter on every lane payload) and §5.5's shortcut-gate
  replacement (fixed trigger J ≥ 0.8, ONE round, linter-preserved).
- **Lock-condition 2, stated verbatim:** *"calibration trials are INSTRUMENT
  data, never experiment data — Phase B re-measures its own baselines,
  stated explicitly in the pre-reg."* Implemented: the cued-format Opus-5
  calibration probe (§4.4a) and every Phase-A hit-rate figure are
  instrument data (item-selection and strata only), endpoint-excluded;
  this study inherits no Phase-A number as an endpoint input.
- **Lock-condition 3 (regime pinning):** results conditioned on subject
  model id AND instrument/CLI version, recorded per trial; a version change
  voids the run's regime (one-way door, §16).
- **Lock-condition 4 (grade scope):** grades are strata for within-grade
  contrasts, never an absolute portable difficulty scale.
- **Structural-covariate manifest** committed alongside (§5.6).
- **Date partition:** all trials on one side of 2026-07-24 by construction;
  asserted per batch.
- [redacted: internal reference] (an internal build-logging tie-in).

## 15. Transport — lock-time decision (register at lock or not at all)

A design-note constraint makes the Batch API (50% off, fixed-n) LEGAL at this
fresh lock, so the choice is evaluated rather than inherited:

- **Batch API:** halves the metered rows (≈$300–350 forgone by declining at
  rev-2 scale — priced, not hand-waved). Against: (a) **the Sq arm requires
  true `--resume` session continuation, which Batch cannot serve** — a
  mixed CLI/Batch transport across compared arms puts an instrument seam
  INSIDE the primary family; (b) the chartering read informs a fleet that
  dispatches via CLI — the external validity of $/true-catch rides the
  deployed instrument's pricing and scaffolding; (c) every validated gate —
  leak SET, parity, regime door, preflight — is CLI-conditioned; a second
  transport is a new build + validation + leak surface.
- **Frozen CLI, metered lab key:** one transport for all arms and tiers;
  comparability by construction.

**RECOMMENDATION: frozen CLI for all trials.** Flagged as a lock-time
decision; the declined discount is named above. Had the lock chosen Batch,
the Sq arms could not run and H-B4 would be VOID at lock (slot kept, state
V), disclosed. [Editor's note: the lock chose the frozen CLI.]

## 16. Instrument plan

- **Sterile envelope:** a new, dedicated config dir built by the lab's
  sterile-envelope builder (never hand-built); subject cwd decoupled, outside $HOME,
  no repo. **Leak-gate full SET re-run for THIS study** — probe + NON-STERILE
  POSITIVE CONTROL + structural refusals + channel enumeration (any one
  alone false-cleans; PASS ≠ sterile) — **including the resumed-session
  channel** (the positive control runs on the Sq shape too). **Per-CALL
  init-event assertions of `memory_paths` and `plugins`** (the sterility
  rule's probe-blind channels) ride every dispatch — **in Sq, per TURN, since
  turns 2–5 are separate invocations with their own init events** (D-9).
  OAuth residue: killed by metered-key auth. [Editor's note, replacing one
  sentence: the locked text described a ~18K-token CLI-scaffolding residue
  as a constant of the instrument, identical across arms (N-6). The trial
  records do not bear that out for this study's calls: under `--bare` with
  the metered key, a single-question (S) dispatch carried a median ≈1.2K
  input tokens at haiku and ≈1.5K at sonnet/opus, and no P or S dispatch
  exceeded ≈4.9K, so the ~18K scaffolding seen in earlier
  subscription-authenticated sessions was not present here; see
  methods/HARNESS-STERILITY.md.] The non-sterile control leg runs on a
  subscription account — an account limit makes the gate INCONCLUSIVE by
  design; probe the control leg, never loosen the gate; schedule off limit
  windows.
- **Runner:** the trial runner (not published), a FORK of an earlier
  study's runner (graduation-not-duplication; the parent is never edited). **New
  components, enumerated (N-7):** (1) bundle assembly (P payload, 5 blocks,
  keyed question order); (2) multi-answer parser (the one genuinely new
  risk surface — guarded by MC-P1's disposition, golden-master vectors, and
  the robustness co-reads); (3) K-turn resume loop (MC-SQ1
  assertions, per-turn payload sha256, per-turn init-event assertions);
  (4) per-turn token/cost split recording **including cache-read /
  cache-write token fields on every record — required fields, asserted
  non-null by the record gate (an earlier study's records lacked them and
  the cache split was unrecoverable; §6a consumes them)**; (5) keyed-derivation
  ordering (§7) + recorded realized orders; (6) the one-sided bootstrap
  adaptation + selftest golden vector (§9); (7) grouped-order S probe mode
  (§6a).
- **Parity gate (per batch):** stimulus source-hash equality across arms;
  question-block byte identity across arms; briefing/schema byte identity
  (including the §4.2 partition statement) across all payloads; zero
  item-specific tokens in any charge; per-(item, arm, turn) payload sha256
  recorded.
- **Single live preflight:** ONE live dispatch per (tier × arm shape) — 8 probes
  (P and S at three tiers; Sq at haiku and sonnet) + the grouped-order S
  probe (§6a) — through the runner's REAL accept gate before any fan-out;
  the driver self-refuses `--max-dispatches != 1` until a live ledger read
  exists; plus the AST call-site tripwire. **The preflight probes are the
  pricing pass: each probe REPLACES its tier×shape cost row and re-prices
  the ceiling before record #1** (measured-budget rule).
- **Regime one-way door:** repairs → gates → record #1; `expected_regime`
  sources cli_version + invocation flags + resolved model ids +
  runner_commit from the recorded regime on resume; per-tier output files,
  one regime per file.
- **Instrument failure is never a subject verdict:**
  `api_error_status`/`terminal_reason` checked BEFORE any gate reads a
  response; cause-owner partition; MONOTONE halt predicate; account-owner
  causes halt the RUN; failure rows keep billed cost but never
  consume an (item, question, arm, rep) key; resume fills missing keys
  only, up to registered n; attempts retained for §10's denominator.
- **Run hygiene:** O_EXCL output locks with owner PID; recorded-PID liveness
  only; explicit-path staging around live drivers (never `git add -A`);
  instrument calls through the frozen binary only; the JSONL cost total is a
  floor — the key console is the meter of record.
- **Fleet dispatches** (audit panel, framer, checker, adjudication) ride
  a resumable workflow runner with a journal; checked-downstream lanes at sonnet.

## 17. Budget block (measured rows cited; extrapolations LABELED; probes REPLACE)

Measured anchors of record: haiku **$0.03702/trial** on THIS bank
(bank calibration, measured, itself 8.1× its registered estimate — the
cautionary anchor); sonnet-5 **$0.2317/dispatch** single-request and
**$0.2839** two-request resumed, realized over 672 rows of an earlier
study on larger mined stimuli (upper edges for this bank); the K=2 resumed premium
**1.196×** ($-basis) — measured at K=2, NOT applied at K=5; adjudication
**$0.013/verdict** ($2.61/198); fleet dispatch mean **$2.377**; single-preflight
probe **$0.10** class; cache factor: premium-tier passes ran **4–8× BELOW
cache-cold projections** (probe means are cache-cold upper edges; the
DIRECTION means realized premium rows may land well under these
placeholders, while the haiku anchor's own 8.1× overrun cautions the other
way — the ceiling is EXPECTED TO MOVE at the preflight re-pricing, in a
direction the probes decide — D-3). The bank-calibration strong-tier rows
(opus-4-8 $9.99, fable-5 $18.78) are vintage-/construct-flagged and REFUSED
as anchors.
**Opus-5 has NO measured row — no anchor is invented; the registered
pre-batch probe REPLACES the row.** **Sq per-session placeholders are
ARBITRARY SIZING NUMBERS with no derivation** (D-4: rev 1's $0.075 landed
near a linear K=5 extension of the K=2 premium by coincidence of round
numbers; no derivation is claimed) — the Sq probes replace them.

| Row | dispatches | basis | $/unit | row $ |
|---|---|---|---|---|
| haiku P | 240 | EXTRAPOLATION: $0.03702 measured + 5-question output | 0.056 | 13 |
| haiku S | 1,200 | EXTRAPOLATION (nearest anchor: same bank, same tier, directed vs open question) | 0.037 | 44 |
| haiku Sq | 240 sessions (1,200 turns) | ARBITRARY sizing placeholder — own probe replaces | 0.075/session | 18 |
| sonnet P | 132 | EXTRAPOLATION from $0.2317 measured + bundle output | 0.30 | 40 |
| sonnet S | 660 | measured $0.2317 (different stimulus family — upper edge) | 0.23 | 152 |
| sonnet Sq | 132 sessions (660 turns) | ARBITRARY sizing placeholder — own probe replaces | 0.35/session | 46 |
| opus-5 P | 132 | NO ANCHOR — probe replaces; sizing placeholder only | 0.70 | 92 |
| opus-5 S | 660 | NO ANCHOR — probe replaces; sizing placeholder only | 0.45 | 297 |
| cued opus-P calibration probe (§4.4a: ≤60 items × r3 = ≤180 dispatches) | ≤180 | NO ANCHOR — opus-P placeholder; SELF-PRICING (first dispatch = the opus-P single live preflight; its realized rate replaces this row) | 0.70 | 126 |
| remaining preflight probes (7 + grouped-order) + leak SET | — | measured probe class ($0.10) + SET legs | — | 12 |
| adjudication + belt + re-adjudication | — | $0.013/verdict measured, item-batched | — | 20 |
| audit panel + framer + checker (re-review R-2a: DERIVED, not fleet-mean — §5.3's fresh-context certification forbids item-batching) | — | round 1: 180 reader-item dispatches × sonnet $0.2317 measured ≈ $42; round 2 bounded (splits only, planning 20% ≈ $8); framer + checker ≈ $8 | — | 58 |
| recount + build incidentals | — | — | — | 10 |
| **core sum (planning)** | ≈5,064 requests | | | **≈ 928** |
| R-B1 wing reserve (iff G-FAB; own probe at gate time) | 216 | EXTRAPOLATION | — | 60 |
| **Ceiling proposed at lock (`--ceiling-usd`)** | | | | **$1,050** (committed ≈$988; headroom ≈$62 stated, not implied) |

Lock options priced beside the ceiling: **opus r=4 upgrade**
(H-B3 power ≈0.59/≈0.80 at δ_int 0.20/0.25; ≈+$130 placeholder).

[redacted: internal reference] (an internal program-budget disclosure).

**Registered cut order** (applied only pre-record-#1, on measured probe
pricing; scope shrinks, rigor never does):

1. haiku non-common remainder reps 3→2, all arms.
2. sonnet reps 3→2 on C44.
3. opus-5 reps 3→2 — **HARD FLOOR r=2 per arm on C44; below this the
   CEILING BENDS (budget top-up gate), never the floor.** **The declined
   branch is registered (D-12): if the re-priced r=2 floor exceeds the
   ceiling AND the top-up is declined, the opus wing is CUT —
   H-B3 and the band read take state V (slots kept), the study proceeds as
   a dense-tier study (H-B1/H-B2/H-B4), and the narrowing is disclosed in
   every output.** An underpowered H-B3 is never launched silently.
4. **LAST — mechanism decomposition (the Sq arms), never first** (the
   contested-provenance record rides §4.2), and only on an explicit lock-time
   choice against the surfaced ceiling-bend; cutting it sets H-B4 to V
   (slot kept), disclosed.

**Never cut:** the C44 subset itself; clean wings below 20/8/8 (kills the FA
co-read); the adjudication chain; the leak-gate SET; the preflight/probe
lane; the recount.

## 18. Follow-on program (named, not built here)

- **Successor bank — per-item discrimination-card decomposition:** an
  earlier study's card appendices (DISCRIMINATING [sig]/[poss] + COLLIDING
  + WRONG-OUTCOME; already run as a scoring rubric at that scale — 198
  verdicts, $2.61, 30/30 re-adjudication agreement) on its unburned
  remainder (39
  items; difficulty-extreme; stratifiable-not-blind — measured stage-2
  rates enter as disclosed strata only; framer isolation per §5.4
  mandatory) + the 6 checker-confirmed multi-keyable items. Its authoring
  lane is real new-instrument work priced in ITS budget block.
- **Tier × effort response surface:** separate follow-on registration, not a
  nested factorial (cell explosion kills the sparse opus cells; effort
  changes billed thinking tokens, colliding with natural-shape covariate
  reads). This study's default-effort rows become one measured slice
  (informs, never scores).
- **Encoding × serialization and the family axis:** queued per §3.

## 19. Scope note (binding on every claim)

Single briefing, single question-overlay encoding, same-family reviewers,
frozen-CLI transport, the bank-calibration study's synthetic-bank regime. Family-cued questions hint
the search space in all arms symmetrically — absolute catch rates are NOT
comparable to Phase-A open-search rates and carry no prevalence claim (the
calibration probe therefore runs cued, §4.4a). The class-level overlay is
coarser than item-specific decomposition (§5.1); positive results
generalize to checklist-shaped review mandates, not to arbitrary K-question
payloads. **P's within-dispatch satisficing/allocation behavior is a named
residual channel** (§4.2), priced descriptively by the FLAG-count read,
never fully removed. Sq findings are (one-at-a-time + self-anchoring)
findings under PARTIAL arm-blinding with a named bias direction (§9); no
pure-sequencing claim rides them. Grades are strata, never a portable
scale.

## 20. What this registration does NOT do

No verdict-only endpoint anywhere. No claim about the salience mechanism
from S−P alone (mechanism reads ride H-B4 + the turn-1 anchor check,
qualified by the self-anchoring disclosure and the partial-blinding bias
direction). No identification claim from the output-token association
(D-2). No top-tier-flat TEST (band cell only, at the ±0.20 grain). No
cross-study claim about an earlier study's unmeasured primaries. No prevalence claim.
No encoding or family claim. No change to practice guidance — every
positive cell ends in a PROPOSAL. No Fable arm without G-FAB.

## 21. Order of operations (build → selftest → gates → preflight → record #1)

1. Independent re-review of THIS revision → **lock** (this text + the
   five family definitions + rubrics freeze at lock; question texts and key
   table freeze later, at the freeze commit — §4.3).
2. Build: the runner fork (§16's enumerated components), multi-answer
   parser + golden-master vectors, one-sided bootstrap adaptation +
   selftest, scorer extension, ZC-1/ZC-2/ZC-3, audit-panel charter — each
   selftested.
3. Pre-freeze materials lanes (NO subject dispatches), in this order:
   blinded overlay authoring against the locked definitions (§5.4) →
   adversarial checker pass → exclusivity audit (§5.3, against the locked
   definitions) → ZC gates + any single replacement round (§5.5).
4. **Sterile dir + leak-gate SET (incl. resumed-session channel) — BEFORE
   any subject dispatch** (re-review R-3: the calibration probe is a
   subject lane; the sterility rule governs it).
5. **Cued-format Opus-5 calibration probe inside the envelope** (§4.4a,
   instrument data): dispatch 1 = the opus-P single live preflight through the real
   accept path (`--max-dispatches 1`), then the fan-out (≤179); its
   realized rate replaces the opus-P cost row.
6. C44 selection by the registered algorithm → freeze commit (§5.7).
7. Remaining single live preflights (7: P and S at haiku and sonnet, opus-S, Sq at
   haiku and sonnet) + the grouped-order probe, through the real accept
   path — **measured rows land here and RE-PRICE the ceiling before
   record #1**; cut order applied if it binds; ceiling-bend gate surfaced
   if the r=2 floor prices over (D-12 branch registered in §17).
8. Trials: haiku batch → sonnet batch → opus batch (sequential fixed-n,
   block-randomized under seed 1512, ceilinged, single-writer sinks).
9. Scoring → arm-blinded BORDERLINE adjudication (frozen rubric; 15%
   re-adjudication; 10% blinding check) → fold (merge-never-shrink).
10. G-FAB evaluation; R-B1 iff fired (own probe first).
11. Independent recount BEFORE any result is cited outside the study.

## 22a. Judge-panel defect map (carried from rev 1)

Rev 1's §22 mapped 17 judge-identified fatal defects to resolving sections;
that mapping is carried unchanged in substance — the sections renumber as
follows where rev 2 moved them: defect #1 → §11.1/§11.2/§12; #2 → §4.4;
#3 → §4.2 + §11.1 + §17; #4 → §4.2 (now with the turn-1 anchor check);
#5 → §11.4; #6 → §5.5; #7 → §5.5 ZC-2; #8 → §5.3; #9 → §4.1/§4.5/§17;
#10 → §17; #11 → §17 (D-4 corrected); #12 → §5.1/§18; #13 → §3; #14 → §3 +
§5.6/§14; #15 → §5.4; #16 → §13; #17 → §12 (rebuilt, coverage now proven
by enumeration rather than claimed).

## 22b. Pre-lock review disposition map (independent pre-lock reviewer, 2026-08-17 — 14 B / 14 D / 9 N)

| Finding | Disposition in rev 2 |
|---|---|
| A-1 cell coverage (5 limbs) | §12 rebuilt: member-state grammar {F,N,R,V,G}; composite keying on the (H-B1,H-B3) pair only, 25 pairs enumerated to 6 cells; H-B2/H-B4 as qualifiers; INVERSE-AT-TIER as a stamp (C-B9 contradiction resolved); FA states as stamps (A-1e); guards name every member incl. H-B3's legs, with per-endpoint pools (A-1d); V state routed (A-1c). |
| A-2 common-subset selection rule unregistered | §4.4: algorithm registered (strata quotas, interiority key, tie-breaks, shortfall rule); probe framing stated. |
| A-3 open-search calibration | §4.4a: the calibration probe runs in the DEPLOYED CUED FORMAT; Phase-A bins demoted to strata labels only. |
| A-4 response-set structure | §4.2: five-family partition stated in every arm's briefing; FLAG-count distribution read registered; residual named in §19. |
| A-5 responders at wrong layer | §5.5 ZC-3: family-generic mechanism responder scored THROUGH the real scorer, same lock consequence. |
| A-6 audit certification | §5.3: 3 blinded readers, EXCLUSIVE on unanimity, fixed two-round maximum, second-panel governs, analyst never rules; H-B1 restated over the surviving pool; HIT-ALT denominators per item (D-5/D-7 closed). |
| A-7 replacement paths unbounded (amendment: derived from the hazard — unbounded re-authoring against a gate is optional stopping in a materials hat) | §14 carries lock-condition 1 verbatim; §5.3 fixed two-round maximum with panel-majority disposition; §5.5 fixed trigger J ≥ 0.8, ONE round; the graduated blinding linter on every lane payload (§5.4). |
| A-8 scrub design + inverted citation of the scrub false-positive finding | §9 rebuilt: scoped scrubs (outside code spans — that finding cited in its recorded sense), expanded families incl. ordinals/soft variants, neutral replacement token, arm-blinding registered PARTIAL with named bias direction on H-B4. |
| A-9 order contradiction | §4.3 (definitions freeze at lock; question texts at freeze) + §21.3 (authoring precedes the audit; audit rules against locked definitions). |
| A-10 cache asymmetry | §6a: three registered reconstructions (realized/cache-cold/cache-grouped) + grouped-order S probe; §16: cache token fields required per record. |
| A-11 power decision rules | §11.5: sim values of record, corrected reachability prose, registered decision rule (referee re-sim replaces at lock; GO/NO-GO beside the ceiling); §4.4: pool 24→36; §11.2: 90% TOST convention adopted visibly; §11.4: FAUNRES-by-design stated, haiku = powered FA surface. |
| A-12 randomization re-derivability | §7: keyed derivations registered exactly; realized order recorded and recount-asserted. |
| A-13 dead UNREL trigger | §10: attempt-based denominator defined; failure attempts retained (§16). |
| A-14 (amendment) arm-asymmetric trigger discards a treatment effect | §8 + §10 + §12: cause-owner split — subject format failure becomes the format-noncompliance ENDPOINT (missing block = NON-CATCH, deployment-real; arm-differential read; catch decomposition) with a FORMAT-DEGRADED stamp at >25%, never an UNREL trigger; C-B-UNREL keys on instrument failure alone, so no format signal can take down the Holm family. |
| A-15 / 2.1 matching-rule reversal | §6 departure 2: the 3-of-3 convergence + judge instruction disclosed beside the prior departure, same form. |
| A-16 / 2.2 guard vs disclosure | §4.2: turn-1 anchor check registered as a named instrument check with stated n. |
| D-1…D-14 | D-1 §11.3 (S−Sq relabeled) · D-2 §6/§11.3/§20 (association only) · D-3 §17 (direction stated) · D-4 §17 (placeholders marked arbitrary) · D-5 §5.3/§11.1 · D-6 §12 (unadjusted CI stated for R) · D-7 §5.3/§11.4 · D-8 §11.4 (FA floor stated) · D-9 §16 (per-turn init assertions) · D-10 §4.1 (flags pinned) · D-11 §11.3 (haiku-scoped) · D-12 §17 cut order (declined branch registered) · D-13 §4.2 (contest recorded) · D-14 §11.2 (90% CI adopted visibly). |
| N-1…N-9 | N-1 §5.1 path corrected · N-2 §5.5 (J ≥ 0.8) · N-3 §12 (C-B5 sub-read keys on the +0.10 bound explicitly) · N-4 §8 (cross-ref fixed to §11.3) · N-5 §4.1 (keyfile pinned) · N-6 §16 (OAuth/residue disposition) · N-7 §16 (components enumerated) · N-8/N-9 verified-no-action. |
| **Re-review R-1** (interiority key constant at r=1 — A-3 closed in form, inert in substance) | §4.4 step 2 + §4.4a: probe registered at r=3 (scores {0.5, 0.167} — a real interior/extreme split); the probe self-prices as the opus-P preflight. |
| **Re-review R-2** (two lane rows off their own bases; $18 headroom) | §17 re-derived: calibration probe its own row ($126, self-pricing); audit panel derived from the certification rule's actual dispatch count (180 × sonnet measured + bounded round 2 + framer/checker = $58, fleet-mean basis dropped); core ≈$928, ceiling $1,050 with headroom stated. |
| Re-review N-a…N-f | N-a §12 state precedence V > G > R > F > N explicit; UNREL consumers take state G · N-b C-B5 parenthetical scoped to the weakest tier · N-c C-B6 prose excludes (R, F) · N-d the sub-read names the two-sided 95% CI upper bound · N-e ZC-3 redefined as the COMPOSITE responder (keyword/base-rate family selection + best generic mechanism, through the real scorer; flag-all-five rejected as J-suppressing) · N-f CLEANFAIL re-classed as a stamp modifier. |
| **Final-verify R-3** (calibration probe — a subject lane — sequenced before the sterile envelope; opus-P preflight after its own fan-out; stale probe count) | §21 resequenced: sterile dir + leak SET at step 4, BEFORE any subject dispatch; the probe at step 5 inside the envelope, preflight-first (dispatch 1 = the opus-P preflight, `--max-dispatches 1`, then the ≤179 fan-out); remaining preflights correctly counted at 7 (step 7); §4.4a and §4.4 state the envelope requirement in place. |

## 23. Pre-lock TODO list

[redacted: internal reference] (the analyst's pre-lock TODO list: the referee re-simulation, resolved model ids, charter texts, ZC-3 strings, CLI pin, an internal budget reconciliation, a roadmap pointer).
