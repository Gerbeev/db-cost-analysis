# SYNTHETIC_ONLY - Example analytical output

> The amounts and the apparent March/April 2026 increase below are generated from fictional demonstration CSVs. This is **not** evidence of a real Azure tenant increase.

# Azure Databricks cost investigation - local summary

**Period:** 2026-01 through 2026-10 (completed months only).

**Do not add** Databricks list-price estimates to Azure billed actuals; they are separate lenses.

## Azure Actual

| Month | Currency | Cost |
|---|---|---:|
| 2026-01 | EUR | 810.00 |
| 2026-02 | EUR | 825.00 |
| 2026-03 | EUR | 862.00 |
| 2026-04 | EUR | 1305.00 |
| 2026-05 | EUR | 1322.00 |
| 2026-06 | EUR | 1320.00 |
| 2026-07 | EUR | 1375.00 |
| 2026-08 | EUR | 1405.00 |
| 2026-09 | EUR | 1439.00 |
| 2026-10 | EUR | 1471.00 |

- EUR: **2026-01 → 2026-10 delta: 661.00 (81.60%)**.

## 2026 March/April change-point analysis - Azure

Suspected timing only. The cost increase remains unverified until reconciled to source billing and workload evidence.
Monthly totals are also normalized to average cost per calendar day to account for month length.

| Month | Currency | Previous | Cost | Monthly delta | Daily-average delta | Daily-average % |
|---|---|---|---:|---:|---:|---:|
| 2026-02 | EUR | 2026-01 | 825.00 | 15.00 | 3.34 | 12.76 |
| 2026-03 | EUR | 2026-02 | 862.00 | 37.00 | -1.66 | -5.63 |
| 2026-04 | EUR | 2026-03 | 1305.00 | 443.00 | 15.69 | 56.44 |
| 2026-05 | EUR | 2026-04 | 1322.00 | 17.00 | -0.85 | -1.97 |

Full 2026 month-over-month data: `change_point_mom_azure_actual.csv`.
Check whether the increase began in March, accelerated in April, and persisted in May; compare February and earlier spend before attributing causality.

## Databricks Estimated List Price

| Month | Currency | Cost |
|---|---|---:|
| 2026-01 | USD | 307.60 |
| 2026-02 | USD | 314.20 |
| 2026-03 | USD | 339.20 |
| 2026-04 | USD | 488.40 |
| 2026-05 | USD | 485.80 |
| 2026-06 | USD | 497.00 |
| 2026-07 | USD | 512.80 |
| 2026-08 | USD | 524.00 |
| 2026-09 | USD | 539.80 |
| 2026-10 | USD | 551.00 |

- USD: **2026-01 → 2026-10 delta: 243.40 (79.13%)**.

## 2026 March/April change-point analysis - Databricks

Suspected timing only. The cost increase remains unverified until reconciled to source billing and workload evidence.
Monthly totals are also normalized to average cost per calendar day to account for month length.

| Month | Currency | Previous | Cost | Monthly delta | Daily-average delta | Daily-average % |
|---|---|---|---:|---:|---:|---:|
| 2026-02 | USD | 2026-01 | 314.20 | 6.60 | 1.30 | 13.09 |
| 2026-03 | USD | 2026-02 | 339.20 | 25.00 | -0.28 | -2.49 |
| 2026-04 | USD | 2026-03 | 488.40 | 149.20 | 5.34 | 48.79 |
| 2026-05 | USD | 2026-04 | 485.80 | -2.60 | -0.61 | -3.74 |

Full 2026 month-over-month data: `change_point_mom_databricks_estimated.csv`.
Check whether the increase began in March, accelerated in April, and persisted in May; compare February and earlier spend before attributing causality.

## Largest positive deltas - Azure services

Detailed file: `growth_azure_services.csv`. These are separate breakdowns of the SAME Azure charges; do not sum across breakdowns.

| Driver | Currency | Delta |
|---|---|---:|
| Virtual Machines | EUR | 390.00 |
| Azure Databricks | EUR | 245.00 |
| Storage | EUR | 26.00 |

### February→March drivers - Azure services

Detailed file: `growth_feb_mar_azure_services.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Azure Databricks | EUR | 25.00 |
| Virtual Machines | EUR | 10.00 |
| Storage | EUR | 2.00 |

### March→April drivers - Azure services

Detailed file: `growth_mar_apr_azure_services.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Virtual Machines | EUR | 280.00 |
| Azure Databricks | EUR | 160.00 |
| Storage | EUR | 3.00 |

### April→May drivers - Azure services

Detailed file: `growth_apr_may_azure_services.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Virtual Machines | EUR | 20.00 |
| Storage | EUR | 2.00 |
| Azure Databricks | EUR | -5.00 |

## Largest positive deltas - Azure meters

Detailed file: `growth_azure_meters.csv`. These are separate breakdowns of the SAME Azure charges; do not sum across breakdowns.

| Driver | Currency | Delta |
|---|---|---:|
| Virtual Machines / D-Series VMs | EUR | 390.00 |
| Azure Databricks / Databricks Usage | EUR | 245.00 |
| Storage / Blob Storage | EUR | 26.00 |

### February→March drivers - Azure meters

Detailed file: `growth_feb_mar_azure_meters.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Azure Databricks / Databricks Usage | EUR | 25.00 |
| Virtual Machines / D-Series VMs | EUR | 10.00 |
| Storage / Blob Storage | EUR | 2.00 |

### March→April drivers - Azure meters

Detailed file: `growth_mar_apr_azure_meters.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Virtual Machines / D-Series VMs | EUR | 280.00 |
| Azure Databricks / Databricks Usage | EUR | 160.00 |
| Storage / Blob Storage | EUR | 3.00 |

### April→May drivers - Azure meters

Detailed file: `growth_apr_may_azure_meters.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Virtual Machines / D-Series VMs | EUR | 20.00 |
| Storage / Blob Storage | EUR | 2.00 |
| Azure Databricks / Databricks Usage | EUR | -5.00 |

## Largest positive deltas - Azure resource groups

Detailed file: `growth_azure_resource_groups.csv`. These are separate breakdowns of the SAME Azure charges; do not sum across breakdowns.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE | EUR | 661.00 |

### February→March drivers - Azure resource groups

Detailed file: `growth_feb_mar_azure_resource_groups.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE | EUR | 37.00 |

### March→April drivers - Azure resource groups

Detailed file: `growth_mar_apr_azure_resource_groups.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE | EUR | 443.00 |

### April→May drivers - Azure resource groups

Detailed file: `growth_apr_may_azure_resource_groups.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE | EUR | 17.00 |

## Largest positive deltas - Azure resources

Detailed file: `growth_azure_resources.csv`. These are separate breakdowns of the SAME Azure charges; do not sum across breakdowns.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/vm-synthetic | EUR | 390.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/dbu-synthetic | EUR | 245.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/storage-synthetic | EUR | 26.00 |

### February→March drivers - Azure resources

Detailed file: `growth_feb_mar_azure_resources.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/dbu-synthetic | EUR | 25.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/vm-synthetic | EUR | 10.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/storage-synthetic | EUR | 2.00 |

### March→April drivers - Azure resources

Detailed file: `growth_mar_apr_azure_resources.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/vm-synthetic | EUR | 280.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/dbu-synthetic | EUR | 160.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/storage-synthetic | EUR | 3.00 |

### April→May drivers - Azure resources

Detailed file: `growth_apr_may_azure_resources.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/vm-synthetic | EUR | 20.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/storage-synthetic | EUR | 2.00 |
| SYNTHETIC-EXAMPLE / rg-SYNTHETIC-EXAMPLE / /subscriptions/SYNTHETIC-EXAMPLE/resourceGroups/rg-SYNTHETIC-EXAMPLE/providers/example/dbu-synthetic | EUR | -5.00 |

## Largest positive deltas - Azure charge types

Detailed file: `growth_azure_charge_types.csv`. These are separate breakdowns of the SAME Azure charges; do not sum across breakdowns.

| Driver | Currency | Delta |
|---|---|---:|
| Usage | EUR | 661.00 |

### February→March drivers - Azure charge types

Detailed file: `growth_feb_mar_azure_charge_types.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Usage | EUR | 37.00 |

### March→April drivers - Azure charge types

Detailed file: `growth_mar_apr_azure_charge_types.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Usage | EUR | 443.00 |

### April→May drivers - Azure charge types

Detailed file: `growth_apr_may_azure_charge_types.csv`.

| Driver | Currency | Delta |
|---|---|---:|
| Usage | EUR | 17.00 |

## Largest positive deltas - Databricks account/workspace/product/SKU

Detailed file: `growth_databricks.csv`. These are list-price estimates, NOT Azure billed actuals.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / JOBS / SYNTHETIC_CLASSIC_JOB | USD | 225.40 |
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / SQL / SYNTHETIC_SQL | USD | 18.00 |

### February→March drivers - Databricks account/workspace/product/SKU

Detailed file: `growth_feb_mar_databricks.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / JOBS / SYNTHETIC_CLASSIC_JOB | USD | 23.00 |
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / SQL / SYNTHETIC_SQL | USD | 2.00 |

### March→April drivers - Databricks account/workspace/product/SKU

Detailed file: `growth_mar_apr_databricks.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / JOBS / SYNTHETIC_CLASSIC_JOB | USD | 147.20 |
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / SQL / SYNTHETIC_SQL | USD | 2.00 |

### April→May drivers - Databricks account/workspace/product/SKU

Detailed file: `growth_apr_may_databricks.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / SQL / SYNTHETIC_SQL | USD | 2.00 |
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE / JOBS / SYNTHETIC_CLASSIC_JOB | USD | -4.60 |

## Largest positive deltas - Databricks product/SKU

Detailed file: `growth_databricks_skus.csv`. These are list-price estimates, NOT Azure billed actuals.

| Driver | Currency | Delta |
|---|---|---:|
| JOBS / SYNTHETIC_CLASSIC_JOB | USD | 225.40 |
| SQL / SYNTHETIC_SQL | USD | 18.00 |

### February→March drivers - Databricks product/SKU

Detailed file: `growth_feb_mar_databricks_skus.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| JOBS / SYNTHETIC_CLASSIC_JOB | USD | 23.00 |
| SQL / SYNTHETIC_SQL | USD | 2.00 |

### March→April drivers - Databricks product/SKU

Detailed file: `growth_mar_apr_databricks_skus.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| JOBS / SYNTHETIC_CLASSIC_JOB | USD | 147.20 |
| SQL / SYNTHETIC_SQL | USD | 2.00 |

### April→May drivers - Databricks product/SKU

Detailed file: `growth_apr_may_databricks_skus.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| SQL / SYNTHETIC_SQL | USD | 2.00 |
| JOBS / SYNTHETIC_CLASSIC_JOB | USD | -4.60 |

## Largest positive deltas - Databricks workspaces

Detailed file: `growth_databricks_workspaces.csv`. These are list-price estimates, NOT Azure billed actuals.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE | USD | 243.40 |

### February→March drivers - Databricks workspaces

Detailed file: `growth_feb_mar_databricks_workspaces.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE | USD | 25.00 |

### March→April drivers - Databricks workspaces

Detailed file: `growth_mar_apr_databricks_workspaces.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE | USD | 149.20 |

### April→May drivers - Databricks workspaces

Detailed file: `growth_apr_may_databricks_workspaces.csv`. Modeled list-price estimate only.

| Driver | Currency | Delta |
|---|---|---:|
| SYNTHETIC-ACCOUNT / SYNTHETIC-WORKSPACE | USD | -2.60 |

## Next steps

1. Read `data_quality.md` and resolve gaps.
2. Validate Azure actual totals at the same financial scope and export revision.
3. Review February→March, March→April and April→May per-day-normalized cost changes; investigate March→April top Azure/Databricks drivers and workloads.
4. Capture timestamps, owners, cause and alternatives in `audits/<id>/09_report_and_controls/findings_report.md`.
5. Request approval before making any infrastructure or scheduling change.
