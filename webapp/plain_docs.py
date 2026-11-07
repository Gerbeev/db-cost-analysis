"""Keeps the "Overview" intro block of the documents in sync.

Every step README gets its intro from `plain.STEP` (the same text the step page shows); reference pages and driver
playbooks have their own short intros defined below. Blocks are fenced by `<!-- plain -->` markers, so
`sync()` can be re-run at any time. A test calls `check()` so the files can never drift from this source.
"""
from __future__ import annotations

import re

from . import metrics, plain, steps
from .core import ROOT

LABELS = {
    "en": {"plain": "Overview", "result": "Result", "tip": "Note"},
    "ru": {"plain": "Обзор", "result": "Результат", "tip": "Важно"},
}
START, END = "<!-- plain -->", "<!-- /plain -->"


def T(en: str, ru: str) -> dict:
    return {"en": en, "ru": ru}


DOC: dict[str, dict] = {
    "playbook/README.md": T(
        "The playbook is ten steps done in order. Each step answers one question and ends with a **gate** - a "
        "check you must tick before moving on. You never need to type a command: every action is a button on the "
        "step page of the app, and every result is saved in your audit folder.\n\n"
        "Sequence: *agree on the question (00) → trust the data (01) → prove the growth (02) → remove "
        "accounting effects (03) → find where the money went in Azure (04) and in Databricks (05) → find the "
        "cause (06) → check the numbers add up (07) → have someone repeat them (08) → write it up (09).*",
        "Плейбук - это десять шагов по порядку. Каждый шаг отвечает на один вопрос и заканчивается "
        "**контрольной точкой** - проверкой, которую нужно отметить перед следующим шагом. Вводить команды не "
        "нужно: каждое действие - кнопка на странице шага в приложении, а каждый результат сохраняется в папке "
        "вашего аудита.\n\n"
        "Последовательность: *договоритесь о вопросе (00) → поверьте данным (01) → докажите рост (02) → уберите учётные "
        "эффекты (03) → найдите, куда ушли деньги в Azure (04) и в Databricks (05) → найдите причину (06) → "
        "проверьте, что числа сходятся (07) → дайте их повторить другому (08) → оформите результат (09).*"),
    "reference/00_fundamentals.md": T(
        "Prerequisite reading for anyone new to Azure Databricks cost (about 15 minutes). Key points:\n\n"
        "1. Databricks is billed **within the Azure invoice**; there is no separate Databricks invoice.\n"
        "2. Compute is charged in **DBU**; classic compute additionally incurs the cost of the underlying virtual "
        "machines.\n"
        "3. The DBU price depends on the compute type: identical work costs very different amounts on different "
        "types.\n"
        "4. Storage, network and monitoring are billed separately from compute.\n"
        "5. A bill can rise because of **accounting** (a discount ended, a price changed) without more consumption; "
        "the audit separates the two.\n\n"
        "Terms are defined in the [glossary](14_glossary.md).",
        "Обязательное чтение для тех, кто впервые работает с затратами Azure Databricks (около 15 минут). "
        "Ключевые положения:\n\n"
        "1. Databricks тарифицируется **в составе счёта Azure**; отдельного счёта Databricks нет.\n"
        "2. Вычисления тарифицируются в **DBU**; классические вычисления дополнительно включают стоимость "
        "виртуальных машин.\n"
        "3. Цена DBU зависит от типа вычислений: одна и та же работа на разных типах стоит по-разному.\n"
        "4. Хранилище, сеть и мониторинг тарифицируются отдельно от вычислений.\n"
        "5. Счёт может расти из-за **учёта** (закончилась скидка, изменилась цена) без увеличения потребления; "
        "аудит разделяет одно и другое.\n\n"
        "Термины определены в [словаре](14_glossary.md)."),
    "reference/01_cost_model.md": T(
        "A deeper look at the same picture as the fundamentals: what exactly gets billed, under which Azure "
        "meters it shows up, and how the different views of cost (Actual, Amortized, the Databricks model, IBM) "
        "relate. Read it when you need to know *which number comes from where* before you compare two numbers.",
        "Более подробный взгляд на ту же картину, что и в основах: что именно выставляется, под какими "
        "счётчиками Azure это появляется и как соотносятся разные представления затрат (Actual, Amortized, "
        "модель Databricks, IBM). Читайте, когда нужно понять, *откуда какое число*, прежде чем сравнивать два "
        "числа."),
    "reference/02_access_and_data_collection.md": T(
        "A checklist of what you must be allowed to see and how to download it. Send the access list to the "
        "people who manage Azure and Databricks **early** - getting access is usually the slowest part of an "
        "audit. Everything here is read-only.",
        "Список того, что вам должны разрешить смотреть, и как это скачать. Отправьте список прав тем, кто "
        "управляет Azure и Databricks, **заранее** - получение доступа обычно самая медленная часть аудита. Всё "
        "здесь только для чтения."),
    "reference/03_analysis_method.md": T(
        "The formulas behind the app, written once so anyone can check them: cost per day, growth, the day it "
        "started, volume versus price, and how the delta bridge adds up. You do not need it to use the app, but "
        "you need it to explain a number to a skeptical colleague.",
        "Формулы, на которых работает приложение, записанные в одном месте, чтобы любой мог их проверить: "
        "затраты в сутки, рост, день начала, объём против цены и как складывается мост дельты. Для работы в "
        "приложении это не обязательно, но нужно, чтобы объяснить число скептически настроенному коллеге."),
    "reference/04_pitfalls_and_stop_rules.md": T(
        "Conditions that produce incorrect results without any error message: an export taken twice, two currencies "
        "mixed, a missing month and so on. Each trap says how to notice it and what to do. If the app or the "
        "checks mention a **STOP** number, this is the page that explains it.",
        "Условия, при которых результаты оказываются неверными без сообщения об ошибке: выгрузка, сделанная "
        "дважды, смешанные валюты, пропущенный месяц и т. д. Для каждой указано, как её заметить и что делать. "
        "Если приложение или проверки упоминают номер **STOP**, это страница с объяснением."),
    "reference/05_audit_rules.md": T(
        "The twelve rules of the method. Most important rules:\n\n"
        "- **R1** - only the real Azure bill (Actual) counts as money; other views never get added to it.\n"
        "- **R2** - compare per-day rates over a calm period (B) and a high period (C).\n"
        "- **R4** - explain at least 90%; show the rest openly.\n"
        "- **R6** - the export must match Cost Analysis within 0.5%.\n"
        "- **R9** - a cause is *confirmed* only with four proofs.\n"
        "- **R12** - the audit is read-only.\n\n"
        "The table below is the exact wording; the app refers to the rules by their number.",
        "Двенадцать правил метода. Наиболее важные правила:\n\n"
        "- **R1** - деньгами считается только реальный счёт Azure (Actual); другие представления к нему не "
        "прибавляются.\n"
        "- **R2** - сравниваем суточные ставки спокойного периода (B) и повышенного (C).\n"
        "- **R4** - объясняем не меньше 90%; остальное показываем открыто.\n"
        "- **R6** - выгрузка должна совпадать с Cost Analysis в пределах 0,5%.\n"
        "- **R9** - причина *подтверждена* только при четырёх доказательствах.\n"
        "- **R12** - аудит только читает.\n\n"
        "Таблица ниже - точные формулировки; приложение ссылается на правила по номеру."),
    "reference/06_ibm_apptio_lens.md": T(
        "Only for companies that also use IBM Cloudability or ApptioOne. These tools show the same Azure charges "
        "in their own way. This page explains how to compare them with the audit - and why their totals are never "
        "added to Azure's. Skip it if you do not have IBM tools.",
        "Только для компаний, которые используют ещё и IBM Cloudability или ApptioOne. Эти инструменты "
        "показывают те же начисления Azure по-своему. Страница объясняет, как сравнить их с аудитом и почему "
        "их итоги никогда не прибавляются к итогам Azure. Если IBM у вас нет, пропустите."),
    "reference/07_ibm_api_setup.md": T(
        "Optional. How to give the app access to IBM Cloudability or ApptioOne (keys and URLs) so that steps 8.4-"
        "8.8 can download data for you. Skip it if you do not use IBM tools.",
        "Необязательно. Как дать приложению доступ к IBM Cloudability или ApptioOne (ключи и URL), чтобы "
        "действия 8.4-8.8 могли скачать данные за вас. Если IBM не используете, пропустите."),
    "reference/08_remediation_and_controls.md": T(
        "What to do **after** the audit: how to turn each finding into a fix with an owner, how to prove a saving "
        "(measure it in the real bill, at least 14 days after the change) and which simple alerts keep the same "
        "growth from coming back unnoticed.",
        "Что делать **после** аудита: как превратить каждый вывод в исправление с владельцем, как доказать "
        "экономию (замерить в реальном счёте не меньше 14 дней после изменения) и какие простые оповещения не "
        "дадут тому же росту вернуться незамеченным."),
    "reference/09_sources_and_glossary.md": T(
        "Links to the official Microsoft and Databricks documentation that the method relies on. Terms are "
        "explained in the separate [glossary](14_glossary.md).",
        "Ссылки на официальную документацию Microsoft и Databricks, на которую опирается метод. Термины "
        "объяснены в отдельном [словаре](14_glossary.md)."),
    "reference/10_legacy_mapping.md": T(
        "Only useful if you used the older version of this toolkit: it shows where each old item went. New users "
        "can skip it.",
        "Нужно, только если вы работали со старой версией набора: показывает, куда переехал каждый старый "
        "элемент. Новым пользователям можно пропустить."),
    "reference/11_sql_conventions.md": T(
        "How the SQL files are written and how to read their output. Every query only **reads** data. Running one "
        "uses a little SQL warehouse compute, so tell the Databricks owner before you run them in bulk.",
        "Как написаны SQL-файлы и как читать их результат. Каждый запрос только **читает** данные. Запуск "
        "расходует немного вычислений SQL warehouse, поэтому предупредите владельца Databricks, прежде чем "
        "запускать их пачкой."),
}
_PB = "playbook/06_root_cause/playbooks/"
DOC.update({
    _PB + "01_jobs.md": T(
        "Use when a **scheduled job** costs more. The usual reasons: it runs more often, each run takes longer, "
        "it got a bigger cluster, or it processes more data. The checks tell them apart.",
        "Используйте, когда дороже стала **плановая задача**. Обычные причины: она запускается чаще, каждый "
        "запуск длится дольше, ей дали кластер побольше или она обрабатывает больше данных. Проверки их "
        "различают."),
    _PB + "02_pipelines.md": T(
        "Use when a **data pipeline** (Lakeflow / DLT) costs more: more updates, a change of edition, a bigger "
        "cluster or a switch to continuous mode.",
        "Используйте, когда дороже стал **конвейер данных** (Lakeflow / DLT): больше обновлений, смена "
        "редакции, кластер побольше или переход на непрерывный режим."),
    _PB + "03_classic_compute.md": T(
        "Use when clusters in your own Azure subscription cost more - especially **all-purpose** clusters used "
        "by people. Typical reasons: clusters left running, larger nodes, more nodes, no auto-stop, jobs "
        "running on interactive clusters.",
        "Используйте, когда стали дороже кластеры в вашей подписке Azure, особенно **all-purpose** кластеры, "
        "которыми пользуются люди. Типичные причины: кластеры остаются включёнными, более крупные узлы, больше "
        "узлов, нет автоостановки, задачи идут на интерактивных кластерах."),
    _PB + "04_instance_pools.md": T(
        "Use when **virtual machines** cost more but DBU did not. Idle machines kept warm in an instance pool "
        "cost VM money and show no Databricks usage.",
        "Используйте, когда выросла стоимость **виртуальных машин**, а DBU нет. Простаивающие машины, "
        "удерживаемые в пуле инстансов, стоят денег за VM и не видны в потреблении Databricks."),
    _PB + "05_sql_warehouses.md": T(
        "Use when **SQL** costs more: a larger warehouse size, more clusters, a warehouse that no longer stops "
        "(auto-stop changed), or more or heavier queries from a dashboard or tool.",
        "Используйте, когда дороже стал **SQL**: размер warehouse больше, больше кластеров, warehouse "
        "перестал останавливаться (изменили автоостановку) или больше или тяжелее запросов от дашборда или "
        "инструмента."),
    _PB + "06_serverless.md": T(
        "Use when **serverless** products cost more. There are no virtual machines to look at - the price "
        "is all DBU - so the question is *what is being run, how often and with which feature switched on*.",
        "Используйте, когда дороже стали **serverless**-продукты. Виртуальных машин здесь нет - вся цена в DBU, - "
        "поэтому вопрос в том, *что запускается, как часто и с какой включённой функцией*."),
    _PB + "07_ai_and_apps.md": T(
        "Use when model serving, Vector Search, AI functions, Databricks Apps or Lakebase cost more. These bill in "
        "their own units; look for a new endpoint, more traffic or a larger index.",
        "Используйте, когда дороже стали model serving, Vector Search, AI-функции, Databricks Apps или "
        "Lakebase. Они тарифицируются в своих единицах; ищите новый endpoint, больше трафика или более крупный "
        "индекс."),
    _PB + "08_platform_features.md": T(
        "Use when background platform features cost more: predictive optimization, data-quality monitoring, "
        "networking features. They often appear **after someone enables a setting** for the whole account.",
        "Используйте, когда дороже стали фоновые функции платформы: predictive optimization, мониторинг "
        "качества данных, сетевые функции. Они часто появляются **после того, как кто-то включил настройку** "
        "для всего аккаунта."),
    _PB + "09_storage.md": T(
        "Use when the **STORAGE** category grew: more data stored, longer retention, many small files, or more "
        "reads and writes.",
        "Используйте, когда выросла категория **STORAGE**: хранится больше данных, дольше срок хранения, много "
        "мелких файлов или больше чтений и записей."),
    _PB + "10_network.md": T(
        "Use when the **NETWORK** category grew: data moving between regions, a new private endpoint, NAT or "
        "firewall traffic.",
        "Используйте, когда выросла категория **NETWORK**: данные ходят между регионами, новый private "
        "endpoint, трафик через NAT или firewall."),
    _PB + "11_monitoring.md": T(
        "Use when the **MONITORING** category grew - usually Log Analytics after someone turned on more "
        "detailed diagnostic logs.",
        "Используйте, когда выросла категория **MONITORING** - обычно Log Analytics после того, как кто-то "
        "включил более подробные диагностические логи."),
    _PB + "12_rate_and_accounting.md": T(
        "Use for the effects from step 03: a price change, an ended commitment or credit, a currency move. These "
        "are not about workload, so the proof is in billing data and contracts, not in Databricks.",
        "Используйте для эффектов шага 03: изменение цены, закончившееся обязательство или кредит, "
        "изменение курса. Это не про нагрузку, поэтому доказательства лежат в данных биллинга и договорах, а не "
        "в Databricks."),
})


def _quote(text: str) -> str:
    return "\n".join(("> " + ln) if ln.strip() else ">" for ln in text.split("\n"))


def block(rel: str, lang: str) -> str | None:
    lab = LABELS[lang]
    m = re.match(r"playbook/(\d\d)_[^/]+/README\.md$", rel)
    if m:
        s = plain.STEP[m.group(1)]
        parts = [f"**{lab['plain']}.** {s['plain'][lang]}", f"**{lab['result']}:** {s['result'][lang]}",
                 f"**{lab['tip']}:** {s['tip'][lang]}"]
    elif rel in DOC:
        parts = [f"**{lab['plain']}.** {DOC[rel][lang]}"]
    else:
        return None
    return f"{START}\n{_quote(chr(10).join(p + chr(10) if i < len(parts) - 1 else p for i, p in enumerate(parts)))}\n{END}"


def targets() -> list[str]:
    out = list(DOC)
    out += [f"playbook/{s['folder']}/README.md" for s in steps.STEPS]
    return out


def _insert(text: str, blk: str) -> str:
    text = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n*", "", text, flags=re.S)
    lines = text.split("\n")
    i = next(k for k, ln in enumerate(lines) if ln.startswith("# "))
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j < len(lines) and lines[j].startswith("[") and "](" in lines[j]:  # step navigation line
        i = j
    rest = lines[i + 1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    return "\n".join(lines[: i + 1] + ["", blk, ""] + rest)


GENERATED = "reference/15_data_sources"


def sync_generated(write: bool = True) -> list[str]:
    """reference/15_data_sources[.ru].md is rendered from webapp/metrics.py (why / how for every metric)."""
    stale = []
    for lang in ("en", "ru"):
        p = ROOT / (GENERATED + (".md" if lang == "en" else ".ru.md"))
        new = metrics.reference_doc(lang, steps.STEPS)
        old = p.read_text(encoding="utf-8") if p.is_file() else ""
        if old != new:
            stale.append(p.relative_to(ROOT).as_posix())
            if write:
                p.write_text(new, encoding="utf-8", newline="\n")
    return stale


def sync(write: bool = True) -> list[str]:
    """Return the list of files whose block was missing or stale (and rewrite them when write=True)."""
    stale = sync_generated(write)
    for rel in targets():
        for lang in ("en", "ru"):
            p = ROOT / (rel if lang == "en" else rel[:-3] + ".ru.md")
            if not p.is_file():
                stale.append(f"{p.relative_to(ROOT)} (missing)")
                continue
            old = p.read_text(encoding="utf-8")
            new = _insert(old, block(rel, lang))
            if old != new:
                stale.append(p.relative_to(ROOT).as_posix())
                if write:
                    p.write_text(new, encoding="utf-8", newline="\n")
    return stale


if __name__ == "__main__":
    changed = sync(True)
    print("\n".join(changed) or "all documents are in sync")
