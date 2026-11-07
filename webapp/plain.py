"""Plain-language texts of the playbook (EN / RU).

steps.py keeps the structure (ids, kinds, tools, files); the human-readable wording lives here and is applied on
import by `apply()`. Technical terms are not defined inline: they are linked to the glossary automatically
(reference/14_glossary.md). A test requires every step and action to have an entry here.

Register: professional and precise, written for first-time practitioners; no colloquialisms, no oversimplification.
Text conventions: blank line = new paragraph; lines starting with "- " or "1. " = list; `code`, **bold**, *italic*.
"""
from __future__ import annotations

from . import metrics


def T(en: str, ru: str) -> dict:
    return {"en": en, "ru": ru}


STEP: dict[str, dict] = {}
ACT: dict[str, tuple[dict, dict]] = {}


def step(id_: str, **fields: dict) -> None:
    STEP[id_] = fields


def act(id_: str, title: dict, text: dict | None = None) -> None:
    ACT[id_] = (title, text or T("", ""))


# ======================================================================= 00
step("00",
     question=T("What exactly are we checking, for which period, and who asked?",
                "Что именно мы проверяем, за какой период и кто это заказал?"),
     goal=T("A short written description of the audit: the question, the slice of Azure you look at, the periods "
            "and the currency - approved by the person who ordered the audit.",
            "Короткое письменное описание аудита: вопрос, какой кусок Azure смотрим, периоды и валюта - "
            "утверждённое тем, кто заказал аудит."),
     gate=T("**G0.** The audit owner has approved the question, scope and periods, and you have written them down. "
            "Do not ask for any data before this.",
            "**G0.** Владелец аудита утвердил вопрос, охват и периоды, и всё записано. До этого не запрашивайте "
            "никаких данных."),
     plain=T("The audit starts from an observation: the Azure Databricks bill has increased. This step converts the observation into a precise, approvable question: which bill, which subscriptions, which months, which currency.\n\nThe step is documentation work, but it prevents the most expensive error of an audit. A change of scope after data collection invalidates every number collected so far.",
             "Аудит начинается с наблюдения: счёт за Azure Databricks вырос. Этот шаг превращает наблюдение в точный вопрос, который можно утвердить: какой счёт, какие подписки, какие месяцы, какая валюта.\n\nШаг носит документарный характер, но предотвращает самую дорогую ошибку аудита. Изменение охвата после сбора данных обесценивает все уже собранные числа."),
     result=T("a filled-in `scope_record.md` (sections 1-4 and 8) and the periods saved in the app.",
              "заполненный `scope_record.md` (разделы 1-4 и 8) и периоды, сохранённые в приложении."),
     tip=T("Use full months only. The current month is incomplete and must stay outside the window.",
           "Используйте только полные месяцы. Текущий месяц не завершён и должен остаться вне окна."))

act("0.1", T("Choose the months to compare and the currency", "Выберите месяцы для сравнения и валюту"),
    T("Pick the **window**: the last 10-12 full months. Inside it choose three periods:\n\n"
      "- **B (before)** - a calm period before the growth, at least 28 days. Two full months is a good default.\n"
      "- **C (after)** - the first full month where the cost is already higher.\n"
      "- **P (check)** - the month after C. It shows whether the growth stayed.\n\n"
      "The end date of a period is the first day **after** it (so January is 1 Jan to 1 Feb). The values are provisional: step 02 refines them from the actual data. The application copies them into every tool and SQL query.",
      "Выберите **окно**: последние 10-12 полных месяцев. Внутри него задайте три периода:\n\n"
      "- **B (до)** - спокойный период до роста, не меньше 28 дней. Хорошо подходят два полных месяца.\n"
      "- **C (после)** - первый полный месяц, где затраты уже выше.\n"
      "- **P (проверка)** - месяц после C. Он показывает, удержался ли рост.\n\n"
      "Конец периода - это первый день **после** него (январь: с 1 января по 1 февраля). Значения предварительные: "
      "шаг 02 уточнит их по фактическим данным. Приложение подставляет их в каждый инструмент и SQL-запрос."))
act("0.2", T("Fill in the scope record", "Заполните запись об охвате"),
    T("One file, four blocks, in this order:\n\n"
      "1. **Section 1 - the trigger.** Who saw the growth, where (the invoice, Cost Analysis, a Databricks dashboard, an "
      "IBM report) and which number. Then the question: *\"Azure Actual Cost for scope S rose from X per day (B) to Y "
      "per day (C). Which causes explain at least 90% of it?\"* A question like this tells you when you are done.\n"
      "2. **Section 2 - the scope.** The billing account, subscriptions, Databricks workspaces with regions, and the "
      "resource groups they use (storage, network, monitoring). The contract type (EA, MCA or MPA) and any "
      "commitments or credits with their dates.\n"
      "3. **Sections 3-4 - the rules and the sources.** Rules you will deviate from, or *none*. For each data source "
      "(Azure exports, Cost Analysis, Databricks system tables, IBM tools): **OK**, **DENIED** or **UNKNOWN**.\n"
      "4. **Section 8 - the approval.** The name and date of the person who approved the scope. Then tick the gate "
      "check G0. This is a real stop: no data requests before approval.",
      "Один файл, четыре блока по порядку:\n\n"
      "1. **Раздел 1 - повод.** Кто увидел рост, где (счёт, Cost Analysis, дашборд Databricks, отчёт IBM) и какое "
      "число. Затем вопрос: *«Azure Actual Cost для охвата S вырос с X в сутки (B) до Y в сутки (C). Какие причины "
      "объясняют не меньше 90%?»* Такой вопрос подсказывает, когда вы закончили.\n"
      "2. **Раздел 2 - охват.** Биллинговый аккаунт, подписки, workspace Databricks с регионами и группы ресурсов, "
      "которыми они пользуются (хранилище, сеть, мониторинг). Тип договора (EA, MCA или MPA) и обязательства или "
      "кредиты с датами.\n"
      "3. **Разделы 3-4 - правила и источники.** Правила, от которых отступаете, или *none*. Для каждого "
      "источника данных (выгрузки Azure, Cost Analysis, системные таблицы Databricks, инструменты IBM): **OK**, "
      "**DENIED** или **UNKNOWN**.\n"
      "4. **Раздел 8 - утверждение.** Имя и дата того, кто утвердил охват. Затем отметьте контрольную точку G0. Это "
      "настоящая остановка: до утверждения данные не запрашиваем."))
act("0.3", T("Notes for this step", "Заметки к шагу"),
    T("A free place for observations, decisions and open questions. Anything you would want to remember in a "
      "month goes here.",
      "Свободное место для наблюдений, решений и открытых вопросов. Сюда пишите всё, что захотите вспомнить через "
      "месяц."))

# ======================================================================= 01
step("01",
     question=T("Can we trust the data before we analyze it?",
                "Можно ли доверять данным, прежде чем их анализировать?"),
     goal=T("One complete, clean data set per source: no missing months, no duplicates, one currency, and prices "
            "that match usage.",
            "Один полный и чистый набор данных на источник: без пропущенных месяцев, без дублей, в одной валюте, "
            "с ценами, которые сходятся с потреблением."),
     gate=T("**G1.** The checks R6 (the export agrees with Cost Analysis) and R7 (prices match usage) pass. If some "
            "data fails, you exclude it and write it down as a limitation in section 5.",
            "**G1.** Проверки R6 (выгрузка совпадает с Cost Analysis) и R7 (цены совпадают с потреблением) пройдены. "
            "Если часть данных не проходит, исключите её и запишите как ограничение в разделе 5."),
     plain=T("This step downloads the data and verifies its integrity. Most incorrect conclusions in cost audits originate in the input, not in the analysis: a month exported twice, two currencies in one column, a day without records.\n\nYou download one detailed export from the Azure portal and one summary report for cross-checking, then run read-only SQL checks in Databricks. The application calculates the reconciliation and reports whether it passes.",
             "На этом шаге данные загружаются и проверяются на целостность. Большинство неверных выводов в аудитах затрат возникает из-за входных данных, а не анализа: месяц выгружен дважды, в одной колонке две валюты, за день нет записей.\n\nВы скачиваете из портала Azure одну детальную выгрузку и один сводный отчёт для сверки, затем выполняете SQL-проверки в Databricks (только чтение). Приложение рассчитывает сверку и сообщает, пройдена ли она."),
     result=T("the main export file saved in the audit, a green R6 reconciliation, and a list of SKUs excluded "
              "from the model.",
              "основной файл выгрузки в аудите, зелёная сверка R6 и список SKU, исключённых из модели."),
     tip=T("Export one run per month. Never concatenate runs: overlapping runs double the cost.",
           "Выгружайте один запуск на месяц. Не объединяйте запуски: перекрывающиеся запуски удваивают затраты."))

act("1.1", T("Upload the main cost export", "Загрузите основную выгрузку затрат"),
    T('Download the **Actual cost** export of the whole window, one run per month, and upload it as one CSV. It becomes the main export for all later steps. The steps below show where to click.',
      'Скачайте выгрузку **Actual cost** за всё окно, один запуск на месяц, и загрузите её одним CSV. Она становится основной выгрузкой для всех следующих шагов. Ниже показано, где нажимать.'))
act("1.2", T("Upload the export manifests", "Загрузите манифесты выгрузок"),
    T('Upload the `manifest.json` of each export run, or one `export_manifest.md` with the run IDs.',
      'Загрузите `manifest.json` каждого запуска выгрузки либо один `export_manifest.md` с ID запусков.'))
act("1.3", T("Download the monthly totals from Cost Analysis", "Скачайте месячные итоги из Cost Analysis"),
    T('Download the monthly totals from Cost Analysis: the **second opinion** that the large export is checked against.',
      'Скачайте месячные итоги из Cost Analysis: это **второе мнение**, с которым сверяется большая выгрузка.'))
act("1.4", T("Calculate monthly totals from the export", "Посчитайте месячные итоги по выгрузке"),
    T("Press Run. The app adds up your export by month and shows the total and the cost per day for each month. "
      "These are the numbers that the next action compares with Cost Analysis.",
      "Нажмите «Запустить». Приложение сложит выгрузку по месяцам и покажет итог и затраты в сутки для каждого "
      "месяца. Именно эти числа следующее действие сравнит с Cost Analysis."))
act("1.5", T("Check that the export matches Cost Analysis (rule R6)", "Проверьте, что выгрузка совпадает с Cost Analysis (правило R6)"),
    T("Press Run. For each month the app compares your totals with the Cost Analysis download. The difference must "
      "be **0.5% or less**. If it is bigger, the usual causes are a duplicated export run or a missing day: fix the "
      "export, do not explain the difference away. The largest difference is written into section 5 for you.",
      "Нажмите «Запустить». Для каждого месяца приложение сравнивает ваши итоги с загрузкой из Cost Analysis. "
      "Разница должна быть **не больше 0,5%**. Если больше, обычно виноваты задвоенный запуск выгрузки или "
      "пропущенный день: исправьте выгрузку, а не объясняйте разницу. Наибольшее расхождение запишется в раздел 5 "
      "само."))
act("1.6", T("Check that Databricks has data for every day", "Проверьте, что в Databricks есть данные за каждый день"),
    T("This SQL runs in Databricks (read-only). It counts, for every month, the days that have usage records. "
      "**Pass:** `days_with_data` equals `days_in_month` everywhere. The second query shows which workspaces "
      "appeared or disappeared during the window - note them for step 03. You can run it from the app or copy it "
      "to your Databricks editor and upload the CSV.",
      "Этот SQL выполняется в Databricks (только чтение). Он считает для каждого месяца дни, в которые есть "
      "записи потребления. **Норма:** `days_with_data` равно `days_in_month` везде. Второй запрос показывает, "
      "какие workspace появились или исчезли за окно - запомните их для шага 03. Запустите его из приложения или "
      "скопируйте в редактор Databricks и загрузите CSV."))
act("1.7", T("List the units and SKUs in use", "Составьте список единиц и SKU"),
    T("This SQL lists every product (SKU) and the unit its quantity is measured in. Use it as a map. Remember "
      "one rule for the whole audit: **never add quantities that are measured in different units** (DBU, GB, "
      "hours).",
      "Этот SQL перечисляет все продукты (SKU) и единицу, в которой измерено их количество. Пользуйтесь им как "
      "картой. И запомните правило на весь аудит: **никогда не складывайте количества в разных единицах** (DBU, "
      "ГБ, часы)."))
act("1.8", T("Check that every usage record has exactly one price (rule R7)", "Проверьте, что у каждой записи ровно одна цена (правило R7)"),
    T("To model the cost in Databricks, each usage row is matched with a price. This SQL checks the match. A SKU "
      "with a verdict that starts with `FAIL_` has a broken price match: **leave it out** of every money "
      "conclusion and list it in section 5 as a limitation.",
      "Чтобы смоделировать затраты в Databricks, каждой строке потребления подбирается цена. Этот SQL проверяет "
      "подбор. SKU с вердиктом на `FAIL_` имеет сломанный подбор цены: **исключите его** из любых денежных "
      "выводов и запишите в раздел 5 как ограничение."))
act("1.9", T("Write the data-quality summary", "Запишите итог по качеству данных"),
    T("In section 4 note, for each region, whether the system tables you need are available (in Databricks: "
      "*Catalog Explorer → system*). In section 5 write the results of all the checks above and every limitation "
      "that you carry forward.",
      "В разделе 4 отметьте для каждого региона, доступны ли нужные системные таблицы (в Databricks: *Catalog "
      "Explorer → system*). В разделе 5 запишите результаты всех проверок выше и каждое ограничение, которое "
      "переносите дальше."))
# ======================================================================= 02
step("02",
     question=T("Did the bill really grow? By how much per day, and since which day?",
                "Вырос ли счёт на самом деле? На сколько в сутки и с какого дня?"),
     goal=T("Prove the growth in the real billed amounts, measure it per day, find the day it started and fix the "
            "final periods B, C and P.",
            "Доказать рост в реально выставленных суммах, измерить его в сутки, найти день начала и зафиксировать "
            "итоговые периоды B, C и P."),
     gate=T("**G2.** The growth per day is above zero in Azure Actual and you described its shape. If it is zero or "
            "negative, the \"growth\" is only how the numbers are shown: record that in section 6, do step 03, mark "
            "steps 04-07 as not applicable and go to step 09.",
            "**G2.** Рост в сутки больше нуля в Azure Actual, и вы описали его форму. Если он нулевой или "
            "отрицательный, «рост» - лишь способ показа цифр: запишите это в разделе 6, сделайте шаг 03, отметьте "
            "шаги 04-07 как неприменимые и перейдите к шагу 09."),
     plain=T("This step confirms that the increase is real and quantifies it. Months contain 28 to 31 days, so a longer month appears more expensive without any change in consumption. All comparisons therefore use cost per day.\n\nThe application builds the monthly table, identifies the day the cost level changed, and calculates the additional cost per day, per month and per year at the new level. The final periods B, C and P are then fixed from the actual onset date.",
             "На этом шаге подтверждается, что рост реален, и выполняется его количественная оценка. В месяцах от 28 до 31 дня, поэтому длинный месяц выглядит дороже без изменения потребления. Все сравнения выполняются по затратам в сутки.\n\nПриложение строит помесячную таблицу, определяет день смены уровня затрат и рассчитывает дополнительные затраты в сутки, в месяц и в год на новом уровне. Затем по фактической дате начала фиксируются итоговые периоды B, C и P."),
     result=T("the growth in money per day and per year, the start date, the shape of the growth, and the total "
              "line of the delta bridge.",
              "рост в деньгах за сутки и за год, дата начала, форма роста и итоговая строка моста дельты."),
     tip=T("If the increase is a one-off excursion shorter than 14 days, record it as a spike, not as a trend.",
           "Если рост - разовое отклонение короче 14 дней, зафиксируйте его как всплеск, а не как тренд."))

act("2.1", T("Build the monthly table with cost per day", "Постройте таблицу по месяцам с затратами в сутки"),
    T("Press Run. You get one row per month: the total, the number of days and the cost per day. Use the full "
      "scope without any service filter.",
      "Нажмите «Запустить». Получите по строке на месяц: итог, число дней и затраты в сутки. Берите полный охват "
      "без фильтра по сервису."))
act("2.2", T("Download daily costs (optional)", "Скачайте суточные затраты (необязательно)"),
    T('Needed only if the main export does not cover all days: download daily Actual cost around the suspected change.',
      'Нужно, только если основная выгрузка не покрывает все дни: скачайте дневные затраты Actual вокруг предполагаемого изменения.'))
act("2.3", T("Find the day the growth started (rule R5)", "Найдите день начала роста (правило R5)"),
    T("Press Run. The app looks for the first day when the cost moved to a higher level and **stayed there for "
      "14 days or more**. A shorter rise is called a spike. Write the date (or *spike only*) in section 6.",
      "Нажмите «Запустить». Приложение ищет первый день, когда затраты ушли на более высокий уровень и "
      "**удержались там 14 дней и больше**. Более короткий подъём называется всплеском. Запишите дату (или "
      "*только всплеск*) в раздел 6."))
act("2.4", T("Cross-check the start day in Databricks", "Сверьте день начала в Databricks"),
    T("The same question asked from the Databricks side: on which day did the modeled cost rise? The two dates "
      "should be within **one day** of each other. If they are far apart, something other than Databricks is "
      "moving the bill - keep that in mind for step 04.",
      "Тот же вопрос со стороны Databricks: в какой день вырос модельный расчёт? Две даты должны отличаться "
      "**не больше чем на день**. Если разница большая, счёт двигает что-то помимо Databricks - запомните это для "
      "шага 04."))
act("2.5", T("Get the monthly modeled cost by SKU", "Получите месячный модельный расчёт по SKU"),
    T("This SQL gives the monthly cost of each Databricks product (SKU). Several later checks need it, so run "
      "it now.",
      "Этот SQL даёт месячную стоимость каждого продукта Databricks (SKU). Он нужен нескольким следующим "
      "проверкам, поэтому запустите его сейчас."))
act("2.6", T("Fix the final periods B, C and P (rule R2)", "Зафиксируйте итоговые периоды B, C и P (правило R2)"),
    T("Now that you know the start day, set the periods properly: **B** - at least 28 stable days before it; "
      "**C** - the first full month on the higher level; **P** - the month after C. Save them: every later "
      "calculation uses these dates.",
      "Теперь, когда известен день начала, задайте периоды окончательно: **B** - не меньше 28 стабильных дней "
      "до него; **C** - первый полный месяц на повышенном уровне; **P** - месяц после C. Сохраните: все "
      "дальнейшие расчёты используют эти даты."))
act("2.7", T("Calculate the size of the growth", "Посчитайте размер роста"),
    T("Press Run. The app calculates how much more you pay now: in money per day, as a percentage, per year at "
      "the new level, and whether it persisted in P. It writes the result into section 6 and fills the **TOTAL** "
      "line of the delta bridge - the number everything else must add up to.",
      "Нажмите «Запустить». Приложение считает, на сколько больше вы платите сейчас: в деньгах за сутки, в "
      "процентах, за год на новом уровне и удержался ли рост в P. Результат записывается в раздел 6, и "
      "заполняется строка **TOTAL** моста дельты - число, к которому должно сойтись всё остальное."))
act("2.8", T("Describe the shape of the growth", "Опишите форму роста"),
    T("Look at the daily chart and choose: **step** (a one-time jump), **ramp** (a steady climb), **spike** (a "
      "short peak) or **seasonal** (it repeats every year - compare with last year if you have the data). Write "
      "it in section 6 together with both start dates.",
      "Посмотрите на суточный график и выберите: **ступенька** (разовый скачок), **рампа** (постепенный подъём), "
      "**всплеск** (короткий пик) или **сезонность** (повторяется каждый год - сравните с прошлым годом, если "
      "есть данные). Запишите в раздел 6 вместе с обеими датами начала."))
act("2.9", T("Monthly analyzer (optional)", "Помесячный анализатор (необязательно)"),
    T("A helper that builds ready monthly reports from the Azure export and from the result of 2.2. The two "
      "sources are kept separate on purpose: they are never added together.",
      "Помощник, который строит готовые месячные отчёты из выгрузки Azure и результата 2.2. Два источника "
      "намеренно хранятся раздельно: их нельзя складывать."))
# ======================================================================= 03
step("03",
     question=T("How much of the growth is just accounting, not more work being done?",
                "Какая часть роста - просто учёт, а не новая работа?"),
     goal=T("Separate the changes that come from calendars, purchases, credits, currency, scope and prices from "
            "real growth in consumption - before you look at any workload.",
            "Отделить изменения от календаря, покупок, кредитов, курса, охвата и цен от настоящего роста "
            "потребления - до того, как смотреть на какие-либо нагрузки."),
     gate=T("**G3.** Each test is closed as pass, effect measured or not applicable, and the *operational* growth "
            "is calculated. If check R8 fails, sort out discounts, commitments or scope before step 05.",
            "**G3.** Каждый тест закрыт как «пройден», «эффект измерен» или «неприменимо», и *операционный* рост "
            "рассчитан. Если проверка R8 не пройдена, разберитесь со скидками, обязательствами или охватом до "
            "шага 05."),
     plain=T("A bill can increase without additional consumption: a reservation expired, a credit ran out, a subscription joined the scope, the exchange rate moved, the workspace tier changed. These are accounting effects, not technical defects. Mixing them with consumption growth directs engineering effort at causes that do not exist.\n\nThis step tests each accounting cause, quantifies it and subtracts it from the total. The remainder is the operational growth, which the rest of the audit explains.",
             "Счёт может вырасти без увеличения потребления: закончилось резервирование, истёк кредит, в охват добавлена подписка, изменился курс, изменился уровень workspace. Это учётные эффекты, а не технические дефекты. Если смешать их с ростом потребления, инженеры будут искать несуществующие причины.\n\nНа этом шаге каждая учётная причина проверяется, измеряется и вычитается из итога. Остаток - операционный рост, который объясняет остальной аудит."),
     result=T("lines ACC-01 to ACC-08 in the delta bridge and the operational growth in section 7.",
              "строки ACC-01…ACC-08 в мосте дельты и операционный рост в разделе 7."),
     tip=T("Enter 0 for a cause without effect. An empty cell is indistinguishable from an unchecked cause.",
           "Для причины без эффекта вносите 0. Пустая ячейка неотличима от непроверенной причины."))

act("3.1", T("Calendar effect (ACC-01)", "Календарный эффект (ACC-01)"),
    T("Because we compare cost per day, month length is already removed. Fill ACC-01 only if the people who "
      "raised the question looked at monthly totals. Example: February has 28 days and March has 31, so at "
      "exactly the same usage March costs 10.7% more.",
      "Раз мы сравниваем затраты в сутки, длина месяца уже учтена. Заполняйте ACC-01, только если те, кто поднял "
      "вопрос, смотрели на месячные итоги. Пример: в феврале 28 дней, в марте 31, поэтому при том же потреблении "
      "март дороже на 10,7%."))
act("3.2", T("Charge type and pricing model (ACC-02, ACC-03)", "Тип начисления и модель цены (ACC-02, ACC-03)"),
    T('Download the cost grouped by **Charge type** and by **Pricing model**, for B and for C, and upload the files. Look for a big one-off **purchase** in C (ACC-02) or a **commitment that ended** (ACC-03).',
      'Скачайте затраты, сгруппированные по **Charge type** и по **Pricing model**, для B и для C, и загрузите файлы. Ищите крупную разовую **покупку** в C (ACC-02) или **закончившееся обязательство** (ACC-03).'))
act("3.3", T("Compare Actual with Amortized (ACC-02)", "Сравните Actual и Amortized (ACC-02)"),
    T('Download the same scope as **Amortized** (monthly). If it differs a lot from Actual in C, a purchase is the reason: explain it in ACC-02.',
      'Скачайте тот же охват как **Amortized** (помесячно). Если он сильно отличается от Actual в C, причина в покупке: объясните её в ACC-02.'))
act("3.4", T("Credits, refunds and corrections (ACC-04)", "Кредиты, возвраты и корректировки (ACC-04)"),
    T("Optional. Look at charge types Refund and Adjustment, and in the billing profile at credit balances and "
      "their expiry dates. A credit that ran out makes the bill rise although usage did not.",
      "Необязательно. Посмотрите типы начислений Refund и Adjustment, а в биллинговом профиле - остатки кредитов "
      "и сроки их действия. Закончившийся кредит поднимает счёт при неизменном потреблении."))
act("3.5", T("Did the scope change between B and C? (ACC-07)", "Менялся ли охват между B и C? (ACC-07)"),
    T("Press Run. The app compares subscriptions in B and C. A new subscription in C adds cost that was simply "
      "not counted before. Add the workspaces that were marked `APPEARED_IN_WINDOW` in action 1.6.",
      "Нажмите «Запустить». Приложение сравнит подписки в B и C. Новая подписка в C добавляет затраты, которые "
      "раньше просто не учитывались. Добавьте workspace, отмеченные `APPEARED_IN_WINDOW` в действии 1.6."))
act("3.6", T("Did the unit price change? (ACC-05)", "Менялась ли цена единицы? (ACC-05)"),
    T("Press Run to see the change per day for every meter. For the biggest ones compare `EffectivePrice` in B "
      "and in C inside the export. A higher unit price with the same usage is a price effect (ACC-05). Typical "
      "cause: the move from Standard to Premium workspaces - the automatic upgrade happens on 1 Oct 2026, and "
      "you will see SKUs named `STANDARD_*` replaced by `PREMIUM_*` in action 1.7.",
      "Нажмите «Запустить», чтобы увидеть изменение в сутки по каждому счётчику. Для самых крупных сравните "
      "`EffectivePrice` в B и в C внутри выгрузки. Более высокая цена при том же потреблении - эффект цены "
      "(ACC-05). Типичная причина: переход workspace со Standard на Premium - автоматическое обновление 1 окт "
      "2026, в действии 1.7 вы увидите, что SKU `STANDARD_*` заменились на `PREMIUM_*`."))
act("3.7", T("Did the Databricks list price change? (ACC-05)", "Менялся ли прайс-лист Databricks? (ACC-05)"),
    T("This SQL lists every version of the Databricks price list that was active in your window. A new version "
      "inside the window is a price change, not a usage change.",
      "Этот SQL перечисляет все версии прайс-листа Databricks, действовавшие в вашем окне. Новая версия внутри "
      "окна - это изменение цены, а не потребления."))
act("3.8", T("Exchange rate and late corrections (ACC-06, ACC-08)", "Курс валют и поздние корректировки (ACC-06, ACC-08)"),
    T("**Exchange rate:** compare the rate of the billing currency to the price currency in B and in C (ACC-06). "
      "**Late corrections:** export one old month again and compare it with the first copy; count the "
      "`RETRACTION` and `RESTATEMENT` records from action 1.6 (ACC-08). Write findings in the step notes.",
      "**Курс:** сравните курс валюты счёта к валюте прайса в B и в C (ACC-06). **Поздние корректировки:** "
      "выгрузите один старый месяц ещё раз и сравните с первой копией; посчитайте записи `RETRACTION` и "
      "`RESTATEMENT` из действия 1.6 (ACC-08). Выводы пишите в заметки шага."))
act("3.9", T("Sanity check: do both views move the same way? (rule R8)", "Проверка здравого смысла: двигаются ли оба представления одинаково? (правило R8)"),
    T("Press Run. The app compares the percentage change of the *Azure Databricks* bill with that of the "
      "Databricks cost model. They must have the **same direction** and differ by **no more than 15 percentage "
      "points**. If not, a discount, commitment or scope is distorting one of them - fix that first.",
      "Нажмите «Запустить». Приложение сравнивает процентное изменение счёта *Azure Databricks* с изменением "
      "модели затрат Databricks. Они должны идти в **одну сторону** и отличаться **не больше чем на 15 "
      "процентных пунктов**. Если нет, скидка, обязательство или охват искажают одно из них - исправьте это "
      "сначала."))
act("3.10", T("Fill in the accounting lines of the bridge", "Заполните учётные строки моста"),
    T("In the delta bridge fill `delta_per_day`, `status` and `evidence_ids` for ACC-01 to ACC-08. Use 0 for "
      "causes that had no effect.",
      "В мосте дельты заполните `delta_per_day`, `status` и `evidence_ids` для ACC-01…ACC-08. Для причин без "
      "эффекта ставьте 0."))
act("3.11", T("Calculate the operational growth", "Посчитайте операционный рост"),
    T("Press Run. Operational growth = total growth minus all accounting effects. This is the part the rest of "
      "the audit will explain. It is written into section 7.",
      "Нажмите «Запустить». Операционный рост = общий рост минус все учётные эффекты. Именно эту часть будет "
      "объяснять остальной аудит. Результат записывается в раздел 7."))
act("3.12", T("Set the status of the pricing hypotheses", "Задайте статусы гипотез о ценах"),
    T("Open the hypothesis register and set a status for each rate or accounting hypothesis H-RAT-01 to 11 "
      "(confirmed, rejected, unknown and so on).",
      "Откройте реестр гипотез и задайте статус каждой гипотезе о тарифах и учёте H-RAT-01…11 (подтверждена, "
      "отвергнута, неизвестно и т. д.)."))
act("3.13", T("Write the accounting results", "Запишите учётные результаты"),
    T("In section 7 write one line per test: *pass*, *effect* or *not applicable*, the change per day and the "
      "evidence ID.",
      "В разделе 7 напишите по строке на тест: *пройден*, *эффект* или *неприменимо*, изменение в сутки и ID "
      "доказательства."))

# ======================================================================= 04
step("04",
     question=T("In the Azure bill, which services, meters and resources cost more?",
                "В счёте Azure - по каким сервисам, счётчикам и ресурсам стало дороже?"),
     goal=T("See where the extra money was billed, one view at a time, and put every big line into a cost category.",
            "Увидеть, где выставлено больше денег, по одному разрезу за раз, и отнести каждую крупную строку к "
            "категории затрат."),
     gate=T("**G4.** The category amounts add up to the operational growth (within 1%), and every big line has a "
            "category.",
            "**G4.** Суммы по категориям складываются в операционный рост (с точностью до 1%), и у каждой крупной "
            "строки есть категория."),
     plain=T("The total growth is a single number. This step decomposes it by subscription, service, meter, resource group and resource. Each decomposition is an alternative view of the same total: review them one at a time and never sum two views.\n\nThe result is a ranked list of the largest increases, each assigned to a cost category: the Databricks charge, the underlying virtual machines, storage, network, monitoring, or items outside the audit.",
             "Общий рост - одно число. Этот шаг раскладывает его по подпискам, сервисам, счётчикам, группам ресурсов и ресурсам. Каждое разложение - альтернативное представление одного и того же итога: рассматривайте их по одному и не суммируйте два представления.\n\nРезультат - ранжированный список крупнейших увеличений, каждое отнесено к категории затрат: счёт Databricks, лежащие под ним виртуальные машины, хранилище, сеть, мониторинг либо позиции вне аудита."),
     result=T("BUCKET lines in the delta bridge and a map of workspaces to resource groups.",
              "строки BUCKET в мосте дельты и карта workspace → группы ресурсов."),
     tip=T("Retain decreasing lines as well. Excluding them overstates the remaining increases.",
           "Сохраняйте и убывающие строки. Их исключение завышает остальные увеличения."))

act("4.1", T("Run the Azure decomposition (five groupings)", "Запустите декомпозицию Azure (пять группировок)"),
    T("Press Run. One run shows what changed per day between B and C in five mutually exclusive views, each saved "
      "as its own file:\n\n"
      "- **subscription** - which subscriptions added or lost cost;\n"
      "- **service** - which Azure services (Azure Databricks, Virtual Machines, Storage and others) changed;\n"
      "- **meter** - the most detailed thing Azure bills for;\n"
      "- **resource group** - often a team or a workspace, so this view points to the owner;\n"
      "- **resource** - the 50 resources with the biggest change: the shortlist to investigate.\n\n"
      "Column names differ between contract types (EA and MCA). If a grouping is skipped because a column is missing, "
      "the warning names it and the other groupings are still produced.",
      "Нажмите «Запустить». Один запуск показывает, что изменилось в сутки между B и C, в пяти взаимоисключающих "
      "разрезах; каждый сохраняется в отдельный файл:\n\n"
      "- **подписка** - какие подписки прибавили или потеряли затраты;\n"
      "- **сервис** - какие сервисы Azure (Azure Databricks, Virtual Machines, Storage и другие) изменились;\n"
      "- **счётчик** - самое детальное, за что Azure выставляет деньги;\n"
      "- **группа ресурсов** - часто команда или workspace, поэтому разрез указывает на владельца;\n"
      "- **ресурс** - 50 ресурсов с наибольшим изменением: короткий список для расследования.\n\n"
      "Названия колонок отличаются у разных договоров (EA и MCA). Если группировка пропущена из-за отсутствия "
      "колонки, предупреждение называет её, а остальные группировки всё равно строятся."))
act("4.2", T("Map workspaces to their resource groups", "Сопоставьте workspace и их группы ресурсов"),
    T("Press Run to read the map from Azure (needs a one-time `az login` on this computer; read-only). Without "
      "Azure CLI, take the information from the portal (*the workspace, then Properties*) and upload it in the next "
      "action. The map tells you which virtual machines belong to which workspace.",
      "Нажмите «Запустить», чтобы прочитать карту из Azure (нужен однократный `az login` на этом компьютере; "
      "только чтение). Без Azure CLI возьмите данные из портала (*workspace, затем Properties*) и загрузите в "
      "следующем действии. Карта показывает, какие виртуальные машины принадлежат какому workspace."))
act("4.2b", T("Upload the workspace map by hand", "Загрузите карту workspace вручную"),
    T("Only if you could not run the previous action: upload a CSV named `workspace_rg_map.csv` with columns for "
      "workspace, its managed resource group and the dependent resource groups.",
      "Только если не удалось выполнить предыдущее действие: загрузите CSV `workspace_rg_map.csv` с колонками "
      "workspace, его managed resource group и зависимые группы ресурсов."))
act("4.3", T("Put every big line into a category", "Отнесите каждую крупную строку к категории"),
    T("A line is **big** if it is at least 5% of the total change per day, or among the 10 biggest increases. "
      "Give it one category:\n\n"
      "- `DBX_PLATFORM` - the Databricks charge itself (DBU)\n"
      "- `DBX_CLASSIC_INFRA` - virtual machines, disks and IPs under classic compute\n"
      "- `STORAGE`, `NETWORK`, `MONITORING` - the surrounding services\n"
      "- `SHARED_UNALLOCATED` - used by many, with no clear owner\n"
      "- `OUT_OF_SCOPE` - not part of this audit\n\n"
      "A managed resource group is a hint about ownership, not proof.",
      "Строка **крупная**, если это не менее 5% общего изменения в сутки или она входит в 10 самых больших "
      "увеличений. Дайте ей одну категорию:\n\n"
      "- `DBX_PLATFORM` - сам счёт Databricks (DBU)\n"
      "- `DBX_CLASSIC_INFRA` - виртуальные машины, диски и IP под классическими вычислениями\n"
      "- `STORAGE`, `NETWORK`, `MONITORING` - окружающие сервисы\n"
      "- `SHARED_UNALLOCATED` - используется многими, без явного владельца\n"
      "- `OUT_OF_SCOPE` - не входит в этот аудит\n\n"
      "Managed resource group - подсказка о владельце, а не доказательство."))

# ======================================================================= 05
step("05",
     question=T("Inside Databricks, which products, workspaces and objects used more?",
                "Внутри Databricks - какие продукты, workspace и объекты потребили больше?"),
     goal=T("Explain the Databricks part of the growth step by step - product, price tier, workspace, then the "
            "single job, cluster or warehouse - and make a list of driver candidates.",
            "Объяснить часть роста в Databricks шаг за шагом - продукт, цена, workspace, затем конкретная "
            "задача, кластер или warehouse - и составить список кандидатов в драйверы."),
     gate=T("**G5.** The top objects explain at least 90% of the modeled Databricks growth, or you have measured "
            "what is left unexplained.",
            "**G5.** Главные объекты объясняют не меньше 90% модельного роста Databricks, либо вы измерили, что "
            "осталось необъяснённым."),
     plain=T("Step 04 established how much Databricks cost grew. This step establishes which objects account for it, moving from the general to the specific: product, workspace, then the individual job, pipeline, SQL warehouse or cluster. All queries are read-only SQL on Databricks system tables.\n\nA good result is a short list, typically three to ten objects, that together explain 90% of the growth. These objects are the driver candidates.",
             "Шаг 04 установил, насколько выросли затраты Databricks. Этот шаг определяет, какие объекты за это отвечают, от общего к частному: продукт, workspace, затем отдельная задача, конвейер, SQL warehouse или кластер. Все запросы - SQL только на чтение к системным таблицам Databricks.\n\nХороший результат - короткий список, обычно от трёх до десяти объектов, которые вместе объясняют 90% роста. Эти объекты - кандидаты в драйверы."),
     result=T("DRIVER_CANDIDATE lines in the delta bridge and open hypotheses for each.",
              "строки DRIVER_CANDIDATE в мосте дельты и открытые гипотезы для каждой."),
     tip=T("Calculate money only for SKUs that passed check R7 in step 01. Never add quantities in different units.",
           "Денежные оценки считайте только по SKU, прошедшим проверку R7 на шаге 01. Не складывайте количества в разных единицах."),
     rules=T("Classic compute is billed twice: DBU **and** the virtual machine. Serverless is billed once: never "
             "add a VM cost to it. A job that runs on an all-purpose cluster has an empty `job_id`; its cost "
             "appears as `CLUSTER`.",
             "Классические вычисления оплачиваются дважды: DBU **и** виртуальная машина. Serverless - один раз: "
             "никогда не добавляйте к нему стоимость VM. У задачи на all-purpose кластере пустой `job_id`; её "
             "затраты видны как `CLUSTER`."))

act("5.1", T("Is it more usage or a higher price? (by SKU)", "Больше потребления или выше цена? (по SKU)"),
    T("This SQL splits each product's growth into **volume** (more usage) and **rate** (higher unit price). A "
      "SKU that disappears while a similar one appears is a **mix shift** - usage just moved, and the two "
      "changes mostly cancel out.",
      "Этот SQL делит рост каждого продукта на **объём** (больше потребления) и **цену** (выше цена единицы). "
      "SKU, который исчез, пока появился похожий, - это **смещение состава**: потребление просто переехало, и два "
      "изменения в основном гасят друг друга."))
act("5.2", T("Which workspaces grew", "У каких workspace рост"),
    T("If one workspace grew, the cause is local and probably a team's change. If all workspaces grew a little, "
      "think of the platform or the price.",
      "Если вырос один workspace, причина локальная, скорее всего изменение одной команды. Если подросли все, "
      "думайте о платформе или цене."))
act("5.3", T("Which jobs, pipelines, warehouses and clusters grew", "Какие задачи, конвейеры, warehouse и кластеры выросли"),
    T("The key query of the step. It lists objects from the biggest increase down and labels each "
      "one: NEW, GONE, GROWN, SHRUNK or FLAT. The column `cumulative_share` shows how much of the growth the list "
      "explains so far; the list goes on until it reaches **0.90** (checked automatically).",
      "Ключевой запрос шага. Он перечисляет объекты от самого большого роста вниз и помечает каждый: NEW, "
      "GONE, GROWN, SHRUNK или FLAT. Колонка `cumulative_share` показывает, какую долю роста список объяснил на "
      "данный момент; список идёт, пока не достигнет **0,90** (проверяется автоматически)."))
act("5.4", T("Look at the daily cost of the top objects", "Посмотрите суточную стоимость главных объектов"),
    T("Put the top object IDs from 5.3 into the `object_ids` field. The query shows each object's daily cost so "
      "you can see **when** it started to grow. It should be within ±2 days of the overall start date from step "
      "02. If not, that object is probably not the main cause.",
      "Впишите ID главных объектов из 5.3 в поле `object_ids`. Запрос показывает суточную стоимость каждого "
      "объекта, чтобы вы увидели, **когда** он начал расти. Дата должна быть в пределах ±2 дней от общей даты "
      "начала из шага 02. Если нет, этот объект, скорее всего, не главная причина."))
act("5.5", T("How much cost has no owner", "Сколько затрат без владельца"),
    T("Shows the share of cost that has no tags or no clear owner. That share goes to step 07.",
      "Показывает долю затрат без тегов и без ясного владельца. Эта доля уйдёт в шаг 07."))
act("5.6", T("What is new in the window", "Что нового появилось в окне"),
    T("Lists products and SKUs that appeared for the first time near the start date (`new_in_window`). New "
      "products are common causes of growth.",
      "Перечисляет продукты и SKU, впервые появившиеся около даты начала (`new_in_window`). Новые продукты - "
      "частая причина роста."))
act("5.7", T("Record the candidates", "Запишите кандидатов"),
    T("In the delta bridge add a DRIVER_CANDIDATE line for each top object or SKU: the growth per day at list "
      "price, the object and its change class.",
      "В мост дельты добавьте строку DRIVER_CANDIDATE для каждого главного объекта или SKU: рост в сутки по "
      "прайс-листу, объект и его класс изменения."))
act("5.8", T("Open a hypothesis for each candidate", "Откройте гипотезу для каждого кандидата"),
    T("In the hypothesis register find the matching ready-made hypotheses and mark them as being tested. Step 06 "
      "will confirm or reject them.",
      "В реестре гипотез найдите подходящие готовые гипотезы и отметьте, что они проверяются. Шаг 06 подтвердит "
      "или отвергнет их."))

# ======================================================================= 06
step("06",
     question=T("What exactly changed, when, and how much of the growth does it explain?",
                "Что именно изменилось, когда и какую часть роста это объясняет?"),
     goal=T("For every big driver: a dated technical cause, measured in money, with proof.",
            "Для каждого крупного драйвера: датированная техническая причина, измеренная в деньгах, с "
            "доказательствами."),
     gate=T("**G6.** Every big driver has a driver card and a status other than \"untested hypothesis\".",
            "**G6.** У каждого крупного драйвера есть карточка и статус, отличный от «непроверенная гипотеза»."),
     plain=T("This step establishes causality. For each candidate from step 05 you determine what changed (a new schedule, a larger cluster, a warehouse that no longer stops, a newly enabled feature), when it changed, and how much of the growth the change explains.\n\nEach type of candidate has a ready playbook with the SQL queries to run. Results are recorded on a one-page driver card. A cause is confirmed only when it satisfies four proofs (rule R9); a coincidence in time alone is insufficient.",
             "Этот шаг устанавливает причинность. Для каждого кандидата из шага 05 определяется, что изменилось (новое расписание, более крупный кластер, warehouse, переставший останавливаться, включённая функция), когда это произошло и какую часть роста объясняет изменение.\n\nДля каждого типа кандидатов есть готовый плейбук с SQL-запросами. Результаты фиксируются на одностраничной карточке драйвера. Причина считается подтверждённой, только если выполнены четыре доказательства (правило R9); совпадения по времени недостаточно."),
     result=T("a driver card per big driver, statuses in the hypothesis register, ROOT_CAUSE lines in the bridge.",
              "карточка на каждый крупный драйвер, статусы в реестре гипотез, строки ROOT_CAUSE в мосте."),
     tip=T("Disprove at least one alternative explanation for every driver. This separates evidence from assumption.",
           "Для каждого драйвера опровергните хотя бы одно альтернативное объяснение. Это отличает доказательство от предположения."),
     rules=T("**Rule R9 - four proofs for CONFIRMED:** (a) the growth is visible in the Azure bill; (b) the "
             "change happened within ±2 days of the driver's start; (c) the cause explains at least 70% of the "
             "driver's growth; (d) at least one other explanation was disproved. Time coincidence alone is never "
             "enough.",
             "**Правило R9 - четыре доказательства для CONFIRMED:** (a) рост виден в счёте Azure; (b) изменение "
             "произошло в пределах ±2 дней от начала драйвера; (c) причина объясняет не менее 70% роста драйвера; "
             "(d) опровергнуто хотя бы одно другое объяснение. Одного совпадения во времени никогда не "
             "достаточно."))

act("6.0", T("Select the playbook for each candidate", "Выберите плейбук для каждого кандидата"),
    T("Locate the candidate type on the left and open the playbook on the right:\n\n"
      "- Jobs grew → **Jobs**\n"
      "- Pipelines (DLT) grew → **Pipelines**\n"
      "- All-purpose clusters grew, or VMs and DBU both grew → **Classic compute**\n"
      "- VMs grew but DBU did not → **Instance pools**\n"
      "- SQL grew → **SQL warehouses**\n"
      "- Serverless SKUs grew → **Serverless**\n"
      "- Model serving, Vector Search, AI, Apps grew → **AI and apps**\n"
      "- Predictive optimization, monitoring, networking grew → **Platform features**\n"
      "- Storage, network or monitoring categories from step 04 → playbooks **Storage**, **Network**, "
      "**Monitoring**\n"
      "- Effects from step 03 → **Rate and accounting**",
      "Найдите тип кандидата слева и откройте плейбук справа:\n\n"
      "- Выросли задачи (Jobs) → **Jobs**\n"
      "- Выросли конвейеры (DLT) → **Pipelines**\n"
      "- Выросли all-purpose кластеры, либо растут и VM, и DBU → **Classic compute**\n"
      "- Выросли VM, а DBU нет → **Instance pools**\n"
      "- Вырос SQL → **SQL warehouses**\n"
      "- Выросли serverless SKU → **Serverless**\n"
      "- Выросли model serving, Vector Search, AI, Apps → **AI and apps**\n"
      "- Выросли predictive optimization, мониторинг, сеть → **Platform features**\n"
      "- Категории хранилища, сети или мониторинга из шага 04 → плейбуки **Storage**, **Network**, "
      "**Monitoring**\n"
      "- Эффекты из шага 03 → **Rate and accounting**"))
act("6.1", T("Create a driver card", "Создайте карточку драйвера"),
    T("Press Run to create a one-page card from the template and open it. Make one card for each big driver and "
      "fill it in as you work: what changed, when, how much, proof, alternatives you disproved, the fix.",
      "Нажмите «Запустить», чтобы создать одностраничную карточку из шаблона и открыть её. Делайте по карточке "
      "на каждый крупный драйвер и заполняйте по ходу работы: что изменилось, когда, сколько, доказательства, "
      "опровергнутые альтернативы, исправление."))
act("6.2", T("Run the diagnostic queries from the playbook", "Запустите диагностические запросы из плейбука"),
    T("Choose the query that your playbook asks for. Two things to find out: **how much** (how often it runs "
      "× what one run costs, or volume × price) and **what changed** (the history of the object's settings, the "
      "audit log, a release, a Git change, an Azure Activity Log entry or a ticket).",
      "Выберите запрос, который требует ваш плейбук. Нужно выяснить две вещи: **сколько** (как часто запускается "
      "× сколько стоит один запуск, или объём × цена) и **что изменилось** (история настроек объекта, журнал "
      "аудита, релиз, изменение в Git, запись Azure Activity Log или тикет)."))
act("6.3", T("Upload other evidence", "Загрузите другие доказательства"),
    T("Screenshots of the Databricks UI, Spark UI exports, Azure Activity Log downloads - anything else that "
      "supports your explanation.",
      "Скриншоты интерфейса Databricks, выгрузки Spark UI, скачанный Azure Activity Log - всё остальное, что "
      "подтверждает ваше объяснение."))
act("6.4", T("Set the status of each hypothesis", "Задайте статус каждой гипотезы"),
    T("In the hypothesis register mark each as **CONFIRMED** (all four R9 proofs), **LIKELY** (some), "
      "**REJECTED** (disproved) or **UNKNOWN** (no data).",
      "В реестре гипотез отметьте каждую как **CONFIRMED** (все четыре доказательства R9), **LIKELY** (часть), "
      "**REJECTED** (опровергнута) или **UNKNOWN** (нет данных)."))
act("6.5", T("Record the root causes in the bridge", "Запишите первопричины в мост"),
    T("For each cause add a ROOT_CAUSE line: the growth per day in the Azure Actual currency, the status, the "
      "hypothesis ID and the evidence IDs.",
      "Для каждой причины добавьте строку ROOT_CAUSE: рост в сутки в валюте Azure Actual, статус, ID гипотезы и "
      "ID доказательств."))

# ======================================================================= 07
step("07",
     question=T("Who owns each part of the growth, and what is still unexplained?",
                "Кому принадлежит каждая часть роста и что осталось необъяснённым?"),
     goal=T("Every part of the growth has an owner or is openly marked as unresolved, and the bridge adds up.",
            "У каждой части роста есть владелец или она открыто помечена как неразрешённая, и мост сходится."),
     gate=T("**G7.** The bridge adds up. The unexplained part is at most 10%, or the audit owner has accepted a "
            "bigger one in writing.",
            "**G7.** Мост сходится. Необъяснённая часть не больше 10% либо владелец аудита письменно принял "
            "большую."),
     plain=T("The numbers must now reconcile. Subtract everything explained from the total growth: accounting effects, root causes, shared cost, out-of-scope cost. The remainder is the unexplained part. A residual is acceptable; concealing it is not.\n\nEvery confirmed cause also receives an owner: a person or team able to implement the fix. A finding without an owner does not lead to action.",
             "Теперь числа должны сойтись. Вычтите из общего роста всё объяснённое: учётные эффекты, первопричины, общие затраты, затраты вне охвата. Остаток - необъяснённая часть. Остаток допустим, его сокрытие - нет.\n\nКаждой подтверждённой причине также назначается владелец: человек или команда, способные внедрить исправление. Вывод без владельца не приводит к действиям."),
     result=T("owners on every confirmed line and the calculated unexplained share.",
              "владельцы у каждой подтверждённой строки и рассчитанная доля необъяснённого."),
     tip=T("Do not distribute the unexplained part across drivers to make the table reconcile.",
           "Не распределяйте необъяснённую часть по драйверам ради сходимости таблицы."))

act("7.1", T("Name an owner for every confirmed cause", "Назовите владельца для каждой подтверждённой причины"),
    T("In the bridge write who owns each CONFIRMED or LIKELY line: the workspace owner, the job owner, or the "
      "values of the tags `owner`, `cost_center`, `application`. The column `sample_run_as` from 5.3 shows who "
      "ran the object.",
      "В мосте запишите, кто владеет каждой строкой CONFIRMED или LIKELY: владелец workspace, владелец задачи "
      "или значения тегов `owner`, `cost_center`, `application`. Колонка `sample_run_as` из 5.3 показывает, "
      "кто запускал объект."))
act("7.2", T("Shared cost allocation keys (optional)", "Ключи распределения общих затрат (необязательно)"),
    T("Cost used by several teams can be split only by a key you can prove (share of usage, bytes, number of "
      "requests). If you cannot prove one, leave it as shared (SH-01) - do not estimate.",
      "Затраты, которыми пользуются несколько команд, делятся только по ключу, который можно доказать (доля "
      "использования, байты, число запросов). Если доказать нельзя, оставьте как общие (SH-01) - не оценивайте произвольно."))
act("7.3", T("Describe the cost without tags or owner", "Опишите затраты без тегов и владельца"),
    T("Take the share from query 5.5 and write in the notes why it is unattributed and what would be needed to "
      "assign it.",
      "Возьмите долю из запроса 5.5 и напишите в заметках, почему она не атрибутирована и что нужно для "
      "назначения владельца."))
act("7.4", T("Add the shared and out-of-scope lines", "Добавьте строки общих затрат и вне охвата"),
    T("Add SH-01 (shared, not allocated) and OOS-01 (not part of the audit, for example non-Databricks services "
      "found in step 04) to the bridge.",
      "Добавьте в мост SH-01 (общие, не распределённые) и OOS-01 (не входят в аудит, например не-Databricks "
      "сервисы, найденные на шаге 04)."))
act("7.5", T("Calculate the unexplained part", "Посчитайте необъяснённую часть"),
    T("Press Run. Unexplained = total - (accounting + root causes + shared + out-of-scope). The app shows the "
      "shares and whether the 10% limit is kept. The BUCKET and DRIVER_CANDIDATE lines are only for orientation "
      "and are not part of the sum.",
      "Нажмите «Запустить». Необъяснённое = итог - (учёт + первопричины + общие + вне охвата). Приложение "
      "показывает доли и соблюдён ли предел 10%. Строки BUCKET и DRIVER_CANDIDATE нужны только для "
      "ориентира и в сумму не входят."))

# ======================================================================= 08
step("08",
     question=T("Can someone else repeat our numbers and reach the same result?",
                "Может ли кто-то другой повторить наши числа и получить тот же результат?"),
     goal=T("The findings survive an independent review, and every number in the report can be reproduced.",
            "Выводы выдерживают независимую проверку, и каждое число отчёта воспроизводимо."),
     gate=T("**G8.** All numbers reproduce, and an independent reviewer has signed section 8.",
            "**G8.** Все числа воспроизводятся, и независимый проверяющий подписал раздел 8."),
     plain=T("Before reporting, the results are tested. The application re-runs every saved tool and SQL query with the recorded parameters and verifies that the outputs are identical. A reviewer who did not perform the analysis then examines it and challenges the conclusions.\n\nIf IBM Cloudability or ApptioOne is available, the figures can be compared with theirs. Differences are explained, not added.",
             "Перед отчётом результаты проверяются. Приложение заново запускает каждый сохранённый инструмент и SQL-запрос с записанными параметрами и проверяет, что результаты идентичны. Затем проверяющий, не выполнявший анализ, изучает его и оспаривает выводы.\n\nПри наличии IBM Cloudability или ApptioOne цифры можно сопоставить с их данными. Расхождения объясняются, но не суммируются."),
     result=T("a reproduction log, downgraded statuses where proof was weak, and a reviewer's signature.",
              "журнал воспроизведения, пониженные статусы там, где доказательств мало, и подпись проверяющего."),
     tip=T("Rows created manually cannot be re-run by the application and must be verified by hand.",
           "Строки, созданные вручную, приложение повторить не может: проверьте их вручную."))

act("8.1", T("Re-run everything and compare", "Перезапустите всё и сравните"),
    T("Press Run. The app repeats every evidence row (and the SQL queries too, if the Databricks connection is "
      "set up), compares the new files with the saved ones and writes the `reproduction_log`. Rows you made "
      "manually are listed for you to check by hand.",
      "Нажмите «Запустить». Приложение повторит каждую строку доказательств (и SQL-запросы, если настроено "
      "подключение к Databricks), сравнит новые файлы с сохранёнными и запишет `reproduction_log`. Строки, "
      "сделанные вручную, перечислены для проверки руками."))
act("8.2", T("Re-check the proofs of every CONFIRMED cause", "Перепроверьте доказательства каждой CONFIRMED причины"),
    T("For each hypothesis marked CONFIRMED check once more that all four R9 proofs are really there. If one is "
      "missing, change the status to LIKELY. Downgrading in advance avoids a correction during review.",
      "Для каждой гипотезы со статусом CONFIRMED ещё раз проверьте, что все четыре доказательства R9 на месте. "
      "Если одного нет, поставьте LIKELY. Заблаговременное понижение исключает исправление при проверке."))
act("8.3", T("Compare with other views of the cost", "Сравните с другими представлениями затрат"),
    T("Fill the table: Azure Amortized, the Databricks usage dashboard, IBM (if you have it). For each write "
      "its values for B and C and **explain** the difference to Azure Actual. Differences are explained and "
      "never added.",
      "Заполните таблицу: Azure Amortized, дашборд использования Databricks, IBM (если есть). Для каждого "
      "запишите значения для B и C и **объясните** разницу с Azure Actual. Расхождения объясняются и никогда не "
      "складываются."))
act("8.4", T("IBM Cloudability: check access (optional)", "IBM Cloudability: проверка доступа (необязательно)"),
    T("Only if your company has IBM Cloudability. Press Run to check that your key works and see which "
      "measures are available.",
      "Только если в вашей компании есть IBM Cloudability. Нажмите «Запустить», чтобы проверить ключ и увидеть "
      "доступные показатели."))
act("8.5", T("IBM Cloudability: export (optional)", "IBM Cloudability: выгрузка (необязательно)"),
    T("Downloads the cost data from Cloudability for your window so you can compare it with Azure.",
      "Скачивает данные о затратах из Cloudability за ваше окно, чтобы сравнить их с Azure."))
act("8.6", T("IBM ApptioOne: download a report (optional)", "IBM ApptioOne: загрузка отчёта (необязательно)"),
    T("Only if your company has ApptioOne. Downloads the report you choose.",
      "Только если в вашей компании есть ApptioOne. Скачивает выбранный вами отчёт."))
act("8.7", T("IBM ApptioOne: normalize (optional)", "IBM ApptioOne: нормализация (необязательно)"),
    T("Converts the ApptioOne report into the same simple table format as the other exports.",
      "Приводит отчёт ApptioOne к тому же простому табличному формату, что и остальные выгрузки."))
act("8.8", T("IBM: analyze the export (optional)", "IBM: анализ выгрузки (необязательно)"),
    T("Builds the same monthly comparison from the IBM data as for Azure, so the two can be put side by side.",
      "Строит из данных IBM то же месячное сравнение, что и для Azure, чтобы их можно было сопоставить."))
act("8.9", T("Record the differences with IBM", "Запишите расхождения с IBM"),
    T("Add every difference between IBM and Azure Actual to the discrepancy register with its explanation.",
      "Добавьте каждое расхождение между IBM и Azure Actual в реестр расхождений с объяснением."))
act("8.10", T("Persistence and independent review", "Устойчивость и независимая проверка"),
    T("Persistence: for each driver note whether the growth is still there in P. Review: a person who did not "
      "build the analysis reads it and signs section 8.",
      "Устойчивость: для каждого драйвера отметьте, держится ли рост в P. Проверка: человек, не строивший "
      "анализ, читает его и подписывает раздел 8."))

# ======================================================================= 09
step("09",
     question=T("What do we report, what do we fix, and how do we keep it from happening again?",
                "О чём докладываем, что исправляем и как не допустить повторения?"),
     goal=T("An approved report, a list of fixes with owners, and a plan to monitor the cost from now on.",
            "Утверждённый отчёт, список исправлений с владельцами и план постоянного наблюдения за затратами."),
     gate=T("**G9.** The report is approved and every fix has an owner. Savings are claimed only after you "
            "measure them in Azure Actual for at least 14 days after the change.",
            "**G9.** Отчёт утверждён, у каждого исправления есть владелец. Экономию заявляют только после "
            "замера в Azure Actual не меньше 14 дней после изменения."),
     plain=T("The final step converts the analysis into an actionable result: a report with the delta bridge, one finding per cause, a remediation list with owners, and alerts that detect the next increase within days instead of months.\n\nA saving exists only when it is visible in the actual bill. Until then it is a plan.",
             "Завершающий шаг превращает анализ в результат, пригодный для действий: отчёт с мостом дельты, по одному выводу на причину, список исправлений с владельцами и оповещения, которые выявляют следующий рост за дни, а не за месяцы.\n\nЭкономия существует, только когда она видна в реальном счёте. До этого момента это план."),
     result=T("`findings_report.md` with the bridge table, a fix list and a control plan.",
              "`findings_report.md` с таблицей моста, списком исправлений и планом контроля."),
     tip=T("The bridge table in the report must be identical to delta_bridge.csv.",
           "Таблица моста в отчёте должна совпадать с delta_bridge.csv."))

act("9.1", T("Get the bridge as a table for the report", "Получите мост в виде таблицы для отчёта"),
    T("Press Run and copy the result into section 3 of the report. It must be identical to the CSV.",
      "Нажмите «Запустить» и скопируйте результат в раздел 3 отчёта. Он должен совпадать с CSV."))
act("9.2", T("Write the report", "Напишите отчёт"),
    T("Fill every blank `____` in the template. Sections: 1 summary for managers, 2 size and timing, 3 bridge, "
      "4 one finding per driver, 5-7 rejected ideas, the unexplained part and limitations, 8 fixes and the "
      "control plan, 9 approval. Write section 1 last, in clear non-technical wording: it is the section most readers rely on.",
      "Заполните все пропуски `____` в шаблоне. Разделы: 1 резюме для руководства, 2 размер и время, 3 мост, "
      "4 по выводу на драйвер, 5-7 отвергнутые идеи, необъяснённая часть и ограничения, 8 исправления и план "
      "контроля, 9 утверждение. Раздел 1 пишите последним, без технического жаргона: на него опирается большинство читателей."))


def apply(steps: list[dict]) -> None:
    """Overlay the plain-language wording onto steps.STEPS (in place)."""
    for s in steps:
        for k, v in STEP.get(s["id"], {}).items():
            s[k] = v
        for a in s["actions"]:
            if a["id"] in ACT:
                a["title"], a["text"] = ACT[a["id"]]
            if a["id"] in metrics.INFO:
                a["why"], a["how"] = metrics.INFO[a["id"]]
