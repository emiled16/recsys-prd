from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from recsys_prd.config import get_app_settings  # noqa: E402
from recsys_prd.services.redpanda import bootstrap_redpanda_topics  # noqa: E402


if __name__ == "__main__":
    print(bootstrap_redpanda_topics(get_app_settings()))
