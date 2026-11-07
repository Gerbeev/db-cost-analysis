# PB-CLASSIC

<!-- plain -->
> **Overview.** Use when clusters in your own Azure subscription cost more - especially **all-purpose** clusters used by people. Typical reasons: clusters left running, larger nodes, more nodes, no auto-stop, jobs running on interactive clusters.
<!-- /plain -->

**Signals:** `ALL_PURPOSE`/`INTERACTIVE`/classic `JOBS`/`SQL` DBU ↑ **and** VM meters ↑ in managed RGs; `5.3` `CLUSTER` objects ↑.

**Diagnostics**

| # | Check | Source | Read |
|---|---|---|---|
| C1 | Cluster config history with pre-window baseline | [`6.06_cluster_config_history.sql`](../sql/6.06_cluster_config_history.sql) | `auto_termination_minutes`, workers, autoscale min/max, node types, availability |
| C2 | Node-minutes, CPU/memory utilization | [`6.07_node_utilization.sql`](../sql/6.07_node_utilization.sql) | Node-minutes ↑; low CPU minutes share |
| C3 | Cluster cost B vs C | [`5.3_object_delta.sql`](../../05_databricks_decomposition/sql/5.3_object_delta.sql) (object_type `CLUSTER`) | Top clusters |
| C4 | VM meters by VM size and pricing model | Cost Analysis: Meter + *Pricing model* + Resource (managed RG) | VM family change; Spot vs On-demand |
| C5 | Disks | Cost Analysis: Managed Disks meters in managed RG | Premium/size growth |
| C6 | Who created/edited clusters | [`6.14_audit_change_events.sql`](../sql/6.14_audit_change_events.sql) (service `clusters`) | Actor and timestamp |
| C7 | Observed DBU per node-hour (node type, SKU, Photon) | [`6.15_dbu_per_node_hour.sql`](../sql/6.15_dbu_per_node_hour.sql) (run for B and C) | `dbu_per_node_hour` up with same node type = Photon/SKU/tier (H-CLS-07); node type mix shift = H-CLS-03 |

**Mechanisms**

| ID | Mechanism | Confirms | Rejects |
|---|---|---|---|
| H-CLS-01 | Auto-termination disabled or increased | `auto_termination_minutes` 0 or ↑ at onset; node-minutes ↑ with low CPU | Unchanged; utilization proportional |
| H-CLS-02 | More workers / higher autoscale minimum | Worker/min change at onset; node-minutes ↑ | Spec unchanged |
| H-CLS-03 | Larger / pricier VM family | Node type change; VM meter shifts to new size | Same node types |
| H-CLS-04 | More interactive clusters / users | New `CLUSTER` objects (`cluster_source = UI/API`) | Same cluster set |
| H-CLS-05 | Oversizing (low utilization) | `sampled_low_cpu_minutes / observed_node_minutes` ≥ 50% in C and ↑ vs B | High utilization |
| H-CLS-06 | Spot → on-demand fallback | `azure_availability` change or VM Pricing model shift to On-demand; VM cost ↑ ≫ DBU ↑ | Availability unchanged |
| H-CLS-07 | Photon / runtime / tier raising DBU rate | `dbu_per_node_hour` or SKU/Photon mix up with same node types (`6.15`) | Same SKU and ratio flat |
| H-CLS-08 | Disk growth | Managed Disk meters ↑; elastic disk enabled | Disk meters flat |

**Remediation options:** cluster policies (max auto-termination, max workers, allowed node types); job clusters for scheduled work; shared clusters for interactive users; spot with fallback where tolerant; right-size after utilization review.

---
Record results in `06_root_cause/results/` of the audit; update `hypothesis_register.csv` and `evidence_register.csv`. Back to [step 06](../README.md).
