"""Web UI for the Azure Databricks cost-growth audit playbook.

Start with run.cmd (Windows) or ./run.sh; it serves http://127.0.0.1:8765 via uvicorn.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import core, dbsql, docs, i18n, runner, steps
from .core import ROOT, UserError

STATIC = Path(__file__).resolve().parent / "static"
VERSION = "1.0"
SQL_DEFAULTS = {"object_ids": "ALL", "cluster_sources": "ALL", "required_tag": "cost_center"}

app = FastAPI(title="Databricks cost audit", version=VERSION, docs_url=None, redoc_url=None)
app.add_middleware(i18n.LangMiddleware)


@app.exception_handler(UserError)
async def user_error(_: Request, exc: UserError):
    return JSONResponse({"error": i18n.tr(str(exc))}, status_code=400)


@app.exception_handler(KeyError)
async def key_error(_: Request, exc: KeyError):
    return JSONResponse({"error": i18n.tr(f"not found: {exc}")}, status_code=404)


# ---------------------------------------------------------------- meta
@app.get("/api/meta")
def meta():
    return {"version": VERSION, "steps": [{k: s[k] for k in ("id", "folder", "title", "question")} for s in steps.STEPS],
            "check_ru": steps.CHECK_RU, "registers": list(core.REGISTERS),
            "tools": {k: v["title"] for k, v in runner.TOOLS.items()},
            "calcs": {k: v["title"] for k, v in runner.CALCS.items()}}


# ---------------------------------------------------------------- audits
@app.get("/api/audits")
def audits():
    return core.list_audits()


@app.post("/api/audits")
def create(payload: dict = Body(...)):
    audit_id = str(payload.get("id") or "").strip()
    core.create_audit(audit_id, payload.get("settings") or {}, lang=i18n.LANG.get())
    return {"id": audit_id}


@app.delete("/api/audits/{audit_id}")
def delete_audit(audit_id: str):
    core.delete_audit(audit_id)
    return {"id": audit_id, "deleted": True}


@app.post("/api/demo")
def demo():
    audit_id = "demo-synthetic"
    if not (core.AUDITS / audit_id).is_dir():
        core.create_audit(audit_id, {"window_start": "2026-01-01", "window_end": "2026-11-01",
                                     "b_start": "2026-01-01", "b_end": "2026-04-01", "c_start": "2026-07-01",
                                     "c_end": "2026-10-01", "p_start": "2026-10-01", "p_end": "2026-11-01",
                                     "currency": "EUR", "analyst": "demo"}, lang=i18n.LANG.get())
        audit = core.audit_dir(audit_id)
        shutil.copyfile(ROOT / "examples/SYNTHETIC_azure_actual.csv",
                        audit / "01_data_quality/exports/azure_actual__SYNTHETIC.csv")
        shutil.copyfile(ROOT / "examples/SYNTHETIC_databricks_monthly.csv",
                        audit / "02_confirm_and_size/results/2.2_monthly_cost_by_sku__SYNTHETIC.csv")
        core.save_settings(audit_id, {"primary_export": "01_data_quality/exports/azure_actual__SYNTHETIC.csv"})
    return {"id": audit_id}


@app.get("/api/audits/{audit_id}")
def audit(audit_id: str):
    return {"id": audit_id, "settings": core.settings(audit_id), "status": core.status(audit_id),
            "primary_export": core.primary_export(audit_id)}


@app.put("/api/audits/{audit_id}/settings")
def put_settings(audit_id: str, payload: dict = Body(...)):
    return core.save_settings(audit_id, payload)


@app.get("/api/audits/{audit_id}/steps/{step_id}")
def step_view(audit_id: str, step_id: str):
    s = steps.step(step_id)
    st = core.status(audit_id)
    actions = []
    for a in s["actions"]:
        a = dict(a)
        if a.get("out"):
            a["out_expanded"] = core.expand(a["out"], audit_id, {"ext": ""})
        if a.get("name"):
            a["name_expanded"] = core.expand(a["name"], audit_id)
        if a["kind"] == "tool":
            a["tool_title"] = runner.TOOLS[a["tool"]]["title"]
        if a["kind"] == "calc":
            a["calc_title"] = runner.CALCS[a["calc"]]["title"]
        if a["kind"] == "sql":
            a["sql_titles"] = {f: docs.title_of(f) for f in a["sqls"]}
        actions.append(a)
    return {"step": {**{k: v for k, v in s.items() if k != "actions"}, "actions": actions},
            "status": next(x for x in st["steps"] if x["id"] == s["id"]), "all": st,
            "checks": core.read_checks(audit_id, step_id)}


# ---------------------------------------------------------------- checks
@app.put("/api/audits/{audit_id}/steps/{step_id}/checks/{check_id}")
def put_check(audit_id: str, step_id: str, check_id: str, payload: dict = Body(...)):
    checks = core.write_check(audit_id, step_id, check_id, str(payload.get("state", " ")), str(payload.get("reason", "")))
    return {"checks": checks, "status": core.status(audit_id)}


# ---------------------------------------------------------------- files
@app.get("/api/audits/{audit_id}/files")
def files(audit_id: str, folder: str = ""):
    return core.list_files(audit_id, folder)


@app.get("/api/audits/{audit_id}/preview")
def preview(audit_id: str, path: str, limit: int = Query(500, ge=1, le=5000)):
    out = core.preview(audit_id, path, limit)
    if out["kind"] == "markdown":
        out["html"] = docs.render_markdown(out["text"])
    return out


@app.get("/api/audits/{audit_id}/download")
def download(audit_id: str, path: str):
    p = core.inside(core.audit_dir(audit_id), path)
    if not p.is_file():
        raise UserError("file not found")
    return FileResponse(p, filename=p.name)


@app.delete("/api/audits/{audit_id}/file")
def delete_file(audit_id: str, path: str):
    return {"moved_to": core.trash(audit_id, path)}


@app.post("/api/audits/{audit_id}/upload")
def upload(audit_id: str, file: UploadFile = File(...), folder: str = Form(...), name: str = Form(""),
           overwrite: bool = Form(False), step: str = Form(""), action: str = Form(""), primary: bool = Form(False),
           evidence: bool = Form(True)):
    rel = core.save_upload(audit_id, folder, name or file.filename or "upload.csv", file.file, overwrite)
    if primary:
        core.save_settings(audit_id, {"primary_export": rel})
    eid = None
    if evidence and step:
        eid = core.add_evidence(audit_id, step, {"check_or_hypothesis": action, "ledger_or_source": "portal export",
                                                 "query_file_or_portal_view": "upload", "result_file": rel})
    return {"path": rel, "evidence_id": eid}


@app.get("/api/audits/{audit_id}/text")
def get_text(audit_id: str, path: str, create: str = ""):
    p = core.inside(core.audit_dir(audit_id), path)
    if not p.exists() and create:
        core.write_text(audit_id, path, create)
    text = core.read_text(audit_id, path)
    return {"path": path, "text": text, "html": docs.render_markdown(text)}


@app.put("/api/audits/{audit_id}/text")
def put_text(audit_id: str, payload: dict = Body(...)):
    core.write_text(audit_id, str(payload.get("path") or ""), str(payload.get("text") or ""))
    return {"ok": True, "status": core.status(audit_id)}


@app.post("/api/render")
def render(payload: dict = Body(...)):
    return {"html": docs.render_markdown(str(payload.get("text") or ""))}


@app.get("/api/audits/{audit_id}/headers")
def headers(audit_id: str, path: str):
    return core.csv_headers(audit_id, path)


# ---------------------------------------------------------------- registers
@app.get("/api/audits/{audit_id}/registers/{name}")
def get_register(audit_id: str, name: str):
    return core.read_register(audit_id, name)


@app.put("/api/audits/{audit_id}/registers/{name}")
def put_register(audit_id: str, name: str, payload: dict = Body(...)):
    core.write_register(audit_id, name, payload.get("header") or [], payload.get("rows") or [])
    return {"ok": True, "status": core.status(audit_id)}


# ---------------------------------------------------------------- tools & calculators
@app.get("/api/audits/{audit_id}/form")
def form(audit_id: str, step: str, action: str):
    a = steps.action(step, action)
    if a["kind"] == "tool":
        return {"fields": runner.form(audit_id, "tool", a["tool"], a.get("preset")),
                "out": core.expand(a["out"], audit_id, {"ext": ""}), "title": runner.TOOLS[a["tool"]]["title"]}
    if a["kind"] == "calc":
        return {"fields": runner.form(audit_id, "calc", a["calc"]), "title": runner.CALCS[a["calc"]]["title"]}
    raise UserError("action has no form")


@app.post("/api/audits/{audit_id}/run")
def run(audit_id: str, payload: dict = Body(...)):
    step_id, action_id = str(payload.get("step")), str(payload.get("action"))
    a = steps.action(step_id, action_id)
    values = dict(payload.get("values") or {}) | (a.get("preset") or {})
    evidence = bool(payload.get("evidence", True))
    if a["kind"] == "tool":
        out = core.expand(a["out"], audit_id, {"ext": str(values.get("ext") or "")})
        result = runner.run_tool(audit_id, step_id, action_id, a["tool"], out, values, evidence)
    elif a["kind"] == "calc":
        result = runner.run_calc(audit_id, step_id, action_id, a["calc"], values, evidence)
    else:
        raise UserError("action cannot be run")
    for key in ("message", "summary", "stdout", "stderr"):
        if result.get(key):
            result[key] = i18n.tr(result[key])
    if result.get("warnings"):
        result["warnings"] = [i18n.tr(w) for w in result["warnings"]]
    result["status"] = core.status(audit_id)
    return result


# ---------------------------------------------------------------- SQL
def sql_defaults(audit_id: str) -> dict[str, str]:
    s = core.settings(audit_id)
    out = dict(SQL_DEFAULTS) | {"start_date": s["window_start"], "end_date": s["window_end"],
                                "base_start": s["b_start"], "base_end": s["b_end"],
                                "cmp_start": s["c_start"], "cmp_end": s["c_end"]}
    top = core.latest_file(audit_id, "05_databricks_decomposition/results/5.3_object_delta*.csv")
    if top:
        ids = []
        with (core.audit_dir(audit_id) / top).open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if row.get("object_id") and not row["object_id"].startswith("product:"):
                    ids.append(row["object_id"])
                try:
                    if float(row.get("cumulative_share") or 0) >= 0.9 or len(ids) >= 25:
                        break
                except ValueError:
                    pass
        if ids:
            out["object_ids"] = ",".join(ids)
    return out


def sql_out(audit_id: str, step_id: str, action: dict, file: str, index: int, params: list[str]) -> str:
    stem = Path(file).stem
    names = (action.get("outs") or {}).get(stem, [stem])
    name = names[index] if index < len(names) else f"{stem}_{chr(65 + index)}"
    tag = "{details}" if any(p.startswith(("base_", "cmp_")) for p in params) else "{window}"
    folder = steps.step(step_id)["folder"]
    return core.expand(f"{folder}/results/{name}__{tag}__{{today}}.csv", audit_id)


@app.get("/api/audits/{audit_id}/sql")
def sql_view(audit_id: str, step: str, action: str, file: str):
    a = steps.action(step, action)
    if file not in a.get("sqls", []):
        raise UserError("SQL file not part of this action")
    defaults = sql_defaults(audit_id)
    stmts = []
    for i, st in enumerate(dbsql.statements(file)):
        params = {p: defaults.get(p, "") for p in st["params"]}
        stmts.append({"index": i, "sql": st["sql"], "inline": dbsql.inline(st["sql"], params), "params": params,
                      "out": sql_out(audit_id, step, a, file, i, st["params"])})
    return {"file": file, "header": dbsql.header_comment(file), "statements": stmts, "configured": dbsql.configured()}


@app.post("/api/audits/{audit_id}/sql/run")
def sql_run(audit_id: str, payload: dict = Body(...)):
    step_id, action_id, file = str(payload.get("step")), str(payload.get("action")), str(payload.get("file"))
    a = steps.action(step_id, action_id)
    if file not in a.get("sqls", []):
        raise UserError("SQL file not part of this action")
    index = int(payload.get("statement") or 0)
    params = {k: str(v) for k, v in (payload.get("params") or {}).items()}
    stmt = dbsql.statements(file)[index]
    out_rel = sql_out(audit_id, step_id, a, file, index, stmt["params"])
    audit = core.audit_dir(audit_id)
    n = dbsql.run_to_csv(file, params, index, core.inside(audit, out_rel))
    eid = None
    if payload.get("evidence", True):
        eid = core.add_evidence(audit_id, step_id, {
            "check_or_hypothesis": action_id, "ledger_or_source": "Databricks system tables",
            "query_file_or_portal_view": file,
            "parameters": json.dumps({"sql": file, "statement": index, "params": params}, ensure_ascii=False),
            "result_file": out_rel, "observation": f"{n} rows"})
    return {"path": out_rel, "rows": n, "evidence_id": eid, "status": core.status(audit_id)}


# ---------------------------------------------------------------- settings
@app.get("/api/settings/databricks")
def get_db():
    return dbsql.config()


@app.put("/api/settings/databricks")
def put_db(payload: dict = Body(...)):
    return dbsql.save_config(payload)


@app.post("/api/settings/databricks/test")
def test_db():
    return {"message": dbsql.test_connection()}


@app.post("/api/system/selftest")
def selftest():
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tools/tests", "-p", "test_*.py"],
                       cwd=ROOT, capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
    return {"rc": p.returncode, "output": (p.stdout + p.stderr)[-20000:], "python": sys.version.split()[0]}


# ---------------------------------------------------------------- docs
@app.get("/api/docs/tree")
def doc_tree(lang: str = "en"):
    return docs.tree(lang if lang in ("en", "ru") else "en")


@app.get("/api/glossary")
def glossary(lang: str = "en"):
    return docs.glossary(lang if lang in ("en", "ru") else "en")


@app.get("/api/docs/page")
def doc_page(path: str, lang: str = "en"):
    return docs.render(path, lang if lang in ("en", "ru") else "en")


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
