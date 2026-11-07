# 00 · Основы - как формируются затраты Azure Databricks

<!-- plain -->
> **Обзор.** Обязательное чтение для тех, кто впервые работает с затратами Azure Databricks (около 15 минут). Ключевые положения:
>
> 1. Databricks тарифицируется **в составе счёта Azure**; отдельного счёта Databricks нет.
> 2. Вычисления тарифицируются в **DBU**; классические вычисления дополнительно включают стоимость виртуальных машин.
> 3. Цена DBU зависит от типа вычислений: одна и та же работа на разных типах стоит по-разному.
> 4. Хранилище, сеть и мониторинг тарифицируются отдельно от вычислений.
> 5. Счёт может расти из-за **учёта** (закончилась скидка, изменилась цена) без увеличения потребления; аудит разделяет одно и другое.
>
> Термины определены в [словаре](14_glossary.md).
<!-- /plain -->

Минимум теории перед аудитом. ~15 минут. Подробнее: [01 модель затрат](01_cost_model.md), формулы: [03 метод анализа](03_analysis_method.md), термины: [14 словарь](14_glossary.md).
Цены ниже **иллюстративные**; реальные ставки зависят от региона, уровня, договора и валюты - всегда берите их из счёта или `system.billing.list_prices`.

## 1. Архитектура → где тратятся деньги

```
 Control plane Databricks (управляет Databricks)  UI, планировщик задач, notebooks, метаданные Unity Catalog → отдельной строки нет
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Compute plane, CLASSIC (ваша подписка,           VM, managed disks, public IP, load balancer             → счётчики инфраструктуры Azure
   managed RG на каждый workspace)                + плата платформы Databricks за DBU                      → счётчик Azure Databricks
 Compute plane, SERVERLESS (управляет Databricks) вычисления входят в более высокую цену DBU                → счётчик Azure Databricks
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ваши аккаунты хранения (ADLS / Blob)             данные, логи Delta, checkpoints, корень DBFS             → счётчики Storage
 Ваша сеть (VNet, NAT, Private Link, FW)          egress, обработка данных, часы endpoint                  → сетевые счётчики
 Ваш мониторинг (Log Analytics)                   приём / хранение диагностических логов                   → счётчики Monitor
```

Azure Databricks - собственный сервис Azure: **всё приходит в счёт Azure**; отдельного счёта Databricks нет.

## 2. Счёт = 5 слоёв

| # | Слой | За что платите | Драйвер (что заставляет расти) | Счётчик Azure / источник |
|---|---|---|---|---|
| 1 | **Платформа Databricks (DBU)** | DBU × $/DBU по SKU | узло-часы, размер узла, тип вычислений, Photon, serverless, функции | счётчики *Azure Databricks*; `system.billing.usage` |
| 2 | **Классическая инфраструктура** | часы VM, managed disks, public IP, LB | узло-часы, семейство VM, spot vs on-demand, простаивающие пулы | Virtual Machines, Managed Disks… в managed RG |
| 3 | **Данные** | объём хранения, транзакции, репликация | объём данных, срок хранения, мелкие файлы, частота чтения/записи | Storage |
| 4 | **Сеть и эксплуатация** | egress, обработка NAT / Private Link, firewall, приём логов | межрегиональные чтения, новые endpoint, подробная диагностика | Bandwidth, NAT Gateway, Private Link, Log Analytics |
| 5 | **Финансы** | обязательства, кредиты, скидки, курс, налог | события договора, а не нагрузка | Charge type, Pricing model, счёт |

Слои 1-2 обычно доминируют в затратах на Databricks; слой 5 может изменить счёт при нулевом изменении нагрузки.

## 3. DBU - основная единица

- **DBU (Databricks Unit)** = нормализованная единица вычислительной мощности в час, **тарификация посекундная**.
- **DBU/час узла** определяется **размером VM** (больше VM → больше DBU/ч). Photon увеличивает число DBU.
- **$ за DBU** определяется **SKU** = тип вычислений × уровень × (serverless или classic) × регион, минус договорная скидка.

| Тип вычислений (семейство SKU) | Для чего | Относительная $/DBU | VM оплачивается отдельно? |
|---|---|---|---|
| Jobs Light | простые плановые задачи без Spark | самая низкая | да |
| **Jobs** | job-кластеры по расписанию | низкая | да |
| SQL classic / **SQL Pro** | классические / pro SQL warehouses | низкая-средняя | да |
| Pipelines (Lakeflow / DLT) Core / Pro / Advanced | декларативные конвейеры | растёт с редакцией | да (classic) |
| **All-Purpose** | интерактивные notebooks, shared-кластеры | высокая (≈ 1,8× Jobs по прайсу) | да |
| **Serverless** (jobs, notebooks, pipelines, SQL) | вычисления под управлением Databricks | самая высокая за DBU | **нет - включено** |
| Model serving, Vector Search, Apps, Lakebase, AI functions | AI / приложения | единицы продукта | обычно нет |

Одна и та же задача на той же VM на All-Purpose стоит заметно дороже, чем на Jobs-кластере - выбор типа вычислений один из главных рычагов затрат.

## 4. Формулы затрат

**Классический кластер, в час**
```
стоимость/ч = Σ узлов [ DBU/ч(размер узла, Photon) × $/DBU(SKU) ]  +  Σ узлов [ VM $/ч ]  (+ диски, IP)
```
Пример: 1 driver + 4 воркера, по 1,5 DBU/ч, Jobs $0,30/DBU, VM $0,50/ч
→ 5 × (1,5 × 0,30 + 0,50) = **$4,75/ч**; то же на All-Purpose по $0,55/DBU → 5 × (0,825 + 0,50) = **$6,63/ч**.

**Serverless, в час**
```
стоимость/ч = DBU/ч(размер или нагрузка) × множитель(функция) × $/DBU(serverless SKU)     - без строки VM
```
Размеры serverless SQL warehouse (DBU/ч): 2X-Small 4 · X-Small 6 · Small 12 · Medium 24 · Large 40 · X-Large 80 · 2X-Large 144.
Есть множители функций (напр. мониторинг качества данных 2×, Databricks Apps medium 0,5×) - см. Microsoft «Serverless DBU consumption by SKU».

**Взгляд через нагрузку (что раскладывает аудит)**
```
стоимость/сутки = запусков/сутки × длительность × узлы × (DBU/ч × $/DBU + VM $/ч)
                  └ частота ─┘     └──── стоимость одного запуска ──────────────┘
```
Каждый множитель соответствует типичной первопричине: больше запусков, дольше запуски, больше кластеры, дороже SKU, выше цена.

## 5. Уровни и изменения 2026 года

| Факт | Влияние на аудит |
|---|---|
| Уровни в Azure: **Standard** и **Premium** (Unity Catalog, RBAC, SQL warehouses, serverless только на Premium) | $/DBU на Premium выше, чем на Standard |
| Новых Standard workspace нет с **1 апр 2026**; оставшиеся Standard workspace автоматически переведены на Premium **1 окт 2026** | Ступенька ставки 1 окт 2026 при неизменном потреблении = смена уровня, а не нагрузка (H-RAT-11) |

## 6. Скидки и обязательства

| Инструмент | Что покрывает | Механика | Как выглядит в счёте |
|---|---|---|---|
| **Предоплата DBCU** (1 или 3 года) | Начисления DBU, все нагрузки/уровни | предоплаченный пул; потребление списывается по соотношению прайс-листа; сначала используется план с ближайшим сроком; скидка до ~37% | пока действует покрытие, потребление DBU показывает **0** on-demand стоимости; покупка - одна строка в Actual. **Пул исчерпан или истёк → затраты DBU внезапно появляются в Actual** (H-RAT-02) |
| **Резервирования VM** (1 / 3 года) | только классические VM | почасовое обязательство по использованию | Actual: строка покупки; Amortized: распределена на срок |
| **Savings plan for compute** | классические VM (и другие вычисления) | почасовое обязательство по расходам | так же |
| **Spot VM** | классические воркеры | большая скидка, могут быть вытеснены; откат на on-demand повышает стоимость | Pricing model *Spot* vs *OnDemand* |
| **Договорная скидка / MACC** | по договору | фактическая цена ниже прайса | `EffectivePrice` < прайса; `list_prices` Databricks её **не** показывает |

У serverless нет строки VM, поэтому резервирования VM / savings plans к нему не применяются - перенос нагрузок на serverless может оставить обязательства по VM неиспользованными.

## 7. Основы биллинга Azure

| Понятие | Значение |
|---|---|
| Тип биллингового аккаунта | **EA** (Enterprise Agreement), **MCA** (Microsoft Customer Agreement), MPA (партнёр/CSP) - имена колонок в выгрузках различаются |
| Охват (scope) | биллинговый аккаунт → биллинговый профиль → подписка → группа ресурсов; затраты всегда «в охвате» |
| Счётчик (meter) | оплачиваемая позиция со своей ценой за единицу (напр. *Premium Jobs Compute DBU*, *D8s v5*, *Hot LRS Data Stored*) |
| **Actual cost** | как выставлено; покупки попадают в месяц покупки → всплески |
| **Amortized cost** | покупки распределены на срок → для операционных трендов |
| Charge type | Usage, Purchase, Refund, Adjustment |
| Pricing model | OnDemand, Reservation, SavingsPlan, Spot |
| Выгрузка cost details | построчные данные (дата, счётчик, количество, фактическая цена, стоимость, ресурс, теги) - сырьё аудита |

## 8. Откуда обычно берётся рост (проверять в этом порядке)

| # | Типичная причина | Сигнал | Плейбук |
|---|---|---|---|
| 1 | Событие обязательства / кредита / уровня / цены | ступенька 1-го числа месяца, Actual ≠ Amortized, количество без изменений | [12 rate](../playbook/06_root_cause/playbooks/12_rate_and_accounting.md) |
| 2 | Новые или более частые задачи, backfill | DBU `JOBS` ↑, запусков/сутки ↑ | [01 jobs](../playbook/06_root_cause/playbooks/01_jobs.md) |
| 3 | Простаивающие / избыточные all-purpose кластеры | DBU `ALL_PURPOSE` + VM ↑, низкий CPU | [03 classic](../playbook/06_root_cause/playbooks/03_classic_compute.md) |
| 4 | SQL warehouses работают дольше / крупнее, опрос из BI | DBU `SQL` ↑, время работы warehouse ↑ | [05 SQL](../playbook/06_root_cause/playbooks/05_sql_warehouses.md) |
| 5 | Конвейеры переведены в continuous / full refresh | DBU `DLT` ↑ | [02 pipelines](../playbook/06_root_cause/playbooks/02_pipelines.md) |
| 6 | Переход на serverless / включены управляемые функции | новые serverless SKU | [06](../playbook/06_root_cause/playbooks/06_serverless.md), [08](../playbook/06_root_cause/playbooks/08_platform_features.md) |
| 7 | Рост данных → дольше запуски, хранение, транзакции | длительность ↑, Storage ↑ | [09 storage](../playbook/06_root_cause/playbooks/09_storage.md) |
| 8 | Побочные эффекты сети / логирования | NAT, egress, Log Analytics ↑ | [10](../playbook/06_root_cause/playbooks/10_network.md), [11](../playbook/06_root_cause/playbooks/11_monitoring.md) |

## 9. Где смотреть каждое число

| Вопрос | Источник |
|---|---|
| Сколько мы заплатили? | Azure Cost Management → Cost analysis (Actual) / Exports |
| Сколько потребил Databricks (DBU по задачам/кластерам/warehouse)? | `system.billing.usage` |
| Какой прайс по SKU во времени? | `system.billing.list_prices` |
| Сколько мы реально платили за единицу? | `EffectivePrice` в выгрузке Azure |
| Как настроены кластеры / warehouse / задачи и когда это менялось? | `system.compute.*`, `system.lakeflow.*` (история) |
| Кто что изменил? | `system.access.audit`, Azure Activity Log |
| Остаток и срок обязательств | Портал Azure → Reservations (план DBCU, резервирования VM) |

## 10. Практические правила

1. Счёт (Azure Actual) - истина; стоимость Databricks по прайсу - **модель**, никогда не складывайте их.
2. Classic = DBU **и** VM; serverless = только DBU.
3. Сравнивайте **стоимость в сутки**, а не в месяц.
4. Большая часть роста = больше узло-часов (запуски × длительность × узлы) или более дорогой SKU; изменения цены реже, но внезапнее.
5. Ступенька 1-го числа месяца → сначала договоры, потом нагрузки.
6. Обязательства скрывают затраты, пока действуют; их окончание выглядит как рост.
7. All-purpose вычисления для плановых задач и отсутствие автоотключения - самые частые потери.
8. За каждым утверждением о росте должно стоять датированное событие изменения.

## Источники

- [Azure Databricks pricing](https://azure.microsoft.com/en-us/pricing/details/databricks/) - определение DBU, типы вычислений, Photon, размеры serverless SQL, вывод уровня Standard, уровни DBCU
- [Serverless DBU consumption by SKU](https://learn.microsoft.com/en-us/azure/databricks/resources/pricing) - serverless SKU и множители DBU
- [Optimize Azure Databricks costs with a pre-purchase](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/prepay-databricks-reserved-capacity) - соотношения списания DBCU
- [How the Databricks pre-purchase discount is applied](https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/reservation-discount-databricks) - сначала план с ближайшим сроком; on-demand начисления показываются нулём
- [Billable usage system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing), [Pricing system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/pricing)
- [Cost analysis - Actual vs Amortized](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-analysis-common-uses)
