#!/usr/bin/env python3
"""Create a new audit workspace under audits/<audit-id>/ from the playbook and templates.

    python tools/new_audit.py 2026-04-dbx-growth
    (normally created from the web interface: Audits -> New audit)

Creates one folder per playbook step with CHECKS.md (copied from playbook/<step>/CHECKS.md),
exports/ (raw downloads from portals) and results/ (SQL and tool outputs), plus the living
registers in the audit root. Never overwrites an existing audit. Python 3.10+, stdlib only.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "playbook"
TEMPLATES = ROOT / "templates"

# Living registers kept in the audit root (updated across several steps).
ROOT_FILES = ["scope_record.md", "evidence_register.csv", "hypothesis_register.csv", "delta_bridge.csv"]
# Step-specific templates: template file -> destination inside the audit.
STEP_FILES = {
    "driver_card.md": "06_root_cause/_driver_card_TEMPLATE.md",
    "ibm_discrepancy_register.csv": "08_validation/ibm_discrepancy_register.csv",
    "findings_report.md": "09_report_and_controls/findings_report.md",
}
NO_IO_FOLDERS = {"00_frame", "09_report_and_controls"}


def steps() -> list[Path]:
    found = sorted(p for p in PLAYBOOK.iterdir() if p.is_dir() and re.match(r"^\d\d_", p.name))
    if not found:
        raise SystemExit(f"ERROR: no step folders in {PLAYBOOK}")
    return found


def create(audit_id: str, base: Path) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,63}", audit_id):
        raise SystemExit(
            "ERROR: audit id must be 2-64 chars: Latin letters and digits only; "
            "start with a letter or digit; then '.', '_', '-' are also allowed"
        )
    target = base / audit_id
    if target.exists():
        raise SystemExit(f"ERROR: {target} already exists - nothing changed")
    target.mkdir(parents=True)
    for step in steps():
        dest = target / step.name
        dest.mkdir()
        shutil.copyfile(step / "CHECKS.md", dest / "CHECKS.md")
        (dest / "notes.md").write_text(f"# {step.name} - notes\n\nObservations, decisions, open questions.\n",
                                       encoding="utf-8")
        if step.name not in NO_IO_FOLDERS:
            (dest / "exports").mkdir()
            (dest / "results").mkdir()
    for name in ROOT_FILES:
        shutil.copyfile(TEMPLATES / name, target / name)
    for name, rel in STEP_FILES.items():
        shutil.copyfile(TEMPLATES / name, target / rel)
    (target / "STATUS.md").write_text(
        f"# Audit {audit_id}\n\nCreated {date.today().isoformat()}. Status is refreshed by the web interface after every change.\n",
        encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audit_id", help="Short id, e.g. 2026-04-dbx-growth")
    ap.add_argument("--base", type=Path, default=ROOT / "audits", help="Workspace root (default: audits/)")
    args = ap.parse_args(argv)
    target = create(args.audit_id, args.base)
    print(f"Created {target}")
    print("Next: open the audit in the web interface (run.cmd) and start with step 00")
    return 0


if __name__ == "__main__":
    sys.exit(main())
