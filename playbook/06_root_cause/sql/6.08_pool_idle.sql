-- Step 6 · PB-POOLS P1 · Observed idle (INSTANCE_READY) vs placed (INSTANCE_PLACED) hours
--          of pooled instances per month. system.compute.instance_events (Public Preview).
-- Params : :start_date, :end_date   (end exclusive; :start_date must be the 1st of a month)
-- Method : last event before the window reconstructs intervals crossing the start; first event
--          after the window closes the last interval; intervals are clipped to month boundaries.
-- Limits : completed intervals only -> lower bound; not an Azure VM charge. SQL warehouse
--          placements are not covered.

WITH pre_window AS (
  SELECT workspace_id, instance_pool_id, instance_id, node_type, state, event_time
  FROM system.compute.instance_events
  WHERE instance_pool_id IS NOT NULL
    AND event_time < CAST(:start_date AS TIMESTAMP)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY workspace_id, instance_pool_id, instance_id
                             ORDER BY event_time DESC) = 1
),
post_window AS (
  SELECT workspace_id, instance_pool_id, instance_id, node_type, state, event_time
  FROM system.compute.instance_events
  WHERE instance_pool_id IS NOT NULL
    AND event_time >= CAST(:end_date AS TIMESTAMP)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY workspace_id, instance_pool_id, instance_id
                             ORDER BY event_time ASC) = 1
),
window_events AS (
  SELECT workspace_id, instance_pool_id, instance_id, node_type, state, event_time
  FROM system.compute.instance_events
  WHERE instance_pool_id IS NOT NULL
    AND event_time >= CAST(:start_date AS TIMESTAMP)
    AND event_time <  CAST(:end_date   AS TIMESTAMP)
),
events AS (
  SELECT * FROM pre_window
  UNION ALL SELECT * FROM window_events
  UNION ALL SELECT * FROM post_window
),
intervals AS (
  SELECT workspace_id, instance_pool_id, instance_id, node_type, state,
         event_time AS started_at,
         LEAD(event_time) OVER (PARTITION BY workspace_id, instance_pool_id, instance_id
                                ORDER BY event_time) AS ended_at
  FROM events
),
months AS (
  SELECT EXPLODE(SEQUENCE(CAST(:start_date AS DATE),
                          ADD_MONTHS(CAST(:end_date AS DATE), -1),
                          INTERVAL 1 MONTH)) AS month_start
),
clipped AS (
  SELECT m.month_start, i.workspace_id, i.instance_pool_id, i.node_type, i.state,
         TIMESTAMPDIFF(SECOND,
           GREATEST(i.started_at, CAST(m.month_start AS TIMESTAMP)),
           LEAST(i.ended_at, CAST(ADD_MONTHS(m.month_start, 1) AS TIMESTAMP))) AS seconds
  FROM intervals i
  CROSS JOIN months m
  WHERE i.state IN ('INSTANCE_READY', 'INSTANCE_PLACED')
    AND i.ended_at IS NOT NULL
    AND i.ended_at > i.started_at
    AND i.started_at < CAST(ADD_MONTHS(m.month_start, 1) AS TIMESTAMP)
    AND i.ended_at   > CAST(m.month_start AS TIMESTAMP)
)
SELECT
  DATE_FORMAT(month_start, 'yyyy-MM')                                              AS month,
  workspace_id,
  instance_pool_id,
  node_type,
  ROUND(SUM(CASE WHEN state = 'INSTANCE_READY'  THEN seconds ELSE 0 END) / 3600.0, 2) AS observed_idle_hours,
  ROUND(SUM(CASE WHEN state = 'INSTANCE_PLACED' THEN seconds ELSE 0 END) / 3600.0, 2) AS observed_placed_hours,
  COUNT(*)                                                                         AS interval_segments
FROM clipped
GROUP BY ALL
ORDER BY month, observed_idle_hours DESC;
