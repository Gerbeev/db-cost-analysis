"""Playbook definition for the web UI: steps, actions and translations (EN / RU).

Action kinds
  settings  - edit audit periods / currency (audit.json, mirrored into scope_record §3)
  edit      - open a markdown file of the audit in the editor (`file`, optional `create` text)
  register  - open a living register in the table editor (`register`)
  upload    - upload a portal export into `folder` with a suggested `name`
  tool      - run a tool from tools/ (`tool`, fixed `preset` values, output `out`)
  calc      - run a built-in calculator (`calc`)
  sql       - show / run read-only Databricks SQL (`sqls`: list of playbook SQL files)
  docs      - links to documentation pages (`links`)
"""
from __future__ import annotations


def T(en: str, ru: str) -> dict:
    return {"en": en, "ru": ru}


def A(id_: str, kind: str, en: str, ru: str, text_en: str = "", text_ru: str = "", **kw) -> dict:
    return {"id": id_, "kind": kind, "title": T(en, ru), "text": T(text_en, text_ru), **kw}


def SQL(step_folder: str, *names: str) -> list[str]:
    return [f"playbook/{step_folder}/sql/{n}.sql" for n in names]


RULES_DOC = "reference/05_audit_rules.md"
STOP_DOC = "reference/04_pitfalls_and_stop_rules.md"

STEPS: list[dict] = [
    {
        "id": "00", "folder": "00_frame",
        "title": T("Frame the question", "Постановка вопроса"),
        "question": T("What exactly are we auditing - scope, periods, currency, ledger?",
                      "Что именно проверяем - охват, периоды, валюта, учётный регистр?"),
        "goal": T("A written, unambiguous audit question, scope and period set, approved before any data work.",
                  "Записанный однозначный вопрос аудита, охват и периоды, утверждённые до любой работы с данными."),
        "gate": T("G0 - scope, periods, currency and ledger are written and approved. Do not request exports before G0.",
                  "G0 - охват, периоды, валюта и регистр записаны и утверждены. Не запрашивайте выгрузки до G0."),
        "docs": ["playbook/00_frame/README.md", "reference/00_fundamentals.md",
                 "reference/02_access_and_data_collection.md", RULES_DOC],
        "actions": [
            A("0.1", "settings", "Analysis window, provisional B / C / P, currency",
              "Окно анализа, предварительные B / C / P, валюта",
              "Full months only (default 10-12), current month-to-date excluded. All period ends are **exclusive** "
              "(first day after the period). Values are mirrored into `scope_record.md` §3 and pre-fill every tool "
              "and SQL parameter.",
              "Только полные месяцы (обычно 10-12), текущий неполный месяц исключён. Конец периода **не включается** "
              "(первый день после периода). Значения дублируются в `scope_record.md` §3 и подставляются во все "
              "инструменты и параметры SQL."),
            A("0.2", "edit", "Scope record (trigger, scope, sources, approval)",
              "Запись об охвате (повод, охват, источники, утверждение)",
              "One file, four blocks, in order. §1: who saw the growth, in which report, which metric; the question "
              "on Azure Actual Cost. §2: billing account/profile, subscriptions, Databricks account and workspaces "
              "with regions, managed and dependency resource groups, agreement type, commitments with dates. "
              "§3-§4: rule deviations and the status of every data source (OK / DENIED / UNKNOWN). §8: name and date "
              "of the audit owner who approved the scope. Then tick G0.",
              "Один файл, четыре блока по порядку. §1: кто увидел рост, в каком отчёте, какая метрика; вопрос по "
              "Azure Actual Cost. §2: биллинговый аккаунт/профиль, подписки, аккаунт Databricks и workspace с "
              "регионами, managed и зависимые группы ресурсов, тип договора, обязательства с датами. §3-§4: "
              "отклонения от правил и статус каждого источника данных (OK / DENIED / UNKNOWN). §8: имя и дата "
              "владельца аудита, утвердившего охват. Затем отметьте G0.",
              file="scope_record.md", docs=["reference/02_access_and_data_collection.md", RULES_DOC]),
            A("0.3", "edit", "Step notes", "Заметки шага", "Observations, decisions, open questions.",
              "Наблюдения, решения, открытые вопросы.", file="00_frame/notes.md"),
        ],
    },
    {
        "id": "01", "folder": "01_data_quality",
        "title": T("Data quality", "Качество данных"),
        "question": T("Is the data complete, deduplicated, single-currency, priceable?",
                      "Данные полные, без дублей, в одной валюте, оцениваемые по прайсу?"),
        "goal": T("One complete, deduplicated, comparable dataset per ledger before any delta is computed.",
                  "Один полный, дедуплицированный, сопоставимый набор данных на регистр до расчёта любых дельт."),
        "gate": T("G1 - R6 and R7 pass, or the failing scope / SKUs are excluded and recorded as limitations in §5.",
                  "G1 - R6 и R7 пройдены, либо проблемный охват / SKU исключены и записаны как ограничения в §5."),
        "docs": ["playbook/01_data_quality/README.md", "reference/02_access_and_data_collection.md", STOP_DOC,
                 "reference/11_sql_conventions.md"],
        "actions": [
            A("1.1", "upload", "Azure Actual cost-details export", "Выгрузка детализации Azure Actual",
              "Cost Management → **Exports** → Cost and usage details (**Actual cost**, not Amortized / FOCUS), "
              "**one export run per month**. Concatenate the partitions of one run once (single header) and upload "
              "the consolidated CSV. It becomes the primary export used by all tools.",
              "Cost Management → **Exports** → Cost and usage details (**Actual cost**, не Amortized / FOCUS), "
              "**один запуск выгрузки на месяц**. Объедините части одного запуска один раз (один заголовок) и "
              "загрузите сводный CSV. Он станет основной выгрузкой для всех инструментов.",
              folder="01_data_quality/exports", name="azure_actual__{window}.csv", primary=True,
              docs=["reference/02_access_and_data_collection.md"]),
            A("1.2", "upload", "Export manifests / run IDs", "Манифесты / ID запусков выгрузки",
              "From each monthly export run: `manifest.json` (or one `export_manifest.md` list of run IDs).",
              "Из каждого месячного запуска: `manifest.json` (или один список ID запусков `export_manifest.md`).",
              folder="01_data_quality/exports", name="export_manifest__YYYY-MM.json"),
            A("1.3", "upload", "Cost Analysis monthly (Actual)", "Cost Analysis помесячно (Actual)",
              "Cost Analysis → **Actual**, granularity **Monthly**, same scope, no filters → Download CSV.",
              "Cost Analysis → **Actual**, детализация **Monthly**, тот же охват, без фильтров → Download CSV.",
              folder="01_data_quality/exports", name="cost_analysis_monthly__{window}.csv"),
            A("1.4", "tool", "Monthly totals of the export", "Помесячные итоги выгрузки",
              "Totals and per-day rates per month from the consolidated export.",
              "Итоги и суточные ставки по месяцам из сводной выгрузки.",
              tool="monthly", out="01_data_quality/results/export_monthly__{today}.csv"),
            A("1.5", "calc", "R6 reconciliation (≤ 0.5% per month)", "Сверка R6 (≤ 0,5% по месяцам)",
              "Compares 1.4 with the Cost Analysis download month by month and writes the max diff into §5.",
              "Сравнивает 1.4 с выгрузкой Cost Analysis помесячно и записывает максимальное расхождение в §5.",
              calc="r6"),
            A("1.6", "sql", "Databricks usage coverage and workspace presence",
              "Покрытие использования Databricks и присутствие workspace",
              "Statement A → `1.1_usage_coverage`, statement B → `1.1_workspace_presence`. "
              "Pass: `days_with_data = days_in_month` for every full month.",
              "Запрос A → `1.1_usage_coverage`, запрос B → `1.1_workspace_presence`. "
              "Норма: `days_with_data = days_in_month` для каждого полного месяца.",
              sqls=SQL("01_data_quality", "1.1_usage_coverage"),
              outs={"1.1_usage_coverage": ["1.1_usage_coverage", "1.1_workspace_presence"]}),
            A("1.7", "sql", "Units / SKU inventory", "Инвентаризация единиц / SKU",
              "Never sum quantities across `usage_unit`.", "Никогда не суммируйте количества разных `usage_unit`.",
              sqls=SQL("01_data_quality", "1.2_usage_units_inventory")),
            A("1.8", "sql", "Price-join validation (R7)", "Проверка соединения с прайсом (R7)",
              "SKUs with a `FAIL_*` verdict must be excluded from modeled cost and listed in §5.",
              "SKU с вердиктом `FAIL_*` исключаются из модельной стоимости и перечисляются в §5.",
              sqls=SQL("01_data_quality", "1.3_price_join_check")),
            A("1.9", "edit", "System tables per region; data-quality summary", "Системные таблицы по регионам; итог качества",
              "§4: availability of `system.lakeflow`, `compute`, `query`, `access` per region (Catalog Explorer → "
              "system). §5: data-quality results and limitations carried forward.",
              "§4: наличие `system.lakeflow`, `compute`, `query`, `access` по регионам (Catalog Explorer → system). "
              "§5: результаты проверки качества и переносимые ограничения.", file="scope_record.md"),
        ],
    },
    {
        "id": "02", "folder": "02_confirm_and_size",
        "title": T("Confirm and size", "Подтверждение и размер"),
        "question": T("Did billed cost really grow, by how much per day, since when?",
                      "Действительно ли выросли выставленные затраты, на сколько в сутки, с какого дня?"),
        "goal": T("Prove the increase exists on Azure Actual, size it per day, date its onset, set final B / C / P.",
                  "Доказать рост в Azure Actual, измерить его в сутки, датировать начало, зафиксировать B / C / P."),
        "gate": T("G2 - Δ_day > 0 on Azure Actual at fixed scope and shape classified. If Δ_day ≤ 0: record the "
                  "artefact path in §6, do step 03, mark 04-07 `[-] | artefact path`, go to 09.",
                  "G2 - Δ_сутки > 0 в Azure Actual при фиксированном охвате и форма классифицирована. Если "
                  "Δ_сутки ≤ 0: запишите «артефакт» в §6, выполните шаг 03, отметьте 04-07 `[-] | artefact path`, "
                  "перейдите к 09."),
        "docs": ["playbook/02_confirm_and_size/README.md", "reference/03_analysis_method.md", RULES_DOC],
        "actions": [
            A("2.1", "tool", "Monthly series with per-day rates", "Помесячный ряд с суточными ставками",
              "Full scope, no service filter.", "Полный охват, без фильтра по сервису.",
              tool="monthly", out="02_confirm_and_size/results/monthly_series__{today}.csv"),
            A("2.2", "upload", "Daily Actual cost (optional)", "Суточные затраты Actual (необязательно)",
              "Cost Analysis → Actual, **Daily**, ≥ 90 days around the suspected change → Download. Not needed if the "
              "consolidated export is used for onset detection.",
              "Cost Analysis → Actual, **Daily**, ≥ 90 дней вокруг предполагаемого изменения → Download. Не нужно, "
              "если для определения начала используется сводная выгрузка.",
              folder="02_confirm_and_size/exports", name="cost_analysis_daily__{window}.csv"),
            A("2.3", "tool", "Onset on Azure Actual (R5)", "Начало роста в Azure Actual (R5)",
              "Baseline = provisional B. Record the onset date (or “spike only”) in §6.",
              "Базовый период = предварительный B. Запишите дату начала (или «только всплеск») в §6.",
              tool="onset", out="02_confirm_and_size/results/onset_azure__{today}.csv"),
            A("2.4", "sql", "Onset cross-check on Databricks modeled cost", "Сверка начала по модельной стоимости Databricks",
              "Difference to the Azure onset in days (± 1 day expected).",
              "Разница с началом по Azure в днях (ожидается ± 1 день).",
              sqls=SQL("02_confirm_and_size", "2.1_daily_cost_onset")),
            A("2.5", "sql", "Monthly modeled cost by SKU", "Помесячная модельная стоимость по SKU",
              "Also the input of the monthly analyzer and of the R8 direction check.",
              "Также вход помесячного анализатора и проверки направления R8.",
              sqls=SQL("02_confirm_and_size", "2.2_monthly_cost_by_sku")),
            A("2.6", "settings", "Final B / C / P (R2)", "Итоговые B / C / P (R2)",
              "B ≥ 28 stable days before onset; C = first full elevated month; P = month after C.",
              "B ≥ 28 стабильных дней до начала; C = первый полный месяц на новом уровне; P = месяц после C."),
            A("2.7", "calc", "Size the increase and fill TOTAL", "Размер роста и строка TOTAL",
              "Δ_abs, Δ_day, Δ_day %, ×365 and persistence r(P) - r(C) → `scope_record.md` §6 and the `TOTAL` row "
              "of `delta_bridge.csv`.",
              "Δ_abs, Δ_сутки, Δ_сутки %, ×365 и устойчивость r(P) - r(C) → `scope_record.md` §6 и строка `TOTAL` "
              "в `delta_bridge.csv`.", calc="size"),
            A("2.8", "edit", "Shape and onset in §6", "Форма и начало роста в §6",
              "Classify the shape: step / ramp / spike / seasonal (check prior year if data exists). Record both onset "
              "dates.",
              "Классифицируйте форму: ступенька / рампа / всплеск / сезонность (сверьте с прошлым годом при наличии "
              "данных). Запишите обе даты начала.", file="scope_record.md"),
            A("2.9", "tool", "Monthly analyzer (optional)", "Помесячный анализатор (необязательно)",
              "Monthly reports from the Azure export and the 2.2 result, kept as separate ledgers.",
              "Помесячные отчёты из выгрузки Azure и результата 2.2 - регистры не смешиваются.",
              tool="analyze", out="02_confirm_and_size/results/analyzer__{today}"),
        ],
    },
    {
        "id": "03", "folder": "03_accounting_effects",
        "title": T("Accounting effects", "Учётные эффекты"),
        "question": T("How much is calendar / purchases / credits / FX / scope / price?",
                      "Сколько дают календарь / покупки / кредиты / курс / охват / цена?"),
        "goal": T("Separate non-operational movement from consumption growth before any workload analysis.",
                  "Отделить неоперационные изменения от роста потребления до анализа нагрузок."),
        "gate": T("G3 - every test PASS / EFFECT QUANTIFIED / N/A in §7; operational Δ computed. If R8 fails, resolve "
                  "discount / commitment / scope before step 05.",
                  "G3 - каждый тест PASS / EFFECT QUANTIFIED / N/A в §7; операционная Δ рассчитана. Если R8 не "
                  "пройдена, устраните расхождения скидок / обязательств / охвата до шага 05."),
        "docs": ["playbook/03_accounting_effects/README.md", "reference/00_fundamentals.md",
                 "playbook/06_root_cause/playbooks/12_rate_and_accounting.md"],
        "actions": [
            A("3.1", "register", "Calendar effect → ACC-01", "Календарный эффект → ACC-01",
              "Per-day comparison removes month length; fill ACC-01 only if monthly totals are reported "
              "(Feb 28 d → Mar 31 d = +10.7% at flat usage).",
              "Сравнение в сутки убирает длину месяца; заполняйте ACC-01, только если в отчётах помесячные итоги "
              "(фев 28 д → мар 31 д = +10,7% при неизменном потреблении).", register="delta_bridge"),
            A("3.2", "upload", "Charge type and pricing model, B and C", "Тип начисления и модель цены, B и C",
              "Cost Analysis → Actual, group by **Charge type** (and separately **Pricing model**), periods B and C. "
              "Upload `charge_type__…csv` and `pricing_model__…csv`. Purchases → ACC-02, lost commitment → ACC-03.",
              "Cost Analysis → Actual, группировка по **Charge type** (и отдельно **Pricing model**), периоды B и C. "
              "Загрузите `charge_type__…csv` и `pricing_model__…csv`. Покупки → ACC-02, потеря покрытия → ACC-03.",
              folder="03_accounting_effects/exports", name="charge_type__{details}.csv"),
            A("3.3", "upload", "Amortized monthly", "Amortized помесячно",
              "Cost Analysis → **Amortized**, monthly, same scope. Divergence vs Actual explained → ACC-02.",
              "Cost Analysis → **Amortized**, помесячно, тот же охват. Расхождение с Actual объяснить → ACC-02.",
              folder="03_accounting_effects/exports", name="amortized_monthly__{window}.csv"),
            A("3.4", "upload", "Credits / refunds / adjustments (optional)", "Кредиты / возвраты / корректировки (необяз.)",
              "Charge type Refund / Adjustment; credit balances and expiry dates in the billing profile → ACC-04.",
              "Charge type Refund / Adjustment; остатки и сроки кредитов в биллинговом профиле → ACC-04.",
              folder="03_accounting_effects/exports", name="credits__{details}.csv"),
            A("3.5", "tool", "Scope change: subscriptions B vs C", "Изменение охвата: подписки B и C",
              "Plus workspaces `APPEARED_IN_WINDOW` from 1.6 → ACC-07.",
              "Плюс workspace `APPEARED_IN_WINDOW` из 1.6 → ACC-07.",
              tool="delta", preset={"group": "SubscriptionId"},
              out="03_accounting_effects/results/delta_by_subscription_scope__{details}__{today}.csv"),
            A("3.6", "tool", "Billed rate change: top meters", "Изменение тарифа: основные счётчики",
              "Δ/day by meter; for the top meters compare `EffectivePrice` B vs C in the export → ACC-05. "
              "Tier change Standard → Premium (auto-upgrade 1 Oct 2026; SKU `STANDARD_*` → `PREMIUM_*` in 1.7) → ACC-05.",
              "Δ/сутки по счётчикам; для основных сравните `EffectivePrice` B и C в выгрузке → ACC-05. "
              "Смена уровня Standard → Premium (автоапгрейд 1 окт 2026; SKU `STANDARD_*` → `PREMIUM_*` в 1.7) → ACC-05.",
              tool="delta", preset={"group": "MeterName"},
              out="03_accounting_effects/results/effective_price_top_meters__{details}__{today}.csv"),
            A("3.7", "sql", "List price history", "История прайс-листа",
              "Databricks list-price versions inside the window → ACC-05.",
              "Версии прайс-листа Databricks внутри окна → ACC-05.",
              sqls=SQL("03_accounting_effects", "3.1_list_price_history")),
            A("3.8", "edit", "FX, tier, late corrections", "Курс, уровень, поздние корректировки",
              "FX: billing vs pricing currency, rate B vs C → ACC-06. Late corrections: re-export one month and "
              "compare; `RETRACTION` / `RESTATEMENT` counts from 1.6 → ACC-08.",
              "Курс: валюта счёта vs валюта прайса, курс B и C → ACC-06. Поздние корректировки: перевыгрузите один "
              "месяц и сравните; количество `RETRACTION` / `RESTATEMENT` из 1.6 → ACC-08.",
              file="03_accounting_effects/notes.md"),
            A("3.9", "calc", "Direction check (R8)", "Проверка направления (R8)",
              "Δ% of Azure meter *Azure Databricks* vs Δ% of modeled cost (2.5): same sign and ≤ 15 pp apart.",
              "Δ% сервиса Azure *Azure Databricks* vs Δ% модельной стоимости (2.5): один знак и разница ≤ 15 п.п.",
              calc="r8"),
            A("3.10", "register", "ACC lines in the bridge", "Строки ACC в мосте",
              "Fill `delta_per_day`, `status`, `evidence_ids` for ACC-01 … ACC-08 (0 if no effect).",
              "Заполните `delta_per_day`, `status`, `evidence_ids` для ACC-01 … ACC-08 (0 при отсутствии эффекта).",
              register="delta_bridge"),
            A("3.11", "calc", "Operational Δ", "Операционная Δ",
              "TOTAL - Σ ACC → `scope_record.md` §7.", "TOTAL - Σ ACC → `scope_record.md` §7.", calc="operational"),
            A("3.12", "register", "Hypotheses H-RAT-01…11", "Гипотезы H-RAT-01…11",
              "Set the status of every rate / accounting hypothesis.", "Задайте статус каждой гипотезы тарифа / учёта.",
              register="hypothesis_register"),
            A("3.13", "edit", "Accounting results in §7", "Учётные результаты в §7",
              "One line per test: PASS / EFFECT / N/A, Δr per day, evidence ID.",
              "Строка на тест: PASS / EFFECT / N/A, Δr в сутки, ID доказательства.", file="scope_record.md"),
        ],
    },
    {
        "id": "04", "folder": "04_azure_decomposition",
        "title": T("Azure decomposition", "Декомпозиция Azure"),
        "question": T("Which Azure services / meters / resources were billed more?",
                      "По каким сервисам / счётчикам / ресурсам Azure выставлено больше?"),
        "goal": T("Know what was billed more, one mutually exclusive grouping at a time, and assign every material "
                  "line to a cost bucket.",
                  "Понять, что выставлено больше, по одной взаимоисключающей группировке за раз, и отнести каждую "
                  "существенную строку к корзине затрат."),
        "gate": T("G4 - Σ bucket Δ = operational Δ (± 1%); every material line has a bucket.",
                  "G4 - Σ Δ корзин = операционная Δ (± 1%); у каждой существенной строки есть корзина."),
        "docs": ["playbook/04_azure_decomposition/README.md", "reference/03_analysis_method.md",
                 "reference/01_cost_model.md"],
        "actions": [
            A("4.1", "calc", "Azure decomposition: subscription, service, meter, resource group, resource",
              "Декомпозиция Azure: подписка, сервис, счётчик, группа ресурсов, ресурс",
              "One run produces the five groupings of Δ/day between B and C. A grouping whose columns are missing in "
              "the export schema (EA / MCA differ) is reported; the others are still written.",
              "Один запуск строит пять группировок Δ/сутки между B и C. Группировка, для которой в схеме выгрузки "
              "нет колонок (EA и MCA различаются), будет показана в предупреждении; остальные записываются.",
              calc="decompose"),
            A("4.2", "tool", "Workspace ↔ managed RG ↔ dependency RG map", "Карта workspace ↔ managed RG ↔ зависимые RG",
              "Read-only Azure CLI inventory (requires `az login` on this computer).",
              "Инвентаризация через Azure CLI, только чтение (нужен `az login` на этом компьютере).",
              tool="inventory", out="04_azure_decomposition/results/workspace_rg_map__{today}.csv"),
            A("4.2b", "upload", "Workspace map (manual alternative)", "Карта workspace (ручной вариант)", "", "",
              folder="04_azure_decomposition/results", name="workspace_rg_map.csv"),
            A("4.3", "register", "BUCKET lines in the bridge", "Строки BUCKET в мосте",
              "Material line (R3): |Δ/day| ≥ 5% of total or top-10 positive. Buckets: `DBX_PLATFORM`, "
              "`DBX_CLASSIC_INFRA`, `STORAGE`, `NETWORK`, `MONITORING`, `SHARED_UNALLOCATED`, `OUT_OF_SCOPE`. "
              "Keep negative movers. A managed RG is a mapping hint, not proof of ownership.",
              "Существенная строка (R3): |Δ/сутки| ≥ 5% итога или топ-10 положительных. Корзины: `DBX_PLATFORM`, "
              "`DBX_CLASSIC_INFRA`, `STORAGE`, `NETWORK`, `MONITORING`, `SHARED_UNALLOCATED`, `OUT_OF_SCOPE`. "
              "Отрицательные изменения сохраняйте. Managed RG - подсказка, а не доказательство владения.",
              register="delta_bridge"),
        ],
    },
    {
        "id": "05", "folder": "05_databricks_decomposition",
        "title": T("Databricks decomposition", "Декомпозиция Databricks"),
        "question": T("Which products / SKUs / workspaces / objects consumed more?",
                      "Какие продукты / SKU / workspace / объекты потребили больше?"),
        "goal": T("Explain DBX_PLATFORM (and drive DBX_CLASSIC_INFRA) by product → SKU → workspace → object and "
                  "produce the driver-candidate list.",
                  "Объяснить DBX_PLATFORM (и DBX_CLASSIC_INFRA) по цепочке продукт → SKU → workspace → объект и "
                  "составить список кандидатов в драйверы."),
        "gate": T("G5 - top objects explain ≥ 90% of modeled DBX_PLATFORM Δ, or the unattributed remainder is "
                  "quantified.",
                  "G5 - основные объекты объясняют ≥ 90% модельной Δ DBX_PLATFORM, либо неатрибутированный "
                  "остаток количественно оценён."),
        "docs": ["playbook/05_databricks_decomposition/README.md", "reference/11_sql_conventions.md",
                 "reference/01_cost_model.md"],
        "rules": T("Quantities only within one `usage_unit`; money only for SKUs that pass R7. Classic compute: DBU and "
                   "VM are **both** billed. Serverless: never add VM cost. `job_id` is NULL for jobs on all-purpose "
                   "clusters - that usage appears as `CLUSTER`.",
                   "Количества - только в пределах одного `usage_unit`; деньги - только для SKU, прошедших R7. "
                   "Классические вычисления: DBU и VM выставляются **оба**. Serverless: стоимость VM не добавлять. "
                   "`job_id` пуст для задач на all-purpose кластерах - такое потребление видно как `CLUSTER`."),
        "actions": [
            A("5.1", "sql", "Products / SKUs: volume vs rate", "Продукты / SKU: объём vs цена",
              "`volume_effect` vs `rate_effect`; GONE + NEW pairs = MIX_SHIFT.",
              "`volume_effect` vs `rate_effect`; пары GONE + NEW = MIX_SHIFT.",
              sqls=SQL("05_databricks_decomposition", "5.1_sku_volume_rate")),
            A("5.2", "sql", "Workspaces", "Workspace",
              "One workspace = local change; spread = platform / price.",
              "Один workspace - локальное изменение; во всех - платформа / цена.",
              sqls=SQL("05_databricks_decomposition", "5.2_workspace_delta")),
            A("5.3", "sql", "Objects (job, pipeline, warehouse, cluster, endpoint, app, notebook, pool)",
              "Объекты (job, pipeline, warehouse, cluster, endpoint, app, notebook, pool)",
              "`change_class`, `cumulative_share` up to 0.90 (checked automatically).",
              "`change_class`, `cumulative_share` до 0,90 (проверяется автоматически).",
              sqls=SQL("05_databricks_decomposition", "5.3_object_delta")),
            A("5.4", "sql", "Daily cost of top objects", "Суточная стоимость основных объектов",
              "`object_ids` = top IDs from 5.3; object onset vs total onset (± 2 days). Window: 30 days before B "
              "through end of C.",
              "`object_ids` = основные ID из 5.3; начало по объекту vs общее начало (± 2 дня). Окно: 30 дней до B "
              "и до конца C.", sqls=SQL("05_databricks_decomposition", "5.4_object_daily")),
            A("5.5", "sql", "Attribution coverage", "Покрытие атрибуции",
              "Unattributed share → step 07.", "Неатрибутированная доля → шаг 07.",
              sqls=SQL("05_databricks_decomposition", "5.5_attribution_coverage")),
            A("5.6", "sql", "First-seen products / SKUs", "Впервые появившиеся продукты / SKU",
              "`new_in_window` near the onset.", "`new_in_window` около даты начала.",
              sqls=SQL("05_databricks_decomposition", "5.6_first_seen_skus")),
            A("5.7", "register", "DRIVER_CANDIDATE lines", "Строки DRIVER_CANDIDATE",
              "One line per top object / SKU: Δ/day in list price, object, change_class.",
              "Строка на каждый основной объект / SKU: Δ/сутки по прайсу, объект, change_class.",
              register="delta_bridge"),
            A("5.8", "register", "Open matching hypotheses", "Открыть соответствующие гипотезы", "", "",
              register="hypothesis_register"),
        ],
    },
    {
        "id": "06", "folder": "06_root_cause",
        "title": T("Root cause", "Первопричина"),
        "question": T("What changed, when, and how much does it explain?",
                      "Что изменилось, когда и сколько это объясняет?"),
        "goal": T("For every material driver: a dated technical mechanism with quantified effect, evidenced per R9.",
                  "Для каждого существенного драйвера: датированный технический механизм с количественным эффектом, "
                  "доказанный по R9."),
        "gate": T("G6 - every material driver has a driver card and a status other than HYPOTHESIS.",
                  "G6 - у каждого существенного драйвера есть карточка и статус, отличный от HYPOTHESIS."),
        "docs": ["playbook/06_root_cause/README.md", RULES_DOC, "reference/03_analysis_method.md"],
        "rules": T("R9: (a) Δ visible in Azure Actual · (b) change timestamp within ± 2 days of the driver onset · "
                   "(c) mechanism explains ≥ 70% of the driver Δ · (d) ≥ 1 alternative falsified. Time correlation "
                   "alone is never CONFIRMED. List price → billed: ratio = Azure DBX_PLATFORM Δ / modeled DBX Δ.",
                   "R9: (a) Δ видна в Azure Actual · (b) время изменения в пределах ± 2 дней от начала драйвера · "
                   "(c) механизм объясняет ≥ 70% Δ драйвера · (d) опровергнута ≥ 1 альтернатива. Одна лишь "
                   "корреляция по времени никогда не даёт CONFIRMED. Прайс → счёт: коэффициент = Δ Azure "
                   "DBX_PLATFORM / модельная Δ DBX."),
        "actions": [
            A("6.0", "docs", "Route each driver to its playbook", "Направьте каждый драйвер в свой плейбук",
              "JOBS ↑ → Jobs · DLT ↑ → Pipelines · ALL_PURPOSE ↑ or VM ↑ with DBU ↑ → Classic compute · VM ↑ with DBU "
              "flat → Instance pools · SQL ↑ → SQL warehouses · serverless SKUs ↑ → Serverless · MODEL_SERVING / "
              "VECTOR_SEARCH / AI / APPS ↑ → AI and apps · PREDICTIVE_OPTIMIZATION / MONITORING / NETWORKING ↑ → "
              "Platform features · buckets STORAGE / NETWORK / MONITORING → 09 / 10 / 11 · step 03 effects → 12.",
              "JOBS ↑ → Jobs · DLT ↑ → Pipelines · ALL_PURPOSE ↑ или VM ↑ вместе с DBU ↑ → Classic compute · VM ↑ "
              "при неизменных DBU → Instance pools · SQL ↑ → SQL warehouses · serverless SKU ↑ → Serverless · "
              "MODEL_SERVING / VECTOR_SEARCH / AI / APPS ↑ → AI and apps · PREDICTIVE_OPTIMIZATION / MONITORING / "
              "NETWORKING ↑ → Platform features · корзины STORAGE / NETWORK / MONITORING → 09 / 10 / 11 · "
              "эффекты шага 03 → 12.",
              links=[f"playbook/06_root_cause/playbooks/{n}.md" for n in (
                  "01_jobs", "02_pipelines", "03_classic_compute", "04_instance_pools", "05_sql_warehouses",
                  "06_serverless", "07_ai_and_apps", "08_platform_features", "09_storage", "10_network",
                  "11_monitoring", "12_rate_and_accounting")]),
            A("6.1", "calc", "New driver card", "Новая карточка драйвера",
              "Creates `06_root_cause/driver_<nn>_<name>.md` from the template and opens it.",
              "Создаёт `06_root_cause/driver_<nn>_<name>.md` из шаблона и открывает его.", calc="driver_card"),
            A("6.2", "sql", "Playbook diagnostics", "Диагностика по плейбуку",
              "Choose the query the playbook asks for. Quantify: frequency × unit cost (6.01) or volume × rate (5.1). "
              "Change event: SCD2 history (6.04, 6.06, 6.09), audit (6.14), release / Git / Activity Log / tickets.",
              "Выберите запрос, указанный в плейбуке. Количественно: частота × стоимость запуска (6.01) или объём × "
              "цена (5.1). Событие изменения: история SCD2 (6.04, 6.06, 6.09), аудит (6.14), релизы / Git / "
              "Activity Log / тикеты.",
              sqls=SQL("06_root_cause", "6.01_job_cost_per_run", "6.02_job_runs_monthly", "6.03_job_runs_daily",
                       "6.04_job_definition_changes", "6.05_pipeline_updates", "6.06_cluster_config_history",
                       "6.07_node_utilization", "6.08_pool_idle", "6.09_warehouse_config_history",
                       "6.10_warehouse_events", "6.11_query_trends", "6.12_query_clients",
                       "6.13_serverless_and_features", "6.14_audit_change_events",
                       "6.15_dbu_per_node_hour")),
            A("6.3", "upload", "Other diagnostics (UI screenshots, Spark UI, Activity Log exports)",
              "Прочая диагностика (скриншоты, Spark UI, выгрузки Activity Log)", "", "",
              folder="06_root_cause/results", name="6.xx_name__{today}.csv"),
            A("6.4", "register", "Hypothesis statuses (R9)", "Статусы гипотез (R9)",
              "CONFIRMED (a+b+c+d) / LIKELY / REJECTED / UNKNOWN.", "CONFIRMED (a+b+c+d) / LIKELY / REJECTED / UNKNOWN.",
              register="hypothesis_register"),
            A("6.5", "register", "ROOT_CAUSE lines", "Строки ROOT_CAUSE",
              "Δ/day in Azure Actual currency, status, hypothesis_id, evidence_ids.",
              "Δ/сутки в валюте Azure Actual, статус, hypothesis_id, evidence_ids.", register="delta_bridge"),
        ],
    },
    {
        "id": "07", "folder": "07_attribution_and_residual",
        "title": T("Attribution and residual", "Атрибуция и остаток"),
        "question": T("Who owns each part; what is unexplained?", "Кому принадлежит каждая часть; что не объяснено?"),
        "goal": T("Every unit of Δ has an owner or is explicitly unresolved; the delta bridge closes.",
                  "Каждая единица Δ имеет владельца или явно не объяснена; мост дельты сходится."),
        "gate": T("G7 - bridge closes; UNEXPLAINED ≤ 10% or explicitly accepted by the audit owner "
                  "(C7.6 `[!] | accepted by <owner>`).",
                  "G7 - мост сходится; UNEXPLAINED ≤ 10% или явно принят владельцем аудита "
                  "(C7.6 `[!] | accepted by <owner>`)."),
        "docs": ["playbook/07_attribution_and_residual/README.md"],
        "actions": [
            A("7.1", "register", "Owners of CONFIRMED / LIKELY lines", "Владельцы строк CONFIRMED / LIKELY",
              "Workspace owner, job owner, tags `owner`, `cost_center`, `application`; `sample_run_as` from 5.3.",
              "Владелец workspace, владелец задачи, теги `owner`, `cost_center`, `application`; `sample_run_as` из 5.3.",
              register="delta_bridge"),
            A("7.2", "upload", "Shared allocation keys (optional)", "Ключи распределения общих ресурсов (необяз.)",
              "Allocate only with an evidenced key (usage share, bytes, request count); otherwise line SH-01.",
              "Распределяйте только по доказанному ключу (доля использования, байты, запросы); иначе строка SH-01.",
              folder="07_attribution_and_residual/results", name="shared_allocation__{details}.csv"),
            A("7.3", "edit", "Unattributed / untagged Databricks Δ", "Неатрибутированная / без тегов Δ Databricks",
              "From `5.5_attribution_coverage` (step 05).", "Из `5.5_attribution_coverage` (шаг 05).",
              file="07_attribution_and_residual/notes.md"),
            A("7.4", "register", "SH-01 and OOS-01", "SH-01 и OOS-01",
              "Shared unallocated and out-of-scope (non-Databricks services from step 04).",
              "Общие нераспределённые и вне охвата (не-Databricks сервисы из шага 04).", register="delta_bridge"),
            A("7.5", "calc", "Residual UNX and shares", "Остаток UNX и доли",
              "UNX = TOTAL - Σ(ACCOUNTING + ROOT_CAUSE + SHARED_UNALLOCATED + OUT_OF_SCOPE); BUCKET and "
              "DRIVER_CANDIDATE are informational.",
              "UNX = TOTAL - Σ(ACCOUNTING + ROOT_CAUSE + SHARED_UNALLOCATED + OUT_OF_SCOPE); BUCKET и "
              "DRIVER_CANDIDATE - справочные.", calc="unx"),
        ],
    },
    {
        "id": "08", "folder": "08_validation",
        "title": T("Validation", "Валидация"),
        "question": T("Are the numbers reproducible and the claims evidenced?",
                      "Воспроизводимы ли цифры и доказаны ли утверждения?"),
        "goal": T("Findings survive independent review; every reported number is reproducible.",
                  "Выводы выдерживают независимую проверку; каждое число воспроизводимо."),
        "gate": T("G8 - all numbers reproducible; reviewer sign-off in §8.",
                  "G8 - все числа воспроизводимы; подпись проверяющего в §8."),
        "docs": ["playbook/08_validation/README.md", "reference/06_ibm_apptio_lens.md", "reference/07_ibm_api_setup.md"],
        "actions": [
            A("8.1", "calc", "Reproduce every evidence row", "Воспроизвести каждую строку доказательств",
              "Re-runs every tool and (if a Databricks connection is set) every SQL with the recorded parameters and "
              "compares the outputs → `reproduction_log`. Manual rows must be checked by hand.",
              "Перезапускает каждый инструмент и (при настроенном подключении Databricks) каждый SQL с сохранёнными "
              "параметрами и сравнивает результаты → `reproduction_log`. Ручные строки проверяются вручную.",
              calc="reproduce"),
            A("8.2", "register", "Re-check R9 for CONFIRMED", "Перепроверка R9 для CONFIRMED",
              "Downgrade to LIKELY if a criterion is missing.", "Понизьте до LIKELY, если не хватает критерия.",
              register="hypothesis_register"),
            A("8.3", "edit", "Cross-check alternative views", "Сверка с альтернативными представлениями",
              "Azure Amortized (step 03), Databricks usage dashboard, IBM if licensed - differences explained, never "
              "added.",
              "Azure Amortized (шаг 03), дашборд использования Databricks, IBM при наличии лицензии - расхождения "
              "объясняются, но не суммируются.", file="08_validation/results/cross_check.md",
              create="# Cross-check of alternative views\n\n| View | Scope / metric | Value B | Value C | Δ/day | "
                     "Difference vs Azure Actual | Explanation |\n|---|---|---|---|---|---|---|\n| Azure Amortized | | | "
                     "| | | |\n| Databricks usage dashboard | | | | | | |\n| IBM Cloudability / ApptioOne | | | | | | |\n"),
            A("8.4", "tool", "IBM Cloudability: verify access (optional)", "IBM Cloudability: проверка доступа (необяз.)",
              "", "", tool="cloudability_probe", out="08_validation/exports/cloudability_measures__{today}.json",
              docs=["reference/07_ibm_api_setup.md"]),
            A("8.5", "tool", "IBM Cloudability: export (optional)", "IBM Cloudability: выгрузка (необяз.)",
              "", "", tool="cloudability_export", out="08_validation/exports/apptio_cloudability__{window}.csv"),
            A("8.6", "tool", "IBM ApptioOne: download report (optional)", "IBM ApptioOne: загрузка отчёта (необяз.)",
              "", "", tool="apptioone_download", out="08_validation/exports/apptioone_report__{today}{ext}"),
            A("8.7", "tool", "IBM ApptioOne: normalize (optional)", "IBM ApptioOne: нормализация (необяз.)",
              "", "", tool="apptio_normalize", out="08_validation/exports/apptioone_normalized__{today}.csv"),
            A("8.8", "tool", "IBM: analyze export (optional)", "IBM: анализ выгрузки (необяз.)",
              "", "", tool="apptio_analyze", out="08_validation/results/apptio_analysis__{today}"),
            A("8.9", "register", "IBM discrepancy register", "Реестр расхождений IBM", "", "",
              register="ibm_discrepancy_register"),
            A("8.10", "edit", "Persistence and peer review", "Устойчивость и независимая проверка",
              "Persistence in P per driver (driver cards / notes). Independent reviewer (did not build the analysis) "
              "signs §8.",
              "Устойчивость в P по каждому драйверу (карточки / заметки). Независимый проверяющий (не участвовал в "
              "анализе) подписывает §8.", file="scope_record.md"),
        ],
    },
    {
        "id": "09", "folder": "09_report_and_controls",
        "title": T("Report and controls", "Отчёт и контроль"),
        "question": T("What do we report, fix and monitor?", "Что докладываем, исправляем и отслеживаем?"),
        "goal": T("An approved findings report, remediation backlog and control plan.",
                  "Утверждённый отчёт, план исправлений и план контроля."),
        "gate": T("G9 - report approved; every remediation item has an owner. Savings are claimed only after "
                  "post-change measurement on Azure Actual (≥ 14 days, same method).",
                  "G9 - отчёт утверждён; у каждого пункта исправлений есть владелец. Экономия заявляется только "
                  "после замера в Azure Actual после изменения (≥ 14 дней, тот же метод)."),
        "docs": ["playbook/09_report_and_controls/README.md", "reference/08_remediation_and_controls.md"],
        "actions": [
            A("9.1", "calc", "Bridge as a markdown table", "Мост в виде таблицы markdown",
              "Copy into report §3 - must equal `delta_bridge.csv`.",
              "Скопируйте в §3 отчёта - должно совпадать с `delta_bridge.csv`.", calc="bridge_md"),
            A("9.2", "edit", "Findings report", "Отчёт о выводах",
              "§1 executive summary · §2 size / timing · §3 bridge · §4 one finding per driver · §5-7 rejected, "
              "residual, limitations · §8 remediation and control plan · §9 approval. Fill every `____`.",
              "§1 резюме · §2 размер / время · §3 мост · §4 вывод по каждому драйверу · §5-7 отклонённые, остаток, "
              "ограничения · §8 исправления и план контроля · §9 утверждение. Заполните все `____`.",
              file="09_report_and_controls/findings_report.md", docs=["reference/08_remediation_and_controls.md"]),
        ],
    },
]

# Level of an action: "core" - needed to pass the step; "optional" - collapsed by default (supporting, alternative or
# licence-dependent work). Evidence rows and many checks are filled automatically (tools/check_audit.derive).
OPTIONAL = {"0.3", "2.2", "2.9", "4.2b", "7.2", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9"}
for _s in STEPS:
    for _a in _s["actions"]:
        _a["level"] = "optional" if _a["id"] in OPTIONAL else "core"

from . import plain  # noqa: E402

plain.apply(STEPS)

CHECK_RU = {
    "C0.1": "Повод записан: кто, какой отчёт, какая метрика (scope_record §1)",
    "C0.2": "Вопрос аудита сформулирован для Azure Actual Cost с охватом S, B и C (§1)",
    "C0.3": "Охват полный: биллинговый аккаунт/профиль, подписки, workspace с регионами (§2)",
    "C0.4": "Managed RG каждого workspace и зависимые RG перечислены (§2)",
    "C0.5": "Окно = только полные месяцы; текущий неполный месяц исключён (§3) - авто",
    "C0.6": "Предварительные B / C / P записаны (§3) - авто",
    "C0.7": "Валюта счёта, тип договора, контракты с датами записаны (§2-§3)",
    "C0.8": "У каждого источника в §4 статус OK / DENIED / UNKNOWN",
    "C0.9": "Отклонения от правил записаны или «none» (§3)",
    "G0": "Владелец аудита утвердил охват (имя + дата в §8)",
    "C1.1": "Один запуск выгрузки на месяц; части одного запуска объединены один раз; ID запусков сохранены (STOP-1)",
    "C1.2": "Выгрузка - Actual cost (не Amortized / FOCUS) (STOP-4)",
    "C1.3": "В выгрузке одна валюта счёта (STOP-2) - авто",
    "C1.4": "Нет пропущенных месяцев в окне (STOP-3) - авто",
    "C1.5": "Выгрузка vs Cost Analysis по месяцам ≤ 0,5% или объяснено (R6); макс. расхождение в §5",
    "C1.6": "1.1_usage_coverage: days_with_data = days_in_month для каждого полного месяца",
    "C1.7": "Присутствие workspace проверено; APPEARED_IN_WINDOW отмечены для шага 03 (изменение охвата)",
    "C1.8": "Инвентаризация единиц 1.2 проверена; суммирование разных единиц не планируется",
    "C1.9": "Соединение с прайсом 1.3: все SKU FAIL_* перечислены в §5 и исключены из модели (R7) - авто",
    "C1.10": "Наличие системных таблиц по регионам в §4; отсутствующие = UNKNOWN",
    "C1.11": "Строки доказательств EVD-01-nnn добавлены для каждого сохранённого результата - авто",
    "G1": "R6 и R7 пройдены, либо нарушения записаны как ограничения в §5",
    "C2.1": "Помесячный ряд с суточными ставками построен по выгрузке шага 01 (без фильтра сервиса) - авто",
    "C2.2": "Суточный ряд покрывает ≥ 30 дней до и ≥ 30 дней после предполагаемого изменения",
    "C2.3": "Начало роста в Azure Actual по R5 записано (дата или «только всплеск» с началом/концом)",
    "C2.4": "Начало по модельной стоимости Databricks (2.1) сравнено; разница в днях записана (ожидается ±1 день)",
    "C2.5": "Итоговые B / C / P по R2 в §3 (B ≥ 28 стабильных дней, C полный месяц роста, P месяц после C)",
    "C2.6": "Δ_abs, Δ_сутки, Δ_сутки %, годовой эффект и устойчивость записаны в §6 - авто",
    "C2.7": "Форма классифицирована (ступенька / рампа / всплеск / сезонность); сезонность сверена с прошлым годом",
    "C2.8": "Строка TOTAL в delta_bridge.csv заполнена (cost_per_day_b, cost_per_day_c, delta_per_day, currency) - авто",
    "C2.9": "Строки доказательств EVD-02-nnn добавлены - авто",
    "G2": "Δ_сутки > 0 в Azure Actual при фиксированном охвате - или путь «артефакт» выбран и записан в §6",
    "C3.1": "Календарный эффект оценён (сутки vs месяц) - мост ACC-01",
    "C3.2": "Разбивка по типу начисления и модели цены B vs C проверена; покупки оценены - ACC-02",
    "C3.3": "Actual vs Amortized сравнены; расхождение объяснено - ACC-02",
    "C3.4": "Покрытие обязательств (RI / SP / DBCU) B vs C проверено; остаток и срок DBCU в Портале → Reservations - ACC-03",
    "C3.5": "Кредиты / возвраты / корректировки проверены - ACC-04",
    "C3.6": "Изменение охвата проверено (подписки, workspace, появившиеся в окне) - ACC-07",
    "C3.7": "Курс проверен (валюта счёта vs прайса, курс B vs C) - ACC-06",
    "C3.8": "Цена за единицу (EffectivePrice) основных счётчиков проверена - ACC-05",
    "C3.9": "Версии прайс-листа Databricks в окне проверены (3.1) - ACC-05",
    "C3.10": "Поздние корректировки проверены - ACC-08",
    "C3.11": "Проверка направления R8 пройдена или отклонение объяснено",
    "C3.12": "Операционная Δ = TOTAL - Σ ACC записана в §7",
    "C3.13": "Статусы гипотез H-RAT-01…11 заданы в hypothesis_register.csv",
    "C3.14": "Уровень workspace (Standard / Premium) в B vs C проверен; дата смены записана - ACC-05",
    "C3.15": "Строки доказательств EVD-03-nnn добавлены - авто",
    "G3": "Каждый учётный тест решён; операционная Δ рассчитана",
    "C4.1": "Δ/сутки по подпискам построена - авто",
    "C4.2": "Δ/сутки по сервисам построена - авто",
    "C4.3": "Δ/сутки по счётчикам построена - авто",
    "C4.4": "Δ/сутки по группам ресурсов построена - авто",
    "C4.5": "Δ/сутки по ресурсам построена для существенных строк - авто",
    "C4.6": "Все группировки дают одинаковую Δ/сутки - авто",
    "C4.7": "Отрицательные изменения сохранены (не отфильтрованы)",
    "C4.8": "Каждая существенная строка (R3) отнесена к одной корзине; строки корзин добавлены в delta_bridge.csv",
    "C4.9": "Карта workspace ↔ managed RG ↔ зависимые RG сохранена - авто",
    "C4.10": "Σ Δ корзин = операционная Δ (±1%)",
    "C4.11": "Строки доказательств EVD-04-nnn добавлены - авто",
    "G4": "У каждой существенной строки Azure есть корзина, корзины сходятся с операционной Δ",
    "C5.1": "Для денежных выводов используются только SKU, прошедшие R7",
    "C5.2": "5.1: основные SKU классифицированы как объёмные или ценовые; пары MIX_SHIFT (GONE + NEW) взаимозачтены",
    "C5.3": "5.2: концентрация дельты по workspace отмечена",
    "C5.4": "5.3: объекты перечислены до cumulative_share ≥ 0,90 - авто",
    "C5.5": "5.4: дата начала каждого основного объекта сравнена с общим началом (±2 дня)",
    "C5.6": "5.5: неатрибутированная / без тегов дельта оценена",
    "C5.7": "5.6: новые продукты / SKU в окне перечислены с датой first_seen",
    "C5.8": "Строки DRIVER_CANDIDATE добавлены в delta_bridge.csv",
    "C5.9": "Для каждого кандидата открыты гипотезы в hypothesis_register.csv",
    "C5.10": "Строки доказательств EVD-05-nnn добавлены - авто",
    "G5": "Основные объекты объясняют ≥ 90% модельной дельты DBX, или остаток оценён",
    "C6.1": "Каждая существенная корзина / DRIVER_CANDIDATE направлена в плейбук",
    "C6.2": "Одна карточка на каждый существенный драйвер (driver_<nn>_<name>.md) - авто",
    "C6.3": "Диагностика плейбука сохранена в results/ - авто",
    "C6.4": "Δ каждого драйвера разложена (частота × стоимость запуска или объём × цена)",
    "C6.5": "Для каждого CONFIRMED / LIKELY драйвера найдено событие изменения с временем и источником",
    "C6.6": "Опровергнута ≥ 1 альтернатива на драйвер (R9-d)",
    "C6.7": "R9 применено; статусы заданы в hypothesis_register.csv",
    "C6.8": "Строки ROOT_CAUSE в delta_bridge.csv в валюте Azure Actual/сутки с hypothesis_id и evidence_ids - авто",
    "C6.9": "Коэффициент пересчёта прайс → счёт записан там, где использовался",
    "C6.10": "Строки доказательств EVD-06-nnn добавлены - авто",
    "G6": "Ни один существенный драйвер не остался в статусе HYPOTHESIS",
    "C7.1": "Владелец записан для каждой строки моста CONFIRMED / LIKELY",
    "C7.2": "Общие ресурсы распределены по доказанному ключу или отнесены в SH-01",
    "C7.3": "Неатрибутированная / без тегов Δ Databricks оценена",
    "C7.4": "Δ вне охвата в OOS-01",
    "C7.5": "Тождество моста выполняется с точностью 1% - авто",
    "C7.6": "UNEXPLAINED ≤ 10% от TOTAL (R4) - авто; или `[!] | accepted by <owner>`",
    "C7.7": "Строки доказательств EVD-07-nnn добавлены - авто",
    "G7": "Мост сходится; остаток в пределах R4 или принят",
    "C8.1": "Каждая строка доказательств воспроизведена; расхождения устранены (reproduction_log.md)",
    "C8.2": "R9 перепроверено для каждого CONFIRMED; понижения применены",
    "C8.3": "У каждой гипотезы CONFIRMED есть существующие ID доказательств - авто",
    "C8.4": "Альтернативные представления сверены (Amortized, дашборд использования); расхождения объяснены",
    "C8.5": "Сверка с IBM Cloudability / ApptioOne и реестр расхождений - или `[-] | not licensed`",
    "C8.6": "Устойчивость в P проверена по каждому драйверу",
    "C8.7": "Независимая проверка выполнена (scope §8)",
    "G8": "Числа воспроизводимы; подпись проверяющего",
    "C9.1": "Резюме содержит Δ/сутки, дату начала, % объяснения, драйверы со статусами",
    "C9.2": "Мост в отчёте совпадает с delta_bridge.csv",
    "C9.3": "Блок вывода для каждого драйвера CONFIRMED / LIKELY с ID доказательств",
    "C9.4": "Отклонённые гипотезы, остаток и ограничения перечислены",
    "C9.5": "Пункты исправлений с диапазоном экономии, риском, откатом, владельцем, метрикой проверки",
    "C9.6": "План контроля с владельцами и периодичностью",
    "C9.7": "Плейсхолдеры заполнены - авто",
    "G9": "Отчёт утверждён владельцем аудита; владельцы исправлений назначены",
}


def step(step_id: str) -> dict:
    hit = next((s for s in STEPS if s["id"] == step_id[:2]), None)
    if hit is None:
        raise KeyError(step_id)
    return hit


def action(step_id: str, action_id: str) -> dict:
    hit = next((a for a in step(step_id)["actions"] if a["id"] == action_id), None)
    if hit is None:
        raise KeyError(action_id)
    return hit
