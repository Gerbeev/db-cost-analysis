# Step 08 - Validation · checks

Mark: `[x]` done · `[-]` not applicable ` | reason` · `[!]` done with limitation ` | limitation`. Gate (`G…`) must be `[x]`.
Tick in the UI: audit → step → **Checks**. Status (checks, outputs, automatic data checks) refreshes after every change.

## Checks

- [ ] C8.1 Every evidence row reproduced; mismatches resolved (reproduction_log.md)
- [ ] C8.2 R9 re-checked for each CONFIRMED; downgrades applied
- [ ] C8.3 Every CONFIRMED hypothesis has existing evidence IDs - auto
- [ ] C8.4 Alternative views cross-checked (Amortized, usage dashboard); differences explained
- [ ] C8.5 IBM Cloudability / ApptioOne cross-check with discrepancy register - or `[-] | not licensed`
- [ ] C8.6 Persistence in P checked per driver
- [ ] C8.7 Independent peer review done (scope §8)
- [ ] G8 Numbers reproducible; reviewer sign-off

## Required outputs

- `08_validation/results/reproduction_log*` - rerun results per evidence row
- `08_validation/results/cross_check*` - alternative-view comparison
