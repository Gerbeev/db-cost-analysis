# PB-FEATURES

<!-- plain -->
> **Overview.** Use when background platform features cost more: predictive optimization, data-quality monitoring, networking features. They often appear **after someone enables a setting** for the whole account.
<!-- /plain -->

**Signals:** `PREDICTIVE_OPTIMIZATION`, `LAKEHOUSE_MONITORING`, `DATA_QUALITY_MONITORING`, `FINE_GRAINED_ACCESS_CONTROL`, `LAKEFLOW_CONNECT`, `DEFAULT_STORAGE`, `DATA_CLASSIFICATION` ↑ or first seen.

| # | Check | Source | Read |
|---|---|---|---|
| F1 | First-seen products/SKUs | [`5.6_first_seen_skus.sql`](../../05_databricks_decomposition/sql/5.6_first_seen_skus.sql) | Start date = enablement |
| F2 | Monthly usage | [`6.13_serverless_and_features.sql`](../sql/6.13_serverless_and_features.sql) | Growth |
| F3 | Enablement state | Account console → Settings / Previews; catalog settings (predictive optimization inheritance); audit `6.14` | Who enabled, when |

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-FEA-01 | Predictive optimization enabled / scope widened | First seen or step ↑ in `PREDICTIVE_OPTIMIZATION` | Absent/flat |
| H-FEA-02 | Lakehouse / data quality monitors added | Monitoring SKUs ↑; monitor count ↑ | Flat |
| H-FEA-03 | FGAC filtering on dedicated compute | `FINE_GRAINED_ACCESS_CONTROL` ↑ | Flat |
| H-FEA-04 | Managed ingestion (Lakeflow Connect) | Product ↑, new gateways | Flat |
| H-FEA-05 | Default storage usage | `DEFAULT_STORAGE` ↑ | Flat |

**Remediation options:** scope feature to required catalogs; monitor refresh frequency; evaluate benefit vs cost (predictive optimization often reduces query cost - measure both sides).

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
