# Dated amendment — the corrected scoring pass (rules of record for the post-recount re-scoring)

> **Public restatement.** The rules below were recorded in the study's private
> decision ledger, which is not published. This file restates them from the
> rule text only: the counts, definitions and parameters are the ledger's,
> unchanged; internal names were replaced by descriptive words, and the
> ledger's internal routing and bookkeeping are omitted. Private references:
> the finding that triggered this pass was recorded 2026-08-22 (after the
> first independent recount, report commits `648c9d1`/`addde4d`); these rules
> were committed at `ad9be8a`, **2026-08-27 23:41:42 -0400**, and the pass was
> executed at `7e9d89e` (2026-08-28 00:01:09 -0400).
>
> **Timing, stated exactly.** The first verdict of the corrected adjudication
> lane was written at 23:41:48, six seconds after the rules commit. That
> verdict came from a one-batch preflight whose dispatch was probably already
> in flight when the commit landed (verdict records are time-stamped on
> completion; dispatch start times were not recorded). The rules therefore
> predate every corrected-lane verdict and every corrected endpoint; they
> cannot be shown to predate the first corrected-lane dispatch.

## 1. What triggered it (recorded 2026-08-22)

The independent recount of the first published table (fresh code from the
rules text, blind pass before any of the original analysis's numbers was
opened) proved at row level that the original analysis parser scored **978
text-present question-rows as MISSING** instead of routing them through §8's
registered BORDERLINE lane. Answer shapes off the fenced letter
(`## Q-<family>` headings, `FLAG-<family>:`, bold unfenced heads, an opening
"YES") failed BOTH the strict and the loose presence grammars: the loose tier
widened punctuation and fencing tolerance but not the set of head shapes, so
"present but malformed" collapsed into "no text" at scale. The deletions were
strictly one-directional (132 key-matched target FLAGs, 26 clean-item FLAGs,
114 off-family FLAGs, 3 HIT-ALTs); every divergent row that a registered
reader had actually seen was ruled FLAG by that reader. A second layer: a lane
verdict of FLAG on a strict-MISSING / loose-PARSED target row could never
produce a CATCH, because the merge key-matched a parser fragment rather than
§9's scored text. Cross-checks isolating the defect: the original statistics
layer reproduced its own published deltas to ≤ 0.0001 on its own row
statuses, and the registered keyword re-derivation entry point fired on
132/132 of the divergent scored texts.

Rulings recorded that day:

1. The published results were stamped SUPERSEDED, with a list of what stood
   and what fell. (The superseded issue is not published; its numbers are not
   cited anywhere.) [Editor's note: true of the record when ruled. This
   public extract cites a few of the superseded issue's values to show what
   the defect did: `methods/RECOUNT.md` (a haiku S−P of 0.000) and
   `results/RESULTS.md` (the 08-22 haiku S−Sq of +0.256). No conclusion rests
   on them.]
2. The corrected scoring pass is a new workstream, not a patch to the old
   record: extraction reads §9's scored text, the corrected table is
   recounted again independently, the one new J.4 pair (clean-sf-02, units)
   runs, and the robustness co-read is redesigned to perturb EXTRACTION — the
   published co-read's variants shared the primary's extraction and so could
   not fail on this defect.
3. Root cause, recorded for the design review of the fix: the parser's
   golden-master vectors were authored from IMAGINED noncompliant shapes,
   never from live weakest-tier output.
4. No external text cites any fallen number.

## 2. The rules of the corrected pass (recorded 2026-08-27, before the corrected lane's verdicts)

1. **Presence is permissive; the pinned parser is untouched.** A new
   analysis-layer module (`analysis/presence.py`) overlays every
   registered-chain row: strict-MISSING ∧ ¬loose-PARSED rows whose text EXISTS
   ride the BORDERLINE lane instead of mechanical NON-CATCH/SILENT. §9's
   scored text per arm — **S/Sq: the whole turn** (a single-question dispatch
   or turn IS the text for its question; no family label required); **P: the
   family's segment**, from its first live-shape marker (`Q-<f>` /
   `NO-DEFECT-<f>` / `FLAG-<f>` / `NONE-<f>` under any of `#`, `**`, bullets,
   numbering) to the next different-family marker. Live result: 471 residual
   rows → **470 PRESENT, 1 MISSING** (opus P mf-sign-06 rep 3, units — four
   fenced blocks, no units block). Every mechanically scored row of the
   corrected table equals the committed table byte-for-byte (status and
   raw_block); only the route of those 470 rows changes. Corrected table:
   7,340 rows; BORDERLINE 1,804 = 1,334 prior + 470.
2. **Every BORDERLINE row presents §9's text, never a parser fragment**, and
   the merge key-matches that same text (the second-layer defect).
   **Retention is TEXT-CONDITIONED:** an existing lane verdict is kept iff the
   block its adjudicator saw equals the corrected text under
   `normalize_for_retention` (fence-only lines dropped, whitespace
   collapsed); otherwise the row is re-laned. Result: **940 retained (81 FLAG
   / 859 NONE), 394 re-laned, 470 new → queue 864** (S 317, Sq 305, P 242;
   target 191, off-family 428, clean 245; haiku 842, sonnet 21, opus 1). Old
   verdicts are kept, never overwritten; the merged table cites each row's
   lane (`adjudicated.lane` = current | retained).
3. **Lane parameters unchanged:** the same frozen charge
   (`materials/rubrics/adjudication-charge.md`; its "answer block" wording
   covers a whole turn — one question per turn — and a P segment; no charge
   edit), sterile metered claude-opus-5 via the frozen CLI 2.1.212, seed 1512,
   15 % re-adjudication by a second fresh reader (with a third, governing
   reader on disagreement), 10 % arm-guess check, scrub belt and blinding
   assertion. Ids `adj-2001..2864` (offset 2000, no collision with
   `adj-0001..1334`). One preflight batch dispatched and inspected before the
   full run.
4. **Co-reads REDESIGNED to perturb EXTRACTION**, defined over all three arms
   BEFORE any corrected endpoint is computed:
   - **V1 (primary)** — the corrected pass as merged.
   - **V2 (P-maximal key scope)** — for every P row whose verdict is FLAG
     (mechanical or adjudicated), the key-matching scope widens from the
     family's block/segment to the WHOLE bundle; S/Sq unchanged (their scored
     text already is the whole turn). Direction: can only add catches
     (target), or move FA → HIT-ALT / set `key_matched_wrong_family`.
   - **V3 (label-respecting punitive)** — a permissive-route S/Sq row counts
     as PRESENT only if the turn carries a marker for the ASKED family
     anywhere; otherwise it composes as MISSING (NON-CATCH / SILENT)
     regardless of the lane verdict. P rows unchanged (their segment requires
     the marker by construction). Direction: can only remove catches/FAs
     recovered by the permissive route.

   The earlier loose-primary and NONE-scope variants are kept as legacy lines
   (they perturb nothing upstream of the lane). Divergence in member states,
   Holm firings, or the composite cell is DISCLOSED, never averaged.
5. **Endpoints:** the registered chain (`analysis/endpoints.py`,
   `analysis/costs.py`, `analysis/descriptives.py`) runs unchanged on the
   merged corrected table. Format noncompliance stays defined under the
   PINNED strict grammar (the registered instrument), with the first
   recount's rate co-stated; where FORMAT-DEGRADED fires mechanically but the
   construct is refuted, the measured lane recovery is co-stated beside the
   stamp.
6. **J.4:** the one new pair (clean-sf-02, units), plus any clean-item FLAG
   pair the corrected lane newly surfaces, runs through the keying checker
   (NOT-REAL default) before FA is read.
7. **Disclosures written in advance:** (a) whole-turn presented blocks make
   the arm partially inferable from text SHAPE (recap prose, fence habits) —
   label blinding held, shape blinding was never registered; both lanes'
   arm-guess accuracy is reported against chance. (b) The lane's text volume
   is ~2.2× the first lane's (576 K vs 267 K characters); its cost is re-sized
   at close from the results file, never from the first lane's $5.79.
   (c) 21 sonnet rows and 1 opus row enter the lane for the first time; every
   other new row is haiku — the correction is concentrated in the weakest tier
   by construction of the defect.
8. **Then:** the results are re-issued from the corrected table, and an
   independent re-recount of the CORRECTED chain (fresh code from this rule
   text, including the retention rule and V2/V3) runs before any number is
   cited.
