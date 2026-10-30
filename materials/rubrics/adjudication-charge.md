# ADJUDICATION CHARGE — verdict resolution

You are given answer blocks from code reviews. Each block was written in
response to exactly ONE of five review questions; the question texts are
reproduced below, and each entry's `family` field names which question its
block answers. You never see the code diff, and your task is NOT to judge
whether the review is correct. Your task is to resolve what each block
ASSERTS as its answer to its question.

For each entry, output exactly one verdict:

- FLAG — the block asserts that a defect of the asked family IS present.
  Any location or mechanism claim, however brief or hedged, counts:
  "possible off-by-one at line 12" is a FLAG.
- NONE — the block asserts that NO defect of the asked family is present,
  or explicitly declines to flag one. The token `NO-DEFECT-<family>`, in
  any casing, wrapping, or prefix form, is an assertion of NONE.
- NEITHER — the block asserts neither: it is empty, restates the question,
  refuses, or is garbled beyond assertion. If you cannot decide between
  FLAG and NONE, output NEITHER — ambiguity never awards a flag and never
  awards a pass.

Judge only what the block answers to ITS question. If it affirms that a
defect is present — whatever mechanism it names, right or wrong — that is
FLAG; the correctness and family-fit of the named mechanism are scored
elsewhere, mechanically, and are none of your concern.

FORMAT — one line per entry, in the order presented:

<adjudication-id>: FLAG|NONE|NEITHER — <reason, at most 15 words>

No preamble, no code fences, no extra lines.
