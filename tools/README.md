# Tools

Python 3.10+, standard library only. Read-only towards data sources. **They are run by the web interface** (`run.cmd` → step actions); this page documents what each one does.

| Tool | Interface actions | Purpose |
|---|---|---|
| `new_audit.py` | Audits → New audit | Create `audits/<id>/` from `playbook/*/CHECKS.md` and `templates/` |
| `check_audit.py` | every change (step status, `STATUS.md`) | Evaluate checks, required outputs and data checks per step |
| `period_delta.py` | 1.4, 2.1 (monthly series); 3.5, 3.6 (Δ/day by grouping), 4.1 (five groupings); calculators 2.7, 3.9 | Rank Δ/day between B and C by any columns; monthly series; R3 materiality, R4 coverage |
| `onset_detect.py` | 2.3 | Rule R5 onset / spike detection on a daily series (sums rows per day) |
| `analyze_costs.py` | 2.9 | Monthly reports from Azure Actual CSV + SQL 2.2 export (separate ledgers) |
| `azure_workspace_inventory.ps1` | 4.2 (Python port in `webapp/runner.py`, same columns) | Workspace ↔ managed RG inventory via Azure CLI (read-only) |
| `apptio_api.py`, `normalize_apptioone.py`, `analyze_apptio.py` | 8.4-8.8 | Optional IBM Cloudability / ApptioOne export and analysis ([reference/07](../reference/07_ibm_api_setup.md)) |
| `tests/` | Settings → Self-test | Unit tests on synthetic data (tools and interface) |

`period_delta` and `onset_detect` auto-detect common Azure columns (`Date`/`UsageDate`, `CostInBillingCurrency`/`Cost`, `BillingCurrencyCode`/`BillingCurrency`/`Currency`), accept `YYYY-MM-DD` and `MM/DD/YYYY`, and refuse mixed currencies (use the *currency* field of the action). Period ends are exclusive.

Each run from the interface records its parameters in `evidence_register.csv` (`parameters` column, JSON), which is what the reproduction calculator (8.1) re-runs.

Logs of the IBM tools: `audits/_logs/`.
