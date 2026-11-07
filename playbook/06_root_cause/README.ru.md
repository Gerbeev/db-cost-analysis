# Шаг 06 - Первопричина каждого существенного драйвера

[05 Декомпозиция Databricks](../05_databricks_decomposition/README.md) ← `06` → [07 Атрибуция и остаток](../07_attribution_and_residual/README.md) · [Оглавление плейбука](../README.md)

<!-- plain -->
> **Обзор.** Этот шаг устанавливает причинность. Для каждого кандидата из шага 05 определяется, что изменилось (новое расписание, более крупный кластер, warehouse, переставший останавливаться, включённая функция), когда это произошло и какую часть роста объясняет изменение.
>
> Для каждого типа кандидатов есть готовый плейбук с SQL-запросами. Результаты фиксируются на одностраничной карточке драйвера. Причина считается подтверждённой, только если выполнены четыре доказательства (правило R9); совпадения по времени недостаточно.
>
> **Результат:** карточка на каждый крупный драйвер, статусы в реестре гипотез, строки ROOT_CAUSE в мосте.
>
> **Важно:** Для каждого драйвера опровергните хотя бы одно альтернативное объяснение. Это отличает доказательство от предположения.
<!-- /plain -->

**Цель:** для каждого существенного драйвера - датированный технический механизм с количественным эффектом, доказанный по правилу R9.
**Входные данные:** G5 пройдена; строки корзин (шаг 04) и строки DRIVER_CANDIDATE (шаг 05). **Где работать:** `audits/<id>/06_root_cause/`.

## 1. Направьте каждый драйвер в его плейбук

| Сигнал из шагов 04-05 | Плейбук |
|---|---|
| Продукт `JOBS` ↑; объекты job `NEW` / `GROWN` | [01 Jobs](playbooks/01_jobs.md) |
| `DLT` / объекты pipeline ↑ | [02 Pipelines](playbooks/02_pipelines.md) |
| `ALL_PURPOSE` / `INTERACTIVE` ↑, или классические VM ↑ вместе с DBU ↑ | [03 Classic compute](playbooks/03_classic_compute.md) |
| Классические VM ↑ при неизменных DBU | [04 Instance pools](playbooks/04_instance_pools.md) |
| Продукт `SQL` ↑; объекты warehouse ↑ | [05 SQL warehouses](playbooks/05_sql_warehouses.md) |
| Serverless SKU ↑ (`is_serverless`) | [06 Serverless](playbooks/06_serverless.md) |
| `MODEL_SERVING`, `VECTOR_SEARCH`, `AI_*`, `FOUNDATION_MODEL_*`, `APPS`, `DATABASE` ↑ | [07 AI and apps](playbooks/07_ai_and_apps.md) |
| `PREDICTIVE_OPTIMIZATION`, `*_MONITORING`, `FINE_GRAINED_ACCESS_CONTROL`, `NETWORKING`, `DEFAULT_STORAGE` ↑ | [08 Platform features](playbooks/08_platform_features.md) |
| Корзина `STORAGE` ↑ | [09 Storage](playbooks/09_storage.md) |
| Корзина `NETWORK` ↑ | [10 Network](playbooks/10_network.md) |
| Корзина `MONITORING` ↑ | [11 Monitoring](playbooks/11_monitoring.md) |
| Тарифные эффекты / покупки / кредиты (шаг 03) | [12 Rate and accounting](playbooks/12_rate_and_accounting.md) |

## 2. Порядок работы с драйвером

| # | Действие | Куда сохранить (`audits/<id>/06_root_cause/…`) |
|---|---|---|
| 6.1 | Действие 6.1 *Новая карточка драйвера* создаёт `driver_<nn>_<short-name>.md` из шаблона | `driver_01_nightly_etl.md` |
| 6.2 | Открыть плейбук; перечислить гипотезы-кандидаты (ID `H-…`) | карточка §Hypotheses |
| 6.3 | Выполнить диагностику плейбука (действие 6.2 содержит все SQL из [`sql/`](sql/); прочие доказательства - загрузка 6.3) | `results/6.xx_<name>__….csv` |
| 6.4 | Количественно: частота × стоимость запуска (`6.01_job_cost_per_run.sql`) или объём × цена (`5.1`) | карточка §Quantification |
| 6.5 | Найти событие изменения: история SCD2 (`6.04`, `6.06`, `6.09`), аудит (`6.14`), релиз / Git / Activity Log / тикеты | карточка §Change event |
| 6.6 | Опровергнуть ≥ 1 альтернативную гипотезу | карточка §Alternatives |
| 6.7 | Задать статус по R9: `CONFIRMED` (a+b+c+d) / `LIKELY` / `REJECTED` / `UNKNOWN` | `hypothesis_register.csv` |
| 6.8 | Добавить строку `ROOT_CAUSE` в мост: Δ/сутки в валюте Azure Actual, статус, hypothesis_id, evidence_ids | `delta_bridge.csv` |

Кратко R9: (a) Δ видна в Azure Actual · (b) время изменения в пределах ±2 дней от начала драйвера · (c) механизм объясняет ≥ 70% Δ драйвера · (d) опровергнута ≥ 1 альтернатива. Одна лишь корреляция по времени никогда не даёт `CONFIRMED`.

Драйвер измерен по прайсу → пересчёт: `коэффициент = Δ Azure DBX_PLATFORM / модельная Δ DBX`; запишите коэффициент в карточку ([reference/03 §7](../../reference/03_analysis_method.md)).

## Автоматические проверки

- У каждой строки моста `ROOT_CAUSE` со значением статус ≠ `HYPOTHESIS`; ни одна гипотеза, на которую она ссылается, не имеет в реестре статус `HYPOTHESIS`.

## Контрольная точка G6

У каждого существенного драйвера есть карточка и статус, отличный от `HYPOTHESIS`.
