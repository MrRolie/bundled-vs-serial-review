"""The exact prompts are reconstructible: every dispatch's payload, rebuilt from
the frozen public materials, matches its recorded SHA-256 (and the check fails
when the materials are perturbed)."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

import payloads  # noqa: E402


def test_every_recorded_payload_hash_reproduces():
    r = payloads.check(ROOT)
    assert r["records"] == 3675  # 3,660 trial records + 15 grouped-order probes
    assert r["payloads"] == 5163  # 5,148 model invocations + 15 probes
    assert r["records_matching"] == r["records"], r["mismatches"]
    assert r["keyed_orders"] == 920 and r["keyed_orders_matching"] == 920


def _copy_public(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "materials", root / "materials")
    shutil.copytree(ROOT / "data/dispatches", root / "data/dispatches")
    return root


def test_check_fails_on_a_perturbed_briefing(tmp_path):
    root = _copy_public(tmp_path)
    b = root / "materials/overlay/briefing.md"
    b.write_text(b.read_text().replace("five defect families", "five  defect families"))
    r = payloads.check(root)
    assert r["records_matching"] == 0
    assert any("payload_sha256s" in m for m in r["mismatches"])


def test_check_fails_on_a_perturbed_question(tmp_path):
    root = _copy_public(tmp_path)
    q = root / "materials/overlay/questions.json"
    d = json.loads(q.read_text())
    d["units"] = d["units"] + " "
    q.write_text(json.dumps(d))
    r = payloads.check(root)
    assert 0 < r["records_matching"] < r["records"]
    assert any("charge_sha256s.units" in m for m in r["mismatches"])


def test_render_matches_recorded_sq_turn_hash():
    out = payloads.render(ROOT, "claude-haiku-4-5-20251001", "clean-sf-01", "Sq", 2, None)
    rec = next(json.loads(ln) for ln in
               (ROOT / "data/dispatches/claude-haiku-4-5-20251001.jsonl").read_text().splitlines()
               if '"clean-sf-01"' in ln and '"arm": "Sq"' in ln and '"rep": 2' in ln)
    assert [h for h, _ in out] == rec["payload_sha256s"]
    assert out[1][1].startswith("You are asked about family ")
