# Punctuation and dashes (binding)

Use **ASCII hyphen-minus** only: U+002D `-`.

## Forbidden in repository text

Do **not** use these in prose, UI strings, comments, or templates (Markdown, CSV, Python, JavaScript, HTML):

| Character | Name | Use instead |
|-----------|------|-------------|
| U+2013 | en dash | `-` |
| U+2014 | em dash | `-` |
| U+2015 | horizontal bar | `-` |

Examples: `step 02 - 07`, `2-64 characters`, `Azure - Databricks`, not em/en dashes.

**Exception:** inside fenced code blocks or literals that must reproduce an external API or portal label exactly (rare). If you copy such text, prefer ASCII in new project-authored content.

## Unicode minus

Mathematical minus `−` (U+2212) is discouraged in new docs; prefer ASCII `-` in formulas and tables unless a rendered spec requires U+2212.

## Enforcement

`tools/tests/test_typography.py` scans tracked source paths and fails on forbidden dash characters. Fix before merge.

## For agents

When editing or generating any project file, type `-` on the keyboard. Never insert U+2013/U+2014 from typography substitutions or smart punctuation.
