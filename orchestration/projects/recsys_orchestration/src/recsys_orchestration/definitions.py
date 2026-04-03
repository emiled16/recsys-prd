from __future__ import annotations

import dagster as dg

from recsys_orchestration.defs.assets import ASSETS
from recsys_orchestration.defs.jobs import JOBS
from recsys_orchestration.defs.schedules import SCHEDULES


defs = dg.Definitions(
    assets=ASSETS,
    jobs=JOBS,
    schedules=SCHEDULES,
)
