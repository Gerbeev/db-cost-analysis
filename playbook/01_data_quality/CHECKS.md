# Step 01 - Data quality · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C1.1 One export run per month; partitions of one run concatenated once; run IDs saved (STOP-1)
- [ ] C1.2 Export is Actual cost (not Amortized / FOCUS) (STOP-4)
- [ ] C1.3 Single billing currency in the export (STOP-2) - auto
- [ ] C1.4 No month gaps in the window (STOP-3) - auto
- [ ] C1.5 Export vs Cost Analysis per month ≤ 0.5% or explained (R6); max diff in scope §5
- [ ] C1.6 1.1_usage_coverage: days_with_data = days_in_month for every full month
- [ ] C1.7 Workspace presence reviewed; APPEARED_IN_WINDOW workspaces noted for step 03 (scope change)
- [ ] C1.8 1.2 units inventory reviewed; no cross-unit sums planned
- [ ] C1.9 1.3 price join: every FAIL_* SKU listed in §5 and excluded from modeled cost (R7) - auto lists them
- [ ] C1.10 System-table availability per region in §4; missing tables = UNKNOWN
- [ ] C1.11 Evidence rows EVD-01-nnn added for every saved output - auto
- [ ] G1 R6 and R7 pass, or failures recorded as limitations in scope §5

## Required outputs

- `01_data_quality/exports/azure_actual*.csv` - consolidated Azure Actual export
- `01_data_quality/exports/export_manifest*` - run IDs / manifests per month
- `01_data_quality/exports/cost_analysis_monthly*.csv` - Cost Analysis monthly download
- `01_data_quality/results/export_monthly*.csv` - export monthly totals (tool)
- `01_data_quality/results/R6_reconciliation*.csv` - export vs Cost Analysis per month
- `01_data_quality/results/1.1_usage_coverage*.csv` - SQL 1.1
- `01_data_quality/results/1.2_usage_units_inventory*.csv` - SQL 1.2
- `01_data_quality/results/1.3_price_join_check*.csv` - SQL 1.3
