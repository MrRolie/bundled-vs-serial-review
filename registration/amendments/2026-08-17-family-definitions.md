# Dated amendment — the five frozen family definitions (supplying a locked referent)

> Public copy. Private commit `79ce12b`, 2026-08-17 15:06 -0400 (three minutes
> after the lock `7bbe83e`); unchanged since. Original git blob
> `6dc873efb8e8b1478a8a522567c4215f86c57f7d`, SHA-256
> `7e393927efb9a3bc72eb2a5ec0cd42f20dab280dbdae3b10a76c1d5b82d2c545`. Internal
> names and paths replaced by descriptive words; nothing else changed.

Amends: `registration/preregistration.md` (LOCKED rev 2.4 @ 7bbe83e).
Recorded 2026-08-17, same day as the lock, before any post-lock artifact
was built and before any dispatch.

## The defect

The locked text freezes "the five family definitions" at lock (§4.3, the
status header, §5.3's audit referent, §21 step 1) — and contains no
definition text. The lock froze a referent that did not exist. Caught by
the analyst's own verify-before-assert pass immediately after the lock
commit; the audit lane and the question-framer both consume the
definitions, so building anything without this repair would have forced an
illegal improvisation downstream.

## The repair — adopt the bank's own canonical definitions, verbatim

The definitions below are copied VERBATIM from the certification checker
charter the bank-calibration study's own blinded certification ran
against. They are the text that DEFINED these classes when every item in
the bank was certified; they predate this study entirely and are
hypothesis-neutral by construction (authored for the bank-calibration
study's metrology, never shown any treatment of this study). No new
authoring occurred; adopting them is the minimum-degrees-of-freedom
repair.

**The five frozen family definitions (of record for §4.3, §5.2's
⟨one-line frozen family definition⟩ slots, and §5.3's audit):**

- **boundary:** the code mishandles the EDGE of a range: an index, limit,
  slice, or loop bound takes in one element too many or one too few. The
  quantities being related are the right ones — it is the edge that is
  off.
- **sign:** an arithmetic sign is inverted or wrong: a term is added where
  it should be subtracted, negated where it should not be, or a delta is
  applied in the wrong direction.
- **exception:** error handling is wrong: a failure case is unhandled,
  caught too broadly, swallowed silently, or raised for a case that is
  actually valid.
- **units:** two quantities of different scale or unit are combined
  without conversion, or a value is converted with the wrong factor
  (seconds vs milliseconds, percent vs fraction, bytes vs kilobytes).
- **comparison:** a decision relates the WRONG things or in the wrong
  direction: the operands are swapped, the wrong field is tested, or the
  operator expresses the opposite relation. This is not about the edge of
  a range.

## Impact

Zero on any endpoint, cell, or gate: no artifact had consumed the missing
referent. The question-framer embeds these definitions in the overlay
question texts (§5.2); the exclusivity audit rules against them (§5.3);
both lanes were not yet dispatched. Direction-of-bias: none — the text was
fixed before any selection, authoring, or measurement touched it, and its
source predates the study.
