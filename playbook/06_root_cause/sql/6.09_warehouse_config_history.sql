-- Step 6 · PB-SQL S1 · SQL warehouse configuration history (SCD2) with pre-window baseline
--          and fields changed per version.
-- Params : :start_date, :end_date   (end exclusive)
-- Read   : warehouse_size / max_clusters / auto_stop_minutes / warehouse_type changes near a
--          warehouse cost onset (H-SQL-01, H-SQL-02, H-SQL-06). A config change is a candidate
--          cause, not a cost - confirm with 5.3 / 5.4 and 6.10.

WITH marked AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY workspace_id, warehouse_id
                       ORDER BY CASE WHEN change_time < CAST(:start_date AS TIMESTAMP) THEN 0 ELSE 1 END,
                                change_time DESC) AS pre_rank
  FROM system.compute.warehouses
  WHERE change_time < CAST(:end_date AS TIMESTAMP)
),
history AS (
  SELECT
    CASE WHEN change_time < CAST(:start_date AS TIMESTAMP) THEN 'BASELINE_PRE_WINDOW'
         ELSE 'CHANGE_IN_WINDOW' END AS record_kind,
    *
  FROM marked
  WHERE change_time >= CAST(:start_date AS TIMESTAMP)
     OR (change_time < CAST(:start_date AS TIMESTAMP) AND pre_rank = 1)
),
diffed AS (
  SELECT *,
    CONCAT_WS(',',
      IF(LAG(warehouse_size)    OVER w <=> warehouse_size,    NULL, 'warehouse_size'),
      IF(LAG(warehouse_type)    OVER w <=> warehouse_type,    NULL, 'warehouse_type'),
      IF(LAG(warehouse_channel) OVER w <=> warehouse_channel, NULL, 'warehouse_channel'),
      IF(LAG(min_clusters)      OVER w <=> min_clusters,      NULL, 'min_clusters'),
      IF(LAG(max_clusters)      OVER w <=> max_clusters,      NULL, 'max_clusters'),
      IF(LAG(auto_stop_minutes) OVER w <=> auto_stop_minutes, NULL, 'auto_stop_minutes')
    )                                     AS changed_fields_raw,
    LAG(change_time) OVER w               AS previous_change_time
  FROM history
  WINDOW w AS (PARTITION BY workspace_id, warehouse_id ORDER BY change_time)
)
SELECT
  record_kind,
  workspace_id,
  warehouse_id,
  warehouse_name,
  change_time,
  delete_time,
  CASE WHEN delete_time IS NOT NULL THEN 'DELETED' ELSE 'CONFIGURED' END AS snapshot_state,
  CASE WHEN previous_change_time IS NULL THEN 'FIRST_VISIBLE_VERSION'
       ELSE NULLIF(changed_fields_raw, '') END                           AS changed_fields,
  warehouse_type,
  warehouse_channel,
  warehouse_size,
  min_clusters,
  max_clusters,
  auto_stop_minutes
FROM diffed
ORDER BY workspace_id, warehouse_id, change_time;
