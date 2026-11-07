# 10 · Соответствие прежней структуре - прежнее рабочее место → этот набор

<!-- plain -->
> **Обзор.** Нужно, только если вы работали со старой версией набора: показывает, куда переехал каждый старый элемент. Новым пользователям можно пропустить.
<!-- /plain -->

Заменённые материалы прежнего рабочего места лежат в `../outdated/` (старые документы, каталоги исследований, офлайн-руководство HTML, SQL 00-24 и его инструменты). Позиции с пометкой *история* были записями управления проектом и **удалены**. SQL-файлы названы по шагам: `5.3_object_delta.sql` лежит в `playbook/05_databricks_decomposition/sql/`.

## 0. Промежуточный набор `databricks-cost-audit/` (2026-11-09) → текущая структура

| Промежуточный путь | Текущий путь |
|---|---|
| `AUDIT_GUIDE.md` | `playbook/README.md` + `playbook/<step>/README.md` |
| `CHECKLIST.md` | `playbook/<step>/CHECKS.md` (копируется в каждый аудит; отмечается и проверяется в интерфейсе) |
| `docs/01`, `02`, `03` | `reference/01`, `02`, `03` |
| `docs/04_driver_playbooks.md` | `playbook/06_root_cause/playbooks/01…12_*.md` |
| `docs/05_pitfalls_and_stop_rules.md` | `reference/04_pitfalls_and_stop_rules.md` |
| `docs/06_ibm_apptio_lens.md` | `reference/06_ibm_apptio_lens.md` |
| `docs/07_remediation_and_controls.md` | `reference/08_remediation_and_controls.md` |
| `docs/08_sources_and_glossary.md` | `reference/09_sources_and_glossary.md` |
| `docs/09_legacy_mapping.md` | этот файл |
| `docs/10_ibm_api_setup.md` | `reference/07_ibm_api_setup.md` |
| Правила аудита (в AUDIT_GUIDE) | `reference/05_audit_rules.md` |
| `sql/README.md` | `reference/11_sql_conventions.md` |
| `sql/S1…S6/*.sql` | `playbook/<step>/sql/*.sql` |
| `templates/` | `templates/` (+ `driver_card.md`) |
| `tools/`, `scripts/`, `tests/`, `cmd/*.cmd`, `setup.cmd` | `tools/`, `tools/tests/`, веб-интерфейс `webapp/` (запускается `run.cmd`) |
| `references/source_catalog.csv` | `reference/source_catalog.csv` |
| `data/`, `reports/`, `logs/` | `audits/<id>/…`, `audits/_logs/` |

## 1. Документы

| Старый файл | Новое место |
|---|---|
| `docs/01_scope_and_access.md` | шаг плейбука 0; reference/02 §1 |
| `docs/02_data_collection.md` | reference/02 §2-3; шаг плейбука 1 |
| `docs/03_rca_playbook.md` | шаг плейбука 4-6; плейбуки драйверов |
| `docs/04_reconciliation_and_controls.md` | Правила R6-R8; шаг плейбука 8; reference/08 |
| `docs/05_findings_template.md` | templates/findings_report.md (старый файл удалён) |
| `docs/06_references.md` | reference/09 (старый файл удалён) |
| `docs/07_ibm_apptio_integration.md` | Перенесено в docs/10_ibm_api_setup.md |
| `docs/08_march_april_change_point.md` | шаг плейбука 2; reference/03 §1-2 |
| `docs/09_cost_economics_atlas.md` | reference/01 |
| `docs/10_investigation_workflows.md` | шаги плейбука 02-08; правило R10 |
| `docs/11_azure_cost_research.md` | reference/02 §2; шаг плейбука 3-4 |
| `docs/12_databricks_system_tables.md` | reference/02 §3; sql/README.md |
| `docs/13_change_point_method.md` | reference/03 |
| `docs/14_reconciliation_and_quality.md` | reference/04; правила R6-R8 |
| `docs/15_security_and_permissions.md` | reference/02 §1, §5; правило R12 |
| `docs/16_optimization_and_controls.md` | reference/08 |
| `docs/17_research_workspace_guide.md` | *история* - удалено |
| `docs/18_evidence_record.md` | templates/evidence_register.csv (старый файл удалён) |
| `docs/20`-`25` (IBM) | reference/06; templates/ibm_discrepancy_register.csv |
| `docs/27_first_pass_route.md` | playbook/README.md → Быстрый путь |
| `docs/stage1_scope_record.md` | templates/scope_record.md (старый файл удалён) |
| `docs/evidence_register.csv` | templates/evidence_register.csv (старый файл удалён) |
| `docs/19`, `26`, `28`, `plan`, `changelog`, `requirements`, `PROJECT_IDEA`, `audit_backlog`, `build_validation`, `live_investigation_plan_deferred` | *история* - удалено |
| `research/research_checks.csv` | playbook/*/CHECKS.md (§3 ниже) |
| `research/hypotheses.csv` | templates/hypothesis_register.csv (§4 ниже) |
| `research/cost_components.csv` | reference/01 §2 (кратко); CSV сохранён как подробный каталог компонентов |
| `research/first_pass_checks.csv` | playbook/README.md → Быстрый путь |
| `research/ibm_investigations.csv` | reference/06 §4 |

## 2. SQL

| Старый | Новый | Изменение |
|---|---|---|
| `00_preflight.sql` | `1.1_usage_coverage.sql`, `1.2_usage_units_inventory.sql` | + дни с данными по месяцам |
| `01_monthly_baseline.sql` | `2.2_monthly_cost_by_sku.sql` | Те же выходные колонки (контракт анализатора); параметризован |
| `02_top_resources.sql` | `5.3_object_delta.sql` | Периоды B vs C, в сутки, класс изменения, больше типов объектов |
| `03_daily_spikes.sql` | `2.1_daily_cost_onset.sql` | + скользящее среднее, порог, флаг начала |
| `04_new_or_growing_skus.sql` | `5.1_sku_volume_rate.sql` | Любые периоды; разделение объём vs цена |
| `05_price_changes.sql` | `3.1_list_price_history.sql` | Параметризован |
| `06_unattributed_usage.sql`, `18_tags_and_ownership.sql` | `5.5_attribution_coverage.sql` | Объединены, B vs C |
| `07_job_run_diagnostics.sql` | `6.02_job_runs_monthly.sql` | + p95 длительности |
| `08_pricing_join_diagnostics.sql` | `1.3_price_join_check.sql` | + доля непрайсованного по SKU vs R7 |
| `09_inflection_daily_workloads.sql` | `5.4_object_daily.sql` | Параметризован, больше типов объектов |
| `10_product_usage_units.sql` | `1.2_usage_units_inventory.sql` | Объединён |
| `11_job_inventory.sql` | `6.04_job_definition_changes.sql` | Параметры окна |
| `12_cluster_changes.sql` | `6.06_cluster_config_history.sql` | Параметризован |
| `13_node_utilization.sql` | `6.07_node_utilization.sql` | + доля низкого CPU |
| `14_sql_query_trends.sql` | `6.11_query_trends.sql` | Параметризован |
| `15_pipeline_updates.sql` | `6.05_pipeline_updates.sql` | Параметризован |
| `16_pool_idle.sql` | `6.08_pool_idle.sql` | Параметризован |
| `17_serverless_usage.sql` | `6.13_serverless_and_features.sql` | Использует `product_features.is_serverless`, уровень продукта |
| `19_audit_events.sql` | `6.14_audit_change_events.sql` | Фокус на сервисах конфигурации |
| (черновик RCA 2026.11.08) | `6.15_dbu_per_node_hour.sql` | PB-CLASSIC C7; DBU per node-hour for H-CLS-07 / H-CLS-03 |
| `20_daily_run_counts.sql` | `6.03_job_runs_daily.sql` | Параметризован |
| `21_workspace_day_usage.sql` | `5.2_workspace_delta.sql`, `5.4_object_daily.sql` | Сравнение периодов |
| `22_sql_client_sources.sql` | `6.12_query_clients.sql` | Параметризован |
| `23_warehouse_config_history.sql` | `6.09_warehouse_config_history.sql` | Параметризован |
| `24_warehouse_events.sql` | `6.10_warehouse_events.sql` | Параметризован |
| - | `5.6_first_seen_skus.sql`, `6.01_job_cost_per_run.sql` | **Новые** |

## 3. ID проверок

| Старые ID | Новое место |
|---|---|
| CHK-001-007 | Шаг 0 |
| CHK-008, 009 | Шаг 1 (1.1), STOP-1, STOP-8 |
| CHK-010-012 | Шаг 2 |
| CHK-013-019 | Шаг 4 |
| CHK-020-022, 024 | Шаг 3 (3.5, 3.2, 3.3, 3.6) |
| CHK-023 | Шаг 7 |
| CHK-025, 026, 028 | Шаг 1 (1.3, 1.5) |
| CHK-027, 030-034 | Шаг 5 |
| CHK-029 | Шаг 3.6 |
| CHK-035 | Правила R1, R8 |
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
| CHK-074 | Шаг 6.4 |
| CHK-075 | Шаг 7.1 |
| CHK-076 | Правило R10 |
| CHK-077 | reference/06 |
| CHK-078 | Шаг 9.3, reference/08 §3 |
| CHK-079 | reference/02 §5 |
| IBM-001-026 | reference/06 IB-C1-C9 |
| IBM-027-042 | reference/06 IB-T1-T8 |
| IBM-043-049 | reference/06 §3, шаг 8.3 |

## 4. ID гипотез

| Старый | Новый | Старый | Новый |
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

## 5. Единый словарь статусов (R10)

| Старые (разные файлы) | Новый |
|---|---|
| Confirmed, VERIFIED, CONFIRMED | `CONFIRMED` |
| Likely, SUPPORTED, SUPPORTED_HYPOTHESIS | `LIKELY` |
| Unverified, HYPOTHESIS, UNTESTED | `HYPOTHESIS` |
| Rejected, DISPROVEN, REJECTED | `REJECTED` |
| UNKNOWN, UNRESOLVED | `UNKNOWN` |
