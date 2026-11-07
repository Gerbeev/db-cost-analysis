# Step 07 - Attribution, ownership and residual

[06 Root cause](../06_root_cause/README.md) ← `07` → [08 Validation](../08_validation/README.md) · [Playbook index](../README.md)

<!-- plain -->
> **Overview.** The numbers must now reconcile. Subtract everything explained from the total growth: accounting effects, root causes, shared cost, out-of-scope cost. The remainder is the unexplained part. A residual is acceptable; concealing it is not.
>
> Every confirmed cause also receives an owner: a person or team able to implement the fix. A finding without an owner does not lead to action.
>
> **Result:** owners on every confirmed line and the calculated unexplained share.
>
> **Note:** Do not distribute the unexplained part across drivers to make the table reconcile.
<!-- /plain -->

**Goal:** every unit of Δ has an owner or is explicitly unresolved; the delta bridge closes.
**Inputs:** G6 passed. **Work in:** `audits/<id>/delta_bridge.csv`, `audits/<id>/07_attribution_and_residual/`.

## Do

| # | Action | Source | Save to |
|---|---|---|---|
| 7.1 | Owner for every CONFIRMED / LIKELY driver (workspace owner, job owner, tags `owner`, `cost_center`, `application`) | driver cards, `5.3` `sample_run_as`, tags | `delta_bridge.csv` column `owner` |
| 7.2 | Shared resources: allocate only with an evidenced key (usage share, bytes, request count); else `SHARED_UNALLOCATED` | Azure resources, metrics | `results/shared_allocation.csv` + line `SH-01` |
| 7.3 | Unattributed / untagged Databricks Δ | `05_databricks_decomposition/results/5.5_attribution_coverage*.csv` | `notes.md` |
| 7.4 | Out-of-scope Δ (non-Databricks services) | step 04 buckets | line `OOS-01` |
| 7.5 | Residual: `UNX = TOTAL - Σ(ACCOUNTING + ROOT_CAUSE + SHARED_UNALLOCATED + OUT_OF_SCOPE)` | UI calculator 7.5 | line `UNX` + shares |

Bridge identity (checked automatically): `TOTAL = Σ ACCOUNTING + Σ ROOT_CAUSE + SHARED_UNALLOCATED + OUT_OF_SCOPE + UNEXPLAINED`. `BUCKET` and `DRIVER_CANDIDATE` lines are informational and excluded.

## Automatic checks

- Bridge identity within 1% of TOTAL.
- `UNEXPLAINED` ≤ 10% of TOTAL (R4). If larger: either continue step 06, or mark C7.6 `[!] | accepted by <owner>`.

## Gate G7

Bridge closes; UNEXPLAINED ≤ 10% or explicitly accepted by the audit owner.
