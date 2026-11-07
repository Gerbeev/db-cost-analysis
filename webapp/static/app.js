/* Databricks cost audit - single-page UI (no build step). */
"use strict";

const S = {
  lang: localStorage.getItem("lang") || "en",
  theme: document.documentElement.getAttribute("data-theme") || "light",
  meta: null,
  dirty: false,
  lastHash: location.hash,
  skipGuard: false,
  pendingCreate: {},
};

// ---------------------------------------------------------------- helpers
const t = (k) => (I18N[S.lang] && I18N[S.lang][k]) || I18N.en[k] || k;
const L = (o) => (o == null ? "" : typeof o === "string" ? o : o[S.lang] || o.en || "");
const enc = encodeURIComponent;
const AUDIT_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/;

function suggestAuditId() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}-dbx`;
}

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k === "html") el.innerHTML = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "value") el.value = v;
    else if (k === "checked") el.checked = !!v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Tiny inline markdown for action texts: `code`, **bold**, *italic*. Input is escaped first.
function inlineMd(text) {
  const html = esc(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return h("span", { html });
}

// Multi-paragraph text: blank line = new paragraph; lines starting with "- " or "1. " become lists.
function blockMd(text) {
  const box = h("div", { class: "block" });
  for (const para of String(text || "").split(/\n{2,}/)) {
    const lines = para.split("\n").filter((x) => x.trim());
    if (!lines.length) continue;
    if (lines.every((l) => /^\s*(-|\d+\.)\s+/.test(l))) {
      const ordered = /^\s*\d+\./.test(lines[0]);
      box.append(h(ordered ? "ol" : "ul", {}, lines.map((l) => h("li", {}, inlineMd(l.replace(/^\s*(-|\d+\.)\s+/, ""))))));
    } else box.append(h("p", {}, inlineMd(lines.join(" "))));
  }
  return box;
}

// ---------------------------------------------------------------- glossary links
const GL = { lang: null, terms: [], rules: [], re: null };
async function loadGlossary() {
  if (GL.lang === S.lang && GL.re) return GL;
  const terms = await GET(`/api/glossary?lang=${S.lang}`);
  const esc2 = (x) => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const rules = [];
  for (const term of terms) {
    const forms = new Set(term.aliases);
    const base = term.name.replace(/\s*\{#.*$/, "");
    const m = base.match(/^(.*?)\s*\((.+)\)\s*$/);
    const main = m ? m[1] : base;
    if (!/,| and | и | \/ /.test(main)) forms.add(main);
    if (m && !/,| and | и | \/ /.test(m[2]) && m[2].length > 2) forms.add(m[2]);
    for (let f of forms) {
      f = f.trim();
      if (f.length < 2) continue;
      const wild = f.endsWith("~") || f.includes("~");
      const src = f.split("~").map(esc2).join("\\p{L}*");
      const canon = f.replace(/~/g, "");
      const acronym = canon === canon.toUpperCase() && /[A-ZА-Я]/.test(canon) || /\d/.test(canon) && canon.length <= 6;
      rules.push({ term, src, acronym, canon, wild });
    }
  }
  rules.sort((a, b) => b.canon.length - a.canon.length);
  const alt = rules.map((r) => r.src).join("|");
  GL.re = new RegExp(`(?<![\\p{L}\\p{N}_-])(?:${alt})(?![\\p{L}\\p{N}_-])`, "giu");
  GL.rules = rules.map((r) => ({ ...r, re: new RegExp(`^(?:${r.src})$`, "iu") }));
  GL.terms = terms; GL.lang = S.lang;
  return GL;
}

const SKIP_TAGS = new Set(["A", "CODE", "PRE", "H1", "H2", "H3", "H4", "BUTTON", "INPUT", "TEXTAREA", "SELECT", "OPTION", "SCRIPT", "STYLE", "LABEL", "SUMMARY", "KBD"]);
async function linkTerms(root, seen) {
  if (!root) return;
  let g;
  try { g = await loadGlossary(); } catch { return; }
  seen = seen || new Set();
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(n) {
      for (let p = n.parentNode; p && p !== root.parentNode; p = p.parentNode) {
        if (p.nodeType === 1 && (SKIP_TAGS.has(p.tagName) || p.classList.contains("no-terms") || p.classList.contains("side"))) return NodeFilter.FILTER_REJECT;
      }
      return n.nodeValue.trim().length > 1 ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const text = node.nodeValue;
    g.re.lastIndex = 0;
    let last = 0, m, frag = null;
    while ((m = g.re.exec(text))) {
      const rule = g.rules.find((r) => r.re.test(m[0]) && (!r.acronym || m[0] === r.canon || (r.wild && m[0].startsWith(r.canon))));
      if (!rule || seen.has(rule.term.id)) continue;
      seen.add(rule.term.id);
      frag = frag || document.createDocumentFragment();
      frag.append(text.slice(last, m.index));
      frag.append(h("a", { class: "term", href: `#/glossary/${rule.term.id}`, title: rule.term.short }, m[0]));
      last = m.index + m[0].length;
    }
    if (frag) { frag.append(text.slice(last)); node.replaceWith(frag); }
  }
}

async function api(method, url, body, isForm) {
  const opt = { method, headers: { "X-Lang": S.lang } };
  if (body !== undefined) {
    if (isForm) opt.body = body;
    else { opt.body = JSON.stringify(body); opt.headers["Content-Type"] = "application/json"; }
  }
  const r = await fetch(url, opt);
  const ct = r.headers.get("content-type") || "";
  const data = ct.includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error((data && (data.error || data.detail)) ? (typeof (data.error || data.detail) === "string" ? (data.error || data.detail) : JSON.stringify(data.detail)) : `HTTP ${r.status}`);
  return data;
}
const GET = (u) => api("GET", u);
const PUT = (u, b) => api("PUT", u, b);
const POST = (u, b) => api("POST", u, b);

function toast(msg, kind) {
  const el = h("div", { class: `toast ${kind || ""}` }, msg);
  document.getElementById("toasts").append(el);
  setTimeout(() => el.remove(), kind === "bad" ? 9000 : 4000);
}

function fmtSize(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

function copyBtn(getText) {
  return h("button", {
    class: "sm", onclick: async (e) => {
      e.stopPropagation();
      try { await navigator.clipboard.writeText(getText()); toast(t("copied"), "ok"); }
      catch { toast(t("error"), "bad"); }
    },
  }, "⧉ ", t("copy"));
}

function busy(btn, on) {
  if (on) { btn._label = Array.from(btn.childNodes); btn.disabled = true; btn.replaceChildren(h("span", { class: "spin" }), t("running")); }
  else { btn.disabled = false; btn.replaceChildren(...(btn._label || [t("run")])); }
}

function chip(state, label) {
  const tr = I18N[S.lang][`state_${state}`] || I18N.en[`state_${state}`];
  return h("span", { class: `chip ${state}` }, label || tr || state);
}

function loading() { return h("div", { class: "empty" }, h("span", { class: "spin" }), " ", t("loading")); }
function errorBox(e) { return h("div", { class: "card" }, h("div", { class: "result bad" }, `${t("error")}: ${e.message || e}`)); }

const fileHref = (id, p) => `#/a/${enc(id)}/f/${enc(p)}`;
const editHref = (id, p) => `#/a/${enc(id)}/e/${enc(p)}`;
const docHref = (p) => `#/docs/${p}`;

const DEFAULT_AUDIT_KEY = "defaultAuditId";

function getDefaultAuditId() {
  return localStorage.getItem(DEFAULT_AUDIT_KEY) || "";
}

function preferredAuditId(audits) {
  const d = getDefaultAuditId();
  if (d && audits.some((a) => a.id === d)) return d;
  const last = localStorage.getItem("lastAuditId");
  if (last && audits.some((a) => a.id === last)) return last;
  return audits[0]?.id || "";
}

function setDefaultAuditId(id) {
  localStorage.setItem(DEFAULT_AUDIT_KEY, id);
  localStorage.setItem("lastAuditId", id);
  toast(t("default_audit_saved"), "ok");
  renderChrome();
}

function defaultAuditButton(id) {
  const isDefault = getDefaultAuditId() === id;
  return h("button", {
    type: "button", class: `btn ${isDefault ? "on" : ""}`,
    disabled: isDefault,
    title: isDefault ? t("default_audit_active") : t("set_default_audit"),
    onclick: () => { setDefaultAuditId(id); route(true); },
  }, isDefault ? `★ ${t("default_audit")}` : `☆ ${t("set_default_audit")}`);
}

async function deleteAudit(id, { goHome = false } = {}) {
  const msg = t("delete_audit_confirm").replace("<id>", id);
  if (!confirm(msg)) return;
  try {
    await api("DELETE", `/api/audits/${enc(id)}`);
    if (getDefaultAuditId() === id) localStorage.removeItem(DEFAULT_AUDIT_KEY);
    toast(t("audit_deleted"), "ok");
    if (goHome) location.hash = "#/audits";
    else route();
  } catch (e) { toast(e.message, "bad"); }
}

function auditsNavHref() {
  const d = getDefaultAuditId();
  if (d) return `#/a/${enc(d)}`;
  const segs = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  if (segs[0] === "a" && segs[1]) return `#/audits/${enc(segs[1])}`;
  if (segs[0] === "audits" && segs[1] && segs[1] !== "new") return `#/audits/${enc(segs[1])}`;
  return "#/audits";
}

function goAuditTab(e) {
  const target = auditsNavHref();
  if (location.hash === target) {
    e.preventDefault();
    route();
  }
}

function auditCreatePanel() {
  const idIn = h("input", {
    type: "text", placeholder: "2026-11-dbx-growth", value: suggestAuditId(),
    pattern: "[A-Za-z0-9][A-Za-z0-9._-]{1,63}", autocomplete: "off", spellcheck: "false",
  });
  const ws = h("input", { type: "date" }), we = h("input", { type: "date" });
  const createBtn = h("button", {
    class: "primary", onclick: async () => {
      try {
        const id = idIn.value.trim();
        if (!AUDIT_ID_RE.test(id)) { toast(t("audit_id_invalid"), "bad"); idIn.focus(); return; }
        await POST("/api/audits", { id, settings: { window_start: ws.value, window_end: we.value } });
        localStorage.setItem("lastAuditId", id);
        location.hash = `#/a/${enc(id)}/s/00`;
      } catch (e) { toast(e.message, "bad"); }
    },
  }, t("create"));
  const demoBtn = h("button", {
    onclick: async () => {
      const r = await POST("/api/demo");
      localStorage.setItem("lastAuditId", r.id);
      location.hash = `#/a/${enc(r.id)}`;
    },
  }, "▶ ", t("demo"));
  return h("div", { class: "card audit-manage" },
    h("h2", {}, t("audit_manage")),
    h("p", { class: "muted small" }, t("audit_manage_hint")),
    h("div", { class: "form-grid" },
      h("label", { class: "field" }, h("span", {}, `${t("audit_id")} - ${t("audit_id_hint")}`), idIn),
      h("label", { class: "field" }, h("span", {}, `${t("window")} - ${t("start")}`), ws),
      h("label", { class: "field" }, h("span", {}, `${t("window")} - ${t("end_excl")}`), we)),
    h("div", { class: "row", style: "margin-top:12px" }, createBtn, demoBtn));
}

// ---------------------------------------------------------------- chrome
function renderChrome() {
  document.documentElement.lang = S.lang;
  document.getElementById("brand-name").textContent = t("app");
  document.title = t("app");
  const route = location.hash.slice(2).split("/")[0] || "";
  const nav = document.getElementById("nav");
  nav.replaceChildren(
    h("a", { href: "#/docs/README.md", class: route === "docs" || route === "" ? "active" : "" }, t("docs")),
    h("a", {
      href: auditsNavHref(), class: route === "audits" || route === "a" ? "active" : "",
      onclick: goAuditTab,
    }, t("audit_tab")),
    h("a", { href: "#/glossary", class: route === "glossary" ? "active" : "" }, t("glossary")),
    h("a", { href: "#/settings", class: route === "settings" ? "active" : "" }, t("settings")),
  );
  document.querySelectorAll("#lang-switch button").forEach((b) => b.classList.toggle("on", b.dataset.lang === S.lang));
  document.querySelectorAll("#theme-switch button").forEach((b) => {
    b.classList.toggle("on", b.dataset.theme === S.theme);
    b.title = t(`theme_${b.dataset.theme}`);
  });
}

document.querySelectorAll("#lang-switch button").forEach((b) => b.addEventListener("click", () => {
  S.lang = b.dataset.lang; localStorage.setItem("lang", S.lang); route(true);
}));
document.querySelectorAll("#theme-switch button").forEach((b) => b.addEventListener("click", () => {
  S.theme = b.dataset.theme; localStorage.setItem("theme", S.theme);
  document.documentElement.setAttribute("data-theme", S.theme); renderChrome();
}));

window.addEventListener("beforeunload", (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });
window.addEventListener("hashchange", () => {
  if (S.skipGuard) { S.skipGuard = false; return; }
  if (S.dirty && !confirm(t("unsaved") + " - " + t("cancel") + "?")) { S.skipGuard = true; location.hash = S.lastHash; return; }
  S.dirty = false;
  route();
});

// ---------------------------------------------------------------- router
async function route(keepScroll) {
  S.lastHash = location.hash;
  renderChrome();
  const app = document.getElementById("app");
  const raw = location.hash.replace(/^#\/?/, "");
  const y = window.scrollY;
  if (!S.meta) S.meta = await GET("/api/meta");
  let el;
  try {
    const parts = raw.split("/");
    if (parts[0] === "audits") {
      el = await pageAudits(parts[1] ? decodeURIComponent(parts[1]) : "");
    }
    else if (raw === "" || parts[0] === "docs") {
      const docPath = parts[0] === "docs" ? (parts.slice(1).join("/") || "README.md") : "README.md";
      el = await pageDocs(docPath);
    }
    else if (parts[0] === "settings") el = await pageSettings();
    else if (parts[0] === "glossary") el = await pageGlossary(parts[1] || "");
    else if (parts[0] === "a") {
      const id = decodeURIComponent(parts[1] || "");
      if (id) { S.lastAuditId = id; localStorage.setItem("lastAuditId", id); }
      const sub = parts[2] || "";
      const rest = decodeURIComponent(parts.slice(3).join("/"));
      if (sub === "") el = await pageOverview(id);
      else if (sub === "s") el = await pageStep(id, rest);
      else if (sub === "r") el = await pageRegister(id, rest);
      else if (sub === "e") el = await pageEditor(id, rest);
      else if (sub === "f") el = await pageFile(id, rest);
      else if (sub === "files") el = await pageFiles(id);
    }
    if (!el) el = h("div", { class: "page" }, h("div", { class: "empty" }, "404"));
  } catch (e) {
    el = h("div", { class: "page" }, errorBox(e));
  }
  app.replaceChildren(el);
  await linkTerms(app);
  if (keepScroll) window.scrollTo(0, y); else window.scrollTo(0, 0);
  const gt = raw.startsWith("glossary/") ? raw.slice(9) : "";
  if (gt) setTimeout(() => document.getElementById(`t-${gt}`)?.scrollIntoView({ block: "start" }), 30);
}

function auditAllAuditsGroup(audits, currentId, mode, pickerSub) {
  const items = audits.map((a) => {
    const href = mode === "picker" ? `#/audits/${enc(a.id)}` : `#/a/${enc(a.id)}`;
    const on = mode === "picker"
      ? (pickerSub !== "new" && a.id === currentId)
      : a.id === currentId;
    return h("a", {
      class: `item ${on ? "active" : ""}`, href, title: a.id,
    },
    h("span", { class: "grow" },
      getDefaultAuditId() === a.id ? h("span", { class: "muted", title: t("default_audit") }, "★ ") : null,
      h("strong", {}, a.id)),
    a.current ? chip("IN_PROGRESS", a.current) : chip("PASSED", "✓"));
  });
  return h("div", { class: "group" },
    h("div", { class: "label" }, t("audit_picker")),
    ...items,
    h("a", { class: `item ${pickerSub === "new" ? "active" : ""}`, href: "#/audits/new" },
      "+ ", h("span", { class: "grow" }, t("new_audit"))));
}

// ---------------------------------------------------------------- audits (list + picker; create only when empty or #/audits/new)
async function pageAudits(sub) {
  const audits = await GET("/api/audits");
  const def = getDefaultAuditId();
  if (def && !audits.some((a) => a.id === def)) localStorage.removeItem(DEFAULT_AUDIT_KEY);
  if (!sub && audits.length) {
    sub = preferredAuditId(audits);
    const hash = `#/audits/${enc(sub)}`;
    if (location.hash !== hash) {
      history.replaceState(null, "", hash);
      S.lastHash = hash;
    }
  }
  if (!audits.length) {
    return h("div", { class: "page" },
      h("h1", {}, t("audit_tab")),
      h("p", { class: "muted" }, t("audit_manage_empty")),
      auditCreatePanel());
  }
  if (sub === "new") {
    return h("div", { class: "page with-side" },
      h("aside", { class: "side audit-picker" }, auditAllAuditsGroup(audits, null, "picker", "new")),
      h("section", {}, h("h1", {}, t("new_audit")), auditCreatePanel()));
  }
  const selected = audits.find((a) => a.id === sub)?.id || audits[0].id;
  const cur = audits.find((a) => a.id === selected);
  if (!cur) {
    return h("div", { class: "page" }, h("div", { class: "result bad" }, t("error"), ": ", t("no_audits")));
  }
  const list = h("aside", { class: "side audit-picker" }, auditAllAuditsGroup(audits, selected, "picker", sub));
  const detail = h("div", { class: "card audit-detail-card" },
    h("div", { class: "row" }, h("h2", { style: "margin:0" }, cur.id), h("span", { class: "spacer" }),
      cur.current ? chip("IN_PROGRESS", `${t("current_step")} ${cur.current}`) : chip("PASSED", t("all_passed"))),
    h("p", { class: "muted" },
      cur.settings.window_start ? `${cur.settings.window_start} → ${cur.settings.window_end}` : "",
      cur.settings.b_start ? ` · B ${cur.settings.b_start}…  C ${cur.settings.c_start}…` : ""),
    h("div", { class: "bar" }, h("i", { style: `width:${(100 * cur.passed) / cur.total}%` })),
    h("p", { class: "muted small" }, `${cur.passed}/${cur.total} ${t("steps_passed")}`),
    h("div", { class: "row audit-detail-actions" },
      h("a", { class: "btn primary", href: `#/a/${enc(cur.id)}` }, t("open_workspace"), " →"),
      defaultAuditButton(cur.id),
      h("button", {
        type: "button", class: "btn danger",
        onclick: () => deleteAudit(cur.id, { goHome: true }),
      }, "✕ ", t("delete_audit"))),
    h("p", { class: "muted small", style: "margin:10px 0 0" }, t("delete_audit_hint")));
  return h("div", { class: "page with-side" }, list, h("section", {}, h("h1", {}, t("audit_tab")), detail));
}

// ---------------------------------------------------------------- audit shell
function sidebar(id, status, active, audits) {
  const stepLinks = S.meta.steps.map((s) => {
    const st = status.steps.find((x) => x.id === s.id) || { state: "LOCKED" };
    return h("a", { class: `item ${active === `s${s.id}` ? "active" : ""}`, href: `#/a/${enc(id)}/s/${s.id}` },
      h("span", { class: `dot ${st.state}` }), h("span", { class: "num" }, s.id), h("span", { class: "grow" }, L(s.title)),
      st.checks_total ? h("span", { class: "muted small" }, `${st.checks_total - st.checks_open}/${st.checks_total}`) : null);
  });
  const reg = S.meta.registers.map((r) => h("a", { class: `item ${active === `r${r}` ? "active" : ""}`, href: `#/a/${enc(id)}/r/${r}` },
    "▦ ", h("span", { class: "grow" }, r)));
  const docsL = [["scope_record.md", "scope_record.md"], ["09_report_and_controls/findings_report.md", "findings_report.md"],
    ["STATUS.md", "STATUS.md"]].map(([p, n]) => h("a", {
      class: `item ${active === `e${p}` ? "active" : ""}`, href: p === "STATUS.md" ? fileHref(id, p) : editHref(id, p),
    }, "✎ ", h("span", { class: "grow" }, n)));
  const auditList = (audits && audits.length)
    ? auditAllAuditsGroup(audits, id, "workspace", null)
    : h("div", { class: "group" },
      h("a", { class: "item active", href: `#/a/${enc(id)}` }, h("span", { class: "grow" }, h("strong", {}, id))),
      h("a", { class: "item", href: `#/audits/${enc(id)}` }, "☰ ", h("span", { class: "grow" }, t("audit_picker"))));
  return h("aside", { class: "side" },
    auditList,
    h("div", { class: "group" }, h("div", { class: "label" }, t("steps")), stepLinks),
    h("div", { class: "group" }, h("div", { class: "label" }, t("registers")), reg),
    h("div", { class: "group" }, h("div", { class: "label" }, t("documents")), docsL,
      h("a", { class: `item ${active === "files" ? "active" : ""}`, href: `#/a/${enc(id)}/files` }, "🗀 ", h("span", { class: "grow" }, t("all_files")))));
}

async function shell(id, status, active, content) {
  let audits = [];
  try { audits = await GET("/api/audits"); } catch { /* keep working if list fails */ }
  return h("div", { class: "page with-side" }, sidebar(id, status, active, audits), h("section", {}, content));
}

function pipeline(id, status) {
  return h("div", { class: "pipeline" }, status.steps.map((s) => {
    const meta = S.meta.steps.find((m) => m.id === s.id);
    return h("a", { class: s.state, href: `#/a/${enc(id)}/s/${s.id}`, title: L(meta.title) },
      h("span", { class: "n" }, s.id), h("span", { class: "small" }, L(meta.title)));
  }));
}

// ---------------------------------------------------------------- settings (periods) form
function periodsForm(id, settings, onSaved, files) {
  const inp = {};
  const date = (k) => (inp[k] = h("input", { type: "date", value: settings[k] || "" }));
  const pair = (label, a, b) => h("label", { class: "field" }, h("span", {}, label),
    h("div", { class: "period" }, date(a), h("span", { class: "muted" }, "→"), date(b)));
  inp.currency = h("input", { type: "text", value: settings.currency, placeholder: "EUR", maxlength: 3 });
  inp.analyst = h("input", { type: "text", value: settings.analyst });
  const exports_ = (files || []).filter((f) => f.path.startsWith("01_data_quality/exports/") && f.path.endsWith(".csv"));
  inp.primary_export = h("select", {}, h("option", { value: "" }, t("choose_file")),
    exports_.map((f) => h("option", { value: f.path, selected: f.path === settings.primary_export }, f.path)));
  const btn = h("button", {
    class: "primary", onclick: async () => {
      const body = {};
      for (const [k, el] of Object.entries(inp)) body[k] = el.value;
      try { await PUT(`/api/audits/${enc(id)}/settings`, body); toast(t("saved"), "ok"); onSaved && onSaved(); }
      catch (e) { toast(e.message, "bad"); }
    },
  }, t("save"));
  return h("div", {},
    h("div", { class: "form-grid" },
      pair(`${t("window")} (${t("end_excl")})`, "window_start", "window_end"),
      pair(`${t("baseline")} (${t("end_excl")})`, "b_start", "b_end"),
      pair(`${t("comparison")} (${t("end_excl")})`, "c_start", "c_end"),
      pair(`${t("persistence")} (${t("end_excl")})`, "p_start", "p_end"),
      h("label", { class: "field" }, h("span", {}, t("currency")), inp.currency),
      h("label", { class: "field" }, h("span", {}, t("analyst")), inp.analyst),
      files ? h("label", { class: "field wide" }, h("span", {}, t("primary_export")), inp.primary_export) : null),
    h("div", { class: "row", style: "margin-top:12px" }, btn));
}

// ---------------------------------------------------------------- overview
async function pageOverview(id) {
  const [a, files, bridge] = await Promise.all([GET(`/api/audits/${enc(id)}`), GET(`/api/audits/${enc(id)}/files`),
    GET(`/api/audits/${enc(id)}/registers/delta_bridge`)]);
  const total = bridge.rows.find((r) => r[0] === "TOTAL");
  const ix = (c) => bridge.header.indexOf(c);
  const kpi = total && total[ix("delta_per_day")] ? h("div", { class: "card" }, h("dl", { class: "kv" },
    h("dt", {}, t("kpi_delta")), h("dd", {}, h("strong", {}, `${total[ix("delta_per_day")]} ${total[ix("currency")]}`),
      ` (B ${total[ix("cost_per_day_b")]} → C ${total[ix("cost_per_day_c")]})`))) : null;
  const content = h("div", {},
    h("h1", {}, id),
    h("p", { class: "muted" }, a.status.current ? `${t("current_step")}: ${a.status.current}` : t("all_passed"), " · ", t("status_file")),
    pipeline(id, a.status),
    a.status.current ? h("p", {}, h("a", { class: "btn primary", href: `#/a/${enc(id)}/s/${a.status.current}` }, `${t("open_step")} ${a.status.current} →`)) : null,
    kpi,
    h("div", { class: "card" }, h("h2", {}, t("periods")), periodsForm(id, a.settings, () => route(true), files)),
    h("div", { class: "card audit-detail-card" },
      h("h2", {}, t("audit_manage_this")),
      h("p", { class: "muted small" }, t("delete_audit_hint")),
      h("div", { class: "row audit-detail-actions" },
        h("a", { class: "btn", href: `#/audits/${enc(id)}` }, t("audit_picker")),
        defaultAuditButton(id),
        h("button", {
          type: "button", class: "btn danger",
          onclick: () => deleteAudit(id, { goHome: true }),
        }, "✕ ", t("delete_audit")))),
    h("p", { class: "muted small" }, t("workspace_hint")));
  return await shell(id, a.status, "overview", content);
}

// ---------------------------------------------------------------- step page
async function pageStep(id, stepId) {
  const [view, files] = await Promise.all([GET(`/api/audits/${enc(id)}/steps/${stepId}`), GET(`/api/audits/${enc(id)}/files`)]);
  const ctx = { id, stepId, files, view, slots: {} };
  ctx.refresh = async () => {
    const [v, f] = await Promise.all([GET(`/api/audits/${enc(id)}/steps/${stepId}`), GET(`/api/audits/${enc(id)}/files`)]);
    ctx.view = v; ctx.files = f;
    fillStatus(ctx);
  };
  const s = view.step;
  const idx = S.meta.steps.findIndex((x) => x.id === s.id);
  const prev = S.meta.steps[idx - 1], next = S.meta.steps[idx + 1];
  ctx.slots.chip = h("span", {});
  ctx.slots.checks = h("div", {});
  ctx.slots.outputs = h("div", {});
  ctx.slots.auto = h("div", {});
  ctx.slots.files = h("div", {});
  ctx.slots.side = h("div", {});
  const content = h("div", {},
    h("div", { class: "card" },
      h("div", { class: "step-head" }, h("div", { class: "big" }, s.id),
        h("div", { style: "flex:1" }, h("div", { class: "row" }, h("h1", {}, L(s.title)), ctx.slots.chip),
          h("div", { class: "muted" }, L(s.question)))),
      s.plain ? h("div", { class: "plain" },
        h("div", { class: "plain-title" }, "💡 ", t("plain")), blockMd(L(s.plain)),
        s.result ? h("div", { class: "plain-row" }, h("strong", {}, `${t("you_get")}: `), inlineMd(L(s.result))) : null,
        s.tip ? h("div", { class: "plain-row" }, h("strong", {}, `${t("tip")}: `), inlineMd(L(s.tip))) : null) : null,
      h("p", {}, h("strong", {}, `${t("goal")}: `), L(s.goal)),
      h("div", { class: "gate" }, h("strong", {}, `${t("gate")}: `), inlineMd(L(s.gate))),
      s.rules ? h("div", { class: "rules" }, h("strong", {}, `${t("rules")}: `), inlineMd(L(s.rules))) : null,
      h("div", { class: "row small" }, h("span", { class: "muted" }, `${t("step_docs")}:`),
        s.docs.map((d) => h("a", { href: docHref(d) }, d.split("/").slice(-2).join("/"))))),
    h("h2", {}, t("actions")),
    s.actions.filter((a) => a.level !== "optional").map((a) => actionCard(ctx, a)),
    s.actions.some((a) => a.level === "optional")
      ? h("details", { class: "opt-actions" },
        h("summary", {}, `${t("optional_actions")} (${s.actions.filter((a) => a.level === "optional").length})`),
        s.actions.filter((a) => a.level === "optional").map((a) => actionCard(ctx, a))) : null,
    h("h2", {}, t("checks")), h("div", { class: "card" }, ctx.slots.checks),
    h("div", { class: "two" },
      h("div", { class: "card" }, h("h3", {}, t("outputs")), ctx.slots.outputs),
      h("div", { class: "card" }, h("h3", {}, t("auto_checks")), ctx.slots.auto)),
    h("div", { class: "card" }, h("div", { class: "row" }, h("h3", { style: "margin:0" }, t("step_files")), h("span", { class: "spacer" }),
      h("a", { class: "btn sm", href: editHref(id, `${s.folder}/notes.md`) }, "✎ ", t("notes"))), ctx.slots.files),
    h("div", { class: "row" },
      prev ? h("a", { class: "btn", href: `#/a/${enc(id)}/s/${prev.id}` }, `← ${prev.id} ${L(prev.title)}`) : null,
      h("span", { class: "spacer" }),
      next ? h("a", { class: "btn", href: `#/a/${enc(id)}/s/${next.id}` }, `${next.id} ${L(next.title)} →`) : null));
  let audits = [];
  try { audits = await GET("/api/audits"); } catch { /* empty */ }
  ctx.slots.side.replaceChildren(sidebar(ctx.id, view.all, `s${stepId}`, audits));
  const root = h("div", { class: "page with-side" }, ctx.slots.side, h("section", {}, content));
  fillStatus(ctx, audits);
  return root;
}

function fillStatus(ctx, audits = null) {
  const v = ctx.view;
  if (audits) ctx.slots.side.replaceChildren(sidebar(ctx.id, v.all, `s${v.step.id}`, audits));
  else GET("/api/audits").then((list) => {
    ctx.slots.side.replaceChildren(sidebar(ctx.id, v.all, `s${v.step.id}`, list));
  }).catch(() => {});
  ctx.slots.chip.replaceChildren(chip(v.status.state));
  ctx.slots.checks.replaceChildren(checksList(ctx));
  linkTerms(ctx.slots.checks);
  ctx.slots.outputs.replaceChildren(...(v.status.outputs.length ? v.status.outputs.map((o) => h("div", { class: "row small out-row" },
    h("span", { class: `chip ${o.found ? "ok" : o.optional ? "neutral" : "bad"}` }, o.found ? `✓ ${t("found")}` : `✗ ${t("missing")}`),
    h("code", {}, o.pattern), o.optional ? h("span", { class: "muted" }, `(${t("optional")})`) : null)) : [h("div", { class: "muted" }, t("none"))]));
  ctx.slots.auto.replaceChildren(...(v.status.auto.length ? v.status.auto.map((a) => h("div", { class: "row small", style: "align-items:flex-start;flex-wrap:nowrap" },
    chip(a.level), h("span", {}, a.message))) : [h("div", { class: "muted small" }, t("none"))]));
  const mine = ctx.files.filter((f) => f.path.startsWith(`${v.step.folder}/`) && !/\/(CHECKS|notes)\.md$/.test(f.path));
  ctx.slots.files.replaceChildren(filesTable(ctx.id, mine, ctx.refresh));
}

function checksList(ctx) {
  const ru = S.lang === "ru" ? S.meta.check_ru : {};
  return h("div", { class: "checks" }, ctx.view.checks.map((c) => {
    const reasonIn = h("input", { type: "text", value: c.reason, placeholder: t("reason") });
    const reasonRow = h("div", { class: "reason", style: c.state === "-" || c.state === "!" ? "" : "display:none" });
    let pending = c.state;
    const save = async (state) => {
      if ((state === "-" || state === "!") && !reasonIn.value.trim()) {
        pending = state; reasonRow.style.display = ""; reasonIn.focus(); toast(t("reason_required")); return;
      }
      try {
        const r = await PUT(`/api/audits/${enc(ctx.id)}/steps/${ctx.stepId}/checks/${enc(c.id)}`, { state, reason: reasonIn.value });
        ctx.view.checks = r.checks; ctx.view.all = r.status;
        ctx.view.status = r.status.steps.find((x) => x.id === ctx.view.step.id);
        fillStatus(ctx);
      } catch (e) { toast(e.message, "bad"); }
    };
    reasonRow.append(reasonIn, h("button", { class: "sm primary", onclick: () => save(pending) }, t("save")));
    const b = (st, sym, cls, title) => h("button", { class: `${c.state === st ? `on ${cls}` : ""}`, title, onclick: () => save(st), disabled: c.auto || (c.gate && (st === "-" || st === "!")) }, sym);
    return h("div", { class: `ck ${c.gate ? "gate" : ""} ${c.auto ? "auto" : ""}` },
      h("div", { class: "tri" }, b(" ", "○", "", t("check_open")), b("x", "✓", "x", t("check_done")),
        b("-", "-", "na", t("check_na")), b("!", "!", "lim", t("check_lim"))),
      h("div", { class: "cid" }, c.id),
      h("div", {}, inlineMd(ru[c.id] || c.text), c.auto ? h("span", { class: "chip neutral auto-chip", title: t("auto_tick_title") }, t("auto_tick")) : null, c.reason && c.state !== "x" && c.state !== " " ? h("div", { class: "muted small" }, `${t("reason")}: ${c.reason}`) : null, reasonRow));
  }));
}

function filesTable(id, files, onChange) {
  if (!files.length) return h("div", { class: "muted small", style: "padding:8px 0" }, t("no_files"));
  return h("div", { class: "table-wrap", style: "margin-top:8px" }, h("table", {},
    h("thead", {}, h("tr", {}, h("th", {}, t("path")), h("th", {}, t("size")), h("th", {}, t("modified")), h("th", {}, ""))),
    h("tbody", {}, files.map((f) => h("tr", {},
      h("td", {}, h("a", { href: fileHref(id, f.path) }, f.path)),
      h("td", { class: "num" }, fmtSize(f.size)), h("td", { class: "small" }, f.modified.replace("T", " ")),
      h("td", { style: "white-space:nowrap" },
        /\.(md|txt)$/.test(f.path) ? h("a", { class: "btn sm", href: editHref(id, f.path) }, "✎") : null, " ",
        h("a", { class: "btn sm", href: `/api/audits/${enc(id)}/download?path=${enc(f.path)}`, title: t("download") }, "⤓"), " ",
        h("button", {
          class: "sm danger", title: t("delete"), onclick: async () => {
            if (!confirm(t("delete_confirm"))) return;
            try { const r = await api("DELETE", `/api/audits/${enc(id)}/file?path=${enc(f.path)}`); toast(`${t("moved")} ${r.moved_to}`, "ok"); onChange && onChange(); }
            catch (e) { toast(e.message, "bad"); }
          },
        }, "🗑")))))));
}

// ---------------------------------------------------------------- actions
function actionCard(ctx, a) {
  const key = `open:${ctx.id}:${ctx.stepId}:${a.id}`;
  const body = h("div", { class: "ab" });
  const card = h("div", { class: `action ${sessionStorage.getItem(key) ? "" : "collapsed"}` });
  let built = false;
  const build = () => {
    if (built) return;
    built = true;
    const desc = L(a.text);
    if (desc) body.append(h("div", { class: "desc" }, blockMd(desc)));
    if (a.why && L(a.why)) body.append(h("div", { class: "why" }, h("div", { class: "wl" }, t("why")), blockMd(L(a.why))));
    if (a.how && L(a.how)) body.append(h("div", { class: "how" }, h("div", { class: "wl" }, t("how")), blockMd(L(a.how))));
    if (a.docs) body.append(h("div", { class: "row small", style: "margin-bottom:8px" }, a.docs.map((d) => h("a", { href: docHref(d) }, "📖 ", d.split("/").pop()))));
    const fn = { settings: actSettings, edit: actEdit, register: actRegister, upload: actUpload, tool: actForm, calc: actForm, sql: actSql, docs: actDocs }[a.kind];
    if (fn) body.append(fn(ctx, a));
    linkTerms(body);
  };
  const head = h("div", {
    class: "ah no-terms", onclick: () => {
      card.classList.toggle("collapsed");
      if (card.classList.contains("collapsed")) sessionStorage.removeItem(key); else { sessionStorage.setItem(key, "1"); build(); }
    },
  }, h("div", { class: "aid" }, a.id), h("div", { class: "at" }, L(a.title)), h("div", { class: "kind" }, t(`k_${a.kind}`)));
  card.append(head, body);
  if (!card.classList.contains("collapsed")) build();
  return card;
}

function actSettings(ctx) {
  const holder = h("div", {}, loading());
  GET(`/api/audits/${enc(ctx.id)}`).then((a) => holder.replaceChildren(periodsForm(ctx.id, a.settings, ctx.refresh, ctx.files)));
  return holder;
}

function actEdit(ctx, a) {
  return h("div", { class: "row" }, h("button", {
    class: "primary", onclick: () => { if (a.create) S.pendingCreate[a.file] = a.create; location.hash = editHref(ctx.id, a.file); },
  }, "✎ ", t("open_editor")), h("code", {}, a.file));
}

function actRegister(ctx, a) {
  return h("div", { class: "row" }, h("a", { class: "btn primary", href: `#/a/${enc(ctx.id)}/r/${a.register}` }, "▦ ", t("open_register")), h("code", {}, a.register));
}

function actDocs(ctx, a) {
  return h("div", { class: "grid2" }, a.links.map((d) => h("a", { class: "card flat", href: docHref(d) }, "📖 ", d.split("/").pop().replace(".md", ""))));
}

function uploadBox(ctx, opts) {
  const fileIn = h("input", { type: "file", style: "display:none" });
  const nameIn = h("input", { type: "text", value: opts.name || "" });
  const ow = h("input", { type: "checkbox" });
  const ev = h("input", { type: "checkbox", checked: true });
  const zone = h("div", { class: "dropzone", onclick: () => fileIn.click() }, t("upload_drop"));
  let picked = null;
  const pick = (f) => {
    picked = f; zone.textContent = `${f.name} · ${fmtSize(f.size)}`;
    if (!nameIn.value) nameIn.value = f.name;
    else if (nameIn.dataset.auto !== "0") {
      const ext = (f.name.match(/\.[A-Za-z0-9]+$/) || [""])[0];
      if (ext) nameIn.value = nameIn.value.replace(/\.[A-Za-z0-9]+$/, "") + ext;
    }
  };
  nameIn.addEventListener("input", () => (nameIn.dataset.auto = "0"));
  fileIn.addEventListener("change", () => fileIn.files[0] && pick(fileIn.files[0]));
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("over"));
  zone.addEventListener("drop", (e) => { e.preventDefault(); zone.classList.remove("over"); if (e.dataTransfer.files[0]) pick(e.dataTransfer.files[0]); });
  const out = h("div", {});
  const btn = h("button", {
    class: "primary", onclick: async () => {
      if (!picked) { fileIn.click(); return; }
      const fd = new FormData();
      fd.append("file", picked); fd.append("folder", opts.folder); fd.append("name", nameIn.value || picked.name);
      fd.append("overwrite", ow.checked); fd.append("step", ctx.stepId); fd.append("action", opts.action || "");
      fd.append("primary", !!opts.primary); fd.append("evidence", ev.checked);
      busy(btn, true);
      try {
        const r = await api("POST", `/api/audits/${enc(ctx.id)}/upload`, fd, true);
        out.replaceChildren(h("div", { class: "result ok" }, `${t("uploaded")}: `, h("a", { href: fileHref(ctx.id, r.path) }, r.path),
          r.evidence_id ? ` · ${t("evidence")} ${r.evidence_id}` : ""));
        await ctx.refresh();
      } catch (e) { out.replaceChildren(h("div", { class: "result bad" }, e.message)); }
      busy(btn, false); btn.replaceChildren("⤒ ", t("upload"));
    },
  }, "⤒ ", t("upload"));
  return h("div", { class: "stack" }, zone, fileIn,
    h("div", { class: "form-grid" }, h("label", { class: "field wide" }, h("span", {}, `${t("file_name")} → ${opts.folder}/`), nameIn)),
    h("div", { class: "row" }, h("label", { class: "check" }, ow, t("overwrite")), h("label", { class: "check" }, ev, t("evidence_add")),
      h("span", { class: "spacer" }), btn), out);
}

function actUpload(ctx, a) {
  const existing = ctx.files.filter((f) => f.path.startsWith(`${a.folder}/`));
  return h("div", {}, uploadBox(ctx, { folder: a.folder, name: a.name_expanded, primary: a.primary, action: a.id }),
    existing.length ? h("div", { class: "small", style: "margin-top:8px" }, h("span", { class: "muted" }, `${t("existing")}: `),
      existing.map((f) => h("span", {}, h("a", { href: fileHref(ctx.id, f.path) }, f.path.split("/").pop()), "  "))) : null);
}

// -- generic form for tools and calculators
function actForm(ctx, a) {
  const holder = h("div", {}, loading());
  GET(`/api/audits/${enc(ctx.id)}/form?step=${ctx.stepId}&action=${enc(a.id)}`).then((form) => {
    const getters = {};
    const fileWatch = {};
    const fields = form.fields.map((f) => fieldInput(ctx, f, getters, fileWatch));
    const ev = h("input", { type: "checkbox", checked: true });
    const result = h("div", {});
    const btn = h("button", {
      class: "primary", onclick: async () => {
        const values = {};
        for (const [k, g] of Object.entries(getters)) values[k] = g();
        busy(btn, true);
        try {
          const r = await POST(`/api/audits/${enc(ctx.id)}/run`, { step: ctx.stepId, action: a.id, values, evidence: ev.checked });
          result.replaceChildren(resultView(ctx, r));
          await ctx.refresh();
          if (r.open) location.hash = editHref(ctx.id, r.open);
        } catch (e) { result.replaceChildren(h("div", { class: "result bad" }, e.message)); }
        busy(btn, false); btn.replaceChildren("▶ ", t("run"));
      },
    }, "▶ ", t("run"));
    holder.replaceChildren(
      fields.length ? h("div", { class: "form-grid" }, fields) : null,
      h("div", { class: "row", style: "margin-top:12px" },
        form.out ? h("span", { class: "small muted" }, `${t("output")}: `, h("code", {}, form.out)) : null,
        h("span", { class: "spacer" }),
        a.kind === "tool" || ["r6", "size", "r8"].includes(a.calc) ? h("label", { class: "check small" }, ev, t("evidence_add")) : null, btn),
      result);
  }).catch((e) => holder.replaceChildren(h("div", { class: "result bad" }, e.message)));
  return holder;
}

function fieldInput(ctx, f, getters, fileWatch) {
  const label = `${L(f.label)}${f.required ? " *" : ""}`;
  const wrap = (el, wide) => h("label", { class: `field ${wide ? "wide" : ""}` }, h("span", {}, label), el);
  const dis = f.fixed || undefined;
  if (f.type === "file") {
    const opts = ctx.files.filter((x) => !f.ext || f.ext.some((e) => x.path.toLowerCase().endsWith(e)));
    const sel = h("select", { disabled: dis }, h("option", { value: "" }, t("choose_file")),
      opts.map((x) => h("option", { value: x.path, selected: x.path === f.value }, x.path)));
    getters[f.name] = () => sel.value;
    sel.addEventListener("change", () => (fileWatch[f.name] || []).forEach((cb) => cb(sel.value)));
    setTimeout(() => (fileWatch[f.name] || []).forEach((cb) => cb(sel.value)), 0);
    return wrap(sel, true);
  }
  if (f.type === "period") {
    const [s, e] = (f.value || ":").split(":");
    const a = h("input", { type: "date", value: s || "", disabled: dis }), b = h("input", { type: "date", value: e || "", disabled: dis });
    getters[f.name] = () => (a.value && b.value ? `${a.value}:${b.value}` : "");
    return wrap(h("div", { class: "period" }, a, h("span", { class: "muted" }, "→"), b));
  }
  if (f.type === "month") { const i = h("input", { type: "month", value: f.value, disabled: dis }); getters[f.name] = () => i.value; return wrap(i); }
  if (f.type === "lines") { const i = h("textarea", { rows: 2, disabled: dis }); i.value = f.value || ""; getters[f.name] = () => i.value; return wrap(i, true); }
  if (f.type === "bool") {
    const i = h("input", { type: "checkbox", checked: String(f.value) === "true", disabled: dis });
    getters[f.name] = () => (i.checked ? "true" : "false");
    return h("label", { class: "check wide" }, i, L(f.label));
  }
  if (f.type === "select") {
    const i = h("select", { disabled: dis }, f.options.map((o) => h("option", { value: o, selected: o === f.value }, o)));
    getters[f.name] = () => i.value; return wrap(i);
  }
  if (f.type === "columns" || f.type === "column") {
    const box = h("div", { class: f.type === "columns" ? "multi" : "" });
    let current = String(f.value || "").split(",").map((x) => x.trim()).filter(Boolean);
    let single = null;
    const draw = async (path) => {
      if (f.fixed) { box.replaceChildren(h("input", { type: "text", value: f.value, disabled: true })); return; }
      let cols = [];
      if (path) { try { cols = await GET(`/api/audits/${enc(ctx.id)}/headers?path=${enc(path)}`); } catch { cols = []; } }
      if (f.type === "column") {
        single = h("select", {}, h("option", { value: "" }, t("auto_detect")), cols.map((c) => h("option", { value: c, selected: c === f.value }, c)));
        box.replaceChildren(single);
        return;
      }
      if (!cols.length) { const i = h("input", { type: "text", value: current.join(","), oninput: (e) => (current = e.target.value.split(",").map((x) => x.trim()).filter(Boolean)) }); box.replaceChildren(i); return; }
      box.replaceChildren(...cols.map((c) => {
        const cb = h("input", { type: "checkbox", checked: current.includes(c) });
        const lab = h("label", { class: current.includes(c) ? "on" : "" }, cb, c);
        cb.addEventListener("change", () => {
          current = cb.checked ? [...current, c] : current.filter((x) => x !== c);
          lab.classList.toggle("on", cb.checked);
        });
        return lab;
      }));
    };
    getters[f.name] = () => (f.fixed ? f.value : f.type === "column" ? (single ? single.value : "") : current.join(","));
    (fileWatch[f.of] = fileWatch[f.of] || []).push(draw);
    if (f.fixed) draw("");
    return wrap(box, f.type === "columns");
  }
  const type = f.type === "secret" ? "password" : f.type === "int" || f.type === "float" ? "number" : "text";
  const i = h("input", { type, value: f.value, disabled: dis, step: f.type === "float" ? "any" : undefined, autocomplete: f.type === "secret" ? "off" : undefined });
  getters[f.name] = () => i.value;
  return wrap(i, f.type === "text" && /url/i.test(f.name));
}

function resultView(ctx, r) {
  const ok = r.rc === undefined ? r.ok !== false : r.rc === 0;
  const parts = [];
  const msg = r.message || r.summary;
  if (msg) parts.push(h("div", {}, h("strong", {}, msg)));
  if (r.rc !== undefined && r.rc !== 0) parts.push(h("div", {}, `${t("exit_code")} ${r.rc}`));
  if (r.warnings && r.warnings.length) parts.push(h("div", { class: "small" }, h("strong", {}, `${t("warnings")}: `), r.warnings.join(" · ")));
  if (r.text) parts.push(h("div", { class: "row", style: "margin-top:6px" }, copyBtn(() => r.text)), h("pre", {}, r.text));
  if (r.outputs && r.outputs.length) parts.push(h("div", { class: "small" }, `${t("output")}: `,
    r.outputs.slice(0, 20).map((p) => h("span", {}, h("a", { href: p.endsWith(".md") && !p.includes("/results/") ? editHref(ctx.id, p) : fileHref(ctx.id, p) }, p), "  ")),
    r.outputs.length > 20 ? `… +${r.outputs.length - 20}` : ""));
  if (r.evidence_id) parts.push(h("div", { class: "small" }, `${t("evidence")}: `, h("a", { href: `#/a/${enc(ctx.id)}/r/evidence_register` }, r.evidence_id)));
  if (r.stdout || r.stderr) parts.push(h("details", { open: !ok }, h("summary", { class: "small" }, t("log")), h("pre", {}, `${r.stdout || ""}${r.stderr ? `\n${r.stderr}` : ""}`)));
  return h("div", { class: `result ${ok ? "ok" : "bad"}` }, parts);
}

// -- SQL
const PARAM_RE = /(^|[^:\w]):([a-z_][a-z0-9_]*)\b/g;
function inlineSql(sql, params) {
  return sql.split("\n").map((line) => {
    const i = line.indexOf("--");
    const code = i >= 0 ? line.slice(0, i) : line, rest = i >= 0 ? line.slice(i) : "";
    return code.replace(PARAM_RE, (m, pre, name) => (name in params ? `${pre}'${String(params[name]).replace(/'/g, "''")}'` : m)) + rest;
  }).join("\n");
}

function actSql(ctx, a) {
  const holder = h("div", {});
  let file = a.sqls[0];
  const sel = a.sqls.length > 1 ? h("select", {
    onchange: (e) => { file = e.target.value; load(); },
  }, a.sqls.map((f) => h("option", { value: f }, a.sql_titles[f] || f))) : null;
  const body = h("div", {}, loading());
  const load = async () => {
    body.replaceChildren(loading());
    try { body.replaceChildren(sqlBody(ctx, a, await GET(`/api/audits/${enc(ctx.id)}/sql?step=${ctx.stepId}&action=${enc(a.id)}&file=${enc(file)}`))); }
    catch (e) { body.replaceChildren(h("div", { class: "result bad" }, e.message)); }
  };
  holder.append(sel ? h("label", { class: "field" }, h("span", {}, t("sql_query")), sel) : null, body);
  load();
  return holder;
}

function sqlBody(ctx, a, v) {
  let current = 0;
  const params = {};
  v.statements.forEach((st) => Object.assign(params, st.params));
  const ORDER = ["start_date", "end_date", "base_start", "base_end", "cmp_start", "cmp_end"];
  const rank = (k) => (ORDER.includes(k) ? ORDER.indexOf(k) : 99);
  const paramInputs = Object.keys(params).sort((x, y) => rank(x) - rank(y) || x.localeCompare(y)).map((k) => {
    const i = h("input", { type: /_(date|start|end)$/.test(k) ? "date" : "text", value: params[k] });
    i.addEventListener("input", () => { params[k] = i.value; draw(); });
    return h("label", { class: "field" }, h("span", {}, `:${k}`), i);
  });
  const mode = { inline: false };
  const tabs = h("div", { class: "tabs" });
  const code = h("pre", { class: "code sql" });
  const runOut = h("div", {});
  const upSlot = h("div", {});
  const modeSw = h("div", { class: "switch" },
    h("button", { class: "on", onclick: (e) => { mode.inline = false; e.target.classList.add("on"); e.target.nextSibling.classList.remove("on"); draw(); } }, t("sql_with_markers")),
    h("button", { onclick: (e) => { mode.inline = true; e.target.classList.add("on"); e.target.previousSibling.classList.remove("on"); draw(); } }, t("sql_with_values")));
  const ev = h("input", { type: "checkbox", checked: true });
  const runBtn = h("button", {
    class: "primary", disabled: !v.configured, onclick: async () => {
      if (!confirm(t("sql_confirm"))) return;
      busy(runBtn, true);
      try {
        const st = v.statements[current];
        const p = {}; st.sql && Object.keys(st.params).forEach((k) => (p[k] = params[k]));
        const r = await POST(`/api/audits/${enc(ctx.id)}/sql/run`, { step: ctx.stepId, action: a.id, file: v.file, statement: current, params: p, evidence: ev.checked });
        runOut.replaceChildren(h("div", { class: "result ok" }, `${r.rows} ${t("rows")} → `, h("a", { href: fileHref(ctx.id, r.path) }, r.path),
          r.evidence_id ? ` · ${t("evidence")} ${r.evidence_id}` : ""));
        await ctx.refresh();
      } catch (e) { runOut.replaceChildren(h("div", { class: "result bad" }, e.message)); }
      busy(runBtn, false); runBtn.replaceChildren("▶ ", t("sql_run"));
    },
  }, "▶ ", t("sql_run"));
  const draw = () => {
    const st = v.statements[current];
    tabs.replaceChildren(...(v.statements.length > 1 ? v.statements.map((s, i) => h("button", { class: i === current ? "on" : "", onclick: () => { current = i; draw(); } },
      `${t("statement")} ${String.fromCharCode(65 + i)} → ${s.out.split("/").pop().split("__")[0]}`)) : []));
    tabs.style.display = v.statements.length > 1 ? "" : "none";
    code.textContent = mode.inline ? inlineSql(st.sql, params) : st.sql;
    const out = st.out;
    upSlot.replaceChildren(h("h3", {}, t("sql_upload")),
      uploadBox(ctx, { folder: out.slice(0, out.lastIndexOf("/")), name: out.split("/").pop(), action: a.id }));
  };
  draw();
  return h("div", { class: "stack" },
    v.header ? h("details", {}, h("summary", { class: "small muted" }, v.file), h("pre", {}, v.header)) : null,
    paramInputs.length ? h("div", {}, h("div", { class: "small muted", style: "margin-bottom:4px" }, t("sql_params")), h("div", { class: "form-grid" }, paramInputs)) : null,
    tabs,
    h("div", { class: "row" }, modeSw, h("span", { class: "spacer" }), copyBtn(() => code.textContent)),
    code,
    v.configured ? h("div", { class: "row" }, h("label", { class: "check small" }, ev, t("evidence_add")), h("span", { class: "spacer" }), runBtn)
      : h("div", { class: "banner" }, t("sql_not_configured"), " ", h("a", { href: "#/settings" }, t("settings"))),
    runOut, upSlot);
}

// ---------------------------------------------------------------- register editor
async function pageRegister(id, name) {
  const [a, data] = await Promise.all([GET(`/api/audits/${enc(id)}`), GET(`/api/audits/${enc(id)}/registers/${enc(name)}`)]);
  const header = data.header;
  let rows = data.rows.map((r) => [...r]);
  const lists = {
    status: ["HYPOTHESIS", "LIKELY", "CONFIRMED", "REJECTED", "UNKNOWN", "OK", "UNRESOLVED"],
    category: ["TOTAL", "ACCOUNTING", "BUCKET", "DRIVER_CANDIDATE", "ROOT_CAUSE", "SHARED_UNALLOCATED", "OUT_OF_SCOPE", "UNEXPLAINED"],
    bucket: ["DBX_PLATFORM", "DBX_CLASSIC_INFRA", "STORAGE", "NETWORK", "MONITORING", "SHARED_UNALLOCATED", "OUT_OF_SCOPE"],
  };
  const dl = Object.entries(lists).map(([k, vals]) => h("datalist", { id: `dl-${k}` }, vals.map((v) => h("option", { value: v }))));
  const filter = h("input", { type: "text", placeholder: t("filter"), style: "max-width:260px" });
  const dirtyChip = h("span", {});
  const setDirty = (on) => { S.dirty = on; dirtyChip.replaceChildren(on ? chip("WARN", t("unsaved")) : ""); };
  const tbody = h("tbody", {});
  const draw = () => {
    const q = filter.value.trim().toLowerCase();
    tbody.replaceChildren(...rows.map((r, ri) => {
      if (q && !r.join(" ").toLowerCase().includes(q)) return null;
      const tr = h("tr", {}, h("td", { class: "rowno" }, ri + 1));
      header.forEach((col, ci) => {
        const inp = h("input", { type: "text", value: r[ci] ?? "", list: lists[col] ? `dl-${col}` : undefined, title: col });
        inp.addEventListener("input", () => { r[ci] = inp.value; tr.classList.add("dirty"); setDirty(true); });
        tr.append(h("td", {}, inp));
      });
      tr.append(h("td", {}, h("button", { class: "sm ghost danger", title: t("remove_row"), onclick: () => { rows.splice(ri, 1); setDirty(true); draw(); } }, "✕")));
      return tr;
    }).filter(Boolean));
  };
  filter.addEventListener("input", draw);
  const save = async () => {
    try { await PUT(`/api/audits/${enc(id)}/registers/${enc(name)}`, { header, rows }); setDirty(false); toast(t("saved"), "ok"); route(true); }
    catch (e) { toast(e.message, "bad"); }
  };
  draw();
  const content = h("div", {},
    h("div", { class: "row" }, h("h1", {}, name), dirtyChip, h("span", { class: "spacer" }), filter,
      h("button", { onclick: () => { rows.push(header.map(() => "")); setDirty(true); draw(); tbody.lastChild && tbody.lastChild.scrollIntoView({ block: "nearest" }); } }, "+ ", t("add_row")),
      h("button", { class: "primary", onclick: save }, t("save_register"))),
    h("p", { class: "muted small" }, `${rows.length} ${t("rows_total")} · ${t("status_file")}`),
    dl,
    h("div", { class: "table-wrap grid-edit" }, h("table", {},
      h("thead", {}, h("tr", {}, h("th", {}, "#"), header.map((c) => h("th", {}, c)), h("th", {}, ""))), tbody)));
  document.onkeydown = (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "s" && location.hash.includes("/r/")) { e.preventDefault(); save(); } };
  return await shell(id, a.status, `r${name}`, content);
}

// ---------------------------------------------------------------- markdown editor
async function pageEditor(id, path) {
  const create = S.pendingCreate[path] || "";
  delete S.pendingCreate[path];
  const [a, doc] = await Promise.all([GET(`/api/audits/${enc(id)}`),
    GET(`/api/audits/${enc(id)}/text?path=${enc(path)}${create ? `&create=${enc(create)}` : ""}`)]);
  const ta = h("textarea", { spellcheck: "false" });
  ta.value = doc.text;
  const prev = h("div", { class: "md-preview doc", html: doc.html });
  const dirtyChip = h("span", {});
  let timer = null;
  ta.addEventListener("input", () => {
    S.dirty = true; dirtyChip.replaceChildren(chip("WARN", t("unsaved")));
    clearTimeout(timer);
    timer = setTimeout(async () => { try { prev.innerHTML = (await POST("/api/render", { text: ta.value })).html; } catch { /* ignore */ } }, 350);
  });
  const save = async () => {
    try { await PUT(`/api/audits/${enc(id)}/text`, { path, text: ta.value }); S.dirty = false; dirtyChip.replaceChildren(); toast(t("saved"), "ok"); }
    catch (e) { toast(e.message, "bad"); }
  };
  ta.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); save(); } });
  const stepId = path.match(/^(\d\d)_/);
  const content = h("div", {},
    h("div", { class: "row" }, h("h1", {}, path.split("/").pop()), dirtyChip, h("span", { class: "spacer" }),
      stepId ? h("a", { class: "btn", href: `#/a/${enc(id)}/s/${stepId[1]}` }, `← ${t("open_step")} ${stepId[1]}`) : null,
      h("button", { class: "primary", onclick: save }, t("save"), h("span", { class: "muted small", style: "color:inherit;opacity:.7" }, " Ctrl+S"))),
    h("p", { class: "muted small" }, h("code", {}, path)),
    h("div", { class: "editor" }, ta, prev));
  return await shell(id, a.status, `e${path}`, content);
}

// ---------------------------------------------------------------- file preview / files
async function pageFile(id, path) {
  const [a, p] = await Promise.all([GET(`/api/audits/${enc(id)}`), GET(`/api/audits/${enc(id)}/preview?path=${enc(path)}&limit=1000`)]);
  let body;
  if (p.kind === "table") {
    const numeric = p.header.map((_, ci) => p.rows.slice(0, 50).every((r) => r[ci] === "" || !isNaN(Number(r[ci]))));
    body = h("div", {}, h("p", { class: "muted small" }, `${p.rows.length} ${t("rows_shown")} ${p.total}`),
      h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, h("tr", {}, p.header.map((c) => h("th", {}, c)))),
        h("tbody", {}, p.rows.map((r) => h("tr", {}, r.map((c, ci) => h("td", { class: numeric[ci] ? "num" : "" }, c))))))));
  } else if (p.kind === "markdown") body = h("div", { class: "card doc", html: p.html });
  else if (p.kind === "text") body = h("pre", {}, p.text);
  else body = h("div", { class: "empty" }, `${fmtSize(p.size)} - `, h("a", { href: `/api/audits/${enc(id)}/download?path=${enc(path)}` }, t("download")));
  const stepId = path.match(/^(\d\d)_/);
  const content = h("div", {},
    h("div", { class: "row" }, h("h1", { style: "word-break:break-all" }, path.split("/").pop()), h("span", { class: "spacer" }),
      stepId ? h("a", { class: "btn", href: `#/a/${enc(id)}/s/${stepId[1]}` }, `← ${t("open_step")} ${stepId[1]}`) : null,
      /\.(md|txt)$/.test(path) && path !== "STATUS.md" ? h("a", { class: "btn", href: editHref(id, path) }, "✎ ", t("open_editor")) : null,
      h("a", { class: "btn primary", href: `/api/audits/${enc(id)}/download?path=${enc(path)}` }, "⤓ ", t("download"))),
    h("p", { class: "muted small" }, h("code", {}, path)), body);
  return await shell(id, a.status, path === "STATUS.md" ? "eSTATUS.md" : "files", content);
}

async function pageFiles(id) {
  const [a, files] = await Promise.all([GET(`/api/audits/${enc(id)}`), GET(`/api/audits/${enc(id)}/files`)]);
  const filter = h("input", { type: "text", placeholder: t("filter"), style: "max-width:300px" });
  const slot = h("div", {});
  const draw = () => { const q = filter.value.toLowerCase(); slot.replaceChildren(filesTable(id, files.filter((f) => f.path.toLowerCase().includes(q)), () => route(true))); };
  filter.addEventListener("input", draw);
  draw();
  return await shell(id, a.status, "files", h("div", {}, h("div", { class: "row" }, h("h1", {}, t("all_files")), h("span", { class: "spacer" }), filter), slot));
}

// ---------------------------------------------------------------- docs
async function pageDocs(rest) {
  const [path, anchor] = rest.split("#");
  const docPath = path || "README.md";
  const [tree, doc] = await Promise.all([GET(`/api/docs/tree?lang=${S.lang}`), GET(`/api/docs/page?path=${enc(docPath)}&lang=${S.lang}`)]);
  const side = h("aside", { class: "side" }, tree.map((g) => h("div", { class: "group" }, h("div", { class: "label" }, L(g.label)),
    g.items.map((it) => h("a", { class: `item ${it.path === doc.path ? "active" : ""}`, href: docHref(it.path), title: it.path },
      h("span", { class: "grow" }, it.title))))));
  const art = h("article", { class: "card doc", html: doc.html });
  const el = h("div", { class: "page with-side" }, side, h("section", {},
    !doc.translated ? h("div", { class: "banner" }, t("doc_ru_missing")) : null,
    h("div", { class: "muted small", style: "margin-bottom:8px" }, h("code", {}, doc.path)), art));
  if (anchor) setTimeout(() => { const target = document.getElementById(anchor); if (target) target.scrollIntoView(); }, 30);
  return el;
}

// ---------------------------------------------------------------- glossary page
async function pageGlossary(focus) {
  const g = await loadGlossary();
  const box = h("div", { class: "no-terms" });
  const search = h("input", { type: "search", placeholder: t("glossary_search"), class: "gl-search" });
  const draw = () => {
    const q = search.value.trim().toLowerCase();
    const items = g.terms.filter((x) => !q || `${x.name} ${x.aliases.join(" ")} ${x.body}`.toLowerCase().includes(q));
    const groups = [...new Set(items.map((x) => x.group))];
    box.replaceChildren(...(items.length ? groups.map((grp) => h("div", { class: "gl-group" }, h("h2", {}, grp),
      items.filter((x) => x.group === grp).map((x) => h("div", { class: `card gl-term ${x.id === focus ? "focus" : ""}`, id: `t-${x.id}` },
        h("h3", {}, x.name.replace(/\s*\{#.*$/, ""), h("a", { class: "anchor", href: `#/glossary/${x.id}` }, "#")),
        h("div", { class: "doc", html: x.html })))))
      : [h("div", { class: "empty" }, t("glossary_none"))]));
  };
  search.addEventListener("input", () => { focus = ""; draw(); });
  draw();
  const toc = h("aside", { class: "side no-terms" }, [...new Set(g.terms.map((x) => x.group))].map((grp) => h("div", { class: "group" },
    h("div", { class: "label" }, grp), g.terms.filter((x) => x.group === grp).map((x) => h("a", { class: "item", href: `#/glossary/${x.id}` },
      h("span", { class: "grow" }, x.name.replace(/\s*\{#.*$/, "").replace(/\s*\(.*$/, "")))))));
  return h("div", { class: "page with-side" }, toc, h("section", {}, h("h1", {}, t("glossary")), h("p", { class: "muted" }, t("glossary_intro")), search, box));
}

// ---------------------------------------------------------------- settings
async function pageSettings() {
  const c = await GET("/api/settings/databricks");
  const host = h("input", { type: "text", value: c.host, placeholder: "https://adb-1234567890123456.7.azuredatabricks.net" });
  const wh = h("input", { type: "text", value: c.warehouse_id, placeholder: "abcdef1234567890" });
  const auth = h("select", {}, h("option", { value: "pat", selected: c.auth === "pat" }, t("db_pat")),
    h("option", { value: "azure_cli", selected: c.auth === "azure_cli" }, t("db_cli")));
  const tok = h("input", { type: "password", autocomplete: "off", placeholder: c.token_set ? `•••• ${t("db_token_set")}` : "dapi…" });
  const timeout = h("input", { type: "number", value: c.timeout, min: 30, max: 3600 });
  const out = h("div", {});
  const save = async (extra) => {
    try { await PUT("/api/settings/databricks", { host: host.value, warehouse_id: wh.value, auth: auth.value, token: tok.value, timeout: timeout.value, ...extra }); toast(t("saved"), "ok"); route(true); }
    catch (e) { toast(e.message, "bad"); }
  };
  const testBtn = h("button", {
    onclick: async () => {
      busy(testBtn, true);
      try { out.replaceChildren(h("div", { class: "result ok" }, (await POST("/api/settings/databricks/test")).message)); }
      catch (e) { out.replaceChildren(h("div", { class: "result bad" }, e.message)); }
      busy(testBtn, false); testBtn.replaceChildren(t("db_test"));
    },
  }, t("db_test"));
  const stOut = h("div", {});
  const stBtn = h("button", {
    onclick: async () => {
      busy(stBtn, true);
      try { const r = await POST("/api/system/selftest"); stOut.replaceChildren(h("div", { class: `result ${r.rc === 0 ? "ok" : "bad"}` }, `Python ${r.python}`, h("pre", {}, r.output))); }
      catch (e) { stOut.replaceChildren(h("div", { class: "result bad" }, e.message)); }
      busy(stBtn, false); stBtn.replaceChildren(t("selftest_run"));
    },
  }, t("selftest_run"));
  return h("div", { class: "page" }, h("h1", {}, t("settings")),
    h("div", { class: "card" }, h("h2", {}, t("db_title")), h("p", { class: "muted small" }, t("db_hint")),
      h("div", { class: "form-grid" },
        h("label", { class: "field wide" }, h("span", {}, t("db_host")), host),
        h("label", { class: "field" }, h("span", {}, t("db_wh")), wh),
        h("label", { class: "field" }, h("span", {}, t("db_auth")), auth),
        h("label", { class: "field" }, h("span", {}, t("db_token")), tok),
        h("label", { class: "field" }, h("span", {}, t("db_timeout")), timeout)),
      h("div", { class: "row", style: "margin-top:12px" }, h("button", { class: "primary", onclick: () => save({}) }, t("save")), testBtn,
        c.token_set ? h("button", { onclick: () => save({ forget_token: true }) }, t("db_forget")) : null,
        !c.az_available ? h("span", { class: "muted small" }, "az CLI: -") : h("span", { class: "muted small" }, "az CLI: ✓")),
      out),
    h("div", { class: "card" }, h("h2", {}, t("selftest")), stBtn, stOut),
    h("div", { class: "card" }, h("h2", {}, t("about")), h("p", { class: "muted" }, `v${S.meta.version} · `, t("workspace_hint"))));
}

if (!location.hash || location.hash === "#" || location.hash === "#/") {
  location.hash = "#/docs/README.md";
} else {
  route();
}
