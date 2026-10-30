"""presence.py — permissive PRESENCE + §9 scored-text extraction for the
corrected scoring pass (registration/amendments/2026-08-27-corrected-scoring-
pass.md; authored 2026-08-27, ANALYSIS layer — `answer_parser` stays regime-PINNED and
untouched; this module runs BESIDE it, never inside it).

Why this module exists (root cause found by the first independent recount,
methods/RECOUNT.md):
the pinned parser's presence grammars were authored from IMAGINED
noncompliance shapes and scored 978 text-present rows as MISSING — "present
but malformed → judged" (§8) collapsed into "no text → silent non-catch",
deleting 132 key-matched target FLAGs one-directionally. §8's registered
disposition is: MISSING ENTIRELY (no text for the question) → NON-CATCH /
SILENT; PRESENT but failing the strict grammar → the BORDERLINE lane ("text
exists; it gets judged"). Presence must therefore be judged PERMISSIVELY and
grammars may be strict about PARSING, never about EXISTENCE.

What "the text for the question" IS, per arm (§9's scored text):

  * arms S and Sq — §9: "the block from that question's turn — turn text
    only, never the session transcript." A single-family dispatch/turn
    carries exactly one question's answer, so when no registered fenced
    block parses, the WHOLE TURN is the text that exists for that question.
    No family label is required for presence: a turn that answers under the
    wrong family label, under no label, or as bare `FLAG — …` prose is text
    for the question it was asked (the lane judges what it asserts; the V3
    co-read in `coreads` is the label-respecting punitive reading).
    Presence for S/Sq = the turn is non-empty after stripping.
  * arm P — the bundle carries all five answers; the text for family f is
    the SEGMENT that f's own marker opens: from the first line carrying a
    live-shape marker for f (below) to the line before the next marker for a
    DIFFERENT family (or end of bundle). Same-family repeats stay inside the
    segment (the lane, not this module, adjudicates a conflicting repeat).
    No marker for f anywhere → MISSING (genuinely no text for f).

Live-shape marker grammar — authored from the LIVE residual inventory
(471 strict-MISSING ∧ ¬loose-PARSED rows; P marker-line shapes observed:
`Q-<F>: NO-DEFECT-<F>` unfenced ×35, `## Q-<F>` ×15, `Q-<F>:` head-only ×8,
`## Q-<F>:` ×6, `**Q-<F>:** NO-DEFECT-<F>` ×4, `## Q-<F>: NO-DEFECT-<F>` ×4,
`# Q-<F>:` ×2, `# Q-<F>` ×2, bold/heading variants ×3, no marker ×1; S/Sq
marker shapes add `FLAG-<F>:` and `**NO-DEFECT-<F>**`), NOT from imagined
shapes: a line is a marker for family f when, after stripping leading
markdown decoration (heading hashes, bold/italic stars and underscores,
backticks, blockquote `>`, list bullets, 1–2 digit numbering), it begins
with `Q-<f>`, `NO-DEFECT-<f>`, `FLAG-<f>` or `NONE-<f>` — case-insensitive,
word-bounded after the family (`Q-significance` is never family `sign`,
the pinned parser's finding-6 poisoning vector, preserved here).

Retention normalization (`normalize_for_retention`): the corrected pass keeps
an EXISTING lane verdict only where the text the adjudicator saw equals the
corrected scored text once fence-only lines are dropped and whitespace is
collapsed — a verdict composes against §9's scored text or it is re-laned
(ruled 2026-08-27; blanket retention would hand the independent re-recount
the exact defect class this pass repairs). Old verdicts are kept, never
overwritten; the corrected table cites the new ones.

Nothing here decides FLAG/NONE: `compose_with_presence` only re-routes the
one registered divergence — strict-MISSING ∧ ¬loose-PARSED ∧ permissive-
PRESENT — from mechanical NON-CATCH/SILENT to the BORDERLINE lane, and
attaches `scored_text`/`presented_block` so downstream key-matching (the
lane merge) reads §9's text rather than a parser fragment. Every other row
keeps the registered chain's disposition byte-for-byte.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Mapping

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from answer_parser import FAMILIES  # noqa: E402

_FAMILY_ALT = "|".join(FAMILIES)

# Leading markdown decoration a live weak-tier response puts before a marker:
# heading hashes, bold/italic stars/underscores, backticks, blockquote, list
# bullets (- * +), and 1–2 digit numbering ("1." / "1)"). Bounded quantifiers;
# every regex anchors on ONE stripped line (no catastrophic-backtracking
# shape, same discipline as the pinned parser).
_DECOR = r"(?:[\s#>*_`~+\-]{0,12}(?:\d{1,2}[.)])?[\s#>*_`~+\-]{0,12})"
MARKER_RE = re.compile(
    rf"^{_DECOR}(?:Q-|NO-DEFECT-|FLAG-|NONE-)({_FAMILY_ALT})\b", re.IGNORECASE)

_FENCE_ONLY_RE = re.compile(r"^\s{0,3}```[^`\n]*$")
_WS_RE = re.compile(r"\s+")

ROUTES = ("strict-parsed", "strict-malformed", "loose-parsed",
          "permissive-present", "missing")


def marker_family(line: str) -> str | None:
    """The family a line's live-shape marker names, lower-cased, or None."""
    m = MARKER_RE.match(line.strip())
    return m.group(1).lower() if m else None


def _trim_dangling(lines: list[str]) -> list[str]:
    """Drop blank and fence-only lines from BOTH ends of a segment (a segment
    cut at the next family's marker otherwise ends on the previous block's
    closing fence + the next block's opening fence). Interior lines are
    verbatim."""
    def _dangling(ln: str) -> bool:
        return not ln.strip() or bool(_FENCE_ONLY_RE.match(ln))
    lo, hi = 0, len(lines)
    while lo < hi and _dangling(lines[lo]):
        lo += 1
    while hi > lo and _dangling(lines[hi - 1]):
        hi -= 1
    return lines[lo:hi]


def p_segment(text: str | None, family: str) -> dict:
    """Arm P: the text for `family` in a bundle — from its FIRST marker line
    to the line before the next DIFFERENT-family marker (or end of text).
    Returns {"present", "text", "marker_line", "start", "end"}; `text` is
    None when no marker for the family exists anywhere in the bundle."""
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; expected one of {FAMILIES}")
    lines = (text or "").splitlines()
    markers = [(i, fam) for i, ln in enumerate(lines)
               if (fam := marker_family(ln)) is not None]
    start = next((i for i, fam in markers if fam == family), None)
    if start is None:
        return {"present": False, "text": None, "marker_line": None,
                "start": None, "end": None}
    end = next((i for i, fam in markers if i > start and fam != family), len(lines))
    seg = _trim_dangling(lines[start:end])
    return {"present": True, "text": "\n".join(seg), "marker_line": lines[start].strip(),
            "start": start, "end": end}


def turn_text(text: str | None) -> dict:
    """Arms S/Sq: the whole turn is the text for the turn's question.
    Present iff non-empty after stripping; no label is required."""
    t = (text or "").strip()
    return {"present": bool(t), "text": t or None, "marker_line": None}


def scored_text(arm: str, text: str | None, family: str) -> dict:
    """§9's scored text for one (arm, family) when the registered grammar
    found no parseable block — dispatches on arm."""
    if arm == "P":
        return p_segment(text, family)
    if arm in ("S", "Sq"):
        return turn_text(text)
    raise ValueError(f"unknown arm {arm!r}; expected P, S or Sq")


def normalize_for_retention(s: str | None) -> str:
    """Fence-only lines dropped, whitespace collapsed, ends stripped — the
    equality under which an existing lane verdict is retained."""
    lines = [ln for ln in (s or "").splitlines() if not _FENCE_ONLY_RE.match(ln)]
    return _WS_RE.sub(" ", "\n".join(lines)).strip()


def compose_with_presence(row: Mapping, *, arm: str, text: str | None) -> dict:
    """Overlay presence on a registered-chain row (`score_target_question` /
    `score_off_family_question` output). Adds `route`, `presence`,
    `presence_marker`, `scored_text`; sets `presented_block` on every
    BORDERLINE row to §9's text; re-routes ONLY strict-MISSING ∧ ¬loose-
    PARSED ∧ permissive-PRESENT rows from mechanical NON-CATCH/SILENT to
    BORDERLINE. Never touches a PARSED row's disposition or `raw_block`."""
    new = dict(row)
    fam = row["family"]
    strict, loose = row["parser_strict_status"], row["parser_loose_status"]
    ext = scored_text(arm, text, fam)
    if strict == "PARSED":
        new["route"] = "strict-parsed"
        new["presence"] = "PRESENT"
        new["scored_text"] = row.get("raw_block")
        new["presence_marker"] = None
        return new
    if strict == "MALFORMED":
        new["route"] = "strict-malformed"
    elif loose == "PARSED":
        new["route"] = "loose-parsed"
    elif ext["present"]:
        new["route"] = "permissive-present"
        if row["status"] not in ("NON-CATCH", "SILENT"):
            raise ValueError(
                f"strict-MISSING/¬loose-PARSED row carries unexpected status "
                f"{row['status']!r} (family {fam}, arm {arm})")
        new["status"] = "BORDERLINE"
        if "hit" in new:
            new["hit"] = None
        new.pop("key_matched_wrong_family", None)
    else:
        new["route"] = "missing"
        new["presence"] = "MISSING"
        new["scored_text"] = None
        new["presence_marker"] = None
        if row["status"] not in ("NON-CATCH", "SILENT"):
            raise ValueError(
                f"permissive-MISSING row carries unexpected status "
                f"{row['status']!r} (family {fam}, arm {arm})")
        return new
    if not ext["present"]:
        # the pinned grammars located text this module's marker set does not
        # — impossible by construction (its presence regexes are a subset);
        # refuse rather than present nothing to the lane.
        raise ValueError(
            f"parser located text for {fam} ({strict}/{loose}) but permissive "
            f"extraction found no marker — marker grammar is not a superset")
    new["presence"] = "PRESENT"
    new["scored_text"] = ext["text"]
    new["presence_marker"] = ext["marker_line"]
    if new["status"] == "BORDERLINE":
        new["presented_block"] = ext["text"]
    return new
