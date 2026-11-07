# Step 01 - Lock data and check quality

[00 Frame](../00_frame/README.md) ← `01` → [02 Confirm and size](../02_confirm_and_size/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** This step downloads the data and verifies its integrity. Most incorrect conclusions in cost audits originate in the input, not in the analysis: a month exported twice, two currencies in one column, a day without records.
>
> You download one detailed export from the Azure portal and one summary report for cross-checking, then run read-only SQL checks in Databricks. The application calculates the reconciliation and reports whether it passes.
>
> **Result:** the main export file saved in the audit, a green R6 reconciliation, and a list of SKUs excluded from the model.
>
> **Note:** Export one run per month. Never concatenate runs: overlapping runs double the cost.
<!-- /plain -->

**Goal:** one complete, deduplicated, comparable dataset per ledger before any delta is computed.
**Inputs:** approved scope (G0). **Work in:** `audits/<id>/01_data_quality/`.
**How-to for portals and exports:** [reference/02](../../reference/02_access_and_data_collection.md).

## Do

| # | Action | Tool | Save to (`audits/<id>/01_data_quality/…`) |
|---|---|---|---|
| 1.1 | Azure Actual cost-details export for the window, **one export run per month**; concatenate the partitions of one run once (single header) | Cost Management → Exports; upload in UI action 1.1 | `exports/azure_actual__<from>_<to>.csv` |
| 1.2 | Save the run IDs / manifest of every month used | Exports → `manifest.json` | `exports/export_manifest__<month>.json` (or one `export_manifest.md` list) |
| 1.3 | Download Cost Analysis **Actual, monthly**, same scope, no filters | Cost Analysis → Download CSV | `exports/cost_analysis_monthly__<from>_<to>.csv` |
| 1.4 | Monthly totals of the export | UI action 1.4 (tool *Monthly series*) | `results/export_monthly__….csv` |
| 1.5 | Compare 1.3 vs 1.4 per month (R6 ≤ 0.5%) | UI action 1.5 (calculator *R6 reconciliation*) | `results/R6_reconciliation.csv` (month, export, cost_analysis, diff %) |
| 1.6 | Databricks usage coverage | [`sql/1.1_usage_coverage.sql`](sql/1.1_usage_coverage.sql) (`:start_date`, `:end_date`) | `results/1.1_usage_coverage__<run date>.csv` (+ query B as `1.1_workspace_presence__….csv`) |
| 1.7 | Units / SKU inventory | [`sql/1.2_usage_units_inventory.sql`](sql/1.2_usage_units_inventory.sql) | `results/1.2_usage_units_inventory__….csv` |
| 1.8 | Price-join validation (R7) | [`sql/1.3_price_join_check.sql`](sql/1.3_price_join_check.sql) | `results/1.3_price_join_check__….csv` |
| 1.9 | System-table availability per region (`lakeflow`, `compute`, `query`, `access`) | Catalog Explorer → `system` | `scope_record.md` §4 |
| 1.10 | Summarize in scope_record §5 (UI action 1.9); evidence rows `EVD-01-nnn` are added automatically and check C1.11 is ticked by the app | - | `scope_record.md`, `evidence_register.csv` |

SQL actions (1.6-1.8) show the query with parameters pre-filled from the audit periods: run it directly from the UI when a Databricks connection is configured (**Settings**), or copy it into the Databricks SQL editor and upload the CSV in the same action. Conventions: [reference/11](../../reference/11_sql_conventions.md).

## Automatic checks (shown on the step page)

- Export: single currency (STOP-2), no month gaps (STOP-3), count of exact duplicate rows (STOP-1 hint).
- `1.3_price_join_check`: lists SKUs with `FAIL_*` verdict - these must be excluded from modeled cost.

## Stop rules

Overlapping export runs, mixed currencies, missing months → **do not compute deltas** until fixed ([reference/04](../../reference/04_pitfalls_and_stop_rules.md)).

## Gate G1

R6 and R7 pass, or the failing scope/SKUs are excluded and recorded as limitations in §5.
