#!/usr/bin/env python3
"""Read-only IBM Cloudability v3 and ApptioOne/TBM Studio exports.

Credentials stay in memory. TLS verification is enabled, redirects are blocked,
and user-supplied reporting parameters are never interpreted as executable code.
"""
from __future__ import annotations

import argparse
import base64
import calendar
import csv
import getpass
import json
import logging
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from http.cookies import SimpleCookie

from analyze_costs import month_sequence, csv_safe_cell

TRACE = 5
logging.addLevelName(TRACE, "TRACE")
LOG = logging.getLogger("apptio_export")
ROOT = Path(__file__).resolve().parents[1]
REGIONS = {
    "us": "api.cloudability.com",
    "usgov": "api.usgov.cloudability.com",
    "eu": "api-eu.cloudability.com",
    "apac": "api-au.cloudability.com",
    "me": "api-me.cloudability.com",
    "ca": "api-ca.cloudability.com",
    "in": "api-in.cloudability.com",
    "jp": "api-jp.cloudability.com",
    "sg": "api-sg.cloudability.com",
}
MEASURE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
MAX_EXPORT_BYTES = 500 * 1024 * 1024


class ExportError(ValueError):
    """A safe-to-display operational or validation error."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ExportError(f"HTTP redirect {code} blocked to prevent credential disclosure")


OPENER = build_opener(NoRedirect())


def configure_log(level: str) -> None:
    folder = ROOT / "audits" / "_logs"
    folder.mkdir(exist_ok=True, parents=True)
    LOG.setLevel(TRACE)
    for handler in list(LOG.handlers):
        LOG.removeHandler(handler)
        handler.close()
    handler = logging.FileHandler(folder / "apptio_api.log", mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    handler.setLevel({"CRITICAL": 50, "ERROR": 40, "WARNING": 30,
                      "INFO": 20, "DEBUG": 10, "TRACE": TRACE}[level])
    LOG.addHandler(handler)
    LOG.propagate = False


def credentials(env_name: str, prompt: str) -> str:
    value = os.getenv(env_name, "").strip()
    if value:
        return value
    if not sys.stdin.isatty():
        raise ExportError(f"Set the {env_name} environment variable (interactive prompt unavailable)")
    value = getpass.getpass(prompt).strip()
    if not value:
        raise ExportError(f"Missing {env_name}")
    return value


def validated_https(url: str, allowed: set[str]) -> str:
    p = urlsplit(url)
    if (p.scheme != "https" or not p.hostname or p.port not in (None, 443)
            or p.username or p.password or p.fragment or p.hostname.lower() not in allowed):
        raise ExportError("HTTPS URL host is not in the explicit allowed-host list")
    return url


def response_bytes(url: str, headers: dict[str, str], timeout: int, retries: int = 3) -> tuple[bytes, dict]:
    # The exporter only issues GET calls, except the documented Frontdoor login.
    req = Request(url, headers=headers, method="GET")
    for attempt in range(retries + 1):
        try:
            with OPENER.open(req, timeout=timeout) as result:
                data = result.read(MAX_EXPORT_BYTES + 1)
                if len(data) > MAX_EXPORT_BYTES:
                    raise ExportError("API response exceeds 500 MiB; use a smaller report")
                return data, dict(result.headers)
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = min(30, 2 ** attempt)
                raw = exc.headers.get("Retry-After")
                if raw and raw.isdecimal():
                    wait = min(30, int(raw))
                LOG.warning("Retrying read-only API GET after HTTP %d", exc.code)
                time.sleep(wait)
                continue
            raise ExportError(f"API request failed (HTTP {exc.code}); verify access, scope and region") from None
        except URLError as exc:
            raise ExportError("Cannot reach API endpoint; check DNS, HTTPS proxy and network access") from None
    raise ExportError("Retry limit reached")


def request_json(url: str, headers: dict[str, str], timeout: int) -> dict | list:
    body, _ = response_bytes(url, headers, timeout)
    try:
        return json.loads(body)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ExportError("API returned invalid JSON (possible login page or unsupported endpoint)") from exc


def cloudability_headers(api_key: str) -> dict[str, str]:
    basic = base64.b64encode((api_key + ":").encode("utf-8")).decode("ascii")
    return {"Authorization": "Basic " + basic, "Accept": "application/json"}


def cloudability_url(region: str, endpoint: str, query: list[tuple[str, str]] | None = None) -> str:
    base = f"https://{REGIONS[region]}/v3/{endpoint}"
    return base + ("?" + urlencode(query) if query else "")


def ensure_measures(data: dict | list) -> dict[str, str]:
    if isinstance(data, dict):
        data = data.get("result", [])
    if not isinstance(data, list):
        raise ExportError("Cost measures endpoint returned an unexpected schema")
    return {item["name"]: item["type"] for item in data
            if isinstance(item, dict) and isinstance(item.get("name"), str)
            and item.get("type") in ("metric", "dimension")}


def parse_fields(raw: str, label: str, max_count: int) -> list[str]:
    fields = [part.strip() for part in raw.split(",")]
    if not fields or len(fields) > max_count or len(fields) != len(set(fields)) or not all(MEASURE_RE.fullmatch(f) for f in fields):
        raise ExportError(f"Invalid {label}: use 1-{max_count} distinct measure names")
    return fields


def number(value: object, name: str) -> str:
    try:
        d = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ExportError(f"Report returned a non-numeric {name} value") from exc
    if not d.is_finite():
        raise ExportError(f"Report returned a non-finite {name} value")
    return str(d)


def get_cost_rows(api_key: str, region: str, query: list[tuple[str, str]], timeout: int,
                  max_pages: int = 500) -> tuple[list[dict], int]:
    headers = cloudability_headers(api_key)
    token = None
    used_tokens: set[str] = set()
    rows: list[dict] = []
    pages = 0
    while pages < max_pages:
        params = query + ([("token", token)] if token else [])
        payload = request_json(cloudability_url(region, "reporting/cost/run", params), headers, timeout)
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ExportError("Cost reporting response has no results array")
        rows.extend(payload["results"])
        pages += 1
        pagination = payload.get("pagination") or {}
        if not isinstance(pagination, dict):
            raise ExportError("Invalid cost report pagination metadata")
        next_token = pagination.get("next")
        if not next_token:
            return rows, pages
        if not isinstance(next_token, str) or next_token in used_tokens:
            raise ExportError("Cost pagination token is invalid or repeated")
        used_tokens.add(next_token)
        token = next_token
    raise ExportError("Pagination safety limit reached; reduce dimensions or split the report")


def atomic_write_csv(path: Path, columns: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", dir=path.parent,
                                     prefix=".apptio_", suffix=".tmp", delete=False) as fh:
        temp_name = fh.name
        try:
            writer = csv.writer(fh)
            writer.writerow([csv_safe_cell(cell) for cell in columns])
            writer.writerows([csv_safe_cell(cell) for cell in row] for row in rows)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
    os.replace(temp_name, path)


def run_cloudability(args: argparse.Namespace) -> None:
    key = credentials("CLOUDABILITY_API_KEY", "Cloudability API key (hidden): ")
    measures_data = request_json(cloudability_url(args.region, "reporting/cost/measures"),
                                 cloudability_headers(key), args.timeout)
    measures = ensure_measures(measures_data)
    if not measures:
        raise ExportError("No cost measures returned; check Cloudability permissions")
    if args.action == "probe":
        metrics = sorted(n for n, kind in measures.items() if kind == "metric")
        dimensions = sorted(n for n, kind in measures.items() if kind == "dimension")
        print(f"Cloudability API access verified: {len(metrics)} metrics, {len(dimensions)} dimensions")
        print("Metrics (sample): " + ", ".join(metrics[:25]))
        print("Dimensions (sample): " + ", ".join(dimensions[:25]))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"metrics": metrics, "dimensions": dimensions}, indent=2) + "\n", encoding="utf-8")
        print(f"Allowed measures saved to {args.out}")
        return

    dims = parse_fields(args.dimensions, "dimensions", 15)
    metric = parse_fields(args.metric, "metric", 1)[0]
    unsupported = [d for d in dims if measures.get(d) != "dimension"]
    if unsupported or measures.get(metric) != "metric":
        raise ExportError("Requested measure is not available to this user: " + ", ".join(unsupported or [metric]))
    if not CURRENCY_RE.fullmatch(args.currency.upper()):
        raise ExportError("--currency must be a three-letter reporting currency verified in the Cloudability UI")
    if args.view_id is not None and args.view_id < 0:
        raise ExportError("--view-id must be non-negative")
    if args.max_pages < 1 or args.max_pages > 10000:
        raise ExportError("--max-pages must be 1..10000")
    months = month_sequence(args.start, args.end)
    all_rows: list[list[str]] = []
    month_info = []
    for month in months:
        year, mon = map(int, month.split("-"))
        last = calendar.monthrange(year, mon)[1]
        query = [("start_date", f"{month}-01"), ("end_date", f"{month}-{last:02d}"),
                 ("dimensions", ",".join(dims)), ("metrics", metric), ("limit", "10000")]
        if args.view_id is not None:
            query.append(("view_id", str(args.view_id)))
        if args.apply_allocations:
            query.append(("applyAllocations", "true"))
        for item in args.filter:
            if not item.strip() or len(item) > 500:
                raise ExportError("Invalid report filter")
            query.append(("filters", item))
        LOG.info("Cloudability export: month=%s dimensions=%s metric=%s", month, ",".join(dims), metric)
        results, pages = get_cost_rows(key, args.region, query, args.timeout, args.max_pages)
        for item in results:
            if not isinstance(item, dict):
                raise ExportError("Cost result row is not an object")
            missing = [dim for dim in dims if dim not in item]
            if missing or metric not in item:
                raise ExportError("Cost result omitted requested fields: " + ", ".join(missing or [metric]))
            all_rows.append([month, args.currency.upper(), metric,
                             str(args.view_id) if args.view_id is not None else "USER_DEFAULT",
                             *[str(item.get(d) if item[d] is not None else "") for d in dims],
                             number(item[metric], metric)])
        month_info.append({"month": month, "rows": len(results), "pages": pages})
        print(f"{month}: {len(results)} rows across {pages} page(s)")
    columns = ["month", "currency", "metric", "view_id", *dims, "amount"]
    atomic_write_csv(args.out, columns, all_rows)
    manifest = {
        "source": "IBM Cloudability v3 reporting/cost/run", "region": args.region,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "month_start": args.start, "month_end": args.end, "currency_user_verified": args.currency.upper(),
        "metric": metric, "dimensions": dims, "view_id": args.view_id if args.view_id is not None else "USER_DEFAULT",
        "filters": args.filter, "apply_allocations": args.apply_allocations,
        "months": month_info, "total_rows": len(all_rows),
        "scope_warning": "Cloudability costs may overlap Azure actuals. Never add ledgers.",
        "zero_row_warning": [m["month"] for m in month_info if m["rows"] == 0]
    }
    manifest_path = args.out.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Cost export: {args.out}")
    print(f"Evidence manifest: {manifest_path}")
    print("IMPORTANT: Cloudability reporting currency and view scope are user-verified; do not add to Azure Actual totals.")


def post_frontdoor(url: str, payload: dict, timeout: int) -> str:
    req = Request(url, headers={"Content-Type": "application/json", "Accept": "application/json"},
                  data=json.dumps(payload).encode("utf-8"), method="POST")
    try:
        with OPENER.open(req, timeout=timeout) as result:
            token = result.headers.get("apptio-opentoken")
            if not token:
                for cookie_header in result.headers.get_all("Set-Cookie", []):
                    cookies = SimpleCookie()
                    try:
                        cookies.load(cookie_header)
                    except Exception:
                        continue
                    if "apptio-opentoken" in cookies:
                        token = cookies["apptio-opentoken"].value
                        break
    except HTTPError as exc:
        raise ExportError(f"Apptio Frontdoor authentication failed (HTTP {exc.code})") from None
    except URLError:
        raise ExportError("Apptio Frontdoor is unreachable") from None
    if not token:
        raise ExportError("Frontdoor did not return apptio-opentoken header")
    return token


def run_apptioone(args: argparse.Namespace) -> None:
    api_access = credentials("APPTIO_KEY_ACCESS", "Apptio key access (hidden): ")
    api_secret = credentials("APPTIO_KEY_SECRET", "Apptio key secret (hidden): ")
    frontdoor_host = args.frontdoor.lower().strip()
    if frontdoor_host not in {"frontdoor.apptio.com", "frontdoor-eu.apptio.com", "frontdoor.au.apptio.com"}:
        raise ExportError("Unsupported Frontdoor host; verify the Apptio region in official documentation")
    frontdoor_url = validated_https(f"https://{frontdoor_host}/service/apikeylogin", {frontdoor_host})
    report_host = urlsplit(args.api_url).hostname
    allowed_hosts = {h.lower() for h in args.allowed_host}
    if report_host and report_host.lower().endswith(".apptio.com"):
        allowed_hosts.add(report_host.lower())
    validated_https(args.api_url, allowed_hosts)
    environment_id = (args.environment_id or "").strip()
    if not environment_id and not args.customer:
        raise ExportError("Provide --environment-id or --customer for read-only environment discovery")
    if args.customer and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,253}", args.customer):
        raise ExportError("Invalid customer name")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", args.environment_name):
        raise ExportError("Invalid environment name")
    if args.out.suffix.lower() not in (".tsv", ".csv", ".json", ".xlsx"):
        raise ExportError("Output must use .tsv, .csv, .json or .xlsx extension")
    LOG.info("Authenticating with Frontdoor to download a read-only TBM Studio artifact")
    token = post_frontdoor(frontdoor_url, {"keyAccess": api_access, "keySecret": api_secret}, args.timeout)
    if not environment_id:
        env_url = f"https://{frontdoor_host}/api/environment/{quote(args.customer, safe='')}/{quote(args.environment_name, safe='')}"
        env_data = request_json(env_url, {"apptio-opentoken": token, "Accept": "application/json"}, args.timeout)
        if not isinstance(env_data, dict) or not isinstance(env_data.get("id"), (str, int)):
            raise ExportError("Environment lookup returned no usable id; use --environment-id")
        environment_id = str(env_data["id"])
    headers = {"apptio-opentoken": token, "apptio-current-environment": environment_id,
               "app-type": "Flagship", "app-version": "NA", "Accept": "*/*"}
    content, response_headers = response_bytes(args.api_url, headers, args.timeout)
    content_type = str(response_headers.get("Content-Type", "")).lower()
    if "text/html" in content_type or content[:128].lstrip().lower().startswith(b"<!doctype html"):
        raise ExportError("TBM Studio returned HTML instead of the selected report export")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="wb", dir=args.out.parent, prefix=".apptioone_", delete=False) as fh:
        temp_name = fh.name
        fh.write(content)
    os.replace(temp_name, args.out)
    LOG.info("TBM Studio export downloaded (%d bytes)", len(content))
    print(f"TBM Studio export: {args.out} ({len(content)} bytes)")
    print("This is a report-specific export; inspect its column definitions before reconciliation with Azure Actual.")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Read-only IBM Apptio API data exports")
    ap.add_argument("--log-level", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"], default="INFO")
    sub = ap.add_subparsers(dest="product", required=True)
    cloud = sub.add_parser("cloudability", help="IBM Cloudability v3 cost reports")
    cloud.add_argument("action", choices=["probe", "export"])
    cloud.add_argument("--region", choices=sorted(REGIONS), default="eu")
    cloud.add_argument("--timeout", type=int, default=60)
    cloud.add_argument("--start", default="2026-01")
    cloud.add_argument("--end", default="2026-10")
    cloud.add_argument("--dimensions", default="vendor,enhanced_service_name")
    cloud.add_argument("--metric", default="unblended_cost")
    cloud.add_argument("--filter", action="append", default=[], help="Cost filter, e.g. vendor==Azure (may be repeated)")
    cloud.add_argument("--view-id", type=int, help="Cloudability view ID; 0 only if user may access unfiltered data")
    cloud.add_argument("--currency", help="Required for export: reporting currency confirmed in Cloudability UI")
    cloud.add_argument("--apply-allocations", action="store_true")
    cloud.add_argument("--max-pages", type=int, default=500)
    cloud.add_argument("--out", type=Path)
    tbm = sub.add_parser("apptioone", help="Download a TBM Studio report using its UI-provided API URL")
    tbm.add_argument("--api-url", required=True)
    tbm.add_argument("--environment-id", help="Known Frontdoor environment ID")
    tbm.add_argument("--customer", help="Frontdoor customer domain for automatic environment ID lookup")
    tbm.add_argument("--environment-name", default="main", help="Frontdoor environment (default: main)")
    tbm.add_argument("--frontdoor", default="frontdoor-eu.apptio.com")
    tbm.add_argument("--allowed-host", action="append", default=[], help="Explicit host if a custom Apptio report domain is used")
    tbm.add_argument("--timeout", type=int, default=120)
    tbm.add_argument("--out", type=Path, required=True)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = parser()
    args = ap.parse_args(argv)
    configure_log(args.log_level)
    try:
        if args.product == "cloudability":
            if args.action == "probe":
                args.out = args.out or ROOT / "audits" / "_shared" / "cloudability_measures.json"
            else:
                if not args.currency:
                    raise ExportError("--currency is required; confirm the currency shown in the Cloudability report UI")
                args.out = args.out or ROOT / "audits" / "_shared" / "apptio_cloudability.csv"
            if not 1 <= args.timeout <= 600:
                raise ExportError("--timeout must be 1..600 seconds")
            run_cloudability(args)
        else:
            if not 1 <= args.timeout <= 600:
                raise ExportError("--timeout must be 1..600 seconds")
            run_apptioone(args)
        return 0
    except (ExportError, ValueError, OSError) as exc:
        LOG.error("Apptio export failed: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
