-- Step 6 · PB-JOBS J2 · Monthly run count, duration (avg / p95 / max) and outcomes per job.
-- Params : :start_date, :end_date   (end exclusive)
-- Operational evidence only - not cost. Hourly slices are collapsed per run.
-- Regional table: query each region that hosts in-scope workspaces.

WITH runs AS (
  SELECT
    workspace_id, job_id, run_id,
    MAX_BY(run_type, period_end_time)         AS run_type,
    MIN(period_start_time)                    AS started_at,
    MAX(period_end_time)                      AS ended_at,
    MAX_BY(result_state, period_end_time)     AS final_result,
    MAX_BY(trigger_type, period_end_time)     AS trigger_type
  FROM system.lakeflow.job_run_timeline
  WHERE period_start_time >= CAST(:start_date AS TIMESTAMP)
    AND period_start_time <  CAST(:end_date   AS TIMESTAMP)
  GROUP BY workspace_id, job_id, run_id
)
SELECT
  DATE_FORMAT(started_at, 'yyyy-MM')                                       AS month,
  workspace_id,
  job_id,
  run_type,
  ARRAY_JOIN(COLLECT_SET(trigger_type), ',')                               AS trigger_types,
  COUNT(*)                                                                 AS runs,
  ROUND(AVG(TIMESTAMPDIFF(SECOND, started_at, ended_at)) / 60.0, 2)        AS avg_duration_min,
  ROUND(PERCENTILE_APPROX(TIMESTAMPDIFF(SECOND, started_at, ended_at), 0.95) / 60.0, 2) AS p95_duration_min,
  ROUND(MAX(TIMESTAMPDIFF(SECOND, started_at, ended_at)) / 60.0, 2)        AS max_duration_min,
  ROUND(SUM(TIMESTAMPDIFF(SECOND, started_at, ended_at)) / 3600.0, 2)      AS total_run_hours,
  COUNT_IF(final_result = 'SUCCEEDED')                                     AS succeeded,
  COUNT_IF(final_result IN ('FAILED', 'ERROR'))                            AS failed,
  COUNT_IF(final_result = 'TIMED_OUT')                                     AS timed_out,
  COUNT_IF(final_result = 'CANCELLED')                                     AS cancelled
FROM runs
GROUP BY ALL
ORDER BY workspace_id, job_id, month;
