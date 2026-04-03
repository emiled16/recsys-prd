from __future__ import annotations

import dagster as dg

from recsys_orchestration.defs.jobs import evaluation_job, replay_job, training_job


daily_training_schedule = dg.ScheduleDefinition(
    job=training_job,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Toronto",
)

weekly_evaluation_schedule = dg.ScheduleDefinition(
    job=evaluation_job,
    cron_schedule="0 8 * * 1",
    execution_timezone="America/Toronto",
)

hourly_replay_schedule = dg.ScheduleDefinition(
    job=replay_job,
    cron_schedule="0 * * * *",
    execution_timezone="America/Toronto",
)

SCHEDULES = [
    daily_training_schedule,
    weekly_evaluation_schedule,
    hourly_replay_schedule,
]
