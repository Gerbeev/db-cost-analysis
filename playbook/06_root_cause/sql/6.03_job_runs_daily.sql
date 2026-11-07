-- Step 6 · PB-JOBS J3 · Daily run starts and run-hours per job (onset of extra runs).
-- Params : :start_date, :end_date   (end exclusive; e.g. 30 days before B through end of C)
-- Read   : first day of persistent increase in started_runs or total_run_hours vs the
--          total cost onset (+/- 2 days).

WITH runs AS (
  SELECT
    workspace_id, job_id, run_id,
    MAX_BY(run_type, period_end_time)   AS run_type,
    MIN(period_start_time)              AS started_at,
    MAX(period_end_time)                AS ended_at
  FROM system.lakeflow.job_run_timeline
  WHERE period_start_time >= CAST(:start_date AS TIMESTAMP)
    AND period_start_time <  CAST(:end_date   AS TIMESTAMP)
  GROUP BY workspace_id, job_id, run_id
)
SELECT
  DATE(started_at)                                                   AS run_date,
  workspace_id,
  job_id,
  run_type,
  COUNT(*)                                                           AS started_runs,
  ROUND(SUM(TIMESTAMPDIFF(SECOND, started_at, ended_at)) / 3600.0, 2) AS total_run_hours
FROM runs
GROUP BY ALL
ORDER BY workspace_id, job_id, run_date;
