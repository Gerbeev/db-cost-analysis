# PB-MONITOR - мониторинг

<!-- plain -->
> **Обзор.** Используйте, когда выросла категория **MONITORING** - обычно Log Analytics после того, как кто-то включил более подробные диагностические логи.
<!-- /plain -->

**Сигналы:** счётчики Log Analytics / Azure Monitor ↑.

| ID | Механизм | Подтверждает | Опровергает |
|---|---|---|---|
| H-MON-01 | Новые / подробные настройки диагностики (workspace, storage, NSG flow logs) | ГБ приёма ↑; настройка диагностики создана ≈ начало (Activity Log) | Без изменений |
| H-MON-02 | Увеличен срок хранения | Счётчик хранения ↑; изменён срок хранения workspace | Не менялся |
| H-MON-03 | Объём логов кластеров / init-скриптов | Таблицы приёма по источнику (таблица `Usage` в Log Analytics) | Другой источник |

Диагностика: Log Analytics → *Usage and estimated costs*; запрос `Usage | summarize sum(Quantity) by DataType, bin(TimeGenerated, 1d)`.

---
Результаты сохраняйте в `06_root_cause/results/` аудита; обновляйте `hypothesis_register.csv` и `evidence_register.csv`. Назад к [шагу 06](../README.md).
