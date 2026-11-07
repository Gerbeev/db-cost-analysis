-- Step 6 · PB-JOBS J4 · Job definitions (SCD2): first seen, versions, changes in window.
-- Params : :start_date, :end_date   (end exclusive)
-- Read   : change_times_in_window close to a driver onset -> change event candidate;
--          first_recorded_change inside window -> job created (bounded by retention).
-- Limits : job_id is unique per workspace only. SCD2 shows that a definition changed,
--          not which field - open the job / bundle history for the diff.

WITH versions AS (
  SELECT
    workspace_id, job_id, name, change_time, delete_time,
    ROW_NUMBER() OVER (PARTITION BY workspace_id, job_id ORDER BY change_time DESC) AS rn
  FROM system.lakeflow.jobs
  WHERE change_time < CAST(:end_date AS TIMESTAMP)
)
SELECT
  workspace_id,
  job_id,
  MAX(CASE WHEN rn = 1 THEN name END)                                       AS latest_name,
  MAX(CASE WHEN rn = 1 THEN delete_time END)                                AS deleted_at,
  MIN(change_time)                                                          AS first_recorded_change,
  MIN(change_time) >= CAST(:start_date AS TIMESTAMP)                        AS created_in_window,
  COUNT(*)                                                                  AS recorded_versions,
  COUNT_IF(change_time >= CAST(:start_date AS TIMESTAMP))                   AS changes_in_window,
  ARRAY_SORT(COLLECT_LIST(change_time)
             FILTER (WHERE change_time >= CAST(:start_date AS TIMESTAMP)))  AS change_times_in_window,
  COUNT(DISTINCT name)                                                      AS distinct_names
FROM versions
GROUP BY workspace_id, job_id
ORDER BY changes_in_window DESC, first_recorded_change DESC;
