# 02 · Доступы и сбор данных

<!-- plain -->
> **Обзор.** Список того, что вам должны разрешить смотреть, и как это скачать. Отправьте список прав тем, кто управляет Azure и Databricks, **заранее** - получение доступа обычно самая медленная часть аудита. Всё здесь только для чтения.
<!-- /plain -->

## 1. Минимальный доступ на чтение {#1-minimum-read-access}

| Источник | Роль / привилегия | Используется на шагах | Если отказано |
|---|---|---|---|
| Azure Cost Management | **Cost Management Reader** (просмотр) или **Cost Management Contributor** (создание выгрузок) в биллинговом охвате / подписках; EA: Enterprise read-only user; MCA: Reader биллингового профиля | 1-4 | Попросить у FinOps существующую выгрузку Actual того же охвата |
| Хранилище Azure Exports | Storage Blob Data Reader на контейнер выгрузок | 1 | Попросить у владельца выгрузки файлы + манифест |
| Ресурсы Azure | **Reader** на подписки, включая managed RG | 4, 6 | Сопоставление workspace↔RG становится `UNKNOWN` |
| Azure Activity Log | Reader (портал хранит 90 дней) | 6 | Доказательства изменений только из аудита Databricks |
| Системные таблицы Databricks | `USE CATALOG system`, `USE SCHEMA` + `SELECT` на `billing`, `compute`, `lakeflow`, `query`, `access` | 1, 2, 5, 6 | Пометить источник `UNKNOWN`, а не ноль |
| Databricks SQL warehouse | CAN USE на существующий warehouse | 1-6 | Нужно согласие: запросы расходуют DBU |
| UI Databricks (Jobs, Compute, SQL Warehouses) | CAN VIEW / пользователь workspace | 6 | Опираться на системные таблицы |
| IBM Cloudability / ApptioOne | Доступ к отчётам на чтение | 3, 8 | Пропустить (необязательный взгляд) |

Никогда не повышайте привилегии сверх согласованного. Источники с отказом записывайте в scope record §4.

## 2. Azure Actual Cost

### 2.1 Интерактивно (Cost analysis)
1. `portal.azure.com` → поиск **Cost Management** → **Scope** (слева вверху), выделить охват, **Select** → **Cost analysis** в левом меню.
2. Cost analysis открывается списком видов или графиком. В **All views** откройте *настраиваемый* вид (например **Cost by service**): только у них есть период, детализация и **Group by**.
3. Метрика: **Actual cost** (стрелка вниз рядом с показателем затрат переключает на **Amortized cost**). Даты: полные месяцы окна. Детализация: **Monthly**; **Daily** только для окна начала роста (не больше трёх месяцев в одном дневном диапазоне).
4. **Group by** по одному признаку за раз: *Subscription*, *Service name*, *Meter category*, *Meter*, *Resource group name*, *Resource*, *Charge type*, *Pricing model*, *Location*, *Tag*.
5. Начинайте **без** фильтра сервиса; фильтры добавляйте только после того, как известен итог по полному охвату.
6. **Download** → CSV как доказательство (запишите ID охвата, представление, время). Cost analysis показывает данные Cost Management, где нет налогов и кредитов: сравнивайте его с выгрузкой, а не со счётом.

### 2.2 Массово (Exports)
Нужны **Cost Management Contributor** (или выше) на охвате и право записи в storage account.
1. Cost Management → **Exports** → **+ Create** → **Basics**: *Create your own export* → **Datasets**: **Type of data** *Cost and usage details (actual)*, **Export prefix** и **Export name**; частота *Monthly export of last month's costs* → **Destination**: Azure blob storage, подписка, группа ресурсов, storage account, контейнер, каталог, формат **CSV**, сжатие **None** → **Review + create**. Данные могут быть готовы до 24 часов.
2. Для каждого прошлого месяца: выбрать выгрузку → **Export selected dates** → первый и последний день одного месяца (портал достаёт 13 месяцев назад, один месяц на запуск; более старые данные: REST API Exports - Execute). Запуск может идти до 4 часов; обновляйте историю запусков (**Refresh**). После сбора **Disable** выгрузку.
3. Файлы: `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/` в контейнере (storage account → **Open in Explorer** или **Storage browser**). Сохраните **манифест** (`manifest.json`): ID запуска, список частей.
4. На каждый месяц берите **один запуск**; разбиение на части отключить нельзя, поэтому объедините части один раз (один заголовок). Никогда не дописывайте несколько запусков одного месяца или ежедневные снимки с начала месяца - это умножает затраты.
5. Минимальные колонки: `Date`, `CostInBillingCurrency` (EA/MCA) или `Cost`, `BillingCurrencyCode`/`BillingCurrency`, `SubscriptionId`, `ResourceGroup`, `ResourceId`, `ServiceName`, `MeterCategory`, `MeterSubCategory`, `MeterName`, `Quantity`, `UnitOfMeasure`, `EffectivePrice`, `ChargeType`, `PricingModel`, `PublisherType`, `Tags`, `ResourceLocation`.
6. Не подавайте файлы Amortized или FOCUS в инструменты, ожидающие Actual. Нет прав: попросите у FinOps готовую выгрузку *Cost and usage details (actual)* того же охвата.

### 2.3 Сопоставление workspace ↔ managed RG
- Портал → поиск **Azure Databricks** → workspace → **Overview**: *Managed Resource Group*, *Pricing Tier*.
- Или действие 4.2 в интерфейсе (инвентаризация через Azure CLI после `az login`, только чтение; та же логика, что `../tools/azure_workspace_inventory.ps1`).
- Также перечислите зависимые RG: хранилище lake, VNet/NAT/Private Link, Key Vault, Log Analytics.

## 3. Системные таблицы Databricks

| Таблица | Зернистость | Охват | Хранение (бесплатное) | Оговорки |
|---|---|---|---|---|
| `system.billing.usage` | Запись потребления (примерно почасовая) по SKU | Весь аккаунт | Бессрочно | Корректировки (`RETRACTION`/`RESTATEMENT`); пустые ID по замыслу; разные единицы |
| `system.billing.list_prices` | Версия цены по SKU/единице | Аккаунт | Бессрочно | Прайс-лист, не договор; валюта в каждой строке |
| `system.lakeflow.jobs` | Определения задач SCD2 | Регион | 395 дней | `job_id` уникален только в пределах workspace |
| `system.lakeflow.job_run_timeline` | Запуск, нарезанный по часам | Регион | 395 дней | Сворачивать по `workspace_id, job_id, run_id` |
| `system.lakeflow.pipeline_update_timeline` | Обновление конвейера, нарезанное | Регион | 395 дней | Сворачивать по `update_id` |
| `system.compute.clusters` | Конфигурация кластера SCD2 | Регион | Бессрочно | Последнюю строку до окна держать как базу |
| `system.compute.node_timeline` | По узлу поминутно | Регион | 395 дней | Короткоживущих узлов может не быть |
| `system.compute.instance_events` | Переходы состояний инстансов пула | Регион | 395 дней | Только завершённые интервалы |
| `system.compute.warehouses` | Конфигурация warehouse SCD2 | Регион | 395 дней | |
| `system.compute.warehouse_events` | События старта/остановки/масштабирования | Регион | 395 дней | События ≠ оплаченные часы |
| `system.query.history` | Запрос | Регион | 365 дней | Длительность ≠ стоимость |
| `system.access.audit` | События аудита | Регион (события уровня аккаунта: глобально) | 395 дней | Чувствительные данные; только агрегаты |

Сроки хранения - по странице Microsoft Learn *Monitor account activity with system tables* (проверено 9 ноября 2026); они меняются, поэтому проверяйте актуальную страницу ([`reference/09`](09_sources_and_glossary.md)). Отсутствующая таблица - это пробел в возможностях, а не отсутствие нагрузки. Системным таблицам нужен workspace с Unity Catalog; они недоступны в Azure China, Azure Government, West India и Switzerland West. Где смотреть: **Catalog** в левой панели workspace → каталог `system`. Кто может читать: пользователи, которые одновременно account admin и metastore admin; остальным - `USE CATALOG` на `system`, `USE SCHEMA` и `SELECT` на схемы.

**Порядок запуска:** следуйте шагам плейбука; README каждого шага перечисляет его SQL и точное место сохранения (`audits/<id>/<step>/results/`). Соглашения: [11_sql_conventions.md](11_sql_conventions.md).

## 4. Источники доказательств изменений (шаг 6)

| Источник | Что доказывает |
|---|---|
| `system.compute.clusters` / `warehouses` / `lakeflow.jobs` (SCD2) | Значение конфигурации и время изменения |
| `system.access.audit` | Кто / какое действие / когда (создание/правка/запуск/права) |
| Azure Activity Log | Изменения уровня ARM (workspace, VNet, хранилище, настройки диагностики) |
| История Git / CI-CD / Terraform / Asset Bundle | Развёрнутое определение и дата релиза |
| Тикеты изменений, release notes | Намерение и согласование |
| Account console Databricks → Previews / включение функций | Переключатели функций уровня аккаунта |

## 5. Обращение с данными

- Сырые выгрузки и результаты запросов содержат ID подписок, имена ресурсов, пользователей, центры затрат → храните в месте с контролем доступа, никогда в Git.
- Не выгружайте `statement_text`, параметры запросов или e-mail пользователей; SQL в этом наборе агрегирует.
- Маскируйте ID и имена во всём, что выходит за пределы команды аудита; немаскированный оригинал храните как доказательство.
- Не запускайте и не меняйте размер warehouse только ради SQL аудита без согласия.
- CSV, открытые в таблицах: осторожно с ячейками, похожими на формулы (`=`, `+`, `-`, `@`), из недоверенных имён.
