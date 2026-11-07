"""Optional Databricks SQL execution (Statement Execution API 2.0, read-only SELECT queries).

Connection settings (host, warehouse) live in audits/_settings.json (git-ignored). Tokens are never
written to disk: either a personal access token kept in server memory for the session, the
DATABRICKS_TOKEN environment variable, or a short-lived Microsoft Entra token from `az account
get-access-token` (Azure CLI login).
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .core import AUDITS, ROOT, UserError

AZURE_DATABRICKS_RESOURCE = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
PARAM_RE = re.compile(r"(?<![:\w]):([a-z_][a-z0-9_]*)\b")
FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|COPY|OPTIMIZE|VACUUM)\b",
                       re.I)
_TOKEN: dict[str, str] = {}
CONFIG_FILE = AUDITS / "_settings.json"


# ---------------------------------------------------------------- config
def config() -> dict:
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.is_file() else {}
    d = data.get("databricks", {})
    return {"host": d.get("host", ""), "warehouse_id": d.get("warehouse_id", ""), "auth": d.get("auth", "pat"),
            "timeout": int(d.get("timeout", 600)),
            "token_set": bool(_TOKEN.get("pat") or os.getenv("DATABRICKS_TOKEN")),
            "az_available": bool(shutil.which("az") or shutil.which("az.cmd"))}


def save_config(values: dict) -> dict:
    host = str(values.get("host") or "").strip().rstrip("/")
    if host and not host.startswith("https://"):
        host = "https://" + host
    if host:
        p = urlsplit(host)
        if p.scheme != "https" or not p.hostname or p.path not in ("", "/") or p.username or p.query:
            raise UserError("host must look like https://adb-1234567890123456.7.azuredatabricks.net")
        host = f"https://{p.hostname}"
    wh = str(values.get("warehouse_id") or "").strip()
    if wh and not re.fullmatch(r"[A-Za-z0-9]{6,64}", wh):
        raise UserError("warehouse ID: letters and digits only (SQL warehouse → Connection details)")
    auth = values.get("auth") or "pat"
    if auth not in ("pat", "azure_cli"):
        raise UserError("auth must be pat or azure_cli")
    timeout = int(values.get("timeout") or 600)
    if not 30 <= timeout <= 3600:
        raise UserError("timeout must be 30..3600 seconds")
    AUDITS.mkdir(exist_ok=True)
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.is_file() else {}
    data["databricks"] = {"host": host, "warehouse_id": wh, "auth": auth, "timeout": timeout}
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    token = str(values.get("token") or "").strip()
    if token:
        _TOKEN["pat"] = token
    if values.get("forget_token"):
        _TOKEN.pop("pat", None)
    return config()


def configured() -> bool:
    c = config()
    return bool(c["host"] and c["warehouse_id"])


def token() -> str:
    c = config()
    if c["auth"] == "azure_cli":
        az = shutil.which("az") or shutil.which("az.cmd")
        if not az:
            raise UserError("Azure CLI (az) not found; install it and run 'az login', or use a personal access token")
        p = subprocess.run([az, "account", "get-access-token", "--resource", AZURE_DATABRICKS_RESOURCE,
                            "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True, timeout=60,
                           stdin=subprocess.DEVNULL)
        if p.returncode != 0 or not p.stdout.strip():
            raise UserError("az account get-access-token failed - run 'az login' first: " + p.stderr.strip()[-300:])
        return p.stdout.strip()
    tok = _TOKEN.get("pat") or os.getenv("DATABRICKS_TOKEN", "").strip()
    if not tok:
        raise UserError("no Databricks token: enter a personal access token in Settings or set DATABRICKS_TOKEN")
    return tok


# ---------------------------------------------------------------- SQL files
def sql_path(rel: str) -> Path:
    rel = (rel or "").replace("\\", "/")
    p = (ROOT / rel).resolve()
    if not (p.suffix == ".sql" and (ROOT / "playbook").resolve() in p.parents and p.is_file()):
        raise UserError("unknown SQL file")
    return p


def statements(rel: str) -> list[dict]:
    """Split a playbook SQL file into statements; comments kept with the statement that follows."""
    text = sql_path(rel).read_text(encoding="utf-8")
    out, buf, code = [], [], []
    for line in text.splitlines():
        buf.append(line)
        stripped = line.split("--", 1)[0].rstrip()
        if stripped.strip():
            code.append(stripped)
        if stripped.endswith(";"):
            body = "\n".join(buf).rstrip()
            if code:
                out.append({"sql": body, "params": sorted(set(PARAM_RE.findall("\n".join(code))))})
            buf, code = [], []
    if code:
        out.append({"sql": "\n".join(buf).rstrip(), "params": sorted(set(PARAM_RE.findall("\n".join(code))))})
    return out


def header_comment(rel: str) -> str:
    lines = []
    for line in sql_path(rel).read_text(encoding="utf-8").splitlines():
        if not line.startswith("--"):
            break
        lines.append(line[2:].strip())
    return "\n".join(lines)


def inline(sql: str, params: dict[str, str]) -> str:
    """SQL with parameter markers replaced by quoted literals (for copy/paste without widgets)."""
    def rep(m: re.Match) -> str:
        name = m.group(1)
        if name not in params:
            return m.group(0)
        return "'" + str(params[name]).replace("'", "''") + "'"
    out = []
    for line in sql.splitlines():
        code, sep, comment = line.partition("--")
        out.append(PARAM_RE.sub(rep, code) + sep + comment)
    return "\n".join(out)


# ---------------------------------------------------------------- execution
def _request(method: str, url: str, body: dict | None, tok: str, timeout: int = 60) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json", "User-Agent": "db-cost-analysis-ui"})
    try:
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise UserError(f"Databricks API HTTP {exc.code}: {detail}") from None
    except URLError as exc:
        raise UserError(f"cannot reach Databricks: {exc.reason}") from None


def execute(sql: str, params: dict[str, str], on_progress=None) -> tuple[list[str], list[list]]:
    if FORBIDDEN.search("\n".join(l.split("--", 1)[0] for l in sql.splitlines())):
        raise UserError("only read-only SELECT statements are executed (rule R12)")
    c = config()
    if not configured():
        raise UserError("Databricks connection not configured (Settings)")
    tok = token()
    base = c["host"]
    resp = _request("POST", f"{base}/api/2.0/sql/statements/", {
        "warehouse_id": c["warehouse_id"], "statement": sql.strip().rstrip(";"),
        "parameters": [{"name": k, "value": str(v), "type": "STRING"} for k, v in params.items()],
        "wait_timeout": "30s", "on_wait_timeout": "CONTINUE", "disposition": "INLINE", "format": "JSON_ARRAY",
    }, tok, timeout=90)
    sid = resp.get("statement_id")
    deadline = time.time() + c["timeout"]
    while resp.get("status", {}).get("state") in ("PENDING", "RUNNING"):
        if time.time() > deadline:
            try:
                _request("POST", f"{base}/api/2.0/sql/statements/{sid}/cancel", {}, tok)
            finally:
                raise UserError(f"query exceeded {c['timeout']} s and was cancelled")
        time.sleep(3)
        resp = _request("GET", f"{base}/api/2.0/sql/statements/{sid}", None, tok)
    state = resp.get("status", {}).get("state")
    if state != "SUCCEEDED":
        err = resp.get("status", {}).get("error", {})
        raise UserError(f"query {state}: {err.get('message', '')[:800]}")
    cols = [col["name"] for col in resp.get("manifest", {}).get("schema", {}).get("columns", [])]
    result = resp.get("result", {}) or {}
    rows = list(result.get("data_array", []) or [])
    link = result.get("next_chunk_internal_link")
    while link:
        chunk = _request("GET", f"{base}{link}", None, tok)
        rows += chunk.get("data_array", []) or []
        link = chunk.get("next_chunk_internal_link")
    if resp.get("manifest", {}).get("truncated"):
        raise UserError("result truncated by Databricks (> 25 MiB inline) - narrow the period or export from the SQL editor")
    return cols, rows


def safe_cell(value) -> str:
    if value is None:
        return ""
    text = str(value)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r") and not re.fullmatch(r"[+-]?\d+(\.\d+)?([eE][+-]?\d+)?", text):
        return "'" + text
    return text


def run_to_csv(rel: str, params: dict[str, str], index: int, out: Path) -> int:
    stmts = statements(rel)
    if not 0 <= index < len(stmts):
        raise UserError("statement index out of range")
    needed = {p: params.get(p, "") for p in stmts[index]["params"]}
    missing = [p for p, v in needed.items() if not str(v).strip()]
    if missing:
        raise UserError(f"missing parameters: {', '.join(missing)}")
    cols, rows = execute(stmts[index]["sql"], needed)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([safe_cell(x) for x in r])
    return len(rows)


def test_connection() -> str:
    _, rows = execute("SELECT current_user() AS user", {})
    return f"OK: {rows[0][0] if rows else '?'}"
