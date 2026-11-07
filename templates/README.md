# Templates

Master copies. Creating an audit in the interface copies them into the audit workspace - edit the copies there (registers and documents open in the interface), never these.

| Template | Copied to | Used in steps |
|---|---|---|
| `scope_record.md` | `audits/<id>/scope_record.md` | 00, 01, 02, 03, 08 |
| `evidence_register.csv` | `audits/<id>/evidence_register.csv` | all |
| `delta_bridge.csv` | `audits/<id>/delta_bridge.csv` | 02-07, 09 |
| `hypothesis_register.csv` | `audits/<id>/hypothesis_register.csv` | 03, 05, 06, 08 |
| `driver_card.md` | `audits/<id>/06_root_cause/_driver_card_TEMPLATE.md` | 06 (one copy per driver) |
| `ibm_discrepancy_register.csv` | `audits/<id>/08_validation/ibm_discrepancy_register.csv` | 08 (if IBM licensed) |
| `findings_report.md` | `audits/<id>/09_report_and_controls/findings_report.md` | 09 |

## delta_bridge.csv categories

| category | Meaning | In identity |
|---|---|---|
| `TOTAL` | Azure Actual Δ/day for the scope (step 02) | = sum of the lines below |
| `ACCOUNTING` | Calendar, purchases, commitments, credits, rate, FX, scope, corrections (step 03) | yes |
| `ROOT_CAUSE` | One line per driver with status (step 06) | yes |
| `SHARED_UNALLOCATED` | Shared resources without allocation key (step 07) | yes |
| `OUT_OF_SCOPE` | Non-Databricks services (step 07) | yes |
| `UNEXPLAINED` | Residual `UNX` (step 07) | yes |
| `BUCKET` | Bucket subtotal from step 04 | no (informational) |
| `DRIVER_CANDIDATE` | Top object/SKU from step 05, list price | no (informational) |
