# PB-PIPELINES - конвейеры (DLT / Lakeflow)

<!-- plain -->
> **Обзор.** Используйте, когда дороже стал **конвейер данных** (Lakeflow / DLT): больше обновлений, смена редакции, кластер побольше или переход на непрерывный режим.
<!-- /plain -->

**Сигналы:** SKU продукта `DLT` ↑; `5.3` объекты типа `PIPELINE` ↑; serverless SKU конвейеров ↑.

**Диагностика**

| # | Проверка | Источник | Что смотреть |
|---|---|---|---|
| L1 | Обновления/месяц, длительность, триггер, результаты, full refresh | [`6.05_pipeline_updates.sql`](../sql/6.05_pipeline_updates.sql) | Число обновлений ↑, full refresh ↑, `last_trigger` |
| L2 | Стоимость конвейеров B vs C | [`5.3_object_delta.sql`](../../05_databricks_decomposition/sql/5.3_object_delta.sql) (object_type `PIPELINE`) | Какие конвейеры |
| L3 | Суточная стоимость конвейера | [`5.4_object_daily.sql`](../../05_databricks_decomposition/sql/5.4_object_daily.sql) | Дата начала |
| L4 | Настройки конвейера: continuous vs triggered, редакция, кластер | UI конвейера → Settings / JSON; аудит `6.14` (сервис `deltaPipelines`) | Время смены режима/редакции |

**Механизмы**

| ID | Механизм | Подтверждает | Опровергает |
|---|---|---|---|
| H-PIP-01 | Включён режим continuous | Длительность обновлений ≈ отрезки по 24 ч; DBU ровно высокие каждый день с даты начала | Триггерные обновления с паузами |
| H-PIP-02 | Full refresh / backfill / сброс checkpoint | `updates_with_full_refresh_selection` > 0 около даты начала; разовый всплеск | Нет выборов full refresh |
| H-PIP-03 | Более частые триггеры | Число обновлений ↑ при стабильной длительности | Число не изменилось |
| H-PIP-04 | Смена редакции (Core → Pro → Advanced) | Меняется имя SKU для того же конвейера | Тот же SKU |
| H-PIP-05 | Сбои / повторы | `failed_updates` ↑ | Стабильно |
| H-PIP-06 | Новые конвейеры / materialized views / streaming tables | Объекты конвейеров `NEW`; первое появление ≈ начало | Были в B |

**Варианты исправления:** triggered вместо continuous, где позволяет задержка; избегать full refresh по расписанию; подбор размера или enhanced autoscaling; редакция по реальной потребности конвейера.

---
Результаты сохраняйте в `06_root_cause/results/` аудита; обновляйте `hypothesis_register.csv` и `evidence_register.csv`. Назад к [шагу 06](../README.md).
