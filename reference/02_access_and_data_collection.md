# 02 · Access and data collection

<!-- plain -->
> **Overview.** A checklist of what you must be allowed to see and how to download it. Send the access list to the people who manage Azure and Databricks **early** - getting access is usually the slowest part of an audit. Everything here is read-only.
<!-- /plain -->

## 1. Minimum read access

| Source | Role / privilege | Used in steps | If denied |
|---|---|---|---|
| Azure Cost Management | **Cost Management Reader** (view) or **Cost Management Contributor** (create exports) at billing scope / subscriptions; EA: Enterprise read-only user; MCA: billing profile Reader | 1-4 | Ask FinOps for an existing Actual export of the same scope |
| Azure Exports storage | Storage Blob Data Reader on export container | 1 | Ask export owner for files + manifest |
| Azure resources | **Reader** on subscriptions incl. managed RGs | 4, 6 | Mapping workspace↔RG becomes `UNKNOWN` |
| Azure Activity Log | Reader (the portal keeps 90 days) | 6 | Change evidence from Databricks audit only |
| Databricks system tables | `USE CATALOG system`, `USE SCHEMA` + `SELECT` on `billing`, `compute`, `lakeflow`, `query`, `access` | 1, 2, 5, 6 | Mark source `UNKNOWN`, not zero |
| Databricks SQL warehouse | CAN USE on an existing warehouse | 1-6 | Approval needed: queries consume DBUs |
| Databricks UI (Jobs, Compute, SQL Warehouses) | CAN VIEW / workspace user | 6 | Rely on system tables |
| IBM Cloudability / ApptioOne | Read-only report access | 3, 8 | Skip (optional lens) |

Never escalate privileges beyond what is approved. Record denied sources in scope record §4.

## 2. Azure Actual Cost

### 2.1 Interactive (Cost analysis)
1. `portal.azure.com` → search **Cost Management** → select the **Scope** pill (top left), highlight the scope, **Select** → **Cost analysis** in the left menu.
2. Cost analysis opens a list of views or a chart. In **All views** open a *customizable* view (for example **Cost by service**): only these show date range, granularity and **Group by**.
3. Metric: **Actual cost** (the down arrow next to the cost figure switches to **Amortized cost**). Date: the full months of the window. Granularity: **Monthly**; **Daily** only for the onset window (at most three months per daily range).
4. **Group by**, one at a time: *Subscription*, *Service name*, *Meter category*, *Meter*, *Resource group name*, *Resource*, *Charge type*, *Pricing model*, *Location*, *Tag*.
5. Start **without** a service filter; add filters only after the full-scope total is known.
6. **Download** → CSV for evidence (record scope ID, view, timestamp). Cost analysis shows the data of Cost Management, which has no taxes and credits: compare it with the export, not with the invoice.

### 2.2 Bulk (Exports)
Needs **Cost Management Contributor** (or higher) on the scope and write access to a storage account.
1. Cost Management → **Exports** → **+ Create** → **Basics**: *Create your own export* → **Datasets**: **Type of data** *Cost and usage details (actual)*, an **Export prefix** and **Export name**; frequency *Monthly export of last month's costs* → **Destination**: Azure blob storage, subscription, resource group, storage account, container, directory, format **CSV**, compression **None** → **Review + create**. Data can take up to 24 hours to be ready.
2. For each past month: select the export → **Export selected dates** → the first and last day of one month (the portal reaches back 13 months, one month per run; older data: Exports - Execute REST API). A run can take up to 4 hours; **Refresh** the run history. Afterwards **Disable** the export.
3. Files: `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/` in the container (storage account → **Open in Explorer** or **Storage browser**). Keep the **manifest** (`manifest.json`): run ID, partition list.
4. Per month take **one run**; file partitioning cannot be disabled, so join its parts once (single header). Never append several runs of the same month or daily month-to-date snapshots - this multiplies cost.
5. Minimum columns: `Date`, `CostInBillingCurrency` (EA/MCA) or `Cost`, `BillingCurrencyCode`/`BillingCurrency`, `SubscriptionId`, `ResourceGroup`, `ResourceId`, `ServiceName`, `MeterCategory`, `MeterSubCategory`, `MeterName`, `Quantity`, `UnitOfMeasure`, `EffectivePrice`, `ChargeType`, `PricingModel`, `PublisherType`, `Tags`, `ResourceLocation`.
6. Do not feed Amortized or FOCUS files into tools expecting Actual. Without the rights: ask FinOps for an existing *Cost and usage details (actual)* export of the same scope.

### 2.3 Workspace ↔ managed RG mapping
- Portal → search **Azure Databricks** → the workspace → **Overview**: *Managed Resource Group*, *Pricing Tier*.
- Or UI action 4.2 (read-only Azure CLI inventory after `az login`; same logic as `../tools/azure_workspace_inventory.ps1`).
- Also list dependency RGs: lake storage, VNet/NAT/Private Link, Key Vault, Log Analytics.

## 3. Databricks system tables

| Table | Grain | Scope | Retention (free) | Caveats |
|---|---|---|---|---|
| `system.billing.usage` | Usage record (hourly-ish) per SKU | Account-wide | Indefinite | Corrections (`RETRACTION`/`RESTATEMENT`); NULL IDs by design; mixed units |
| `system.billing.list_prices` | Price version per SKU/unit | Account | Indefinite | List price, not contract; currency per row |
| `system.lakeflow.jobs` | SCD2 job definitions | Regional | 395 days | `job_id` unique per workspace only |
| `system.lakeflow.job_run_timeline` | Run, sliced hourly | Regional | 395 days | Collapse by `workspace_id, job_id, run_id` |
| `system.lakeflow.pipeline_update_timeline` | Pipeline update, sliced | Regional | 395 days | Collapse by `update_id` |
| `system.compute.clusters` | SCD2 cluster config | Regional | Indefinite | Keep last pre-window row as baseline |
| `system.compute.node_timeline` | Per node per minute | Regional | 395 days | Short-lived nodes may be missing |
| `system.compute.instance_events` | Pool instance state transitions | Regional | 395 days | Completed intervals only |
| `system.compute.warehouses` | SCD2 warehouse config | Regional | 395 days | |
| `system.compute.warehouse_events` | Start/stop/scale events | Regional | 395 days | Events ≠ billed hours |
| `system.query.history` | Statement | Regional | 365 days | Duration ≠ cost |
| `system.access.audit` | Audit events | Regional (account-level events: global) | 395 days | Sensitive; aggregate only |

Retention as listed on the Microsoft Learn page *Monitor account activity with system tables* (checked 9 Nov 2026); it changes, so check the current page ([`reference/09`](09_sources_and_glossary.md)). A missing table is a capability gap, not absence of workload. System tables need a workspace with Unity Catalog and are not available in Azure China, Azure Government, West India and Switzerland West. Where to look: **Catalog** in the workspace sidebar → catalog `system`. Who can read: users that are both account admin and metastore admin; for everyone else `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas.

**Run order:** follow the playbook steps; each step README lists its SQL and the exact save location (`audits/<id>/<step>/results/`). Conventions: [11_sql_conventions.md](11_sql_conventions.md).

## 4. Change evidence sources (Step 6)

| Source | What it proves |
|---|---|
| `system.compute.clusters` / `warehouses` / `lakeflow.jobs` (SCD2) | Configuration value and change timestamp |
| `system.access.audit` | Who/what action at what time (create/edit/start/permissions) |
| Azure Activity Log | ARM-level changes (workspace, VNet, storage, diagnostic settings) |
| Git / CI-CD / Terraform / Asset Bundle history | Deployed definition and release date |
| Change tickets, release notes | Intent and approval |
| Databricks account console → Previews / feature enablement | Account-level feature switches |

## 5. Data handling

- Raw exports and query results contain subscription IDs, resource names, users, cost centers → store in an access-controlled location, never in Git.
- Do not export `statement_text`, request parameters or user e-mails; the SQL in this kit aggregates.
- Redact IDs and names in anything leaving the audit team; keep the unredacted original as evidence.
- Do not start or resize a warehouse just to run audit SQL without approval.
- CSV files opened in spreadsheets: beware formula-like cells (`=`, `+`, `-`, `@`) from untrusted names.
