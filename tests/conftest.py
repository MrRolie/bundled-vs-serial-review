import sys
from pathlib import Path

_ANALYSIS = Path(__file__).resolve().parents[1] / "analysis"
if str(_ANALYSIS) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS))
