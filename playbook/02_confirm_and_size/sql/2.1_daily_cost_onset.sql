-- Step 2.2 · Daily Databricks modeled cost with onset detection (rule R5).
-- Params : :start_date, :end_date   analysis window (end exclusive)
--          :base_start, :base_end   baseline period inside the window (end exclusive)
-- Output : one row per day and currency.
--          excursion_type = STEP (>= 14 consecutive days above threshold) | SPIKE (< 14)
--          onset_flag     = ONSET on the first day of each STEP after the baseline.
-- Limits : list-price model (R1) - confirm the same onset on Azure Actual daily data
--          (tools/onset_detect.py). Unpriced usage is excluded; run 1.3 first.
--          A run still open at the window end with < 14 days is labelled SPIKE.

WITH daily AS (
  SELECT
    u.usage_date                                              AS d,
    p.currency_code,
    SUM(u.usage_quantity * p.pricing.effective_list.default)  AS cost
  FROM system.billing.usage u
  JOIN system.billing.list_prices p
    ON  p.account_id = u.account_id
    AND p.cloud      = u.cloud
    AND p.sku_name   = u.sku_name
    AND p.usage_unit = u.usage_unit
    AND u.usage_start_time >= p.price_start_time
    AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
  WHERE u.cloud = 'AZURE'
    AND u.usage_date >= CAST(:start_date AS DATE)
    AND u.usage_date <  CAST(:end_date   AS DATE)
  GROUP BY u.usage_date, p.currency_code
),
baseline AS (
  SELECT currency_code,
         AVG(cost)         AS mu,
         STDDEV_SAMP(cost) AS sigma
  FROM daily
  WHERE d >= CAST(:base_start AS DATE) AND d < CAST(:base_end AS DATE)
  GROUP BY currency_code
),
flagged AS (
  SELECT
    x.d, x.currency_code, x.cost, b.mu, b.sigma,
    AVG(x.cost) OVER (PARTITION BY x.currency_code ORDER BY x.d
                      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)        AS ma7,
    b.mu + GREATEST(2 * COALESCE(b.sigma, 0), 0.10 * b.mu)            AS threshold
  FROM daily x
  JOIN baseline b USING (currency_code)
),
islands AS (
  SELECT *,
         CASE WHEN ma7 > threshold THEN 1 ELSE 0 END                   AS above,
         SUM(CASE WHEN ma7 > threshold THEN 0 ELSE 1 END)
           OVER (PARTITION BY currency_code ORDER BY d)                AS grp
  FROM flagged
),
runs AS (
  SELECT *,
         SUM(above) OVER (PARTITION BY currency_code, grp)             AS run_days,
         MIN(CASE WHEN above = 1 THEN d END)
           OVER (PARTITION BY currency_code, grp)                      AS run_start
  FROM islands
)
SELECT
  d                                   AS usage_date,
  currency_code,
  ROUND(cost, 2)                      AS daily_list_cost,
  ROUND(ma7, 2)                       AS ma7,
  ROUND(mu, 2)                        AS baseline_mean,
  ROUND(sigma, 2)                     AS baseline_stddev,
  ROUND(threshold, 2)                 AS threshold,
  above                               AS above_threshold,
  CASE WHEN above = 1 AND run_days >= 14 THEN 'STEP'
       WHEN above = 1                    THEN 'SPIKE' END             AS excursion_type,
  CASE WHEN above = 1 AND run_days >= 14 AND d = run_start
            AND d >= CAST(:base_end AS DATE) THEN 'ONSET' END         AS onset_flag,
  CASE WHEN above = 1 THEN run_days END                               AS run_length_days
FROM runs
ORDER BY currency_code, usage_date;
