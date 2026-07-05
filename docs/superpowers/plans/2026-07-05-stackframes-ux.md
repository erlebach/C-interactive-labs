# stackframes UX Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the frame-anatomy bug (show all live frames per step), add a general inline "Memory glossary" chip beside Concept, and add a zero-JS click-to-enlarge lightbox + a wider default diagram column for the stackframes diagrams.

**Architecture:** All changes live in the engine's presentation layer (`components.py`, one `render_page.py` builder, one `_CSS` rule) plus one demo YAML. The anatomy is folded into `stepped_frames` and gated by the existing step radios; the lightbox promotes the *same* diagram container to a fixed overlay via a CSS-only checkbox (no DOM duplication, so the WCAG `svg==role` invariant holds). Everything is additive — the six pointer renderers and their pages are untouched.

**Tech Stack:** Python 3 (engine), pytest (g++-gated for subject tests, pure for engine unit tests), inline SVG, zero-JS CSS-radio/checkbox interactions.

**Spec:** `docs/superpowers/specs/2026-07-05-stackframes-ux-design.md`. **Run everything from the project root** `/Users/erlebach/src/2026/isc5305_f2026/opencode`.

---

## File structure

**Modify:**
- `cpp_labs/components.py` — `code_diagram_panel` (add `ratio`), `stepped_frames` (add `with_anatomy`), `_demo_variant_body` (rewire); add `glossary_note`, `zoomable`.
- `cpp_labs/html_renderer.py` — one `_CSS` chip-row rule.
- `cpp_labs/yaml_engine/render_page.py` — add `_build_glossary_note` + register in `_BUILDERS`.
- `cpp_labs/stackframes/demos/sf_memmap.demo.yaml` — add the `glossary_note` block.

**Test:**
- `cpp_labs/tests/test_stepped_frames.py` — extend (anatomy-per-step; rewire assertions).
- `cpp_labs/tests/test_zoomable.py` — new.
- `cpp_labs/tests/test_glossary_note.py` — new.
- `cpp_labs/tests/test_code_diagram_panel_ratio.py` — new.
- `cpp_labs/stackframes/tests/test_stackframes.py` — extend (memory glossary, step-synced anatomy, enlarge).

---

## Task 1: `code_diagram_panel` gains a `ratio` argument

**Files:**
- Modify: `cpp_labs/components.py` (`code_diagram_panel`, ~line 757)
- Test: `cpp_labs/tests/test_code_diagram_panel_ratio.py`

- [ ] **Step 1: Write the failing test**

```python
# cpp_labs/tests/test_code_diagram_panel_ratio.py
from cpp_labs.components import code_diagram_panel


def test_default_ratio_is_3_to_1():
    html = code_diagram_panel("cdp", "<pre>c</pre>", "<svg></svg>")
    assert "minmax(0,3fr) minmax(0,1fr)" in html


def test_custom_ratio_2_to_1():
    html = code_diagram_panel("cdp", "<pre>c</pre>", "<svg></svg>", ratio=(2, 1))
    assert "minmax(0,2fr) minmax(0,1fr)" in html
    assert "<pre>c</pre>" in html and "<svg></svg>" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_code_diagram_panel_ratio.py -q`
Expected: FAIL — `TypeError: code_diagram_panel() got an unexpected keyword argument 'ratio'`.

- [ ] **Step 3: Write minimal implementation**

Replace `code_diagram_panel` (currently ~757-772) with:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_code_diagram_panel_ratio.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/components.py cpp_labs/tests/test_code_diagram_panel_ratio.py
git commit -m "feat(components): code_diagram_panel ratio arg (wider diagram for frames/memmap)"
```

---

## Task 2: `zoomable` — zero-JS click-to-enlarge wrapper

**Files:**
- Modify: `cpp_labs/components.py` (add `zoomable` near `code_diagram_panel`)
- Test: `cpp_labs/tests/test_zoomable.py`

- [ ] **Step 1: Write the failing test**

```python
# cpp_labs/tests/test_zoomable.py
from cpp_labs.components import zoomable


def test_zoomable_wraps_without_duplicating_inner():
    inner = "<svg id='the-only-svg'></svg>"
    html = zoomable("z", inner)
    assert html.count("the-only-svg") == 1          # inner appears exactly once
    assert html.count('type="checkbox"') == 1       # one control
    assert "Enlarge" in html                         # visible open affordance
    assert "zoom-body" in html


def test_zoomable_default_state_is_not_fixed_overlay():
    # The overlay styling is gated behind :checked — the checkbox is unchecked
    # by default, so no ' checked' attribute is emitted on the input.
    html = zoomable("z", "<svg></svg>")
    assert " checked" not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_zoomable.py -q`
Expected: FAIL — `ImportError: cannot import name 'zoomable'`.

- [ ] **Step 3: Write minimal implementation**

Add after `code_diagram_panel` in `cpp_labs/components.py`:

```python
def zoomable(comp_id: str, inner_html: str, *, label: str = "⤢ Enlarge") -> str:
    """Wrap HTML in a zero-JS click-to-fullscreen container.

    A visually-hidden but keyboard-focusable checkbox drives the state; the
    visible ``label`` chip opens it. When checked, the SAME ``.zoom-body`` (which
    contains ``inner_html`` verbatim — never duplicated, so any SVGs inside keep
    their one-to-one ``role="img"`` and interactive state) is promoted to a fixed
    full-screen overlay. A close glyph and a full-area backdrop label both toggle
    the checkbox off. No ESC (a native <dialog> would need scripting)."""
    p = _safe(comp_id)
    style = (
        f"#{p} .zoom-cb {{ position:absolute; width:1px; height:1px; overflow:hidden;"
        f" clip:rect(0 0 0 0); white-space:nowrap; }}\n"
        f"#{p} .zoom-open {{ display:inline-flex; align-items:center; min-height:44px;"
        f" padding:.2rem .7rem; margin:.2rem 0 .4rem; border:1px solid var(--border,#bbb);"
        f" border-radius:8px; background:var(--panel-bg,#fff); cursor:pointer;"
        f" font:13px system-ui; width:fit-content; }}\n"
        f"#{p} .zoom-cb:focus-visible ~ .zoom-open {{ outline:2px solid var(--accent,#2a6);"
        f" outline-offset:2px; }}\n"
        f"#{p} .zoom-close, #{p} .zoom-backdrop {{ display:none; }}\n"
        f"#{p} .zoom-cb:checked ~ .zoom-body {{ position:fixed; inset:0; z-index:1000;"
        f" background:#fff; overflow:auto; padding:2.5rem 1.5rem 1.5rem;"
        f" box-shadow:0 0 0 100vmax rgba(0,0,0,.5); }}\n"
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-close {{ display:flex;"
        f" position:fixed; top:.6rem; right:.9rem; z-index:1002; align-items:center;"
        f" justify-content:center; width:44px; height:44px; border:1px solid #bbb;"
        f" border-radius:8px; background:#fff; cursor:pointer; font-size:20px; }}\n"
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-backdrop {{ display:block;"
        f" position:fixed; inset:0; z-index:1001; }}\n"
        f"#{p} .zoom-cb:checked ~ .zoom-body svg {{ width:auto; max-width:100%;"
        f" height:auto; max-height:calc(100vh - 5rem); }}\n"
    )
    return (
        f'<div id="{p}" class="zoomwrap"><style>{style}</style>'
        f'<input type="checkbox" class="zoom-cb" id="{p}-zcb" '
        f'aria-label="Enlarge diagram">'
        f'<label for="{p}-zcb" class="zoom-open">{_e(label)}</label>'
        f'<div class="zoom-body">{inner_html}'
        f'<label for="{p}-zcb" class="zoom-backdrop" aria-hidden="true"></label>'
        f'<label for="{p}-zcb" class="zoom-close" aria-label="Close" '
        f'title="Close">✕</label>'
        f'</div></div>'
    )
```

Note: `⤢` is the ⤢ enlarge glyph, `✕` the ✕ close glyph — written as escapes to keep the source ASCII-safe. The `.zoom-close` sits *after* `.zoom-backdrop` in source so it stacks above (higher z-index also enforces this).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_zoomable.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/components.py cpp_labs/tests/test_zoomable.py
git commit -m "feat(components): zoomable zero-JS click-to-enlarge lightbox"
```

---

## Task 3: `stepped_frames` gains step-synced anatomy (`with_anatomy`)

**Files:**
- Modify: `cpp_labs/components.py` (`stepped_frames`, ~line 852)
- Test: `cpp_labs/tests/test_stepped_frames.py` (add new tests)

- [ ] **Step 1: Write the failing tests** (append to the existing file)

```python
# append to cpp_labs/tests/test_stepped_frames.py
def test_stepped_frames_no_anatomy_by_default():
    html = stepped_frames("sf", _steps())
    assert "Show full frame anatomy" not in html


def test_stepped_frames_anatomy_is_per_step():
    html = stepped_frames("sf", _steps(), with_anatomy=True)
    assert "Show full frame anatomy" in html
    # one anatomy view per step (3), each gated by its radio
    assert html.count("sf-an") >= 3
    # the deepest step (main+foo) anatomy names both frames + real slots
    assert "foo()" in html and "return address" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_stepped_frames.py -q`
Expected: FAIL — `TypeError: stepped_frames() got an unexpected keyword argument 'with_anatomy'`.

- [ ] **Step 3: Write minimal implementation**

`stepped_frames` currently imports are satisfied (`_parse_frames`, `_frames_core`, `_svg_frames_anatomy` are already imported at the top of components.py). Replace the whole `stepped_frames` function (~852-890) with:

```python
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
                   f"{{ background:#2a8a5a; color:#fff; border-color:#2a8a5a; }}")
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
```

Note: the `<details class="sf-anwrap">` is a sibling of the radio `<input>`s (both direct children of `#{p}`), so `#{p}-s{i}:checked ~ .sf-anwrap .sf-an{i}` reaches the per-step anatomy. All `.sf-an` start hidden; the checked step reveals its own.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_stepped_frames.py -q`
Expected: PASS — the four original tests plus the two new ones. (`test_demo_variant_body_uses_stepper_when_steps_present` still passes here; it is updated in Task 5.)

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/components.py cpp_labs/tests/test_stepped_frames.py
git commit -m "feat(components): stepped_frames with_anatomy renders per-step frame anatomy"
```

---

## Task 4: `glossary_note` component + block builder + chip-row CSS

**Files:**
- Modify: `cpp_labs/components.py` (add `glossary_note` near `concept_note`, ~line 263)
- Modify: `cpp_labs/html_renderer.py` (`_CSS`, after the concept caret rules ~line 694)
- Modify: `cpp_labs/yaml_engine/render_page.py` (add `_build_glossary_note`, register in `_BUILDERS`)
- Test: `cpp_labs/tests/test_glossary_note.py`

- [ ] **Step 1: Write the failing test**

```python
# cpp_labs/tests/test_glossary_note.py
from cpp_labs.components import glossary_note


def test_glossary_note_is_a_concept_style_chip():
    html = glossary_note("g", [("bss", "uninitialized globals"),
                               ("heap", "dynamic allocations")])
    assert 'class="concept chip-inline"' in html      # same chip look + inline flag
    assert "Memory glossary" in html                   # default label
    assert "<summary" in html and "caret" in html      # button-like toggle chip
    assert "bss" in html and "uninitialized globals" in html
    assert "heap" in html and "dynamic allocations" in html


def test_glossary_note_custom_label():
    html = glossary_note("g", [("x", "y")], label="Terms")
    assert "Terms" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_glossary_note.py -q`
Expected: FAIL — `ImportError: cannot import name 'glossary_note'`.

- [ ] **Step 3a: Add the component.** Insert after `concept_note` (after ~line 263) in `cpp_labs/components.py`:

```python
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
        f'<details id="{p}" class="concept chip-inline"{op} style="margin:.4rem 0">\n'
        f'<summary class="concept-toggle">'
        f'<span class="caret" aria-hidden="true">▸</span>{_e(label)}</summary>\n'
        f"{body}"
        f"</details>\n"
    )
```

(`▸` is the ▸ caret, matching `concept_note`.)

- [ ] **Step 3b: Add the chip-row CSS.** In `cpp_labs/html_renderer.py`, use Edit to insert these lines inside the `_CSS` triple-quoted string, right after the reduced-motion `}` closing the caret rule (~line 694) and before the `figure {` rule (~line 695). Insert only the CSS text (no stray Python quotes):

```css
/* Two chips on one row: a Concept chip immediately followed by an inline
   glossary chip both go inline-block; a lone Concept chip is unaffected. */
details.concept.chip-inline,
details.concept:has(+ details.concept.chip-inline) {
  display: inline-block; vertical-align: top; margin-right: .6rem;
}
```

Use Edit to insert those CSS lines into the `_CSS` triple-quoted string at that position (do not add stray Python quotes).

- [ ] **Step 3c: Add the block builder.** In `cpp_labs/yaml_engine/render_page.py`, add after `_build_concept` (~line 242):

```python
def _build_glossary_note(args: dict, data: dict) -> str:
    """Build one example's fold-away glossary chip from its YAML block.

    ``args["terms"]`` is a list of ``{term, def}`` maps (already ``${...}``-
    resolved); converted to (term, definition) pairs for the component."""
    terms = [(t["term"], t["def"]) for t in args["terms"]]
    return C.glossary_note(args["id"], terms,
                           label=args.get("label", "Memory glossary"),
                           open_=args.get("open", False))
```

And register it in `_BUILDERS` (add the one line):

```python
_BUILDERS = {
    "heading": _build_heading,
    "html": _build_html,
    "topic": _build_topic,
    "concept": _build_concept,
    "glossary_note": _build_glossary_note,
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest cpp_labs/tests/test_glossary_note.py -q`
Expected: PASS (2 passed).
Also run the render-page tests to confirm the new builder didn't break dispatch:
Run: `python -m pytest cpp_labs/tests/ -q -k "render or block or dispatch or interface"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/components.py cpp_labs/html_renderer.py cpp_labs/yaml_engine/render_page.py cpp_labs/tests/test_glossary_note.py
git commit -m "feat(components): glossary_note inline chip + block builder + chip-row CSS"
```

---

## Task 5: Rewire `_demo_variant_body` (ratio + zoomable + step-synced anatomy)

**Files:**
- Modify: `cpp_labs/components.py` (`_demo_variant_body`, ~line 908-922)
- Test: `cpp_labs/tests/test_stepped_frames.py` (update the demo-variant test)

- [ ] **Step 1: Update the failing test** — replace `test_demo_variant_body_uses_stepper_when_steps_present` in `cpp_labs/tests/test_stepped_frames.py` with:

```python
def test_demo_variant_body_uses_stepper_when_steps_present():
    v = {"code_html": "<pre>x</pre>", "ok": True, "failed": False,
         "stdout": "enter main", "stderr": "", "bytes": [],
         "ptrdata": {"type": "frames", "ptrbytes": "8", "live": "main:0x40:r:4:0"},
         "ptrdata_steps": _steps(), "error_kind": None}
    html = _demo_variant_body("t", v, "cap", diagram=True)
    assert html.count('type="radio"') == 3        # stepper rendered
    assert "Show full frame anatomy" in html       # anatomy present (in stepper now)
    assert "Enlarge" in html                        # zoomable lightbox present
    assert "minmax(0,2fr) minmax(0,1fr)" in html    # wider diagram column for frames
    # step-synced anatomy: the deepest step's anatomy names the deeper frame
    assert "foo()" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_stepped_frames.py::test_demo_variant_body_uses_stepper_when_steps_present -q`
Expected: FAIL — no `Enlarge` / no `2fr` (current code uses the separate anatomy call, `code_diagram_panel` default ratio, and no zoomable).

- [ ] **Step 3: Rewire the `if diagram:` block.** Replace the body of the `if diagram:` branch (components.py ~908-922) with:

```python
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
```

Note: pointer subjects fall into the final `else` (their `ptype` is `raw`/`ref`/`unique`/… — not `frames`/`memmap`, and they have no `ptrdata_steps`), so they keep the old `(3, 1)` ratio, no zoomable, no anatomy — unchanged behavior. `frames_anatomy_details` is still used by the single-snapshot `elif ptype == "frames"` path.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_stepped_frames.py -q`
Expected: PASS (all tests in the file).

- [ ] **Step 4b: Engine regression — the six pointer renderers + all engine unit tests must be unaffected.**

Run: `python -m pytest cpp_labs/tests/ -q`
Expected: PASS (all pre-existing engine tests still green; pointer subjects have no frames/memmap ptype and no steps, so the new branches are skipped).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/components.py cpp_labs/tests/test_stepped_frames.py
git commit -m "feat(components): wire step-synced anatomy + zoomable + 2:1 ratio for frame diagrams"
```

---

## Task 6: Author the memory glossary on `sf_memmap`; extend subject tests

**Files:**
- Modify: `cpp_labs/stackframes/demos/sf_memmap.demo.yaml`
- Modify: `cpp_labs/stackframes/tests/test_stackframes.py`

- [ ] **Step 1: Add the `glossary_note` block.** Edit `cpp_labs/stackframes/demos/sf_memmap.demo.yaml` to:

```yaml
title: "Process Memory Map"
language: cpp
bake: { mm: sf_memmap }
blocks:
  - concept:       { id: mm-note, text: "${mm.explanation}" }
  - glossary_note:
      id: mm-gloss
      label: "Memory glossary"
      terms:
        - { term: "text",    def: "The program's machine code (instructions); read-only, at the lowest addresses." }
        - { term: "data",    def: "Initialized global and static variables." }
        - { term: "bss",     def: "Uninitialized global and static variables; zero-filled at program start." }
        - { term: "heap",    def: "Dynamic allocations (new / malloc); grows toward higher addresses." }
        - { term: "stack",   def: "Call frames holding parameters and local variables; grows toward lower addresses." }
        - { term: "segment", def: "A named region of the process's address space." }
  - topic:         { id: mm, source: mm }
```

- [ ] **Step 2: Extend the subject tests.** Add to `cpp_labs/stackframes/tests/test_stackframes.py`:

```python
def test_memory_glossary_present(html):
    assert "Memory glossary" in html
    assert "zero-filled at program start" in html      # the bss definition
    assert "grows toward lower addresses" in html       # the stack definition


def test_anatomy_is_step_synced(html):
    # Before the fix the anatomy only ever showed main() (local: r). The
    # recursion example's deepest step now renders countdown frames, whose
    # local is n -> "local: n" appears only if per-step anatomy works.
    assert "local: n" in html


def test_enlarge_control_present(html):
    assert "Enlarge" in html and "zoom-body" in html


def test_wider_diagram_ratio(html):
    assert "minmax(0,2fr) minmax(0,1fr)" in html
```

- [ ] **Step 3: Run the subject tests**

Run: `python -m pytest cpp_labs/stackframes/tests/ -q`
Expected: PASS — the original 9 plus the 4 new (13 passed). If `test_wcag_svg_role_invariant` or `test_unique_dom_ids` fail, the per-step anatomy or zoomable introduced an unwrapped SVG or a duplicate id — fix the offending renderer/id (each anatomy view id is `{p}-an{i}`, each zoom id `{pid}-zoom` — all unique). Do NOT weaken those invariants.

- [ ] **Step 4: Commit**

```bash
git add cpp_labs/stackframes/demos/sf_memmap.demo.yaml cpp_labs/stackframes/tests/test_stackframes.py
git commit -m "feat(stackframes): memory glossary on sf_memmap; subject tests for anatomy/glossary/enlarge"
```

---

## Task 7: Regen catalog, full suite, rebuild, docs, finish branch

**Files:**
- Modify: `usage/INTERFACE_ELEMENTS.md` (only if the catalog changed)
- Modify: `JOURNAL.md`, add `handoffs/HANDOFF_<stamp>.md`

- [ ] **Step 1: Regenerate the interface catalog + freshness test.**

Run: `python -m cpp_labs.yaml_engine.interface_catalog`
Then: `git status --porcelain usage/INTERFACE_ELEMENTS.md` and `python -m pytest cpp_labs -k interface_catalog -q`
Expected: freshness test PASS. `glossary_note`/`zoomable` are internal helpers and `glossary_note` is a `_BUILDERS` entry (not a `_DISPATCH` block keyword the catalog introspects), so likely no diff — but commit the file if it changed.

- [ ] **Step 2: Full suite.**

Run: `python -m pytest cpp_labs -q`
Expected: PASS — the prior 500 plus the new engine + subject tests. If a pre-existing pointer test regressed, the culprit is the `_demo_variant_body` rewire — confirm pointer variants still hit the final `else` branch.

- [ ] **Step 3: Rebuild every page + spot-check the built stackframes page.**

```bash
./build_labs.sh
python - <<'PY'
h = open("dist_labs/stackframes.rail/stackframes.rail.html").read()
print("Memory glossary:", "Memory glossary" in h)
print("Enlarge:", "Enlarge" in h, "| zoom-body:", "zoom-body" in h)
print("2fr ratio:", "minmax(0,2fr) minmax(0,1fr)" in h)
print("anatomy local: n:", "local: n" in h)
print("svg==role:", h.count("<svg"), "==", h.count('role="img"'), h.count("<svg") == h.count('role="img"'))
import re
ids = re.findall(r'id="([^"]+)"', h)
print("unique ids:", len(ids) == len(set(ids)))
PY
```
Expected: all True; svg==role equal; ids unique. Serve for a visual check if desired: `python3 -m http.server -d dist_labs 8000` — confirm the Memory glossary chip sits beside Concept, the anatomy shows all live frames at the selected step, and ⤢ Enlarge opens a full-screen diagram that closes on ✕/backdrop.

- [ ] **Step 4: Update JOURNAL + write handoff.** Get the timestamp: `TZ=America/New_York date "+%Y-%m-%d %H:%M"`. Prepend a `JOURNAL.md` entry (summary ≤15 lines + optional `### Details`) covering the three improvements + verification; write `handoffs/HANDOFF_<YYYY-MM-DD_HHhMMmEST>.md`. Commit:

```bash
git add JOURNAL.md handoffs/ usage/INTERFACE_ELEMENTS.md
git commit -m "docs(stackframes-ux): JOURNAL entry + handoff; regen interface catalog"
```

- [ ] **Step 5: Finish the branch.** Use superpowers:finishing-a-development-branch to integrate `feat/stackframes-ux` (the user chose Push + PR last time — offer the same options).

---

## Self-review (against the spec)

- **#1 anatomy fix (spec Item 1):** Task 3 folds per-step anatomy into `stepped_frames`; Task 5 wires `with_anatomy=True` and drops the separate call in the stepped path; single-snapshot path keeps `frames_anatomy_details`. Verified by `test_stepped_frames_anatomy_is_per_step` + subject `test_anatomy_is_step_synced` (`local: n`). ✔
- **#2 memory glossary (spec Item 2):** Task 4 adds `glossary_note` + `_build_glossary_note` + chip-row CSS (`:has()`-scoped, lone concept untouched); Task 6 authors it on `sf_memmap`. Verified by `test_glossary_note.py` + subject `test_memory_glossary_present`. ✔
- **#3 lightbox + bigger default (spec Item 3):** Task 1 (`ratio`), Task 2 (`zoomable`, no DOM duplication), Task 5 (wire `(2,1)` + `zoomable` for frames/memmap only). Verified by `test_zoomable.py`, `test_code_diagram_panel_ratio.py`, subject `test_enlarge_control_present`/`test_wider_diagram_ratio`. ✔
- **Invariants:** WCAG `svg==role` preserved (zoomable duplicates nothing; per-step anatomy SVGs all go through `_wrap_svg`); unique ids (`{p}-an{i}`, `{pid}-zoom`); pointer subjects unchanged (final `else`, `(3,1)`, no zoomable). Task 5 Step 4b + Task 6 Step 3 + Task 7 Step 2 guard these. ✔
- **Placeholder scan:** none — every code step shows complete code. ✔
- **Name consistency:** `with_anatomy`, `ratio`, `zoomable`, `glossary_note`, `_build_glossary_note`, `chip-inline`, `sf-anwrap`/`sf-an{i}`, `{pid}-zoom` used identically across tasks. ✔
