# Step 05 - Decompose Databricks consumption

[04 Azure decomposition](../04_azure_decomposition/README.md) ← `05` → [06 Root cause](../06_root_cause/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** Step 04 established how much Databricks cost grew. This step establishes which objects account for it, moving from the general to the specific: product, workspace, then the individual job, pipeline, SQL warehouse or cluster. All queries are read-only SQL on Databricks system tables.
>
> A good result is a short list, typically three to ten objects, that together explain 90% of the growth. These objects are the driver candidates.
>
> **Result:** DRIVER_CANDIDATE lines in the delta bridge and open hypotheses for each.
>
> **Note:** Calculate money only for SKUs that passed check R7 in step 01. Never add quantities in different units.
<!-- /plain -->

**Goal:** explain `DBX_PLATFORM` (and drive `DBX_CLASSIC_INFRA`) by product → SKU → workspace → object, and produce the driver-candidate list.
**Inputs:** G4 passed; B / C from scope §3; SKUs failing R7 (step 01) excluded from money conclusions.
**Work in:** `audits/<id>/05_databricks_decomposition/results/`. SQL parameters `:base_start`, `:base_end`, `:cmp_start`, `:cmp_end` are pre-filled from the audit; `:object_ids` for 5.4 is pre-filled with the top objects of the latest 5.3 result. Run in the UI (Databricks connection) or copy + upload ([reference/11](../../reference/11_sql_conventions.md)).

## Do

| # | Question | SQL | Read | Save to `results/` |
|---|---|---|---|---|
| 5.1 | Which products / SKUs moved - more quantity or higher price? | [`5.1_sku_volume_rate.sql`](sql/5.1_sku_volume_rate.sql) | `volume_effect` vs `rate_effect` | `5.1_sku_volume_rate__….csv` |
| 5.2 | Which workspaces moved? | [`5.2_workspace_delta.sql`](sql/5.2_workspace_delta.sql) | one workspace = local change; spread = platform / price | `5.2_workspace_delta__….csv` |
| 5.3 | Which objects moved? (job, pipeline, warehouse, cluster, endpoint, app, notebook, pool) | [`5.3_object_delta.sql`](sql/5.3_object_delta.sql) | `change_class`, `cumulative_share` up to 0.90 | `5.3_object_delta__….csv` |
| 5.4 | When did each top object change? (`:object_ids` = top IDs from 5.3) | [`5.4_object_daily.sql`](sql/5.4_object_daily.sql) | object onset vs total onset (±2 days) | `5.4_object_daily__….csv` |
| 5.5 | How much usage has no object ID / tags? | [`5.5_attribution_coverage.sql`](sql/5.5_attribution_coverage.sql) | unattributed share → step 07 | `5.5_attribution_coverage__….csv` |
| 5.6 | Which products / SKUs appeared for the first time? | [`5.6_first_seen_skus.sql`](sql/5.6_first_seen_skus.sql) | `new_in_window` near onset | `5.6_first_seen_skus__….csv` |

Then add one `DRIVER_CANDIDATE` line per top object/SKU to `delta_bridge.csv` (Δ/day in list price, object, change_class), and open matching hypotheses in `hypothesis_register.csv`.

## Rules

- Quantities only within one `usage_unit`; money only for SKUs that pass R7.
- Classic compute: DBU (here) and VM (step 04) are **both** billed - not duplicates.
- Serverless: compute is inside the DBU price; never add VM cost.
- `job_id` is NULL for jobs on all-purpose clusters - that usage appears as `CLUSTER`.

## Automatic checks

- `5.3_object_delta`: reports how many objects reach 90% of the modeled delta (R4).

## Gate G5

Top objects explain ≥ 90% of modeled `DBX_PLATFORM` Δ, or the unattributed remainder is quantified.
