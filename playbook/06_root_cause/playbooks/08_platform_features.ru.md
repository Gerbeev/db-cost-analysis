# PB-FEATURES - функции платформы

<!-- plain -->
> **Обзор.** Используйте, когда дороже стали фоновые функции платформы: predictive optimization, мониторинг качества данных, сетевые функции. Они часто появляются **после того, как кто-то включил настройку** для всего аккаунта.
<!-- /plain -->

**Сигналы:** `PREDICTIVE_OPTIMIZATION`, `LAKEHOUSE_MONITORING`, `DATA_QUALITY_MONITORING`, `FINE_GRAINED_ACCESS_CONTROL`, `LAKEFLOW_CONNECT`, `DEFAULT_STORAGE`, `DATA_CLASSIFICATION` ↑ или появились впервые.

| # | Проверка | Источник | Что смотреть |
|---|---|---|---|
| F1 | Впервые появившиеся продукты/SKU | [`5.6_first_seen_skus.sql`](../../05_databricks_decomposition/sql/5.6_first_seen_skus.sql) | Дата старта = включение |
| F2 | Помесячное потребление | [`6.13_serverless_and_features.sql`](../sql/6.13_serverless_and_features.sql) | Рост |
| F3 | Состояние включения | Account console → Settings / Previews; настройки каталога (наследование predictive optimization); аудит `6.14` | Кто включил и когда |

| ID | Механизм | Подтверждает | Опровергает |
|---|---|---|---|
| H-FEA-01 | Включена / расширена predictive optimization | Первое появление или ступенька ↑ в `PREDICTIVE_OPTIMIZATION` | Отсутствует / без изменений |
| H-FEA-02 | Добавлены мониторы lakehouse / качества данных | SKU мониторинга ↑; число мониторов ↑ | Без изменений |
| H-FEA-03 | Фильтрация FGAC на dedicated compute | `FINE_GRAINED_ACCESS_CONTROL` ↑ | Без изменений |
| H-FEA-04 | Управляемая загрузка (Lakeflow Connect) | Продукт ↑, новые шлюзы | Без изменений |
| H-FEA-05 | Использование default storage | `DEFAULT_STORAGE` ↑ | Без изменений |

**Варианты исправления:** ограничить функцию нужными каталогами; частота обновления мониторов; оценить выгоду против затрат (predictive optimization часто снижает стоимость запросов - замеряйте обе стороны).

---
Результаты сохраняйте в `06_root_cause/results/` аудита; обновляйте `hypothesis_register.csv` и `evidence_register.csv`. Назад к [шагу 06](../README.md).
