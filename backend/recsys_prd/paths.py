from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_ROOT = PROJECT_ROOT / "data"
RAW_HM_ROOT = DATA_ROOT / "raw" / "hm"
NORMALIZED_ROOT = DATA_ROOT / "normalized"
REPORTS_ROOT = DATA_ROOT / "reports"
