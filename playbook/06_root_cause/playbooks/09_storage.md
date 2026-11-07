# PB-STORAGE

<!-- plain -->
> **Overview.** Use when the **STORAGE** category grew: more data stored, longer retention, many small files, or more reads and writes.
<!-- /plain -->

**Signals:** Azure Storage meters ↑ on lake / workspace / UC storage accounts.

| # | Check | Source | Read |
|---|---|---|---|
| T1 | Split capacity vs transactions vs replication vs egress | Cost Analysis: Storage, group by Meter subcategory/Meter, per storage account | Which meter type |
| T2 | Capacity trend | Storage account → Insights / Metrics (`UsedCapacity`) | TB ↑ |
| T3 | Transactions trend | Metrics (`Transactions` by API name) | List/read/write ↑ |
| T4 | Policies | Lifecycle management, soft delete, versioning, redundancy (Activity Log) | Change ≈ onset |
| T5 | Databricks side | Table maintenance (OPTIMIZE/VACUUM) schedules; new jobs reading same paths (`5.3`) | Workload behind transactions |

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-STO-01 | Capacity growth (retention, no VACUUM, new datasets) | Capacity meter ↑, `UsedCapacity` ↑ | Capacity flat |
| H-STO-02 | Transaction surge (small files, listing, retries, new readers) | Transaction meters ↑ with flat capacity; matching job onset | Transactions flat |
| H-STO-03 | Tier / redundancy change (LRS → GRS, cool → hot) | Meter names change; Activity Log | No config change |
| H-STO-04 | Snapshots / soft delete / versioning | Snapshot/versioning capacity meters ↑ | Flat |

**Remediation options:** VACUUM/retention policy; lifecycle tiering; file compaction; redundancy review.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
