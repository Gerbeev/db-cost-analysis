# PB-MONITOR

<!-- plain -->
> **Overview.** Use when the **MONITORING** category grew - usually Log Analytics after someone turned on more detailed diagnostic logs.
<!-- /plain -->

**Signals:** Log Analytics / Azure Monitor meters ↑.

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-MON-01 | New / verbose diagnostic settings (workspace, storage, NSG flow logs) | Ingestion GB ↑; diagnostic setting created ≈ onset (Activity Log) | Flat |
| H-MON-02 | Retention increased | Retention meter ↑; workspace retention change | Unchanged |
| H-MON-03 | Cluster log / init script log volume | Ingestion tables per source (`Usage` table in Log Analytics) | Other source |

Diagnostics: Log Analytics → *Usage and estimated costs*; query `Usage | summarize sum(Quantity) by DataType, bin(TimeGenerated, 1d)`.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
