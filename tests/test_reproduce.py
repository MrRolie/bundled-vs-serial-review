"""End-to-end: the public chain reproduces every artifact of record
(skipping only the two 1e6-draw blocks, which `python analysis/reproduce.py`
runs in full in about half a minute)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reproduce_chain_matches_artifacts_of_record(tmp_path):
    r = subprocess.run([sys.executable, "-B", str(ROOT / "analysis/reproduce.py"),
                        "--out", str(tmp_path), "--skip-large"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "every product reproduces its artifact of record" in r.stdout
