-- Step 6 · PB-SQL S3 / PB-JOBS J6 · Monthly statement volume, duration, bytes and spill
--          per warehouse / compute type / client.
-- Params : :start_date, :end_date   (end exclusive)
-- Read   : statements up = demand growth (H-SQL-03/07); p95 / read_bytes / spill up with flat
--          statements = regression (H-SQL-04).
-- Limits : regional table; query duration is not billed cost; cached results distort counts.

SELECT
  DATE_FORMAT(start_time, 'yyyy-MM')                                       AS month,
  workspace_id,
  compute.type                                                             AS compute_type,
  compute.warehouse_id                                                     AS warehouse_id,
  client_application,
  COUNT(DISTINCT statement_id)                                             AS statements,
  COUNT_IF(execution_status = 'FAILED')                                    AS failed_statements,
  ROUND(AVG(total_duration_ms) / 1000.0, 2)                                AS avg_duration_s,
  ROUND(PERCENTILE_APPROX(total_duration_ms, 0.95) / 1000.0, 2)            AS p95_duration_s,
  ROUND(SUM(total_duration_ms) / 3600000.0, 2)                             AS summed_statement_hours,
  ROUND(SUM(read_bytes) / POW(1024, 4), 4)                                 AS read_tib,
  ROUND(SUM(spilled_local_bytes) / POW(1024, 3), 2)                        AS spilled_gib
FROM system.query.history
WHERE start_time >= CAST(:start_date AS TIMESTAMP)
  AND start_time <  CAST(:end_date   AS TIMESTAMP)
GROUP BY ALL
ORDER BY month, statements DESC;
