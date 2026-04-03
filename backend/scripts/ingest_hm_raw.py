from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
for root in [str(PROJECT_ROOT), str(BACKEND_ROOT)]:
    if root not in sys.path:
        sys.path.insert(0, root)

from recsys_prd.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
