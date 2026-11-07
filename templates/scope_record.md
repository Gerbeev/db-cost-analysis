# Scope record - <audit ID>

Owner: ____  Started: ____  Version: ____
Keep the filled copy in an access-controlled location. Redact IDs before sharing.

## 1. Audit question (Step 0)

| Field | Value |
|---|---|
| Trigger (who, which report, which metric) | |
| Audit question | Azure Actual Cost for scope S increased from ___/day (B) to ___/day (C). Which mechanisms explain ≥ 90%? |
| Out of scope | |

## 2. Scope

| Field | Value |
|---|---|
| Agreement type (EA / MCA / MPA) | |
| Billing account / profile | |
| Subscriptions (alias list) | |
| Databricks account ID | |
| Workspaces (ID, name, region) | |
| Managed RGs (per workspace) | |
| Dependency RGs (storage, network, monitoring) | |
| Workspace tier (Standard / Premium) and change dates | |
| Contracts: DBCU plans (size, start, expiry, balance) / reservations / savings plans / credits (dates) | |

## 3. Periods and currency

| Field | Value |
|---|---|
| Analysis window | `YYYY-MM-DD` → `YYYY-MM-DD` (exclusive) |
| Baseline B | |
| Comparison C | |
| Persistence P | |
| Billing currency | |
| Databricks list price currency | |
| Rule changes vs defaults (R1-R12) with justification | none |

## 4. Sources and access

| Source | Access | Status (OK / DENIED / UNKNOWN) | Notes |
|---|---|---|---|
| Azure Cost analysis (Actual) | | | |
| Azure Exports (run IDs per month) | | | |
| Azure resource inventory | | | |
| Azure Activity Log | | | |
| `system.billing.*` | | | |
| `system.lakeflow.*` (regions) | | | |
| `system.compute.*` (regions) | | | |
| `system.query.history` (regions) | | | |
| `system.access.audit` (regions) | | | |
| IBM Cloudability / ApptioOne | | | |

## 5. Data quality (Step 1)

| Check | Result | Evidence ID |
|---|---|---|
| 1.1 One export run per month | | |
| 1.2 Export vs Cost Analysis per month (R6) | max diff ___% | |
| 1.3 Databricks usage coverage complete | | |
| 1.4 Units inventory reviewed | | |
| 1.5 Price join (R7) - failing SKUs | | |
| 1.6 System tables available per region | | |
| Limitations carried forward | | |

## 6. Size and timing (Step 2)

| Metric | Value |
|---|---|
| r(B) per day | |
| r(C) per day | |
| Δr per day / % | |
| Annualized run-rate impact (Δr × 365) | |
| Monthly absolute Δ (C - B) | |
| Persistence r(P) - r(C) | |
| Onset date (Azure Actual, R5) | |
| Onset date (Databricks modeled, 2.1) | |
| Shape (step / ramp / spike / seasonal) | |

## 7. Accounting effects (Step 3)

| Test | Result (PASS / EFFECT / N/A) | Δr per day | Evidence ID |
|---|---|---|---|
| 3.1 Calendar | | | |
| 3.2 Purchases / commitments | | | |
| 3.3 Credits / refunds | | | |
| 3.4 Scope change | | | |
| 3.5 FX | | | |
| 3.6 Rate change | | | |
| 3.7 Late corrections | | | |
| 3.8 Direction check (R8) | | | |
| **Operational Δr** | | | |

## 8. Sign-off (Step 8-9)

| Role | Name | Date | Decision |
|---|---|---|---|
| Analyst | | | |
| Independent reviewer | | | |
| Audit owner | | | |
| Finance / FinOps | | | |
