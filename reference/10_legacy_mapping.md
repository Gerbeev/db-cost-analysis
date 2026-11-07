# 10 · Legacy mapping - previous workbench → this kit

<!-- plain -->
> **Overview.** Only useful if you used the older version of this toolkit: it shows where each old item went. New users can skip it.
<!-- /plain -->

Superseded material of the previous workbench is in `../outdated/` (old docs, research catalogs, offline HTML guide, SQL 00-24 and its tooling). Items marked *history* were project-management records and have been **deleted**. SQL files are named by step: `5.3_object_delta.sql` lives in `playbook/05_databricks_decomposition/sql/`.

## 0. Interim kit `databricks-cost-audit/` (2026-11-09) → current layout

| Interim path | Current path |
|---|---|
| `AUDIT_GUIDE.md` | `playbook/README.md` + `playbook/<step>/README.md` |
| `CHECKLIST.md` | `playbook/<step>/CHECKS.md` (copied into each audit; ticked and verified in the interface) |
| `docs/01`, `02`, `03` | `reference/01`, `02`, `03` |
| `docs/04_driver_playbooks.md` | `playbook/06_root_cause/playbooks/01…12_*.md` |
| `docs/05_pitfalls_and_stop_rules.md` | `reference/04_pitfalls_and_stop_rules.md` |
| `docs/06_ibm_apptio_lens.md` | `reference/06_ibm_apptio_lens.md` |
| `docs/07_remediation_and_controls.md` | `reference/08_remediation_and_controls.md` |
| `docs/08_sources_and_glossary.md` | `reference/09_sources_and_glossary.md` |
| `docs/09_legacy_mapping.md` | this file |
| `docs/10_ibm_api_setup.md` | `reference/07_ibm_api_setup.md` |
| Audit rules (in AUDIT_GUIDE) | `reference/05_audit_rules.md` |
| `sql/README.md` | `reference/11_sql_conventions.md` |
| `sql/S1…S6/*.sql` | `playbook/<step>/sql/*.sql` |
| `templates/` | `templates/` (+ `driver_card.md`) |
| `tools/`, `scripts/`, `tests/`, `cmd/*.cmd`, `setup.cmd` | `tools/`, `tools/tests/`, web interface `webapp/` (started by `run.cmd`) |
| `references/source_catalog.csv` | `reference/source_catalog.csv` |
| `data/`, `reports/`, `logs/` | `audits/<id>/…`, `audits/_logs/` |

## 1. Documents

| Old file | New location |
|---|---|
| `docs/01_scope_and_access.md` | playbook step 0; reference/02 §1 |
| `docs/02_data_collection.md` | reference/02 §2-3; playbook step 1 |
| `docs/03_rca_playbook.md` | playbook step 4-6; driver playbooks |
| `docs/04_reconciliation_and_controls.md` | Rules R6-R8; playbook step 8; reference/08 |
| `docs/05_findings_template.md` | templates/findings_report.md (old file deleted) |
| `docs/06_references.md` | reference/09 (old file deleted) |
| `docs/07_ibm_apptio_integration.md` | Moved to docs/10_ibm_api_setup.md |
| `docs/08_march_april_change_point.md` | playbook step 2; reference/03 §1-2 |
| `docs/09_cost_economics_atlas.md` | reference/01 |
| `docs/10_investigation_workflows.md` | playbook steps 02-08; rule R10 |
| `docs/11_azure_cost_research.md` | reference/02 §2; playbook step 3-4 |
| `docs/12_databricks_system_tables.md` | reference/02 §3; sql/README.md |
| `docs/13_change_point_method.md` | reference/03 |
| `docs/14_reconciliation_and_quality.md` | reference/04; rules R6-R8 |
| `docs/15_security_and_permissions.md` | reference/02 §1, §5; rule R12 |
| `docs/16_optimization_and_controls.md` | reference/08 |
| `docs/17_research_workspace_guide.md` | *history* - deleted |
| `docs/18_evidence_record.md` | templates/evidence_register.csv (old file deleted) |
| `docs/20`-`25` (IBM) | reference/06; templates/ibm_discrepancy_register.csv |
| `docs/27_first_pass_route.md` | playbook/README.md → Fast path |
| `docs/stage1_scope_record.md` | templates/scope_record.md (old file deleted) |
| `docs/evidence_register.csv` | templates/evidence_register.csv (old file deleted) |
| `docs/19`, `26`, `28`, `plan`, `changelog`, `requirements`, `PROJECT_IDEA`, `audit_backlog`, `build_validation`, `live_investigation_plan_deferred` | *history* - deleted |
| `research/research_checks.csv` | playbook/*/CHECKS.md (§3 below) |
| `research/hypotheses.csv` | templates/hypothesis_register.csv (§4 below) |
| `research/cost_components.csv` | reference/01 §2 (summary); CSV kept as detailed component catalog |
| `research/first_pass_checks.csv` | playbook/README.md → Fast path |
| `research/ibm_investigations.csv` | reference/06 §4 |

## 2. SQL

| Old | New | Change |
|---|---|---|
| `00_preflight.sql` | `1.1_usage_coverage.sql`, `1.2_usage_units_inventory.sql` | + days-with-data per month |
| `01_monthly_baseline.sql` | `2.2_monthly_cost_by_sku.sql` | Same output columns (analyzer contract); parameterized |
| `02_top_resources.sql` | `5.3_object_delta.sql` | Period B vs C, per-day, change class, more object types |
| `03_daily_spikes.sql` | `2.1_daily_cost_onset.sql` | + rolling mean, threshold, onset flag |
| `04_new_or_growing_skus.sql` | `5.1_sku_volume_rate.sql` | Any periods; volume vs rate split |
| `05_price_changes.sql` | `3.1_list_price_history.sql` | Parameterized |
| `06_unattributed_usage.sql`, `18_tags_and_ownership.sql` | `5.5_attribution_coverage.sql` | Merged, B vs C |
| `07_job_run_diagnostics.sql` | `6.02_job_runs_monthly.sql` | + p95 duration |
| `08_pricing_join_diagnostics.sql` | `1.3_price_join_check.sql` | + per-SKU unpriced share vs R7 |
| `09_inflection_daily_workloads.sql` | `5.4_object_daily.sql` | Parameterized, more object types |
| `10_product_usage_units.sql` | `1.2_usage_units_inventory.sql` | Merged |
| `11_job_inventory.sql` | `6.04_job_definition_changes.sql` | Window parameters |
| `12_cluster_changes.sql` | `6.06_cluster_config_history.sql` | Parameterized |
| `13_node_utilization.sql` | `6.07_node_utilization.sql` | + low-CPU share |
| `14_sql_query_trends.sql` | `6.11_query_trends.sql` | Parameterized |
| `15_pipeline_updates.sql` | `6.05_pipeline_updates.sql` | Parameterized |
| `16_pool_idle.sql` | `6.08_pool_idle.sql` | Parameterized |
| `17_serverless_usage.sql` | `6.13_serverless_and_features.sql` | Uses `product_features.is_serverless`, product-level |
| `19_audit_events.sql` | `6.14_audit_change_events.sql` | Focus on configuration services |
| (draft RCA 2026.11.08) | `6.15_dbu_per_node_hour.sql` | PB-CLASSIC C7; DBU per node-hour for H-CLS-07 / H-CLS-03 |
| `20_daily_run_counts.sql` | `6.03_job_runs_daily.sql` | Parameterized |
| `21_workspace_day_usage.sql` | `5.2_workspace_delta.sql`, `5.4_object_daily.sql` | Period comparison |
| `22_sql_client_sources.sql` | `6.12_query_clients.sql` | Parameterized |
| `23_warehouse_config_history.sql` | `6.09_warehouse_config_history.sql` | Parameterized |
| `24_warehouse_events.sql` | `6.10_warehouse_events.sql` | Parameterized |
| - | `5.6_first_seen_skus.sql`, `6.01_job_cost_per_run.sql` | **New** |

## 3. Check IDs

| Old IDs | New location |
|---|---|
| CHK-001-007 | Step 0 |
| CHK-008, 009 | Step 1 (1.1), STOP-1, STOP-8 |
| CHK-010-012 | Step 2 |
| CHK-013-019 | Step 4 |
| CHK-020-022, 024 | Step 3 (3.5, 3.2, 3.3, 3.6) |
| CHK-023 | Step 7 |
| CHK-025, 026, 028 | Step 1 (1.3, 1.5) |
| CHK-027, 030-034 | Step 5 |
| CHK-029 | Step 3.6 |
| CHK-035 | Rule R1, R8 |
| CHK-036-042, 045 | PB-JOBS |
| CHK-043, 044 | PB-PIPELINES |
| CHK-046-051, 053 | PB-CLASSIC |
| CHK-052 | PB-POOLS |
| CHK-054-059 | PB-SQL |
| CHK-060-062 | PB-STORAGE |
| CHK-063-066 | PB-NETWORK |
| CHK-067 | PB-MONITOR |
| CHK-068-070, 072 | PB-AI-APPS |
| CHK-071, 073 | PB-FEATURES |
| CHK-074 | Step 6.4 |
| CHK-075 | Step 7.1 |
| CHK-076 | Rule R10 |
| CHK-077 | reference/06 |
| CHK-078 | Step 9.3, reference/08 §3 |
| CHK-079 | reference/02 §5 |
| IBM-001-026 | reference/06 IB-C1-C9 |
| IBM-027-042 | reference/06 IB-T1-T8 |
| IBM-043-049 | reference/06 §3, Step 8.3 |

## 4. Hypothesis IDs

| Old | New | Old | New |
|---|---|---|---|
| HYP-001 | H-JOB-01 | HYP-028 | H-RAT-09 |
| HYP-002 | H-JOB-02 | HYP-029 | H-STO-01 |
| HYP-003 | H-JOB-03 | HYP-030 | H-STO-03 |
| HYP-004 | H-JOB-04 | HYP-031 | H-STO-02 |
| HYP-005 | H-PIP-02 | HYP-032 | H-NET-01 |
| HYP-006 | H-PIP-01 | HYP-033 | H-NET-02, H-NET-03 |
| HYP-007 | H-JOB-03 | HYP-034 | H-MON-01 |
| HYP-008 | H-SQL-03 | HYP-035 | H-FEA-01 |
| HYP-009 | H-CLS-04 | HYP-036 | H-FEA-04 |
| HYP-010 | H-AI-01 | HYP-037 | H-AI-04 |
| HYP-011 | H-CLS-02 | HYP-038 | H-AI-03 |
| HYP-012 | H-CLS-03 | HYP-039 | H-AI-01, H-AI-05 |
| HYP-013 | H-CLS-01 | HYP-040 | H-FEA-03 |
| HYP-014 | H-POL-01 | HYP-041 | H-IBM-01 |
| HYP-015 | H-SQL-01 | HYP-042 | H-IBM-02 |
| HYP-016 | H-SRV-01, H-SRV-02 | HYP-043 | H-IBM-03 |
| HYP-017 | H-CLS-02 | HYP-044 | H-IBM-04 |
| HYP-018 | H-CLS-06 | HYP-045 | H-IBM-05 |
| HYP-019 | H-RAT-05 | HYP-046 | H-IBM-06 |
| HYP-020 | H-RAT-04 | HYP-047 | H-IBM-07 |
| HYP-021 | H-RAT-06 | HYP-048 | H-IBM-03 |
| HYP-022 | H-RAT-01 | HYP-049 | H-IBM-08 |
| HYP-023 | H-RAT-02 | HYP-050 | H-IBM-09 |
| HYP-024 | H-RAT-03 | HYP-051 | H-IBM-10 |
| HYP-025 | H-RAT-07 | HYP-052 | H-IBM-11 |
| HYP-026 | H-RAT-08 | HYP-053 | H-IBM-12 |
| HYP-027 | H-RAT-07 | HYP-054 | H-IBM-13 |

## 5. Status vocabularies unified (R10)

| Old (various files) | New |
|---|---|
| Confirmed, VERIFIED, CONFIRMED | `CONFIRMED` |
| Likely, SUPPORTED, SUPPORTED_HYPOTHESIS | `LIKELY` |
| Unverified, HYPOTHESIS, UNTESTED | `HYPOTHESIS` |
| Rejected, DISPROVEN, REJECTED | `REJECTED` |
| UNKNOWN, UNRESOLVED | `UNKNOWN` |
