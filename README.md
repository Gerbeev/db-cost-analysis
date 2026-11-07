# Azure Databricks Cost Growth Audit

Step-by-step, read-only method to **confirm, size and root-cause an increase in Azure Databricks-related spend**, with a workspace that stores every intermediate result and checks each step.

## Purpose and audience

The toolkit supports an audit of an increase in Azure Databricks cost: from the observed growth to specific causes, each with a date, a measured effect and an owner. It is designed for practitioners performing such an audit for the **first time**: no knowledge of Databricks internals is assumed, and no commands are typed. Terms are defined in the [glossary](reference/14_glossary.md) and linked automatically.

The toolkit only **reads** data. It does not change anything in Azure or Databricks.

## Audit workflow

1. **Define the question.** Which months, which part of Azure, which currency, who asked.
2. **Download the data.** One big cost export from the Azure portal and one small report to cross-check it. (Optionally, let the app run read-only SQL in Databricks.)
3. **Prove the growth is real** and measure it per day.
4. **Remove accounting causes.** Expired discounts, new purchases, price changes and currency movements raise a bill without additional consumption.
5. **Locate the remainder**, first in Azure (services, resources), then in Databricks (jobs, clusters, warehouses).
6. **Find the cause** of each big item: what changed, when, how much it explains.
7. **Reconcile the numbers**, name an owner for each cause and show what remains unexplained.
8. **Independent verification**, then write the report with fixes and alerts.

The application keeps one folder per audit, stores every result and reports at each step whether the gate condition is met.

## The ten steps at a glance

| Step | Question | Details |
|---|---|---|
| 00 | What exactly are we checking? | [Frame the question](playbook/00_frame/README.md) |
| 01 | Can we trust the data? | [Data quality](playbook/01_data_quality/README.md) |
| 02 | Did the bill really grow, by how much, since when? | [Confirm and size](playbook/02_confirm_and_size/README.md) |
| 03 | How much is just accounting? | [Accounting effects](playbook/03_accounting_effects/README.md) |
| 04 | Which Azure services and resources cost more? | [Azure decomposition](playbook/04_azure_decomposition/README.md) |
| 05 | Which Databricks objects used more? | [Databricks decomposition](playbook/05_databricks_decomposition/README.md) |
| 06 | What exactly changed, and when? | [Root cause](playbook/06_root_cause/README.md) |
| 07 | Who owns it, what is unexplained? | [Attribution and residual](playbook/07_attribution_and_residual/README.md) |
| 08 | Can others repeat our numbers? | [Validation](playbook/08_validation/README.md) |
| 09 | What do we report, fix and monitor? | [Report and controls](playbook/09_report_and_controls/README.md) |

## Prerequisites

- A computer with Python 3.10 or newer (the start script installs the rest).
- **Read access** to Azure Cost Management for the subscriptions in scope. Request it early: access is usually the longest lead-time item. The exact list is in [reference/02](reference/02_access_and_data_collection.md).
- Optional: read access to Databricks system tables and a SQL warehouse, so the app can run the SQL for you; the Azure CLI for the workspace map; IBM keys if you use IBM tools.
- Effort: about one to three working days for a first audit, depending on data availability.

## Start here

The whole playbook runs in a local web interface - no commands to type.

```text
1. Double-click run.cmd            (Windows; macOS / Linux: ./run.sh)
                                   first start creates .venv and installs requirements.txt
2. The browser opens http://127.0.0.1:8765
3. Audits → New audit              creates audits\<id>\ with step folders, checks and registers
4. Walk steps 00 → 09              every action is a button: upload a portal export, run a tool,
                                   run / copy Databricks SQL, edit a register or document, tick checks
```

Interface: opens on **Documentation**; **Audits** starts with workspace management (create, demo, delete) then your audit list. English / Russian and light / dark theme (top right). **Settings** holds the optional Databricks SQL connection and the tool self-test.

New to Databricks cost? Read [reference/00_fundamentals.md](reference/00_fundamentals.md) first (≈15 min): what the bill consists of, DBU, formulas, commitments, typical growth causes.

## What the interface does per step

| Action type | What happens |
|---|---|
| Upload | Portal exports (Cost Management, Cost Analysis) are saved under the step's `exports/` with the conventional name; an evidence row is added |
| Tool | `tools/*.py` run with the audit's export and periods pre-filled; output in `results/`, evidence row added |
| Calculator | R6 reconciliation, size + bridge TOTAL, R8 direction check, operational Δ, UNX residual, driver card, reproduction log, bridge table |
| Databricks SQL | Query shown with parameters from the audit periods; **Run in Databricks** (Statement Execution API, read-only) or copy + upload the CSV |
| Register / document | Table editor for the CSV registers; markdown editor with preview for `scope_record.md`, notes, driver cards, report |
| Checks | Tick `[x]` / `[-] reason` / `[!] limitation`; step status, required outputs and automatic data checks refresh immediately (`STATUS.md` is regenerated) |

## Structure

```text
README.md                    ← you are here
run.cmd / run.sh             ← start the web interface (creates .venv on first run)
requirements.txt             ← fastapi, uvicorn, python-multipart, markdown
webapp/                      ← the interface: FastAPI app (main.py), playbook definition EN/RU (steps.py), static UI
playbook/                    ← THE PROCEDURE (rendered in the interface)
  README.md                    step index, rules, living registers, fast path
  00_frame/ … 09_report_and_controls/
    README.md                  what to do and where results are saved
    CHECKS.md                  checks for the step (copied into each audit)
    sql/                       Databricks SQL used in the step
  06_root_cause/playbooks/     12 driver playbooks (jobs, pipelines, clusters, pools, SQL, serverless, …)
audits/                      ← YOUR WORK (git-ignored); one folder per audit
templates/                   ← master templates copied into each new audit
reference/                   ← background: fundamentals, cost model, data collection, formulas, rules, pitfalls, IBM, sources
tools/                       ← Python tools used by the interface, and their tests
examples/                    ← synthetic demo data (Audits → Open demo)
```

## Audit workspace (created by Audits → New audit)

```text
audits/<id>/
  audit.json                 periods, currency, primary export (edited in the interface)
  STATUS.md                  regenerated by the interface after every change
  scope_record.md            living: question, scope, periods, data quality, size, accounting, sign-off
  evidence_register.csv      living: one row per saved result (EVD-<step>-<nnn>)
  delta_bridge.csv           living: TOTAL Δ = accounting + root causes + shared + out-of-scope + unexplained
  hypothesis_register.csv    living: 80 hypotheses with confirm / reject tests and status
  00_frame/                  CHECKS.md, notes.md
  01_data_quality/ … 08_validation/
    CHECKS.md  notes.md
    exports/                 raw downloads (Azure portal, IBM)
    results/                 SQL and tool outputs
  06_root_cause/driver_<nn>_<name>.md      one per driver (action 6.1)
  08_validation/ibm_discrepancy_register.csv
  09_report_and_controls/findings_report.md
```

File naming for results: `<sql-or-tool-id>__<details>__<YYYYMMDD>.csv`, e.g. `5.3_object_delta__B2026-02_C2026-04__20261109.csv`.

## Principles

- **One money truth:** the real Azure bill (Actual Cost) at a fixed scope counts as money. The Databricks list-price model, Amortized cost and IBM reports are helper views - never added to it.
- **Compare per day,** because months have 28 to 31 days.
- **A cause, not a coincidence:** a finding is `CONFIRMED` only if the growth shows in the bill, the change is dated, the numbers match and another explanation was disproved (R9).
- **Explain at least 90%,** and show the rest openly as `UNEXPLAINED`.
- **Read-only:** nothing here changes your tenant. Running SQL uses warehouse compute - get approval first.

## Requirements

- Python 3.10+ (Windows: `py -3` or `python` on PATH). Internet access to PyPI on first start (or a pre-built `.venv`).
- Optional: Azure CLI (`az login`) for the workspace inventory (4.2) and for Databricks sign-in without a token.
- Optional: Databricks SQL warehouse ID + workspace URL to run the SQL from the interface.
- The server binds to `127.0.0.1` only. Port: `set AUDIT_UI_PORT=8800` before `run.cmd`.

Development: `python -m unittest discover -s tools/tests` runs tool and interface tests (also in **Settings → Self-test**).
