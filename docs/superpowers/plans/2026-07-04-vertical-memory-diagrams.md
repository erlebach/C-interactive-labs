# Vertical Memory Diagrams Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-orient the `cpp_labs` SVG memory diagrams from horizontal to vertical via one shared `_stack_svg` layout helper, so the code column can widen on diagram pages.

**Architecture:** A single vertical-layout helper `_stack_svg(p, title, desc, sources, target, *, arrow_color)` owns geometry and encodes the source-count rule (≤2 converge / ≥3 stack). The six `_svg_*` renderers and the interactive `hover_link_diagram` become thin adapters that build box descriptors and call it. Arrowheads use a native `<marker>`. Box text is `14px ui-monospace` to match the code panel. `code_diagram_panel` widens `2fr:1fr → 3fr:1fr`.

**Tech Stack:** Python 3 (pure string-building functions, no deps), inline SVG, pytest. Run from project root `/Users/erlebach/src/2026/isc5305_f2026/opencode`.

**Spec:** `docs/superpowers/specs/2026-07-04-vertical-memory-diagrams-design.md`

---

## File Structure

- **Modify `cpp_labs/html_renderer.py`** — add vertical primitives (`_marker_defs`, `_arrow_v`, `_vbox`), add `_stack_svg`, give `_wrap_svg` a parameterized viewBox, rewrite the six `_svg_*` adapters. This file owns all diagram geometry.
- **Modify `cpp_labs/components.py`** — widen `code_diagram_panel` grid (line 779); refactor `hover_link_diagram` (lines 300–342) to reuse `_stack_svg` + hover CSS.
- **Modify `cpp_labs/tests/test_html_renderer.py`** — replace the one geometry test, add source-count branch tests.
- **Modify `cpp_labs/tests/test_components.py`** — update `hover_link_diagram` expectations if it asserted the old horizontal geometry.

### Constants (already in `html_renderer.py`, reused)

`_BOX_FILL="#e8f0ff"`, `_BOX_STROKE=addr blue`, `_ARROW_COLOR=addr blue`, `_NULL_COLOR="#8b0000"`, `_LABEL_COLOR="#1a1a1a"`, `_DIM_COLOR="#555555"`, `_SHARED_COUNT_COLOR="#4a7c20"`.

### New module-level layout constants (add near the SVG constants block)

```python
# Vertical-layout geometry (tall + narrow). Box text is 14px to match the code panel.
_FONT = 14           # px, == code panel font-size (ui-monospace)
_LH = 22             # text line height within a box
_BOX_TOP_PAD = 20    # box top padding to first text baseline
_PAD = 16            # outer padding / gap between boxes
_SRC_W1 = 160        # source/target box width when a single source
_SRC_W2 = 120        # source box width when two sources sit side-by-side
_ARROW_GAP = 60      # vertical gap reserved for the arrow between rows
_STACK_RM = 34       # right margin channel for >=3 stacked-source arrows
```

---

## Task 1: Vertical SVG primitives (marker, arrow, box)

**Files:**
- Modify: `cpp_labs/html_renderer.py` (add after the existing `_arrow` at ~line 82)
- Test: `cpp_labs/tests/test_html_renderer.py`

- [ ] **Step 1: Write the failing tests**

Add to `cpp_labs/tests/test_html_renderer.py` (import the private helpers at top of file: `from cpp_labs.html_renderer import _marker_defs, _arrow_v, _vbox`):

```python
class TestVerticalPrimitives:
    def test_marker_defs_has_marker_and_color(self):
        out = _marker_defs("m1", "#0b5394")
        assert "<marker" in out
        assert 'id="m1"' in out
        assert 'orient="auto-start-reverse"' in out
        assert "#0b5394" in out

    def test_arrow_v_references_marker_and_is_not_forced_horizontal(self):
        out = _arrow_v(50, 20, 50, 120, "#0b5394", "m1")
        assert 'marker-end="url(#m1)"' in out
        # vertical: y1 != y2 (the old _arrow forced mid_y = y1)
        assert 'y1="20"' in out and 'y2="120"' in out

    def test_vbox_height_scales_with_line_count(self):
        svg2, h2 = _vbox(10, 10, 160, [("ptr", "#1a1a1a"), ("0xabc", "#555555")], "#0b5394")
        svg3, h3 = _vbox(10, 10, 160,
                         [("a", "#1a1a1a"), ("b", "#555"), ("c", "#555")], "#0b5394")
        assert h3 > h2
        assert 'font-size="14"' in svg2      # matches code panel
        assert "<rect" in svg2 and "ptr" in svg2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest cpp_labs/tests/test_html_renderer.py::TestVerticalPrimitives -v`
Expected: FAIL with `ImportError: cannot import name '_marker_defs'`.

- [ ] **Step 3: Implement the primitives**

Add to `cpp_labs/html_renderer.py` after `_arrow` (keep `_arrow` for now; removed when adapters stop using it):

```python
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
    """A straight arrow from (x1,y1) to (x2,y2) with a marker arrowhead. Unlike the
    old `_arrow`, the endpoints are honored as given (no forced horizontal)."""
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
    ty = y + _BOX_TOP_PAD + 4
    for txt, color in lines:
        parts.append(
            f'<text x="{x + 14}" y="{ty}" font-size="{_FONT}" '
            f'font-family="ui-monospace,monospace" fill="{color}">{_e(txt)}</text>'
        )
        ty += _LH
    return "".join(parts), h
```

Also add the layout constants block (from "File Structure" above) near the existing SVG constants (~line 44).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest cpp_labs/tests/test_html_renderer.py::TestVerticalPrimitives -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/html_renderer.py cpp_labs/tests/test_html_renderer.py
git commit -m "feat(diagram): vertical SVG primitives (marker arrowhead, _arrow_v, _vbox)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `_stack_svg` layout helper + parameterized `_wrap_svg`

**Files:**
- Modify: `cpp_labs/html_renderer.py` (`_wrap_svg` at ~line 85; add `_stack_svg` after the primitives)
- Test: `cpp_labs/tests/test_html_renderer.py`

- [ ] **Step 1: Write the failing tests**

Add to `cpp_labs/tests/test_html_renderer.py` (extend the import: `_stack_svg`):

```python
def _box(lines, stroke="#0b5394"):
    return {"lines": lines, "stroke": stroke}

class TestStackSvg:
    def _one(self):
        return _stack_svg("t", "title", "desc",
                          [_box([("ptr", "#1a1a1a"), ("0xa", "#555")])],
                          _box([("val=42", "#1a1a1a"), ("0xb", "#555")]))

    def test_single_source_is_vertical_viewbox(self):
        out = self._one()
        assert "<svg" in out and 'role="img"' in out
        # tall + narrow: height > width, and not the old 500x160
        import re
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', out)
        w, h = int(m.group(1)), int(m.group(2))
        assert h > w
        assert (w, h) != (500, 160)

    def test_single_source_one_arrow(self):
        assert self._one().count("<line") == 1

    def test_two_sources_converge_two_arrows(self):
        out = _stack_svg("t", "title", "desc",
                         [_box([("sp1", "#1a1a1a")]), _box([("sp2", "#1a1a1a")])],
                         _box([("val=42", "#1a1a1a")]))
        assert out.count("<line") == 2      # both aliases point at the target

    def test_three_sources_stack_three_arrows(self):
        out = _stack_svg("t", "title", "desc",
                         [_box([("a", "#1a1a1a")]), _box([("b", "#1a1a1a")]),
                          _box([("c", "#1a1a1a")])],
                         _box([("val", "#1a1a1a")]))
        # >=3 sources route via <path>, one per source
        assert out.count("<path") >= 3

    def test_no_target_draws_no_arrow(self):
        out = _stack_svg("t", "weak", "desc",
                         [_box([("weak_ptr", "#1a1a1a"), ("exp", "#555")])], None)
        assert out.count("<line") == 0 and "url(#" not in out
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest cpp_labs/tests/test_html_renderer.py::TestStackSvg -v`
Expected: FAIL with `ImportError: cannot import name '_stack_svg'`.

- [ ] **Step 3: Update `_wrap_svg` for a parameterized viewBox**

Replace the existing `_wrap_svg` (html_renderer.py ~line 85–97):

```python
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
```

- [ ] **Step 4: Implement `_stack_svg`**

Add after the primitives in `html_renderer.py`:

```python
def _stack_svg(p: str, title: str, desc: str,
               sources: list[dict], target: dict | None,
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
            y += h + 12
        chan = x + ws + _STACK_RM // 2
        ty = y - 12 + _ARROW_GAP
        tsvg, th = _vbox(x, ty, ws, target["lines"], target["stroke"]) if target else ("", 0)
        body += tsvg
        for ex, ey in right_edges:
            body += (
                f'<path d="M{ex} {ey} H{chan} V{ty + th // 2} H{x + ws}" '
                f'fill="none" stroke="{arrow_color}" stroke-width="3" '
                f'marker-end="url(#{marker_id})"/>'
            )
        vb_w = ws + 2 * _PAD + _STACK_RM
        vb_h = ty + th + _PAD if target else y - 12 + _PAD
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
        body += (
            f'<text x="{tip_x + 8}" y="{(by + tgt_y) // 2}" font-size="11" '
            f'fill="{_DIM_COLOR}">points to</text>'
        )
    vb_h = tgt_y + th + _PAD
    return _wrap_svg(p, title, desc, body, vb_w=vb_w, vb_h=vb_h)
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest cpp_labs/tests/test_html_renderer.py::TestStackSvg -v`
Expected: PASS (5 passed).

- [ ] **Step 6: Commit**

```bash
git add cpp_labs/html_renderer.py cpp_labs/tests/test_html_renderer.py
git commit -m "feat(diagram): _stack_svg vertical layout (converge<=2 / stack>=3) + viewBox param

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Rewire the six `_svg_*` adapters

**Files:**
- Modify: `cpp_labs/html_renderer.py` (`_svg_raw/_null/_ref/_unique/_shared/_weak/_unknown`, lines 105–234)
- Test: `cpp_labs/tests/test_html_renderer.py` (rewrite `test_has_viewbox`)

- [ ] **Step 1: Rewrite the failing geometry test**

Replace `TestSvgRendererRaw::test_has_viewbox` in `cpp_labs/tests/test_html_renderer.py` (currently asserts `viewBox="0 0 500 160"`):

```python
    def test_has_vertical_viewbox(self):
        import re
        out = svg_renderer(_raw_pd())
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', out)
        assert m, "no viewBox"
        w, h = int(m.group(1)), int(m.group(2))
        assert h > w, "diagram should be taller than wide (vertical)"
```

Delete the old `test_has_viewbox` method. Keep every other test in the file unchanged (they assert `role="img"`, `<title>`, `<desc>`, addresses, values, `NULL`).

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest cpp_labs/tests/test_html_renderer.py -v`
Expected: FAIL — `test_has_vertical_viewbox` fails (still 500×160 from the old adapters).

- [ ] **Step 3: Rewrite the adapters**

Replace `_svg_raw`, `_svg_null`, `_svg_ref`, `_svg_unique`, `_svg_shared`, `_svg_weak`, `_svg_unknown` (html_renderer.py lines 105–234) with:

```python
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
    ptype = pd.get("type", "?") if pd else "?"
    body = _text(16, 40, f"type={_e(ptype)} — no diagram", _DIM_COLOR, 13)
    return _wrap_svg(p, f"diagram ({_e(ptype)})", "No diagram available.", body,
                     vb_w=220, vb_h=80)
```

Delete the now-unused `_rect` and `_arrow` helpers (replaced by `_vbox`/`_arrow_v`); keep `_text` (used by `_svg_unknown`).

- [ ] **Step 4: Run the full renderer test file**

Run: `python -m pytest cpp_labs/tests/test_html_renderer.py -v`
Expected: PASS (all green, including `test_has_vertical_viewbox` and the untouched role/title/value/NULL tests).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/html_renderer.py cpp_labs/tests/test_html_renderer.py
git commit -m "feat(diagram): rewire six _svg_* renderers to vertical _stack_svg

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Refactor `hover_link_diagram` to reuse `_stack_svg`

**Files:**
- Modify: `cpp_labs/components.py` (`hover_link_diagram`, lines 300–342)
- Test: `cpp_labs/tests/test_components.py`

- [ ] **Step 1: Write/adjust the failing test**

In `cpp_labs/tests/test_components.py`, add (near the existing `hover_link_diagram` test at ~line 344):

```python
    def test_hover_link_is_vertical_and_interactive(self):
        import re
        out = C.hover_link_diagram("hl", PD)
        assert 'role="img"' in out
        assert ":hover" in out or ":focus" in out          # still interactive
        assert 'tabindex="0"' in out                        # keyboard focusable
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', out)
        assert m and int(m.group(2)) > int(m.group(1))      # taller than wide
```

Keep the existing `hover_link_diagram` role=img assertions (`test_components.py:101`, `:344`) — they must stay green.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest cpp_labs/tests/test_components.py -k hover_link -v`
Expected: FAIL — old horizontal `viewBox="0 0 500 160"` makes the taller-than-wide assertion fail.

- [ ] **Step 3: Refactor `hover_link_diagram`**

Replace `hover_link_diagram` (components.py lines 300–342) so it builds its SVG via the shared renderer and overlays the hover CSS. It targets the boxes/arrow by CSS class hooks that `_stack_svg` does not emit, so we wrap `svg_renderer`'s output and inject a highlight rule keyed on the whole figure hover/focus:

```python
def hover_link_diagram(comp_id: str, ptrdata: dict[str, Any] | None) -> str:
    """Hovering/focusing the diagram lights the arrow + target (CSS only), on top
    of the shared vertical diagram. Highlight is color *and* thicker stroke (a
    non-color cue); the figure is focusable so keyboard users get the same effect."""
    p = _safe(comp_id)
    svg = svg_renderer(ptrdata, p)          # the shared vertical diagram
    style = (
        f"#{p} {{ cursor: pointer; }}\n"
        f"#{p}:focus {{ outline: none; }}\n"
        f"#{p}:hover line, #{p}:focus line,"
        f"#{p}:hover path, #{p}:focus path"
        " { stroke: var(--c-val); stroke-width: 5; }"
    )
    return (
        f'<figure id="{p}" tabindex="0" style="margin:0">\n'
        f'<style>\n{style}\n</style>\n{svg}\n</figure>\n'
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest cpp_labs/tests/test_components.py -k hover_link -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/components.py cpp_labs/tests/test_components.py
git commit -m "refactor(diagram): hover_link_diagram reuses vertical _stack_svg + hover CSS

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Widen `code_diagram_panel` to 3fr:1fr

**Files:**
- Modify: `cpp_labs/components.py` (line 779)
- Test: `cpp_labs/tests/test_components.py`

- [ ] **Step 1: Write the failing test**

Add to `cpp_labs/tests/test_components.py`:

```python
    def test_code_diagram_panel_gives_code_three_quarters(self):
        out = C.code_diagram_panel("cdp", "<pre>code</pre>", "<svg></svg>")
        assert "minmax(0,3fr) minmax(0,1fr)" in out
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest cpp_labs/tests/test_components.py -k code_diagram_panel_gives_code -v`
Expected: FAIL (grid is still `2fr`).

- [ ] **Step 3: Change the grid ratio**

In `cpp_labs/components.py` line 779, change:

```python
        f"#{p} {{ display: grid; grid-template-columns: minmax(0,2fr) minmax(0,1fr); gap: 1rem; }}\n"
```

to:

```python
        f"#{p} {{ display: grid; grid-template-columns: minmax(0,3fr) minmax(0,1fr); gap: 1rem; }}\n"
```

Also update the comment on line 778 from "~two-thirds" to "~three-quarters".

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest cpp_labs/tests/test_components.py -k code_diagram_panel_gives_code -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/components.py cpp_labs/tests/test_components.py
git commit -m "style(layout): widen code_diagram_panel 2fr:1fr -> 3fr:1fr for slim vertical diagram

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Full regression, catalog freshness, rebuild, visual verify

**Files:** none (verification only)

- [ ] **Step 1: Interface-catalog freshness**

`code_diagram_panel`, `memory_diagram`, `hover_link_diagram` signatures are unchanged, so the catalog should not drift. Confirm:

Run: `python -m pytest cpp_labs/tests/ -k interface_catalog -v`
Expected: PASS. If it fails, run `python -m cpp_labs.yaml_engine.interface_catalog` and `git add usage/INTERFACE_ELEMENTS.md`.

- [ ] **Step 2: Full `cpp_labs` suite**

Run: `python -m pytest cpp_labs/ -q`
Expected: PASS (all green). Note: suite runs ~3–4 min (compiles C++). If any `pointers_refs` layout test fails on the `svg-count == role=img-count` invariant, inspect — every `_stack_svg`/`_wrap_svg` output must still have exactly one `role="img"` per `<svg>`.

- [ ] **Step 3: Rebuild every page**

Run: `./build_labs.sh`
Expected: all pages rebuild with no error.

- [ ] **Step 4: Visual check in the browser**

Run: `python3 -m http.server -d dist_labs 8000` (background), open `http://localhost:8000/pointers_refs.rail.html` (the diagram page). Confirm: diagrams are tall+narrow, arrows point down with real arrowheads, `shared_ptr` two-alias converges, box text matches the code font size, and the code column is visibly wider (~3/4). Adjust `_ARROW_GAP`/box widths or the `3fr` ratio if it reads cramped.

- [ ] **Step 5: Commit any rebuild artifacts / final tweaks**

```bash
git add -A cpp_labs/ usage/
git commit -m "chore(diagram): verified vertical diagrams — full suite green, pages rebuilt

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review notes

- **Spec coverage:** vertical orientation (Tasks 1–3), source-count rule ≤2/≥3 (Task 2), marker arrows (Task 1), 14px-matches-code + max-width (Tasks 1–2), per-type mapping (Task 3), `hover_link_diagram` reuse (Task 4), `3fr:1fr` grid (Task 5), tests + rebuild (all tasks + Task 6). `byte_grid` correctly untouched (out of scope). Skills correctly absent (deferred).
- **Type consistency:** box spec shape `{"lines": [(text,color)...], "stroke": color}` is identical across `_stack_svg` and all Task-3 adapters; `_vbox` returns `(svg, height)` and every caller unpacks the pair; `_wrap_svg(..., vb_w=, vb_h=)` keyword args match every call site.
- **Deferred (not this plan):** `dangling_ptr` ASan run-time flag and `cls_copy_assign` gotcha (tracked in prior handoff).
