"""zc.py -- the three registered degenerate responders + the J gate.

Analysis-helper file: never trial-time, no regime hash. Imports
`parse_response`/`FAMILIES` from `answer_parser` and
`score_target_question`/`score_off_family_question` from `scorer` -- NEVER
re-implements parsing or key-matching (single-parser/single-scorer rule).
This file only adds: three pure-function zero-comprehension responders
(registration §5.5, as amended by the rev-2.2 N-e disposition, §22b), the J
metric, and the gate that composes §5.5's LOCK CONSEQUENCE.

**What "J" is, and how that was resolved (no formula appears in the
registration text itself):** the shortcut-gate rule this registration
inherits states the formula in one line: "each trigger item ships a matched
no-trigger twin; hit rate from triggers, false-alarm rate from twins,
**J = hits - FA co-reported**. A model that refutes everything scores 100%
hits and J ~= 0", and "any degenerate responder reaching J >~ 0.8 means the
pairs measure a shortcut". This is Youden's J statistic (TPR - FPR) under a
different name, and `compute_j` implements it literally. Confirmed against
the independent pre-lock review's own account of why flag-all-five is
rejected (N-e, rev 2.2): "if it flags all five families its false-alarm
load suppresses J and the gate reads weaker than the bank is" -- this
sentence is coherent ONLY under a TPR-FPR formula (flagging everything
drives FPR to 1.0 in lockstep with TPR, collapsing J toward 0 even though
raw catch/hit rate is maximal); it is NOT coherent under a naive "fraction
correct per class" reading (which flag-all-five would instead maximize on
every defective class, forcing mass BANKFAIL -- the opposite of "reads
weaker").

**Class granularity (resolved the same way):** §5.5's lock-consequence tuple
reads "any item class (mf/sf x defective/clean, per question family)". This
is NOT read as 20 independently-scored classes (5 families x 2 x 2); it is
read as **10 strata** (5 families x mf/sf), each stratum's ONE J number
computed from TWO item populations that the tuple's "defective/clean" phrase
names: the TARGET population (items whose own `defect_class` equals this
stratum's family -- the "triggers") supplies the hit-rate/TPR term, and the
NONTARGET population (every other item in the same mf/sf bucket: clean items
AND items whose real defect is a DIFFERENT family -- the "twins") supplies
the false-alarm-rate/FPR term. A 20-class "correctness rate per class"
reading was considered and rejected: under it, every CLEAN class clears
trivially (ZC-2's constant-NONE policy scores 1.0 on every clean class by
construction; ZC-1 scores >=0.8 on every clean class for free, since 4 of 5
per-item family questions are correct-NONE with zero signal) -- guaranteeing
mass replacement by design, which a three-round reviewed registration cannot
have intended, and which does not square with the flag-all-five sentence.

Build-time note: this reading is the strongest available from the primary
sources (the inherited formula + the flag-all-five sentence's own internal
coherence), but the registration never restates the formula in its own
text. `compute_j` returns every component (`tpr`, `fpr`, `j`, `hits`,
`false_alarms`, `n_target`, `n_nontarget`) rather than a bare float so a
different composition ruled at freeze is arithmetic over the returned dict,
not a rebuild.

**"Verdict layer" and the registration's verdict-only ban -- these do not
conflict.** §5.2/§20 ban a verdict-only SUBJECT endpoint (nothing in
H-B1..H-B4 may key on verdict alone). §5.5 registers "verdict layer" scoring
for the ZC degenerate responders specifically -- a pre-freeze
MATERIALS-VALIDITY diagnostic, never a reported study endpoint. The two are
different objects; this file implements the verdict-layer check locally
(reading an already-`answer_parser`-parsed `verdict` field is not "a second
parser") precisely because `scorer` deliberately does NOT expose a bare
verdict-only function (its own docstring: "NOT graduated:
verdict_only_rate / gap").

**Item / key-table shape (generic; written before the trial runner and the
freeze lane's key table existed -- mirrors `materials/manifest.jsonl`'s own
field names where they overlap):**

    item = {
        "item_id": str,
        "item_class": "multi_file" | "single_function",   # the mf/sf axis
        "defect_class": one of FAMILIES, or "clean",
        "defect_keys": Sequence[str],                       # [] for clean
        "allowed_families": Sequence[str] = (),              # §5.3 MULTI-
                                                              # FAMILY ALLOWANCE
        "text": str,            # OR "files": [{"path","content"}, ...]
    }

`item_class` values are the bank's own literal strings (confirmed against
`materials/items/*.json`) -- "single_function", never "single_file" despite
the registration's shorthand "sf"; disclosed once here rather than silently
remapped.

ZC-1's "diff hunk headers/identifiers" scan pool: the bank's item payloads
ship as (path, content) file pairs, not literal unified diffs -- no `@@` hunk
markers exist in the materials as built. `_scan_pool` maps the registered
phrase onto the closest structural analogue actually available (def/class
signature lines, file paths) while ALSO recognizing true diff markers (`@@`
hunk headers, `diff --git`, `+++`/`---` file lines) should `item["text"]` ever
carry a literal diff -- so the scan pool is correct either way materials end
up shaped. Comments, docstrings, and free prose are never scanned (that would
not be "content-blind" -- it would be reading semantics).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from answer_parser import FAMILIES, parse_response  # noqa: E402
from scorer import score_off_family_question, score_target_question  # noqa: E402

MF, SF = "multi_file", "single_function"
ITEM_CLASSES = (MF, SF)
LAYERS = ("verdict", "keyed")

_EM_DASH = "—"


# ============================================================ item plumbing
def _item_text(item: Mapping) -> str:
    """The stimulus text a responder reads (ZC-1/ZC-3) or ignores (ZC-2).
    Prefers an explicit `text` field (a literal diff, if one is ever
    supplied); falls back to concatenating `files` with an injected path
    marker line so file identity is still part of the content-blind scan
    pool even when no true diff exists."""
    if item.get("text"):
        return item["text"]
    parts = []
    for f in item.get("files", ()):
        parts.append(f"--- {f.get('path', '')} ---\n{f.get('content', '')}")
    return "\n\n".join(parts)


def build_key_table(items: Sequence[Mapping]) -> dict[str, dict]:
    """The small, freeze-committable metadata table (§5.7 item 2's shape):
    item_id -> {item_class, defect_class, defect_keys, allowed_families}.
    Deliberately excludes the stimulus text -- that stays in `items` /
    `responses`, never duplicated into the key table."""
    return {
        it["item_id"]: {
            "item_class": it["item_class"],
            "defect_class": it["defect_class"],
            "defect_keys": tuple(it.get("defect_keys", ())),
            "allowed_families": tuple(it.get("allowed_families", ())),
        }
        for it in items
    }


def build_responses(items: Sequence[Mapping], responder: Callable[[Mapping], str]) -> dict[str, str]:
    """item_id -> the responder's full 5-block formatted response text.
    `responder` is one of `zc1_response_text` / `zc2_response_text` /
    a `zc3_response_text` partial."""
    return {it["item_id"]: responder(it) for it in items}


def _format_response(selected: str | None, mechanism: str | None) -> str:
    """Byte-exact strict grammar (`answer_parser._S_HEAD_RE`): one CLOSED fence
    per family, `Q-<family>: FLAG|NONE` with a literal ` -- ` (em dash)
    mechanism separator on FLAG. `selected` is a SINGLE family or None --
    every responder in this file is structurally incapable of flagging more
    than one family per item (the flag-all-five shape is rejected by
    construction here, not just by policy, per §5.5's N-e disposition)."""
    if selected is not None and selected not in FAMILIES:
        raise ValueError(f"unknown family {selected!r}")
    blocks = []
    for f in FAMILIES:
        if f == selected:
            mech = mechanism or "(content-blind match; no mechanism stated)"
            blocks.append(f"```\nQ-{f}: FLAG {_EM_DASH} {mech}\n```")
        else:
            blocks.append(f"```\nQ-{f}: NONE\n```")
    return "\n".join(blocks)


# ================================================================== ZC-1
# Content-blind keyword responder (§5.5): FLAGs the family whose keywords
# appear in the diff's hunk headers/identifiers; never reads semantics --
# these lists are drawn from vocabulary intrinsic to the FIVE FROZEN FAMILY
# DEFINITIONS themselves (registration/amendments/2026-08-17-family-
# definitions.md) plus their common snake_case/camelCase code-identifier
# variants -- never from any item's own curated `defect_keys`, which would
# make this a content-AWARE responder instead. Authored as the STRONGEST
# content-blind attempt the builder can make (the same "make it strong" bar
# the mechanism strings below are held to), since a weak adversary would
# understate the bank's real shortcut exposure.
ZC1_FAMILY_SURFACE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "boundary": ("range", "index", "slice", "bound", "limit", "loop", "window",
                 "edge", "last", "first", "len", "off_by_one", "offbyone", "-1", "+1"),
    "sign": ("sign", "negat", "invert", "subtract", "add", "minus", "plus",
             "delta", "direction", "flip"),
    "exception": ("except", "try", "catch", "raise", "error", "fail", "exc",
                  "handler", "swallow"),
    "units": ("unit", "scale", "factor", "convert", "second", "millisecond",
              "percent", "fraction", "byte", "kilobyte", "rate", "ratio"),
    "comparison": ("compare", "less", "greater", "equal", "swap", "operator",
                   "cmp", "threshold", "gt", "lt", "eq", "ge", "le"),
}

_HUNK_HEADER_RE = re.compile(r"^@@[^\n]*@@[^\n]*$", re.MULTILINE)
_DIFF_GIT_RE = re.compile(r"^diff --git .+$", re.MULTILINE)
_DIFF_FILE_LINE_RE = re.compile(r"^[+-]{3} .+$", re.MULTILINE)
_DEF_CLASS_LINE_RE = re.compile(r"^\s*(?:def|class)\s+.+$", re.MULTILINE)
_PATH_MARKER_RE = re.compile(r"^--- .+ ---$", re.MULTILINE)


def _scan_pool(text: str) -> str:
    """Content-blind scan pool: hunk headers + diff file markers (present
    only if `text` is a literal diff) + def/class signature lines + injected
    file-path markers. Never comments, docstrings, or free prose -- see
    module docstring."""
    lines = (
        _HUNK_HEADER_RE.findall(text)
        + _DIFF_GIT_RE.findall(text)
        + _DIFF_FILE_LINE_RE.findall(text)
        + _DEF_CLASS_LINE_RE.findall(text)
        + _PATH_MARKER_RE.findall(text)
    )
    return "\n".join(lines)


def zc1_select_family(text: str) -> tuple[str | None, dict[str, int]]:
    """Content-blind family selection: argmax keyword-hit count over the
    scan pool, case-insensitive substring count (a keyword may appear more
    than once). Deterministic tie-break: canonical `FAMILIES` order. Never
    flags with zero signal (all-zero counts -> None, no family selected) --
    a responder that flagged unconditionally would not be "content-blind
    keyword", it would be a disguised flag-one-family-always policy."""
    pool_low = _scan_pool(text).lower()
    counts = {f: sum(pool_low.count(kw.lower()) for kw in ZC1_FAMILY_SURFACE_KEYWORDS[f])
              for f in FAMILIES}
    best = max(counts.values())
    if best == 0:
        return None, counts
    for f in FAMILIES:
        if counts[f] == best:
            return f, counts
    raise AssertionError("unreachable: FAMILIES is exhaustive")  # pragma: no cover


def zc1_response_text(item: Mapping) -> str:
    """ZC-1's full 5-block response for one item. The stated mechanism is
    itself content-blind: it names the matched keyword(s), never any
    semantic claim about what the code does."""
    text = _item_text(item)
    family, counts = zc1_select_family(text)
    if family is None:
        return _format_response(None, None)
    matched = [kw for kw in ZC1_FAMILY_SURFACE_KEYWORDS[family] if kw.lower() in _scan_pool(text).lower()]
    mechanism = f"keyword match in identifiers: {', '.join(matched[:3])}"
    return _format_response(family, mechanism)


# ================================================================== ZC-2
# Template-targeted responder (§5.5): "never reads the diff" -- a policy
# fixed at authoring time, item-content-independent by construction (no
# function below takes `item` for anything other than call-signature
# uniformity with ZC-1/ZC-3). "Base-rate play on the 1-of-5 target structure
# and the 3:1 defective:clean ratio": ANY diff-blind constant per-family
# FLAG/NONE assignment is Youden-degenerate -- P(FLAG | target) and
# P(FLAG | non-target) are IDENTICAL for a policy that never looks at the
# item (both equal the policy's own constant), so TPR == FPR and J == 0 in
# EVERY stratum, for EVERY possible choice of policy. This is not a bug in
# the choice below; it is the exact base-rate-floor property the inherited
# formula guarantees ("a model that refutes everything scores 100% hits and
# J ~= 0") and is asserted directly as a test (`TestZC2StructuralNullJ`).
# `ZC2_POLICY` flags exactly one family (rather than none, or all five) so
# the identity is demonstrated non-vacuously: TPR and FPR both land at a
# real, non-zero, EQUAL value for "boundary" rather than trivially at 0/0.
ZC2_POLICY: dict[str, str] = {
    "boundary": "FLAG",
    "comparison": "NONE",
    "exception": "NONE",
    "sign": "NONE",
    "units": "NONE",
}
_ZC2_MECHANISM = "template-targeted base-rate policy (item content not read)"


def zc2_response_text(item: Mapping) -> str:  # noqa: ARG001 -- item unread by design
    flagged = [f for f, v in ZC2_POLICY.items() if v == "FLAG"]
    selected = flagged[0] if flagged else None
    return _format_response(selected, _ZC2_MECHANISM if selected else None)


# ================================================================== ZC-3
# Composite responder (§5.5, N-e disposition, §22b): family selection by
# ZC-1's keyword policy (registered primary) OR ZC-2's base-rate policy
# (registered variant) -- "publish the better of the two" -- PLUS the
# author's best family-generic mechanism string per family, scored THROUGH
# THE REAL SCORER (key-match), never at the verdict layer. These strings are
# the REGISTERED ADVERSARIAL CONTENT: authored to be the most key-overlapping
# generic phrasing crafted per family from the five frozen definitions --
# natural-language restatements close enough to how a real author would
# phrase a `defect_keys` entry that they legitimately collide with curated
# keys on some items (the A-5 hazard the through-scorer requirement exists
# to measure, not suppress). A flag-all-five policy is explicitly NOT used
# here (§5.5, N-e) -- `_format_response`'s single-family shape makes that
# structurally impossible, not merely policy-avoided.
ZC3_GENERIC_MECHANISM: dict[str, str] = {
    "boundary": "off by one in the loop bound; the range excludes the last element",
    "sign": "the sign is inverted; a value is added where it should be subtracted",
    "exception": "the error is swallowed silently; the exception is caught too broadly and never re-raised",
    "units": "the conversion factor is wrong; a value is combined at the wrong scale, e.g. seconds vs milliseconds",
    "comparison": "the comparison is inverted; the operands are compared in the wrong direction",
}

ZC3_FAMILY_SELECTIONS = ("keyword", "base_rate")


def zc3_response_text(item: Mapping, *, family_selection: str = "keyword") -> str:
    if family_selection == "keyword":
        family, _ = zc1_select_family(_item_text(item))
    elif family_selection == "base_rate":
        flagged = [f for f, v in ZC2_POLICY.items() if v == "FLAG"]
        family = flagged[0] if flagged else None
    else:
        raise ValueError(f"unknown family_selection {family_selection!r}; "
                          f"expected one of {ZC3_FAMILY_SELECTIONS}")
    if family is None:
        return _format_response(None, None)
    return _format_response(family, ZC3_GENERIC_MECHANISM[family])


# =========================================================== the J metric
def _verdict_positive(text: str, family: str) -> bool:
    """The verdict-layer criterion: FLAG regardless of key match. Reads an
    already-`parse_response`-parsed field -- not a second parser."""
    return parse_response(text, [family], variant="strict")[family].get("verdict") == "FLAG"


def _is_positive_target(defect_keys: Sequence[str], text: str, family: str, *, layer: str) -> bool:
    if layer == "verdict":
        return _verdict_positive(text, family)
    row = score_target_question(text, family, defect_keys)
    return row["status"] == "CATCH"


def _is_false_alarm(defect_keys: Sequence[str], allowed_families: Sequence[str],
                     text: str, family: str, *, layer: str) -> bool:
    if layer == "verdict":
        return _verdict_positive(text, family)
    row = score_off_family_question(text, family, item_defect_keys=defect_keys,
                                     allowed_families=allowed_families)
    return row["status"] == "FA"


def compute_j(
    family: str,
    item_class: str,
    responses: Mapping[str, str],
    key_table: Mapping[str, Mapping],
    *, layer: str = "keyed",
) -> dict:
    """J for ONE (family, mf/sf) stratum -- see module docstring for the
    formula and its provenance. `responses` is item_id -> the responder's
    full formatted text (`build_responses`'s output); `key_table` is
    item_id -> metadata (`build_key_table`'s output). TARGET population =
    this stratum's own family's defective items (the "triggers", supplies
    TPR); NONTARGET population = every other item in the same mf/sf bucket
    -- clean items AND other-family-defective items (the "twins", supplies
    FPR). Refuses (never silently zero-divides) on an empty population --
    house style, `scorer.wilson_ci`'s precedent."""
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; expected one of {FAMILIES}")
    if item_class not in ITEM_CLASSES:
        raise ValueError(f"unknown item_class {item_class!r}; expected one of {ITEM_CLASSES}")
    if layer not in LAYERS:
        raise ValueError(f"unknown layer {layer!r}; expected one of {LAYERS}")

    pool_ids = [iid for iid, meta in key_table.items() if meta["item_class"] == item_class]
    target_ids = [iid for iid in pool_ids if key_table[iid]["defect_class"] == family]
    nontarget_ids = [iid for iid in pool_ids if key_table[iid]["defect_class"] != family]
    if not target_ids or not nontarget_ids:
        raise SystemExit(
            f"compute_j: empty {'target' if not target_ids else 'nontarget'} population for "
            f"family={family!r} item_class={item_class!r}; refusing an undefined J")

    hits = sum(
        1 for iid in target_ids
        if _is_positive_target(key_table[iid]["defect_keys"], responses[iid], family, layer=layer)
    )
    false_alarms = sum(
        1 for iid in nontarget_ids
        if _is_false_alarm(key_table[iid]["defect_keys"], key_table[iid]["allowed_families"],
                            responses[iid], family, layer=layer)
    )
    tpr = hits / len(target_ids)
    fpr = false_alarms / len(nontarget_ids)
    return {
        "family": family, "item_class": item_class, "layer": layer,
        "tpr": tpr, "fpr": fpr, "j": tpr - fpr,
        "hits": hits, "n_target": len(target_ids),
        "false_alarms": false_alarms, "n_nontarget": len(nontarget_ids),
    }


# ================================================================ the gate
J_LOCK_THRESHOLD = 0.8  # §5.5 / N-2 (rev-2.2 wording fixed): "J >= 0.8"


def zc_gate(items: Sequence[Mapping], *, threshold: float = J_LOCK_THRESHOLD) -> dict:
    """Runs every REGISTERED responder at its REGISTERED scored layer over
    every (family, mf/sf) stratum and names which strata clear at
    J >= threshold under ANY of them (§5.5's lock consequence: "any item
    class ... cleared ... by ANY registered responder at its scored layer
    is re-authored or dropped ... one replacement round"). Registered set:
    ZC-1 verdict, ZC-1 keyed, ZC-2 verdict (ZC-2 is never run through the
    real scorer, §5.5), ZC-3 keyed (published as max(keyword, base_rate)
    per N-e's "the better of the two published"). `items` should already be
    the AUDIT-SURVIVING pool (§5.3) -- this function does not filter for
    that; the caller passes the audit-surviving pool."""
    key_table = build_key_table(items)
    responses_zc1 = build_responses(items, zc1_response_text)
    responses_zc2 = build_responses(items, zc2_response_text)
    responses_zc3_kw = build_responses(items, lambda it: zc3_response_text(it, family_selection="keyword"))
    responses_zc3_br = build_responses(items, lambda it: zc3_response_text(it, family_selection="base_rate"))

    results: dict[tuple[str, str], dict] = {}
    cleared: list[dict] = []
    for family in FAMILIES:
        for item_class in ITEM_CLASSES:
            zc1_v = compute_j(family, item_class, responses_zc1, key_table, layer="verdict")
            zc1_k = compute_j(family, item_class, responses_zc1, key_table, layer="keyed")
            zc2_v = compute_j(family, item_class, responses_zc2, key_table, layer="verdict")
            zc3_kw = compute_j(family, item_class, responses_zc3_kw, key_table, layer="keyed")
            zc3_br = compute_j(family, item_class, responses_zc3_br, key_table, layer="keyed")
            zc3_published = zc3_kw if zc3_kw["j"] >= zc3_br["j"] else zc3_br
            zc3_published = {**zc3_published, "variant": "keyword" if zc3_published is zc3_kw else "base_rate"}

            named = {"zc1_verdict": zc1_v, "zc1_keyed": zc1_k, "zc2_verdict": zc2_v,
                     "zc3_published": zc3_published}
            results[(family, item_class)] = named
            best_key = max(named, key=lambda k: named[k]["j"])
            if named[best_key]["j"] >= threshold:
                cleared.append({"family": family, "item_class": item_class,
                                 "j": named[best_key]["j"], "source": best_key})

    return {"threshold": threshold, "results": results, "cleared": cleared, "locks": not cleared}


def main() -> int:  # pragma: no cover - manual smoke entry, no CLI surface registered
    print("zc: analysis-helper module, no CLI. Import zc1_response_text / "
          "zc2_response_text / zc3_response_text / compute_j / zc_gate.", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
