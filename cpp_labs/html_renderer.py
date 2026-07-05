"""HTML renderer for the C++ Pointer Lab static build.

Pure functions — no I/O, no compilation. All take plain dicts/lists and return
HTML strings. Tests can call these without invoking g++.
"""

from __future__ import annotations

import html as _html
from typing import Any


# ---------------------------------------------------------------------------
# Semantic per-role color palette — single source of truth (WCAG AA)
# ---------------------------------------------------------------------------
#
# These five role tokens are the one contrast-vetted color language shared by
# prose, code, and the inline SVG diagrams.  Each value is >=4.5:1 against the
# white page background (--bg: #ffffff), so it is safe as a foreground color.
# The same hex values are emitted as `:root` CSS custom properties (--c-<role>)
# *and* used directly in the SVG palette, so a "blue address" in the code is a
# "blue box" in the diagram.  Color is always paired with text/border/icon —
# never the sole signal (WCAG 1.4.1).
SEMANTIC_PALETTE: dict[str, str] = {
    "addr": "#0b5394",   # blue   — addresses / pointer boxes
    "val": "#0b7d3e",    # green  — stored values
    "type": "#6b3fa0",   # purple — type names
    "const": "#9a6700",  # amber  — const / immutable
    "err": "#b00020",    # red    — errors / compile failures
}


# ---------------------------------------------------------------------------
# SVG geometry constants — vertical layout (tall + narrow); box font matches code panel
# ---------------------------------------------------------------------------

_BOX_FILL = "#e8f0ff"
_BOX_STROKE = SEMANTIC_PALETTE["addr"]
_ARROW_COLOR = SEMANTIC_PALETTE["addr"]
_NULL_COLOR = "#8b0000"
_LABEL_COLOR = "#1a1a1a"
_DIM_COLOR = "#555555"
_SHARED_COUNT_COLOR = "#4a7c20"

# Vertical-layout geometry (tall + narrow). Box text is 14px to match the code panel.
_FONT = 14           # px, == code panel font-size (ui-monospace)
_LH = 22             # text line height within a box
_BOX_TOP_PAD = 20    # box top padding to first text baseline
_SVG_TEXT_ASCENDER = 4  # SVG <text> y is the baseline; add this to reach the visual top of glyphs
_PAD = 16            # outer padding / gap between boxes
_SRC_W1 = 160        # source/target box width when a single source
_SRC_W2 = 120        # source box width when two sources sit side-by-side
_ARROW_GAP = 60      # vertical gap reserved for the arrow between rows
_STACK_RM = 34       # right margin channel for >=3 stacked-source arrows
_BOX_GAP = 12  # inter-box vertical gap in the stacked column


def _e(s: Any) -> str:
    """HTML-escape a value; return '?' for None/missing."""
    if s is None:
        return "?"
    return _html.escape(str(s))


# ---------------------------------------------------------------------------
# SVG building helpers
# ---------------------------------------------------------------------------


def _text(x: int, y: int, txt: str, color: str = _LABEL_COLOR, size: int = 14) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" '
        f'font-family="ui-monospace,monospace" fill="{color}">{_e(txt)}</text>'
    )


def _marker_defs(marker_id: str, color: str) -> str:
    """A reusable arrowhead <marker>. `orient="auto-start-reverse"` rotates it to
    the line direction, so vertical / diagonal / curved arrows all get a correct
    head. Fill is fixed per-diagram (one arrow color per diagram)."""
    return (
        f'<defs><marker id="{marker_id}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>'
    )


def _arrow_v(x1: int, y1: int, x2: int, y2: int, color: str, marker_id: str) -> str:
    """A straight arrow from (x1,y1) to (x2,y2) with a marker arrowhead.
    Endpoints are honored as given, so vertical and diagonal arrows are supported."""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="3" marker-end="url(#{marker_id})"/>'
    )


def _vbox(x: int, y: int, w: int, lines: list[tuple[str, str]], stroke: str) -> tuple[str, int]:
    """Draw a rounded box at (x,y) with stacked text `lines` (each a
    (text, color) pair). Height scales with the number of lines. Text is 14px
    monospace to match the code panel. Returns (svg, height)."""
    h = _BOX_TOP_PAD + len(lines) * _LH
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="{_BOX_FILL}" stroke="{stroke}" stroke-width="2"/>'
    ]
    ty = y + _BOX_TOP_PAD + _SVG_TEXT_ASCENDER
    for txt, color in lines:
        parts.append(
            f'<text x="{x + 14}" y="{ty}" font-size="{_FONT}" '
            f'font-family="ui-monospace,monospace" fill="{color}">{_e(txt)}</text>'
        )
        ty += _LH
    return "".join(parts), h


def _stack_svg(p: str, title: str, desc: str,
               sources: list[dict], target: "dict | None",
               *, arrow_color: str = _ARROW_COLOR) -> str:
    """Vertical memory diagram. `sources`/`target` are box specs
    ({"lines": [(text,color)...], "stroke": color}). Encodes the source-count
    rule: <=2 sources sit side-by-side and converge onto the target; >=3 stack
    in a column with arrows routed down the right. `target=None` draws no arrow
    (e.g. weak_ptr)."""
    n = len(sources)
    marker_id = f"{p}-ah"
    body = _marker_defs(marker_id, arrow_color) if target is not None else ""

    if n >= 3:
        # Stacked column; arrows route down a right-side channel into the target.
        ws = _SRC_W1
        x = _PAD
        y = _PAD
        right_edges = []
        for s in sources:
            svg, h = _vbox(x, y, ws, s["lines"], s["stroke"])
            body += svg
            right_edges.append((x + ws, y + h // 2))
            y += h + _BOX_GAP
        chan = x + ws + _STACK_RM // 2
        ty = y - _BOX_GAP + _ARROW_GAP
        tsvg, th = _vbox(x, ty, ws, target["lines"], target["stroke"]) if target else ("", 0)
        body += tsvg
        if target is not None:
            for ex, ey in right_edges:
                body += (
                    f'<path d="M{ex} {ey} H{chan} V{ty + th // 2} H{x + ws}" '
                    f'fill="none" stroke="{arrow_color}" stroke-width="3" '
                    f'marker-end="url(#{marker_id})"/>'
                )
        vb_w = ws + 2 * _PAD + _STACK_RM
        vb_h = ty + th + _PAD if target else y - _BOX_GAP + _PAD
        return _wrap_svg(p, title, desc, body, vb_w=vb_w, vb_h=vb_h)

    # n <= 2: converge. Sources in a top row, target centered below.
    sw = _SRC_W1 if n == 1 else _SRC_W2
    tw = _SRC_W1
    row_w = n * sw + (n - 1) * _PAD
    vb_w = max(row_w + 2 * _PAD, tw + 2 * _PAD)
    start_x = (vb_w - row_w) // 2
    src_y = _PAD
    src_h = 0
    bottoms = []
    for i, s in enumerate(sources):
        bx = start_x + i * (sw + _PAD)
        svg, h = _vbox(bx, src_y, sw, s["lines"], s["stroke"])
        body += svg
        src_h = max(src_h, h)
        bottoms.append((bx + sw // 2, src_y + h))

    if target is None:
        vb_h = src_y + src_h + _PAD
        return _wrap_svg(p, title, desc, body, vb_w=vb_w, vb_h=vb_h)

    tgt_y = src_y + src_h + _ARROW_GAP
    tgt_x = (vb_w - tw) // 2
    tsvg, th = _vbox(tgt_x, tgt_y, tw, target["lines"], target["stroke"])
    body += tsvg
    tip_x = vb_w // 2
    for bx, by in bottoms:
        body += _arrow_v(bx, by, tip_x, tgt_y, arrow_color, marker_id)
    if n == 1:
        _, src_bottom = bottoms[0]
        body += (
            f'<text x="{tip_x + 8}" y="{(src_bottom + tgt_y) // 2}" font-size="13" '
            f'fill="{_DIM_COLOR}">points to</text>'
        )
    vb_h = tgt_y + th + _PAD
    return _wrap_svg(p, title, desc, body, vb_w=vb_w, vb_h=vb_h)


def _wrap_svg(p: str, title_text: str, desc_text: str, body: str,
              *, vb_w: int = 500, vb_h: int = 160) -> str:
    """Wrap *body* in an accessible SVG shell. `p` is the unique id prefix.
    `vb_w`/`vb_h` set the viewBox. `max-width:{vb_w}px; height:auto` keeps the
    diagram at its intrinsic aspect and caps it so 14 user-units ≈ 14px (matching
    the code panel) in the common case, scaling down only on very narrow screens."""
    title_id = f"{p}-title"
    desc_id = f"{p}-desc"
    return (
        f'<svg viewBox="0 0 {vb_w} {vb_h}" role="img" '
        f'aria-labelledby="{title_id} {desc_id}" '
        f'style="width:100%;max-width:{vb_w}px;height:auto;background:#fff;'
        f'border:1px solid #c5cee0;border-radius:8px">'
        f'<title id="{title_id}">{_e(title_text)}</title>'
        f'<desc id="{desc_id}">{_e(desc_text)}</desc>'
        f'{body}'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# Six diagram renderers (port of the six _draw_* methods in app_base.py)
# ---------------------------------------------------------------------------


def _svg_raw(pd: dict, p: str) -> str:
    addr, tgt, val = pd.get("ptr_addr", "?"), pd.get("target_addr", "?"), pd.get("target_val", "?")
    src = {"lines": [("ptr", _LABEL_COLOR), (str(addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "raw pointer diagram",
                      f"ptr at {_e(addr)} → val={_e(val)} at {_e(tgt)}.", [src], dst)


def _svg_null(pd: dict, p: str) -> str:
    addr = pd.get("ptr_addr", "0x0")
    src = {"lines": [("ptr", _LABEL_COLOR), (str(addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    dst = {"lines": [("NULL", _NULL_COLOR)], "stroke": _NULL_COLOR}
    return _stack_svg(p, "null pointer diagram", f"ptr at {_e(addr)} points to NULL.",
                      [src], dst, arrow_color=_NULL_COLOR)


def _svg_ref(pd: dict, p: str) -> str:
    ref_addr, tgt, val = pd.get("ref_addr", "?"), pd.get("target_addr", "?"), pd.get("target_val", "?")
    src = {"lines": [("ref", _LABEL_COLOR), (str(ref_addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "reference diagram",
                      f"ref at {_e(ref_addr)} → val={_e(val)} at {_e(tgt)}.", [src], dst)


def _svg_unique(pd: dict, p: str) -> str:
    ptr_addr, tgt, val = pd.get("ptr_addr", "?"), pd.get("target_addr", "?"), pd.get("val", "?")
    is_null = pd.get("is_null", "0") == "1"
    src = {"lines": [("unique_ptr", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    if is_null:
        dst = {"lines": [("NULL", _NULL_COLOR)], "stroke": _NULL_COLOR}
        return _stack_svg(p, "unique_ptr diagram", f"unique_ptr at {_e(ptr_addr)} → NULL.",
                          [src], dst, arrow_color=_NULL_COLOR)
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "unique_ptr diagram",
                      f"unique_ptr at {_e(ptr_addr)} → val={_e(val)} at {_e(tgt)}.", [src], dst)


def _svg_shared(pd: dict, p: str) -> str:
    ptr_addr, ptr2_addr = pd.get("ptr_addr", "?"), pd.get("ptr2_addr")
    tgt, val, use_count = pd.get("target_addr", "?"), pd.get("val", "?"), pd.get("use_count", "?")
    if ptr2_addr:
        sources = [
            {"lines": [("sp1", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR)], "stroke": _BOX_STROKE},
            {"lines": [("sp2", _LABEL_COLOR), (str(ptr2_addr), _DIM_COLOR)], "stroke": _BOX_STROKE},
        ]
    else:
        sources = [{"lines": [("shared_ptr", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR)],
                    "stroke": _BOX_STROKE}]
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR),
                     (f"use_count={use_count}", _SHARED_COUNT_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "shared_ptr diagram",
                      f"shared_ptr at {_e(ptr_addr)} → val={_e(val)}, use_count={_e(use_count)}.",
                      sources, dst)


def _svg_weak(pd: dict, p: str) -> str:
    ptr_addr, expired, use_count = pd.get("ptr_addr", "?"), pd.get("expired", "?"), pd.get("use_count", "?")
    src = {"lines": [("weak_ptr", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR),
                     (f"expired={expired}", _LABEL_COLOR),
                     (f"use_count={use_count}", _SHARED_COUNT_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "weak_ptr diagram",
                      f"weak_ptr at {_e(ptr_addr)}, expired={_e(expired)}, use_count={_e(use_count)}.",
                      [src], None)


def _svg_unknown(pd: dict, p: str) -> str:
    # No box structure to stack; use _wrap_svg directly with a minimal fallback label.
    ptype = pd.get("type", "?") if pd else "?"
    body = _text(16, 40, f"type={_e(ptype)} — no diagram", _DIM_COLOR, 13)
    return _wrap_svg(p, f"diagram ({_e(ptype)})", "No diagram available.", body,
                     vb_w=220, vb_h=80)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def svg_renderer(ptrdata: dict[str, Any] | None, svg_id: str = "d") -> str:
    """Return an inline SVG string for one pointer-data snapshot.

    *svg_id* is used as a prefix for the ``<title id>`` and ``<desc id>``
    attributes so that multiple SVGs in the same document have unique ids.
    Pass a unique string per variant (e.g. ``f"{topic_id}-v{i}"``).

    Dispatches on ``ptrdata["type"]``.  Missing keys degrade to ``"?"`` rather
    than raising.  Returns an accessible SVG with ``role="img"``,
    ``<title>``, and ``<desc>`` elements.
    """
    if not ptrdata:
        return _svg_unknown({}, svg_id)
    ptr_type = ptrdata.get("type")
    dispatch = {
        "raw": _svg_raw,
        "null": _svg_null,
        "ref": _svg_ref,
        "unique": _svg_unique,
        "shared": _svg_shared,
        "weak": _svg_weak,
    }
    fn = dispatch.get(ptr_type)
    if fn:
        return fn(ptrdata, svg_id)
    return _svg_unknown(ptrdata, svg_id)


# ---------------------------------------------------------------------------
# CSS for the WCAG AA theme (inlined by assemble_page)
# ---------------------------------------------------------------------------

_CSS = """
:root {
  --fg:        #1a1a1a;
  --fg-dim:    #555555;
  --bg:        #ffffff;
  --panel-bg:  #f6f8fc;
  --border:    #4a4a4a;
  --accent:    #0b5394;
  --accent-fg: #ffffff;
  --code-bg:   #1d2433;
  --code-fg:   #e8edf6;
  --ok:        #0a6b2e;
  /*SEMANTIC_TOKENS*/
}
* { box-sizing: border-box; }
body {
  font-size: 16px; line-height: 1.5;
  font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
  color: var(--fg); background: var(--bg);
  margin: 0; padding: 0;
}
/* legacy DPG-style lab shell: lock to viewport, panels scroll internally.
   Document pages (page_shell) opt OUT by not carrying the class. */
body.lab-shell { height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.skip {
  position: absolute; left: -9999px; top: 0;
  background: var(--accent); color: var(--accent-fg);
  padding: .4rem .8rem; z-index: 10; border-radius: 0 0 6px 0;
}
.skip:focus { left: 0; }
header { padding: .5rem 1rem; border-bottom: 3px solid var(--accent); flex-shrink: 0; }
header h1 { margin: 0; font-size: 1.2rem; }
/* topic-nav: zero-JS tab bar using radio + CSS sibling */
.vtopic {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
.topic-nav {
  display: flex; flex-wrap: wrap; gap: .3rem;
  padding: .4rem .8rem; background: var(--panel-bg);
  border-bottom: 2px solid var(--border); flex-shrink: 0;
}
.topic-nav label {
  display: inline-flex; align-items: center;
  min-height: 44px; padding: .3rem .9rem;
  border: 2px solid var(--border); border-radius: 6px;
  background: var(--bg); cursor: pointer;
  font-size: 14px; font-weight: 700;
}
.topic-nav label:hover { background: #e2e9f5; }
/* lab-content fills remaining viewport height */
.lab-content { flex: 1 1 0; overflow: hidden; }
/* all topic panels hidden by default; shown by :checked sibling rule */
.topic-panel { display: none; height: 100%; }
/* topic explanation compact header */
.topic-header { padding: .3rem .8rem; }
.topic-header h2 { font-size: 1rem; margin: 0 0 .2rem; }
.explanation {
  border-left: 4px solid var(--accent); background: var(--panel-bg);
  padding: .4rem .8rem; border-radius: 0 4px 4px 0; font-size: .9rem;
}
/* variant tab controls */
.vradio {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
.tabs { display: flex; gap: .4rem; flex-wrap: wrap; margin-bottom: -1px; padding: .3rem .8rem 0; }
.tabs label {
  display: inline-flex; align-items: center;
  min-height: 44px; min-width: 44px; padding: .4rem .9rem;
  border: 2px solid var(--border); border-bottom: none;
  border-radius: 8px 8px 0 0; background: var(--panel-bg);
  cursor: pointer; font-size: 15px; font-weight: 700; font-family: ui-monospace, monospace;
}
.tabs label:hover { background: #e2e9f5; }
/* panels area fills remaining height in topic-panel */
.panels {
  border: 2px solid var(--border); border-radius: 0 8px 8px 8px;
  background: var(--bg); margin: 0 .8rem;
  flex: 1 1 0; min-height: 0; overflow: hidden;
  display: flex; flex-direction: column;
}
.panel { display: none; flex: 1 1 0; min-height: 0; overflow-y: auto; }
/* multi-case: each stacked sub-case keeps a usable height; .panel scrolls */
.case { margin-bottom: 1rem; }
.case:last-child { margin-bottom: 0; }
.case-label { font-size: 1rem; margin: .2rem 0 .5rem; }
.case .panel-grid { height: auto; }
.case .diagram-col figure { flex: 0 0 auto; min-height: 200px; }
/* panel-grid: left = scrolling code col, right = flex diagram col */
.panel-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;
  height: 100%; padding: .8rem;
}
@media (max-width: 760px) { .panel-grid { grid-template-columns: 1fr; } }
.code-col { overflow-y: auto; }
.diagram-col { display: flex; flex-direction: column; }
h3 { font-size: .95rem; margin: 0 0 .3rem; }
pre {
  background: var(--code-bg); color: var(--code-fg);
  padding: .7rem .9rem; border-radius: 8px;
  /* soft-wrap long lines so the full code is always visible (no horizontal
     scroll); preserves indentation via pre-wrap. */
  white-space: pre-wrap; overflow-wrap: anywhere;
  font: 14px/1.5 ui-monospace, "SF Mono", Menlo, monospace; margin: 0;
}
.out {
  background: var(--panel-bg); border: 1px solid #c5cee0;
  border-radius: 8px; padding: .6rem .9rem;
  font: 14px/1.5 ui-monospace, monospace; white-space: pre-wrap;
}
.out .ok { color: var(--ok); font-weight: 700; }
.out .err { color: #8b0000; font-weight: 700; }
.out--err { border: 2px solid #c20000; background: #fff5f5; }
details { margin-top: .5rem; }
summary { cursor: pointer; font-weight: 600; min-height: 44px; padding: .3rem 0; }
/* per-example Concept: a button-like chip with a rotating caret so it clearly
   reads as pressable. Native details/summary — zero-JS, keyboard + SR. */
details.concept > summary {
  display: inline-flex; align-items: center; gap: .5rem; width: fit-content;
  min-height: 44px; padding: .3rem .9rem;
  border: 2px solid var(--accent); border-radius: 8px;
  background: var(--panel-bg); color: var(--accent); font-weight: 700;
  cursor: pointer; list-style: none;
}
details.concept > summary::-webkit-details-marker { display: none; }
details.concept > summary:hover { background: #e2e9f5; }
details.concept > summary .caret { font-size: .96em; transition: transform .15s ease; }
details.concept[open] > summary .caret { transform: rotate(90deg); }
@media (prefers-reduced-motion: reduce) {
  details.concept > summary .caret { transition: none; }
}
figure { margin: 0; flex: 1 1 0; min-height: 0; display: flex; flex-direction: column; }
figcaption { color: var(--fg-dim); font-size: .85rem; margin-top: .3rem; flex-shrink: 0; }
"""


def _semantic_token_lines() -> str:
    """Render the semantic palette as `:root` custom-property declarations."""
    return "\n  ".join(f"--c-{role}: {hexv};" for role, hexv in SEMANTIC_PALETTE.items())


# Inject the single-source palette into the theme `:root` so the CSS tokens and
# the SVG palette can never drift (both read from SEMANTIC_PALETTE).
_CSS = _CSS.replace("/*SEMANTIC_TOKENS*/", _semantic_token_lines())


def _css_checked_rules(tid: str, variant_ids: list[str]) -> str:
    """Generate the :checked-based tab/panel show rules for one topic."""
    lines = []
    for vid in variant_ids:
        lines.append(
            f'#{vid}:checked ~ .tabs label[for="{vid}"] '
            f'{{ background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }}'
        )
    for vid in variant_ids:
        lines.append(
            f'#{vid}:focus-visible ~ .tabs label[for="{vid}"] '
            f'{{ outline: 3px solid var(--accent); outline-offset: 2px; }}'
        )
    for vid in variant_ids:
        panel_id = f"{tid}-panel-{vid.replace(tid + '-', '', 1)}"
        lines.append(
            f'#{vid}:checked ~ .panels #{panel_id} {{ display: block; }}'
        )
    return "\n".join(lines)


def render_fragment(topic: Any, variants: list[dict[str, Any]]) -> str:
    """Return a self-contained ``<section>`` for *topic* with all *variants*.

    Each variant dict carries ``{"label", "svg", "source", "stdout",
    "membytes", "failed", "stderr"}``.

    When exactly one variant is supplied, no radio controls are emitted.
    Every ``id``, radio ``name``, and CSS selector is namespaced by
    ``topic.id``.  The first variant is ``checked``.
    """
    tid = topic.id
    name = _html.escape(topic.name)
    explanation = _html.escape(topic.explanation)

    if len(variants) == 1:
        return _render_single_variant(tid, name, explanation, variants[0])

    def _vid(i: int, label: str) -> str:
        # Slug must be a valid CSS identifier: ids are referenced in
        # unescaped `#id:checked ~ ...` selectors, where raw '(', ')', ','
        # are parse errors that silently kill the variant-switching rule.
        safe = label.strip().replace("/", "_").replace("*", "ptr")
        safe = "".join(c if (c.isalnum() or c in "_-") else "_" for c in safe)
        return f"{tid}-v{i}-{safe}"

    vids = [_vid(i, v["label"]) for i, v in enumerate(variants)]
    css_rules = _css_checked_rules(tid, vids)

    radios = ""
    for i, (vid, _v) in enumerate(zip(vids, variants)):
        checked = " checked" if i == 0 else ""
        radios += (
            f'<input class="vradio" type="radio" '
            f'name="{tid}-type" id="{vid}"{checked}>\n'
        )

    tab_labels = ""
    for vid, v in zip(vids, variants):
        tab_labels += f'<label for="{vid}">{_html.escape(v["label"])}</label>\n'

    panels = ""
    for i, (vid, v) in enumerate(zip(vids, variants)):
        suffix = vid[len(tid) + 1:]
        panel_id = f"{tid}-panel-{suffix}"
        # Each SVG in the document needs a unique id prefix
        svg_id_prefix = f"{tid}-svg-v{i}"
        panels += (
            f'<section class="panel" id="{panel_id}" '
            f'aria-label="{_html.escape(v["label"])} variant">\n'
            + _panel_body(v, svg_id_prefix)
            + "</section>\n"
        )

    return (
        f'<style>\n{css_rules}\n</style>\n'
        f'<section class="topic" id="{tid}" style="display:flex;flex-direction:column;height:100%">\n'
        f'<div class="topic-header">\n'
        f'<h2>{name}</h2>\n'
        f'<div class="explanation">{explanation}</div>\n'
        f'</div>\n'
        + radios
        + f'<div class="tabs" role="group" aria-label="Choose variant">\n{tab_labels}</div>\n'
        + f'<div class="panels">\n{panels}</div>\n'
        + f'</section>\n'
    )


def _render_single_variant(tid: str, name: str, explanation: str, v: dict) -> str:
    return (
        f'<section class="topic" id="{tid}" style="display:flex;flex-direction:column;height:100%">\n'
        f'<div class="topic-header">\n'
        f'<h2>{name}</h2>\n'
        f'<div class="explanation">{explanation}</div>\n'
        f'</div>\n'
        + _panel_body(v, f"{tid}-svg")
        + f'</section>\n'
    )


def _panel_body(v: dict, svg_id_prefix: str = "d") -> str:
    # Multi-case variant: render each independently-compiled sub-case under
    # its own labelled block, with a unique svg-id prefix per case.
    cases = v.get("cases")
    if cases:
        blocks = ""
        for j, case in enumerate(cases):
            blocks += (
                f'<div class="case">\n'
                f'<h3 class="case-label">{_html.escape(case.get("label", ""))}</h3>\n'
                + _case_block(case, f"{svg_id_prefix}-c{j}")
                + '</div>\n'
            )
        return blocks
    return _case_block(v, svg_id_prefix)


def _case_block(v: dict, svg_id_prefix: str = "d") -> str:
    source = _html.escape(v.get("source", ""))
    stdout = v.get("stdout", "")
    stderr = v.get("stderr", "")
    membytes = v.get("membytes", "n/a")
    failed = v.get("failed", False)

    # Re-render SVG with a unique per-variant prefix to avoid duplicate ids
    # when multiple variants appear in one document.  Fall back to the
    # pre-rendered svg field if ptrdata is not stored.  When there is no
    # pointer data (compile failure, or a topic with no diagram), leave the
    # diagram column empty rather than drawing a "no diagram" placeholder.
    ptrdata = v.get("ptrdata")
    no_diagram = "ptrdata" in v and not ptrdata
    if no_diagram:
        diagram_col = '<div class="diagram-col diagram-col--empty"></div>\n'
    else:
        if "ptrdata" in v:
            svg = svg_renderer(ptrdata, svg_id_prefix)
        else:
            svg = v.get("svg") or svg_renderer(None, svg_id_prefix)
        diagram_col = (
            f'<div class="diagram-col">\n'
            f'<h3>Memory diagram</h3>\n'
            f'<figure>\n'
            f'{svg}\n'
            f'<figcaption>Addresses are real output from a 64-bit build; frozen here for stable study.</figcaption>\n'
            f'</figure>\n'
            f'</div>\n'
        )

    if failed:
        out_html = (
            f'<div class="out out--err">'
            f'<span class="err">Compile failed.</span><br>'
            f'<pre style="margin-top:.5rem"><samp>{_html.escape(stderr)}</samp></pre>'
            f'</div>'
        )
    else:
        out_html = (
            f'<div class="out">'
            f'<span class="ok">Compiled and ran successfully.</span><br>'
            f'{_html.escape(stdout)}'
        )
        if membytes and membytes != "n/a":
            out_html += (
                f'<details><summary>Raw bytes of <code>ptr</code> (8 bytes)</summary>'
                f'<code>{_html.escape(membytes)}</code> &mdash; little-endian'
                f'</details>'
            )
        out_html += '</div>'

    return (
        f'<div class="panel-grid">\n'
        f'<div class="code-col">\n'
        f'<h3>Generated code</h3>\n'
        f'<pre><code>{source}</code></pre>\n'
        f'<h3 style="margin-top:.8rem">Program output</h3>\n'
        f'{out_html}\n'
        f'</div>\n'
        f'{diagram_col}'
        f'</div>\n'
    )


def _topic_nav_css(topics: list[tuple[str, str]]) -> str:
    """Generate per-topic :checked rules for topic-level tab switching."""
    lines = []
    for tid, _name in topics:
        lines.append(
            f'#t-{tid}:checked ~ .topic-nav label[for="t-{tid}"] '
            f'{{ background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }}'
        )
    for tid, _name in topics:
        lines.append(
            f'#t-{tid}:checked ~ .lab-content #tp-{tid} {{ display: flex; flex-direction: column; }}'
        )
    return "\n".join(lines)


def assemble_page(
    fragments: list[str],
    title: str = "C++ Pointer Lab",
    topics: list[tuple[str, str]] | None = None,
) -> str:
    """Wrap *fragments* into a complete WCAG AA HTML document.

    All CSS is inlined.  No external scripts, stylesheets, or network
    resources are referenced.

    *topics* is an optional list of ``(id, name)`` tuples.  When two or more
    entries are supplied, a zero-JS topic-navigation tab bar is generated and
    each fragment is wrapped in a ``<div id="tp-{id}" class="topic-panel">``.
    When ``topics`` is ``None`` or has fewer than 2 entries the output is
    identical to the old single-page layout (backward compatible).
    """
    use_topic_nav = topics is not None and len(topics) >= 2

    if use_topic_nav:
        # Topic radio inputs — first children of <body> so CSS sibling combinator
        # can reach both .topic-nav and .lab-content that follow.
        topic_radios = ""
        for i, (tid, _name) in enumerate(topics):
            checked = " checked" if i == 0 else ""
            topic_radios += (
                f'<input class="vtopic" type="radio" '
                f'name="topic-sel" id="t-{tid}" aria-hidden="true"{checked}>\n'
            )

        nav_labels = ""
        for tid, name in topics:
            nav_labels += f'<label for="t-{tid}">{_html.escape(name)}</label>\n'
        topic_nav = f'<nav class="topic-nav" aria-label="Topics">\n{nav_labels}</nav>\n'

        panel_css = _topic_nav_css(topics)
        extra_style = f'<style>\n{panel_css}\n</style>\n'

        wrapped = ""
        for (tid, _name), frag in zip(topics, fragments):
            wrapped += f'<div id="tp-{tid}" class="topic-panel">\n{frag}\n</div>\n'

        body_open = f'<main class="lab-content" id="main">\n'
        body_close = f'</main>\n'
        body_inner = wrapped
    else:
        topic_radios = ""
        topic_nav = ""
        extra_style = ""
        body_open = f'<main id="main">\n'
        body_close = f'</main>\n'
        body_inner = "\n".join(fragments) + "\n"

    return (
        f'<!DOCTYPE html>\n'
        f'<html lang="en">\n'
        f'<head>\n'
        f'<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_html.escape(title)}</title>\n'
        f'<style>\n{_CSS}\n</style>\n'
        f'{extra_style}'
        f'</head>\n'
        f'<body class="lab-shell">\n'
        f'{topic_radios}'
        f'<a class="skip" href="#main">Skip to lab content</a>\n'
        f'<header>\n'
        f'<h1>{_html.escape(title)}</h1>\n'
        f'</header>\n'
        f'{topic_nav}'
        f'{body_open}'
        f'{body_inner}'
        f'{body_close}'
        f'</body>\n'
        f'</html>\n'
    )
