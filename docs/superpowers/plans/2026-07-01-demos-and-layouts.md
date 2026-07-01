# Demos & Layouts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the Pointers & References lab as one standalone page where only one demo (= one whole topic) shows at a time, driven by a reusable, data-only (YAML) demo/glossary/layout system with a selectable navigation style (left-rail now, top-tabs next).

**Architecture:** Keep Python as a small fixed engine + pure component library; demos, glossaries, and layouts are YAML data. A demo renders as an HTML *fragment* (no page shell); a *layout* spec composes N demo fragments into one standalone page, renders a `header:` (legend + glossaries) once at the top, and wraps everything in one shell with a chosen nav component. All switching is zero-JS (radio + `:checked ~`), WCAG AA, with real g++ output baked at build time.

**Tech Stack:** Python 3, PyYAML, g++ (build-time only), pytest. No runtime JS.

**Spec:** `docs/superpowers/specs/2026-07-01-demos-and-layouts-design.md`

**Run all commands from the project root** `/Users/erlebach/src/2026/isc5305_f2026/opencode`.

---

## File structure

Engine / components (Python — one-time additions, not per-demo):
- Modify `cpp_ptr_lab/yaml_engine/render_page.py` — add `dangling_ptr` to the registry; split `render_fragment` out of `render_page`; make `_build_topic` a thin adapter over `C.demo_panel`; add `_render_header`, `build_layout`, `_LAYOUTS`, CLI routing.
- Modify `cpp_ptr_lab/components.py` — add `glossary`, `demo_panel` (+ private `_demo_variant_body`), `left_rail_layout`, `top_tabs_layout`.
- Modify `cpp_ptr_lab/yaml_engine/test_render_page.py` — pure tests for the above.

Content (YAML — the whole point: no Python added per demo):
- Create `cpp_ptr_lab/pointers_refs/demos/*.demo.yaml` (8 files).
- Create `cpp_ptr_lab/pointers_refs/glossaries/pointers.glossary.yaml`.
- Create `cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml` (a) and `pointers_refs.tabs.yaml` (b).
- Create `cpp_ptr_lab/pointers_refs/test_layouts.py` — g++-gated build integration + accessibility scan.

---

## Task 1: Add `dangling_ptr` to the engine topic registry

**Files:**
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py:55-64` (the `_topic_registry` function)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

Add to `test_render_page.py` (inside a new class at end of file):

```python
class TestRegistry:
    def test_dangling_ptr_is_registered(self):
        reg = R._topic_registry()
        assert "dangling_ptr" in reg
        assert reg["dangling_ptr"].id == "dangling_ptr"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestRegistry -v`
Expected: FAIL — `KeyError`/assert: `"dangling_ptr" not in reg`.

- [ ] **Step 3: Implement**

In `render_page.py`, update `_topic_registry` imports and list to include `dangling_ptr`:

```python
def _topic_registry() -> dict[str, Any]:
    from ..pointers_refs.topics import (
        basic_ptr, const_taxonomy, dangling_ptr, null_deref, ref_const,
        ref_must_bind, ref_no_null, ref_rebind_illusion,
    )
    from ..smart_ptrs.topics import TOPICS as SMART
    from ..function_args.topics import TOPICS as FUNC_ARGS
    topics = [basic_ptr, const_taxonomy, ref_must_bind, ref_no_null,
              ref_rebind_illusion, ref_const, null_deref, dangling_ptr,
              *SMART, *FUNC_ARGS]
    return {t.id: t for t in topics}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestRegistry -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "feat(yaml_engine): register dangling_ptr topic"
```

---

## Task 2: Split `render_fragment` out of `render_page`

Lets a layout embed several demos' inner HTML into one page. `render_page` keeps emitting the full shell (behavior preserved).

**Files:**
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py:240-246` (the `render_page` function)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

```python
class TestFragment:
    def test_render_fragment_has_no_html_shell(self):
        spec = {"title": "T", "blocks": [{"color_legend": {"id": "lg"}}]}
        frag = R.render_fragment(spec, FAKE)
        assert "<html" not in frag and "<head" not in frag and "<!DOCTYPE" not in frag
        assert 'class="legend"' in frag  # the block itself is present

    def test_render_page_still_wraps_shell(self):
        spec = {"title": "T", "blocks": [{"color_legend": {"id": "lg"}}]}
        html = R.render_page(spec, FAKE)
        assert "<!DOCTYPE html>" in html and 'lang="en"' in html
        assert 'class="legend"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestFragment -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'render_fragment'`.

- [ ] **Step 3: Implement**

Replace `render_page` in `render_page.py` with:

```python
def render_fragment(spec: dict, data: dict) -> str:
    """Translate *spec*'s blocks to HTML — no page shell. Pure (no g++)."""
    return "\n".join(_render_block(b, data) for b in spec.get("blocks", []))


def render_page(spec: dict, data: dict) -> str:
    """Translate *spec* (with pre-baked *data*) into a self-contained page.

    Pure — no I/O, no g++.  Use :func:`build_page` to bake and write.
    """
    body = render_fragment(spec, data)
    return C.page_shell("page", body, title=spec.get("title", "Topic"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestFragment -v`
Expected: PASS. Also run the whole engine file to confirm no regression:
Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "refactor(yaml_engine): split render_fragment from render_page"
```

---

## Task 3: `glossary` component

A pure component rendering a definition list. Term/def pairs arrive from YAML as a list of `{term, def}` dicts; the block adapter converts them to tuples (matching the existing `_PAIR_ARGS` pattern).

**Files:**
- Modify: `cpp_ptr_lab/components.py` (add function near `callout_note`)
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py` (`_DISPATCH` + `_PAIR_ARGS`)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

```python
class TestGlossary:
    def test_glossary_renders_dl_with_terms(self):
        from cpp_ptr_lab import components as C
        html = C.glossary("g1", "Pointers", [("dereference (*)", "reads the pointee")])
        assert "<dl" in html and "</dl>" in html
        assert "<dt" in html and "dereference (*)" in html
        assert "<dd" in html and "reads the pointee" in html
        assert 'id="g1"' in html

    def test_glossary_block_via_engine_pairs_adapter(self):
        spec = {"title": "T", "blocks": [
            {"glossary": {"id": "g", "title": "Vocab",
                          "terms": [{"term": "pointee", "def": "the object pointed to"}]}},
        ]}
        html = R.render_page(spec, FAKE)
        assert "pointee" in html and "the object pointed to" in html
        assert "<dl" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestGlossary -v`
Expected: FAIL — `AttributeError: module 'cpp_ptr_lab.components' has no attribute 'glossary'`.

- [ ] **Step 3: Implement**

In `components.py`, add after `callout_note` (around line 145):

```python
def glossary(comp_id: str, title: str, terms: Sequence[tuple[str, str]]) -> str:
    """A reusable term/definition list (prose vocabulary), rendered as a <dl>.

    Accessible: the <section> is labelled by its heading via aria-labelledby.
    """
    p = _safe(comp_id)
    tid = f"{p}-title"
    rows = ""
    for term, definition in terms:
        rows += f"<dt>{_e(term)}</dt><dd>{_e(definition)}</dd>\n"
    return (
        f'<section class="glossary" id="{p}" aria-labelledby="{tid}" '
        f'style="border:2px solid var(--border);border-radius:8px;padding:.6rem .9rem;margin:.6rem 0">\n'
        f'<h2 id="{tid}" style="font-size:1rem;margin:.2rem 0 .4rem">{_e(title)}</h2>\n'
        f'<dl style="margin:0">\n{rows}</dl>\n'
        f"</section>\n"
    )
```

In `render_page.py`, register it in `_DISPATCH` (after `"stacked_subcases": C.stacked_subcases,`):

```python
    "glossary": C.glossary,
```

and add the pairs adapter to `_PAIR_ARGS`:

```python
    "glossary": ("terms", ("term", "def")),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestGlossary -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/components.py cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "feat(components): add glossary component (term/def <dl>)"
```

---

## Task 4: `demo_panel` component + make `_build_topic` a thin adapter

Promote the hardcoded body of `_build_topic` to a reusable, tested component `demo_panel(comp_id, entry)`, where `entry` is one topic's baked data (`{variants, <label>: {...}|{"cases":[...]}}`). Wrap the byte grid in `<details>` so a demo stays ~one screen.

**Files:**
- Modify: `cpp_ptr_lab/components.py` (add `demo_panel` + `_demo_variant_body`)
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py:191-211` (`_build_topic`) and remove the now-moved `_panel_program`
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

```python
class TestDemoPanel:
    def test_demo_panel_variant_tabs_and_details_bytes(self):
        from cpp_ptr_lab import components as C
        html = C.demo_panel("dp", FAKE["bp"])
        assert "vt-tabs" in html                 # int/double variant tabs
        assert "<details" in html                # byte grid collapsed
        assert 'class="badge"' in html and 'class="byte-grid"' in html
        ids = _ids(html)
        assert len(ids) == len(set(ids)), "dup ids in demo_panel"

    def test_demo_panel_cases_topic_stacks_subcases(self):
        from cpp_ptr_lab import components as C
        html = C.demo_panel("dp", FAKE_CASES["ct"])
        assert html.count('class="ssc"') == 2    # one per decl-type tab
        assert "console--err" in html            # the failing sub-case
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestDemoPanel -v`
Expected: FAIL — no attribute `demo_panel`.

- [ ] **Step 3: Implement**

In `components.py`, add near `code_diagram_panel` (after `stacked_subcases`):

```python
def _demo_variant_body(pid: str, v: dict, caption: str) -> str:
    """One compiled program: code+diagram split, badge, output, collapsed bytes."""
    return (
        code_diagram_panel(f"{pid}-cdp", v["code_html"],
                           memory_diagram(f"{pid}-md", v["ptrdata"]))
        + '<div style="margin-top:.8rem">'
        + compile_status_badge(f"{pid}-badge", v["ok"])
        + "</div>"
        + output_console(f"{pid}-out", v["stdout"] if v["ok"] else v["stderr"],
                         error=v["failed"])
        + f'<details style="margin-top:.6rem"><summary style="min-height:44px;'
          f'cursor:pointer">Raw bytes of ptr (little-endian)</summary>\n'
        + byte_grid(f"{pid}-bytes", v["bytes"], caption=caption)
        + "</details>\n"
    )


def demo_panel(comp_id: str, entry: dict) -> str:
    """One demo's inner content: a variant_tabs cluster over a topic's baked data.

    A cases-topic variant carries a ``cases`` list; its sub-cases are stacked
    (each with its own compile verdict) inside the tab. Layout-agnostic.
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
                body = _demo_variant_body(spid, case, "Raw bytes of ptr (little-endian)")
                subcases.append((case["label"], body))
            body = stacked_subcases(f"{pid}-ssc", subcases)
        else:
            body = _demo_variant_body(pid, v, f"Raw bytes of ptr for {label} (little-endian)")
        panels.append((label, body))
    return variant_tabs(cid, panels)
```

In `render_page.py`, delete the `_panel_program` and `_build_topic` bodies (lines ~191-211) and replace with a thin adapter:

```python
def _build_topic(args: dict, data: dict) -> str:
    """A demo_panel over a baked topic (thin adapter; content lives in components)."""
    return C.demo_panel(args["id"], data[args["source"]])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestDemoPanel -v`
Expected: PASS. Then the full suite (the existing basic_ptr/function_args/pointers_refs build tests exercise `_build_topic` via `demo_panel`; the only intended output change is the byte grid now sitting inside `<details>`):
Run: `python -m pytest cpp_ptr_lab/ -q`
Expected: all PASS. If a prior build test asserted the byte grid is *not* inside details, update that assertion (none currently do).

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/components.py cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "refactor(components): promote _build_topic body to demo_panel; collapse byte grid"
```

---

## Task 5: `left_rail_layout` component

A vertical radio rail (demo selector) beside a panel area; only the selected demo shows. Zero-JS; single-column reflow at narrow width (WCAG 1.4.10).

**Files:**
- Modify: `cpp_ptr_lab/components.py` (add after `variant_tabs`)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

```python
class TestLeftRailLayout:
    def test_left_rail_one_panel_per_item_first_checked(self):
        from cpp_ptr_lab import components as C
        html = C.left_rail_layout("lab", [("Basic", "<p>a</p>"), ("const", "<p>b</p>")])
        assert html.count("lr-panel") == 2
        assert html.count("<input") == 2
        assert "checked" in html                       # first item checked
        assert "@media" in html                        # single-column reflow rule
        assert 'aria-label' in html                    # nav group has a name
        ids = _ids(html)
        assert len(ids) == len(set(ids)), "dup ids in left_rail_layout"

    def test_left_rail_zero_js(self):
        from cpp_ptr_lab import components as C
        html = C.left_rail_layout("lab", [("A", "<p>a</p>")])
        assert "<script" not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestLeftRailLayout -v`
Expected: FAIL — no attribute `left_rail_layout`.

- [ ] **Step 3: Implement**

In `components.py`, add after `variant_tabs`:

```python
def left_rail_layout(comp_id: str, items: Sequence[tuple[str, str]]) -> str:
    """Vertical radio rail (left) + panel area (right); one item visible at a time.

    Zero-JS (radio + ``:checked ~``). Reflows to a single column at narrow widths.
    """
    p = _safe(comp_id)
    style_lines = [
        f"#{p} {{ display:grid; grid-template-columns:14rem 1fr; gap:1rem; align-items:start; }}",
        f"#{p} .lr-rail {{ display:flex; flex-direction:column; gap:.3rem; }}",
        f"#{p} .lr-panel {{ display:none; }}",
        f"@media (max-width:760px) {{ #{p} {{ grid-template-columns:1fr; }} }}",
    ]
    inputs, rail, panels = "", "", ""
    for i, (label, body) in enumerate(items):
        rid = f"{p}-r{i}"
        checked = " checked" if i == 0 else ""
        style_lines.append(f"#{rid}:checked ~ .lr-body .lr-p{i} {{ display:block; }}")
        style_lines.append(
            f'#{rid}:checked ~ .lr-rail label[for="{rid}"]'
            " { background:var(--accent); color:var(--accent-fg); border-color:var(--accent); }")
        style_lines.append(
            f'#{rid}:focus-visible ~ .lr-rail label[for="{rid}"]'
            " { outline:3px solid var(--accent); outline-offset:2px; }")
        inputs += f'<input type="radio" name="{p}-lr" id="{rid}" style="{_VH}"{checked}>\n'
        rail += (
            f'<label for="{rid}" style="border:2px solid var(--border);border-radius:8px;'
            f'padding:.5rem .8rem;min-height:44px;display:flex;align-items:center;'
            f'cursor:pointer;font-weight:700">{_e(label)}</label>\n')
        panels += f'<div class="lr-panel lr-p{i}">{body}</div>\n'
    style = "\n".join(style_lines)
    return (
        f'<div id="{p}" class="lr">\n<style>\n{style}\n</style>\n'
        f"{inputs}"
        f'<div class="lr-rail" role="group" aria-label="Choose demo">\n{rail}</div>\n'
        f'<div class="lr-body">\n{panels}</div>\n'
        f"</div>\n"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestLeftRailLayout -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/components.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "feat(components): add left_rail_layout (vertical demo nav, zero-JS)"
```

---

## Task 6: header rendering + glossary file loading

`_render_header(blocks, base_dir)` renders the layout's `header:` list once. A `glossary` block with `source:` loads a shared `*.glossary.yaml`; other blocks (color_legend, heading, html) reuse the normal block dispatch.

**Files:**
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py` (add `_render_header`)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

```python
class TestHeader:
    def test_render_header_inline_and_legend(self, tmp_path):
        blocks = [
            {"color_legend": {"id": "lg"}},
            {"glossary": {"id": "g", "title": "V",
                          "terms": [{"term": "t1", "def": "d1"}]}},
        ]
        html = R._render_header(blocks, tmp_path)
        assert 'class="legend"' in html
        assert "t1" in html and "d1" in html and "<dl" in html

    def test_render_header_glossary_from_file(self, tmp_path):
        (tmp_path / "g.glossary.yaml").write_text(
            "title: Pointers\nterms:\n  - {term: pointee, def: the object pointed to}\n",
            encoding="utf-8")
        blocks = [{"glossary": {"id": "g", "source": "g.glossary.yaml"}}]
        html = R._render_header(blocks, tmp_path)
        assert "Pointers" in html and "pointee" in html and "the object pointed to" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestHeader -v`
Expected: FAIL — no attribute `_render_header`.

- [ ] **Step 3: Implement**

In `render_page.py`, add (near `render_fragment`):

```python
def _render_header(blocks: list, base_dir: Path) -> str:
    """Render a layout's ``header:`` blocks once. A ``glossary`` with ``source:``
    loads a shared ``*.glossary.yaml`` (relative to *base_dir*)."""
    out = []
    for block in blocks or []:
        (name, raw), = block.items()
        args = dict(raw or {})
        if name == "glossary" and "source" in args:
            g = load_spec(Path(base_dir) / args["source"])
            terms = [(t["term"], t["def"]) for t in g.get("terms", [])]
            out.append(C.glossary(args.get("id", "glossary"),
                                  g.get("title", "Glossary"), terms))
        else:
            out.append(_render_block(block, {}))
    return "\n".join(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestHeader -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "feat(yaml_engine): render layout header + load glossary files"
```

---

## Task 7: layout loader (`build_layout`) + CLI routing

`build_layout` bakes each referenced demo, renders it as a fragment, wraps the fragments in the chosen nav component, prepends the header, and writes one standalone page. The CLI routes a spec with a `demos:` key to `build_layout`.

**Files:**
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py` (add `_LAYOUTS`, `_stacked_layout`, `build_layout`; update `main`)
- Test: `cpp_ptr_lab/pointers_refs/test_layouts.py` (new; g++-gated)

- [ ] **Step 1: Write the failing test**

Create `cpp_ptr_lab/pointers_refs/test_layouts.py`:

```python
"""Build integration for demo/layout composition. Compiler-gated."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from cpp_ptr_lab.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None


def _ids(html):
    return re.findall(r'\bid="([^"]+)"', html)


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestBuildLayoutMinimal:
    def _mini(self, tmp_path):
        demo = tmp_path / "basic.demo.yaml"
        demo.write_text(
            "title: Basic Pointer\nbake: {bp: basic_ptr}\n"
            "blocks:\n  - topic: {id: bp, source: bp}\n", encoding="utf-8")
        layout = tmp_path / "mini.rail.yaml"
        layout.write_text(
            "title: Mini Lab\nstyle: left_rail\n"
            "header:\n  - color_legend: {id: lg}\n"
            "demos:\n  - basic.demo.yaml\n", encoding="utf-8")
        out = R.build_layout(layout, tmp_path / "dist")
        return out, out.read_text(encoding="utf-8")

    def test_writes_standalone_page_under_stem(self, tmp_path):
        out, html = self._mini(tmp_path)
        assert out.exists() and out.parent.name == "mini.rail"
        assert "<!DOCTYPE html>" in html and 'lang="en"' in html

    def test_left_rail_and_header_present(self, tmp_path):
        _, html = self._mini(tmp_path)
        assert "lr-rail" in html and 'class="legend"' in html
        assert "Basic Pointer" in html and "PTRDATA" in html

    def test_no_duplicate_ids(self, tmp_path):
        _, html = self._mini(tmp_path)
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_layouts.py -v`
Expected: FAIL — no attribute `build_layout`.

- [ ] **Step 3: Implement**

In `render_page.py`, add:

```python
def _stacked_layout(comp_id: str, items) -> str:
    """Fallback nav: stack every demo (no selector)."""
    return "\n".join(body for _label, body in items)


_LAYOUTS = {
    "left_rail": C.left_rail_layout,
    "top_tabs": C.variant_tabs,      # top tabs == variant_tabs (two-row via flex-wrap)
    "stacked": _stacked_layout,
}


def build_layout(layout_path: Path | str, dist_dir: Path) -> Path:
    """Bake+compose a layout spec into one standalone page.

    Writes ``<dist>/<layout-stem>/<layout-stem>.html``. Raises before baking if
    g++ is unavailable.
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. This page bakes real compiler output at "
            "build time; install a C++ compiler first.")
    layout_path = Path(layout_path)
    base = layout_path.parent
    spec = load_spec(layout_path)

    header_html = _render_header(spec.get("header", []), base)
    items = []
    for demo_ref in spec.get("demos", []):
        demo_spec = load_spec(base / demo_ref)
        data = bake_all(demo_spec.get("bake", {}))
        fragment = render_fragment(demo_spec, data)
        items.append((demo_spec.get("title", "Demo"), fragment))

    nav = _LAYOUTS[spec.get("style", "left_rail")]("lab", items)
    body = f"{header_html}\n{nav}" if header_html else nav
    page = C.page_shell("page", body, title=spec.get("title", "Lab"))

    stem = layout_path.stem
    out = Path(dist_dir) / stem / f"{stem}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out
```

Update `main()` to route on the `demos:` key. Replace the `out = build_page(...)` line with:

```python
    spec_probe = load_spec(spec_path)
    out = build_layout(spec_path, dist) if "demos" in spec_probe else build_page(spec_path, dist)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_layouts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/pointers_refs/test_layouts.py
git commit -m "feat(yaml_engine): build_layout composes demos into one page + CLI routing"
```

---

## Task 8: author the demos, glossary, and left-rail layout (phase a deliverable)

All content is YAML — no Python added.

**Files (create):**
- `cpp_ptr_lab/pointers_refs/demos/basic_ptr.demo.yaml`
- `cpp_ptr_lab/pointers_refs/demos/const_taxonomy.demo.yaml`
- `cpp_ptr_lab/pointers_refs/demos/ref_must_bind.demo.yaml`
- `cpp_ptr_lab/pointers_refs/demos/ref_no_null.demo.yaml`
- `cpp_ptr_lab/pointers_refs/demos/ref_rebind_illusion.demo.yaml`
- `cpp_ptr_lab/pointers_refs/demos/ref_const.demo.yaml`
- `cpp_ptr_lab/pointers_refs/demos/null_deref.demo.yaml`
- `cpp_ptr_lab/pointers_refs/demos/dangling_ptr.demo.yaml`
- `cpp_ptr_lab/pointers_refs/glossaries/pointers.glossary.yaml`
- `cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml`
- Test: extend `cpp_ptr_lab/pointers_refs/test_layouts.py`

- [ ] **Step 1: Write the failing test**

Append to `test_layouts.py`:

```python
LAYOUT = Path(__file__).parent / "layouts" / "pointers_refs.rail.yaml"

TOPIC_NAMES = [
    "Basic Pointer", "const Taxonomy", "Ref: Must Bind", "Ref: No Null",
    "Ref: Rebind Illusion", "Ref: const Ref", "Gotcha: Null Deref",
    "Gotcha: Dangling Ptr",
]


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestPointersRefsRailPage:
    def _html(self, tmp_path):
        out = R.build_layout(LAYOUT, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_all_eight_demos_present(self, tmp_path):
        _, html = self._html(tmp_path)
        for name in TOPIC_NAMES:
            assert name in html, f"missing demo: {name}"

    def test_basic_ptr_type_tabs_and_const_2x2(self, tmp_path):
        _, html = self._html(tmp_path)
        for t in ("int", "double", "float"):
            assert f">{t}<" in html
        assert 'class="ssc"' in html and "read-only" in html   # const 2x2 + real error

    def test_glossary_in_header(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "<dl" in html and "dereference" in html

    def test_no_dup_ids_self_contained(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "<script" not in html and "https://" not in html and "src=" not in html
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"

    def test_every_svg_has_accessible_name(self, tmp_path):
        _, html = self._html(tmp_path)
        # WCAG 1.1.1: every inline svg must be role="img" with a non-empty <title>.
        assert html.count("<svg") == html.count('role="img"'), "an svg lacks role=img"
        assert "<title></title>" not in html and "<title/>" not in html
        # no <img> without alt (there should be no <img> at all)
        assert not re.search(r"<img(?![^>]*\balt=)", html), "an <img> lacks alt"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_layouts.py::TestPointersRefsRailPage -v`
Expected: FAIL — `FileNotFoundError` for `layouts/pointers_refs.rail.yaml`.

- [ ] **Step 3: Create the content files**

`demos/basic_ptr.demo.yaml`:
```yaml
title: "Basic Pointer"
bake: { bp: basic_ptr }
blocks:
  - callout_note: { id: bp-note, label: Concept, text: "${bp.explanation}" }
  - topic: { id: bp, source: bp }
```

`demos/const_taxonomy.demo.yaml`:
```yaml
title: "const Taxonomy"
bake: { ct: const_taxonomy }
blocks:
  - callout_note: { id: ct-note, label: Concept, text: "${ct.explanation}" }
  - topic: { id: ct, source: ct }
```

`demos/ref_must_bind.demo.yaml`:
```yaml
title: "Ref: Must Bind"
bake: { rmb: ref_must_bind }
blocks:
  - callout_note: { id: rmb-note, label: Concept, text: "${rmb.explanation}" }
  - topic: { id: rmb, source: rmb }
```

`demos/ref_no_null.demo.yaml`:
```yaml
title: "Ref: No Null"
bake: { rnn: ref_no_null }
blocks:
  - callout_note: { id: rnn-note, label: Concept, text: "${rnn.explanation}" }
  - topic: { id: rnn, source: rnn }
```

`demos/ref_rebind_illusion.demo.yaml`:
```yaml
title: "Ref: Rebind Illusion"
bake: { rri: ref_rebind_illusion }
blocks:
  - callout_note: { id: rri-note, label: Concept, text: "${rri.explanation}" }
  - topic: { id: rri, source: rri }
```

`demos/ref_const.demo.yaml`:
```yaml
title: "Ref: const Ref"
bake: { rc: ref_const }
blocks:
  - callout_note: { id: rc-note, label: Concept, text: "${rc.explanation}" }
  - topic: { id: rc, source: rc }
```

`demos/null_deref.demo.yaml`:
```yaml
title: "Gotcha: Null Deref"
bake: { nd: null_deref }
blocks:
  - callout_note: { id: nd-note, label: Concept, text: "${nd.explanation}" }
  - topic: { id: nd, source: nd }
```

`demos/dangling_ptr.demo.yaml`:
```yaml
title: "Gotcha: Dangling Ptr"
bake: { dp: dangling_ptr }
blocks:
  - callout_note: { id: dp-note, label: Concept, text: "${dp.explanation}" }
  - topic: { id: dp, source: dp }
```

`glossaries/pointers.glossary.yaml`:
```yaml
title: "Vocabulary — Pointers & References"
terms:
  - { term: "address-of (&)", def: "operator that yields the memory address of an object" }
  - { term: "dereference (*)", def: "operator that accesses the object a pointer points to" }
  - { term: "pointee", def: "the object a pointer refers to" }
  - { term: "null pointer", def: "a pointer that points to nothing (nullptr); dereferencing it is undefined behaviour" }
  - { term: "reference", def: "an alias for an existing object; must bind at declaration and cannot be rebound" }
  - { term: "dangling pointer", def: "a pointer to memory that has been freed or gone out of scope; using it is undefined behaviour" }
  - { term: "const pointer vs pointer to const", def: "int* const fixes the pointer; const int* fixes the pointee (read declarations right-to-left)" }
```

`layouts/pointers_refs.rail.yaml`:
```yaml
title: "Pointers & References — Lab 1"
style: left_rail
header:
  - color_legend: { id: legend }
  - glossary: { id: g-ptr, source: ../glossaries/pointers.glossary.yaml }
demos:
  - ../demos/basic_ptr.demo.yaml
  - ../demos/const_taxonomy.demo.yaml
  - ../demos/ref_must_bind.demo.yaml
  - ../demos/ref_no_null.demo.yaml
  - ../demos/ref_rebind_illusion.demo.yaml
  - ../demos/ref_const.demo.yaml
  - ../demos/null_deref.demo.yaml
  - ../demos/dangling_ptr.demo.yaml
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_layouts.py::TestPointersRefsRailPage -v`
Expected: PASS. Then build the real page and eyeball it:
Run: `python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml`
Expected: `Wrote …/dist/pointers_refs.rail/pointers_refs.rail.html`
Run: `open dist/pointers_refs.rail/pointers_refs.rail.html`

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/pointers_refs/demos cpp_ptr_lab/pointers_refs/glossaries cpp_ptr_lab/pointers_refs/layouts cpp_ptr_lab/pointers_refs/test_layouts.py
git commit -m "feat(pointers_refs): left-rail lab page from data-only demos + glossary"
```

---

## Task 9: make `variant_tabs` nesting-safe (prerequisite for top-tabs)

`top_tabs` reuses `variant_tabs` as the *outer* nav, so it nests a `variant_tabs`
(a demo's own type tabs) inside another `variant_tabs`. Today `variant_tabs` hides
panels with a **descendant** selector (`#id .vt-panel`), so the outer rule would
also match the inner demo's panels and corrupt switching. Scope the selectors to
**direct children** so any nesting depth is isolated. (Phase-a left-rail does not
hit this — it uses distinct `.lr-*` classes — but do this before Task 10.)

**Files:**
- Modify: `cpp_ptr_lab/components.py` (`variant_tabs`, lines ~430-463)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

```python
class TestVariantTabsNesting:
    def test_scoped_with_child_combinator(self):
        from cpp_ptr_lab import components as C
        html = C.variant_tabs("outer", [("A", "x"), ("B", "y")])
        assert "> .vt-panels >" in html  # panels scoped to direct children

    def test_nested_variant_tabs_no_dup_ids(self):
        from cpp_ptr_lab import components as C
        inner = C.variant_tabs("inner", [("i0", "a"), ("i1", "b")])
        outer = C.variant_tabs("outer", [("o0", inner), ("o1", "z")])
        ids = _ids(outer)
        assert len(ids) == len(set(ids)), "dup ids across nested variant_tabs"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestVariantTabsNesting -v`
Expected: FAIL on `test_scoped_with_child_combinator` — `"> .vt-panels >"` absent
(current selectors are descendant-scoped).

- [ ] **Step 3: Implement**

In `components.py`, change the three style rules inside `variant_tabs` to use the
child combinator `>` (structure is `#p > .vt-panels > .vt-panel`, tabs are
`#p ~ .vt-tabs > label`):

```python
    style_lines = [f"#{p} > .vt-panels > .vt-panel {{ display: none; }}"]
    inputs, tabs, panel_html = "", "", ""
    for i, (label, body) in enumerate(panels):
        tid = f"{p}-t{i}"
        checked = " checked" if i == 0 else ""
        style_lines.append(f"#{tid}:checked ~ .vt-panels > .vt-p{i} {{ display: block; }}")
        style_lines.append(
            f'#{tid}:checked ~ .vt-tabs > label[for="{tid}"]'
            " { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }")
        style_lines.append(
            f'#{tid}:focus-visible ~ .vt-tabs > label[for="{tid}"]'
            " { outline: 3px solid var(--accent); outline-offset: 2px; }")
        inputs += f'<input type="radio" name="{p}-vt" id="{tid}" style="{_VH}"{checked}>\n'
        tabs += (
            f'<label for="{tid}" style="border:2px solid var(--border);border-radius:8px 8px 0 0;'
            f'padding:.4rem .9rem;min-height:44px;display:inline-flex;align-items:center;'
            f'cursor:pointer;font-weight:700">{_e(label)}</label>\n')
        panel_html += f'<div class="vt-panel vt-p{i}">{body}</div>\n'
```

(Only the three `style_lines.append`/first-line selectors change; the rest of
`variant_tabs` is unchanged.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestVariantTabsNesting -v`
Expected: PASS. Then the full suite (single-level usage is unaffected — panels are
already direct children of `.vt-panels`):
Run: `python -m pytest cpp_ptr_lab/ -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/components.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "fix(components): scope variant_tabs with child combinators (nesting-safe)"
```

---

## Task 10 (phase b): top-tabs layout from the same demos

Prove a second layout is a data-only change: the same demo files, a new layout spec with `style: top_tabs`.

**Files:**
- Create: `cpp_ptr_lab/pointers_refs/layouts/pointers_refs.tabs.yaml`
- Test: extend `cpp_ptr_lab/pointers_refs/test_layouts.py`

- [ ] **Step 1: Write the failing test**

Append to `test_layouts.py`:

```python
TABS = Path(__file__).parent / "layouts" / "pointers_refs.tabs.yaml"


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestPointersRefsTabsPage:
    def _html(self, tmp_path):
        out = R.build_layout(TABS, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_top_tabs_all_demos_and_real_output(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "vt-tabs" in html                       # outer top tabs present
        for name in TOPIC_NAMES:
            assert name in html
        assert "PTRDATA" in html and "read-only" in html

    def test_no_dup_ids_self_contained(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "<script" not in html and "https://" not in html
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_layouts.py::TestPointersRefsTabsPage -v`
Expected: FAIL — `FileNotFoundError` for `pointers_refs.tabs.yaml`.

- [ ] **Step 3: Create the layout file**

`layouts/pointers_refs.tabs.yaml` (identical to the rail file except `style`):
```yaml
title: "Pointers & References — Lab 1"
style: top_tabs
header:
  - color_legend: { id: legend }
  - glossary: { id: g-ptr, source: ../glossaries/pointers.glossary.yaml }
demos:
  - ../demos/basic_ptr.demo.yaml
  - ../demos/const_taxonomy.demo.yaml
  - ../demos/ref_must_bind.demo.yaml
  - ../demos/ref_no_null.demo.yaml
  - ../demos/ref_rebind_illusion.demo.yaml
  - ../demos/ref_const.demo.yaml
  - ../demos/null_deref.demo.yaml
  - ../demos/dangling_ptr.demo.yaml
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_layouts.py::TestPointersRefsTabsPage -v`
Expected: PASS. Build and compare side-by-side with the rail page:
Run: `python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.tabs.yaml`
Run: `open dist/pointers_refs.tabs/pointers_refs.tabs.html dist/pointers_refs.rail/pointers_refs.rail.html`

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/pointers_refs/layouts/pointers_refs.tabs.yaml cpp_ptr_lab/pointers_refs/test_layouts.py
git commit -m "feat(pointers_refs): top-tabs layout from the same demos (data-only)"
```

---

## Final verification

- [ ] Run the full suite: `python -m pytest cpp_ptr_lab/ -q` — expected: all PASS (357 prior + new tests).
- [ ] Build both pages and open them; confirm one demo shows at a time, the glossary sits once at the top, basic_ptr has int/double/float tabs, const shows the 2×2 with a real `read-only` error, and the byte grid is collapsed.
- [ ] Update `JOURNAL.md` (prepend an entry) describing the demos/layouts system and both pages; commit JOURNAL.md last.

## Notes for the implementer

- **Run everything from the project root.** Module paths and relative `dist/` resolve against cwd.
- **`FAKE` and `FAKE_CASES`** already exist in `test_render_page.py` (reuse them; don't redefine).
- **`_ids` helper** already exists in `test_render_page.py`; `test_layouts.py` defines its own copy (shown above).
- **ASan topics** (`null_deref`, `dangling_ptr`) compile then crash at *run* time; `capture_variant` captures whatever printed before the crash — they bake without raising (already proven for `null_deref`).
- **DRY/YAGNI:** `top_tabs` reuses `variant_tabs` (no new component, but Task 9 must make it nesting-safe first); `stacked` is a one-liner. Don't build a third bespoke nav.
- **SVG accessible-name contingency:** the const_taxonomy failing sub-cases have no pointer data, so they render an "unknown" diagram via `svg_renderer(None)`. If `test_every_svg_has_accessible_name` (Task 8) fails, the unknown/None branch of `svg_renderer` in `cpp_ptr_lab/html_renderer.py` is missing `role="img"` + a non-empty `<title>` — add it (RED→GREEN: assert the fix, then give the unknown svg `role="img"` and a `<title>` like "no pointer data available") and re-run. This is a real WCAG 1.1.1 gap worth fixing, not a test to loosen.
