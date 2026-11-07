"""Server-side message translation (EN -> RU) for errors, calculator results and automatic checks.

Messages are produced in English by tools/ and webapp/. The UI sends its language in the X-Lang header;
`tr()` rewrites known messages with regex patterns. Unknown messages are returned unchanged (English).
Rule: ASCII hyphen only, see reference/13_punctuation.md.
"""
from __future__ import annotations

import contextvars
import re

LANG: contextvars.ContextVar[str] = contextvars.ContextVar("lang", default="en")

# (pattern, replacement) - applied with re.sub, first full match wins per segment.
RU: list[tuple[str, str]] = [
    # ---------------------------------------------------------------- automatic checks (tools/check_audit.py)
    (r"^(.+): unreadable \((.*)\)$", r"\1: не читается (\2)"),
    (r"^(.+): currencies (.+) \(STOP-2\)$", r"\1: валюты \2 (STOP-2)"),
    (r"^(.+): months (\S+)\.\.(\S+), gaps none \(STOP-3\)$", r"\1: месяцы \2..\3, пропусков нет (STOP-3)"),
    (r"^(.+): months (\S+)\.\.(\S+), gaps (.+) \(STOP-3\)$", r"\1: месяцы \2..\3, пропуски \4 (STOP-3)"),
    (r"^(.+): (\d+) rows, (\d+) exact duplicate rows \(verify not an overlapping export, STOP-1\)$",
     r"\1: строк \2, точных дублей \3 (проверьте, что выгрузки не перекрываются, STOP-1)"),
    (r"^(.+): (\d+) SKU\(s\) fail R7 - must be excluded from modeled cost (.*)$",
     r"\1: SKU, не прошедших R7: \2 - исключите их из модельной стоимости \3"),
    (r"^delta_bridge\.csv: TOTAL row has no numeric delta_per_day$",
     "delta_bridge.csv: в строке TOTAL нет числового delta_per_day"),
    (r"^delta_bridge\.csv: TOTAL delta_per_day = (.+)$", r"delta_bridge.csv: TOTAL delta_per_day = \1"),
    (r"^fewer than 2 delta_by_\*\.csv files - grouping consistency not checked$",
     "меньше 2 файлов delta_by_*.csv - согласованность группировок не проверена"),
    (r"^groupings of the same ledger must total the same delta/day: (.*)$",
     r"группировки одного регистра должны давать одинаковую дельту в сутки: \1"),
    (r"^(.+): (\S+) objects reach >= 90% of modeled delta \(R4\)$",
     r"\1: \2 объектов набирают >= 90% модельной дельты (R4)"),
    (r"^(.+): 90% coverage not reached in exported rows - export more rows or quantify remainder$",
     r"\1: в выгруженных строках не набрано 90% - выгрузите больше строк или оцените остаток"),
    (r"^delta_bridge\.csv: no ROOT_CAUSE line with numeric delta_per_day$",
     "delta_bridge.csv: нет строки ROOT_CAUSE с числовым delta_per_day"),
    (r"^bridge (\S+) -> (\S+): register status (\S+)$", r"мост \1 -> \2: статус в реестре \3"),
    (r"^bridge (\S+): status \(blank\)$", r"мост \1: статус не задан"),
    (r"^bridge (\S+): status (\S+)$", r"мост \1: статус \2"),
    (r"^delta_bridge\.csv: TOTAL missing$", "delta_bridge.csv: нет строки TOTAL"),
    (r"^bridge identity: sum of lines (\S+) vs TOTAL (\S+) \(tolerance 1%\)$",
     r"тождество моста: сумма строк \1 vs TOTAL \2 (допуск 1%)"),
    (r"^UNX \(UNEXPLAINED\) line has no numeric delta_per_day$",
     "в строке UNX (UNEXPLAINED) нет числового delta_per_day"),
    (r"^UNEXPLAINED = (\S+) of TOTAL \(R4: <= 10% or accepted in CHECKS\)$",
     r"UNEXPLAINED = \1 от TOTAL (R4: <= 10% или принято в проверках)"),
    (r"^evidence_register\.csv: (\d+) evidence rows$", r"evidence_register.csv: строк доказательств \1"),
    (r"^(\S+) CONFIRMED: evidence (.+?) missing (.+)$", r"\1 CONFIRMED: доказательства \2, отсутствуют \3"),
    (r"^(\S+) CONFIRMED: evidence none$", r"\1 CONFIRMED: доказательств нет"),
    (r"^(\S+) CONFIRMED: evidence (.+)$", r"\1 CONFIRMED: доказательства \2"),
    (r"^findings_report\.md: (\d+) unfilled '____' placeholders$",
     r"findings_report.md: незаполненных плейсхолдеров '____': \1"),
    # ---------------------------------------------------------------- calculators (webapp/runner.py)
    (r"^R6: (\d+) months, max diff (\S+) \(tolerance (\S+)\), (\d+) not PASS$",
     r"R6: месяцев \1, макс. расхождение \2 (допуск \3), не PASS: \4"),
    (r"^Operational Δ = (.+)/day \(scope_record §7\)$", r"Операционная Δ = \1/сутки (scope_record §7)"),
    (r"^UNX = (\S+)/day = (\S+) of TOTAL \(R4 ≤ 10%\)$", r"UNX = \1/сутки = \2 от TOTAL (R4 ≤ 10%)"),
    (r"^Created (.+)$", r"Создано \1"),
    (r"^Reproduced: (\d+) match, (\d+) mismatch, (\d+) manual$",
     r"Воспроизведено: совпало \1, не совпало \2, вручную \3"),
    (r"^(\d+) bridge lines \(BUCKET / DRIVER_CANDIDATE and empty lines omitted\)$",
     r"строк моста: \1 (BUCKET / DRIVER_CANDIDATE и пустые строки пропущены)"),
    (r"^R8 (\S+): Azure (\S*) vs modeled (\S*)$", r"R8 \1: Azure \2 vs модель \3"),
    (r"^persistence (.*)$", r"устойчивость \1"), (r"^×365 (.*)$", r"×365 \1"), (r"/day", "/сутки"),
    # ---------------------------------------------------------------- tool output lines
    (r"^Per day: B (\S+) -> C (\S+) \| delta (\S+)/day \((\S+)\) \| annualized (\S+)",
     r"В сутки: B \1 -> C \2 | дельта \3/сутки (\4) | за год \5"),
    (r"Rows needed for >= 90% of net delta \(R4\): (\S+)", r"Строк для >= 90% чистой дельты (R4): \1"),
    (r"^Monthly series \((\S+)\) - per-day rate = total / calendar days$",
     r"Помесячный ряд (\1) - ставка в сутки = итог / календарные дни"),
    (r"^ONSET: none - no excursion above T lasting >= (\d+) days after the baseline$",
     r"НАЧАЛО: нет - нет выхода выше T длительностью >= \1 дней после базового периода"),
    (r"^ONSET: (\S+)\s+\(post-onset mean (\S+)/day, (\S+)/day, (\S+) vs baseline\)$",
     r"НАЧАЛО: \1 (среднее после начала \2/сутки, \3/сутки, \4 к базе)"),
    (r"^Threshold T = (\S+)/day$", r"Порог T = \1/сутки"),
    (r"^Generated report: (.+)$", r"Отчёт создан: \1"),
    (r"^Baseline has data on (\d+) of (\d+) days - missing days are UNKNOWN, not zero$",
     r"В базовом периоде данные есть за \1 из \2 дней - пропущенные дни UNKNOWN, а не ноль"),
    (r"^Comparison has data on (\d+) of (\d+) days - missing days are UNKNOWN, not zero$",
     r"В периоде сравнения данные есть за \1 из \2 дней - пропущенные дни UNKNOWN, а не ноль"),
    (r"^Read-only Azure Databricks workspace inventory: (.+)$", r"Инвентаризация workspace Azure Databricks (только чтение): \1"),
    # ---------------------------------------------------------------- errors (webapp)
    (r"^invalid audit id$", "недопустимый ID аудита"),
    (r"^audit id must be 2-64 chars.*$",
     "ID аудита: 2-64 символа, только латинские буквы и цифры; начинается с буквы или цифры, далее можно '.', '_', '-'"),
    (r"^(.+) already exists - nothing changed$", r"\1 уже существует - ничего не изменено"),
    (r"^audit not found: (.+)$", r"аудит не найден: \1"),
    (r"^not an audit workspace: (.+)$", r"не папка аудита: \1"),
    (r"^step not found: (.+)$", r"шаг не найден: \1"),
    (r"^check not found: (.+)$", r"проверка не найдена: \1"),
    (r"^invalid path$", "недопустимый путь"),
    (r"^path outside the audit$", "путь вне папки аудита"),
    (r"^file not found$", "файл не найден"),
    (r"^file exists: (.+)$", r"файл уже есть: \1 (отметьте «Перезаписать»)"),
    (r"^file too large \(max 1 GiB\)$", "файл слишком большой (макс. 1 ГиБ)"),
    (r"^invalid file name .*$", "недопустимое имя файла (латинские буквы, цифры, пробел . _ - ( ) +)"),
    (r"^living registers cannot be removed$", "живые реестры удалять нельзя"),
    (r"^CHECKS\.md cannot be removed$", "CHECKS.md удалять нельзя"),
    (r"^only \.md and \.txt files can be edited as text$", "как текст можно редактировать только .md и .txt"),
    (r"^edit checks in the checklist, not as text$", "проверки отмечаются в списке проверок, а не текстом"),
    (r"^reason required for \[-\] and \[!\]$", "для [-] и [!] нужна причина"),
    (r"^gate checks can only be open or done \[x\]$", "контрольная точка может быть только открыта или выполнена [x]"),
    (r"^state must be one of .*$", "недопустимое состояние проверки"),
    (r"^register columns cannot be changed$", "колонки реестра менять нельзя"),
    (r"^unknown register$", "неизвестный реестр"),
    (r"^(\S+): expected YYYY-MM-DD:YYYY-MM-DD$", r"\1: ожидается YYYY-MM-DD:YYYY-MM-DD"),
    (r"^(\S+): expected YYYY-MM-DD$", r"\1: ожидается YYYY-MM-DD"),
    (r"^(\S+): expected YYYY-MM$", r"\1: ожидается YYYY-MM"),
    (r"^(\S+) must be before (\S+) \(end is exclusive\)$", r"\1 должно быть раньше \2 (конец не включается)"),
    (r"^(.+): choose a file$", r"\1: выберите файл"),
    (r"^(.+): file not found \((.+)\)$", r"\1: файл не найден (\2)"),
    (r"^(.+): number expected$", r"\1: ожидается число"),
    (r"^filter must be COLUMN=VALUE: (.+)$", r"фильтр должен быть КОЛОНКА=ЗНАЧЕНИЕ: \1"),
    (r"^choose at least one input file$", "выберите хотя бы один входной файл"),
    (r"^currency is required$", "нужна валюта"),
    (r"^api_url must be an https URL copied from TBM Studio$", "api_url должен быть https-адресом, скопированным из TBM Studio"),
    (r"^give either the environment ID or the customer domain$", "укажите ID окружения или домен клиента"),
    (r"^(.+): required \(or set environment variable (\S+)\)$", r"\1: обязательно (или задайте переменную окружения \2)"),
    (r"^short name required$", "нужно краткое имя"),
    (r"^TOTAL row has no delta_per_day yet \(step 02\)$", "в строке TOTAL ещё нет delta_per_day (шаг 02)"),
    (r"^no service column \(ServiceName / MeterCategory\) in the export$",
     "в выгрузке нет колонки сервиса (ServiceName / MeterCategory)"),
    (r"^B and C must each contain at least one full calendar month for the modeled side$",
     "для модельной стороны B и C должны содержать хотя бы по одному полному календарному месяцу"),
    (r"^Mixed currencies (.+) - rerun with --currency \(rule R11\)$",
     r"смешанные валюты \1 - укажите валюту в поле «Только валюта» (правило R11)"),
    (r"^No rows after filters$", "после фильтров не осталось строк"),
    (r"^Column '(.+)' not found\. Available: (.*)$", r"колонка '\1' не найдена. Доступны: \2"),
    (r"^unknown SQL file$", "неизвестный SQL-файл"),
    (r"^SQL file not part of this action$", "SQL-файл не относится к этому действию"),
    (r"^statement index out of range$", "номер запроса вне диапазона"),
    (r"^missing parameters: (.+)$", r"не заданы параметры: \1"),
    (r"^only read-only SELECT statements are executed \(rule R12\)$",
     "выполняются только SELECT-запросы на чтение (правило R12)"),
    (r"^Databricks connection not configured.*$", "подключение к Databricks не настроено (Настройки)"),
    (r"^no Databricks token: .*$", "нет токена Databricks: введите personal access token в Настройках или задайте DATABRICKS_TOKEN"),
    (r"^Azure CLI \(az\) not found.*$", "Azure CLI (az) не найден; установите его и выполните 'az login' или используйте токен"),
    (r"^az account get-access-token failed - run 'az login' first: (.*)$",
     r"az account get-access-token не сработал - сначала выполните 'az login': \1"),
    (r"^host must look like (.+)$", r"хост должен выглядеть как \1"),
    (r"^warehouse ID: .*$", "ID warehouse: только латинские буквы и цифры (SQL warehouse → Connection details)"),
    (r"^timeout must be 30\.\.3600 seconds$", "тайм-аут должен быть 30..3600 секунд"),
    (r"^query exceeded (\d+) s and was cancelled$", r"запрос превысил \1 с и был отменён"),
    (r"^query (\S+): (.*)$", r"запрос \1: \2"),
    (r"^cannot reach Databricks: (.*)$", r"нет связи с Databricks: \1"),
    (r"^result truncated by Databricks .*$",
     "результат обрезан Databricks (> 25 МиБ) - сузьте период или выгрузите из SQL-редактора"),
    (r"^needs live credentials - reproduce manually$", "нужны учётные данные - воспроизведите вручную"),
    (r"^action cannot be run$", "это действие нельзя запустить"),
    (r"^action has no form$", "у действия нет формы"),
    (r"^document not found$", "документ не найден"),
    (r"^not found: (.*)$", r"не найдено: \1"),
    (r"^Databricks API HTTP (\S+): (.*)$", r"API Databricks HTTP \1: \2"),
    (r"^auth must be pat or azure_cli$", "аутентификация: pat или azure_cli"),
    (r"^exit (\d+)$", r"код завершения \1"),
    (r"^unknown calculator (.+)$", r"неизвестный расчёт \1"),
    (r"^unknown tool (.+)$", r"неизвестный инструмент \1"),
    (r"^unknown (\w+): (.+)$", r"неизвестно (\1): \2"),
]
_COMPILED = [(re.compile(p), r) for p, r in RU]
_INLINE = {r"/day"}


def tr(message: str, lang: str | None = None) -> str:
    """Translate one message (or a multi-line text line by line) into the request language."""
    lang = lang or LANG.get()
    if lang != "ru" or not message:
        return message
    out = []
    for line in str(message).split("\n"):
        prefix = ""
        m = re.match(r"^(ERROR: |WARNING: )(.*)$", line)
        if m:
            prefix, line = {"ERROR: ": "ОШИБКА: ", "WARNING: ": "ВНИМАНИЕ: "}[m.group(1)], m.group(2)
        done = False
        for rx, rep in _COMPILED:
            if rx.pattern in _INLINE:
                continue
            if rx.search(line) and rx.pattern.startswith("^"):
                line = rx.sub(rep, line)
                done = True
                break
        if not done:  # tool summaries are joined with " · " - translate each part
            parts = line.split(" · ")
            if len(parts) > 1:
                line = " · ".join(tr(p, "ru") for p in parts)
            else:
                for rx, rep in _COMPILED:
                    if not rx.pattern.startswith("^") and rx.search(line):
                        line = rx.sub(rep, line)
        for rx, rep in _COMPILED:
            if rx.pattern in _INLINE:
                line = rx.sub(rep, line)
        out.append(prefix + line)
    return "\n".join(out)


class LangMiddleware:
    """Pure ASGI middleware: reads X-Lang (en/ru) into a context variable for the request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            raw = dict(scope.get("headers") or []).get(b"x-lang", b"en").decode("latin-1").lower()
            token = LANG.set("ru" if raw.startswith("ru") else "en")
            try:
                await self.app(scope, receive, send)
            finally:
                LANG.reset(token)
            return
        await self.app(scope, receive, send)
