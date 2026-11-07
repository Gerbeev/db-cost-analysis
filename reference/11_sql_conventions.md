# 11 · SQL conventions

<!-- plain -->
> **Overview.** How the SQL files are written and how to read their output. Every query only **reads** data. Running one uses a little SQL warehouse compute, so tell the Databricks owner before you run them in bulk.
<!-- /plain -->

All SQL is read-only `SELECT` for Databricks SQL Editor over Unity Catalog `system` schemas. Running it consumes SQL warehouse compute (R12).

## Where files live

The number before the dot is the step: `5.3_object_delta.sql` → `playbook/05_databricks_decomposition/sql/`, `6.01_job_cost_per_run.sql` → `playbook/06_root_cause/sql/`.

| Step folder | Files |
|---|---|
| `01_data_quality/sql/` | 1.1 usage coverage · 1.2 units inventory · 1.3 price-join check |
| `02_confirm_and_size/sql/` | 2.1 daily cost onset · 2.2 monthly cost by SKU (input for the analyzer, action 2.9) |
| `03_accounting_effects/sql/` | 3.1 list price history |
| `05_databricks_decomposition/sql/` | 5.1 SKU volume/rate · 5.2 workspace delta · 5.3 object delta · 5.4 object daily · 5.5 attribution coverage · 5.6 first-seen SKUs |
| `06_root_cause/sql/` | 6.01 job cost per run · 6.02 job runs monthly · 6.03 job runs daily · 6.04 job definition changes · 6.05 pipeline updates · 6.06 cluster config history · 6.07 node utilization · 6.08 pool idle · 6.09 warehouse config history · 6.10 warehouse events · 6.11 query trends · 6.12 query clients · 6.13 serverless and features · 6.14 audit change events · 6.15 DBU per node-hour (classic) |

## Parameters

Named parameter markers; the SQL Editor shows a widget per marker. Dates as text `YYYY-MM-DD`. **All `_end` values are exclusive** (first day after the period).

| Parameter | Meaning | Example |
|---|---|---|
| `:start_date` / `:end_date` | Analysis window | `2026-01-01` / `2026-11-01` |
| `:base_start` / `:base_end` | Baseline B | `2026-01-01` / `2026-03-01` |
| `:cmp_start` / `:cmp_end` | Comparison C | `2026-04-01` / `2026-05-01` |
| `:object_ids` | Comma list of object IDs from 5.3, or `ALL` | `123456789,0412-abc123-xyz` |
| `:cluster_sources` | `ALL` or comma list (`UI,API` / `JOB`) | `UI,API` |
| `:required_tag` | Tag key that must exist | `cost_center` |

Billing queries filter `cloud = 'AZURE'`.

## Price join (every cost query)

```sql
LEFT JOIN system.billing.list_prices p
  ON  p.account_id = u.account_id AND p.cloud = u.cloud
  AND p.sku_name = u.sku_name     AND p.usage_unit = u.usage_unit
  AND u.usage_start_time >= p.price_start_time
  AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
```
Validate with `1.3_price_join_check.sql` first (R7). Modeled cost = `usage_quantity × pricing.effective_list.default` (list price, not invoice).

## Saving results

In the interface every SQL action pre-fills these parameters from the audit, can run the query directly (Settings → Databricks SQL connection; read-only Statement Execution API) and saves the CSV under the correct name with an evidence row. Without a connection: copy the query, run it in the SQL editor and upload the CSV in the same action.


- Export the full result (no UI row limit) as CSV into `audits/<id>/<step>/results/`.
- File name: `<sql-id>__<details>__<YYYYMMDD>.csv`, e.g. `5.3_object_delta__B2026-02_C2026-04__20261109.csv`.
- Add an evidence row: file, parameters, run timestamp, observation.

## Conventions inside the SQL

- Corrections: all `record_type` values kept and netted.
- Units: quantities summed only within one `usage_unit`.
- Regional tables (`lakeflow`, `compute`, `query`, `access`): run in each region with in-scope workspaces.
- If a column is not found (schema evolution, preview features), remove that column and note it in the evidence row.
