"""Tests for the web interface (webapp/). Skipped when FastAPI is not installed."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    from fastapi.testclient import TestClient
    from webapp import core, dbsql, steps
    from webapp.main import app
except ImportError:  # pragma: no cover - interface dependencies not installed
    TestClient = None


@unittest.skipIf(TestClient is None, "fastapi / webapp dependencies not installed")
class WebappTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._audits, self._cfg = core.AUDITS, dbsql.CONFIG_FILE
        core.AUDITS = self.tmp
        dbsql.CONFIG_FILE = self.tmp / "_settings.json"
        self.c = TestClient(app)
        r = self.c.post("/api/audits", json={"id": "t1", "settings": {
            "window_start": "2026-01-01", "window_end": "2026-11-01", "b_start": "2026-01-01", "b_end": "2026-04-01",
            "c_start": "2026-07-01", "c_end": "2026-10-01", "p_start": "2026-10-01", "p_end": "2026-11-01",
            "currency": "eur"}})
        self.assertEqual(r.status_code, 200, r.text)
        shutil.copyfile(ROOT / "examples/SYNTHETIC_azure_actual.csv",
                        self.tmp / "t1/01_data_quality/exports/azure_actual__SYNTH.csv")

    def tearDown(self):
        core.AUDITS, dbsql.CONFIG_FILE = self._audits, self._cfg
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_audit_rejects_invalid_id(self):
        r = self.c.post("/api/audits", json={"id": "аудит", "settings": {}})
        self.assertEqual(r.status_code, 400)
        self.assertIn("audit id", r.json()["error"].lower())

    def test_delete_audit(self):
        r = self.c.post("/api/audits", json={"id": "t-del", "settings": {}})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue((self.tmp / "t-del").is_dir())
        r = self.c.delete("/api/audits/t-del")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse((self.tmp / "t-del").exists())
        self.assertEqual(self.c.delete("/api/audits/t-del").status_code, 400)

    def test_settings_mirrored_into_scope_record(self):
        s = self.c.get("/api/audits/t1").json()["settings"]
        self.assertEqual(s["currency"], "EUR")
        text = (self.tmp / "t1/scope_record.md").read_text(encoding="utf-8")
        self.assertIn("`2026-01-01:2026-04-01`", text)
        r = self.c.put("/api/audits/t1/settings", json={"b_start": "2026-05-01", "b_end": "2026-04-01"})
        self.assertEqual(r.status_code, 400)

    def test_step_definitions_cover_playbook(self):
        folders = sorted(p.name for p in (ROOT / "playbook").iterdir() if p.is_dir() and p.name[:2].isdigit())
        self.assertEqual([s["folder"] for s in steps.STEPS], folders)
        ids = {c for s in folders for c in [l.split()[3] for l in (ROOT / "playbook" / s / "CHECKS.md")
               .read_text(encoding="utf-8").splitlines() if l.startswith("- [ ]")]}
        self.assertEqual(ids - set(steps.CHECK_RU), set(), "checks without Russian translation")
        for s in steps.STEPS:
            for a in s["actions"]:
                for f in a.get("sqls", []):
                    self.assertTrue((ROOT / f).is_file(), f)
                for d in a.get("docs", []) + a.get("links", []):
                    self.assertTrue((ROOT / d).is_file(), d)
                self.assertTrue(a["title"]["en"] and a["title"]["ru"], a["id"])

    def test_decompose_writes_five_groupings_and_evidence(self):
        r = self.c.post("/api/audits/t1/run", json={"step": "04", "action": "4.1", "values": {
            "csv": "01_data_quality/exports/azure_actual__SYNTH.csv", "base": "2026-01-01:2026-04-01",
            "cmp": "2026-07-01:2026-10-01"}}).json()
        self.assertIn("message", r, r)
        names = sorted(Path(o).name.split("__")[0] for o in r["outputs"])
        self.assertEqual(names, ["delta_by_meter", "delta_by_resource", "delta_by_resource_group",
                                 "delta_by_service", "delta_by_subscription"], r)
        self.assertEqual(r["evidence_id"].count("EVD-04-"), 5)
        ev = self.c.get("/api/audits/t1/registers/evidence_register").json()
        self.assertEqual(ev["rows"][-1][0], "EVD-04-005")
        # the five outputs and the evidence rows tick the derived checks without a manual tick
        view = self.c.get("/api/audits/t1/steps/04").json()
        auto = {c["id"] for c in view["checks"] if c["auto"]}
        self.assertTrue({"C4.1", "C4.2", "C4.3", "C4.4", "C4.5", "C4.11"} <= auto, auto)
        self.assertFalse(next(c for c in view["checks"] if c["id"] == "C4.7")["auto"])

    def test_derived_checks_do_not_override_manual_marks(self):
        base = "/api/audits/t1/steps/00/checks"
        view = self.c.get("/api/audits/t1/steps/00").json()
        self.assertTrue(next(c for c in view["checks"] if c["id"] == "C0.5")["auto"])  # periods were saved
        r = self.c.put(f"{base}/C0.5", json={"state": "-", "reason": "not needed"}).json()
        hit = next(c for c in r["checks"] if c["id"] == "C0.5")
        self.assertEqual((hit["state"], hit["auto"]), ("-", False))

    def test_levels_and_info_in_step_view(self):
        view = self.c.get("/api/audits/t1/steps/08").json()
        levels = {a["id"]: a["level"] for a in view["step"]["actions"]}
        self.assertEqual(levels["8.1"], "core")
        self.assertEqual(levels["8.5"], "optional")
        view = self.c.get("/api/audits/t1/steps/01").json()
        a11 = next(a for a in view["step"]["actions"] if a["id"] == "1.1")
        self.assertTrue(a11["why"]["en"] and a11["how"]["ru"])

    def test_size_calc_fills_bridge_total_and_unx(self):
        r = self.c.post("/api/audits/t1/run", json={"step": "02", "action": "2.7", "values": {
            "csv": "01_data_quality/exports/azure_actual__SYNTH.csv", "base": "2026-01-01:2026-04-01",
            "cmp": "2026-07-01:2026-10-01"}}).json()
        self.assertTrue(r["ok"], r)
        bridge = self.c.get("/api/audits/t1/registers/delta_bridge").json()
        ix = bridge["header"].index("delta_per_day")
        total = next(row for row in bridge["rows"] if row[0] == "TOTAL")
        self.assertNotEqual(total[ix], "")
        auto02 = next(s for s in r["status"]["steps"] if s["id"] == "02")["auto"]
        self.assertEqual(auto02[0]["level"], "PASS")
        r = self.c.post("/api/audits/t1/run", json={"step": "07", "action": "7.5", "values": {}}).json()
        auto07 = next(s for s in r["status"]["steps"] if s["id"] == "07")["auto"]
        self.assertEqual(auto07[0]["level"], "PASS")  # identity holds after UNX

    def test_checks_require_reason_and_gate_rules(self):
        base = "/api/audits/t1/steps/00/checks"
        self.assertEqual(self.c.put(f"{base}/C0.9", json={"state": "-"}).status_code, 400)
        self.assertEqual(self.c.put(f"{base}/G0", json={"state": "!", "reason": "x"}).status_code, 400)
        r = self.c.put(f"{base}/C0.9", json={"state": "-", "reason": "none | really"}).json()
        hit = next(c for c in r["checks"] if c["id"] == "C0.9")
        self.assertEqual((hit["state"], hit["reason"]), ("-", "none / really"))
        text = (self.tmp / "t1/00_frame/CHECKS.md").read_text(encoding="utf-8")
        self.assertIn("- [-] C0.9 Rule deviations recorded or \"none\" (§3) | none / really", text)

    def test_upload_and_path_safety(self):
        r = self.c.post("/api/audits/t1/upload", data={"folder": "01_data_quality/exports", "name": "export_manifest__x.json",
                                                       "step": "01", "action": "1.2"},
                        files={"file": ("m.json", b"{}")})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["evidence_id"], "EVD-01-001")
        bad = self.c.post("/api/audits/t1/upload", data={"folder": "../..", "name": "x.csv"}, files={"file": ("x", b"1")})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.c.get("/api/audits/t1/preview", params={"path": "../../README.md"}).status_code, 400)
        self.assertEqual(self.c.put("/api/audits/t1/text", json={"path": "x.py", "text": "1"}).status_code, 400)

    def test_sql_view_splits_statements_and_inlines(self):
        v = self.c.get("/api/audits/t1/sql", params={"step": "01", "action": "1.6",
                                                     "file": "playbook/01_data_quality/sql/1.1_usage_coverage.sql"}).json()
        self.assertEqual(len(v["statements"]), 2)
        self.assertIn("1.1_workspace_presence__", v["statements"][1]["out"])
        self.assertIn("'2026-01-01'", v["statements"][0]["inline"])
        code = "\n".join(l.split("--")[0] for l in v["statements"][0]["inline"].splitlines())
        self.assertNotIn(":start_date", code)
        self.assertEqual(self.c.post("/api/audits/t1/sql/run", json={
            "step": "01", "action": "1.6", "file": "playbook/01_data_quality/sql/1.1_usage_coverage.sql",
            "statement": 0, "params": {"start_date": "2026-01-01", "end_date": "2026-11-01"}}).status_code, 400)
        for f in (ROOT / "playbook").rglob("*.sql"):
            self.assertTrue(dbsql.statements(f.relative_to(ROOT).as_posix()), f)
        with self.assertRaises(core.UserError):
            dbsql.execute("DELETE FROM x", {})

    def test_docs_render_and_localize(self):
        page = self.c.get("/api/docs/page", params={"path": "playbook/README.md", "lang": "ru"}).json()
        self.assertTrue(page["translated"])
        self.assertIn('href="#/docs/reference/05_audit_rules.md"', page["html"])
        self.assertEqual(self.c.get("/api/docs/page", params={"path": "../.env"}).status_code, 400)
        self.assertEqual(self.c.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
