# PB-SQL

<!-- plain -->
> **Overview.** Use when **SQL** costs more: a larger warehouse size, more clusters, a warehouse that no longer stops (auto-stop changed), or more or heavier queries from a dashboard or tool.
<!-- /plain -->

**Signals:** `SQL` product ↑ (classic, pro or serverless SQL SKUs); `5.3` `WAREHOUSE` objects ↑.

| # | Check | Source | Read |
|---|---|---|---|
| S1 | Warehouse config history | [`6.09_warehouse_config_history.sql`](../sql/6.09_warehouse_config_history.sql) | Size, type, min/max clusters, auto-stop changes |
| S2 | Lifecycle and scaling events | [`6.10_warehouse_events.sql`](../sql/6.10_warehouse_events.sql) | More starts, longer RUNNING, more SCALED_UP |
| S3 | Query volume, duration, bytes, spill | [`6.11_query_trends.sql`](../sql/6.11_query_trends.sql) | Statements ↑, p95 ↑, read bytes ↑ |
| S4 | Client applications / users | [`6.12_query_clients.sql`](../sql/6.12_query_clients.sql) | New BI tool / service principal / polling |
| S5 | Warehouse cost B vs C, daily | `5.3`, `5.4` | Onset per warehouse |

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-SQL-01 | Size or max clusters increased | SCD2 change ≈ onset; cost/hour ↑ | Unchanged config |
| H-SQL-02 | Auto-stop increased / disabled | `auto_stop_minutes` ↑; RUNNING periods lengthen without query ↑ | Auto-stop unchanged |
| H-SQL-03 | BI refresh / polling storm | Statements ↑ from one `client_application`; regular intervals; keeps warehouse up overnight | Client mix stable |
| H-SQL-04 | Query regression | p95 duration / read bytes / spill ↑ for stable statement count | Per-query metrics stable |
| H-SQL-05 | New warehouse | `NEW` warehouse object | Existed in B |
| H-SQL-06 | Classic/Pro → serverless migration | Classic SQL ↓, serverless SQL ↑ same warehouse IDs | No SKU shift |
| H-SQL-07 | More users | `active_users` ↑ | Stable |

**Remediation options:** auto-stop 5-10 min for serverless; right-size; cap max clusters; dashboard schedules / result caching; query optimization.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
