-- Step 6 · PB-SQL S2 · SQL warehouse lifecycle: starts, scaling and observed running
--          cluster-hours (proxy for uptime).
-- Params : :start_date, :end_date   (end exclusive)
-- Method : each RUNNING / SCALED_UP / SCALED_DOWN event opens an interval until the next event;
--          interval hours x cluster_count = observed cluster-hours, attributed to the interval
--          start date. The last pre-window event provides the entry state.
-- Limits : proxy, not billed hours. Missing pre-window events -> entry state unknown.
--          Compare B vs C trend, not absolute values, against 5.3 warehouse cost.

WITH events AS (
  SELECT workspace_id, warehouse_id, event_type, cluster_count, event_time
  FROM system.compute.warehouse_events
  WHERE event_time < CAST(:end_date AS TIMESTAMP)
  QUALIFY event_time >= CAST(:start_date AS TIMESTAMP)
       OR ROW_NUMBER() OVER (PARTITION BY workspace_id, warehouse_id
                             ORDER BY CASE WHEN event_time < CAST(:start_date AS TIMESTAMP) THEN 0 ELSE 1 END,
                                      event_time DESC) = 1
),
intervals AS (
  SELECT *,
         LEAD(event_time) OVER (PARTITION BY workspace_id, warehouse_id ORDER BY event_time) AS next_time
  FROM events
)
SELECT
  DATE(GREATEST(event_time, CAST(:start_date AS TIMESTAMP)))                 AS day,
  workspace_id,
  warehouse_id,
  COUNT_IF(event_type = 'STARTING')                                          AS starts,
  COUNT_IF(event_type = 'SCALED_UP')                                         AS scale_ups,
  MAX(cluster_count)                                                         AS max_cluster_count,
  ROUND(SUM(CASE WHEN event_type IN ('RUNNING', 'SCALED_UP', 'SCALED_DOWN')
                  AND next_time IS NOT NULL
                 THEN TIMESTAMPDIFF(SECOND,
                        GREATEST(event_time, CAST(:start_date AS TIMESTAMP)),
                        LEAST(next_time, CAST(:end_date AS TIMESTAMP)))
                      * COALESCE(cluster_count, 1)
                 ELSE 0 END) / 3600.0, 2)                                    AS observed_cluster_hours,
  COUNT_IF(event_type IN ('RUNNING', 'SCALED_UP', 'SCALED_DOWN') AND next_time IS NULL)
                                                                             AS open_intervals
FROM intervals
GROUP BY ALL
ORDER BY workspace_id, warehouse_id, day;
