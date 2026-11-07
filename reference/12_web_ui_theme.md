# Web UI theme (binding for `webapp/static/`)

The audit web interface supports **light** (default tokens in `:root`) and **dark** (`[data-theme="dark"]` in `app.css`). When changing styles, keep the two themes aligned with this reference.

## Dark theme - “true black” (reference palette)

Dark mode follows a **ChatGPT-style** sidebar: pure black canvas, light grey text, charcoal hover/selection. Do not revert to blue-tinted slate backgrounds unless this document is updated.

| Token | Hex | Use |
|-------|-----|-----|
| `--bg`, `--panel` | `#000000` | Page, top bar, cards |
| `--panel-2` | `#212121` | Hover, active nav/sidebar item, muted fills |
| `--border` | `#2f2f2f` | Dividers and inputs (subtle; prefer spacing over heavy borders) |
| `--text` | `#ececec` | Primary copy and default links |
| `--muted` | `#b4b4b4` | Labels, hints, icons |
| `--accent` / `--accent-soft` | `#ececec` / `#212121` | Highlights without a strong brand blue |
| Primary button | `#ffffff` on `#000000` | Main CTA; hover `#e5e5e5` |
| `--radius` | `8px` | List rows, cards, controls (rounded “pill” rows) |
| `--shadow` | `none` | No elevation shadows on dark surfaces |

Semantic status colors (`--ok`, `--warn`, `--bad` and `*-soft` variants) stay green/amber/red but use **dark** soft backgrounds so they read on black.

Scrollbars (WebKit): thin thumb `#3f3f3f` on black track.

## Light theme

Unchanged business-as-usual: light grey page (`#f6f7f9`), white panels, blue accent (`#2563eb`). Only touch light tokens when fixing contrast or accessibility.

## Rules for contributors and agents

1. **Single source of tokens** - dark colors live in `[data-theme="dark"]` in `app.css`; avoid hard-coded hex in `app.js` except transient UI.
2. **Active/hover in dark** - use `var(--panel-2)`, not blue `accent-soft`.
3. **Links in dark** - default link color is `--text`, not blue.
4. **New components** - must look correct in both themes using CSS variables only.
5. **Changing the dark look** - update this file and `app.css` in the same change.

## Where in the interface

The **☀ / ☾** switch in the top-right corner; the choice is stored in `localStorage.theme`.

## Files

| File | Role |
|------|------|
| `webapp/static/app.css` | Theme tokens and layout |
| `webapp/static/app.js` | `data-theme` on `<html>` |
| `webapp/static/index.html` | Early theme read (no flash) |
