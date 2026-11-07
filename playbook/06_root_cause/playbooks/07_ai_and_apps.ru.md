# PB-AI-APPS - AI и приложения

<!-- plain -->
> **Обзор.** Используйте, когда дороже стали model serving, Vector Search, AI-функции, Databricks Apps или Lakebase. Они тарифицируются в своих единицах; ищите новый endpoint, больше трафика или более крупный индекс.
<!-- /plain -->

**Сигналы:** продукты `MODEL_SERVING`, `VECTOR_SEARCH`, `FOUNDATION_MODEL_TRAINING`, `AI_GATEWAY`, `AI_FUNCTIONS`, `AGENT_*`, `APPS`, `DATABASE` ↑.

| # | Проверка | Источник | Что смотреть |
|---|---|---|---|
| A1 | Потребление по продукту/SKU/единице | [`1.2_usage_units_inventory.sql`](../../01_data_quality/sql/1.2_usage_units_inventory.sql), `6.13` | Единицы (DBU, токены, часы) по продукту |
| A2 | Объекты endpoint/app | `5.3` (`SERVING_ENDPOINT`, `APP`) | Новые / постоянно работающие endpoint |
| A3 | Конфигурация endpoint | UI Serving: scale-to-zero, min/max concurrency, provisioned throughput, размер GPU | Изменение конфигурации ≈ начало |
| A4 | Первое появление | [`5.6_first_seen_skus.sql`](../../05_databricks_decomposition/sql/5.6_first_seen_skus.sql) | Дата старта функции |

| ID | Механизм | Подтверждает | Опровергает |
|---|---|---|---|
| H-AI-01 | Новый endpoint / provisioned throughput | Объект endpoint `NEW`; SKU впервые появился ≈ начало | Существовал |
| H-AI-02 | Scale-to-zero выключен / min concurrency ↑ | Ровное круглосуточное потребление endpoint с даты начала | Потребление следует за запросами |
| H-AI-03 | Всплеск токенов (FM API, AI Functions) | Количество токенов ↑ | Без изменений |
| H-AI-04 | Endpoint Vector Search / рост индекса | Единицы Vector Search ↑ | Без изменений |
| H-AI-05 | Apps / Lakebase работают постоянно | Часы ≈ 24/сутки | Потребление пропорционально активности |

**Варианты исправления:** scale-to-zero для непродуктивных сред; подбор provisioned throughput; останавливать простаивающие приложения; пакетный вызов AI functions.

---
Результаты сохраняйте в `06_root_cause/results/` аудита; обновляйте `hypothesis_register.csv` и `evidence_register.csv`. Назад к [шагу 06](../README.md).
