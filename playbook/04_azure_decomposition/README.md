# Step 04 - Decompose the Azure billed delta

[03 Accounting effects](../03_accounting_effects/README.md) ← `04` → [05 Databricks decomposition](../05_databricks_decomposition/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** The total growth is a single number. This step decomposes it by subscription, service, meter, resource group and resource. Each decomposition is an alternative view of the same total: review them one at a time and never sum two views.
>
> The result is a ranked list of the largest increases, each assigned to a cost category: the Databricks charge, the underlying virtual machines, storage, network, monitoring, or items outside the audit.
>
> **Result:** BUCKET lines in the delta bridge and a map of workspaces to resource groups.
>
> **Note:** Retain decreasing lines as well. Excluding them overstates the remaining increases.
<!-- /plain -->

**Goal:** know *what was billed more*, line by line, one mutually exclusive grouping at a time, and assign every material line to a cost bucket.
**Inputs:** G3 passed; Azure export from step 01. **Work in:** `audits/<id>/04_azure_decomposition/`.
**Formulas and materiality (R3):** [reference/03 §3](../../reference/03_analysis_method.md).

## Do

Every grouping is a UI action with the export, B and C pre-filled from the audit; the output is saved to `audits/<id>/04_azure_decomposition/results/` with an evidence row.

| # | Grouping | UI action | Saved as |
|---|---|---|---|
| 4.1 | Subscription, service, meter, resource group, resource (top 50) | UI action 4.1 - one run writes all five groupings (`SubscriptionId`; `ServiceName`; `ServiceName,MeterCategory,MeterName`; `SubscriptionId,ResourceGroup`; `ResourceId`) | `results/delta_by_subscription__….csv`, `delta_by_service`, `delta_by_meter`, `delta_by_resource_group`, `delta_by_resource` |
| 4.2 | Workspace ↔ managed RG ↔ dependency RG map | UI action 4.2 - read-only Azure CLI inventory (needs `az login`), or build it from Portal → Azure Databricks → workspace → Overview and upload (4.2b) | `results/workspace_rg_map__….csv` |

Column names follow your export schema (EA / MCA differ) - if a column is missing, the action shows the available columns.

Then assign every **material** line (R3: `|Δ/day| ≥ 5%` of total or top-10 positive) to one bucket and add one line per bucket to `delta_bridge.csv` with `category = BUCKET` (informational subtotal, not part of the bridge identity; step 06 replaces it with `ROOT_CAUSE` lines):

| Bucket | Typical Azure lines | Continue in |
|---|---|---|
| `DBX_PLATFORM` | Service *Azure Databricks* (DBU, serverless meters) | Step 05 |
| `DBX_CLASSIC_INFRA` | Virtual Machines, Managed Disks, Public IP, Load Balancer in workspace **managed RG** | Step 05 + playbooks 03 / 04 |
| `STORAGE` | Storage capacity / transactions / replication on lake, DBFS, UC storage | Playbook 09 |
| `NETWORK` | Bandwidth, NAT Gateway, Private Link, Firewall, VPN / ExpressRoute | Playbook 10 |
| `MONITORING` | Log Analytics, Azure Monitor | Playbook 11 |
| `SHARED_UNALLOCATED` | Shared resources without evidenced allocation key | Step 07 |
| `OUT_OF_SCOPE` | Non-Databricks services | Bridge line `OOS-01` |

Keep negative movers. A managed RG is a mapping hint, not proof of ownership.

## Automatic checks

- All `results/delta_by_*.csv` must total the **same** delta/day (same ledger, different groupings) - a mismatch means filters or periods differ.

## Gate G4

Σ bucket Δ = operational Δ (±1%); every material line has a bucket.
