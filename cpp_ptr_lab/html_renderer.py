"""HTML renderer for the C++ Pointer Lab static build.

Pure functions — no I/O, no compilation. All take plain dicts/lists and return
HTML strings. Tests can call these without invoking g++.
"""

from __future__ import annotations

import html as _html
from typing import Any


# ---------------------------------------------------------------------------
# SVG constants — mirror the 500×160 DPG coordinate space
# ---------------------------------------------------------------------------

_BOX_FILL = "#e8f0ff"
_BOX_STROKE = "#0b5394"
_ARROW_COLOR = "#0b5394"
_NULL_COLOR = "#8b0000"
_LABEL_COLOR = "#1a1a1a"
_DIM_COLOR = "#555555"
_SHARED_COUNT_COLOR = "#4a7c20"


def _e(s: Any) -> str:
    """HTML-escape a value; return '?' for None/missing."""
    if s is None:
        return "?"
    return _html.escape(str(s))


# ---------------------------------------------------------------------------
# SVG building helpers
# ---------------------------------------------------------------------------


def _rect(x1: int, y1: int, x2: int, y2: int, stroke: str = _BOX_STROKE) -> str:
    w, h = x2 - x1, y2 - y1
    return (
        f'<rect x="{x1}" y="{y1}" width="{w}" height="{h}" rx="8" '
        f'fill="{_BOX_FILL}" stroke="{stroke}" stroke-width="2"/>'
    )


def _text(x: int, y: int, txt: str, color: str = _LABEL_COLOR, size: int = 14) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" '
        f'font-family="ui-monospace,monospace" fill="{color}">{_e(txt)}</text>'
    )


def _arrow(x1: int, y1: int, x2: int, y2: int, color: str = _ARROW_COLOR) -> str:
    tip = x2
    mid_y = y1
    return (
        f'<line x1="{x1}" y1="{mid_y}" x2="{tip - 16}" y2="{mid_y}" '
        f'stroke="{color}" stroke-width="3"/>'
        f'<polygon points="{tip-16},{mid_y-6} {tip},{mid_y} {tip-16},{mid_y+6}" '
        f'fill="{color}"/>'
        f'<text x="{x1 + 6}" y="{mid_y - 6}" font-size="11" fill="{_DIM_COLOR}">points to</text>'
    )


def _wrap_svg(p: str, title_text: str, desc_text: str, body: str) -> str:
    """Wrap *body* in an accessible SVG shell.  ``p`` is the unique id prefix."""
    title_id = f"{p}-title"
    desc_id = f"{p}-desc"
    return (
        f'<svg viewBox="0 0 500 160" role="img" '
        f'aria-labelledby="{title_id} {desc_id}" '
        f'style="width:100%;height:100%;min-height:0;background:#fff;border:1px solid #c5cee0;border-radius:8px">'
        f'<title id="{title_id}">{_e(title_text)}</title>'
        f'<desc id="{desc_id}">{_e(desc_text)}</desc>'
        f'{body}'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# Six diagram renderers (port of the six _draw_* methods in app_base.py)
# ---------------------------------------------------------------------------


def _svg_raw(pd: dict, p: str) -> str:
    addr = pd.get("ptr_addr", "?")
    tgt = pd.get("target_addr", "?")
    val = pd.get("target_val", "?")
    body = (
        _rect(20, 50, 200, 112)
        + _text(34, 75, "ptr", size=16)
        + _text(34, 96, str(addr), _DIM_COLOR, 12)
        + _arrow(200, 81, 312, 81)
        + _rect(312, 50, 482, 112)
        + _text(326, 75, f"val={val}", size=16)
        + _text(326, 96, str(tgt), _DIM_COLOR, 12)
    )
    return _wrap_svg(p, "raw pointer diagram",
                     f"ptr at {_e(addr)} → val={_e(val)} at {_e(tgt)}.", body)


def _svg_null(pd: dict, p: str) -> str:
    addr = pd.get("ptr_addr", "0x0")
    body = (
        _rect(20, 50, 200, 112)
        + _text(34, 75, "ptr", size=16)
        + _text(34, 96, str(addr), _DIM_COLOR, 12)
        + _arrow(200, 81, 312, 81, _NULL_COLOR)
        + _rect(312, 50, 482, 112, stroke=_NULL_COLOR)
        + _text(350, 88, "NULL", _NULL_COLOR, 18)
    )
    return _wrap_svg(p, "null pointer diagram",
                     f"ptr at {_e(addr)} points to NULL.", body)


def _svg_ref(pd: dict, p: str) -> str:
    ref_addr = pd.get("ref_addr", "?")
    tgt = pd.get("target_addr", "?")
    val = pd.get("target_val", "?")
    body = (
        _rect(20, 50, 200, 112)
        + _text(34, 75, "ref", size=16)
        + _text(34, 96, str(ref_addr), _DIM_COLOR, 12)
        + _arrow(200, 81, 312, 81)
        + _rect(312, 50, 482, 112)
        + _text(326, 75, f"val={val}", size=16)
        + _text(326, 96, str(tgt), _DIM_COLOR, 12)
    )
    return _wrap_svg(p, "reference diagram",
                     f"ref at {_e(ref_addr)} → val={_e(val)} at {_e(tgt)}.", body)


def _svg_unique(pd: dict, p: str) -> str:
    ptr_addr = pd.get("ptr_addr", "?")
    tgt = pd.get("target_addr", "?")
    val = pd.get("val", "?")
    is_null = pd.get("is_null", "0") == "1"
    body = (
        _rect(20, 50, 200, 112)
        + _text(34, 75, "unique_ptr", size=14)
        + _text(34, 96, str(ptr_addr), _DIM_COLOR, 12)
    )
    if is_null:
        body += (
            _arrow(200, 81, 312, 81, _NULL_COLOR)
            + _rect(312, 50, 482, 112, stroke=_NULL_COLOR)
            + _text(350, 88, "NULL", _NULL_COLOR, 18)
        )
        desc = f"unique_ptr at {_e(ptr_addr)} → NULL."
    else:
        body += (
            _arrow(200, 81, 312, 81)
            + _rect(312, 50, 482, 112)
            + _text(326, 75, f"val={val}", size=16)
            + _text(326, 96, str(tgt), _DIM_COLOR, 12)
        )
        desc = f"unique_ptr at {_e(ptr_addr)} → val={_e(val)} at {_e(tgt)}."
    return _wrap_svg(p, "unique_ptr diagram", desc, body)


def _svg_shared(pd: dict, p: str) -> str:
    ptr_addr = pd.get("ptr_addr", "?")
    ptr2_addr = pd.get("ptr2_addr")
    tgt = pd.get("target_addr", "?")
    val = pd.get("val", "?")
    use_count = pd.get("use_count", "?")
    body = ""
    if ptr2_addr:
        body += (
            _rect(10, 20, 170, 70)
            + _text(20, 45, "sp1", size=14)
            + _text(20, 62, str(ptr_addr), _DIM_COLOR, 11)
            + _arrow(170, 45, 310, 81)
            + _rect(10, 90, 170, 140)
            + _text(20, 115, "sp2", size=14)
            + _text(20, 132, str(ptr2_addr), _DIM_COLOR, 11)
            + _arrow(170, 115, 310, 81)
        )
    else:
        body += (
            _rect(10, 50, 170, 112)
            + _text(20, 75, "shared_ptr", size=13)
            + _text(20, 95, str(ptr_addr), _DIM_COLOR, 11)
            + _arrow(170, 81, 310, 81)
        )
    body += (
        _rect(310, 50, 480, 112)
        + _text(320, 72, f"val={val}", size=15)
        + _text(320, 90, str(tgt), _DIM_COLOR, 11)
        + _text(320, 108, f"use_count={use_count}", _SHARED_COUNT_COLOR, 11)
    )
    return _wrap_svg(p, "shared_ptr diagram",
                     f"shared_ptr at {_e(ptr_addr)} → val={_e(val)}, use_count={_e(use_count)}.", body)


def _svg_weak(pd: dict, p: str) -> str:
    ptr_addr = pd.get("ptr_addr", "?")
    expired = pd.get("expired", "?")
    use_count = pd.get("use_count", "?")
    body = (
        _rect(10, 30, 490, 130)
        + _text(25, 60, "weak_ptr", size=15)
        + _text(25, 80, str(ptr_addr), _DIM_COLOR, 12)
        + _text(25, 100, f"expired={expired}", _LABEL_COLOR, 13)
        + _text(25, 118, f"use_count={use_count}", _SHARED_COUNT_COLOR, 13)
    )
    return _wrap_svg(p, "weak_ptr diagram",
                     f"weak_ptr at {_e(ptr_addr)}, expired={_e(expired)}, use_count={_e(use_count)}.", body)


def _svg_unknown(pd: dict, p: str) -> str:
    ptype = pd.get("type", "?") if pd else "?"
    return _wrap_svg(p, f"diagram ({_e(ptype)})", "No diagram available.",
                     _text(20, 80, f"type={_e(ptype)} — no diagram", _DIM_COLOR, 13))


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
}
* { box-sizing: border-box; }
body {
  font-size: 16px; line-height: 1.5;
  font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
  color: var(--fg); background: var(--bg);
  margin: 0; padding: 0;
  height: 100vh; overflow: hidden;
  display: flex; flex-direction: column;
}
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
  padding: .7rem .9rem; border-radius: 8px; overflow-x: auto;
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
figure { margin: 0; flex: 1 1 0; min-height: 0; display: flex; flex-direction: column; }
figcaption { color: var(--fg-dim); font-size: .85rem; margin-top: .3rem; flex-shrink: 0; }
"""


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
    # pre-rendered svg field if ptrdata is not stored.
    ptrdata = v.get("ptrdata")
    if "ptrdata" in v:
        svg = svg_renderer(ptrdata, svg_id_prefix)
    else:
        svg = v.get("svg") or svg_renderer(None, svg_id_prefix)

    if failed:
        out_html = (
            f'<div class="out out--err">'
            f'<span class="err">Compile failed.</span><br>'
            f'<pre style="margin-top:.5rem">{_html.escape(stderr)}</pre>'
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
        f'<div class="diagram-col">\n'
        f'<h3>Memory diagram</h3>\n'
        f'<figure>\n'
        f'{svg}\n'
        f'<figcaption>Addresses are real output from a 64-bit build; frozen here for stable study.</figcaption>\n'
        f'</figure>\n'
        f'</div>\n'
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
        f'<body>\n'
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
