"""Reject typographic dashes in project text (reference/13_punctuation.md)."""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = re.compile("[\u2013\u2014\u2015\u2212]")
# reference/13_punctuation*.md name the forbidden characters on purpose (the U+2212 example).
ALLOW = {"reference/13_punctuation.md"}
# audits/ holds git-ignored user data and generated outputs; .venv holds third-party packages.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".cursor", "terminals", "assets", "audits", ".venv"}
SKIP_SUFFIX = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".pyc", ".woff", ".woff2",
}


def candidate_paths():
    """Tracked + untracked-but-not-ignored files when git is available, else every file under ROOT."""
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT,
                             capture_output=True, timeout=60, check=True).stdout.decode("utf-8", "replace")
        return [ROOT / rel for rel in out.split("\0") if rel]
    except (OSError, subprocess.SubprocessError):
        return list(ROOT.rglob("*"))


def iter_text_files():
    for p in candidate_paths():
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in SKIP_SUFFIX:
            continue
        yield p


class TypographyTests(unittest.TestCase):
    def test_no_typographic_dashes(self):
        bad: list[str] = []
        for p in iter_text_files():
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if FORBIDDEN.search(text) and p.relative_to(ROOT).as_posix() not in ALLOW:
                bad.append(str(p.relative_to(ROOT)))
        self.assertFalse(bad, "typographic dashes found (use ASCII '-'): " + ", ".join(sorted(bad)[:20]) +
                         (f" … +{len(bad) - 20}" if len(bad) > 20 else ""))


if __name__ == "__main__":
    unittest.main()
