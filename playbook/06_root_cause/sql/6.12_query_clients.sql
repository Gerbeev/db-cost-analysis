-- Step 6 · PB-SQL S4 · Demand by client application and hour-of-day: BI polling / refresh
--          storms and overnight activity that keeps warehouses running (H-SQL-03).
-- Params : :start_date, :end_date   (end exclusive)
-- Read   : a client whose statements rise sharply, run at regular intervals, or appear
--          outside business hours. No user identities are returned.

SELECT
  DATE_FORMAT(start_time, 'yyyy-MM')                AS month,
  workspace_id,
  compute.warehouse_id                              AS warehouse_id,
  client_application,
  HOUR(start_time)                                  AS hour_of_day_utc,
  COUNT(DISTINCT statement_id)                      AS statements,
  COUNT(DISTINCT executed_by_user_id)               AS distinct_principals,
  ROUND(SUM(total_duration_ms) / 3600000.0, 3)      AS summed_statement_hours
FROM system.query.history
WHERE start_time >= CAST(:start_date AS TIMESTAMP)
  AND start_time <  CAST(:end_date   AS TIMESTAMP)
GROUP BY ALL
ORDER BY month, warehouse_id, client_application, hour_of_day_utc;
