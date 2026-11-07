# Step 04 - Azure decomposition · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C4.1 Δ/day by subscription produced - auto
- [ ] C4.2 Δ/day by service produced - auto
- [ ] C4.3 Δ/day by meter produced - auto
- [ ] C4.4 Δ/day by resource group produced - auto
- [ ] C4.5 Δ/day by resource produced for material lines - auto
- [ ] C4.6 All groupings total the same delta/day - auto
- [ ] C4.7 Negative movers kept (not filtered out)
- [ ] C4.8 Every material line (R3) assigned to one bucket; bucket lines added to delta_bridge.csv
- [ ] C4.9 Workspace ↔ managed RG ↔ dependency RG map saved - auto
- [ ] C4.10 Σ bucket Δ = operational Δ (±1%)
- [ ] C4.11 Evidence rows EVD-04-nnn added - auto
- [ ] G4 Every material Azure line has a bucket and buckets reconcile to operational Δ

## Required outputs

- `04_azure_decomposition/results/delta_by_subscription*.csv` - grouping by subscription
- `04_azure_decomposition/results/delta_by_service*.csv` - grouping by service
- `04_azure_decomposition/results/delta_by_meter*.csv` - grouping by meter
- `04_azure_decomposition/results/delta_by_resource_group*.csv` - grouping by RG
- `04_azure_decomposition/results/workspace_rg_map*` - workspace ↔ RG mapping
