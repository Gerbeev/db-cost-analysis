"""Plain-language layer: glossary parity, every step / action has human wording in both languages,
and the "Overview" blocks of the documents are in sync with webapp/plain*.py."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from webapp import docs, plain, plain_docs, steps  # noqa: E402


class GlossaryTests(unittest.TestCase):
    def test_same_terms_in_both_languages(self):
        en = [t["id"] for t in docs.glossary("en")]
        ru = [t["id"] for t in docs.glossary("ru")]
        self.assertEqual(en, ru)
        self.assertGreaterEqual(len(en), 60)
        self.assertEqual(len(en), len(set(en)), "duplicate term ids")

    def test_every_term_has_a_short_definition(self):
        for lang in ("en", "ru"):
            for t in docs.glossary(lang):
                self.assertTrue(t["short"], f"{lang}:{t['id']} has no definition")
                self.assertLess(len(t["short"]), 220, f"{lang}:{t['id']} tooltip too long")

    def test_russian_glossary_is_russian(self):
        for t in docs.glossary("ru"):
            self.assertRegex(t["body"], r"[А-Яа-яЁё]", f"{t['id']} body is not translated")

    def test_internal_links_resolve(self):
        ids = {t["id"] for t in docs.glossary("en")}
        for t in docs.glossary("en"):
            for target in re.findall(r"\(#([a-z0-9-]+)\)", t["body"]):
                self.assertIn(target, ids)


class PlainStepsTests(unittest.TestCase):
    def test_every_step_has_plain_text_in_both_languages(self):
        for s in steps.STEPS:
            for key in ("plain", "result", "tip", "question", "goal", "gate"):
                for lang in ("en", "ru"):
                    self.assertTrue(s.get(key, {}).get(lang, "").strip(), f"step {s['id']} {key} {lang}")

    def test_every_action_has_plain_text_in_both_languages(self):
        for s in steps.STEPS:
            for a in s["actions"]:
                self.assertIn(a["id"], plain.ACT, f"action {a['id']} not in plain.py")
                for lang in ("en", "ru"):
                    self.assertTrue(a["title"][lang].strip(), f"{a['id']} title {lang}")
                    self.assertTrue(a["text"][lang].strip(), f"{a['id']} text {lang}")
        known = {a["id"] for s in steps.STEPS for a in s["actions"]}
        self.assertFalse(set(plain.ACT) - known, "plain.py has actions that do not exist")

    def test_russian_text_is_russian(self):
        for s in steps.STEPS:
            self.assertRegex(s["plain"]["ru"], r"[А-Яа-яЁё]")
            for a in s["actions"]:
                self.assertRegex(a["text"]["ru"], r"[А-Яа-яЁё]", f"action {a['id']}")


class PlainDocsTests(unittest.TestCase):
    def test_plain_blocks_in_sync(self):
        self.assertEqual(plain_docs.sync(write=False), [],
                         "run webapp.plain_docs.sync() to refresh the 'Overview' blocks")


if __name__ == "__main__":
    unittest.main()


class MetricsTests(unittest.TestCase):
    def test_every_data_action_explains_why_and_how(self):
        from webapp import metrics, steps
        ids = {a["id"] for s in steps.STEPS for a in s["actions"]}
        self.assertEqual(set(metrics.INFO) - ids, set(), "info for an unknown action")
        # every action that collects data from a portal, a system table or a file needs a how-to
        for s in steps.STEPS:
            for a in s["actions"]:
                if a["kind"] in ("upload", "sql") and a["level"] == "core":
                    self.assertIn(a["id"], metrics.INFO, a["id"])
        for aid, (why, how) in metrics.INFO.items():
            for lang in ("en", "ru"):
                self.assertTrue(why[lang].strip(), f"{aid} why {lang}")
        for aid in [a["id"] for s in steps.STEPS for a in s["actions"] if a["kind"] in ("upload", "sql")
                    and a["level"] == "core"]:
            for lang in ("en", "ru"):
                self.assertTrue(metrics.INFO[aid][1][lang].strip(), f"{aid} how {lang}")

    def test_no_long_dashes_in_metrics(self):
        from webapp import metrics
        text = (ROOT / "webapp/metrics.py").read_text(encoding="utf-8")
        for ch in ("\u2013", "\u2014", "\u2212"):
            self.assertNotIn(ch, text)
        self.assertEqual(metrics.reference_doc("en", []).count("\u2014"), 0)

    def test_reference_page_in_sync(self):
        from webapp import plain_docs
        self.assertEqual(plain_docs.sync_generated(write=False), [], "run: python -m webapp.plain_docs")

    def test_levels_cover_known_actions(self):
        from webapp import steps
        ids = {a["id"] for s in steps.STEPS for a in s["actions"]}
        self.assertLessEqual(steps.OPTIONAL, ids)
        for s in steps.STEPS:
            self.assertTrue(any(a["level"] == "core" for a in s["actions"]))
