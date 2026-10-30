# The independent recount — methods note

Every number in `results/RESULTS.md` was re-derived by an independent recount
before it was cited: an AI agent separate from the one that ran the analysis,
writing fresh code from the registration text and the dated rules alone, on the
raw trial records. This note says what was recounted, how, what it found, and
what can be checked from this repository.

## Protocol

- **Fresh code from rules text.** The recount was given the registration, its
  dated amendments, and (for the second recount) the corrected-pass rules. It
  did not import or read the original analysis code before its own numbers
  were committed.
- **Blind first, then compare.** Each recount committed its own results
  (the "blind pass") before opening the original analysis's outputs. Only then
  did it compare, localize every disagreement to rows, and classify each
  divergence by cause.
- **Raw inputs.** Trial records, the 80 frozen items, the frozen key table and
  C44 list, and the adjudication verdicts as reader data.

There were two recounts of the main table and one of the economics.

## Recount 1 (2026-08-22): the table did not reproduce

Blind pass committed `36c871b`; report `648c9d1`/`addde4d` (private).

**Finding.** The original analysis parser scored **978 text-present
question-rows as MISSING**. The registration (§8) says a block that is present
but malformed goes to the BORDERLINE adjudication lane ("text exists; it gets
judged"); only a block with no text at all scores as a non-catch. Answer shapes
off the registered fenced form (`## Q-<family>` headings, `FLAG-<family>:`,
bold unfenced heads, an opening "YES" with a mechanism) failed both the strict
and the loose presence grammars, so "present but malformed" collapsed into "no
text". The whole study contained exactly **one** genuinely missing block.

- **132 target rows** carried a key-matched FLAG that the original table scored
  as a miss (haiku P 16, haiku S 31, haiku Sq 78, sonnet Sq 6, opus S 1), plus
  26 clean-item FLAGs, 114 off-family FLAGs and 3 HIT-ALTs. **Zero divergences
  ran the other way.**
- A second layer: on the 3 such rows that did reach the lane, readers ruled
  FLAG and the merge still scored a miss, because it key-matched the parser's
  empty fragment instead of the scored text.
- The defect was confounded with the independent variable: it concentrated at
  the weakest tier, whose format discipline is worst, and hit the serialized
  arms hardest. The first table therefore read as a clean tier story it did
  not support (a haiku S−P of 0.000 manufactured by deleting 31 S and 16 P
  catches; an apparent Sq "sequencing harm" from 78 deleted Sq catches).
- The original statistics layer was correct: re-running the recount's
  bootstrap on the original row statuses reproduced every published delta, p
  and CI to ≤ 0.0001. The registered keyword re-derivation entry point fired on
  132/132 of the divergent rows' scored texts. The defect was wholly in
  extraction.
- The registered robustness co-reads had not caught it: both variants sat
  downstream of the same extraction, so they could not fail on it.

**Root cause.** The parser's golden-master vectors had been written from
imagined noncompliant shapes, never from live weakest-tier output.

**What happened next.** The first table was stamped SUPERSEDED (it is not
published). A corrected scoring pass was registered as a dated rule set before
its adjudication lane produced any verdict
(`registration/amendments/2026-08-27-corrected-scoring-pass.md`, including its
timing note): permissive presence authored from the live residual rows, §9's
scored text presented and key-matched on every BORDERLINE row, text-conditioned
retention of earlier verdicts, and a redesigned co-read that perturbs
EXTRACTION (V2 widens P's key scope to the whole bundle; V3 refuses S/Sq turns
that carry no marker for the asked family).

## Recount 2 (2026-08-28): the corrected chain reproduces

Blind pass `5920136`, report `099c5c1`; economics blind pass `021eaa8`, report
`59a2b33` (private). Fresh code from the corrected-pass rule text:
`recount/code/recount_v2.py` (reference) and
`recount/code/recount_economics.py` (re-runnable here).

**Agreement.** 7,340/7,340 rows identical on status, hit,
key-matched-wrong-family, verdict of record and lane label. Every Δ, CI and p
reproduced to the last printed digit (10k draws and 1e6), together with the
member states, composite cell, band cell, stamps, V2/V3 co-reads, FA classes,
J.4, and the economics (8/8 cells: units, dispatches, realized dollars, token
totals, true catches, $/true-catch, equal-dollars).

Exact p agreement is algorithmic identity, not independent Monte Carlo: both
implementations arrived from §11's text at the same draw
(`numpy.random.default_rng(1512).integers(0, n_items, size=(n_boot, n_items))`).
The recount's Monte-Carlo independence comes from its own seed sweep (30 seeds:
H-B1 fires 24/30, H-B4 13/30) and from a second reading of the bootstrap.

**Divergences, classified.**

- **D1, definition.** FA bound-state labels on three ratio-only cells. The
  registration's adoption bound has two clauses (absolute Δ ≤ 0.15; ratio
  FA_S ≤ 2 × FA_P). The recount keyed the label on the absolute clause; the
  registered reading uses both. The registered reading stands, with a caveat:
  the registration gives the ratio clause no resolution signal, so those three
  stamps are point-estimate stamps.
- **D2, counting convention.** V3 "relabeled" 171 (rows whose status changed)
  vs 199 (rows demoted, including 28 no-ops). Same consequential set.
- **D3, economics label.** Rows are priced at the CLI-billed table (sonnet-5
  $3/$15 per MTok). A provider reference cached before the trials lists $2/$10;
  console billing per model is unverified. Sonnet stays the cheapest tier per
  true catch either way.
- **D4, economics mechanism.** The gap between realized cost and the token
  formula is the CLI's own haiku helper call on each session's first
  invocation ($6.97 of $140.87; exactly $0 on the 532 units whose
  `served_models` lists only the subject), not an undercount of subject input.
  Removing it entirely leaves bundling ahead 2.93× / 2.00× / 2.18×.

**Fragility the recount confirmed independently** (disclosed beside the
verdict, never a re-decision): H-B1 fires at the registered 10k draws on most
but not all seeds; both H-B1 and H-B4 fire at 1e6 draws; V2 and V3 both move
the composite cell to C-B5; and under a WITHIN-item reading of "item-stratified
cluster bootstrap" (resample reps within each item) both H-B1 and H-B4 fire
comfortably (p 0.0057 / 0.0022). Both implementers read the registration as
cluster-resampling items; the wording admits both.

**Blindness caveat, stated by the recount itself.** The corrected-pass rule text
carried the presence and retention counts (470/471, 940/394), so those two
checks were verification against a known target. Every other layer (lane
coverage, composition, endpoints, co-reads, FA, J.4, economics) was blind.

**Construct notes from the recount.** Of the 940 retained verdicts, 459 are
byte-equal and 481 are retained only because the registered normalization
drops fence-only lines and collapses whitespace; under byte equality the
corrected lane would have had 1,345 rows, not 864 (no retained row differs in
content). On the P side, a segment runs to the next different-family marker, so
the last family's segment absorbs closing prose: 17 of 242 P lane rows mention
another family, all judged NONE on an explicit `NO-DEFECT-<f>`. Of the 199 S/Sq
turns without an asked-family marker, none carries a marker for any other
family.

## What you can check here

| Check | How | Result in this repository |
|---|---|---|
| Recount rows vs the scored table | `python recount/check_agreement.py` | 7,340/7,340 statuses, hits, key-matched-wrong-family; 1,804/1,804 verdicts and lane labels |
| Recount economics | `python recount/code/recount_economics.py OUT.json`, compare with `recount/recount-economics.json` | identical except two probe bookkeeping fields not in the public tables (`lane`, `regime_n_per_cell`) |
| The whole analysis chain | `python analysis/reproduce.py` | every artifact of record reproduced (see README) |
| The 470/471 presence finding | `pytest tests/test_presence.py -k live_residual` | 471 residual rows, 470 present, 1 missing |

**What you cannot re-run here.** `recount/code/recount_v2.py` is published as
reference only: its inputs include the first table's lane inputs and mappings
(the text each adjudicator was shown, and the blinded batch maps), which are
not published. Its outputs are: `recount/recount-rows.jsonl` (per-row route,
presence, verdict, and V1/V2/V3 status; text appears only as a 16-hex digest and
a length) and `recount/recount-summary.json`. The first recount's code is not
published; its findings are summarized above.
