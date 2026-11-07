"""Russian localization coverage: every documentation page has a *.ru.md twin, UI strings exist in both
languages, audit templates and server messages are translated."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Generated sample output, not documentation.
NOT_TRANSLATED = {"examples/SYNTHETIC_report_example.md"}
CHECK_RE = re.compile(r"^- \[( |x|X|-|!)\] (\S+)\s")


def doc_files() -> list[Path]:
    globs = ["README.md", "playbook/**/*.md", "reference/*.md", "tools/README.md", "templates/*.md",
             "examples/*.md", "audits/README.md"]
    out = set()
    for g in globs:
        out.update(p for p in ROOT.glob(g) if not p.name.endswith(".ru.md"))
    return sorted(out)


class DocsLocalizationTests(unittest.TestCase):
    def test_every_doc_has_russian_twin(self):
        missing = [p.relative_to(ROOT).as_posix() for p in doc_files()
                   if p.relative_to(ROOT).as_posix() not in NOT_TRANSLATED
                   and not p.with_name(f"{p.stem}.ru.md").is_file()]
        self.assertEqual(missing, [], "add a *.ru.md translation")

    def test_russian_twins_have_cyrillic_and_same_tables(self):
        for p in doc_files():
            ru = p.with_name(f"{p.stem}.ru.md")
            if not ru.is_file():
                continue
            text = ru.read_text(encoding="utf-8")
            self.assertRegex(text, "[А-Яа-яЁё]", ru.name)
            en_rows = sum(1 for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("|"))
            ru_rows = sum(1 for l in text.splitlines() if l.startswith("|"))
            self.assertEqual(en_rows, ru_rows, f"table rows differ: {ru.relative_to(ROOT)}")

    def test_checks_ru_match_checks(self):
        for p in ROOT.glob("playbook/*/CHECKS.md"):
            ids = lambda f: [m.group(2) for l in f.read_text(encoding="utf-8").splitlines() if (m := CHECK_RE.match(l))]
            self.assertEqual(ids(p), ids(p.with_name("CHECKS.ru.md")), p.parent.name)

    def test_ui_strings_in_both_languages(self):
        text = (ROOT / "webapp/static/i18n.js").read_text(encoding="utf-8")
        en_part, ru_part = text.split("\n  ru: {", 1)
        key = re.compile(r"(?:^|[\s,{])([a-z][a-z0-9_]*):\s*[\"`]", re.M)
        self.assertEqual(set(key.findall(en_part)), set(key.findall(ru_part)))

    def test_steps_translated(self):
        from webapp import steps
        for s in steps.STEPS:
            for field in ("title", "question", "goal", "gate"):
                self.assertTrue(s[field]["ru"], f"{s['id']} {field}")
            for a in s["actions"]:
                self.assertTrue(a["title"]["ru"], a["id"])
                if a["text"]["en"]:
                    self.assertTrue(a["text"]["ru"], a["id"])


class ServerMessagesTests(unittest.TestCase):
    def test_translations(self):
        from webapp.i18n import tr
        cases = {
            "fewer than 2 delta_by_*.csv files - grouping consistency not checked": "меньше 2 файлов",
            "UNEXPLAINED = 12.0% of TOTAL (R4: <= 10% or accepted in CHECKS)": "от TOTAL",
            "file not found": "файл не найден",
            "reason required for [-] and [!]": "нужна причина",
            "B 1.00 → C 2.00 EUR/day · Δ +1.00/day (+100.0%) · ×365 +365": "/сутки",
            "ERROR: No rows after filters": "ОШИБКА: после фильтров",
        }
        for en, part in cases.items():
            self.assertIn(part, tr(en, "ru"), en)
            self.assertEqual(tr(en, "en"), en)

    def test_scope_labels_exist_in_both_templates(self):
        from webapp.core import SCOPE_LABELS_RU
        en = (ROOT / "templates/scope_record.md").read_text(encoding="utf-8")
        ru = (ROOT / "templates/scope_record.ru.md").read_text(encoding="utf-8")
        for k, v in SCOPE_LABELS_RU.items():
            self.assertIn(f"| {k}", en)
            self.assertIn(f"| {v}", ru)


if __name__ == "__main__":
    unittest.main()
