# J.4 KEYING-CHECKER CHARGE — clean-item flag verification

A code diff certified as containing NO defect of the asked family was
nonetheless flagged by one or more reviewers. You are given the full diff,
the family question, and the reviewers' claimed findings. Your task: verify
each claim AGAINST THE DIFF ITSELF.

Rule an item-family pair REAL only when you can yourself confirm, from the
diff text, a genuine defect of the asked family at the claimed site — the
code, as written, actually misbehaves in the way the family defines. A
claim that is plausible-sounding but does not survive tracing the actual
code is NOT-REAL. A claim about a real weakness of a DIFFERENT family is
NOT-REAL for this pair. Style objections, hypotheticals contingent on
inputs the code excludes, and "could be clearer" observations are NOT-REAL.
When uncertain after tracing the code, rule NOT-REAL — the default is that
the certification stands.

FORMAT — exactly one line:

VERDICT: REAL|NOT-REAL — <reason, at most 25 words>

No preamble, no extra lines.
