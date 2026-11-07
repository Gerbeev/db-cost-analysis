"""Tool and calculator execution for the web UI.

Tools in tools/ are run as subprocesses with arguments built from validated form values;
calculators are small in-process computations that write their result into the audit.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from . import core
from .core import ROOT, UserError

sys.path.insert(0, str(ROOT / "tools"))
import period_delta  # noqa: E402

TIMEOUT = 1800
SECRET_TYPES = {"secret"}


def T(en: str, ru: str) -> dict:
    return {"en": en, "ru": ru}


def F(name, type_, en, ru, required=False, default="", **kw) -> dict:
    return {"name": name, "type": type_, "label": T(en, ru), "required": required, "default": default, **kw}


CSV_EXPORT = F("csv", "file", "Input CSV (Azure Actual export)", "Входной CSV (выгрузка Azure Actual)", True, "export",
               ext=[".csv"])
CURRENCY = F("currency", "text", "Keep only currency (if file mixes currencies)",
             "Только валюта (если в файле несколько валют)", False, "")
FILTERS = F("filter", "lines", "Filters COLUMN=VALUE (one per line, exact match)",
            "Фильтры КОЛОНКА=ЗНАЧЕНИЕ (по одному в строке, точное совпадение)", False, "")

# ---------------------------------------------------------------- tool catalogue
TOOLS: dict[str, dict] = {
    "monthly": {
        "title": T("Monthly series with per-day rates", "Помесячный ряд с суточными ставками"),
        "script": "period_delta.py", "source": "Azure Actual",
        "fields": [CSV_EXPORT, CURRENCY, FILTERS],
    },
    "delta": {
        "title": T("Δ/day between B and C, ranked", "Δ/сутки между B и C с ранжированием"),
        "script": "period_delta.py", "source": "Azure Actual",
        "fields": [CSV_EXPORT,
                   F("base", "period", "Baseline B", "Базовый период B", True, "setting:b"),
                   F("cmp", "period", "Comparison C", "Период сравнения C", True, "setting:c"),
                   F("group", "columns", "Group by columns", "Группировать по колонкам", False, "", of="csv"),
                   FILTERS, CURRENCY,
                   F("top", "int", "Rows printed in the log", "Строк в журнале", False, "20")],
    },
    "onset": {
        "title": T("Onset detection (rule R5)", "Определение начала роста (правило R5)"),
        "script": "onset_detect.py", "source": "Azure Actual",
        "fields": [CSV_EXPORT,
                   F("baseline", "period", "Baseline (≥ 28 stable days)", "Базовый период (≥ 28 стабильных дней)",
                     True, "setting:b"),
                   FILTERS, CURRENCY,
                   F("window", "int", "Trailing mean window, days", "Окно скользящего среднего, дней", False, "7"),
                   F("sigma", "float", "k in μ + k·σ", "k в μ + k·σ", False, "2"),
                   F("min_rel", "float", "Minimum relative uplift", "Минимальный относительный прирост", False, "0.10"),
                   F("min_run", "int", "Consecutive days for a step", "Дней подряд для ступеньки", False, "14")],
    },
    "analyze": {
        "title": T("Monthly analyzer: Azure Actual + SQL 2.2", "Помесячный анализ: Azure Actual + SQL 2.2"),
        "script": "analyze_costs.py", "source": "Azure Actual + Databricks list price",
        "fields": [F("azure", "file", "Azure Actual export", "Выгрузка Azure Actual", False, "export", ext=[".csv"]),
                   F("databricks", "file", "SQL 2.2 result", "Результат SQL 2.2", False,
                     "latest:02_confirm_and_size/results/2.2_monthly_cost_by_sku*.csv", ext=[".csv"]),
                   F("start", "month", "First full month", "Первый полный месяц", True, "setting:window_start_month"),
                   F("end", "month", "Last full month", "Последний полный месяц", True, "setting:window_last_month")],
        "out_dir": True,
    },
    "inventory": {
        "title": T("Workspace ↔ managed RG inventory (Azure CLI, read-only)",
                   "Инвентаризация workspace ↔ managed RG (Azure CLI, только чтение)"),
        "script": None, "source": "Azure Resource Manager",
        "fields": [F("subscription", "text", "Subscription ID", "ID подписки", True, "")],
    },
    "cloudability_probe": {
        "title": T("IBM Cloudability: verify access", "IBM Cloudability: проверка доступа"),
        "script": "apptio_api.py", "source": "IBM Cloudability",
        "fields": [F("api_key", "secret", "Cloudability API key (not stored)", "API-ключ Cloudability (не сохраняется)",
                     False, "", env="CLOUDABILITY_API_KEY"),
                   F("region", "select", "Region", "Регион", True, "eu",
                     options=["eu", "us", "apac", "ca", "me", "in", "jp", "sg", "usgov"])],
    },
    "cloudability_export": {
        "title": T("IBM Cloudability: export costs", "IBM Cloudability: выгрузка затрат"),
        "script": "apptio_api.py", "source": "IBM Cloudability",
        "fields": [F("api_key", "secret", "Cloudability API key (not stored)", "API-ключ Cloudability (не сохраняется)",
                     False, "", env="CLOUDABILITY_API_KEY"),
                   F("region", "select", "Region", "Регион", True, "eu",
                     options=["eu", "us", "apac", "ca", "me", "in", "jp", "sg", "usgov"]),
                   F("currency", "text", "Reporting currency shown in Cloudability UI",
                     "Валюта отчёта из интерфейса Cloudability", True, "setting:currency"),
                   F("start", "month", "First month", "Первый месяц", True, "setting:window_start_month"),
                   F("end", "month", "Last month", "Последний месяц", True, "setting:window_last_month"),
                   F("dimensions", "text", "Dimensions", "Измерения", True, "vendor,enhanced_service_name"),
                   F("metric", "text", "Metric", "Метрика", True, "unblended_cost"),
                   F("filter", "lines", "Filters (one per line, e.g. vendor==Azure)",
                     "Фильтры (по одному в строке, напр. vendor==Azure)", False, "vendor==Azure"),
                   F("view_id", "text", "View ID (optional)", "ID представления (необязательно)", False, "")],
    },
    "apptioone_download": {
        "title": T("IBM ApptioOne: download TBM Studio report", "IBM ApptioOne: загрузка отчёта TBM Studio"),
        "script": "apptio_api.py", "source": "IBM ApptioOne",
        "fields": [F("key_access", "secret", "Apptio key access (not stored)", "Apptio key access (не сохраняется)",
                     False, "", env="APPTIO_KEY_ACCESS"),
                   F("key_secret", "secret", "Apptio key secret (not stored)", "Apptio key secret (не сохраняется)",
                     False, "", env="APPTIO_KEY_SECRET"),
                   F("api_url", "text", "Report API URL (Show API URL)", "API URL отчёта (Show API URL)", True, ""),
                   F("customer", "text", "Frontdoor customer domain", "Домен клиента Frontdoor", False, ""),
                   F("environment_id", "text", "Environment ID (if known)", "ID окружения (если известен)", False, ""),
                   F("frontdoor", "text", "Frontdoor host", "Хост Frontdoor", True, "frontdoor-eu.apptio.com"),
                   F("ext", "select", "File type", "Тип файла", True, ".tsv", options=[".tsv", ".csv", ".json", ".xlsx"])],
    },
    "apptio_normalize": {
        "title": T("IBM ApptioOne: normalize report", "IBM ApptioOne: нормализация отчёта"),
        "script": "normalize_apptioone.py", "source": "IBM ApptioOne",
        "fields": [F("input", "file", "TBM Studio export", "Выгрузка TBM Studio", True,
                     "latest:08_validation/exports/apptioone_report*", ext=[".csv", ".tsv"]),
                   F("date_column", "column", "Date / month column", "Колонка даты / месяца", True, "", of="input"),
                   F("cost_column", "column", "Cost column", "Колонка затрат", True, "", of="input"),
                   F("dimension", "columns", "Dimension columns", "Колонки измерений", True, "", of="input"),
                   F("currency", "text", "Currency", "Валюта", False, "setting:currency"),
                   F("metric_name", "text", "Cost metric name (from TBM UI)", "Имя метрики затрат (из TBM UI)", True, ""),
                   F("report_label", "text", "Report label", "Метка отчёта", True, ""),
                   F("start", "month", "First month", "Первый месяц", True, "setting:window_start_month"),
                   F("end", "month", "Last month", "Последний месяц", True, "setting:window_last_month")],
    },
    "apptio_analyze": {
        "title": T("IBM Apptio: analyze export", "IBM Apptio: анализ выгрузки"),
        "script": "analyze_apptio.py", "source": "IBM Cloudability / ApptioOne",
        "fields": [F("input", "file", "Cloudability export or normalized ApptioOne CSV",
                     "Выгрузка Cloudability или нормализованный CSV ApptioOne", True,
                     "latest:08_validation/exports/*cloudability*.csv", ext=[".csv"]),
                   F("manifest", "file", "Manifest (optional)", "Манифест (необязательно)", False,
                     "latest:08_validation/exports/*.manifest.json", ext=[".json"]),
                   F("start", "month", "First month", "Первый месяц", True, "setting:window_start_month"),
                   F("end", "month", "Last month", "Последний месяц", True, "setting:window_last_month")],
        "out_dir": True,
    },
}

# ---------------------------------------------------------------- calculators
CALCS: dict[str, dict] = {
    "r6": {
        "title": T("R6 reconciliation: export vs Cost Analysis", "R6 сверка: выгрузка vs Cost Analysis"),
        "fields": [F("export_monthly", "file", "Export monthly totals (action 1.4)", "Помесячные итоги выгрузки (действие 1.4)",
                     True, "latest:01_data_quality/results/export_monthly*.csv", ext=[".csv"]),
                   F("cost_analysis", "file", "Cost Analysis monthly download", "Выгрузка Cost Analysis помесячно",
                     True, "latest:01_data_quality/exports/cost_analysis_monthly*.csv", ext=[".csv"]),
                   F("date_col", "column", "Cost Analysis date column (auto)", "Колонка даты Cost Analysis (авто)",
                     False, "", of="cost_analysis"),
                   F("cost_col", "column", "Cost Analysis cost column (auto)", "Колонка затрат Cost Analysis (авто)",
                     False, "", of="cost_analysis"),
                   F("tolerance", "float", "Tolerance, %", "Допуск, %", False, "0.5")],
    },
    "size": {
        "title": T("Size the increase and fill the TOTAL bridge row", "Размер роста и строка TOTAL моста"),
        "fields": [CSV_EXPORT,
                   F("base", "period", "Baseline B", "Базовый период B", True, "setting:b"),
                   F("cmp", "period", "Comparison C", "Период сравнения C", True, "setting:c"),
                   F("persist", "period", "Persistence P (optional)", "Период устойчивости P (необязательно)",
                     False, "setting:p"),
                   CURRENCY,
                   F("write_scope", "bool", "Write §6 of scope_record.md and TOTAL row of delta_bridge.csv",
                     "Записать §6 scope_record.md и строку TOTAL delta_bridge.csv", False, "true")],
    },
    "r8": {
        "title": T("R8 direction check", "R8 проверка направления"),
        "fields": [CSV_EXPORT,
                   F("service_value", "text", "Azure service name", "Имя сервиса Azure", True, "Azure Databricks"),
                   F("databricks", "file", "SQL 2.2 result", "Результат SQL 2.2", True,
                     "latest:02_confirm_and_size/results/2.2_monthly_cost_by_sku*.csv", ext=[".csv"]),
                   F("base", "period", "Baseline B (full months)", "Базовый период B (полные месяцы)", True, "setting:b"),
                   F("cmp", "period", "Comparison C (full months)", "Период сравнения C (полные месяцы)", True, "setting:c")],
    },
    "decompose": {
        "title": T("Azure decomposition: five groupings in one run", "Декомпозиция Azure: пять группировок за один запуск"),
        "fields": [CSV_EXPORT,
                   F("base", "period", "Baseline B", "Базовый период B", True, "setting:b"),
                   F("cmp", "period", "Comparison C", "Период сравнения C", True, "setting:c"),
                   FILTERS, CURRENCY,
                   F("top", "int", "Resources kept in the resource grouping", "Ресурсов в группировке по ресурсам",
                     False, "50")],
    },
    "operational": {
        "title": T("Operational Δ = TOTAL - Σ ACCOUNTING", "Операционная Δ = TOTAL - Σ ACCOUNTING"),
        "fields": [],
    },
    "unx": {
        "title": T("Close the bridge: UNX residual and shares", "Закрыть мост: остаток UNX и доли"),
        "fields": [],
    },
    "driver_card": {
        "title": T("New driver card", "Новая карточка драйвера"),
        "fields": [F("name", "text", "Short driver name", "Краткое имя драйвера", True, "")],
    },
    "bridge_md": {
        "title": T("Bridge as a markdown table", "Мост в виде таблицы markdown"),
        "fields": [],
    },
    "reproduce": {
        "title": T("Reproduce evidence (re-run tools and SQL)", "Воспроизвести доказательства (перезапуск инструментов и SQL)"),
        "fields": [],
    },
}


# ---------------------------------------------------------------- defaults
def resolve_default(audit_id: str, spec: str) -> str:
    s = core.settings(audit_id)
    if spec == "export":
        return core.primary_export(audit_id)
    if spec.startswith("latest:"):
        return core.latest_file(audit_id, spec[7:])
    if spec.startswith("setting:"):
        key = spec[8:]
        if key in ("b", "c", "p"):
            return core.period(s, key)
        if key == "window_start_month":
            return s["window_start"][:7]
        if key == "window_last_month":
            if not s["window_end"]:
                return ""
            d = date.fromisoformat(s["window_end"])
            return f"{d.year - (d.month == 1)}-{(d.month - 2) % 12 + 1:02d}"
        return s.get(key, "")
    return spec


def form(audit_id: str, kind: str, name: str, preset: dict | None = None) -> list[dict]:
    spec = (TOOLS if kind == "tool" else CALCS).get(name)
    if spec is None:
        raise UserError(f"unknown {kind}: {name}")
    preset = preset or {}
    out = []
    for f in spec["fields"]:
        f = dict(f)
        if f["name"] in preset:
            f["value"], f["fixed"] = preset[f["name"]], True
        else:
            f["value"], f["fixed"] = resolve_default(audit_id, f["default"]), False
        out.append(f)
    return out


# ---------------------------------------------------------------- validation helpers
def v_file(audit: Path, value: str, label: str, required: bool = True) -> Path | None:
    if not value:
        if required:
            raise UserError(f"{label}: choose a file")
        return None
    p = core.inside(audit, value)
    if not p.is_file():
        raise UserError(f"{label}: file not found ({value})")
    return p


def v_period(value: str, label: str) -> str:
    try:
        s, e = period_delta.parse_period(value)
    except Exception:
        raise UserError(f"{label}: expected YYYY-MM-DD:YYYY-MM-DD") from None
    return f"{s.isoformat()}:{e.isoformat()}"


def v_month(value: str, label: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise UserError(f"{label}: expected YYYY-MM") from None
    return value


def v_num(value: str, label: str, cast=float) -> str:
    try:
        return str(cast(value))
    except (TypeError, ValueError):
        raise UserError(f"{label}: number expected") from None


def lines(value) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in str(value or "").splitlines() if x.strip()]


def columns(value) -> str:
    return ",".join(lines(value if isinstance(value, list) else str(value or "").replace(",", "\n")))


# ---------------------------------------------------------------- tool argv
def build(audit_id: str, tool: str, v: dict, out: Path) -> tuple[list[str], dict]:
    audit = core.audit_dir(audit_id)
    env: dict[str, str] = {}
    a: list[str] = []
    if tool in ("monthly", "delta", "onset"):
        a = ["--csv", str(v_file(audit, v.get("csv"), "csv"))]
        for f in lines(v.get("filter")):
            if "=" not in f:
                raise UserError(f"filter must be COLUMN=VALUE: {f}")
            a += ["--filter", f]
        if v.get("currency"):
            a += ["--currency", str(v["currency"]).strip().upper()]
        if tool == "monthly":
            a += ["--monthly"]
        elif tool == "delta":
            a += ["--base", v_period(v.get("base", ""), "B"), "--cmp", v_period(v.get("cmp", ""), "C"),
                  "--top", v_num(v.get("top") or 20, "top", int)]
            if columns(v.get("group")):
                a += ["--group", columns(v.get("group"))]
        else:
            a += ["--baseline", v_period(v.get("baseline", ""), "baseline"),
                  "--window", v_num(v.get("window") or 7, "window", int),
                  "--sigma", v_num(v.get("sigma") or 2, "sigma"),
                  "--min-rel", v_num(v.get("min_rel") or 0.1, "min_rel"),
                  "--min-run", v_num(v.get("min_run") or 14, "min_run", int)]
        a += ["--out", str(out)]
    elif tool == "analyze":
        az = v_file(audit, v.get("azure"), "azure", False)
        db = v_file(audit, v.get("databricks"), "databricks", False)
        if not (az or db):
            raise UserError("choose at least one input file")
        a = (["--azure", str(az)] if az else []) + (["--databricks", str(db)] if db else [])
        a += ["--start", v_month(v.get("start", ""), "start"), "--end", v_month(v.get("end", ""), "end"),
              "--out", str(out)]
    elif tool == "cloudability_probe":
        a = ["cloudability", "probe", "--region", v.get("region") or "eu", "--out", str(out)]
        env = secret_env(tool, v)
    elif tool == "cloudability_export":
        if not v.get("currency"):
            raise UserError("currency is required")
        a = ["cloudability", "export", "--region", v.get("region") or "eu", "--currency", v["currency"].upper(),
             "--start", v_month(v.get("start", ""), "start"), "--end", v_month(v.get("end", ""), "end"),
             "--dimensions", columns(v.get("dimensions")) or "vendor,enhanced_service_name",
             "--metric", (v.get("metric") or "unblended_cost").strip(), "--out", str(out)]
        for f in lines(v.get("filter")):
            a += ["--filter", f]
        if str(v.get("view_id") or "").strip():
            a += ["--view-id", v_num(v["view_id"], "view_id", int)]
        env = secret_env(tool, v)
    elif tool == "apptioone_download":
        if not str(v.get("api_url") or "").startswith("https://"):
            raise UserError("api_url must be an https URL copied from TBM Studio")
        a = ["apptioone", "--api-url", v["api_url"].strip(), "--frontdoor", (v.get("frontdoor") or "").strip(),
             "--out", str(out)]
        if v.get("environment_id"):
            a += ["--environment-id", v["environment_id"].strip()]
        elif v.get("customer"):
            a += ["--customer", v["customer"].strip()]
        else:
            raise UserError("give either the environment ID or the customer domain")
        env = secret_env(tool, v)
    elif tool == "apptio_normalize":
        a = ["--input", str(v_file(audit, v.get("input"), "input")), "--out", str(out),
             "--date-column", v.get("date_column") or "", "--cost-column", v.get("cost_column") or "",
             "--metric-name", v.get("metric_name") or "", "--report-label", v.get("report_label") or "",
             "--start", v_month(v.get("start", ""), "start"), "--end", v_month(v.get("end", ""), "end")]
        for d in lines(columns(v.get("dimension")).replace(",", "\n")):
            a += ["--dimension", d]
        if v.get("currency"):
            a += ["--currency", v["currency"].upper()]
    elif tool == "apptio_analyze":
        a = ["--input", str(v_file(audit, v.get("input"), "input")),
             "--start", v_month(v.get("start", ""), "start"), "--end", v_month(v.get("end", ""), "end"),
             "--out", str(out)]
        m = v_file(audit, v.get("manifest"), "manifest", False)
        if m:
            a += ["--manifest", str(m)]
    else:
        raise UserError(f"unknown tool {tool}")
    return [sys.executable, str(ROOT / "tools" / TOOLS[tool]["script"]), *a], env


def secret_env(tool: str, v: dict) -> dict[str, str]:
    env = {}
    for f in TOOLS[tool]["fields"]:
        if f["type"] == "secret":
            val = str(v.get(f["name"]) or "").strip()
            if val:
                env[f["env"]] = val
            elif not os.getenv(f["env"]):
                raise UserError(f"{f['label']['en']}: required (or set environment variable {f['env']})")
    return env


def public_values(tool: str, v: dict) -> dict:
    spec = TOOLS.get(tool) or CALCS.get(tool) or {"fields": []}
    secret = {f["name"] for f in spec["fields"] if f["type"] in SECRET_TYPES}
    return {k: val for k, val in v.items() if k not in secret and not k.startswith("_")}


def summary(tool: str, stdout: str) -> str:
    keys = {"delta": ("Per day:", "Rows needed"), "onset": ("ONSET:", "Threshold"),
            "monthly": ("Monthly series",), "analyze": ("Generated report",)}.get(tool, ())
    picked = [ln.strip() for ln in stdout.splitlines() if ln.strip().startswith(keys)] if keys else []
    if picked:
        return " · ".join(picked)
    rest = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    return rest[-1] if rest else ""


def run_process(argv: list[str], env_extra: dict, timeout: int = TIMEOUT) -> tuple[int, str, str]:
    env = os.environ.copy() | env_extra | {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    try:
        p = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return 124, "", f"ERROR: timed out after {timeout} s"
    except FileNotFoundError as exc:
        return 127, "", f"ERROR: {exc}"
    return p.returncode, p.stdout, p.stderr


def inventory(subscription: str, out: Path) -> tuple[int, str, str]:
    """Python port of tools/azure_workspace_inventory.ps1 (read-only, Azure CLI)."""
    sub = subscription.strip()
    if not sub or not all(c.isalnum() or c == "-" for c in sub):
        return 2, "", "ERROR: invalid subscription ID"
    az = shutil.which("az") or shutil.which("az.cmd")
    if not az:
        return 127, "", "ERROR: Azure CLI (az) is not installed or not on PATH. Run 'az login' after installing it."
    rc, so, se = run_process([az, "resource", "list", "--subscription", sub, "--resource-type",
                              "Microsoft.Databricks/workspaces", "--output", "json", "--only-show-errors"], {}, 300)
    if rc != 0:
        return rc, so, se or "ERROR: Azure Resource Manager query failed - check 'az login' and permissions"
    try:
        items = json.loads(so or "[]")
    except json.JSONDecodeError:
        return 2, so, "ERROR: unexpected Azure CLI output"
    cols = ["subscription_id", "workspace_name", "databricks_workspace_id", "azure_resource_id", "resource_group",
            "managed_resource_group_id", "location", "sku"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in items:
            props = r.get("properties") or {}
            w.writerow([sub, r.get("name", ""), props.get("workspaceId", ""), r.get("id", ""),
                        r.get("resourceGroup", ""), props.get("managedResourceGroupId", ""), r.get("location", ""),
                        (r.get("sku") or {}).get("name", "")])
    return 0, f"Read-only Azure Databricks workspace inventory: {out.name}\nWorkspace count: {len(items)}\n", ""


def run_tool(audit_id: str, step: str, action_id: str, tool: str, out_rel: str, values: dict,
             evidence: bool = True) -> dict:
    audit = core.audit_dir(audit_id)
    if tool not in TOOLS:
        raise UserError(f"unknown tool {tool}")
    out = core.inside(audit, out_rel)
    out.parent.mkdir(parents=True, exist_ok=True)
    if tool == "inventory":
        rc, so, se = inventory(str(values.get("subscription") or ""), out)
    else:
        argv, env = build(audit_id, tool, values, out)
        rc, so, se = run_process(argv, env)
    outputs = []
    if out.is_dir():
        outputs = [core.rel_of(audit, p) for p in sorted(out.rglob("*")) if p.is_file()]
    elif out.is_file():
        outputs = [core.rel_of(audit, out)]
    result = {"rc": rc, "stdout": so, "stderr": se, "outputs": outputs, "summary": summary(tool, so)}
    if rc == 0 and evidence and outputs:
        result["evidence_id"] = core.add_evidence(audit_id, step, {
            "check_or_hypothesis": action_id, "ledger_or_source": TOOLS[tool]["source"],
            "query_file_or_portal_view": f"tool:{tool}",
            "parameters": json.dumps({"tool": tool, "values": public_values(tool, values)}, ensure_ascii=False),
            "result_file": core.rel_of(audit, out), "observation": result["summary"][:500],
            "currency": str(values.get("currency") or "").upper() or core.settings(audit_id)["currency"],
        })
    return result


# ---------------------------------------------------------------- calculators
def month_cost_series(path: Path, date_col: str | None, cost_col: str | None) -> dict[str, Decimal]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        dcol = period_delta.pick(headers, date_col or None,
                                 period_delta.DATE_ALIASES + ("BillingMonth", "Month", "month", "UsageMonth"), True, "date")
        ccol = period_delta.pick(headers, cost_col or None,
                                 ("CostUSD", "Cost (USD)", "total") + period_delta.COST_ALIASES, True, "cost")
        out: dict[str, Decimal] = {}
        for row in reader:
            raw = (row.get(dcol) or "").strip()
            if not raw:
                continue
            m = raw[:7] if len(raw) == 7 and raw[4] == "-" else period_delta.parse_date(raw).strftime("%Y-%m")
            out[m] = out.get(m, Decimal(0)) + period_delta.parse_cost(row.get(ccol) or "0")
    return out


def calc_r6(audit_id: str, v: dict) -> dict:
    audit = core.audit_dir(audit_id)
    exp = month_cost_series(v_file(audit, v.get("export_monthly"), "export monthly"), "month", "total")
    ca = month_cost_series(v_file(audit, v.get("cost_analysis"), "cost analysis"), v.get("date_col"), v.get("cost_col"))
    tol = Decimal(v_num(v.get("tolerance") or "0.5", "tolerance"))
    rows, worst = [], Decimal(0)
    for m in sorted(set(exp) | set(ca)):
        e, c = exp.get(m), ca.get(m)
        if e is None or c is None:
            rows.append([m, f"{e or ''}", f"{c or ''}", "", "", "MISSING"])
            continue
        diff = e - c
        pct = abs(diff) / abs(c) * 100 if c else Decimal(0)
        worst = max(worst, pct)
        rows.append([m, f"{e:.2f}", f"{c:.2f}", f"{diff:.2f}", f"{pct:.3f}", "PASS" if pct <= tol else "FAIL"])
    out = audit / "01_data_quality/results" / f"R6_reconciliation__{core.today()}.csv"
    write_rows(out, ["month", "export", "cost_analysis", "diff", "diff_pct", "verdict"], rows)
    fails = sum(r[-1] != "PASS" for r in rows)
    msg = f"R6: {len(rows)} months, max diff {worst:.3f}% (tolerance {tol}%), {fails} not PASS"
    core.set_table_values(audit / "scope_record.md", {"1.2 Export vs Cost Analysis": f"Δmax {worst:.3f}% ({'PASS' if not fails else 'FAIL - R6_reconciliation'})"})
    return {"message": msg, "outputs": [core.rel_of(audit, out)], "ok": fails == 0}


def total_rate(path: Path, v: dict, base: str, cmp: str) -> tuple[Decimal, Decimal, Decimal, str, list[str]]:
    ns = type("A", (), {"filter": lines(v.get("filter")), "date_col": None, "cost_col": None,
                        "currency_col": None, "currency": (v.get("currency") or None), "group": ""})()
    try:
        rows, _, currency = period_delta.load(path, ns)
        _, rb, rc, dt, _, _, warnings = period_delta.deltas(rows, period_delta.parse_period(base),
                                                           period_delta.parse_period(cmp))
    except period_delta.InputError as exc:
        raise UserError(str(exc)) from None
    return rb, rc, dt, currency, warnings


def calc_size(audit_id: str, v: dict) -> dict:
    audit = core.audit_dir(audit_id)
    path = v_file(audit, v.get("csv"), "csv")
    base, cmp = v_period(v.get("base", ""), "B"), v_period(v.get("cmp", ""), "C")
    rb, rc, dt, currency, warnings = total_rate(path, v, base, cmp)
    b0, b1 = period_delta.parse_period(base)
    c0, c1 = period_delta.parse_period(cmp)
    abs_delta = rc * (c1 - c0).days - rb * (b1 - b0).days
    pct = dt / rb * 100 if rb else None
    rows = [["r(B) per day", f"{rb:.2f}"], ["r(C) per day", f"{rc:.2f}"], ["delta per day", f"{dt:.2f}"],
            ["delta per day %", "" if pct is None else f"{pct:.1f}"], ["annualized (x365)", f"{dt * 365:.0f}"],
            ["absolute delta C - B", f"{abs_delta:.2f}"], ["currency", currency]]
    persistence = ""
    if v.get("persist"):
        per = v_period(v["persist"], "P")
        r_c2, r_p, _, _, w2 = total_rate(path, v, cmp, per)
        warnings += w2
        persistence = f"{r_p - r_c2:+.2f}/day (r(P) {r_p:.2f} vs r(C) {r_c2:.2f})"
        rows.append(["persistence r(P) - r(C)", f"{r_p - r_c2:.2f}"])
    out = audit / "02_confirm_and_size/results" / f"size__{core.template_vars(audit_id)['details']}__{core.today()}.csv"
    write_rows(out, ["metric", "value"], rows)
    if str(v.get("write_scope", "true")).lower() in ("true", "1", "on", "yes"):
        core.set_table_values(audit / "scope_record.md", {
            "r(B) per day": f"{rb:.2f} {currency}", "r(C) per day": f"{rc:.2f} {currency}",
            "Δr per day / %": f"{dt:+.2f} {currency}" + ("" if pct is None else f" / {pct:+.1f}%"),
            "Annualized run-rate impact": f"{dt * 365:+.0f} {currency}",
            "Monthly absolute Δ": f"{abs_delta:+.2f} {currency}",
            **({"Persistence r(P)": persistence} if persistence else {}),
        })
        core.update_register_rows(audit_id, "delta_bridge", "line_id", {"TOTAL": {
            "currency": currency, "cost_per_day_b": f"{rb:.2f}", "cost_per_day_c": f"{rc:.2f}",
            "delta_per_day": f"{dt:.2f}", "share_of_total": "1.00"}})
    msg = f"B {rb:.2f} → C {rc:.2f} {currency}/day · Δ {dt:+.2f}/day" + ("" if pct is None else f" ({pct:+.1f}%)") \
        + f" · ×365 {dt * 365:+.0f}" + (f" · persistence {persistence}" if persistence else "")
    return {"message": msg, "warnings": warnings, "outputs": [core.rel_of(audit, out)], "ok": True}


def month_days_in(period: tuple[date, date]) -> list[str]:
    s, e = period
    months, d = [], date(s.year, s.month, 1)
    while d < e:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        if d >= s and nxt <= e:
            months.append(d.strftime("%Y-%m"))
        d = nxt
    return months


def calc_r8(audit_id: str, v: dict) -> dict:
    audit = core.audit_dir(audit_id)
    path = v_file(audit, v.get("csv"), "csv")
    base, cmp = v_period(v.get("base", ""), "B"), v_period(v.get("cmp", ""), "C")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        headers = csv.DictReader(fh).fieldnames or []
    svc = next((h for h in ("ServiceName", "ConsumedService", "MeterCategory", "serviceName") if h in headers), None)
    if not svc:
        raise UserError("no service column (ServiceName / MeterCategory) in the export")
    rb, rc, dt, currency, _ = total_rate(path, {"filter": f"{svc}={v.get('service_value') or 'Azure Databricks'}"},
                                         base, cmp)
    az_pct = dt / rb * 100 if rb else None
    db_path = v_file(audit, v.get("databricks"), "databricks")
    totals: dict[str, Decimal] = {}
    with db_path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if (row.get("currency_code") or "").upper() == "UNPRICED" or not (row.get("estimated_list_cost") or "").strip():
                continue
            m = (row.get("month") or "")[:7]
            totals[m] = totals.get(m, Decimal(0)) + period_delta.parse_cost(row["estimated_list_cost"])
    pb, pc = period_delta.parse_period(base), period_delta.parse_period(cmp)
    mb, mc = month_days_in(pb), month_days_in(pc)
    if not mb or not mc:
        raise UserError("B and C must each contain at least one full calendar month for the modeled side")
    def rate(ms):
        days = sum(monthrange(int(m[:4]), int(m[5:]))[1] for m in ms)
        return sum((totals.get(m, Decimal(0)) for m in ms), Decimal(0)) / days
    db_b, db_c = rate(mb), rate(mc)
    db_pct = (db_c - db_b) / db_b * 100 if db_b else None
    if az_pct is None or db_pct is None:
        verdict, gap = "UNKNOWN", None
    else:
        gap = abs(az_pct - db_pct)
        verdict = "PASS" if (az_pct >= 0) == (db_pct >= 0) and gap <= 15 else "FAIL"
    lines_ = [f"# R8 direction check - {core.today()}", "",
              f"B `{base}` · C `{cmp}` (end exclusive). Modeled side uses full months only: B {mb}, C {mc}.", "",
              "| View | r(B)/day | r(C)/day | Δ% |", "|---|---|---|---|",
              f"| Azure Actual, {svc} = {v.get('service_value') or 'Azure Databricks'} ({currency}) | {rb:.2f} | {rc:.2f} | "
              f"{'' if az_pct is None else f'{az_pct:+.1f}%'} |",
              f"| Databricks modeled list price (SQL 2.2) | {db_b:.2f} | {db_c:.2f} | {'' if db_pct is None else f'{db_pct:+.1f}%'} |",
              "", f"**Verdict: {verdict}**" + ("" if gap is None else f" - same sign required, gap {gap:.1f} pp (≤ 15 pp)."),
              "", "If FAIL: resolve discount / commitment / scope differences before step 05 (reference/03)."]
    out = audit / "03_accounting_effects/results" / f"R8_direction_check__{core.today()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines_) + "\n", encoding="utf-8")
    core.set_table_values(audit / "scope_record.md", {"3.8 Direction check": verdict})
    return {"message": f"R8 {verdict}: Azure {'' if az_pct is None else f'{az_pct:+.1f}%'} vs modeled "
                       f"{'' if db_pct is None else f'{db_pct:+.1f}%'}",
            "outputs": [core.rel_of(audit, out)], "ok": verdict == "PASS"}


def bridge_rows(audit_id: str) -> tuple[list[str], list[list[str]], dict[str, int]]:
    data = core.read_register(audit_id, "delta_bridge")
    return data["header"], data["rows"], {h: i for i, h in enumerate(data["header"])}


def num(s: str) -> Decimal | None:
    try:
        return Decimal(str(s).replace(",", "").strip())
    except Exception:
        return None


# One run produces every grouping of step 04; the file names are the ones listed in the step's CHECKS.md.
DECOMPOSE = (("delta_by_subscription", "SubscriptionId", "subscription"),
             ("delta_by_service", "ServiceName", "service"),
             ("delta_by_meter", "ServiceName,MeterCategory,MeterName", "meter"),
             ("delta_by_resource_group", "SubscriptionId,ResourceGroup", "resource group"),
             ("delta_by_resource", "ResourceId", "resource"))


def calc_decompose(audit_id: str, step: str, action_id: str, v: dict, evidence: bool = True) -> dict:
    """Run the delta tool for every grouping. A grouping whose columns are missing in the export schema (EA and MCA
    differ) is reported as a warning; the others are still produced."""
    base = {k: val for k, val in v.items() if k in ("csv", "base", "cmp", "filter", "currency")}
    src = v_file(core.audit_dir(audit_id), v.get("csv"), "csv")
    with src.open(newline="", encoding="utf-8-sig") as fh:
        header = {h.strip() for h in next(csv.reader(fh), [])}
    folder = core.step_dir(core.audit_dir(audit_id), step).name
    details = core.template_vars(audit_id)["details"]
    outputs, warnings, evidence_ids, done = [], [], [], []
    for stem, group, label in DECOMPOSE:
        wanted = group.split(",")
        usable = [c for c in wanted if c in header]
        if not usable:
            warnings.append(f"{label}: columns not found in the export ({group})")
            continue
        if usable != wanted:
            warnings.append(f"{label}: columns {sorted(set(wanted) - set(usable))} are not in the export; "
                            f"grouped by {','.join(usable)}")
        values = base | {"group": ",".join(usable),
                         "top": str(v.get("top") or 50) if stem == "delta_by_resource" else "20"}
        out_rel = f"{folder}/results/{stem}__{details}__{core.today()}.csv"
        try:
            res = run_tool(audit_id, step, action_id, "delta", out_rel, values, evidence)
        except UserError as exc:
            warnings.append(f"{label}: {exc}")
            continue
        if res["rc"] != 0:
            tail = [ln for ln in (res["stderr"] or res["stdout"]).splitlines() if ln.strip()]
            warnings.append(f"{label}: {tail[-1] if tail else 'failed'}")
            continue
        outputs += res["outputs"]
        done.append(label)
        if res.get("evidence_id"):
            evidence_ids.append(res["evidence_id"])
    if not done:
        raise UserError("no grouping could be produced: " + "; ".join(warnings))
    msg = f"Groupings produced: {', '.join(done)} ({len(outputs)} files)"
    result = {"message": msg, "warnings": warnings, "outputs": outputs, "ok": len(done) == len(DECOMPOSE)}
    if evidence_ids:
        result["evidence_id"] = ", ".join(evidence_ids)
    return result


def calc_operational(audit_id: str, v: dict) -> dict:
    header, rows, ix = bridge_rows(audit_id)
    total = next((num(r[ix["delta_per_day"]]) for r in rows if r[ix["line_id"]] == "TOTAL"), None)
    if total is None:
        raise UserError("TOTAL row has no delta_per_day yet (step 02)")
    acc = sum((num(r[ix["delta_per_day"]]) or Decimal(0) for r in rows if r[ix["category"]] == "ACCOUNTING"), Decimal(0))
    op = total - acc
    cur = next((r[ix["currency"]] for r in rows if r[ix["line_id"]] == "TOTAL"), "")
    core.set_table_values(core.audit_dir(audit_id) / "scope_record.md", {"**Operational Δr**": f"{op:+.2f} {cur}"})
    return {"message": f"Operational Δ = {total:.2f} - {acc:.2f} = {op:+.2f} {cur}/day (scope_record §7)", "outputs": [],
            "ok": True}


def calc_unx(audit_id: str, v: dict) -> dict:
    header, rows, ix = bridge_rows(audit_id)
    total_row = next((r for r in rows if r[ix["line_id"]] == "TOTAL"), None)
    total = num(total_row[ix["delta_per_day"]]) if total_row else None
    if total is None:
        raise UserError("TOTAL row has no delta_per_day yet (step 02)")
    explained = sum((num(r[ix["delta_per_day"]]) or Decimal(0) for r in rows
                     if r[ix["category"]] in ("ACCOUNTING", "ROOT_CAUSE", "SHARED_UNALLOCATED", "OUT_OF_SCOPE")),
                    Decimal(0))
    unx = total - explained
    unx_row = next((r for r in rows if r[ix["line_id"]] == "UNX"), None)
    if unx_row is None:
        unx_row = [""] * len(header)
        unx_row[ix["line_id"]], unx_row[ix["category"]] = "UNX", "UNEXPLAINED"
        rows.append(unx_row)
    unx_row[ix["delta_per_day"]] = f"{unx:.2f}"
    unx_row[ix["currency"]] = total_row[ix["currency"]]
    for r in rows:
        d = num(r[ix["delta_per_day"]])
        if d is not None and total:
            r[ix["share_of_total"]] = f"{d / total:.4f}"
    core.write_register(audit_id, "delta_bridge", header, rows)
    share = abs(unx) / abs(total) if total else Decimal(0)
    return {"message": f"UNX = {unx:+.2f}/day = {share:.1%} of TOTAL (R4 ≤ 10%)", "outputs": ["delta_bridge.csv"],
            "ok": share <= Decimal("0.10")}


def calc_driver_card(audit_id: str, v: dict) -> dict:
    rel = core.new_driver_card(audit_id, str(v.get("name") or ""))
    return {"message": f"Created {rel}", "outputs": [rel], "ok": True, "open": rel}


def file_digest(path: Path) -> tuple[str, int]:
    if path.is_dir():
        h = hashlib.sha256()
        n = 0
        for p in sorted(path.rglob("*")):
            if p.is_file() and p.suffix in (".csv", ".json"):
                h.update(p.name.encode())
                h.update(p.read_bytes().replace(b"\r\n", b"\n"))
                n += 1
        return h.hexdigest()[:16], n
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()[:16], data.count(b"\n")


def calc_reproduce(audit_id: str, v: dict) -> dict:
    from . import dbsql  # local import: optional connection
    audit = core.audit_dir(audit_id)
    data = core.read_register(audit_id, "evidence_register")
    ix = {h: i for i, h in enumerate(data["header"])}
    log = [f"# Reproduction log - {datetime.now():%Y-%m-%d %H:%M}", "",
           "| evidence_id | source | original | rerun | match |", "|---|---|---|---|---|"]
    stats = {"Y": 0, "N": 0, "MANUAL": 0}
    with tempfile.TemporaryDirectory() as tmp:
        for row in data["rows"]:
            eid = row[ix["evidence_id"]]
            if not eid or "YYYYMMDD" in eid:
                continue
            try:
                spec = json.loads(row[ix["parameters"]] or "{}")
            except json.JSONDecodeError:
                spec = {}
            original = core.inside(audit, row[ix["result_file"]]) if row[ix["result_file"]] else None
            if not original or not original.exists() or not ({"tool", "sql"} & set(spec)):
                log.append(f"| {eid} | {row[ix['query_file_or_portal_view']]} | - | - | MANUAL |")
                stats["MANUAL"] += 1
                continue
            o_hash, o_n = file_digest(original)
            target = Path(tmp) / f"{eid}{'' if original.is_dir() else original.suffix}"
            try:
                if "tool" in spec:
                    tool = spec["tool"]
                    if TOOLS[tool]["script"] is None or any(f["type"] == "secret" for f in TOOLS[tool]["fields"]):
                        raise UserError("needs live credentials - reproduce manually")
                    argv, env = build(audit_id, tool, spec.get("values", {}), target)
                    rc, _, se = run_process(argv, env)
                    if rc != 0:
                        raise UserError(se.strip().splitlines()[-1] if se.strip() else f"exit {rc}")
                else:
                    if not dbsql.configured():
                        raise UserError("Databricks connection not configured")
                    dbsql.run_to_csv(spec["sql"], spec.get("params", {}), spec.get("statement", 0), target)
                r_hash, r_n = file_digest(target)
                match = "Y" if r_hash == o_hash else "N"
                log.append(f"| {eid} | {spec.get('tool') or spec.get('sql')} | {o_n} rows · {o_hash} | "
                           f"{r_n} rows · {r_hash} | {match} |")
                stats[match] += 1
            except (UserError, KeyError, OSError) as exc:
                log.append(f"| {eid} | {spec.get('tool') or spec.get('sql')} | {o_n} rows · {o_hash} | "
                           f"{str(exc)[:120]} | MANUAL |")
                stats["MANUAL"] += 1
    log += ["", f"Match: {stats['Y']} · mismatch: {stats['N']} · manual: {stats['MANUAL']}.",
            "Mismatches and manual rows must be resolved and noted before C8.1 is ticked."]
    out = audit / "08_validation/results" / f"reproduction_log__{core.today()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(log) + "\n", encoding="utf-8")
    return {"message": f"Reproduced: {stats['Y']} match, {stats['N']} mismatch, {stats['MANUAL']} manual",
            "outputs": [core.rel_of(audit, out)], "ok": stats["N"] == 0}


def calc_bridge_md(audit_id: str, v: dict) -> dict:
    header, rows, ix = bridge_rows(audit_id)
    cols = ["line_id", "category", "description", "delta_per_day", "share_of_total", "status", "owner", "evidence_ids"]
    cols = [c for c in cols if c in ix]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        if r[ix["category"]] in ("BUCKET", "DRIVER_CANDIDATE") or not r[ix["delta_per_day"]].strip():
            continue
        out.append("| " + " | ".join(r[ix[c]].replace("|", "/") for c in cols) + " |")
    return {"message": f"{len(out) - 2} bridge lines (BUCKET / DRIVER_CANDIDATE and empty lines omitted)",
            "text": "\n".join(out), "outputs": [], "ok": True}


CALC_FUNCS = {"decompose": calc_decompose, "r6": calc_r6, "size": calc_size, "r8": calc_r8, "operational": calc_operational, "unx": calc_unx,
              "driver_card": calc_driver_card, "reproduce": calc_reproduce, "bridge_md": calc_bridge_md}


def run_calc(audit_id: str, step: str, action_id: str, calc: str, values: dict, evidence: bool = True) -> dict:
    if calc not in CALC_FUNCS:
        raise UserError(f"unknown calculator {calc}")
    try:
        if calc == "decompose":
            return calc_decompose(audit_id, step, action_id, values, evidence)
        result = CALC_FUNCS[calc](audit_id, values)
    except period_delta.InputError as exc:
        raise UserError(str(exc)) from None
    if evidence and calc in ("r6", "size", "r8") and result.get("outputs"):
        result["evidence_id"] = core.add_evidence(audit_id, step, {
            "check_or_hypothesis": action_id, "ledger_or_source": "Azure Actual",
            "query_file_or_portal_view": f"calc:{calc}",
            "parameters": json.dumps({"calc": calc, "values": public_values(calc, values)}, ensure_ascii=False),
            "result_file": result["outputs"][0], "observation": result["message"][:500]})
    return result


def write_rows(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
