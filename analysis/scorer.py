"""scorer.py — per-question scoring primitives.

Analysis-helper file: never trial-time, no regime hash, freely fixable.
Consumes `answer_parser.parse_response` (NEVER re-implements a second parser
— single-parser rule) and composes
the registered §8/§10 disposition routing + the §5.2/§5.3/§11.4 scoring rules
on top of it. Does NOT implement the H-B1..H-B4 Holm-family / interpretation-
cell (§12) composition — that endpoint-orchestration layer is a separate
consumer of this module's per-question rows (`endpoints.py`); this file supplies
arithmetic and disposition, not judgment about which cell a study lands in.

**PARENT graduation (the bank-calibration study's scorer) — exactly, with
deltas stated:**

* `is_instrument_failure` graduates `is_error_trial` UNCHANGED in its
  fail-safe posture (absent field -> error, never assumed clean) and ADDS
  the two independent signals §16 names explicitly (`api_error_status`,
  `terminal_reason == "api_error"`) that the parent's regime never
  carried — this study's §16 requires checking these BEFORE any gate reads a
  response; folding them into the same classifier keeps that check in one
  place rather than duplicated at every call site.
* `family_hit` graduates `placement_hit`'s core rule (verdict == the
  "positive" token AND >=1 `defect_keys` substring match, case-insensitive)
  EXACTLY — §5.2's "per-question hit = FLAG verdict AND `keys_matched`
  non-empty" is placement_hit's "BUG verdict AND >=1 defect_keys match"
  restated for the family-question schema. Two deltas, both consequences
  of taking an ALREADY-PARSED entry rather than raw response text: (1) no
  separate verdict regex — `answer_parser` already extracted `verdict`;
  (2) the match scope is `raw_block` (the SINGLE located answer block for
  ONE family), never the whole response — §9 registers `raw_block` as the
  scored text, a narrower and more precise scope than the parent's
  whole-response-minus-fences scan (there is no cross-family echo risk to
  guard against inside one already-isolated block, so no fence-stripping
  step is needed here; the parser already only ever reads inside fences).
* `wilson_ci` graduates UNCHANGED (byte-identical formula; carried for the
  per-item/per-cell CI reads this module's callers need without a second
  Wilson implementation appearing anywhere in this tree).
* **NOT graduated:** `verdict_only_rate` / `gap` (the parent's verdict-only
  descriptive). §5.2 states "no verdict-only endpoint exists anywhere in
  this registration" and §20 repeats the ban explicitly — carrying that
  field forward would hand a downstream reader a banned number under a
  familiar name. The registered adjacent descriptive is §11.3's per-item
  FLAG-count distribution per arm (`flag_count`, below), built fresh.

**§8/§10 disposition routing (the load-bearing new logic, not in the
parent):** every question-row's parser status composes to EXACTLY one of
CATCH / NON-CATCH / BORDERLINE (target questions) or FA / HIT-ALT / NO-FLAG
/ SILENT / BORDERLINE (off-family questions) by ONE fixed rule, applied
identically to strict and loose as independent co-reads (§9's robustness
commitment: "conclusions shown invariant or the divergence disclosed" —
never a strict-then-loose FALLBACK chain, matching `answer_parser`'s own
docstring on this exact point):

  * parser status MISSING  -> mechanically NON-CATCH (target) / SILENT
    (off-family) — "in deployment, no answer is no answer" (§8), never
    re-drawn, never sent to a human.
  * parser status MALFORMED -> BORDERLINE, UNCONDITIONALLY — "text exists;
    it gets judged" (§8/§10). This holds even when the LOOSE parse of the
    same block recovers a clean verdict: the loose reading rides along as
    `co_read_loose_status` / `co_read_divergence` for the adjudicator and
    for the robustness invariance check, but it never substitutes for human
    judgment on a row the strict grammar rejected — a block that failed
    format is exhibiting the cost of bundling (or the format-noncompliance
    endpoint's other subject) that this design measures rather than papers
    over with an automatic override.
  * parser status PARSED    -> the mechanical rule decides directly
    (`family_hit` for target questions; FLAG + allowed-family key match for
    off-family questions).

**Record contract (confirmed against the trial runner's own record builders
— repair-set review finding 1; the runner itself is not published).** The
runner builds TWO DIFFERENT top-level record shapes that
`is_instrument_failure`/`trial_text` must both handle correctly. The public
dispatch tables (`data/dispatches/`) keep exactly the completion fields this
contract reads, and `tests/test_scorer.py` pins it against them:

* **Single-dispatch records (arms P, S; `build_single_record`):** a clean
  record carries `rc` (the PROCESS return code), `is_error`, `subtype`,
  `stop_reason`, and `result` all at TOP LEVEL (from the envelope, folded
  in by `_envelope_fields`) — `is_instrument_failure`'s original checks are
  correct for this shape.
* **Sq SESSION records (arm Sq; `build_sq_record`):** the per-turn
  completion fields live ONLY inside `record["turns"][k]` (each carrying
  its OWN `rc`/`is_error`/`subtype`/`stop_reason`/`result`/`family`); the
  SESSION record's top level carries `is_error: False` on a fully clean
  session and NOTHING else from that list (no top-level `rc`/`subtype`/
  `stop_reason` ever — a failed session sets `failure` instead and skips
  `is_error` entirely). The BUG this fixes, confirmed empirically before
  the fix: checking top-level `rc`/`subtype`/`stop_reason` against an Sq
  record read every clean Sq session as 100% instrument failure (those
  fields are simply always absent on that shape), which would have driven
  `unreliability()` to 1.0 for every Sq cell and fired C-B-UNREL on healthy
  data — subject data converted into an instrument verdict, the exact
  inversion of "instrument failure is never a subject verdict." The fix:
  `"turns" in record` is the reliable, always-present discriminant
  `build_sq_record` guarantees (set unconditionally before its own failure
  check), so `is_instrument_failure` branches on record SHAPE rather than
  assuming one universal field set. `trial_text` refuses on an Sq record
  (it has no single top-level answer text to return) and points the caller
  at `sq_turn_text` instead, which extracts §9's registered Sq scored text
  — the OWN TURN's `result`, matched by the turn's `family` field, never a
  session-transcript concatenation.

**Build-time notes (open when this module was written; how they settled is
stated at the end of each):**

3. **Key-table schema for HIT-ALT (§5.3):** the audit lane's key table
   (not yet built — a materials lane, not analysis code) is registered to
   mark "named additional families TRUE-ALLOWED" but never states whether
   an allowed family gets its OWN key list or shares the item's one
   `defect_keys` list. `allowed_family_keys` defaults to the item's own
   `defect_keys` for every allowed family (the plain reading: one
   underlying defect, legitimately describable under >1 family label,
   so the SAME textual keys should match under either family's question)
   but accepts an explicit per-family override if the freeze commit's key
   table turns out to carry one. Settled: the frozen key table carries no
   per-family key lists, so the default applies everywhere.
4. **Class 3's denominator ("key-matched-but-wrong-family rate", §11.4)**
   is not registered explicitly. This module reports it as a SUBSET count
   over the SAME denominator as class 2 (the off-family FA denominator,
   `4 - |allowed|`) so class 3 <= class 2 by construction and the two
   rates are directly comparable — a choice, not a registered rule;
   kept at freeze and disclosed.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Mapping, Sequence

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from answer_parser import FAMILIES, parse_response  # noqa: E402
from stats import bootstrap_delta  # noqa: E402

# --------------------------------------------------------------- thresholds
FORMAT_DEGRADED_THRESHOLD = 0.25   # §8/§10/§12: >25% noncompliance in a cell
UNRELIABILITY_THRESHOLD = 0.10     # §10: >10% instrument-failure attempts -> C-B-UNREL
FA_BOUND_ABS = 0.15                # §11.4 adoption bound: FA_hi - FA_lo <= 0.15
CLEANFAIL_MIN_SURVIVORS = 4        # §11.4/§12 N-f: <4 surviving cleans -> UNDECIDABLE

Z_95 = 1.959963984540054           # two-sided 95% normal quantile (Wilson)

PctPair = tuple[int, int]          # (successes, n) for one item/cell


# ---------------------------------------------------------- instrument side
def is_instrument_failure(record: Mapping) -> bool:
    """TERMINAL-record test, graduated from the parent's `is_error_trial` +
    §16's two independent signals. Fail-safe throughout: a record missing a
    field reads as failed, never as clean (a record that cannot POSITIVELY
    evidence completion cannot be scored as a subject response).

    SHAPE-AWARE (finding 1 fix — see the module docstring's "Record
    contract" section): the runner's `build_sq_record` SESSION shape (arm
    Sq) carries `is_error` at top level on a clean session and NOTHING else
    from the completion-field set (no top-level `rc`/`subtype`/
    `stop_reason` — those live per-turn); `build_single_record`'s
    single-dispatch shape (arms P/S) carries the full set at top level.
    `"turns" in record` is `build_sq_record`'s own unconditional marker
    (set before its failure check, so it survives on both a clean AND a
    failed Sq record) — the reliable discriminant between the two shapes."""
    if record.get("failure"):
        return True
    if record.get("api_error_status") is not None:
        return True
    if record.get("terminal_reason") == "api_error":
        return True
    if "turns" in record:
        # Sq SESSION shape: the ONLY completion evidence at this level.
        return record.get("is_error") is not False
    if record.get("rc") != 0:
        return True
    if record.get("is_error") is not False:
        return True
    if record.get("subtype") != "success":
        return True
    if record.get("stop_reason") != "end_turn":
        return True
    return False


def trial_text(record: Mapping) -> str:
    """The subject's response text for a NON-instrument-failure
    SINGLE-DISPATCH record (arms P/S). Raises on a failed record —
    refusing here (rather than returning "") is what stops a terminal
    record from being silently scored as a parse miss on a real response
    (the parent's `trial_result` rationale, graduated unchanged).
    Also raises on an Sq SESSION record: that shape has no single
    top-level answer text (§9 scores the TURN's own text) — call
    `sq_turn_text(record, family)` instead."""
    if is_instrument_failure(record):
        raise ValueError(
            "instrument failure is TERMINAL and is never scored; it counts in the "
            f"unreliability denominator instead: {dict(record)!r}"
        )
    if "turns" in record:
        raise ValueError(
            "trial_text: an Sq SESSION record has no single top-level answer text "
            "(§9 scores the TURN's own text, never a session-transcript "
            f"concatenation) -- call sq_turn_text(record, family) instead: {dict(record)!r}"
        )
    return record.get("result") or ""


def sq_turn_text(record: Mapping, family: str) -> str:
    """§9's registered Sq extraction: "the block from that question's
    turn — turn text only, never the session transcript." Looks up the
    turn matching `family` (the runner's per-turn `family` field) inside a CLEAN Sq SESSION record and
    returns THAT TURN's own `result` text. Same TERMINAL discipline as
    `trial_text`: raises on a session that carries any instrument
    failure — a partially-completed session's later, never-dispatched
    turns cannot be scored, and an earlier turn's text is never
    substituted for a later one."""
    if is_instrument_failure(record):
        raise ValueError(
            "instrument failure is TERMINAL and is never scored; it counts in the "
            f"unreliability denominator instead: {dict(record)!r}"
        )
    for turn in record.get("turns", ()):
        if turn.get("family") == family:
            return turn.get("result") or ""
    raise ValueError(
        f"sq_turn_text: no turn for family {family!r} in this Sq record's turns"
    )


# ------------------------------------------------------------- key matching
def _keys_match(text: str | None, keys: Sequence[str]) -> bool:
    low = (text or "").lower()
    return any(k.lower() in low for k in keys)


def family_hit(entry: Mapping, defect_keys: Sequence[str]) -> bool:
    """§5.2 per-question hit: FLAG verdict AND >=1 `defect_keys` match
    against `raw_block` (case-insensitive substring, ANY-of-tuple).
    Graduated from the parent's `placement_hit` — see module docstring for
    the two deltas (already-parsed entry, narrower `raw_block` scope)."""
    if entry.get("verdict") != "FLAG":
        return False
    return _keys_match(entry.get("raw_block"), defect_keys)


def keyword_rederivation(text: str | None, defect_keys: Sequence[str]) -> dict:
    """§9's registered RECOUNT entry point: keyword-only re-derivation —
    curated-key containment against a raw text, no parser, no verdict
    logic. Exists so an independent recount (fresh code from
    rules text) has a named, stable surface to cross-check the mechanical
    chain's key-matching half against; it is NEVER a scoring path (§9:
    hit = FLAG verdict ∧ keys_matched — the verdict half is the parser's,
    and text-containment alone is not trusted beyond the curated lists)."""
    low = (text or "").lower()
    matched = [k for k in defect_keys if k.lower() in low]
    return {"any_match": bool(matched), "matched_keys": matched}


def clean_any_flag(entries: Mapping[str, Mapping]) -> bool:
    """§11.4 FA class 1: does ANY family among a clean item's parsed
    answers carry a FLAG verdict. `entries` is one `parse_response(...)`
    return (all requested families for one trial)."""
    return any(e.get("verdict") == "FLAG" for e in entries.values())


def flag_count(entries: Mapping[str, Mapping]) -> int:
    """§11.3/§4.2's registered descriptive: how many of the answered
    families FLAG in one response — the direct signature of within-
    dispatch allocation/satisficing behaviour the P-arm residual channel
    names (§4.2, §19). MISSING/MALFORMED entries never count (no verdict
    was recoverable)."""
    return sum(1 for e in entries.values() if e.get("verdict") == "FLAG")


def off_family_denominator(allowed_families: Sequence[str]) -> int:
    """§5.3/§11.4 D-7: each MULTI-FAMILY ALLOWANCE shrinks the off-family
    FA denominator by one (4 possible off-family slots per item, since K=5
    and one family is the target)."""
    n = len(set(allowed_families))
    if n > 4:
        raise ValueError(f"{n} allowed families exceeds the 4 possible off-family slots")
    return 4 - n


# --------------------------------------------------------- §8/§10 disposition
def _compose_target(entry: Mapping, defect_keys: Sequence[str]) -> dict:
    if entry["status"] == "MISSING":
        return {"status": "NON-CATCH", "hit": False}
    if entry["status"] == "MALFORMED":
        return {"status": "BORDERLINE", "hit": None}
    hit = family_hit(entry, defect_keys)
    return {"status": "CATCH" if hit else "NON-CATCH", "hit": hit}


def _compose_target_primary(
    strict_entry: Mapping, loose_entry: Mapping, defect_keys: Sequence[str],
) -> dict:
    """The PRIMARY (strict-governed) disposition, with the finding-3(b)
    design ruling folded in: strict finds no fenced attempt at all
    (`_compose_target`'s plain MISSING->NON-CATCH would apply), but loose
    — which ALSO scans unfenced text (`answer_parser`'s finding-3(b) scope
    widening) — recovers a well-formed answer. Text manifestly exists,
    just never fenced, so this routes to BORDERLINE exactly like a
    strict-MALFORMED block, never mechanical NON-CATCH: "strict-MISSING
    but loose-PARSED -> BORDERLINE lane, never mechanical NON-CATCH" is
    the ruling's own words. Every OTHER strict status (MALFORMED, PARSED,
    or MISSING-under-both-variants) composes exactly as before via
    `_compose_target` — this function changes nothing beyond that one
    named divergence."""
    if strict_entry["status"] == "MISSING" and loose_entry["status"] == "PARSED":
        return {"status": "BORDERLINE", "hit": None}
    return _compose_target(strict_entry, defect_keys)


def score_target_question(text: str | None, family: str, defect_keys: Sequence[str]) -> dict:
    """The primary per-question scoring row for a defective item's TARGET
    family (§5.2/§9/§11.1's catch/miss unit). Runs BOTH parser variants
    (robustness co-reads, never chained — see module docstring): `status`
    (CATCH/NON-CATCH/BORDERLINE) is the STRICT-primary composed disposition
    (`_compose_target_primary`, folding in the strict-MISSING/loose-PARSED
    BORDERLINE fallback); `co_read_loose_status` is what the SAME
    single-variant composition would say if loose were primary instead
    (`_compose_target`, unchanged), for the invariance check;
    `co_read_divergence` flags the two apart. `raw_block` is the STRICT
    block (§9's scored text for the mechanical scorer)."""
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; expected one of {FAMILIES}")
    strict = parse_response(text, [family], variant="strict")[family]
    loose = parse_response(text, [family], variant="loose")[family]
    primary = _compose_target_primary(strict, loose, defect_keys)
    loose_co_read = _compose_target(loose, defect_keys)
    return {
        "family": family, **primary,
        "raw_block": strict["raw_block"], "occurrences": strict["occurrences"],
        "parser_strict_status": strict["status"], "parser_loose_status": loose["status"],
        "co_read_loose_status": loose_co_read["status"],
        "co_read_divergence": primary["status"] != loose_co_read["status"],
    }


def _compose_off_family(
    entry: Mapping, family: str, *, item_defect_keys: Sequence[str],
    allowed_families: Sequence[str], allowed_family_keys: Mapping[str, Sequence[str]] | None,
) -> dict:
    if entry["status"] == "MISSING":
        return {"status": "SILENT"}          # deployment silence; not FA, not counted
    if entry["status"] == "MALFORMED":
        return {"status": "BORDERLINE"}
    if entry.get("verdict") != "FLAG":
        return {"status": "NO-FLAG"}
    keys_for_allowed = (allowed_family_keys or {}).get(family, item_defect_keys)
    if family in allowed_families and _keys_match(entry.get("raw_block"), keys_for_allowed):
        return {"status": "HIT-ALT"}
    wrong_family_match = _keys_match(entry.get("raw_block"), item_defect_keys)
    return {"status": "FA", "key_matched_wrong_family": wrong_family_match}


def _compose_off_family_primary(
    strict_entry: Mapping, loose_entry: Mapping, family: str, **kwargs,
) -> dict:
    """`_compose_target_primary`'s mirror for off-family questions — same
    finding-3(b) fallback (strict-MISSING + loose-PARSED -> BORDERLINE,
    never the mechanical SILENT a plain MISSING would otherwise compose)."""
    if strict_entry["status"] == "MISSING" and loose_entry["status"] == "PARSED":
        return {"status": "BORDERLINE"}
    return _compose_off_family(strict_entry, family, **kwargs)


def score_off_family_question(
    text: str | None, family: str, *, item_defect_keys: Sequence[str],
    allowed_families: Sequence[str] = (),
    allowed_family_keys: Mapping[str, Sequence[str]] | None = None,
) -> dict:
    """§5.3/§11.4's off-family disposition for a defective item's NON-
    target family question: SILENT (missing) / BORDERLINE (malformed) /
    NO-FLAG (parsed, NONE) / HIT-ALT (parsed FLAG, matches an ALLOWED
    family's keys — co-reported, never FA) / FA (parsed FLAG, not
    allowed-matched; `key_matched_wrong_family` flags §11.4 class 3's
    subset — see build-time notes 3/4 on the key-table schema and the
    class-3 denominator). Same strict/loose co-read shape as `score_target_question`."""
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; expected one of {FAMILIES}")
    strict = parse_response(text, [family], variant="strict")[family]
    loose = parse_response(text, [family], variant="loose")[family]
    kwargs = dict(item_defect_keys=item_defect_keys, allowed_families=allowed_families,
                  allowed_family_keys=allowed_family_keys)
    primary = _compose_off_family_primary(strict, loose, family, **kwargs)
    loose_co_read = _compose_off_family(loose, family, **kwargs)
    return {
        "family": family, **primary,
        "raw_block": strict["raw_block"], "occurrences": strict["occurrences"],
        "parser_strict_status": strict["status"], "parser_loose_status": loose["status"],
        "co_read_loose_status": loose_co_read["status"],
        "co_read_divergence": primary["status"] != loose_co_read["status"],
    }


# ---------------------------------------------------------------- CI / rates
def wilson_ci(k: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson 95% score interval. Graduated UNCHANGED from
    the parent's `wilson_ci`."""
    if n <= 0:
        raise ValueError("Wilson CI on zero trials is undefined; an empty cell is "
                         "UNMEASURABLE, not a point at 0")
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def format_noncompliance(rows: Sequence[Mapping]) -> dict:
    """§8/§10/§11.3's format-noncompliance endpoint, one arm x tier cell:
    (strict MISSING + strict MALFORMED) / total SCOREABLE question-rows.
    Instrument-failure rows are excluded here (a different limb, different
    cause-owner — `unreliability` below); `rows` are already-composed rows
    (from `score_target_question`/`score_off_family_question`) carrying
    `parser_strict_status`, each optionally flagged `is_instrument_failure`
    by the caller. >25% -> FORMAT-DEGRADED (readings survive stamped,
    never voided — §12)."""
    scoreable = [r for r in rows if not r.get("is_instrument_failure")]
    if not scoreable:
        raise SystemExit("format_noncompliance: zero scoreable rows in this cell; refusing "
                         "an empty-denominator rate")
    noncompliant = sum(1 for r in scoreable if r["parser_strict_status"] in ("MISSING", "MALFORMED"))
    rate = noncompliant / len(scoreable)
    return {"rate": rate, "noncompliant": noncompliant, "total": len(scoreable),
            "format_degraded": rate > FORMAT_DEGRADED_THRESHOLD}


def unreliability(attempts: Sequence[Mapping]) -> dict:
    """§10's OTHER limb — different cause-owner, different denominator
    from `format_noncompliance`: instrument-failure ATTEMPT records /
    TOTAL attempt records (final rows + retained instrument-failure
    attempts, one arm x tier cell, §16) > 10% -> C-B-UNREL (blocks every
    cell that consumes it; never imputed)."""
    total = len(attempts)
    if total == 0:
        raise SystemExit("unreliability: zero attempt records in this cell; refusing")
    failed = sum(1 for a in attempts if is_instrument_failure(a))
    rate = failed / total
    return {"rate": rate, "failed": failed, "total": total,
            "unreliable": rate > UNRELIABILITY_THRESHOLD}


def fa_bound_check(hi_pairs: Sequence[PctPair], lo_pairs: Sequence[PctPair],
                    *, bound: float = FA_BOUND_ABS) -> dict:
    """§11.4's adoption bound: FA_hi - FA_lo <= 0.15 absolute (ratio clause
    FA_hi <= 2*FA_lo only when FA_lo > 0 — zero-cell rule). Three-state
    read (never a routing cell, §12's "FA states are QUALIFIER STAMPS"):
    IN-BOUND / OUT-OF-BOUND / UNRESOLVED (the bootstrap CI spans the bound
    -> FA-UNRESOLVED). Mirrors an earlier study's `fa_side` bound logic,
    generalized off that file's fixed A/C arm names and re-expressed over
    `stats.bootstrap_delta`.

    Finding 5 fix: the bound is violated by EITHER clause (absolute OR
    ratio) — `bound_violated` composes both, so a class that satisfies the
    absolute bound but breaches the ratio clause (e.g. fa_hi=0.25,
    fa_lo=0.11: diff=0.14<=0.15 but 0.25 > 2*0.11) correctly stamps
    OUT-OF-BOUND rather than falling through to UNRESOLVED (the previous
    three-branch logic only ever routed to OUT-OF-BOUND via `not in_abs`,
    so a pure ratio-clause breach with `in_abs` True had no branch that
    would fire it — a registered-taxonomy mis-stamp, FACON's paired-triage
    adoption misread as FAUNRES's adoption-blocked, in the conservative
    direction but still the wrong reason). `ci_spans_bound` (the bootstrap
    CI on the absolute diff, against `bound`) is the ONE resolution signal
    available — no separate CI is computed for the ratio clause — so it
    gates BOTH clauses identically: CI spans the bound -> UNRESOLVED
    regardless of which clause is violated; CI does not span it -> the
    point estimate's `bound_violated` composite decides IN-BOUND vs
    OUT-OF-BOUND directly."""
    n_hi, n_lo = sum(n for _, n in hi_pairs), sum(n for _, n in lo_pairs)
    if n_hi == 0 or n_lo == 0:
        raise SystemExit("fa_bound_check: an empty arm; refusing (UNDECIDABLE, not a bound read)")
    fa_hi = sum(c for c, _ in hi_pairs) / n_hi
    fa_lo = sum(c for c, _ in lo_pairs) / n_lo
    boot = bootstrap_delta(hi_pairs, lo_pairs)
    diff = fa_hi - fa_lo
    in_abs = diff <= bound
    ratio_ok = (fa_hi <= 2 * fa_lo) if fa_lo > 0 else None
    ci_spans_bound = boot["ci95"][0] <= bound <= boot["ci95"][1]
    bound_violated = (not in_abs) or (ratio_ok is False)
    if ci_spans_bound:
        state = "UNRESOLVED"
    else:
        state = "OUT-OF-BOUND" if bound_violated else "IN-BOUND"
    return {"state": state, "fa_hi": fa_hi, "fa_lo": fa_lo, "diff": diff,
            "bound": bound, "ratio_clause": ratio_ok, **boot}


def apply_j4_exclusion(clean_item_ids: Sequence[str], falsified_items: Sequence[str]) -> dict:
    """§10's J.4 rule, carried verbatim: a keying-checker-verified real
    finding on a clean item is never an FA; the item leaves EVERY FA cell.
    `survivors` recomputes the denominator; `low_power` (<4 survivors) is
    the §12 N-f CLEANFAIL stamp modifier (that class's FA read becomes
    UNDECIDABLE/FAUNRES-form)."""
    falsified = set(falsified_items)
    survivors = [i for i in clean_item_ids if i not in falsified]
    return {
        "survivors": survivors,
        "falsified_count": len(falsified & set(clean_item_ids)),
        "low_power": len(survivors) < CLEANFAIL_MIN_SURVIVORS,
    }


def main() -> int:  # pragma: no cover - manual smoke entry, no CLI surface registered
    print("scorer: analysis-helper module, no CLI. Import score_target_question / "
          "score_off_family_question / format_noncompliance / unreliability / "
          "fa_bound_check.", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
