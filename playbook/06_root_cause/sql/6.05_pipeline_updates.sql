-- Step 6 · PB-PIPELINES L1 · Pipeline updates per month: count, duration, trigger,
--          outcomes (COMPLETED / FAILED / CANCELED), full-refresh selections.
-- Params : :start_date, :end_date   (end exclusive)
-- Notes  : updates can be split into hourly slices -> collapsed by update_id.
--          Updates crossing the window edges have partially observed durations.
--          Continuous pipelines show very long observed durations.

WITH updates AS (
  SELECT
    workspace_id, pipeline_id, update_id,
    MIN(period_start_time)                                                     AS observed_start,
    MAX(period_end_time)                                                       AS observed_end,
    MAX_BY(result_state, period_end_time) FILTER (WHERE result_state IS NOT NULL) AS final_result,
    MAX_BY(trigger_type, period_end_time) FILTER (WHERE trigger_type IS NOT NULL) AS last_trigger,
    MAX(CASE WHEN SIZE(full_refresh_selection) > 0 THEN 1 ELSE 0 END)          AS full_refresh
  FROM system.lakeflow.pipeline_update_timeline
  WHERE period_start_time < CAST(:end_date   AS TIMESTAMP)
    AND period_end_time   > CAST(:start_date AS TIMESTAMP)
  GROUP BY workspace_id, pipeline_id, update_id
)
SELECT
  DATE_FORMAT(observed_start, 'yyyy-MM')                                     AS month,
  workspace_id,
  pipeline_id,
  last_trigger,
  COUNT(*)                                                                   AS updates,
  ROUND(AVG(TIMESTAMPDIFF(SECOND, observed_start, observed_end)) / 60.0, 2)  AS avg_observed_duration_min,
  ROUND(SUM(TIMESTAMPDIFF(SECOND, observed_start, observed_end)) / 3600.0, 2) AS total_observed_hours,
  COUNT_IF(final_result = 'COMPLETED')                                       AS completed,
  COUNT_IF(final_result = 'FAILED')                                          AS failed,
  COUNT_IF(final_result = 'CANCELED')                                        AS canceled,
  COUNT_IF(final_result IS NULL)                                             AS no_terminal_result,
  SUM(full_refresh)                                                          AS updates_with_full_refresh
FROM updates
GROUP BY ALL
ORDER BY workspace_id, pipeline_id, month;
