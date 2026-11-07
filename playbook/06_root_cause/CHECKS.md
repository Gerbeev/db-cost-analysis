# Step 06 - Root cause · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C6.1 Every material bucket / DRIVER_CANDIDATE routed to a playbook
- [ ] C6.2 One driver card per material driver (driver_<nn>_<name>.md) - auto
- [ ] C6.3 Playbook diagnostics saved in results/ - auto
- [ ] C6.4 Each driver Δ decomposed (frequency × unit cost or volume × rate)
- [ ] C6.5 Change event found with timestamp and source for each CONFIRMED / LIKELY driver
- [ ] C6.6 ≥ 1 alternative falsified per driver (R9-d)
- [ ] C6.7 R9 applied; statuses set in hypothesis_register.csv
- [ ] C6.8 ROOT_CAUSE lines in delta_bridge.csv in Azure Actual currency/day, with hypothesis_id and evidence_ids - auto
- [ ] C6.9 List-price → billed conversion ratio recorded where used
- [ ] C6.10 Evidence rows EVD-06-nnn added - auto
- [ ] G6 No material driver left as HYPOTHESIS

## Required outputs

- `06_root_cause/driver_*.md` - one driver card per material driver
- `06_root_cause/results/*.csv` - playbook diagnostic results
