"""Interactive, accessible, zero-JS page-element components for the C++ lab.

Each public function in this module is a **pure renderer**: it takes plain data
(dicts/strings/lists) plus a caller-supplied ``comp_id`` and returns a
self-contained HTML-fragment string.  No function performs file, network, or
subprocess I/O, so every component is unit-testable without g++.

Contract (enforced by parametrized invariant tests in test_components.py):

* **Pure** — data in, HTML string out; deterministic; no I/O.
* **Zero-JS / zero-network** — interactivity is CSS only (`:checked`, `:hover`,
  `:focus`, `:target`, `<details>`).  No `<script>`, no external `src`/`href`.
* **id-namespaced** — every emitted ``id``/``name``/``for``/CSS selector is
  prefixed by the sanitised ``comp_id`` and restricted to ``[A-Za-z0-9_-]``, so
  multiple instances coexist in one document without id collision or
  ``:checked ~`` cross-contamination.
* **Color is never alone** — any meaning carried by color is also carried by
  text and a border/icon (WCAG 1.4.1).
* **Focus preserved** — state-driving radios/checkboxes are hidden by
  clip/off-screen, never ``display:none``/``visibility:hidden``.

The semantic color language lives in :data:`html_renderer.SEMANTIC_PALETTE` and
its ``:root`` ``--c-*`` tokens; components reference those tokens, never raw
hex, so chrome and SVG share one contrast-vetted palette.
"""

from __future__ import annotations

import html as _html
from pathlib import Path
from typing import Any, Sequence

from .html_renderer import (
    _CSS,
    SEMANTIC_PALETTE,
    svg_renderer,
    _svg_frames_anatomy,
    _parse_frames,
    _frames_core,
)

# Vendored highlight.js (common bundle incl. C++) + theme, inlined for
# self-contained syntax highlighting. Loaded once at import; opt-in per page.
_VENDOR = Path(__file__).parent / "vendor" / "highlightjs"
_HLJS_JS = (_VENDOR / "highlight.min.js").read_text(encoding="utf-8")
_HLJS_CSS = (_VENDOR / "atom-one-dark.min.css").read_text(encoding="utf-8")
# WCAG AA fix (applied in our layer, not the vendored theme, so a re-fetch keeps it):
# atom-one-dark's comment #5c6370 is only 2.32:1 on its #282c34 bg. #9199a8 is 4.88:1
# and stays muted (dimmer than the #abb2bf code text). Inlined AFTER the theme so it wins.
_HLJS_OVERRIDE_CSS = ".hljs-comment,.hljs-quote{color:#9199a8}"

# Zero-JS "Monochrome" toggle for the highlighted code. A visually-hidden
# checkbox (placed just before <main>) drives a header-row label chip and, when
# checked, forces every highlight.js token span to inherit the base code colour
# — a single-colour ("monochrome") accessible view — without consuming any extra
# vertical space (the chip lives in the existing header row). It does NOT remove
# the SIA-R79 badge in colour mode (the spans stay in the DOM), but it provides
# the accessible monochrome view as a best-practice accommodation.
_MONO_TOGGLE_CSS = (
    ".mono-cb{position:absolute;width:1px;height:1px;overflow:hidden;"
    "clip:rect(0 0 0 0);white-space:nowrap}\n"
    "header{display:flex;align-items:center;justify-content:space-between;"
    "gap:.75rem;flex-wrap:wrap}\n"
    ".mono-toggle{display:inline-flex;align-items:center;min-height:36px;"
    "padding:.15rem .7rem;border:1px solid var(--accent);border-radius:8px;"
    "background:var(--panel-bg);color:var(--accent);font:600 13px system-ui;"
    "cursor:pointer;white-space:nowrap}\n"
    ".mono-cb:focus-visible ~ header .mono-toggle{outline:2px solid var(--accent);"
    "outline-offset:2px}\n"
    ".mono-cb:checked ~ header .mono-toggle{background:var(--accent);color:#fff}\n"
    ".mono-cb:checked ~ main .hljs span{color:inherit !important}\n"
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# Visually hide a state-driving radio/checkbox WITHOUT dropping it from the
# focus order (clip/off-screen, never display:none — WCAG / keyboard).
_VH = (
    "position:absolute;width:1px;height:1px;"
    "overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap"
)

# Human-readable names for the semantic roles (used by the color legend).
_ROLE_NAMES = {
    "addr": "Address",
    "val": "Value",
    "type": "Type",
    "const": "const / immutable",
    "err": "Error",
}


def _safe(s: Any) -> str:
    """Return a CSS-identifier-safe slug of *s* (``[A-Za-z0-9_-]`` only)."""
    return "".join(c if (str(c).isalnum() or c in "_-") else "_" for c in str(s))


def _e(s: Any) -> str:
    """HTML-escape a value for safe text/attribute interpolation."""
    return _html.escape(str(s))


# ---------------------------------------------------------------------------
# 3. Chrome components
# ---------------------------------------------------------------------------

# Extra CSS used by demo pages (page_shell).  No external/network reference.
COMPONENT_CSS = """
.demo-wrap { max-width: 100rem; margin: 0 auto; padding: 1rem 1.2rem; }
.demo-wrap h2 { font-size: 1.1rem; }
.legend { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: .6rem; }
.legend li { display: inline-flex; align-items: center; gap: .4rem;
  border: 1px solid var(--border); border-radius: 6px; padding: .2rem .5rem; }
.swatch { display: inline-block; width: 1rem; height: 1rem; border-radius: 3px;
  border: 1px solid var(--fg); }
.callout { border: 2px solid var(--accent); border-left-width: 6px;
  background: var(--panel-bg); border-radius: 0 6px 6px 0; padding: .5rem .8rem; margin: .6rem 0; }
.callout-label { font-weight: 700; }
.badge { display: inline-flex; align-items: center; gap: .35rem; font-weight: 700;
  border: 2px solid; border-radius: 6px; padding: .15rem .6rem; }
.console { border: 2px solid var(--border); border-radius: 8px; padding: .6rem .9rem;
  font: 14px/1.5 ui-monospace, monospace; white-space: pre-wrap; background: var(--panel-bg); }
.console-label { display: block; font-weight: 700; margin-bottom: .3rem; }
/* long-output disclosure: a caret toggle to reveal the folded overflow lines */
.console-more { margin-top: .4rem; }
.console-more > summary { cursor: pointer; font-weight: 700; min-height: 44px;
  display: inline-flex; align-items: center; gap: .4rem; list-style: none;
  color: var(--accent); }
.console-more > summary::-webkit-details-marker { display: none; }
.console-more > summary .caret { font-size: .9em; transition: transform .15s ease; }
.console-more[open] > summary .caret { transform: rotate(90deg); }
@media (prefers-reduced-motion: reduce) {
  .console-more > summary .caret { transition: none; }
}
.byte-grid { border-collapse: collapse; }
.byte-grid caption { text-align: left; font-weight: 700; margin-bottom: .3rem; }
.byte-grid td, .byte-grid th { border: 1px solid var(--border); padding: .35rem .6rem;
  font: 15px ui-monospace, monospace; text-align: center; }
"""


def page_shell(comp_id: str, body_html: str, *, title: str = "Demo",
               highlight: bool = False) -> str:
    """Wrap *body_html* in a complete, self-contained WCAG AA document.

    Declares ``lang``, exposes a skip link targeting the ``#main`` landmark,
    and inlines all CSS (theme + component styles).  No external/network
    reference is emitted, so the page pastes directly into Canvas.

    When *highlight* is true, the vendored highlight.js library and theme are
    inlined and run on load (``<pre><code class="language-XXX">`` blocks get
    coloured).  Still fully self-contained — nothing external is fetched — and
    it degrades gracefully: with JS off the code shows as plain text.
    """
    t = _e(title)
    hl_style = (f"<style>\n{_HLJS_CSS}\n{_HLJS_OVERRIDE_CSS}\n{_MONO_TOGGLE_CSS}\n</style>\n"
                if highlight else "")
    hl_script = (f"<script>\n{_HLJS_JS}\nhljs.highlightAll();\n</script>\n"
                 if highlight else "")
    # Zero-JS monochrome toggle (only meaningful when the code is highlighted).
    # The checkbox sits just before <main> so `:checked ~ main` reaches the code;
    # its label chip rides in the header row beside the title (no extra height).
    mono_cb = ('<input type="checkbox" class="mono-cb" id="mono-code" '
               'aria-label="Show code in a single colour (accessible monochrome view)">\n'
               if highlight else "")
    mono_label = ('<label for="mono-code" class="mono-toggle" '
                  'title="Show code in a single colour (accessible view)">Monochrome</label>\n'
                  if highlight else "")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{t}</title>\n"
        f"<style>\n{_CSS}\n{COMPONENT_CSS}\n</style>\n"
        f"{hl_style}"
        "</head>\n"
        "<body>\n"
        '<a class="skip" href="#main">Skip to content</a>\n'
        f"{mono_cb}"
        f"<header>\n<h1>{t}</h1>\n{mono_label}</header>\n"
        '<main id="main">\n'
        f'<div class="demo-wrap">\n{body_html}\n</div>\n'
        "</main>\n"
        f"{hl_script}"
        "</body>\n"
        "</html>\n"
    )


def color_legend(comp_id: str) -> str:
    """Document the semantic palette: a colored swatch + text name per role."""
    p = _safe(comp_id)
    items = ""
    for role, name in _ROLE_NAMES.items():
        items += (
            f'<li><span class="swatch" style="background:var(--c-{role});'
            f'border:1px solid var(--fg)"></span> {_e(name)}</li>\n'
        )
    return (
        f'<ul class="legend" id="{p}" aria-label="Color legend">\n{items}</ul>\n'
    )


def callout_note(comp_id: str, text: str, *, label: str = "Note") -> str:
    """A pedagogical aside distinguished by a text label and a border."""
    p = _safe(comp_id)
    return (
        f'<aside class="callout" id="{p}" '
        f'style="border:2px solid var(--accent);border-left-width:6px">\n'
        f'<span class="callout-label">{_e(label)}:</span> {_e(text)}\n'
        f"</aside>\n"
    )


def _prose_box(comp_id: str, body_html: str, *, title: str | None = None,
               css_class: str) -> str:
    """Draw a bordered box with some text inside.

    This is the one shared look for the vocabulary list and the concept boxes,
    so they all match. Give it a title to add a heading at the top of the box
    (screen readers then announce the box by that heading). Leave the title out
    for a plain box with no heading.

    Args:
        comp_id: A short unique name for this box, used to build its HTML ids.
        body_html: The ready-made HTML shown inside the box.
        title: Optional heading at the top of the box; ``None`` means no heading.
        css_class: The style class placed on the box so it can be styled.

    Returns:
        The box as a piece of HTML.
    """
    p = _safe(comp_id)
    if title is not None:
        tid = f"{p}-title"
        head = f'<h2 id="{tid}" style="font-size:1rem;margin:.2rem 0 .4rem">{_e(title)}</h2>\n'
        label_attr = f' aria-labelledby="{tid}"'
    else:
        head = ""
        label_attr = ""
    return (
        f'<section class="{css_class}" id="{p}"{label_attr} '
        f'style="border:2px solid var(--border);border-radius:8px;padding:.6rem .9rem;margin:.6rem 0">\n'
        f"{head}{body_html}\n"
        f"</section>\n"
    )


def glossary(comp_id: str, title: str, terms: Sequence[tuple[str, str]]) -> str:
    """A reusable term/definition list (prose vocabulary), rendered as a <dl>.

    Accessible: the <section> is labelled by its heading via aria-labelledby.
    """
    rows = ""
    for term, definition in terms:
        rows += f"<dt>{_e(term)}</dt><dd>{_e(definition)}</dd>\n"
    return _prose_box(comp_id, f'<dl style="margin:0">\n{rows}</dl>',
                      title=title, css_class="glossary")


def concept_note(comp_id: str, text: str, *, label: str = "Concept",
                 open_: bool = False) -> str:
    """Show one example's Concept as a fold-away note.

    The note starts folded, showing just a "Concept" toggle styled as a
    button-like chip with a ``>`` caret that rotates down when opened, so it
    clearly reads as pressable. Clicking it (or pressing Enter/Space) opens it
    to reveal the text; clicking again folds it back. It works with the keyboard
    and with screen readers (the caret is decorative/``aria-hidden``; the native
    ``<details>`` announces its expanded state), and needs no scripting. Use it
    for the short note that says why one example is here.

    Args:
        comp_id: A short unique name for this note, used to build its HTML ids.
        text: The note's wording, shown once the reader opens it.
        label: The wording of the clickable line; defaults to "Concept".
        open_: Start already open instead of folded. Defaults to folded.

    Returns:
        The fold-away note as a piece of HTML.
    """
    p = _safe(comp_id)
    body = _prose_box(f"{p}-box", f'<p style="margin:0">{_e(text)}</p>', css_class="concept")
    op = " open" if open_ else ""
    return (
        f'<details id="{p}" class="concept"{op} style="margin:.4rem 0">\n'
        f'<summary class="concept-toggle">'
        f'<span class="caret" aria-hidden="true">▸</span>{_e(label)}</summary>\n'
        f"{body}"
        f"</details>\n"
    )


def glossary_note(comp_id: str, terms, *, label: str = "Memory glossary",
                  open_: bool = False) -> str:
    """A per-example glossary as a fold-away chip, matching ``concept_note``.

    Renders the same button-like ``<details class="concept">`` chip (rotating
    caret, keyboard + screen-reader friendly, zero-JS) but its body is a term
    list (``<dl>``) instead of prose. Carries the extra ``chip-inline`` class so
    it can sit on one row beside the Concept chip. ``terms`` is a sequence of
    ``(term, definition)`` pairs."""
    p = _safe(comp_id)
    rows = "".join(f"<dt>{_e(t)}</dt><dd>{_e(d)}</dd>\n" for t, d in terms)
    body = _prose_box(f"{p}-box", f'<dl style="margin:0">\n{rows}</dl>',
                      css_class="concept")
    op = " open" if open_ else ""
    return (
        f'<details id="{p}" class="concept chip-inline"{op} '
        f'style="margin:.4rem 0 .4rem .6rem">\n'
        f'<summary class="concept-toggle">'
        f'<span class="caret" aria-hidden="true">▸</span>{_e(label)}</summary>\n'
        f"{body}"
        f"</details>\n"
    )


def concept_panel(comp_id: str, text: str, *, title: str = "Concept") -> str:
    """Show the whole page's Concept as its own titled panel.

    This is the "what this whole page teaches" note. It appears as an entry in
    the side list (like the Vocabulary entry) and is shown in full whenever it is
    picked — it does not fold away. For the fold-away note that belongs to a
    single example, use ``concept_note`` instead.

    Args:
        comp_id: A short unique name for this panel, used to build its HTML ids.
        text: The Concept wording.
        title: The heading shown at the top of the panel; defaults to "Concept".

    Returns:
        The panel as a piece of HTML.
    """
    return _prose_box(comp_id, f'<p style="margin:0">{_e(text)}</p>',
                      title=title, css_class="concept")


# ---------------------------------------------------------------------------
# 4. memory-diagram
# ---------------------------------------------------------------------------


def memory_diagram(comp_id: str, ptrdata: dict[str, Any] | None) -> str:
    """Render pointer state as an accessible inline SVG.

    Delegates to :func:`html_renderer.svg_renderer`, which emits ``role="img"``
    with a ``<title>``/``<desc>`` (referenced by ``aria-labelledby``) narrated
    from the data; missing keys degrade to ``"?"`` and never raise.  The id is
    sanitised so a punctuated *comp_id* still yields CSS-safe element ids.
    """
    return svg_renderer(ptrdata, _safe(comp_id))


# ---------------------------------------------------------------------------
# 5. High-value interactions
# ---------------------------------------------------------------------------


def hover_link_diagram(comp_id: str, ptrdata: dict[str, Any] | None) -> str:
    """Hovering/focusing the diagram lights the arrow + target (CSS only), on top
    of the shared vertical diagram. Highlight is color *and* thicker stroke (a
    non-color cue); the figure is focusable so keyboard users get the same effect."""
    p = _safe(comp_id)
    svg = svg_renderer(ptrdata, p)          # the shared vertical diagram
    style = (
        f"#{p} {{ cursor: pointer; }}\n"
        f"#{p}:focus:not(:focus-visible) {{ outline: none; }}\n"
        f"#{p}:hover line, #{p}:focus line,"
        f"#{p}:hover path, #{p}:focus path"
        " { stroke: var(--c-val); stroke-width: 5; }"
    )
    return (
        f'<figure id="{p}" tabindex="0" '
        f'aria-label="pointer diagram — hover or focus to highlight the arrow" '
        f'style="margin:0">\n'
        f'<style>\n{style}\n</style>\n{svg}\n</figure>\n'
    )


def before_after_toggle(
    comp_id: str,
    before_svg: str,
    after_svg: str,
    *,
    labels: tuple[str, str] = ("Before", "After"),
    caption: str = "",
) -> str:
    """Switch one diagram between two pre-baked states via a 2-option radio."""
    p = _safe(comp_id)
    bid, aid = f"{p}-before", f"{p}-after"
    style = (
        f"#{p} .ba-state {{ display: none; }}\n"
        f"#{bid}:checked ~ .ba-stage .ba-before {{ display: block; }}\n"
        f"#{aid}:checked ~ .ba-stage .ba-after {{ display: block; }}\n"
        f"#{bid}:checked ~ .ba-tabs label[for=\"{bid}\"],"
        f"#{aid}:checked ~ .ba-tabs label[for=\"{aid}\"]"
        " { background: var(--accent); color: var(--accent-fg); }\n"
        f"#{p} .ba-tabs label {{ border:2px solid var(--border); border-radius:6px;"
        " padding:.3rem .8rem; min-height:44px; display:inline-flex; align-items:center;"
        " cursor:pointer; font-weight:700; }\n"
        f"#{bid}:focus-visible ~ .ba-tabs label[for=\"{bid}\"],"
        f"#{aid}:focus-visible ~ .ba-tabs label[for=\"{aid}\"]"
        " { outline: 3px solid var(--accent); outline-offset: 2px; }"
    )
    cap = f"<figcaption>{_e(caption)}</figcaption>\n" if caption else ""
    return (
        f'<figure id="{p}" style="margin:0">\n<style>\n{style}\n</style>\n'
        f'<input type="radio" name="{p}-ba" id="{bid}" style="{_VH}" checked>\n'
        f'<input type="radio" name="{p}-ba" id="{aid}" style="{_VH}">\n'
        f'<div class="ba-tabs" role="group" aria-label="Choose state">'
        f'<label for="{bid}">{_e(labels[0])}</label>'
        f'<label for="{aid}">{_e(labels[1])}</label></div>\n'
        f'<div class="ba-stage">\n'
        f'<div class="ba-state ba-before">{before_svg}</div>\n'
        f'<div class="ba-state ba-after">{after_svg}</div>\n'
        f"</div>\n{cap}</figure>\n"
    )


def predict_reveal_quiz(
    comp_id: str,
    question: str,
    options: Sequence[str],
    correct_index: int,
    *,
    explanation: str = "",
) -> str:
    """Radio answers reveal baked correct/incorrect feedback via ``:checked``.

    Correctness is signalled by text + an icon (✓/✗) in addition to color, and
    the real answer/explanation is baked in.
    """
    p = _safe(comp_id)
    style_lines = [f"#{p} .qfb {{ display: none; }}"]
    inputs, labels, feedback = "", "", ""
    for i, opt in enumerate(options):
        oid = f"{p}-opt{i}"
        correct = i == correct_index
        style_lines.append(f"#{oid}:checked ~ .qfb-wrap .qfb-{i} {{ display: block; }}")
        inputs += f'<input type="radio" name="{p}-q" id="{oid}" style="{_VH}">\n'
        labels += (
            f'<label for="{oid}" style="display:block;border:2px solid var(--border);'
            f'border-radius:6px;padding:.4rem .7rem;margin:.25rem 0;min-height:44px;'
            f'cursor:pointer">{_e(opt)}</label>\n'
        )
        if correct:
            feedback += (
                f'<p class="qfb qfb-{i}" style="border:2px solid var(--c-val);'
                f'border-radius:6px;padding:.4rem .7rem;color:var(--c-val)">'
                f'✓ Correct. {_e(explanation)}</p>\n'
            )
        else:
            feedback += (
                f'<p class="qfb qfb-{i}" style="border:2px solid var(--c-err);'
                f'border-radius:6px;padding:.4rem .7rem;color:var(--c-err)">'
                f'✗ Not quite — try again. (Answer: {_e(explanation)})</p>\n'
            )
    style = "\n".join(style_lines)
    return (
        f'<fieldset id="{p}" style="border:2px solid var(--border);border-radius:8px;padding:.6rem .8rem">\n'
        f"<style>\n{style}\n</style>\n"
        f"<legend>{_e(question)}</legend>\n"
        f"{inputs}{labels}"
        f'<div class="qfb-wrap">\n{feedback}</div>\n'
        f"</fieldset>\n"
    )


# ---------------------------------------------------------------------------
# 6. Output + status
# ---------------------------------------------------------------------------


def compile_status_badge(comp_id: str, ok: bool, *, label: str | None = None,
                         kind: str = "compile") -> str:
    """Build/run verdict shown by text + icon + border in addition to colour.

    ``kind`` distinguishes the two ways a program can fail so they never look
    alike: ``"compile"`` (red ``✗ Compile failed``) versus ``"runtime"`` (amber
    ``⚠ Runtime error`` — the program compiled but crashed). Ignored when *ok*.
    """
    p = _safe(comp_id)
    if ok:
        icon, txt, color = "✓", label or "Compiled", "var(--c-val)"
    elif kind == "runtime":
        icon, txt, color = "⚠", label or "Runtime error", "var(--c-const)"
    else:
        icon, txt, color = "✗", label or "Compile failed", "var(--c-err)"
    return (
        f'<span class="badge" id="{p}" '
        f'style="border:2px solid {color};color:{color}">'
        f"{icon} {_e(txt)}</span>"
    )


_OUTPUT_LINE_LIMIT = 12  # long output beyond this many lines folds into <details>


def _samp_pre(text: str) -> str:
    """Wrap sample output as a semantic ``<pre><samp>`` (never a bare ``<pre>``)."""
    return (f'<pre style="margin:0;background:none;color:inherit;padding:0">'
            f"<samp>{_e(text)}</samp></pre>")


def output_console(comp_id: str, text: str, *, error: bool = False,
                   title: str | None = None, kind: str = "compile") -> str:
    """Monospaced output block; the error variant is marked by text + border.

    On an error, ``kind`` picks the failure styling so a compile error and a
    runtime crash are unmistakably different: ``"compile"`` (red border,
    *Compiler error*) versus ``"runtime"`` (amber border, *Runtime error*).

    Very long output (compiler template/STL walls, ASan reports) is shortened:
    the first :data:`_OUTPUT_LINE_LIMIT` lines show inline and the remainder
    folds into a native ``<details>`` disclosure, keeping the panel readable.
    """
    p = _safe(comp_id)
    if error and kind == "runtime":
        heading = title or "Runtime error"
        border = "var(--c-const)"
        cls = "console console--runtime"
    elif error:
        heading = title or "Compiler error"
        border = "var(--c-err)"
        cls = "console console--err"
    else:
        heading = title or "Program output"
        border = "var(--border)"
        cls = "console"

    lines = text.split("\n")
    if len(lines) > _OUTPUT_LINE_LIMIT:
        head = "\n".join(lines[:_OUTPUT_LINE_LIMIT])
        rest = "\n".join(lines[_OUTPUT_LINE_LIMIT:])
        more = len(lines) - _OUTPUT_LINE_LIMIT
        body = (
            _samp_pre(head)
            + f'<details class="console-more"><summary>'
            + f'<span class="caret" aria-hidden="true">▸</span>'
            + f"Show {more} more line{'s' if more != 1 else ''}</summary>\n"
            + _samp_pre(rest)
            + "</details>\n"
        )
    else:
        body = _samp_pre(text)

    return (
        f'<div class="{cls}" id="{p}" style="border:2px solid {border}">'
        f'<span class="console-label">{_e(heading)}</span>'
        f"{body}"
        f"</div>\n"
    )


# ---------------------------------------------------------------------------
# 7. Secondary diagram interactions
# ---------------------------------------------------------------------------


def byte_grid(comp_id: str, byte_values: Sequence[str], *, caption: str = "Memory bytes") -> str:
    """Render a byte sequence as a labelled, captioned grid (little-endian)."""
    p = _safe(comp_id)
    index_row = "".join(f'<th scope="col">{i}</th>' for i in range(len(byte_values)))
    value_row = "".join(f'<td class="byte-cell">{_e(b)}</td>' for b in byte_values)
    return (
        f'<table class="byte-grid" id="{p}">\n'
        f"<caption>{_e(caption)}</caption>\n"
        f'<thead><tr><th scope="row">byte</th>{index_row}</tr></thead>\n'
        f'<tbody><tr><th scope="row">value</th>{value_row}</tr></tbody>\n'
        f"</table>\n"
    )


def code_line_link(
    comp_id: str,
    lines: Sequence[tuple[str, str | None]],
    ptrdata: dict[str, Any] | None = None,
) -> str:
    """Hovering/focusing a linked source line highlights its diagram box.

    Each linked line and its diagram box share a ``comp_id``-namespaced class so
    a CSS ``:hover``/``:focus`` rule connects them — no JavaScript.
    """
    pd = ptrdata or {}
    p = _safe(comp_id)
    keys = sorted({k for _c, k in lines if k})

    # The highlight uses the general-sibling combinator (`~`), so the linked
    # source line and the diagram box MUST be siblings under #{p}.  Lines are
    # therefore emitted as direct children of the container (not wrapped in a
    # <pre>, which would trap them one level down and break the rule); a shared
    # background makes the consecutive lines read as one code block.
    style_lines = [
        f"#{p} .cll-line {{ display:block; margin:0; padding:.1rem .7rem;"
        " font:14px/1.6 ui-monospace,monospace;"
        " background:var(--code-bg); color:var(--code-fg); }",
        f"#{p} .cll-line:first-of-type {{ border-radius:8px 8px 0 0; padding-top:.5rem; }}",
        f"#{p} .cll-line:last-of-type {{ border-radius:0 0 8px 8px; padding-bottom:.5rem; }}",
        f"#{p} .cll-link {{ cursor:pointer; text-decoration:underline dotted; }}",
        f"#{p} .cll-diagram {{ margin-top:.6rem; }}",
    ]
    for k in keys:
        sk = _safe(k)
        style_lines.append(
            f"#{p} .ln-{sk}:hover ~ .cll-diagram .bx-{sk},"
            f"#{p} .ln-{sk}:focus ~ .cll-diagram .bx-{sk}"
            " { outline: 3px solid var(--c-val); background: #e8f7ee; }"
        )
    style = "\n".join(style_lines)

    code_lines = ""
    for code, k in lines:
        if k:
            sk = _safe(k)
            code_lines += (
                f'<code class="cll-line cll-link ln-{sk}" tabindex="0">{_e(code)}</code>\n'
            )
        else:
            code_lines += f'<code class="cll-line">{_e(code)}</code>\n'

    boxes = ""
    for k in keys:
        sk = _safe(k)
        boxes += (
            f'<span class="bx bx-{sk}" '
            f'style="display:inline-block;border:1px solid var(--c-addr);'
            f'border-radius:6px;padding:.2rem .5rem;margin:.2rem">'
            f'{_e(k)} → {_e(pd.get("target_val", "?"))}</span>\n'
        )

    return (
        f'<div id="{p}" style="display:flex;flex-direction:column">\n'
        f"<style>\n{style}\n</style>\n"
        f"{code_lines}"
        f'<div class="cll-diagram">{boxes}</div>\n'
        f"</div>\n"
    )


# ---------------------------------------------------------------------------
# 8. Layout + stepped
# ---------------------------------------------------------------------------


def variant_tabs(comp_id: str, panels: Sequence[tuple[str, str]], *, selected: int = 0) -> str:
    """Switch between N labelled panels with native radios + ``:checked ~``.

    A single panel has nothing to switch between, so the tab strip is noise:
    render just its body in the same bordered container, with no radios/labels.
    """
    p = _safe(comp_id)
    if len(panels) == 1:
        _, body = panels[0]
        return (
            f'<div id="{p}">\n'
            f'<div class="vt-panels-{p}" style="border:2px solid var(--border);'
            f'border-radius:8px;padding:.7rem">\n{body}</div>\n'
            f"</div>\n"
        )
    style_lines = [f"#{p} .vt-panel-{p} {{ display: none; }}"]
    inputs, tabs, panel_html = "", "", ""
    for i, (label, body) in enumerate(panels):
        tid = f"{p}-t{i}"
        checked = " checked" if i == selected else ""
        style_lines.append(f"#{tid}:checked ~ .vt-panels-{p} .vt-p{i}-{p} {{ display: block; }}")
        style_lines.append(
            f'#{tid}:checked ~ .vt-tabs-{p} label[for="{tid}"]'
            " { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }")
        style_lines.append(
            f'#{tid}:focus-visible ~ .vt-tabs-{p} label[for="{tid}"]'
            " { outline: 3px solid var(--accent); outline-offset: 2px; }")
        inputs += f'<input type="radio" name="{p}-vt" id="{tid}" style="{_VH}"{checked}>\n'
        tabs += (
            f'<label for="{tid}" style="border:2px solid var(--border);border-radius:8px 8px 0 0;'
            f'padding:.4rem .9rem;min-height:44px;display:inline-flex;align-items:center;'
            f'cursor:pointer;font-weight:700">{_e(label)}</label>\n')
        panel_html += f'<div class="vt-panel-{p} vt-p{i}-{p}">{body}</div>\n'
    style = "\n".join(style_lines)
    return (
        f'<div id="{p}">\n<style>\n{style}\n</style>\n'
        f"{inputs}"
        f'<div class="vt-tabs-{p}" role="group" aria-label="Choose variant" '
        f'style="display:flex;gap:.3rem;flex-wrap:wrap">\n{tabs}</div>\n'
        f'<div class="vt-panels-{p}" style="border:2px solid var(--border);border-radius:0 8px 8px 8px;'
        f'padding:.7rem">\n{panel_html}</div>\n'
        f"</div>\n"
    )


def left_rail_layout(comp_id: str, items: Sequence[tuple[str, str]],
                     *, italic_count: int = 0, selected: int = 0) -> str:
    """Vertical radio rail (left) + panel area (right); one item visible at a time.

    Zero-JS (radio + ``:checked ~``). Reflows to a single column at narrow widths.
    Structural class names are id-namespaced (e.g. ``lr-panel-{p}``) so no class is
    ever shared across instances — nesting can never bleed styles or switching.

    ``italic_count`` renders the first N rail labels in italic (used to set a leading
    glossary entry apart from the demos). ``selected`` picks which panel is shown on
    load (default the first item); the mobile menu button labels that panel.
    """
    p = _safe(comp_id)
    style_lines = [
        f"#{p} {{ display:grid; grid-template-columns:minmax(0,14rem) minmax(0,1fr); gap:1rem; align-items:start; }}",
        f"#{p} .lr-rail-{p} {{ display:flex; flex-direction:column; gap:.3rem; }}",
        f"#{p} .lr-body-{p} {{ min-width:0; }}",
        f"#{p} .lr-panel-{p} {{ display:none; min-width:0; }}",
        f"#{p} .lr-menu-{p} {{ display:none; }}",  # menu toggle: shown only on narrow + JS
        f"@media (max-width:760px) {{ #{p} {{ grid-template-columns:minmax(0,1fr); }} }}",
        # progressive enhancement: with JS, narrow screens collapse the rail behind a menu
        f"@media (max-width:760px) {{ #{p}.lr-js .lr-menu-{p} {{ display:flex; }} }}",
        f"@media (max-width:760px) {{ #{p}.lr-js .lr-rail-{p} {{ display:none; }} }}",
        f"@media (max-width:760px) {{ #{p}.lr-js.lr-open .lr-rail-{p} {{ display:flex; }} }}",
    ]
    inputs, rail, panels = "", "", ""
    for i, (label, body) in enumerate(items):
        rid = f"{p}-r{i}"
        checked = " checked" if i == selected else ""
        italic = "font-style:italic;" if i < italic_count else ""
        style_lines.append(f"#{rid}:checked ~ .lr-body-{p} .lr-p{i}-{p} {{ display:block; }}")
        style_lines.append(
            f'#{rid}:checked ~ .lr-rail-{p} label[for="{rid}"]'
            " { background:var(--accent); color:var(--accent-fg); border-color:var(--accent); }")
        style_lines.append(
            f'#{rid}:focus-visible ~ .lr-rail-{p} label[for="{rid}"]'
            " { outline:3px solid var(--accent); outline-offset:2px; }")
        inputs += f'<input type="radio" name="{p}-lr" id="{rid}" style="{_VH}"{checked}>\n'
        rail += (
            f'<label for="{rid}" style="border:2px solid var(--border);border-radius:8px;'
            f'padding:.5rem .8rem;min-height:44px;display:flex;align-items:center;'
            f'cursor:pointer;font-weight:700;{italic}">{_e(label)}</label>\n')
        panels += f'<div class="lr-panel-{p} lr-p{i}-{p}">{body}</div>\n'
    style = "\n".join(style_lines)
    first = _e(items[selected][0]) if items else "Choose demo"
    menu = (
        f'<button type="button" class="lr-menu-{p}" aria-expanded="false" aria-controls="{p}-rail" '
        f'style="min-height:44px;align-items:center;gap:.5rem;border:2px solid var(--border);'
        f'border-radius:8px;padding:.5rem .8rem;cursor:pointer;font-weight:700">'
        f'<span aria-hidden="true">☰</span>'
        f'<span class="lr-menu-label-{p}">{first}</span></button>\n'
    )
    # Scoped progressive-enhancement script: toggle the menu, and close it (and update
    # the button label) when a demo is picked. Baseline works with JS off (rail visible).
    script = (
        "<script>\n(function(){\n"
        f'var r=document.getElementById("{p}");if(!r)return;r.classList.add("lr-js");\n'
        f'var b=r.querySelector(".lr-menu-{p}"),l=r.querySelector(".lr-menu-label-{p}");\n'
        'function s(o){r.classList.toggle("lr-open",o);'
        'b.setAttribute("aria-expanded",o?"true":"false");}\n'
        'b.addEventListener("click",function(){s(!r.classList.contains("lr-open"));});\n'
        f'r.querySelectorAll(\'input[name="{p}-lr"]\').forEach(function(x){{'
        'x.addEventListener("change",function(){'
        'var t=r.querySelector(\'label[for="\'+x.id+\'"]\');'
        "if(t&&l)l.textContent=t.textContent;s(false);});});\n"
        "})();\n</script>\n"
    )
    return (
        f'<div id="{p}" class="lr">\n<style>\n{style}\n</style>\n'
        f"{inputs}"
        f"{menu}"
        f'<div class="lr-rail-{p}" id="{p}-rail" role="group" aria-label="Choose demo">\n{rail}</div>\n'
        f'<div class="lr-body-{p}">\n{panels}</div>\n'
        f"{script}"
        f"</div>\n"
    )


def nav_shell(comp_id: str, items: Sequence[tuple[str, str]], *,
              style: str = "left_rail", leading: int = 0,
              selected: int | None = None) -> str:
    """Arrange a set of titled panels using one chosen navigation style.

    Each panel is a ``(title, html)`` pair. This one function handles all three
    styles, so a page can choose its style purely from its data:

    - ``"left_rail"``: a clickable list down the left; one panel shows at a time.
    - ``"top_tabs"``: a row of tabs across the top; one panel shows at a time.
    - ``"stacked"``: every panel shown one below another, with no switching.

    Args:
        comp_id: A short unique name for this block, used to build its HTML ids.
        items: The panels, in order, each a ``(title, html)`` pair.
        style: Which navigation style to use (see the list above).
        leading: How many of the first entries are reference material (such as
            Vocabulary or the page Concept) to set apart. The left-rail style
            shows them in italics; the other styles ignore this.
        selected: Which panel is open when the page loads, given by its position
            (0 is the first). The left-rail and top-tabs styles honour it; the
            stacked style ignores it. ``None`` means the first panel.

    Returns:
        The navigation block as a piece of HTML.

    Raises:
        ValueError: If ``style`` is not one of the three names above.
    """
    sel = 0 if selected is None else selected
    if style == "left_rail":
        return left_rail_layout(comp_id, items, italic_count=leading, selected=sel)
    if style == "top_tabs":
        return variant_tabs(comp_id, items, selected=sel)
    if style == "stacked":
        return "\n".join(body for _label, body in items)
    raise ValueError(
        f"unknown nav style {style!r}; valid choices: "
        "['left_rail', 'stacked', 'top_tabs']")


def code_diagram_panel(comp_id: str, code_html: str, diagram_html: str,
                       *, ratio: tuple[int, int] = (3, 1)) -> str:
    """Two-column code/diagram split; code scrolls; reflows to one column.

    ``ratio`` is (code_fraction, diagram_fraction) for the CSS grid tracks;
    the default (3, 1) gives the code three-quarters. Diagram-heavy subjects
    (stack frames, memory map) pass (2, 1) so the taller diagram gets more room.
    """
    p = _safe(comp_id)
    cf, df = ratio
    style = (
        f"#{p} {{ display: grid; grid-template-columns: minmax(0,{cf}fr) minmax(0,{df}fr); gap: 1rem; }}\n"
        f"#{p} .cdp-code {{ min-width:0; }}\n"
        f"#{p} .cdp-diagram {{ min-width:0; }}\n"
        f"@media (max-width: 760px) {{ #{p} {{ grid-template-columns: minmax(0,1fr); }} }}"
    )
    return (
        f'<div id="{p}" class="cdp">\n<style>\n{style}\n</style>\n'
        f'<div class="cdp-code">{code_html}</div>\n'
        f'<div class="cdp-diagram">{diagram_html}</div>\n'
        f"</div>\n"
    )


def zoomable(comp_id: str, inner_html: str, *, label: str = "⤢ Enlarge") -> str:
    """Wrap HTML in a zero-JS click-to-fullscreen container with zoom levels.

    A visually-hidden but keyboard-focusable checkbox drives the open state; the
    visible ``label`` chip opens it. When checked, the SAME ``.zoom-body`` (which
    contains ``inner_html`` verbatim — never duplicated, so any SVGs inside keep
    their one-to-one ``role="img"`` AND stay interactive: a stepper's radios
    still work in the overlay) is promoted to a fixed full-screen overlay.

    The enlarged content sits in ``.zoom-content`` — the ENTIRE right panel
    (``inner_html``: stepper + anatomy) as one unit — stacked ABOVE the full-area
    ``.zoom-backdrop`` (so clicks on the diagram/stepper land on it; only clicks
    in the surrounding backdrop, or the ✕, close it). Five zoom-level radios —
    0.5× / 0.75× / 1× / 1.5× / 2× — apply a single CSS ``zoom`` to that whole
    panel, so it scales as one unit and every internal relationship (frame
    diagram ↔ anatomy, spacing, text) is preserved exactly — just bigger or
    smaller. 1.5× is the default. The toolbar wraps and uses 44px touch targets
    for mobile. No ESC (a native <dialog> would need scripting)."""
    p = _safe(comp_id)
    # (sid, label, aria, zoom-factor) — a plain multiplier on the whole panel.
    levels = [
        ("zl0", "0.5×", "half size", "0.5"),
        ("zl1", "0.75×", "three-quarter size", "0.75"),
        ("zl2", "1×", "actual size", "1"),
        ("zl3", "1.5×", "1.5 times", "1.5"),
        ("zl4", "2×", "2 times", "2"),
    ]
    default = "zl3"
    active_sel = ", ".join(
        f"#{p} #{p}-{sid}:checked ~ .zoom-bar label[for={p}-{sid}]"
        for sid, _lab, _aria, _z in levels)
    zoom_css = "".join(
        f"#{p} .zoom-cb:checked ~ .zoom-body #{p}-{sid}:checked ~ .zoom-content"
        f" {{ zoom:{z}; }}\n"
        for sid, _lab, _aria, z in levels)
    style = (
        # hidden-but-focusable controls
        f"#{p} .zoom-cb, #{p} .zl {{ position:absolute; width:1px; height:1px;"
        f" overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}\n"
        f"#{p} .zoom-open {{ display:inline-flex; align-items:center; min-height:44px;"
        f" padding:.2rem .7rem; margin:.2rem 0 .4rem; border:1px solid var(--border,#bbb);"
        f" border-radius:8px; background:var(--panel-bg,#fff); cursor:pointer;"
        f" font:13px system-ui; width:fit-content; }}\n"
        f"#{p} .zoom-cb:focus-visible ~ .zoom-open {{ outline:2px solid var(--accent,#2a6);"
        f" outline-offset:2px; }}\n"
        f"#{p} .zoom-bar, #{p} .zoom-close, #{p} .zoom-backdrop {{ display:none; }}\n"
        # --- overlay open ---
        f"#{p} .zoom-cb:checked ~ .zoom-body {{ position:fixed; inset:0; z-index:1000;"
        f" background:#fff; overflow:auto; padding:1rem;"
        f" box-shadow:0 0 0 100vmax rgba(0,0,0,.5); }}\n"
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-backdrop {{ display:block;"
        f" position:fixed; inset:0; z-index:1001; }}\n"
        # The whole panel, at its natural size, centered; `zoom` (below) scales it
        # as one unit — so nothing inside is re-laid-out and nothing shifts.
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-content {{ position:relative;"
        f" z-index:1002; width:fit-content; margin:0 auto; }}\n"
        # toolbar: sticky so it never overlaps content even when it wraps on mobile
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-bar {{ display:flex; flex-wrap:wrap;"
        f" gap:.4rem; align-items:center; position:sticky; top:0; z-index:1003;"
        f" padding:.5rem; margin-bottom:1rem; background:#f4f6fb; border:1px solid #ccc;"
        f" border-radius:8px; }}\n"
        f"#{p} .zoom-bar .zlab {{ min-height:44px; display:inline-flex; align-items:center;"
        f" padding:.2rem .7rem; border:1px solid #bbb; border-radius:6px; background:#fff;"
        f" cursor:pointer; font:13px system-ui; }}\n"
        f"{active_sel} {{ background:#2a7f54; color:#fff; border-color:#2a7f54; }}\n"
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-close {{ display:inline-flex;"
        f" margin-left:auto; align-items:center; justify-content:center; min-width:44px;"
        f" min-height:44px; border:1px solid #bbb; border-radius:8px; background:#fff;"
        f" cursor:pointer; font-size:20px; }}\n"
        + zoom_css
    )
    radios = "".join(
        f'<input type="radio" class="zl" name="{p}-zl" id="{p}-{sid}"'
        f'{" checked" if sid == default else ""} aria-label="{aria}">'
        for sid, _lab, aria, _h in levels)
    zlabs = "".join(
        f'<label for="{p}-{sid}" class="zlab">{lab}</label>'
        for sid, lab, _aria, _h in levels)
    return (
        f'<div id="{p}" class="zoomwrap"><style>{style}</style>'
        f'<input type="checkbox" class="zoom-cb" id="{p}-zcb" '
        f'aria-label="Enlarge diagram">'
        f'<label for="{p}-zcb" class="zoom-open">{_e(label)}</label>'
        f'<div class="zoom-body">'
        + radios
        + f'<div class="zoom-bar">'
        + zlabs
        + f'<label for="{p}-zcb" class="zoom-close" aria-label="Close" '
        f'title="Close">✕</label>'
        f'</div>'
        f'<div class="zoom-content">{inner_html}</div>'
        f'<label for="{p}-zcb" class="zoom-backdrop" aria-hidden="true"></label>'
        f'</div></div>'
    )


def code_concept_panel(comp_id: str, main_html: str, concept_text: str,
                       *, title: str = "Concept") -> str:
    """Two-column split: the demo on the left, a titled Concept aside on the right.

    Used on subjects with no memory diagram so the otherwise-empty right column
    carries the per-example Concept instead. The aside is capped to the left
    column's height and scrolls internally (``overflow-y:auto``) so a long
    concept never stretches the panel; it is absolutely positioned so the row
    height is driven by the code, not the concept. On narrow screens it reflows
    below the code and shows in full.

    Args:
        comp_id: A short unique name, used to build CSS-safe element ids.
        main_html: The left column's content (the code/tabs cluster).
        concept_text: The Concept prose shown in the right aside.
        title: The bold heading on the aside; defaults to "Concept".

    Returns:
        The two-column panel as a piece of HTML.
    """
    p = _safe(comp_id)
    style = (
        # Code gets ~two-thirds; the prose Concept wraps comfortably in the rest.
        f"#{p} {{ display: grid; grid-template-columns: minmax(0,2fr) minmax(0,1fr);"
        f" gap: 1rem; align-items: start; }}\n"
        f"#{p} .ccp-main {{ min-width: 0; }}\n"
        # Top-aligned aside sized to its own content (no forced stretch, so a
        # short concept never leaves a tall empty box); capped to the viewport
        # and scrolls internally so a long concept never stretches the page.
        f"#{p} .ccp-aside {{ min-width: 0; max-height: calc(100vh - 4rem); overflow-y: auto;"
        f" border-left: 4px solid var(--accent); background: var(--panel-bg);"
        f" border-radius: 0 6px 6px 0; padding: .5rem .8rem; }}\n"
        f"#{p} .ccp-title {{ display: block; font-weight: 700; margin-bottom: .3rem; }}\n"
        f"@media (max-width: 760px) {{ #{p} {{ grid-template-columns: minmax(0,1fr); }} }}"
    )
    return (
        f'<div id="{p}" class="ccp">\n<style>\n{style}\n</style>\n'
        f'<div class="ccp-main">{main_html}</div>\n'
        f'<aside class="ccp-aside">'
        f'<b class="ccp-title">{_e(title)}</b>'
        f'<p style="margin:0">{_e(concept_text)}</p>'
        f"</aside>\n"
        f"</div>\n"
    )


def stacked_subcases(comp_id: str, subcases: Sequence[tuple[str, str]]) -> str:
    """Stack independent sub-cases at natural height (the page scrolls).

    An earlier fixed ``max-height`` boxed the stacked cases into a small
    scroll-region that floated in empty space on tall screens; letting them flow
    fills that space and shows every case's code in full.
    """
    p = _safe(comp_id)
    style = f"#{p} {{ min-width: 0; }}"
    cases = ""
    for label, body in subcases:
        cases += (
            f'<section class="ssc-case" style="border:1px solid var(--border);'
            f'border-radius:8px;padding:.6rem;margin-bottom:.8rem">\n'
            f"<h3>{_e(label)}</h3>\n{body}\n</section>\n"
        )
    return f'<div id="{p}" class="ssc">\n<style>\n{style}\n</style>\n{cases}</div>\n'


def frames_anatomy_details(comp_id: str, pd: dict) -> str:
    """A native <details> disclosure wrapping the full per-frame anatomy SVG."""
    p = _safe(comp_id)
    return (
        f'<details style="margin-top:.5rem;border:1px solid #ddd;border-radius:6px;'
        f'padding:.3rem .6rem"><summary style="cursor:pointer;min-height:44px;'
        f'font-weight:600">Show full frame anatomy</summary>\n'
        + _svg_frames_anatomy(pd, f"{p}-an")
        + "</details>\n"
    )


def stepped_frames(comp_id: str, steps, *, with_anatomy: bool = False) -> str:
    """Zero-JS CSS-radio stepper over frame snapshots: one radio + one frame SVG
    per step; selecting a step shows that snapshot. Frames present at a deeper
    step but gone at the current one are drawn ghost (reclaimed). Defaults to
    the deepest step. Assumes each step's frame list is a prefix of the deepest
    (true for straight call chains and recursion).

    When ``with_anatomy`` is set, a <details> "Show full frame anatomy" is
    emitted *inside the same container* holding one per-step anatomy table; the
    same step radios drive it, so the anatomy always matches the selected step
    (all frames live at that step, not just main)."""
    p = _safe(comp_id)
    ptrbytes, deepest = 8, []
    parsed = []
    for s in steps:
        pb, frames = _parse_frames(s)
        parsed.append(frames)
        if len(frames) > len(deepest):
            ptrbytes, deepest = pb, frames
    default = max(range(len(parsed)), key=lambda i: len(parsed[i])) if parsed else 0

    inputs, labels, views, ans = [], [], [], []
    css = [f"#{p} .sf-v {{ display:none; }}"]
    if with_anatomy:
        css.append(f"#{p} .sf-an {{ display:none; }}")
    for i, frames in enumerate(parsed):
        checked = " checked" if i == default else ""
        inputs.append(f'<input type="radio" name="{p}-step" id="{p}-s{i}"{checked} '
                      f'style="position:absolute;opacity:0">')
        labels.append(
            f'<label for="{p}-s{i}" style="cursor:pointer;border:1px solid #bbb;'
            f'border-radius:6px;padding:2px 9px;font:13px system-ui;'
            f'min-height:44px;display:inline-flex;align-items:center">'
            f'{i + 1}</label>')
        svg = _frames_core(deepest, f"{p}-fr{i}", solid=len(frames))
        views.append(f'<div class="sf-v sf-v{i}">{svg}</div>')
        css.append(f"#{p} #{p}-s{i}:checked ~ .sf-views .sf-v{i} {{ display:block; }}")
        css.append(f"#{p} #{p}-s{i}:checked ~ .sf-steps label[for={p}-s{i}] "
                   f"{{ background:#2a7f54; color:#fff; border-color:#2a7f54; }}")
        if with_anatomy:
            an_svg = _svg_frames_anatomy(steps[i], f"{p}-an{i}")
            ans.append(f'<div class="sf-an sf-an{i}">{an_svg}</div>')
            css.append(f"#{p} #{p}-s{i}:checked ~ .sf-anwrap .sf-an{i} "
                       f"{{ display:block; }}")
    anatomy = ""
    if with_anatomy:
        anatomy = (
            f'<details class="sf-anwrap" style="margin-top:.5rem;border:1px solid #ddd;'
            f'border-radius:6px;padding:.3rem .6rem"><summary style="cursor:pointer;'
            f'min-height:44px;font-weight:600">Show full frame anatomy</summary>'
            + "".join(ans) + "</details>"
        )
    return (
        f'<div id="{p}"><style>{chr(10).join(css)}</style>'
        + "".join(inputs)
        + f'<div class="sf-steps" style="display:flex;gap:6px;margin-bottom:8px">'
        + "".join(labels) + "</div>"
        + f'<div class="sf-views">' + "".join(views) + "</div>"
        + anatomy
        + "</div>"
    )


def _demo_variant_body(pid: str, v: dict, caption: str, diagram: bool = True) -> str:
    """One compiled program: code+diagram split, badge, output, collapsed bytes.

    The byte box is data-driven: it is emitted only when byte data exists. A
    variant with no bytes (e.g. a failed compile that never printed MEMBYTES)
    omits it rather than rendering a degenerate empty grid.

    ``diagram=False`` drops the memory diagram (and the two-column split),
    showing the code full-width — for subjects with no memory-model picture.

    When ``diagram=True`` but this variant has no ``ptrdata`` (a compile-error
    gotcha or a value-pass tab), the two-column grid is KEPT — so the code
    column's width never changes between variants — but the right cell is left
    empty rather than rendering the ``_svg_unknown`` "no diagram" placeholder.
    """
    if diagram:
        pd = v.get("ptrdata")
        steps = v.get("ptrdata_steps") or []
        ptype = (pd or {}).get("type")
        frame_steps = [s for s in steps if s.get("type") == "frames"]
        ratio = (3, 1)
        if len(frame_steps) > 1:
            diagram_html = zoomable(
                f"{pid}-zoom",
                stepped_frames(f"{pid}-md", frame_steps, with_anatomy=True))
            ratio = (2, 1)
        elif ptype == "frames":
            diagram_html = zoomable(
                f"{pid}-zoom",
                memory_diagram(f"{pid}-md", pd)
                + frames_anatomy_details(f"{pid}-fa", pd))
            ratio = (2, 1)
        elif ptype == "memmap":
            diagram_html = zoomable(f"{pid}-zoom", memory_diagram(f"{pid}-md", pd))
            ratio = (2, 1)
        else:
            diagram_html = memory_diagram(f"{pid}-md", pd) if pd else ""
        code_block = code_diagram_panel(f"{pid}-cdp", v["code_html"],
                                        diagram_html, ratio=ratio)
    else:
        code_block = v["code_html"]
    body = (
        code_block
        + '<div style="margin-top:.8rem">'
        + compile_status_badge(f"{pid}-badge", v["ok"], kind=v.get("error_kind") or "compile")
        + "</div>"
        + output_console(f"{pid}-out", v["stdout"] if v["ok"] else v["stderr"],
                         error=v["failed"], kind=v.get("error_kind") or "compile")
    )
    if v["bytes"]:
        body += (
            f'<details style="margin-top:.6rem"><summary style="min-height:44px;'
            f'cursor:pointer">Raw bytes of ptr (little-endian)</summary>\n'
            + byte_grid(f"{pid}-bytes", v["bytes"], caption=caption)
            + "</details>\n"
        )
    return body


def demo_panel(comp_id: str, entry: dict, diagram: bool = True,
               *, concept: str | None = None, concept_title: str = "Concept") -> str:
    """One demo's inner content: a variant_tabs cluster over a topic's baked data.

    A cases-topic variant carries a ``cases`` list; its sub-cases are stacked
    (each with its own compile verdict) inside the tab. Layout-agnostic.

    ``diagram=False`` suppresses the per-program memory diagram (see
    :func:`_demo_variant_body`).  When ``concept`` is given *and* there is no
    diagram, the whole cluster is placed in the left column and the concept fills
    the otherwise-empty right column as a titled aside (see
    :func:`code_concept_panel`); with a diagram, the concept is left to the
    demo's own ``concept`` block and this argument is ignored.
    """
    cid = _safe(comp_id)
    panels = []
    for label in entry["variants"]:
        v = entry[label]
        pid = f"{cid}-{_safe(label)}"
        if "cases" in v:
            subcases = []
            for j, case in enumerate(v["cases"]):
                spid = f"{pid}-c{j}"
                body = _demo_variant_body(spid, case, "Raw bytes of ptr (little-endian)",
                                          diagram=diagram)
                subcases.append((case["label"], body))
            body = stacked_subcases(f"{pid}-ssc", subcases)
        else:
            body = _demo_variant_body(pid, v, f"Raw bytes of ptr for {label} (little-endian)",
                                      diagram=diagram)
        panels.append((label, body))
    tabs = variant_tabs(cid, panels)
    if concept and not diagram:
        return code_concept_panel(f"{cid}-ccp", tabs, concept, title=concept_title)
    return tabs


def progressive_steps(comp_id: str, steps: Sequence[tuple[str, str]]) -> str:
    """Ordered student-paced reveals using native ``<details>/<summary>``."""
    p = _safe(comp_id)
    items = ""
    for i, (summary, content) in enumerate(steps):
        items += (
            f"<li><details>\n"
            f'<summary style="min-height:44px;padding:.3rem 0;cursor:pointer">{_e(summary)}</summary>\n'
            f"<div>{content}</div>\n"
            f"</details></li>\n"
        )
    return f'<ol id="{p}" class="psteps">\n{items}</ol>\n'
