"""Documentation browser: renders the repository's markdown / SQL / CSV docs for the UI."""
from __future__ import annotations

import csv
import html
import posixpath
import re
from pathlib import Path

import markdown

from .core import ROOT, UserError

DOC_GLOBS = ["README*.md", "playbook/**/*.md", "playbook/**/*.sql", "reference/*.md", "reference/*.csv",
             "tools/README*.md", "templates/*.md", "templates/*.csv", "examples/README*.md"]
SECTIONS = [
    ("start", {"en": "Start", "ru": "Начало"}, ["README.md", "playbook/README.md"]),
    ("reference", {"en": "Reference", "ru": "Справочник"}, ["reference/"]),
    ("steps", {"en": "Playbook steps", "ru": "Шаги плейбука"}, ["playbook/0"]),
    ("drivers", {"en": "Driver playbooks", "ru": "Плейбуки драйверов"}, ["playbook/06_root_cause/playbooks/"]),
    ("templates", {"en": "Templates", "ru": "Шаблоны"}, ["templates/"]),
    ("tools", {"en": "Tools and examples", "ru": "Инструменты и примеры"}, ["tools/", "examples/"]),
]
LINK_RE = re.compile(r'(href|src)="([^"]+)"')


def allowed() -> list[str]:
    seen = set()
    for pattern in DOC_GLOBS:
        for p in ROOT.glob(pattern):
            if p.is_file() and not re.search(r"\.[a-z]{2}\.md$", p.name):
                seen.add(p.relative_to(ROOT).as_posix())
    return sorted(seen)


def title_of(rel: str, lang: str = "en") -> str:
    p = ROOT / rel
    if p.suffix == ".md" and lang != "en" and p.with_name(f"{p.stem}.{lang}.md").is_file():
        p = p.with_name(f"{p.stem}.{lang}.md")
    if p.suffix == ".md":
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    if p.suffix == ".sql":
        first = p.read_text(encoding="utf-8").splitlines()[:1]
        if first and first[0].startswith("--"):
            return f"{p.stem} - " + first[0].lstrip("- ").split("·", 1)[-1].strip()
    return rel


def tree(lang: str = "en") -> list[dict]:
    docs = allowed()
    used, out = set(), []
    for key, label, prefixes in SECTIONS:
        items = []
        for rel in docs:
            if rel in used:
                continue
            if any(rel == p or (p.endswith("/") and rel.startswith(p)) or
                   (key == "steps" and rel.startswith(p) and "/playbooks/" not in rel) for p in prefixes):
                if key == "steps" and not rel.endswith("README.md"):
                    continue
                items.append({"path": rel, "title": title_of(rel, lang)})
                used.add(rel)
        if items:
            out.append({"key": key, "label": label, "items": items})
    return out


def resolve(rel: str) -> Path:
    rel = posixpath.normpath((rel or "").replace("\\", "/").lstrip("/"))
    if rel not in allowed():
        raise UserError("document not found")
    return ROOT / rel


def localized(rel: str, lang: str) -> tuple[Path, bool]:
    p = resolve(rel)
    if lang != "en" and p.suffix == ".md":
        alt = p.with_name(f"{p.stem}.{lang}.md")
        if alt.is_file():
            return alt, True
    return p, lang == "en" or p.suffix != ".md"


def rewrite(html_text: str, base_rel: str) -> str:
    base_dir = posixpath.dirname(base_rel)
    docs = set(allowed())

    def rep(m: re.Match) -> str:
        attr, url = m.group(1), html.unescape(m.group(2))
        if re.match(r"^[a-z]+:", url) or url.startswith("#/"):
            return f'{attr}="{html.escape(url)}" target="_blank" rel="noopener"' if url.startswith("http") else m.group(0)
        if url.startswith("#"):
            return f'{attr}="#/docs/{base_rel}{html.escape(url)}"'
        path, _, anchor = url.partition("#")
        target = posixpath.normpath(posixpath.join(base_dir, path)) if path else base_rel
        if target.endswith("/"):
            target += "README.md"
        if target in docs or f"{target}/README.md" in docs:
            target = target if target in docs else f"{target}/README.md"
            return f'{attr}="#/docs/{html.escape(target)}{"#" + html.escape(anchor) if anchor else ""}"'
        return f'{attr}="#" data-missing="{html.escape(target)}"'

    return LINK_RE.sub(rep, html_text)


def render_markdown(text: str, base_rel: str = "") -> str:
    out = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
                            extension_configs={"toc": {"permalink": False}})
    out = re.sub(r"<script\b.*?</script>", "", out, flags=re.S | re.I)
    return rewrite(out, base_rel) if base_rel else out


def render(rel: str, lang: str = "en") -> dict:
    p, translated = localized(rel, lang)
    rel = resolve(rel).relative_to(ROOT).as_posix()
    if p.suffix == ".md":
        body = render_markdown(p.read_text(encoding="utf-8"), rel)
    elif p.suffix == ".sql":
        body = f'<pre class="code sql">{html.escape(p.read_text(encoding="utf-8"))}</pre>'
    else:
        with p.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
        head = "".join(f"<th>{html.escape(c)}</th>" for c in (rows[0] if rows else []))
        body_rows = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
        body = f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body_rows}</tbody></table></div>'
    return {"path": rel, "title": title_of(rel, lang), "html": body, "translated": translated, "kind": p.suffix[1:]}


# ---------------------------------------------------------------- glossary
GLOSSARY_REL = "reference/14_glossary.md"
_TERM_RE = re.compile(r"^###\s+(.+?)\s*\{#([a-z0-9-]+)\}\s*$")


def glossary(lang: str = "en") -> list[dict]:
    """Parse reference/14_glossary[.<lang>].md into [{id, name, aliases, short, body, group}]."""
    p, _ = localized(GLOSSARY_REL, lang)
    terms: list[dict] = []
    group, cur = "", None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            group = line[3:].strip()
            cur = None
            continue
        m = _TERM_RE.match(line)
        if m:
            cur = {"id": m.group(2), "name": m.group(1), "aliases": [], "body": [], "group": group}
            terms.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("*Aliases:") and line.rstrip().endswith("*"):
            cur["aliases"] = [a.strip() for a in line.strip()[len("*Aliases:"):-1].split(",") if a.strip()]
        else:
            cur["body"].append(line)
    for t in terms:
        text = "\n".join(t["body"]).strip()
        t["body"] = text
        t["html"] = render_markdown(text, GLOSSARY_REL) if text else ""
        first = text.split("\n", 1)[0].strip()
        t["short"] = re.sub(r"[`*]", "", first)
    return terms
