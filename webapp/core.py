"""Audit workspace operations used by the web UI.

Everything here works on files under audits/<id>/ only. The playbook, templates and tools
folders are read, never written.
"""
from __future__ import annotations

import csv
import io
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITS = ROOT / "audits"
PLAYBOOK = ROOT / "playbook"
TEMPLATES = ROOT / "templates"
sys.path.insert(0, str(ROOT / "tools"))

import check_audit  # noqa: E402
import new_audit  # noqa: E402

from . import i18n  # noqa: E402

AUDIT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{1,63}")
STEP_RE = re.compile(r"^\d\d_")
CHECK_LINE_RE = re.compile(r"^- \[( |x|X|-|!)\] (\S+)\s+(.*)$")
REGISTERS = {
    "delta_bridge": "delta_bridge.csv",
    "evidence_register": "evidence_register.csv",
    "hypothesis_register": "hypothesis_register.csv",
    "ibm_discrepancy_register": "08_validation/ibm_discrepancy_register.csv",
}
SETTINGS_FILE = "audit.json"
SETTING_KEYS = ("window_start", "window_end", "b_start", "b_end", "c_start", "c_end", "p_start", "p_end",
                "currency", "primary_export", "analyst")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".sql", ".log", ".tsv", ".csv"}
MAX_UPLOAD = 1024 * 1024 * 1024  # 1 GiB


class UserError(Exception):
    """Error shown to the user as-is."""


# ---------------------------------------------------------------- paths
def audit_dir(audit_id: str) -> Path:
    if not AUDIT_ID_RE.fullmatch(audit_id or ""):
        raise UserError("invalid audit id")
    path = AUDITS / audit_id
    if not path.is_dir():
        raise UserError(f"audit not found: {audit_id}")
    return path


def inside(base: Path, rel: str) -> Path:
    """Resolve rel under base; refuse traversal and hidden/system names."""
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel or any(part in ("", ".", "..") for part in rel.split("/")):
        raise UserError("invalid path")
    target = (base / rel).resolve()
    if base.resolve() not in target.parents and target != base.resolve():
        raise UserError("path outside the audit")
    return target


def rel_of(audit: Path, path: Path) -> str:
    return path.resolve().relative_to(audit.resolve()).as_posix()


def steps_of(audit: Path) -> list[Path]:
    return sorted(p for p in audit.iterdir() if p.is_dir() and STEP_RE.match(p.name))


def step_dir(audit: Path, step: str) -> Path:
    hit = next((p for p in steps_of(audit) if p.name[:2] == step[:2]), None)
    if hit is None:
        raise UserError(f"step not found: {step}")
    return hit


def today() -> str:
    return date.today().strftime("%Y%m%d")


# ---------------------------------------------------------------- audits
def list_audits() -> list[dict]:
    if not AUDITS.is_dir():
        return []
    out = []
    for p in sorted(AUDITS.iterdir()):
        if not (p.is_dir() and AUDIT_ID_RE.fullmatch(p.name) and steps_of(p)):
            continue
        st = status(p.name, write=False)
        out.append({"id": p.name, "current": st["current"], "passed": sum(s["passed"] for s in st["steps"]),
                    "total": len(st["steps"]), "settings": settings(p.name),
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")})
    return out


# Audit documents copied from templates; with lang="ru" the *.ru.md variant is used when it exists.
LOCALIZED_TEMPLATES = {
    "scope_record.md": "scope_record.md",
    "driver_card.md": "06_root_cause/_driver_card_TEMPLATE.md",
    "findings_report.md": "09_report_and_controls/findings_report.md",
}


def create_audit(audit_id: str, values: dict | None = None, lang: str = "en") -> str:
    AUDITS.mkdir(exist_ok=True)
    try:
        new_audit.create(audit_id, AUDITS)
    except SystemExit as exc:  # new_audit reports user errors via SystemExit
        raise UserError(str(exc).replace("ERROR: ", "")) from None
    if lang == "ru":
        for name, rel in LOCALIZED_TEMPLATES.items():
            src = TEMPLATES / name.replace(".md", ".ru.md")
            if src.is_file():
                shutil.copyfile(src, AUDITS / audit_id / rel)
    scope = AUDITS / audit_id / "scope_record.md"
    if scope.is_file():
        text = scope.read_text(encoding="utf-8")
        scope.write_text(text.replace("<audit ID>", audit_id).replace("<ID аудита>", audit_id), encoding="utf-8")
    save_settings(audit_id, values or {})
    return audit_id


def delete_audit(audit_id: str) -> None:
    if not AUDIT_ID_RE.fullmatch(audit_id or ""):
        raise UserError("invalid audit id")
    path = AUDITS / audit_id
    if not path.is_dir():
        raise UserError(f"audit not found: {audit_id}")
    if not steps_of(path):
        raise UserError(f"not an audit workspace: {audit_id}")
    shutil.rmtree(path)


# ---------------------------------------------------------------- settings
def settings(audit_id: str) -> dict:
    f = audit_dir(audit_id) / SETTINGS_FILE
    data = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    return {k: str(data.get(k, "") or "") for k in SETTING_KEYS}


def save_settings(audit_id: str, values: dict) -> dict:
    audit = audit_dir(audit_id)
    data = settings(audit_id)
    for k in SETTING_KEYS:
        if k in values:
            v = str(values[k] or "").strip()
            if k.endswith(("_start", "_end")) and v:
                try:
                    date.fromisoformat(v)
                except ValueError:
                    raise UserError(f"{k}: expected YYYY-MM-DD") from None
            if k == "currency":
                v = v.upper()
            data[k] = v
    for a, b in (("window_start", "window_end"), ("b_start", "b_end"), ("c_start", "c_end"), ("p_start", "p_end")):
        if data[a] and data[b] and data[a] >= data[b]:
            raise UserError(f"{a} must be before {b} (end is exclusive)")
    (audit / SETTINGS_FILE).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    sync_scope_periods(audit, data)
    return data


def period(data: dict, key: str) -> str:
    s, e = data.get(f"{key}_start"), data.get(f"{key}_end")
    return f"{s}:{e}" if s and e else ""


def sync_scope_periods(audit: Path, data: dict) -> None:
    """Mirror periods and currency into scope_record.md §3."""
    values = {
        "Analysis window": f"`{data['window_start']}` → `{data['window_end']}`"
        if data["window_start"] and data["window_end"] else "",
        "Baseline B": f"`{period(data, 'b')}`" if period(data, "b") else "",
        "Comparison C": f"`{period(data, 'c')}`" if period(data, "c") else "",
        "Persistence P": f"`{period(data, 'p')}`" if period(data, "p") else "",
        "Billing currency": data["currency"],
    }
    set_table_values(audit / "scope_record.md", {k: v for k, v in values.items() if v})


# Row labels of scope_record.md (EN template) -> the same rows in the RU template (templates/scope_record.ru.md).
SCOPE_LABELS_RU = {
    "Analysis window": "Окно анализа", "Baseline B": "Базовый период B", "Comparison C": "Период сравнения C",
    "Persistence P": "Период устойчивости P", "Billing currency": "Валюта счёта",
    "1.2 Export vs Cost Analysis": "1.2 Выгрузка vs Cost Analysis",
    "r(B) per day": "r(B) в сутки", "r(C) per day": "r(C) в сутки", "Δr per day / %": "Δr в сутки / %",
    "Annualized run-rate impact": "Годовой эффект темпа", "Monthly absolute Δ": "Абсолютная месячная Δ",
    "Persistence r(P)": "Устойчивость r(P)", "3.8 Direction check": "3.8 Проверка направления",
    "**Operational Δr**": "**Операционная Δr**",
}


def set_table_values(path: Path, values: dict[str, str]) -> None:
    """Set the 2nd column of markdown table rows whose first cell starts with a key (EN or RU label)."""
    if not path.is_file() or not values:
        return
    values = values | {SCOPE_LABELS_RU[k]: v for k, v in values.items() if k in SCOPE_LABELS_RU}
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        cells = line.split("|")
        if len(cells) < 4:
            continue
        label = cells[1].strip()
        for key, val in values.items():
            if label.startswith(key):
                cells[2] = f" {val.replace('|', '/')} "
                lines[i] = "|".join(cells)
                break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def template_vars(audit_id: str) -> dict[str, str]:
    s = settings(audit_id)
    b, c = s["b_start"][:7], s["c_start"][:7]
    return {"today": today(), "window": f"{s['window_start']}_{s['window_end']}".strip("_") or "window",
            "details": f"B{b}_C{c}" if b and c else "BC", "B": period(s, "b"), "C": period(s, "c"),
            "P": period(s, "p")}


def expand(template: str, audit_id: str, extra: dict | None = None) -> str:
    vals = template_vars(audit_id) | (extra or {})
    out = template
    for k, v in vals.items():
        out = out.replace("{" + k + "}", re.sub(r"[^A-Za-z0-9._-]", "-", v))
    return out


# ---------------------------------------------------------------- status & checks
def status(audit_id: str, write: bool = True) -> dict:
    audit = audit_dir(audit_id)
    results = [check_audit.evaluate(audit, s) for s in steps_of(audit)]
    if write:
        (audit / "STATUS.md").write_text(check_audit.render(audit, results), encoding="utf-8")
    blocked, steps = False, []
    for r in results:
        state = "PASSED" if r["passed"] else ("LOCKED" if blocked else "IN_PROGRESS")
        blocked = blocked or not r["passed"]
        steps.append({
            "name": r["name"], "id": r["name"][:2], "state": state, "passed": r["passed"],
            "checks_total": len(r["checks"]), "checks_open": len(r["open"]),
            "outputs": [{"pattern": p, "optional": o, "found": f} for p, o, f in r["outputs"]],
            "auto": [{"level": lvl, "message": i18n.tr(msg)} for lvl, msg in r["auto"]],
        })
    current = next((s["id"] for s in steps if not s["passed"]), None)
    return {"steps": steps, "current": current}


def read_checks(audit_id: str, step: str) -> list[dict]:
    audit = audit_dir(audit_id)
    path = step_dir(audit, step) / "CHECKS.md"
    proven = check_audit.derived_ids(audit, step_dir(audit, step))
    items, section = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        m = CHECK_LINE_RE.match(line)
        if m and section != "required outputs":
            body = m.group(3)
            text, _, reason = body.partition(" | ")
            state = m.group(1).lower()
            auto = state == " " and m.group(2) in proven
            items.append({"id": m.group(2), "state": "x" if auto else state, "text": text.strip(),
                          "reason": reason.strip(), "gate": m.group(2).startswith("G"), "auto": auto})
    return items


def write_check(audit_id: str, step: str, check_id: str, state: str, reason: str = "") -> list[dict]:
    if state not in (" ", "x", "-", "!"):
        raise UserError("state must be one of ' ', x, -, !")
    reason = " ".join((reason or "").split()).replace("|", "/")
    if state in "-!" and not reason:
        raise UserError("reason required for [-] and [!]")
    if check_id.startswith("G") and state in "-!":
        raise UserError("gate checks can only be open or done [x]")
    path = step_dir(audit_dir(audit_id), step) / "CHECKS.md"
    lines, found = path.read_text(encoding="utf-8").splitlines(), False
    for i, line in enumerate(lines):
        m = CHECK_LINE_RE.match(line)
        if m and m.group(2) == check_id:
            text = m.group(3).partition(" | ")[0].rstrip()
            lines[i] = f"- [{state}] {check_id} {text}" + (f" | {reason}" if state in "-!" else "")
            found = True
            break
    if not found:
        raise UserError(f"check not found: {check_id}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return read_checks(audit_id, step)


# ---------------------------------------------------------------- files
def list_files(audit_id: str, folder: str = "") -> list[dict]:
    audit = audit_dir(audit_id)
    base = inside(audit, folder) if folder else audit
    if not base.is_dir():
        return []
    out = []
    for p in sorted(base.rglob("*")):
        if not p.is_file() or "_trash" in p.relative_to(audit).parts:
            continue
        st = p.stat()
        out.append({"path": rel_of(audit, p), "size": st.st_size,
                    "modified": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
    return out


def save_upload(audit_id: str, folder: str, name: str, stream, overwrite: bool = False) -> str:
    audit = audit_dir(audit_id)
    name = Path((name or "").replace("\\", "/")).name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._()+-]{0,180}", name):
        raise UserError("invalid file name (letters, digits, space . _ - ( ) + only)")
    dest = inside(audit, f"{folder.strip('/')}/{name}")
    if dest.exists() and not overwrite:
        raise UserError(f"file exists: {rel_of(audit, dest)}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".upload_{dest.name}")
    size = 0
    with tmp.open("wb") as fh:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD:
                fh.close()
                tmp.unlink(missing_ok=True)
                raise UserError("file too large (max 1 GiB)")
            fh.write(chunk)
    tmp.replace(dest)
    return rel_of(audit, dest)


def trash(audit_id: str, rel: str) -> str:
    audit = audit_dir(audit_id)
    src = inside(audit, rel)
    if not src.is_file():
        raise UserError("file not found")
    if src.parent == audit and src.name in {"scope_record.md", *REGISTERS.values(), SETTINGS_FILE}:
        raise UserError("living registers cannot be removed")
    if src.name == "CHECKS.md":
        raise UserError("CHECKS.md cannot be removed")
    dest = audit / "_trash" / f"{datetime.now():%Y%m%d-%H%M%S}" / rel_of(audit, src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), dest)
    return rel_of(audit, dest)


def read_text(audit_id: str, rel: str) -> str:
    path = inside(audit_dir(audit_id), rel)
    if not path.is_file():
        raise UserError("file not found")
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_text(audit_id: str, rel: str, text: str) -> None:
    audit = audit_dir(audit_id)
    path = inside(audit, rel)
    if path.suffix.lower() not in (".md", ".txt"):
        raise UserError("only .md and .txt files can be edited as text")
    if path.name == "CHECKS.md":
        raise UserError("edit checks in the checklist, not as text")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8")


def csv_table(path: Path, limit: int | None = 500) -> dict:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        sample = fh.read(65536)
        fh.seek(0)
        delim = "\t" if path.suffix.lower() == ".tsv" or sample.count("\t") > sample.count(",") else ","
        reader = csv.reader(fh, delimiter=delim)
        header = next(reader, [])
        rows, total = [], 0
        for row in reader:
            total += 1
            if limit is None or len(rows) < limit:
                rows.append(row + [""] * (len(header) - len(row)))
    return {"header": header, "rows": rows, "total": total, "truncated": limit is not None and total > limit}


def preview(audit_id: str, rel: str, limit: int = 500) -> dict:
    path = inside(audit_dir(audit_id), rel)
    if not path.is_file():
        raise UserError("file not found")
    suffix = path.suffix.lower()
    if suffix in (".csv", ".tsv"):
        return {"kind": "table", **csv_table(path, limit)}
    if suffix in TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        return {"kind": "markdown" if suffix == ".md" else "text", "text": text[:400_000]}
    return {"kind": "binary", "size": path.stat().st_size}


def csv_headers(audit_id: str, rel: str) -> list[str]:
    path = inside(audit_dir(audit_id), rel)
    if not path.is_file():
        raise UserError("file not found")
    return csv_table(path, limit=0)["header"]


# ---------------------------------------------------------------- registers
def register_path(audit_id: str, name: str) -> Path:
    if name not in REGISTERS:
        raise UserError("unknown register")
    return audit_dir(audit_id) / REGISTERS[name]


def read_register(audit_id: str, name: str) -> dict:
    path = register_path(audit_id, name)
    return csv_table(path, limit=None) if path.is_file() else {"header": [], "rows": [], "total": 0}


def write_register(audit_id: str, name: str, header: list[str], rows: list[list[str]]) -> None:
    path = register_path(audit_id, name)
    original = csv_table(path, limit=0)["header"] if path.is_file() else header
    if header != original:
        raise UserError("register columns cannot be changed")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for row in rows:
        cells = [str(c if c is not None else "").replace("\r", " ").replace("\n", " ") for c in row]
        if any(c.strip() for c in cells):
            w.writerow((cells + [""] * len(header))[: len(header)])
    path.write_text(buf.getvalue(), encoding="utf-8")


def update_register_rows(audit_id: str, name: str, key: str, updates: dict[str, dict[str, str]]) -> None:
    """Set fields on rows identified by `key` column; append rows that do not exist."""
    data = read_register(audit_id, name)
    header, rows = data["header"], data["rows"]
    idx = {h: i for i, h in enumerate(header)}
    for kval, fields in updates.items():
        row = next((r for r in rows if r[idx[key]] == kval), None)
        if row is None:
            row = [""] * len(header)
            row[idx[key]] = kval
            rows.append(row)
        for f, v in fields.items():
            if f in idx:
                row[idx[f]] = v
    write_register(audit_id, name, header, rows)


def add_evidence(audit_id: str, step: str, fields: dict[str, str]) -> str:
    data = read_register(audit_id, "evidence_register")
    header = data["header"]
    prefix = f"EVD-{step[:2]}-"
    nums = [int(r[0][len(prefix):]) for r in data["rows"]
            if r and r[0].startswith(prefix) and r[0][len(prefix):].isdigit()]
    eid = f"{prefix}{(max(nums) + 1) if nums else 1:03d}"
    s = settings(audit_id)
    row = {h: "" for h in header} | {
        "evidence_id": eid, "step": step[:2], "currency": s["currency"],
        "period": " / ".join(x for x in (f"B {period(s, 'b')}" if period(s, "b") else "",
                                         f"C {period(s, 'c')}" if period(s, "c") else "") if x),
        "run_timestamp": datetime.now().isoformat(timespec="seconds"), "analyst": s["analyst"],
    } | {k: v for k, v in fields.items() if k in header}
    write_register(audit_id, "evidence_register", header, data["rows"] + [[row[h] for h in header]])
    return eid


def latest_file(audit_id: str, pattern: str) -> str:
    audit = audit_dir(audit_id)
    hits = sorted(audit.glob(pattern), key=lambda p: p.stat().st_mtime)
    return rel_of(audit, hits[-1]) if hits else ""


def primary_export(audit_id: str) -> str:
    s = settings(audit_id)
    if s["primary_export"] and (audit_dir(audit_id) / s["primary_export"]).is_file():
        return s["primary_export"]
    return latest_file(audit_id, "01_data_quality/exports/azure_actual*.csv")


def new_driver_card(audit_id: str, short_name: str) -> str:
    audit = audit_dir(audit_id)
    slug = re.sub(r"[^a-z0-9]+", "_", (short_name or "").lower()).strip("_")[:40]
    if not slug:
        raise UserError("short name required")
    folder = audit / "06_root_cause"
    nums = [int(m.group(1)) for p in folder.glob("driver_*.md") if (m := re.match(r"driver_(\d+)_", p.name))]
    nn = (max(nums) + 1) if nums else 1
    dest = folder / f"driver_{nn:02d}_{slug}.md"
    own = folder / "_driver_card_TEMPLATE.md"
    text = (own if own.is_file() else TEMPLATES / "driver_card.md").read_text(encoding="utf-8")
    text = text.replace("<nn>", f"{nn:02d}").replace("<short name>", short_name.strip())
    text = text.replace("RC-__", f"RC-{nn:02d}")
    dest.write_text(text, encoding="utf-8")
    return rel_of(audit, dest)
