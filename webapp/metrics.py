"""Why each metric is needed and how to obtain it (EN / RU).

For every action that produces or collects a number, a file or a decision input, `INFO` holds:
  why - the purpose of the metric in the audit (one to three sentences);
  how - where it comes from and how to obtain it (a short list: portal path, system table, what the app does).
The step page shows both blocks inside the action; `reference_doc()` renders the same content as the reference page
`reference/15_data_sources.md` (kept in sync by `plain_docs.sync`, enforced by tests).

Register: professional and precise, for readers who do this for the first time. ASCII hyphen only.
Text conventions as in plain.py: blank line = paragraph, "- " = list, `code`, **bold**.
"""
from __future__ import annotations


def T(en: str, ru: str) -> dict:
    return {"en": en, "ru": ru}


INFO: dict[str, tuple[dict, dict]] = {}


def info(id_: str, why: dict, how: dict | None = None) -> None:
    INFO[id_] = (why, how or T("", ""))


JOIN_CMD = ("python -c \"import glob;p=sorted(glob.glob('*.csv'));o=open('merged.tmp','wb');"
            "[o.writelines(l for n,l in enumerate(open(f,'rb')) if n or not i) for i,f in enumerate(p)];o.close()\"")

SQL_RUN_EN = ("Run in the app: press **Run** (the Databricks connection from Settings is used; read-only).\n"
              "- Run by hand: in the Databricks workspace click **SQL Editor** in the left sidebar, pick a SQL "
              "warehouse in the selector at the top of the editor (it starts by itself, which consumes DBUs; the "
              "right `CAN USE` is needed), paste the SQL and press **Run** (or Ctrl/Cmd+Enter). If the editor shows a "
              "row limit such as **Limit 1000**, switch it off. In the result pane open the menu next to the result "
              "tab, choose **Download**, **CSV**, and upload the file here.\n"
              "- Rights: `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on the schemas used (see action 1.6).")
SQL_RUN_RU = ("Запуск в приложении: нажмите **Run** (используется подключение к Databricks из настроек; только "
              "чтение).\n"
              "- Запуск вручную: в workspace Databricks нажмите **SQL Editor** в левой панели, выберите SQL warehouse "
              "в списке вверху редактора (он запускается сам, это расходует DBU; нужно право `CAN USE`), вставьте SQL и "
              "нажмите **Run** (или Ctrl/Cmd+Enter). Если редактор показывает ограничение строк, например **Limit "
              "1000**, отключите его. В панели результата откройте меню рядом с вкладкой результата, выберите "
              "**Download**, **CSV** и загрузите файл сюда.\n"
              "- Права: `USE CATALOG` на `system`, `USE SCHEMA` и `SELECT` на используемые схемы (см. действие 1.6).")
SQL_ACCESS_EN = ("- Before the first run: by default only users who are both **account admin** and **metastore "
                 "admin** can read system tables. For everyone else an admin grants `USE CATALOG` on the `system` "
                 "catalog and `USE SCHEMA` and `SELECT` on the schemas `billing`, `compute`, `lakeflow`, `query`, "
                 "`access`. System tables exist only if the account has a workspace with Unity Catalog, and are "
                 "not available in Azure China, Azure Government, West India and Switzerland West.")
SQL_ACCESS_RU = ("- Перед первым запуском: по умолчанию системные таблицы читают только пользователи, которые "
                 "одновременно **account admin** и **metastore admin**. Остальным администратор выдаёт `USE CATALOG` "
                 "на каталог `system` и `USE SCHEMA` и `SELECT` на схемы `billing`, `compute`, `lakeflow`, `query`, "
                 "`access`. Системные таблицы есть, только если в аккаунте есть workspace с Unity Catalog; они "
                 "недоступны в Azure China, Azure Government, West India и Switzerland West.")


# ----------------------------------------------------------------------- 00
info("0.1",
     T("The periods B, C and P define every comparison in the audit. The app copies them into all tools and SQL "
       "queries, so they are entered once.",
       "Периоды B, C и P определяют все сравнения в аудите. Приложение подставляет их во все инструменты и SQL, "
       "поэтому вводить их нужно один раз."),
     T("- Take them from the invoice or Cost Analysis chart: find the month where the monthly cost first stayed higher.\n"
       "- Provisional values are enough: step 02 refines them from the daily data.",
       "- Возьмите их из счёта или графика Cost Analysis: найдите месяц, с которого месячные затраты впервые "
       "остались выше.\n"
       "- Достаточно предварительных значений: шаг 02 уточнит их по дневным данным."))
info("0.2",
     T("A scope fixed in writing prevents the costliest audit error: a change of scope after the data has been "
       "collected. The approval of the audit owner is the first gate.",
       "Охват, зафиксированный письменно, предотвращает самую дорогую ошибку аудита: изменение охвата после сбора "
       "данных. Утверждение владельца аудита - первая контрольная точка."),
     T("Labels are given for the English Azure portal (gear icon in the top bar, **Language + region**, switches the "
       "language). Sign in at `portal.azure.com` with your work account.\n"
       "- Agreement type and billing scope: in the search box at the top type **Cost Management + Billing** and open "
       "it. In the left menu choose **Billing scopes** and select the billing account (if there is a single account, "
       "the page opens in it). Then **Properties**: the account type is Enterprise Agreement (EA), Microsoft Customer "
       "Agreement (MCA) or Individual. No **Billing scopes** entry means that you have no billing role: ask the "
       "billing administrator.\n"
       "- Subscriptions: search **Subscriptions**; the list shows the name and the subscription ID of each one.\n"
       "- Workspaces and regions: search **Azure Databricks**; the list shows each workspace with its resource group, "
       "location and subscription. Open a workspace: **Overview** shows **Managed Resource Group** and **Pricing "
       "Tier** (Standard or Premium).\n"
       "- Commitments: search **Reservations**; the list contains the reservation orders you can see, including the "
       "Databricks pre-purchase plan (DBCU) if one was bought. A billing administrator sees all purchases under **Cost "
       "Management + Billing**, the billing scope, **Reservation transactions**. Savings plans: search **Savings "
       "plans**.\n"
       "- Credits: MCA - the billing account, the billing profile, **Payment methods**, **Azure credits**. EA - the "
       "billing account, **Credits + Commitments**.\n"
       "- Access to each source: try it and write OK, DENIED or UNKNOWN. A denied source is a limitation, not a zero.",
       "Названия даны по англоязычному порталу Azure (значок шестерёнки в верхней панели, **Language + region**, "
       "переключает язык). Войдите на `portal.azure.com` рабочей учётной записью.\n"
       "- Тип договора и биллинговый охват: в строке поиска сверху введите **Cost Management + Billing** и откройте "
       "его. В левом меню выберите **Billing scopes** и укажите биллинговый аккаунт (если он один, страница откроется "
       "сразу в нём). Затем **Properties**: тип аккаунта - Enterprise Agreement (EA), Microsoft Customer Agreement "
       "(MCA) или Individual. Нет пункта **Billing scopes** - у вас нет биллинговой роли: обратитесь к "
       "администратору биллинга.\n"
       "- Подписки: поиск **Subscriptions**; в списке видны имя и ID каждой подписки.\n"
       "- Workspace и регионы: поиск **Azure Databricks**; в списке у каждого workspace видны группа ресурсов, "
       "расположение и подписка. Откройте workspace: на **Overview** указаны **Managed Resource Group** и **Pricing "
       "Tier** (Standard или Premium).\n"
       "- Обязательства: поиск **Reservations**; в списке резервации, которые вам доступны, включая предоплаченный "
       "план Databricks (DBCU), если он куплен. Администратор биллинга видит все покупки в **Cost Management + "
       "Billing**, биллинговый охват, **Reservation transactions**. Планы сбережений: поиск **Savings plans**.\n"
       "- Кредиты: MCA - биллинговый аккаунт, биллинговый профиль, **Payment methods**, **Azure credits**. EA - "
       "биллинговый аккаунт, **Credits + Commitments**.\n"
       "- Доступ к каждому источнику: попробуйте и запишите OK, DENIED или UNKNOWN. Недоступный источник - "
       "ограничение, а не ноль."))

# ----------------------------------------------------------------------- 01
info("1.1",
     T("This file is the ledger of the whole audit. Every later number about money (growth per day, services, meters, "
       "resource groups) is computed from it, so it must be Actual cost, complete, and taken once per month.",
       "Этот файл - главный регистр всего аудита. Каждое следующее число о деньгах (рост в сутки, сервисы, "
       "счётчики, группы ресурсов) считается из него, поэтому он должен быть Actual cost, полным и взятым один раз "
       "на месяц."),
     T("Rights: **Cost Management Contributor** (or higher) on the scope to create an export, and write access to a "
       "storage account. **Cost Management Reader** can only view. Without these rights ask FinOps for an existing "
       "export of type **Cost and usage details (actual)** for the same scope and go to step 6.\n\n"
       "1. Sign in at `portal.azure.com`. In the search box type **Cost Management** and open it. Press the "
       "**Scope** pill at the top left, highlight the scope from action 0.2 and press **Select**. In the left menu "
       "choose **Exports**.\n"
       "2. Press **+ Create**. On the **Basics** tab choose **Create your own export** (press **Show more** if it is "
       "not visible) and **Next**.\n"
       "3. **Datasets** tab: enter an **Export prefix**, for example `dbaudit`. Set **Type of data** to **Cost and "
       "usage details (actual)** - not *amortized*, not *FOCUS*, not *usage only*. Keep the offered **Dataset "
       "version**, enter an **Export name**, for example `dbaudit-actual`. Frequency: **Monthly export of last "
       "month's costs** (a recurring export can be re-run for past months, see step 5). If the portal asks for a "
       "date range in UTC, enter the first and last day of one month. Press **Add**, then **Next**.\n"
       "4. **Destination** tab: **Storage type** Azure blob storage; select the **Subscription**, **Resource group**, "
       "**Storage account name** (or create one), **Container** and **Directory path**. **Format** CSV, "
       "**Compression type** None (Gzip files need unpacking). File partitioning is always on: a large month arrives "
       "in several parts. **Next**, then **Review + create**, then **Create**. New exports are enabled; data can take "
       "up to 24 hours to be ready.\n"
       "5. Back in the **Exports** list select the export and press **Export selected dates**. Choose the first and "
       "last day of **one** calendar month (the portal reaches back 13 months, one month per run) and start the run. "
       "Wait until the run appears in the run history (press **Refresh**; up to 4 hours). Repeat for every month of "
       "the window, each month once. When all months are collected press **Disable** on the export so that no new "
       "files appear.\n"
       "6. Download: in the **Exports** list press the storage account name, then **Open in Explorer** (needs the "
       "Azure Storage Explorer application) or, in the portal, **Storage browser** in the left menu, **Blob "
       "containers**, your container. The files are in `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/`. "
       "Download every `.csv` file and `manifest.json` of the run of each month.\n"
       "7. A month with several parts: put the parts of that one run into an empty folder, open a terminal there and "
       "run `" + JOIN_CMD + "`; rename `merged.tmp` to `<month>.csv`. It keeps a single header line. Never join "
       "runs that cover the same month.\n"
       "8. The app takes one file: if the window has several month files, join them in the same way into one CSV "
       "and upload it.",
       "Права: **Cost Management Contributor** (или выше) на охвате для создания выгрузки и права записи в storage "
       "account. **Cost Management Reader** может только просматривать. Без этих прав попросите у FinOps готовую "
       "выгрузку типа **Cost and usage details (actual)** того же охвата и переходите к шагу 6.\n\n"
       "1. Войдите на `portal.azure.com`. В строке поиска введите **Cost Management** и откройте его. Нажмите на "
       "**Scope** в левом верхнем углу, выделите охват из действия 0.2 и нажмите **Select**. В левом меню выберите "
       "**Exports**.\n"
       "2. Нажмите **+ Create**. На вкладке **Basics** выберите **Create your own export** (если его не видно, "
       "нажмите **Show more**) и **Next**.\n"
       "3. Вкладка **Datasets**: введите **Export prefix**, например `dbaudit`. **Type of data** - **Cost and usage "
       "details (actual)** - не *amortized*, не *FOCUS*, не *usage only*. Оставьте предложенную **Dataset version**, "
       "введите **Export name**, например `dbaudit-actual`. Частота: **Monthly export of last month's costs** "
       "(регулярную выгрузку можно перезапустить за прошлые месяцы, см. шаг 5). Если портал запрашивает диапазон дат "
       "в UTC, введите первый и последний день одного месяца. Нажмите **Add**, затем **Next**.\n"
       "4. Вкладка **Destination**: **Storage type** - Azure blob storage; выберите **Subscription**, **Resource "
       "group**, **Storage account name** (или создайте), **Container** и **Directory path**. **Format** CSV, "
       "**Compression type** None (файлы Gzip нужно распаковывать). Разбиение на части всегда включено: большой "
       "месяц приходит в нескольких файлах. **Next**, затем **Review + create**, затем **Create**. Новые выгрузки "
       "включены; данные могут быть готовы до 24 часов.\n"
       "5. В списке **Exports** выберите выгрузку и нажмите **Export selected dates**. Укажите первый и последний "
       "день **одного** календарного месяца (портал достаёт до 13 месяцев назад, один месяц на запуск) и запустите. "
       "Дождитесь появления запуска в истории (нажимайте **Refresh**; до 4 часов). Повторите для каждого месяца окна, "
       "каждый месяц один раз. Когда все месяцы собраны, нажмите **Disable** на выгрузке, чтобы новые файлы не "
       "появлялись.\n"
       "6. Скачивание: в списке **Exports** нажмите на имя storage account, затем **Open in Explorer** (нужно "
       "приложение Azure Storage Explorer) либо в портале **Storage browser** в левом меню, **Blob containers**, ваш "
       "контейнер. Файлы лежат в `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/`. Скачайте все `.csv` "
       "и `manifest.json` запуска каждого месяца.\n"
       "7. Месяц из нескольких частей: положите части этого одного запуска в пустую папку, откройте там терминал и "
       "выполните `" + JOIN_CMD + "`; переименуйте `merged.tmp` в `<месяц>.csv`. Строка заголовка остаётся одна. "
       "Запуски, покрывающие один и тот же месяц, не объединяются.\n"
       "8. Приложение принимает один файл: если в окне несколько файлов месяцев, объедините их так же в один CSV и "
       "загрузите его."))
info("1.2",
     T("The manifest records the run ID and the list of files of each export run. It proves that every month was "
       "taken exactly once; without it a duplicated run cannot be told apart from real cost.",
       "Манифест фиксирует ID запуска и список файлов каждого запуска выгрузки. Он доказывает, что каждый месяц "
       "взят ровно один раз; без него задвоенный запуск не отличить от реальных затрат."),
     T("- Each run has its own folder `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/` in the storage "
       "container; it holds the data files and `manifest.json`. Download the `manifest.json` of every run you used "
       "together with the data files (step 6 of action 1.1).\n"
       "- Check: every month of the window has exactly one run folder.\n"
       "- No manifests (a file received from FinOps)? Write the run IDs or file names in `export_manifest.md` and "
       "upload that file instead.",
       "- У каждого запуска в контейнере своя папка `<directory>/<export name>/<YYYYMMDD-YYYYMMDD>/<run ID>/`; в ней "
       "файлы данных и `manifest.json`. Скачайте `manifest.json` каждого использованного запуска вместе с файлами "
       "данных (шаг 6 действия 1.1).\n"
       "- Проверка: у каждого месяца окна ровно одна папка запуска.\n"
       "- Манифестов нет (файл получен от FinOps)? Запишите ID запусков или имена файлов в `export_manifest.md` и "
       "загрузите этот файл."))
info("1.3",
     T("An independent monthly total from a different Azure screen. If it differs from the export by more than 0.5%, "
       "the export is incomplete or duplicated and no later number can be trusted (rule R6).",
       "Независимый месячный итог с другого экрана Azure. Если он отличается от выгрузки больше чем на 0,5%, "
       "выгрузка неполная или задвоена, и никаким последующим числам верить нельзя (правило R6)."),
     T("1. `portal.azure.com`, search **Cost Management**, open it. Check the **Scope** pill at the top left: it must "
       "be the scope of the export (select it as in action 1.1). In the left menu choose **Cost analysis**.\n"
       "2. Cost analysis opens either a list of views or a chart. Open **All views** and choose a customizable view, "
       "for example **Cost by service**: customizable views show the date range, granularity and **Group by** "
       "controls.\n"
       "3. Metric: the cost figure must read **Actual cost**. Its down arrow switches between **Actual cost** and "
       "**Amortized cost**.\n"
       "4. Date range: press the date pill and choose a custom range from the first day of the first month to the "
       "last day of the last month of the window. Granularity: **Monthly**. **Group by**: choose **None** (or remove "
       "the grouping). No filters.\n"
       "5. Press **Download** at the top, choose **CSV**, and upload the file here.\n"
       "Note: the export and Cost analysis both come from Cost Management, so they are compared with each other, not "
       "with the PDF invoice: the invoice contains taxes and credits that Cost Management does not.",
       "1. `portal.azure.com`, поиск **Cost Management**, откройте. Проверьте **Scope** в левом верхнем углу: это "
       "должен быть охват выгрузки (выбор - как в действии 1.1). В левом меню выберите **Cost analysis**.\n"
       "2. Cost analysis открывается либо списком видов, либо графиком. Откройте **All views** и выберите "
       "настраиваемый вид, например **Cost by service**: у настраиваемых видов есть период, детализация и "
       "**Group by**.\n"
       "3. Метрика: показатель затрат должен называться **Actual cost**. Стрелка вниз у него переключает "
       "**Actual cost** и **Amortized cost**.\n"
       "4. Период: нажмите на дату и задайте произвольный диапазон от первого дня первого месяца до последнего дня "
       "последнего месяца окна. Детализация: **Monthly**. **Group by**: **None** (или уберите группировку). Без "
       "фильтров.\n"
       "5. Нажмите **Download** сверху, выберите **CSV** и загрузите файл сюда.\n"
       "Примечание: выгрузка и Cost analysis обе берутся из Cost Management, поэтому их сравнивают между собой, а не "
       "со счётом в PDF: в счёте есть налоги и кредиты, которых нет в Cost Management."))
info("1.4",
     T("Turns the raw export into a monthly total and a cost per day. The cost per day is the unit of comparison "
       "for the whole audit because months differ in length.",
       "Превращает сырую выгрузку в месячный итог и затраты в сутки. Затраты в сутки - единица сравнения для "
       "всего аудита, так как месяцы различаются по длине."),
     T("Nothing to enter: the app reads the main export and writes `export_monthly`.",
       "Вводить ничего не нужно: приложение читает основную выгрузку и записывает `export_monthly`."))
info("1.5",
     T("Confirms that the export is complete by comparing two independent sources month by month (rule R6). "
       "A failed check stops the audit until the export is fixed.",
       "Подтверждает полноту выгрузки сравнением двух независимых источников по месяцам (правило R6). "
       "Непройденная проверка останавливает аудит, пока выгрузка не исправлена."),
     T("Nothing to enter: the app takes the results of 1.3 and 1.4. A difference above 0.5% usually means a duplicated "
       "run or a missing day - repeat 1.1.",
       "Вводить ничего не нужно: приложение берёт результаты 1.3 и 1.4. Разница выше 0,5% обычно означает задвоенный "
       "запуск или пропущенный день - повторите 1.1."))
info("1.6",
     T("Databricks usage records are the basis of the cost model. A day without records produces a false drop or a "
       "false rise, and the second query lists workspaces that appeared or disappeared in the window.",
       "Записи потребления Databricks - основа модели затрат. День без записей даёт ложное падение или ложный "
       "рост, а второй запрос перечисляет workspace, появившиеся или исчезнувшие за окно."),
     T(f"- Source: `system.billing.usage`.\n{SQL_ACCESS_EN}\n- {SQL_RUN_EN}\n- Result files: `1.1_usage_coverage` and "
       "`1.1_workspace_presence`.",
       f"- Источник: `system.billing.usage`.\n{SQL_ACCESS_RU}\n- {SQL_RUN_RU}\n- Файлы результата: `1.1_usage_coverage` и "
       "`1.1_workspace_presence`."))
info("1.7",
     T("Shows which units each SKU is measured in. Quantities in different units (DBU, GB, hours) must never be "
       "added together.",
       "Показывает, в каких единицах измеряется каждый SKU. Количества в разных единицах (DBU, ГБ, часы) "
       "нельзя складывать."),
     T(f"- Source: `system.billing.usage`.\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.usage`.\n- {SQL_RUN_RU}"))
info("1.8",
     T("The modeled cost is usage multiplied by list price. If a usage row has no price or several prices, the "
       "modeled cost of that SKU is wrong (rule R7); such SKUs are excluded from money conclusions.",
       "Модельная стоимость - это потребление, умноженное на прайс. Если у строки потребления нет цены или их "
       "несколько, модельная стоимость этого SKU неверна (правило R7); такие SKU исключаются из денежных выводов."),
     T(f"- Sources: `system.billing.usage` and `system.billing.list_prices`.\n- {SQL_RUN_EN}\n- Read the column "
       "`verdict`: `FAIL_*` means exclude.",
       f"- Источники: `system.billing.usage` и `system.billing.list_prices`.\n- {SQL_RUN_RU}\n- Смотрите колонку "
       "`verdict`: `FAIL_*` означает исключить."))
info("1.9",
     T("Records what the data allows and what it does not, so that later conclusions are read within these limits.",
       "Фиксирует, что позволяют данные и что нет, чтобы последующие выводы читались в этих границах."),
     T("- Table availability: open the Databricks workspace, click **Catalog** (Catalog Explorer) in the left "
       "sidebar, open the catalog `system` and its schemas `billing`, `compute`, `lakeflow`, `query`, `access`. A "
       "missing schema is UNKNOWN, not zero. A schema that exists but has not been enabled has to be enabled by a "
       "metastore admin first.\n"
       "- Retention of each table: reference 02, section 3.\n"
       "- Limitations: copy the failed SKUs of 1.8 and the largest R6 difference of 1.5.",
       "- Доступность таблиц: откройте workspace Databricks, нажмите **Catalog** (Catalog Explorer) в левой панели, "
       "откройте каталог `system` и схемы `billing`, `compute`, `lakeflow`, `query`, `access`. Отсутствующая схема - "
       "UNKNOWN, а не ноль. Схему, которая есть, но не включена, сначала должен включить администратор "
       "metastore.\n"
       "- Срок хранения каждой таблицы: справочник 02, раздел 3.\n"
       "- Ограничения: перенесите непройденные SKU из 1.8 и наибольшую разницу R6 из 1.5."))

# ----------------------------------------------------------------------- 02
info("2.1",
     T("Shows the growth in the real billed amount and normalises it per day. Without a service filter, so that "
       "growth outside Databricks is visible too.",
       "Показывает рост в реально выставленной сумме и приводит его к суткам. Без фильтра по сервису, чтобы был "
       "виден и рост вне Databricks."),
     T("Nothing to enter: the app reads the main export (1.1) and writes `monthly_series`.",
       "Вводить ничего не нужно: приложение читает основную выгрузку (1.1) и записывает `monthly_series`."))
info("2.2",
     T("A monthly series cannot show the exact day of the change. A daily series is needed only when the main "
       "export does not cover all days.",
       "Помесячный ряд не показывает точный день изменения. Дневной ряд нужен только если основная выгрузка не "
       "покрывает все дни."),
     T("1. `portal.azure.com`, **Cost Management**, check the **Scope** pill, **Cost analysis**, a customizable view "
       "(**All views**, for example **Cost by service**), metric **Actual cost**.\n"
       "2. Granularity **Daily**. The portal allows at most three months in one daily range: choose a range of about "
       "90 days around the suspected change. **Group by**: **None**; no filters.\n"
       "3. **Download**, **CSV**, upload.",
       "1. `portal.azure.com`, **Cost Management**, проверьте **Scope**, **Cost analysis**, настраиваемый вид "
       "(**All views**, например **Cost by service**), метрика **Actual cost**.\n"
       "2. Детализация **Daily**. Портал допускает не больше трёх месяцев в одном дневном диапазоне: выберите "
       "диапазон около 90 дней вокруг предполагаемого изменения. **Group by**: **None**; без фильтров.\n"
       "3. **Download**, **CSV**, загрузите."))
info("2.3",
     T("The start date of the growth narrows the search for the cause: a change event must precede it. A short "
       "rise is a spike, not a step (rule R5).",
       "Дата начала роста сужает поиск причины: событие изменения должно ей предшествовать. Короткий подъём - это "
       "всплеск, а не ступенька (правило R5)."),
     T("Nothing to enter: the app detects the first day of a level that held for 14 days or more, using B as the "
       "baseline.",
       "Вводить ничего не нужно: приложение определяет первый день уровня, продержавшегося 14 дней и более, "
       "используя B как базу."))
info("2.4",
     T("Checks the start date from the Databricks side. A gap of more than a day means that something other than "
       "Databricks is moving the bill.",
       "Проверяет дату начала со стороны Databricks. Разрыв больше суток означает, что счёт двигает что-то кроме "
       "Databricks."),
     T(f"- Source: `system.billing.usage` with `system.billing.list_prices`.\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.usage` и `system.billing.list_prices`.\n- {SQL_RUN_RU}"))
info("2.5",
     T("The monthly modeled cost per SKU is the input for the direction check (3.9) and the volume and rate split "
       "(5.1).",
       "Месячная модельная стоимость по SKU - входные данные для проверки направления (3.9) и разделения на объём "
       "и цену (5.1)."),
     T(f"- Source: `system.billing.usage` with `system.billing.list_prices`.\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.usage` и `system.billing.list_prices`.\n- {SQL_RUN_RU}"))
info("2.6",
     T("Final B, C and P turn the growth into a measurable difference. B must be stable; C must be a full month on "
       "the higher level (rule R2).",
       "Итоговые B, C и P превращают рост в измеримую разницу. B должен быть стабильным; C - полным месяцем на "
       "повышенном уровне (правило R2)."),
     T("- B: at least 28 days before the start date from 2.3, without other changes.\n"
       "- C: the first full month after the start date.\n- P: the month after C.",
       "- B: не меньше 28 дней до даты начала из 2.3, без других изменений.\n"
       "- C: первый полный месяц после даты начала.\n- P: месяц после C."))
info("2.7",
     T("Produces the number the audit must explain: growth per day, in percent, per year, and its persistence. It "
       "becomes the TOTAL line of the bridge.",
       "Даёт число, которое должен объяснить аудит: рост в сутки, в процентах, за год и его устойчивость. Оно "
       "становится строкой TOTAL моста."),
     T("Nothing to enter: the app uses the main export and the periods from 2.6.",
       "Вводить ничего не нужно: приложение использует основную выгрузку и периоды из 2.6."))
info("2.8",
     T("The shape decides which causes are plausible: a step suggests a change or a price; a ramp suggests "
       "accumulation; a spike suggests an event; a seasonal pattern suggests nothing changed.",
       "Форма определяет, какие причины правдоподобны: ступенька указывает на изменение или цену; наклон - на "
       "накопление; всплеск - на событие; сезонность - на отсутствие изменений."),
     T("- Open the daily series (2.2 or the export) as a chart and compare with the same months of the previous year, "
       "if the export covers them.",
       "- Откройте дневной ряд (2.2 или выгрузку) в виде графика и сравните с теми же месяцами прошлого года, если "
       "выгрузка их покрывает."))

# ----------------------------------------------------------------------- 03
info("3.1",
     T("Rules out an apparent growth caused only by month length. Because the audit compares cost per day, the "
       "effect is zero unless someone compared monthly totals.",
       "Исключает кажущийся рост из-за длины месяца. Поскольку аудит сравнивает затраты в сутки, эффект равен нулю, "
       "если только кто-то не сравнивал месячные итоги."),
     T("- Compare the number of days of B and C. The effect is the monthly cost multiplied by the difference in days "
       "divided by the days of B.",
       "- Сравните число дней в B и C. Эффект равен месячным затратам, умноженным на разницу в днях и делённым на "
       "число дней B."))
info("3.2",
     T("A one-off purchase (a reservation) or an ended commitment changes the bill without any change in usage "
       "(ACC-02, ACC-03).",
       "Разовая покупка (резервирование) или закончившееся обязательство меняют счёт без изменения потребления "
       "(ACC-02, ACC-03)."),
     T("1. **Cost Management**, **Cost analysis**, check the **Scope** pill, a customizable view (**All views**), "
       "metric **Actual cost**, granularity **Monthly**.\n"
       "2. Date range: the custom range of period B. Open **Group by** and choose **Charge type**. **Download**, "
       "**CSV**. Repeat for period C.\n"
       "3. Repeat both downloads with **Group by** **Pricing model**.\n"
       "4. Upload the four files named as suggested. Charge types you will see: Usage, Purchase, Refund, "
       "Adjustment (and UnusedReservation or UnusedSavingsPlan in the Amortized view).",
       "1. **Cost Management**, **Cost analysis**, проверьте **Scope**, настраиваемый вид (**All views**), метрика "
       "**Actual cost**, детализация **Monthly**.\n"
       "2. Период: произвольный диапазон периода B. Откройте **Group by** и выберите **Charge type**. **Download**, "
       "**CSV**. Повторите для периода C.\n"
       "3. Повторите обе загрузки с **Group by** **Pricing model**.\n"
       "4. Загрузите четыре файла с предложенными именами. Типы начислений: Usage, Purchase, Refund, Adjustment (и "
       "UnusedReservation или UnusedSavingsPlan в виде Amortized)."))
info("3.3",
     T("Actual shows purchases when they are paid; Amortized spreads them over the term. A large gap in C points "
       "to a purchase (ACC-02).",
       "Actual показывает покупки в момент оплаты, Amortized распределяет их на срок. Большой разрыв в C указывает "
       "на покупку (ACC-02)."),
     T("1. **Cost Management**, **Cost analysis**, the same scope, view and months as in action 1.3.\n"
       "2. Press the down arrow next to the cost figure and choose **Amortized cost**. Granularity **Monthly**, "
       "**Group by** **None**, **Download**, **CSV**, upload.\n"
       "3. If **Amortized cost** is not offered, the scope has no amortized data (for an EA only the billing "
       "account scope has both datasets): record UNKNOWN in the scope record.",
       "1. **Cost Management**, **Cost analysis**, тот же охват, вид и месяцы, что в действии 1.3.\n"
       "2. Нажмите стрелку вниз рядом с показателем затрат и выберите **Amortized cost**. Детализация **Monthly**, "
       "**Group by** **None**, **Download**, **CSV**, загрузите.\n"
       "3. Если **Amortized cost** не предлагается, у охвата нет данных amortized (для EA оба набора есть только на "
       "охвате биллингового аккаунта): запишите UNKNOWN в записи охвата."))
info("3.4",
     T("An exhausted credit or a refund changes the invoice although usage is the same (ACC-04).",
       "Исчерпанный кредит или возврат меняют счёт при том же потреблении (ACC-04)."),
     T("- Refunds and adjustments: the file of 3.2 grouped by **Charge type** contains the lines Refund and "
       "Adjustment.\n"
       "- Credits are not part of Cost analysis; they are on the billing pages. MCA: **Cost Management + Billing**, "
       "the billing account, the billing profile, **Payment methods**, **Azure credits** (balance and "
       "transactions). EA: the billing account, **Credits + Commitments** (Azure Prepayment, and the Microsoft Azure "
       "Consumption Commitment, MACC). These pages need a billing role: Reader or higher for MCA, Enterprise "
       "administrator for EA.\n"
       "- Write the balance and the expiry date, or UNKNOWN if the page is not accessible.",
       "- Возвраты и корректировки: в файле 3.2 с группировкой **Charge type** есть строки Refund и Adjustment.\n"
       "- Кредиты не входят в Cost analysis; они на биллинговых страницах. MCA: **Cost Management + Billing**, "
       "биллинговый аккаунт, биллинговый профиль, **Payment methods**, **Azure credits** (остаток и операции). EA: "
       "биллинговый аккаунт, **Credits + Commitments** (Azure Prepayment и Microsoft Azure Consumption Commitment, "
       "MACC). Для этих страниц нужна биллинговая роль: Reader и выше для MCA, Enterprise administrator для EA.\n"
       "- Запишите остаток и срок действия либо UNKNOWN, если страница недоступна."))
info("3.5",
     T("A subscription or workspace that appeared between B and C adds cost that was simply not counted before "
       "(ACC-07). It is not an operational change.",
       "Подписка или workspace, появившиеся между B и C, добавляют затраты, которые раньше просто не учитывались "
       "(ACC-07). Это не операционное изменение."),
     T("Nothing to enter: the app compares subscriptions of B and C in the main export. Add the workspaces marked "
       "`APPEARED_IN_WINDOW` in 1.6 by hand.",
       "Вводить ничего не нужно: приложение сравнивает подписки B и C в основной выгрузке. Workspace с пометкой "
       "`APPEARED_IN_WINDOW` из 1.6 добавьте вручную."))
info("3.6",
     T("Higher unit price at unchanged usage is a price effect (ACC-05), not an operational change.",
       "Более высокая цена единицы при том же потреблении - ценовой эффект (ACC-05), а не операционное изменение."),
     T("- The app ranks meters by change per day; the column `EffectivePrice` of the export gives the unit price of "
       "B and C.\n- Typical case: Standard to Premium workspace tier, visible as `STANDARD_*` replaced by `PREMIUM_*` "
       "in the SKU list of 1.7. The current tier: portal, **Azure Databricks**, the workspace, **Overview**, "
       "**Pricing Tier**.",
       "- Приложение ранжирует счётчики по изменению в сутки; колонка `EffectivePrice` выгрузки даёт цену единицы "
       "в B и C.\n- Типичный случай: переход уровня workspace со Standard на Premium, виден как замена `STANDARD_*` "
       "на `PREMIUM_*` в списке SKU из 1.7. Текущий уровень: портал, **Azure Databricks**, workspace, **Overview**, "
       "**Pricing Tier**."))
info("3.7",
     T("A new version of the Databricks price list inside the window is a price change, not a usage change "
       "(ACC-05).",
       "Новая версия прайс-листа Databricks внутри окна - это изменение цены, а не потребления (ACC-05)."),
     T(f"- Source: `system.billing.list_prices`.\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.list_prices`.\n- {SQL_RUN_RU}"))
info("3.8",
     T("A change of the exchange rate between price currency and billing currency changes the bill without any "
       "change in usage (ACC-06). Late corrections shift costs between months (ACC-08).",
       "Изменение курса между валютой прайса и валютой счёта меняет счёт без изменения потребления (ACC-06). "
       "Поздние корректировки сдвигают затраты между месяцами (ACC-08)."),
     T("- Rate: open the main export in a spreadsheet and look at the header row for the exchange-rate column (its "
       "name depends on the agreement type, for example `ExchangeRatePricingToBilling` in MCA); compare its value "
       "for B and C. If the column does not exist, write UNKNOWN.\n"
       "- Corrections: re-run an old month (**Export selected dates**, action 1.1) into a separate export prefix "
       "and compare it with the first copy; count `RETRACTION` and `RESTATEMENT` in the result of 1.6.",
       "- Курс: откройте основную выгрузку в таблице и найдите в строке заголовка колонку курса (имя зависит от типа "
       "договора, например `ExchangeRatePricingToBilling` в MCA); сравните её значение для B и C. Если колонки нет, "
       "запишите UNKNOWN.\n"
       "- Корректировки: повторно запустите старый месяц (**Export selected dates**, действие 1.1) с другим "
       "префиксом выгрузки и сравните с первой копией; посчитайте `RETRACTION` и `RESTATEMENT` в результате 1.6."))
info("3.9",
     T("A consistency test of two independent views: the Azure bill and the Databricks cost model must move in "
       "the same direction (rule R8). A mismatch means a discount, a commitment or the scope distorts one of them.",
       "Проверка согласованности двух независимых видов: счёт Azure и модель затрат Databricks должны двигаться в "
       "одном направлении (правило R8). Расхождение означает, что скидка, обязательство или охват искажают один из "
       "них."),
     T("Nothing to enter: the app uses the export and the result of 2.5.",
       "Вводить ничего не нужно: приложение использует выгрузку и результат 2.5."))
info("3.10",
     T("The accounting lines remove from the total the part of the growth that is not operational. What remains "
       "is the part that has causes in the platform.",
       "Учётные строки убирают из итога часть роста, не связанную с эксплуатацией. Остаётся часть, у которой есть "
       "причины в платформе."),
     T("- Take the figures from 3.1-3.8; write 0 where a test had no effect.",
       "- Возьмите числа из 3.1-3.8; пишите 0, где тест не показал эффекта."))
info("3.11",
     T("Operational growth is the number that steps 04-07 must explain.",
       "Операционный рост - число, которое должны объяснить шаги 04-07."),
     T("Nothing to enter: the app subtracts the accounting lines from TOTAL.",
       "Вводить ничего не нужно: приложение вычитает учётные строки из TOTAL."))

# ----------------------------------------------------------------------- 04
info("4.1",
     T("Shows what was billed more, in five mutually exclusive views: subscription, service, meter, resource group, "
       "resource. The totals of all views must be equal; a difference indicates a filtering error.",
       "Показывает, что выставлено больше, в пяти взаимоисключающих разрезах: подписка, сервис, счётчик, группа "
       "ресурсов, ресурс. Итоги всех разрезов должны совпадать; разница указывает на ошибку фильтрации."),
     T("Nothing to enter: the app uses the main export and B and C from settings, writes five files "
       "`delta_by_*` and one evidence row for each.\n"
       "If a grouping is skipped because the export has no such column (EA and MCA schemas differ), the warning "
       "names it; the other groupings are still written.",
       "Вводить ничего не нужно: приложение использует основную выгрузку и B и C из настроек, записывает пять "
       "файлов `delta_by_*` и по одной строке доказательств на каждый.\n"
       "Если группировка пропущена из-за отсутствия колонки (схемы EA и MCA различаются), предупреждение называет "
       "её; остальные группировки всё равно записываются."))
info("4.2",
     T("Links the Databricks workspaces to the Azure resources that are billed under other names: virtual machines "
       "sit in the managed resource group, not in the workspace.",
       "Связывает workspace Databricks с ресурсами Azure, которые выставляются под другими именами: виртуальные "
       "машины находятся в managed resource group, а не в workspace."),
     T("- Azure CLI (read-only): install it once (Microsoft documentation, *Install Azure CLI*), open a terminal and "
       "run `az login`; a browser window opens, sign in with the work account. `az account list --output table` must "
       "list the subscriptions of the audit. With several tenants use `az login --tenant <tenant ID>`. Then press "
       "**Run**.\n"
       "- Without the CLI: portal, search **Azure Databricks**, open each workspace, **Overview**, copy "
       "**Managed Resource Group** and the subscription; upload the table in the next action.",
       "- Azure CLI (только чтение): установите один раз (документация Microsoft, *Install Azure CLI*), откройте "
       "терминал и выполните `az login`; откроется браузер, войдите рабочей учётной записью. `az account list "
       "--output table` должен показать подписки аудита. Если арендаторов несколько, используйте `az login --tenant "
       "<tenant ID>`. Затем нажмите **Run**.\n"
       "- Без CLI: портал, поиск **Azure Databricks**, откройте каждый workspace, **Overview**, скопируйте **Managed "
       "Resource Group** и подписку; загрузите таблицу в следующем действии."))
info("4.2b",
     T("A fallback for the previous action, if the Azure CLI is not available.",
       "Запасной вариант предыдущего действия, если Azure CLI недоступен."),
     T("- CSV `workspace_rg_map.csv` with one line per workspace: workspace name, subscription, managed resource "
       "group, dependent resource groups (storage, network, monitoring).",
       "- CSV `workspace_rg_map.csv` по одной строке на workspace: имя workspace, подписка, managed resource group, "
       "зависимые группы ресурсов (хранилище, сеть, мониторинг)."))
info("4.3",
     T("Every big line must have exactly one category, otherwise the bridge cannot close and the same cost is "
       "counted twice.",
       "У каждой крупной строки должна быть ровно одна категория, иначе мост не сойдётся, а одни и те же затраты "
       "посчитаются дважды."),
     T("- Take the lines from the `delta_by_*` files of 4.1 and the map of 4.2. A managed resource group is a "
       "hint, not proof of ownership.",
       "- Берите строки из файлов `delta_by_*` из 4.1 и карты 4.2. Managed resource group - подсказка, а не "
       "доказательство владения."))

# ----------------------------------------------------------------------- 05
info("5.1",
     T("Separates more usage (volume) from a higher price (rate) per SKU. A SKU that disappears while a similar one "
       "appears is a mix shift: usage only moved.",
       "Разделяет рост потребления (объём) и рост цены (ставка) по SKU. SKU, исчезающий при появлении похожего, - "
       "смещение состава: потребление лишь переместилось."),
     T(f"- Source: `system.billing.usage` with `system.billing.list_prices`.\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.usage` и `system.billing.list_prices`.\n- {SQL_RUN_RU}"))
info("5.2",
     T("Shows whether the growth is local (one workspace, probably one team's change) or platform-wide.",
       "Показывает, локален ли рост (один workspace, вероятно изменение одной команды) или охватывает платформу."),
     T(f"- Source: `system.billing.usage`.\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.usage`.\n- {SQL_RUN_RU}"))
info("5.3",
     T("Finds the objects (jobs, pipelines, warehouses, clusters) that explain the growth. The list continues until "
       "90% of the modeled growth is covered (rule R4).",
       "Находит объекты (jobs, pipelines, warehouses, clusters), объясняющие рост. Список продолжается, пока не "
       "покрыто 90% модельного роста (правило R4)."),
     T(f"- Source: `system.billing.usage` (columns `usage_metadata`, `identity_metadata`).\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.usage` (колонки `usage_metadata`, `identity_metadata`).\n- {SQL_RUN_RU}"))
info("5.4",
     T("The start day of an object must match the overall start day (within 2 days). Otherwise it is probably not "
       "the main cause.",
       "День начала роста объекта должен совпадать с общим днём начала (в пределах 2 дней). Иначе это, вероятно, "
       "не главная причина."),
     T("- The app fills `object_ids` with the objects of 5.3 up to 90% coverage; check the list and run.\n"
       f"- {SQL_RUN_EN}",
       "- Приложение заполняет `object_ids` объектами из 5.3 до покрытия 90%; проверьте список и запустите.\n"
       f"- {SQL_RUN_RU}"))
info("5.5",
     T("Cost without an object ID or required tags cannot be assigned to an owner; its share goes to step 07.",
       "Затраты без ID объекта или обязательных тегов нельзя отнести к владельцу; их доля уходит в шаг 07."),
     T(f"- Source: `system.billing.usage` (`custom_tags`, `usage_metadata`).\n- {SQL_RUN_EN}\n- Parameter "
       "`required_tag`: the tag key your company requires, for example `cost_center`.",
       f"- Источник: `system.billing.usage` (`custom_tags`, `usage_metadata`).\n- {SQL_RUN_RU}\n- Параметр "
       "`required_tag`: ключ тега, обязательный в вашей компании, например `cost_center`."))
info("5.6",
     T("New products and SKUs near the start date are frequent causes of growth.",
       "Новые продукты и SKU около даты начала - частая причина роста."),
     T(f"- Source: `system.billing.usage`.\n- {SQL_RUN_EN}",
       f"- Источник: `system.billing.usage`.\n- {SQL_RUN_RU}"))
info("5.7",
     T("Candidates are the objects that step 06 will investigate; each one is entered with its growth at list price.",
       "Кандидаты - объекты, которые исследует шаг 06; каждый вносится с ростом по прайсу."),
     T("- Take the objects and growth values from the result of 5.3.",
       "- Берите объекты и значения роста из результата 5.3."))

# ----------------------------------------------------------------------- 06
info("6.1",
     T("A driver card keeps the whole proof of one cause in one place: what changed, when, how much, the evidence "
       "and the alternatives that were disproved (rule R9).",
       "Карточка драйвера хранит всё доказательство одной причины в одном месте: что изменилось, когда, "
       "насколько, доказательства и опровергнутые альтернативы (правило R9)."),
     T("Nothing to enter except the driver name: the app creates the card from the template.",
       "Вводить нужно только имя драйвера: карточка создаётся из шаблона."))
info("6.2",
     T("Answers two questions for every driver: how much (frequency times unit cost, or volume times price) and "
       "what changed (a dated event).",
       "Отвечает на два вопроса по каждому драйверу: сколько (частота на стоимость запуска либо объём на цену) и "
       "что изменилось (событие с датой)."),
     T("- Cost and frequency: `system.billing.usage`, `system.lakeflow.*`, `system.compute.*`, `system.query.history`.\n"
       "- Change events: configuration history in `system.compute.clusters`, `system.compute.warehouses`, "
       "`system.lakeflow.jobs`; `system.access.audit` for who and when.\n"
       f"- {SQL_RUN_EN}",
       "- Стоимость и частота: `system.billing.usage`, `system.lakeflow.*`, `system.compute.*`, `system.query.history`.\n"
       "- События изменений: история конфигурации в `system.compute.clusters`, `system.compute.warehouses`, "
       "`system.lakeflow.jobs`; `system.access.audit` показывает кто и когда.\n"
       f"- {SQL_RUN_RU}"))
info("6.3",
     T("Some change events are outside the system tables: a release, a Git commit, a ticket, an Azure resource "
       "change.",
       "Часть событий изменений находится вне системных таблиц: релиз, коммит Git, тикет, изменение ресурса Azure."),
     T("- Azure change: portal, open the resource group (or the resource) and choose **Activity log** in the left "
       "menu; the page opens pre-filtered to that object. Set **Timespan** to a custom range around the start date "
       "(a short range keeps the export fast), use **Add filter** (for example *Operation*) to narrow it, and press "
       "**Download as CSV**. The portal keeps the activity log for 90 days: a change older than that is not here "
       "(write UNKNOWN and use `system.access.audit`).\n"
       "- Release or code: the Git or deployment history of the object; export the page as PDF or text.",
       "- Изменение в Azure: портал, откройте группу ресурсов (или ресурс) и выберите **Activity log** в левом меню; "
       "страница откроется с фильтром по этому объекту. Задайте **Timespan** - произвольный диапазон вокруг даты "
       "начала (короткий диапазон ускоряет выгрузку), сузьте через **Add filter** (например *Operation*) и "
       "нажмите **Download as CSV**. Портал хранит Activity log 90 дней: более старое изменение здесь не найти "
       "(запишите UNKNOWN и используйте `system.access.audit`).\n"
       "- Релиз или код: история Git или развёртывания объекта; сохраните страницу как PDF или текст."))

# ----------------------------------------------------------------------- 07
info("7.1",
     T("Each confirmed cause needs a person who can accept or reject the fix.",
       "Каждой подтверждённой причине нужен человек, который может принять или отклонить исправление."),
     T("- Databricks: the column `sample_run_as` of 5.3, the job or workspace owner, tags `owner`, `cost_center`, "
       "`application`.\n- Azure: tags on the resource group.",
       "- Databricks: колонка `sample_run_as` из 5.3, владелец job или workspace, теги `owner`, `cost_center`, "
       "`application`.\n- Azure: теги группы ресурсов."))
info("7.2",
     T("Shared cost can be split only by a provable key. An estimated share would turn the report into an "
       "opinion.",
       "Общие затраты можно делить только по доказуемому ключу. Оценочная доля превратит отчёт в мнение."),
     T("- A key is a measured quantity: usage share, bytes, requests. Take it from the system tables or from the "
       "owners' reports.",
       "- Ключ - измеренная величина: доля потребления, байты, запросы. Берите её из системных таблиц или отчётов "
       "владельцев."))
info("7.3",
     T("Quantifies the part of the growth that cannot be assigned because of missing tags or IDs, and explains why.",
       "Количественно оценивает часть роста, которую нельзя отнести из-за отсутствия тегов или ID, и объясняет "
       "почему."),
     T("- Take the share from the result of 5.5.",
       "- Возьмите долю из результата 5.5."))
info("7.5",
     T("The unexplained part shows how much of the growth the audit could not attribute. Up to 10% of the total is "
       "acceptable (rule R4).",
       "Необъяснённая часть показывает, сколько роста аудит не смог объяснить. До 10% от итога допустимо "
       "(правило R4)."),
     T("Nothing to enter: the app computes it from the bridge.",
       "Вводить ничего не нужно: приложение считает её по мосту."))

# ----------------------------------------------------------------------- 08
info("8.1",
     T("A result that cannot be repeated is not evidence. The repetition proves that the numbers come from the "
       "saved files and parameters.",
       "Результат, который нельзя повторить, не является доказательством. Повтор подтверждает, что числа "
       "получены из сохранённых файлов и параметров."),
     T("Nothing to enter: the app repeats every evidence row; SQL rows need the Databricks connection.",
       "Вводить ничего не нужно: приложение повторяет каждую строку доказательств; для строк SQL нужно "
       "подключение к Databricks."))
info("8.3",
     T("Other views of the cost (Amortized, the Databricks usage dashboard, IBM) confirm the main numbers. Their "
       "differences are explained and never added.",
       "Другие виды затрат (Amortized, дашборд использования Databricks, IBM) подтверждают основные числа. Их "
       "расхождения объясняются и никогда не складываются."),
     T("- Amortized: the file of 3.3.\n"
       "- Usage dashboard: open `accounts.azuredatabricks.net` and sign in as an **account admin**. Click the "
       "**Usage** icon in the left menu. Choose the months of the window and switch the **$USD/DBU** picker to "
       "compare cost and DBUs. The dollar figures are an estimate from list prices: they can be adjusted in the "
       "settings panel (kebab menu at the top right of the page). **Download** (top right of the graph) gives the "
       "aggregated data; the settings panel, **Download** at the bottom, gives all usage by date. The page does not "
       "show every product: Databricks recommends the system tables for complete usage.\n"
       "- IBM: the actions 8.4-8.8, if the licence exists.",
       "- Amortized: файл из 3.3.\n"
       "- Дашборд использования: откройте `accounts.azuredatabricks.net` и войдите как **account admin**. Нажмите "
       "значок **Usage** в левом меню. Выберите месяцы окна и переключайте **$USD/DBU**, чтобы сравнить затраты и "
       "DBU. Суммы в долларах - оценка по прайсу: их можно изменить в панели настроек (меню из трёх точек справа "
       "вверху страницы). **Download** (справа вверху графика) даёт агрегированные данные; панель настроек, "
       "**Download** внизу, даёт всё потребление по датам. Страница показывает не все продукты: Databricks "
       "рекомендует системные таблицы для полных данных.\n"
       "- IBM: действия 8.4-8.8, если есть лицензия."))

# ----------------------------------------------------------------------- 09
info("9.1",
     T("The bridge in the report must be identical to the working file, otherwise the report cannot be checked.",
       "Мост в отчёте должен быть идентичен рабочему файлу, иначе отчёт нельзя проверить."),
     T("Nothing to enter: the app converts the bridge into a table for the report.",
       "Вводить ничего не нужно: приложение превращает мост в таблицу для отчёта."))


# ----------------------------------------------------------------------- reference page
HEAD = {
    "en": ("# 15 · Data and metrics: why and how\n\n"
           "<!-- plain -->\n> **Overview.** For every number or file in the playbook: why it is needed and how to obtain it. "
           "The same text is shown inside each action of the application. Read-only access is enough for everything "
           "listed here.\n<!-- /plain -->\n\n"
           "Generated from `webapp/metrics.py`; do not edit by hand (`python -m webapp.plain_docs` rewrites it).\n"),
    "ru": ("# 15 · Данные и метрики: зачем и как получить\n\n"
           "<!-- plain -->\n> **Обзор.** Для каждого числа или файла плейбука: зачем он нужен и как его получить. "
           "Тот же текст показан внутри каждого действия приложения. Для всего перечисленного достаточно доступа "
           "только на чтение.\n<!-- /plain -->\n\n"
           "Создано из `webapp/metrics.py`; вручную не редактировать (`python -m webapp.plain_docs` перезапишет).\n"),
}
WHY_LABEL = {"en": "Why", "ru": "Зачем"}
HOW_LABEL = {"en": "How to obtain", "ru": "Как получить"}


def reference_doc(lang: str, steps: list[dict]) -> str:
    out = [HEAD[lang]]
    for s in steps:
        rows = [a for a in s["actions"] if a["id"] in INFO]
        if not rows:
            continue
        out.append(f"\n## {s['id']} · {s['title'][lang]}\n")
        for a in rows:
            why, how = INFO[a["id"]]
            out.append(f"### {a['id']} {a['title'][lang]}\n")
            out.append(f"**{WHY_LABEL[lang]}.** {why[lang]}\n")
            if how[lang]:
                out.append(f"**{HOW_LABEL[lang]}.**\n\n{how[lang]}\n")
    return "\n".join(out).rstrip() + "\n"
