from __future__ import annotations

from recsys_prd.config import get_app_settings
from recsys_prd.services.redpanda import bootstrap_redpanda_topics

if __name__ == "__main__":
    print(bootstrap_redpanda_topics(get_app_settings()))
