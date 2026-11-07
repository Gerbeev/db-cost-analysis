# PB-SERVERLESS - serverless

<!-- plain -->
> **Обзор.** Используйте, когда дороже стали **serverless**-продукты. Виртуальных машин здесь нет - вся цена в DBU, - поэтому вопрос в том, *что запускается, как часто и с какой включённой функцией*.
<!-- /plain -->

**Сигналы:** доля serverless в `6.13` ↑ (`product_features.is_serverless = true`); `5.6` новые serverless SKU.

| # | Проверка | Источник | Что смотреть |
|---|---|---|---|
| V1 | Потребление serverless по продукту/SKU/месяцу | [`6.13_serverless_and_features.sql`](../sql/6.13_serverless_and_features.sql) | Какой продукт растёт |
| V2 | Classic vs serverless для тех же объектов | `5.3`, сгруппированный по объекту через SKU | Смена структуры vs новое потребление |
| V3 | Атрибуция по notebook / пользователю | `5.3` object_type `NOTEBOOK`; `sample_run_as` | Новые пользователи |
| V4 | Покрытие бюджетными политиками / тегами | [`5.5_attribution_coverage.sql`](../../05_databricks_decomposition/sql/5.5_attribution_coverage.sql) | Serverless без тегов |

| ID | Механизм | Подтверждает | Опровергает |
|---|---|---|---|
| H-SRV-01 | Миграция с классических вычислений (смена структуры) | Классическое ↓ для тех же объектов; сравните итог (Δ serverless + Δ классических DBU + Δ VM) | Нет снижения классического |
| H-SRV-02 | Новое использование serverless notebook | Объекты `NOTEBOOK` NEW; пользователи ↑ | Стабильно |
| H-SRV-03 | Режим performance-optimized | `usage_metadata`/`product_features.performance_target` = performance optimized | Стандартный режим |
| H-SRV-04 | SKU сети / egress serverless | Продукт `NETWORKING` ↑ | Без изменений |

**Варианты исправления:** стандартный (cost-optimized) режим для задач без требований к задержке; бюджетные политики; политики использования serverless по командам.

---
Результаты сохраняйте в `06_root_cause/results/` аудита; обновляйте `hypothesis_register.csv` и `evidence_register.csv`. Назад к [шагу 06](../README.md).
