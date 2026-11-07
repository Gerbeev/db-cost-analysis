# PB-AI-APPS

<!-- plain -->
> **Overview.** Use when model serving, Vector Search, AI functions, Databricks Apps or Lakebase cost more. These bill in their own units; look for a new endpoint, more traffic or a larger index.
<!-- /plain -->

**Signals:** `MODEL_SERVING`, `VECTOR_SEARCH`, `FOUNDATION_MODEL_TRAINING`, `AI_GATEWAY`, `AI_FUNCTIONS`, `AGENT_*`, `APPS`, `DATABASE` products ↑.

| # | Check | Source | Read |
|---|---|---|---|
| A1 | Usage by product/SKU/unit | [`1.2_usage_units_inventory.sql`](../../01_data_quality/sql/1.2_usage_units_inventory.sql), `6.13` | Units (DBU, tokens, hours) per product |
| A2 | Endpoint/app objects | `5.3` (`SERVING_ENDPOINT`, `APP`) | New / always-on endpoints |
| A3 | Endpoint configuration | Serving UI: scale-to-zero, min/max concurrency, provisioned throughput, GPU size | Config change ≈ onset |
| A4 | First seen | [`5.6_first_seen_skus.sql`](../../05_databricks_decomposition/sql/5.6_first_seen_skus.sql) | Feature start date |

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-AI-01 | New endpoint / provisioned throughput | `NEW` endpoint object; first-seen SKU ≈ onset | Existed |
| H-AI-02 | Scale-to-zero disabled / min concurrency ↑ | Flat 24h usage per endpoint from onset | Usage tracks requests |
| H-AI-03 | Token surge (FM APIs, AI Functions) | Token quantities ↑ | Flat |
| H-AI-04 | Vector Search endpoints / index growth | Vector Search units ↑ | Flat |
| H-AI-05 | Apps / Lakebase always-on | Hours ≈ 24/day | Usage proportional to activity |

**Remediation options:** scale-to-zero for non-prod; right-size provisioned throughput; stop idle apps; batch AI functions.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
