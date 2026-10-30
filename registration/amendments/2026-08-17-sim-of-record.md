# Dated amendment — referee-sim RNG fix; §11.5 values re-pinned to the post-fix artifact

> Public copy. Private commit `9e23da7`, 2026-08-17 15:08 -0400; unchanged
> since. Original git blob `69fdcfd15ebcca8524bbb43eae76bec45fd524fe`, SHA-256
> `a554442a67b14732e512c66e803e43e1d609b1cd270e63b5f704471214bc9716`. Internal
> names and paths replaced by descriptive words; nothing else changed.

Amends: `registration/preregistration.md` (LOCKED rev 2.4 @ 7bbe83e),
§11.5. Recorded 2026-08-17, same day as the lock, before any post-lock
build artifact or dispatch.

## What happened

The referee simulation carried a reproducibility defect: one module-global
RNG advanced across every function in execution order, so any edit
anywhere in the file silently shifted every downstream number (the
referee caught it by diffing its own commits against §11.5's verbatim
quotes). Fixed at commit 87c569f by content-addressed reseeding
(`_reseed(label)` per reported quantity — results now invariant to
unrelated edits). The full rev-2 block was regenerated under the fix.

## Values of record

§11.5's source artifact is `data/design/referee-sim-results.json` `rev2`
block **as of commit 87c569f** (post-fix). Drift from the locked quotes is
rounding-grade (≤0.012 on every figure, Monte-Carlo noise from the changed
draw sequence): H-B3 r3 0.515 @ δ_int=0.20 / 0.698 @ 0.25 (r4: 0.593 /
0.789); H-B2 0.535 / 0.81 / 0.96; TTFLAT reach 0.88 (r3) / 0.70 (r2) /
0.95 (r4). **The GO/NO-GO statement is unchanged in every word:** H-B3 is
a coin flip at δ_int = 0.20 and adequately powered only near 0.25; the
registration was locked knowing that.

## Instrument lesson (carried)

A shared advancing RNG makes every reported number a function of
unrelated edits — the same defect class as an unkeyed randomization
stream (pre-lock A-12). The registered repair form is the same both
times: content-addressed seeding per reported quantity. This study's own
analysis code inherits this requirement (§7's keyed derivations already
comply).
