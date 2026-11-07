# Audits

One folder per audit, created in the web interface (**Audits → Audit workspace management**). Contents are **git-ignored** (billing data, IDs, names) - store in an access-controlled location; redact before sharing.

- Status of an audit is shown on every step page; `audits/<audit-id>/STATUS.md` is regenerated after every change.
- `_settings.json` - interface settings (Databricks host / warehouse; never a token). May be committed (see `.gitignore`). `_logs/` and per-audit `_trash/` are temporary and stay ignored.
- Remove an audit: **Audits** list or audit **Overview** → **Delete audit** (deletes the folder under `audits/<id>/`).
- `demo-synthetic/` - demo audit on synthetic data (Audits → Open demo); can be deleted like any audit.
