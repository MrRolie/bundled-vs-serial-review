"""answer_parser.py — the shared multi-answer parser.

Parser-robustness co-reads were named at lock, and an independent recount
re-derives every scored row from the rules text. This module was
trial-time pinned: the trial runner imported it to populate MC-P1/MC-S1 on
every record, so it carried the regime hash and edits were legal ONLY
before the first primary record. The analysis co-reads also
consume it; a parsing-rule
fix here never touches a frozen artifact. The scoring driver that will
consume this module (built separately) owns the MC-P1/MC-S1 disposition
routing (missing → NON-CATCH; malformed-but-present → loose parse → the
BORDERLINE lane) — this file only classifies each expected family's
block, once, per variant. It does not decide catch/non-catch and does not
implement the strict-then-loose fallback itself; that composition is the
scoring driver's job, exactly as `parser_strict` / `parser_loose` were
computed side-by-side as co-reads in an earlier study's scoring driver
rather than chained inside the parser. The SCORED TEXT for key-matching
(§9's mechanical scorer) is `raw_block` — the verbatim answer block — not
`mechanism` (a normalized, whitespace-joined convenience field); a scorer
keying on `mechanism` would miss whatever the key-match regex expects to
see in its original layout.

Registered form (prereg §5.2, the family-definitions amendment):

    Question q_f: "Does this diff contain a defect of family f — <one-line
    frozen definition>? If YES, name the file, location, and mechanism in
    free text. If NO, output NO-DEFECT-f."

    Answer schema, identical in every arm: ONE FENCED BLOCK PER QUESTION,

        ```
        Q-<family>: FLAG|NONE — <mechanism>
        ```

    families = boundary, comparison, exception, sign, units (the five
    frozen family definitions,
    `registration/amendments/2026-08-17-family-definitions.md`). Arm P dispatches one response carrying all 5 blocks
    (order randomized, §7); arm S/Sq dispatch one response/turn carrying
    exactly 1 block for the target family. **Arity is NOT enforced here**
    (MC-P1 "5 parseable blocks" / MC-S1 "1 parseable block" is a count the
    CALLER checks against this function's return — the manipulation-check
    code owns that comparison, not the parser, which stays agnostic to
    which arm is asking).

    **Second legal answer shape (repair-set review finding 3(a), design
    ruling):** the question text's OWN closing instruction, "If NO, output
    NO-DEFECT-f," is a standalone NONE answer with no `Q-<family>:` head at
    all — `NO-DEFECT-<family>` parses to verdict NONE, mechanism `None`,
    exactly like a bare `Q-<family>: NONE`.

Two independent full parses (robustness co-reads), never one parser falling
back into the other — `parse_response(text, expected_families,
variant="strict"|"loose")`. Both variants share the SAME two steps and
differ on both, in different ways:

  1. **Presence detection (shared GRAMMAR, variant-dependent SCOPE):** is
     there SOME text that identifies which family it is answering, either
     a `Q-<family>` tag or a `NO-DEFECT-<family>` token? This uses a
     single tolerant regex (numbering token optional, family word
     case-insensitive, colon optional for the `Q-` shape, word-bounded
     against a longer word merely starting with a family name) — the SAME
     regex for both variants, deliberately, since conflating "we can't
     even find an attempt" with "grammar failed" was the bug this design
     replaced (see `_PRESENCE_OR_NO_DEFECT_RE`'s docstring below): a
     garbled verdict token, a numbered prefix, wrong case, or a truncated
     fence are all cases where TEXT MANIFESTLY EXISTS for that question —
     §8 MC-P1 reserves MISSING for "no text for that question", not for
     "text that doesn't parse." **What SURFACE this shared grammar is run
     against differs by variant** (finding 3(b), design ruling): STRICT only
     ever scans INSIDE fenced blocks (`_extract_fenced_blocks`, an
     unclosed trailing fence still yields its content, flagged
     `closed=False`); LOOSE ALSO scans the text OUTSIDE every fence
     (`_unfenced_regions`) — a well-formed but never-fenced answer is text
     that manifestly exists and must not silently read as no answer at
     all. A family MISSING under strict but PARSED under loose (the text
     existed, just unfenced) is NOT resolved here — `parse_response`
     reports each variant's own independent disposition; the composition
     rule that routes that specific divergence to the BORDERLINE lane
     (never mechanical NON-CATCH) lives in `scorer`, the same layer
     that already owns every other strict/loose composition decision.
  2. **Grammar validation (variant-specific):** once a chunk is located,
     each variant's OWN head regex decides PARSED vs MALFORMED — strict
     requires the exact registered form (byte-exact `Q-<family>: FLAG|NONE`
     optionally ` — <mechanism>`, case-sensitive, no numbering, the
     registered em-dash, a properly closed fence, AND — for the NO-DEFECT
     shape — the bare token alone on its line); loose additionally
     tolerates numbering, case, a missing/optional colon, hyphen/en-dash/
     em-dash/no-dash separators, and an unclosed trailing fence. Loose
     never invents a REQUIRED field: a chunk with no recognizable verdict
     word is MALFORMED under both variants (the "garbled verdict token"
     unit test) — loose widens punctuation/case/fencing tolerance, never
     the field set.

Per-family disposition (returned for every family in `expected_families`,
independent of the others — a malformed or family-less fenced block must
never affect a SIBLING family's classification; the "standalone NONE
inside a bundled response" golden vector, §9, is exactly this property):

  * `PARSED`    — a block for this family was found and parses under the
                  chosen variant's grammar (case grammar AND, for strict,
                  fence closure). `verdict` is `"FLAG"` or `"NONE"`;
                  `mechanism` is the stated text (`None` for a bare NONE).
  * `MISSING`   — no attempt at a `Q-<family>`/`NO-DEFECT-<family>` tag is
                  found anywhere WITHIN THIS VARIANT's own scan surface
                  (strict: fenced blocks only; loose: fenced blocks +
                  unfenced text). In deployment this is "no answer" (§8):
                  scores NON-CATCH downstream UNLESS the OTHER variant's
                  co-read found the text unfenced instead — that
                  cross-variant composition is `scorer`'s, not this
                  function's (see point 1 above).
  * `MALFORMED` — a `Q-<family>` tag WAS located (there is text for this
                  question) but it fails the chosen variant's grammar (a
                  garbled verdict token, a FLAG with no stated mechanism,
                  trailing content the grammar cannot consume, or — strict
                  only — a fence that never closed; ALSO the disposition
                  when a family is located MORE THAN ONCE with conflicting
                  verdicts, §`_reconcile_occurrences`). `raw_block` carries
                  the offending text for the BORDERLINE lane (a
                  downstream, non-parser concern).

Every returned dict also carries `occurrences` (how many times the family
was located, 0 for MISSING) — see `_reconcile_occurrences` for the
multiplicity rule (repeat-with-agreement keeps the first occurrence;
repeat-with-conflict becomes MALFORMED with every raw block joined,
because the parser does not adjudicate which repeated answer is "the"
one).

Fence-block-per-family independence (not a single whole-document regex)
is the deliberate design choice that satisfies the "standalone NONE …
must not censor sibling blocks" vector and the "Sq-turn recap … preceding
a real block" vector simultaneously: recap prose sits OUTSIDE any fence
(only the turn's real answer is fenced, per the registered schema) and is
never scanned BY STRICT — a malformed or family-less fence contributes
nothing to its neighbors because every fenced block is chunked and
classified on its own. LOOSE's additional unfenced scan (finding 3(b))
does not weaken this: unfenced text is scanned as its OWN set of regions,
chunked and classified exactly like a fenced block, so a family-less or
malformed unfenced passage still cannot affect a sibling family's
disposition.

Deterministic by construction: every regex anchors on a single stripped
line (never spans an unbounded amount of free-form text with nested
quantifiers) and every quantifier is bounded (`{1,2}` numbering,
`{1,2}` dash runs) or anchored (`^…$`) — no catastrophic-backtracking
shape appears anywhere in this file.
"""
from __future__ import annotations

import re
from typing import Sequence

FAMILIES: tuple[str, ...] = ("boundary", "comparison", "exception", "sign", "units")
_FAMILY_ALT = "|".join(FAMILIES)

STATUSES = ("PARSED", "MISSING", "MALFORMED")
VARIANTS = ("strict", "loose")

# ------------------------------------------------------------------ fences
_FENCE_RE = re.compile(r"^\s{0,3}```")  # markdown fence rule: up to 3 spaces indent


def _extract_fenced_blocks(text: str) -> list[tuple[str, bool]]:
    """Return `(content, closed)` for every ``` … ``` region in `text`, in
    document order. Anything outside a fence (prose prefix, recap
    commentary, trailing remarks) is never returned — the parser only ever
    reads inside a fence, per the registered schema.

    ALWAYS tolerant of an unclosed trailing fence (its content is taken to
    run to end-of-text, `closed=False`) — fence-closure is not a presence
    question, it is a STRICT-GRAMMAR question, decided later per variant
    (`_parse_chunk`'s `require_closed_fence`). Locating the block the same
    way for both variants is what keeps "is this family MISSING" a single,
    variant-independent answer.
    """
    lines = text.splitlines()
    n = len(lines)
    blocks: list[tuple[str, bool]] = []
    i = 0
    while i < n:
        if _FENCE_RE.match(lines[i]):
            start = i + 1
            j = start
            closed = False
            while j < n:
                if _FENCE_RE.match(lines[j]):
                    closed = True
                    break
                j += 1
            if closed:
                blocks.append(("\n".join(lines[start:j]), True))
                i = j + 1
            else:
                blocks.append(("\n".join(lines[start:n]), False))
                i = n
        else:
            i += 1
    return blocks


def _unfenced_regions(text: str) -> list[str]:
    """The complement of `_extract_fenced_blocks`: every contiguous run of
    lines NOT inside a ``` fence, in document order. LOOSE-only scan
    surface (finding 3(b), design ruling): a well-formed but never-fenced
    `Q-<family>:`/`NO-DEFECT-<family>` answer is text that manifestly
    exists and must not be scored as though no answer were given at all.
    STRICT's fenced-only scope is UNCHANGED (the recap/preamble protection
    stays real — an unclosed trailing fence's content is already accounted
    for by `_extract_fenced_blocks`, so it is never double-counted here as
    unfenced too)."""
    lines = text.splitlines()
    n = len(lines)
    regions: list[str] = []
    current: list[str] = []
    i = 0
    while i < n:
        if _FENCE_RE.match(lines[i]):
            if current:
                regions.append("\n".join(current))
                current = []
            j = i + 1
            closed = False
            while j < n:
                if _FENCE_RE.match(lines[j]):
                    closed = True
                    break
                j += 1
            i = (j + 1) if closed else n  # unclosed trailing fence consumes the remainder
        else:
            current.append(lines[i])
            i += 1
    if current:
        regions.append("\n".join(current))
    return regions


# ------------------------------------------------------- presence detection
# Shared by BOTH variants: locates a chunk boundary for family <fam> whenever
# SOME text attempts to answer it — an optional list-numbering token, the
# family word (case-insensitive), an optional colon, then AT LEAST ONE more
# token (whatever verdict word follows, well-formed or not: "FLAG", "NONE",
# "MAYBE", ...). This is deliberately WIDER than either variant's grammar —
# it only ever answers "is there text here", never "does it parse" — so that
# a numbered prefix, wrong case, or a garbled verdict word is `MALFORMED`
# (text exists, grammar failed) rather than silently reported `MISSING`
# (which §8 reserves for "no text for that question"). Conflating the two
# would arm-differentially destroy demonstrated catches: a bundled (P) reply
# enumerating five answers is far more likely to pick up incidental
# numbering than a single-answer (S) reply, so a presence detector that
# required legal grammar to even LOCATE the chunk would inflate catch_S −
# catch_P for reasons having nothing to do with the treatment.
_NUM_PREFIX = r"(?:\d{1,2}[.)]\s*)?"
# Finding 6 (repair-set review): a word boundary — `(?=:|\s)` — is REQUIRED
# right after the family alternation, or a longer word merely starting with
# a family name ("Q-significance:") silently captures as that family
# ("sign") and its raw_block collides with the family's REAL answer inside
# `_reconcile_occurrences`, destroying a clean PARSED verdict into MALFORMED
# via the disagreement branch (confirmed: a poisoning "Q-significance: FLAG
# — note" line beside a real "Q-sign: NONE" answer). Grammar validation
# (`_S_HEAD_RE`/`_L_HEAD_RE` below) already requires this boundary
# implicitly (a literal `:` or the verdict word immediately follows the
# family group); presence detection did not.
_PRESENCE_ENTRY_START_RE = re.compile(
    rf"^{_NUM_PREFIX}Q-({_FAMILY_ALT})(?=:|\s):?\s*\S+", re.IGNORECASE)

# Finding 3(a) (repair-set review, design ruling): the question template's OWN
# registered instruction ("If NO, output NO-DEFECT-f") is a second legal
# answer SHAPE for a NONE verdict, standing alone (no `Q-<family>:` head at
# all). Presence detection recognizes it identically to the Q-<family> shape
# — wide/tolerant, case-insensitive, word-bounded against the same
# poisoning risk (`NO-DEFECT-significance` must never be family "sign").
_PRESENCE_OR_NO_DEFECT_RE = re.compile(
    rf"^{_NUM_PREFIX}(?:Q-({_FAMILY_ALT})(?=:|\s):?\s*\S+"
    rf"|NO-DEFECT-({_FAMILY_ALT})\b)",
    re.IGNORECASE,
)


def _entry_chunks(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split `lines` at every line matching `_PRESENCE_OR_NO_DEFECT_RE` (a
    NEW `Q-<family>` OR `NO-DEFECT-<family>` entry, family captured in
    whichever group matched, lower-cased); everything up to the next match
    (or end of block) is that entry's own continuation lines. Mirrors
    an earlier study's findings-parser chunker, generalized to carry the matched
    family label alongside each chunk (needed because one fenced block may
    legally carry more than one family's answer back to back)."""
    starts: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        m = _PRESENCE_OR_NO_DEFECT_RE.match(ln.strip())
        if m:
            starts.append((i, (m.group(1) or m.group(2)).lower()))
    if not starts:
        return []
    bounds = [i for i, _ in starts] + [len(lines)]
    return [(label, lines[bounds[k]:bounds[k + 1]]) for k, (_, label) in enumerate(starts)]


# ------------------------------------------------------------------- strict
_S_HEAD_RE = re.compile(rf"^Q-({_FAMILY_ALT}):\s*(FLAG|NONE)(?:\s+—\s+(.+))?$")

# -------------------------------------------------------------------- loose
# Tolerated noise (never a widened FIELD set, matching an earlier loose-parser precedent):
#   * the same leading list-numbering token as presence detection;
#   * case-insensitive family word and verdict word;
#   * an optional/missing colon after the family;
#   * a hyphen/en-dash/em-dash run (1-2 chars) OR plain whitespace as the
#     verdict/mechanism separator, in place of the registered em-dash.
_L_SEP = r"(?:\s*[-–—]{1,2}\s*|\s+)"
_L_HEAD_RE = re.compile(
    rf"^{_NUM_PREFIX}Q-({_FAMILY_ALT}):?\s*(FLAG|NONE)\b(?:{_L_SEP}(.+))?$", re.IGNORECASE)

_HEAD_RES: dict[str, re.Pattern] = {"strict": _S_HEAD_RE, "loose": _L_HEAD_RE}

# Finding 3(a)'s grammar half: `NO-DEFECT-<family>` parses as verdict NONE.
# STRICT requires the byte-exact registered token, alone on the head line
# (case-sensitive, no numbering, no trailing junk on that line — matching
# strict's exact-form posture everywhere else); LOOSE tolerates the same
# numbering/case noise as its `Q-<family>` grammar. Presence detection
# (above) already scopes WHERE each variant may see this token at all:
# STRICT only ever scans fenced blocks; LOOSE additionally scans unfenced
# text (`_unfenced_regions`, used only by `parse_response`'s loose branch)
# — so "in STRICT when it appears inside a fenced block, in LOOSE anywhere"
# falls out of the SCOPE these grammars are matched against, not out of the
# grammars themselves.
_ND_STRICT_RE = re.compile(rf"^NO-DEFECT-({_FAMILY_ALT})$")
_ND_LOOSE_RE = re.compile(rf"^{_NUM_PREFIX}NO-DEFECT-({_FAMILY_ALT})\b", re.IGNORECASE)
_ND_HEAD_RES: dict[str, re.Pattern] = {"strict": _ND_STRICT_RE, "loose": _ND_LOOSE_RE}


def _continuation_text(lines: list[str]) -> str | None:
    """All non-blank lines after a chunk's head line, joined with a single
    space. No indentation guard is needed here (unlike an earlier plain-text
    format): a chunk's lines are already bounded by the fence itself and
    by the next `Q-<family>:` line, so there is no trailing free-form doc
    prose that could get glommed on by mistake."""
    parts = [ln.strip() for ln in lines if ln.strip()]
    return " ".join(parts) if parts else None


_SEPARATOR_DEBRIS_RE = re.compile(r"^[\s\-–—]+")


def _strip_leading_separator_debris(inline_mech: str | None) -> str | None:
    """LOOSE's separator class (`_L_SEP`) has two alternatives (a dash run,
    or plain whitespace) so it can match a dangling end-of-line dash by
    falling back to its whitespace alternative and letting the dash itself
    fall inside the CAPTURED mechanism group (a dash with nothing after it
    on the same line has nowhere else to go, since `(.+)` demands >=1
    char). Left alone this glues a meaningless leading dash onto the
    mechanism text. Stripped here so the captured mechanism is never
    contaminated by which separator alternative happened to match — a
    symptom patch over `_L_SEP`'s fallback, named as such rather than
    left to read as designed semantics."""
    if not inline_mech:
        return None
    stripped = _SEPARATOR_DEBRIS_RE.sub("", inline_mech).strip()
    return stripped or None


def _parse_chunk(
    chunk_lines: list[str], head_re: re.Pattern, *, require_closed_fence: bool, closed: bool,
    no_defect_re: re.Pattern,
) -> tuple[str, str | None, str | None]:
    """Returns (status, verdict, mechanism) for one already-located chunk.
    status is PARSED or MALFORMED (never MISSING — a chunk exists by
    construction here; MISSING is decided one level up, by absence).
    `require_closed_fence` is the strict/loose fence-closure rule; `closed`
    is the fact about THIS block. `no_defect_re` is the variant's
    `NO-DEFECT-<family>` grammar (finding 3(a)) — checked FIRST: a chunk
    matching it is a complete NONE answer on its own, no `Q-<family>:` head
    required. The family captured by `no_defect_re` is discarded here (the
    caller already knows which family this chunk belongs to from presence
    detection) — exactly like `head_re`'s own discarded `_family` group
    below."""
    if require_closed_fence and not closed:
        # Strict's registered form lives inside a PROPERLY CLOSED fence;
        # text plainly exists (presence already located it) so this is a
        # format failure, never an invisible MISSING.
        return "MALFORMED", None, None
    first_line = chunk_lines[0].strip()
    if no_defect_re.match(first_line):
        return "PARSED", "NONE", _continuation_text(chunk_lines[1:])
    head = head_re.match(first_line)
    if not head:
        return "MALFORMED", None, None
    _family, verdict_raw, inline_mech = head.groups()
    verdict = verdict_raw.upper()
    inline = _strip_leading_separator_debris(inline_mech)
    continuation = _continuation_text(chunk_lines[1:])
    if inline and continuation:
        mechanism: str | None = f"{inline} {continuation}"
    else:
        mechanism = inline or continuation
    if verdict == "FLAG" and not mechanism:
        # The question demands "name the file, location, and mechanism" on
        # a FLAG; a FLAG with nothing stated is a format failure, never a
        # silently-accepted empty catch.
        return "MALFORMED", None, None
    return "PARSED", verdict, mechanism


def _reconcile_occurrences(occurrences: list[dict]) -> dict:
    """A family may legally be located MORE THAN ONCE (§7's per-question
    fence is the norm, but nothing stops a subject from also naming it in
    a preamble summary before the "details" section, or repeating a fence
    by accident) — this reconciles every located occurrence of ONE family
    into the single returned disposition, never silently picking the first
    one (that would have suppressed a real, later-stated catch: a bundled
    reply that summarizes first and details second is a shape §4.2's
    bundle topology invites and a single-question dispatch essentially
    cannot produce, so picking-the-first would arm-differentially bias P).

    * Zero occurrences → MISSING.
    * One occurrence → that occurrence's own disposition.
    * Two or more, all agreeing on the same `verdict` (including all
      MALFORMED, i.e. every occurrence's verdict is `None`) → the FIRST
      occurrence's fields (a benign repeat carries no ambiguity to judge).
    * Two or more, verdicts in genuine DISAGREEMENT → MALFORMED, verdict
      and mechanism `None`, `raw_block` = every occurrence's raw block
      joined (so the BORDERLINE lane sees the whole conflict rather than
      an arbitrarily chosen half) — the parser does not adjudicate which
      occurrence is "the" answer; picking by verdict (e.g. preferring
      FLAG) would be outcome-dependent selection.

    `occurrences` (the count) rides every returned dict — MC-P1's format-
    noncompliance read needs to know a family answered twice even when the
    two agree, and that fact does not survive a single-chunk return."""
    if not occurrences:
        return {"status": "MISSING", "verdict": None, "mechanism": None,
                "raw_block": None, "occurrences": 0}
    if len(occurrences) == 1:
        return {**occurrences[0], "occurrences": 1}
    verdicts = {o["verdict"] for o in occurrences}
    if len(verdicts) == 1:
        return {**occurrences[0], "occurrences": len(occurrences)}
    return {
        "status": "MALFORMED", "verdict": None, "mechanism": None,
        "raw_block": "\n---\n".join(o["raw_block"] for o in occurrences),
        "occurrences": len(occurrences),
    }


def parse_response(
    text: str | None, expected_families: Sequence[str], *, variant: str = "strict",
) -> dict[str, dict]:
    """Parse `text` for every family in `expected_families` under the named
    variant ("strict", the primary parser, or "loose", the registered
    robustness co-read). Returns `{family: {"status", "verdict", "mechanism",
    "raw_block", "occurrences"}}`, one entry per requested family,
    independent of whichever OTHER families are or are not present in the
    text (arm P passes all 5; arm S/Sq passes the single target family,
    per §4.2). `occurrences` is one field beyond the shape named in the
    build task (status/verdict/mechanism/raw_block) — added because
    without a count, a repeated-and-conflicting family (see
    `_reconcile_occurrences`) is indistinguishable downstream from a
    clean single MALFORMED, and MC-P1's format-noncompliance read needs
    the distinction."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown parser variant {variant!r}; expected one of {VARIANTS}")
    unknown = [f for f in expected_families if f not in FAMILIES]
    if unknown:
        raise ValueError(f"unknown family/families {unknown!r}; expected one of {FAMILIES}")

    head_re = _HEAD_RES[variant]
    no_defect_re = _ND_HEAD_RES[variant]
    require_closed_fence = variant == "strict"
    raw = text or ""
    scan_regions: list[tuple[str, bool]] = list(_extract_fenced_blocks(raw))
    if variant == "loose":
        # Finding 3(b) (design ruling): LOOSE additionally scans text OUTSIDE
        # any fence for well-formed heads — STRICT's fenced-only scope is
        # unchanged (`test_prose_outside_any_fence_is_never_scanned_for_a_
        # verdict` pins strict alone). `closed=True` on these regions is
        # inert: loose never requires a closed fence
        # (`require_closed_fence` is already False for loose).
        scan_regions += [(region, True) for region in _unfenced_regions(raw)]

    occurrences_by_family: dict[str, list[dict]] = {}
    for content, closed in scan_regions:
        for label, chunk_lines in _entry_chunks(content.splitlines()):
            status, verdict, mechanism = _parse_chunk(
                chunk_lines, head_re, require_closed_fence=require_closed_fence,
                closed=closed, no_defect_re=no_defect_re)
            occurrences_by_family.setdefault(label, []).append({
                "status": status,
                "verdict": verdict,
                "mechanism": mechanism,
                "raw_block": "\n".join(chunk_lines).strip(),
            })

    return {
        fam: _reconcile_occurrences(occurrences_by_family.get(fam, []))
        for fam in expected_families
    }
