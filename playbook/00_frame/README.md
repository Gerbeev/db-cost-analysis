# Step 00 - Frame the question

<!-- plain -->
> **Overview.** The audit starts from an observation: the Azure Databricks bill has increased. This step converts the observation into a precise, approvable question: which bill, which subscriptions, which months, which currency.
>
> The step is documentation work, but it prevents the most expensive error of an audit. A change of scope after data collection invalidates every number collected so far.
>
> **Result:** a filled-in `scope_record.md` (sections 1-4 and 8) and the periods saved in the app.
>
> **Note:** Use full months only. The current month is incomplete and must stay outside the window.
<!-- /plain -->

`00` → [01 Data quality](../01_data_quality/README.md) · [Playbook index](../README.md)

**Goal:** a written, unambiguous audit question, scope and period set, approved before any data work.
**Before you start:** [reference/00 Fundamentals](../../reference/00_fundamentals.md) (cost layers, DBU, commitments).
**Inputs:** the report/alert that triggered the audit; access to the audit owner.
**Work in:** `audits/<id>/scope_record.md` (§1-§4), `audits/<id>/00_frame/notes.md`.

## Do

| # | Action | Record in |
|---|---|---|
| 0.1 | Create the audit in the UI (**Audits → New audit**, e.g. `2026-04-dbx-growth`); set window, provisional B / C / P and currency (UI action 0.1) | `audits/<id>/`, `audit.json`, §3 |
| 0.2 | Record the trigger: who saw growth, in which report, which metric (invoice, Cost Analysis, Databricks usage dashboard, IBM report) | `scope_record.md` §1 |
| 0.3 | Write the audit question on the money ledger: *"Azure Actual Cost for scope S rose from X/day (B) to Y/day (C). Which mechanisms explain ≥ 90%?"* | §1 |
| 0.4 | Fix scope: billing account/profile, subscriptions, Databricks account + workspace IDs + regions, each workspace's managed RG, dependency RGs (lake storage, VNet/NAT/Private Link, Log Analytics) | §2 |
| 0.5 | Fix the window: full months only (default 10-12), current month-to-date excluded; provisional B / C / P | §3 |
| 0.6 | Fix currency, agreement type (EA / MCA / MPA), contracts with dates (DBCU, reservations, savings plans, credits) | §2, §3 |
| 0.7 | List every data source and access status (OK / DENIED / UNKNOWN) - see [access table](../../reference/02_access_and_data_collection.md#1-minimum-read-access) | §4 |
| 0.8 | Record deviations from audit rules R1-R12 ([rules](../../reference/05_audit_rules.md)) or "none" | §3 |
| 0.9 | Get audit-owner approval; write name + date | §8 |

## Checks

Tick in the UI (step 00 → **Checks**); status refreshes automatically. Master list: [CHECKS.md](CHECKS.md).

## Gate G0

Scope, periods, currency and ledger are written and approved. **Do not request exports before G0** - wrong scope invalidates everything downstream.
