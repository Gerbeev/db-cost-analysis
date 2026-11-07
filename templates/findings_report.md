# Azure Databricks cost increase - audit findings

**Audit ID:** ____  **Scope:** ____  **Ledger:** Azure Actual Cost, ____ (currency)
**Periods:** B ____ · C ____ · P ____  **Report date:** ____  **Status:** DRAFT / REVIEWED / FINAL

## 1. Executive summary

- Azure Actual cost per day rose from **___** (B) to **___** (C): **+___/day (+__%)**, annualized **+___/year**. Onset: **____** (shape: step / ramp / spike).
- Persistence in P: ____.
- Explained: **__%** of the increase. Unexplained: **__%**.
- Drivers (one line each, largest first):
  1. `CONFIRMED` - <object / mechanism / date> - **+___/day** (__%)
  2. `LIKELY` - … - **+___/day** (__%)
- Accounting effects (not consumption): ____ (+___/day).
- Key recommendation(s) and expected savings range: ____.

## 2. Size and timing

| Period | Days | Total | Per day |
|---|---|---|---|
| B | | | |
| C | | | |
| P | | | |

Charts to attach: monthly per-day series (full window); daily series around onset with threshold (R5).

## 3. Delta bridge

| Line | Category | Description | Δ/day | Share | Status |
|---|---|---|---|---|---|
| TOTAL | | | | 100% | |
| | ACCOUNTING | | | | |
| | ROOT_CAUSE | | | | |
| | SHARED_UNALLOCATED | | | | |
| | UNEXPLAINED | | | | |

Source: `delta_bridge.csv`.

## 4. Findings

Repeat per driver.

### F-01 · <title>

| Field | Content |
|---|---|
| Status | CONFIRMED / LIKELY |
| Bucket / playbook | |
| Object(s) | workspace / type / ID / name |
| Owner | |
| Mechanism | What changed, technically |
| Change event | Timestamp, actor/system, source (SCD2 / audit / release) |
| Δ/day (Azure Actual) | ___ (conversion ratio if measured in list price: ___) |
| Quantification | e.g. runs/day 12 → 48, cost/run flat → frequency effect 92% |
| R9 criteria | (a) ☐ (b) ☐ (c) ☐ (d) ☐ |
| Alternatives tested | H-… rejected because … |
| Evidence IDs | EVD-… |
| Persistence in P | |
| Recommendation | Change, savings range, risk, rollback, validation metric |

## 5. Rejected hypotheses

| Hypothesis | Why rejected | Evidence |
|---|---|---|

## 6. Unexplained residual and open items

| Item | Δ/day | Missing evidence | Owner | Next action |
|---|---|---|---|---|

## 7. Limitations

Data coverage, unavailable sources, retention, price-join exclusions (R7), shared-cost assumptions, currency/FX notes.

## 8. Remediation backlog and controls

| # | Driver | Change | Savings range /day | Risk | Owner | Validation metric | Due |
|---|---|---|---|---|---|---|---|

Controls proposed: budgets/alerts, policies, weekly top-mover review, tag coverage target (reference/08 §3).

## 9. Sign-off

| Role | Name | Date |
|---|---|---|
| Analyst | | |
| Reviewer | | |
| Audit owner | | |
