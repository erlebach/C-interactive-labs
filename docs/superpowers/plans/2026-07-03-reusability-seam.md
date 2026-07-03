# Reusability Seam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the demo/nav seam honest and consistent — one `nav_shell(items, style=…)` interface, a shared prose-box behavior for Vocabulary + Concept, the per-example Concept as a collapsed `<details>`, and one keyworded `sidebar:` list for all leading rail entries — without changing what today's pages render.

**Architecture:** Pure render functions in `cpp_ptr_lab/components.py` produce self-contained, zero-JS, WCAG-AA HTML; `cpp_ptr_lab/yaml_engine/render_page.py` composes them from YAML. This plan adds three components (`_prose_box`, `concept_note`, `concept_panel`, `nav_shell`), refactors `glossary` onto `_prose_box`, adds a `concept` block builder, and migrates 12 demo YAMLs + 2 rail YAMLs. Two byte-for-byte guard tests prove the refactors are lossless.

**Tech Stack:** Python 3, pytest, PyYAML, g++ (build-time only; integration tests are g++-gated and skip without it).

**Conventions (apply to every task):** Run all commands from the project root `/Users/erlebach/src/2026/isc5305_f2026/opencode`. TDD RED→GREEN, surgical diffs. Markdown paragraphs stay single-line. `rm` is interactive here — use `rm -f`. Do not stage scratch files (`session-*.md`, `prototype/`, `BEST-MODELS-*.md`, `TODO_NEXT.md`, `harness.md`, the `"I created this…"` md).

**Ordering rationale:** Section B (`_prose_box`) is a dependency of Concept rendering, so it lands first; then Section C (Example Concept), then Section A (`nav_shell`), then its `build_layout` wiring, then Section D (`sidebar:` + Demonstration Concept), then integration, then docs.

---

### Task 1: `_prose_box` shared helper; refactor `glossary` onto it (Section B)

**Files:**
- Modify: `cpp_ptr_lab/components.py` (add `_prose_box` before `glossary` at line ~169; rewrite `glossary` body)
- Test: `cpp_ptr_lab/tests/test_components.py`

- [ ] **Step 1: Write the failing tests**

Add to `cpp_ptr_lab/tests/test_components.py`:

```python
class TestProseBox:
    def test_glossary_output_unchanged_after_refactor(self):
        # Byte-for-byte guard: the _prose_box refactor must not change glossary's HTML.
        from cpp_ptr_lab import components as C
        html = C.glossary("g1", "Pointers", [("dereference (*)", "reads the pointee")])
        assert html == (
            '<section class="glossary" id="g1" aria-labelledby="g1-title" '
            'style="border:2px solid var(--border);border-radius:8px;padding:.6rem .9rem;margin:.6rem 0">\n'
            '<h2 id="g1-title" style="font-size:1rem;margin:.2rem 0 .4rem">Pointers</h2>\n'
            '<dl style="margin:0">\n'
            '<dt>dereference (*)</dt><dd>reads the pointee</dd>\n'
            '</dl>\n'
            '</section>\n'
        )

    def test_prose_box_without_title_omits_h2_and_aria(self):
        from cpp_ptr_lab import components as C
        html = C._prose_box("b1", "<p>hi</p>", css_class="concept")
        assert "<h2" not in html and "aria-labelledby" not in html
        assert 'class="concept"' in html and "<p>hi</p>" in html
        assert 'border:2px solid var(--border)' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_ptr_lab/tests/test_components.py::TestProseBox -q`
Expected: FAIL — `AttributeError: module 'cpp_ptr_lab.components' has no attribute '_prose_box'`.

- [ ] **Step 3: Add `_prose_box` and refactor `glossary`**

In `cpp_ptr_lab/components.py`, insert `_prose_box` immediately before `def glossary`:

```python
def _prose_box(comp_id: str, body_html: str, *, title: str | None = None,
               css_class: str = "prose") -> str:
    """Shared bordered prose section for glossary and concept panels.

    With a ``title`` the section is labelled by an ``<h2>`` via aria-labelledby
    (the glossary's accessible pattern); without one it is a plain bordered box.
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
```

Replace the body of `glossary` (keep its signature and docstring) with:

```python
    rows = ""
    for term, definition in terms:
        rows += f"<dt>{_e(term)}</dt><dd>{_e(definition)}</dd>\n"
    return _prose_box(comp_id, f'<dl style="margin:0">\n{rows}</dl>',
                      title=title, css_class="glossary")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest cpp_ptr_lab/tests/test_components.py -q`
Expected: PASS (all component tests, including the existing glossary tests, stay green).

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/components.py cpp_ptr_lab/tests/test_components.py
git commit -m "refactor(components): factor _prose_box shared by glossary + concept" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `concept_note` (Example Concept `<details>`) + `concept_panel` (Demonstration Concept) (Section C component + Section D component)

**Files:**
- Modify: `cpp_ptr_lab/components.py` (add both functions after `glossary`)
- Test: `cpp_ptr_lab/tests/test_components.py`

- [ ] **Step 1: Write the failing tests**

Add to `cpp_ptr_lab/tests/test_components.py`:

```python
class TestConcept:
    def test_concept_note_is_collapsed_details_by_default(self):
        from cpp_ptr_lab import components as C
        html = C.concept_note("c1", "A pointer stores an address.")
        assert html.startswith("<details")
        assert " open" not in html.split(">", 1)[0]      # collapsed: no open attr on <details>
        assert "<summary" in html and "Concept" in html
        assert "A pointer stores an address." in html

    def test_concept_note_open_and_custom_label_and_escaping(self):
        from cpp_ptr_lab import components as C
        html = C.concept_note("c2", "1 < 2 & true", label="Why", open=True)
        assert "<details id=\"c2\" class=\"concept\" open" in html
        assert ">Why</summary>" in html
        assert "1 &lt; 2 &amp; true" in html               # body escaped

    def test_concept_panel_is_titled_prose_box(self):
        from cpp_ptr_lab import components as C
        html = C.concept_panel("cp", "What this teaches.", title="Objective")
        assert "<details" not in html                      # a panel, not a disclosure
        assert 'class="concept"' in html
        assert ">Objective</h2>" in html
        assert "What this teaches." in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_ptr_lab/tests/test_components.py::TestConcept -q`
Expected: FAIL — `AttributeError: module 'cpp_ptr_lab.components' has no attribute 'concept_note'`.

- [ ] **Step 3: Add both components**

In `cpp_ptr_lab/components.py`, after `def glossary(...)` returns, add:

```python
def concept_note(comp_id: str, text: str, *, label: str = "Concept",
                 open: bool = False) -> str:
    """Example Concept: a native <details> disclosure (collapsed by default).

    Zero-JS, keyboard- and screen-reader-operable. The expanded body is a
    borderless prose box (the shared prose behaviour) inside the disclosure.
    """
    p = _safe(comp_id)
    body = _prose_box(f"{p}-box", f'<p style="margin:0">{_e(text)}</p>', css_class="concept")
    op = " open" if open else ""
    return (
        f'<details id="{p}" class="concept"{op} style="margin:.4rem 0">\n'
        f'<summary style="cursor:pointer;font-weight:700;min-height:44px;'
        f'display:flex;align-items:center">{_e(label)}</summary>\n'
        f"{body}"
        f"</details>\n"
    )


def concept_panel(comp_id: str, text: str, *, title: str = "Concept") -> str:
    """Demonstration Concept: a titled prose panel shown as a leading rail entry."""
    return _prose_box(comp_id, f'<p style="margin:0">{_e(text)}</p>',
                      title=title, css_class="concept")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest cpp_ptr_lab/tests/test_components.py::TestConcept -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/components.py cpp_ptr_lab/tests/test_components.py
git commit -m "feat(components): concept_note disclosure + concept_panel prose entry" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `concept` block builder in the engine + migrate 12 demo YAMLs (Section C wiring + data)

**Files:**
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py` (add `_build_concept`, register in `_BUILDERS` near line ~224)
- Modify: `cpp_ptr_lab/pointers_refs/demos/*.demo.yaml` (8), `cpp_ptr_lab/op_overload/demos/*.demo.yaml` (4)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing test**

Add to `cpp_ptr_lab/yaml_engine/test_render_page.py`:

```python
class TestConceptBlock:
    def test_concept_block_renders_disclosure_with_resolved_text(self):
        from cpp_ptr_lab.yaml_engine import render_page as R
        spec = {"blocks": [
            {"concept": {"id": "n1", "text": "${x.explanation}"}},
        ]}
        data = {"x": {"explanation": "A reference is an alias."}}
        html = R.render_fragment(spec, data)
        assert "<details" in html and "class=\"concept\"" in html
        assert ">Concept</summary>" in html
        assert "A reference is an alias." in html

    def test_concept_block_open_flag(self):
        from cpp_ptr_lab.yaml_engine import render_page as R
        spec = {"blocks": [{"concept": {"id": "n2", "text": "hi", "open": True}}]}
        html = R.render_fragment(spec, {})
        assert "class=\"concept\" open" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestConceptBlock -q`
Expected: FAIL — `KeyError: 'unknown block type: 'concept''`.

- [ ] **Step 3: Add the builder and register it**

In `cpp_ptr_lab/yaml_engine/render_page.py`, add near `_build_topic` (before `_BUILDERS`):

```python
def _build_concept(args: dict, data: dict) -> str:
    """Example Concept disclosure over resolved prose (default collapsed)."""
    return C.concept_note(args["id"], args["text"],
                          label=args.get("label", "Concept"),
                          open=args.get("open", False))
```

Then add the entry to `_BUILDERS`:

```python
_BUILDERS = {
    "heading": _build_heading,
    "html": _build_html,
    "topic": _build_topic,
    "concept": _build_concept,
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestConceptBlock -q`
Expected: PASS.

- [ ] **Step 5: Migrate the 12 demo YAMLs**

Run this from the project root (converts each demo's opening `callout_note` Concept block to a `concept` block, preserving id and text):

```bash
for f in cpp_ptr_lab/pointers_refs/demos/*.demo.yaml cpp_ptr_lab/op_overload/demos/*.demo.yaml; do
  perl -0pi -e 's/- callout_note: \{ id: ([^,]+), label: Concept, text: (.*?) \}/- concept: { id: $1, text: $2 }/g' "$f"
done
```

Verify all 12 changed and none still carry a `callout_note` Concept line:

Run: `grep -rl "label: Concept" cpp_ptr_lab/pointers_refs/demos cpp_ptr_lab/op_overload/demos; grep -rc "concept:" cpp_ptr_lab/pointers_refs/demos cpp_ptr_lab/op_overload/demos`
Expected: first grep prints nothing (no `label: Concept` left); second prints `:1` for each of the 12 files.

- [ ] **Step 6: Run the render_page + engine tests**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py -q`
Expected: PASS. (If a test asserted `class="callout"` in a demo fragment, update it to `class="concept"` — see Task 7 for the page-level check.)

- [ ] **Step 7: Commit**

```bash
git add cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py cpp_ptr_lab/pointers_refs/demos/*.demo.yaml cpp_ptr_lab/op_overload/demos/*.demo.yaml
git commit -m "feat(engine): concept block builder; migrate demos to collapsed Concept" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: `nav_shell` uniform dispatch + `variant_tabs` gains `selected` (Section A)

**Files:**
- Modify: `cpp_ptr_lab/components.py` (add `nav_shell`; add `selected` param to `variant_tabs` at line ~471)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing tests**

Add to `cpp_ptr_lab/yaml_engine/test_render_page.py`:

```python
class TestNavShell:
    ITEMS = [("A", "<p>a</p>"), ("B", "<p>b</p>"), ("C", "<p>c</p>")]

    def test_left_rail_is_byte_identical_to_left_rail_layout(self):
        from cpp_ptr_lab import components as C
        got = C.nav_shell("lab", self.ITEMS, style="left_rail", leading=1, selected=1)
        want = C.left_rail_layout("lab", self.ITEMS, italic_count=1, selected=1)
        assert got == want

    def test_stacked_ignores_leading_and_selected(self):
        from cpp_ptr_lab import components as C
        html = C.nav_shell("lab", self.ITEMS, style="stacked", leading=2, selected=2)
        assert "<p>a</p>" in html and "<p>b</p>" in html and "<p>c</p>" in html
        assert "type=\"radio\"" not in html and "font-style:italic" not in html

    def test_top_tabs_honors_selected(self):
        from cpp_ptr_lab import components as C
        html = C.nav_shell("lab", self.ITEMS, style="top_tabs", selected=2)
        # the third tab's radio is the checked one
        assert 'id="lab-t2" style=' in html and 'id="lab-t2"' in html
        import re
        checked = re.search(r'id="lab-t(\d)"[^>]*checked', html)
        assert checked and checked.group(1) == "2"

    def test_unknown_style_raises(self):
        from cpp_ptr_lab import components as C
        import pytest
        with pytest.raises(ValueError, match="unknown nav style"):
            C.nav_shell("lab", self.ITEMS, style="carousel")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestNavShell -q`
Expected: FAIL — `AttributeError: module 'cpp_ptr_lab.components' has no attribute 'nav_shell'`.

- [ ] **Step 3: Add `selected` to `variant_tabs`, then add `nav_shell`**

In `cpp_ptr_lab/components.py`, change the `variant_tabs` signature and its `checked` line. Signature:

```python
def variant_tabs(comp_id: str, panels: Sequence[tuple[str, str]], *, selected: int = 0) -> str:
```

Inside the multi-panel loop, change:

```python
        checked = " checked" if i == 0 else ""
```

to:

```python
        checked = " checked" if i == selected else ""
```

(The single-panel short-circuit added earlier needs no change — one panel has nothing to select.)

Add `nav_shell` immediately after `left_rail_layout`:

```python
def nav_shell(comp_id: str, items: Sequence[tuple[str, str]], *,
              style: str = "left_rail", leading: int = 0,
              selected: int | None = None) -> str:
    """Uniform nav over (label, body) items — one signature for every style.

    ``leading`` sets apart the first N reference entries (left_rail italicises
    them; other styles ignore it). ``selected`` picks the on-load panel
    (left_rail and top_tabs honour it; stacked ignores it). Unknown ``style``
    raises ValueError.
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestNavShell cpp_ptr_lab/tests/test_components.py -q`
Expected: PASS (nav_shell tests + all existing variant_tabs tests, which use the default `selected=0`).

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/components.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "feat(components): nav_shell uniform dispatch; variant_tabs selected arg" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: `build_layout` uses `nav_shell`; delete `_LAYOUTS` and the left_rail branch (Section A wiring)

**Files:**
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py` (remove `_stacked_layout` + `_LAYOUTS` at ~314-323; rewrite the nav-selection tail of `build_layout` at ~340-368)
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py` (already covered by the byte-identical guard + the g++-gated page tests)

- [ ] **Step 1: Write the failing test**

Add to `cpp_ptr_lab/yaml_engine/test_render_page.py`:

```python
class TestBuildLayoutNav:
    def test_layouts_dict_and_stacked_layout_are_gone(self):
        # The leaky per-style dispatch is removed; nav_shell is the single seam.
        from cpp_ptr_lab.yaml_engine import render_page as R
        assert not hasattr(R, "_LAYOUTS")
        assert not hasattr(R, "_stacked_layout")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestBuildLayoutNav -q`
Expected: FAIL — `assert not hasattr(R, "_LAYOUTS")` fails (it still exists).

- [ ] **Step 3: Remove `_stacked_layout` + `_LAYOUTS`; rewrite the nav tail**

In `cpp_ptr_lab/yaml_engine/render_page.py`, delete these lines (the helper and dict, ~314-323):

```python
def _stacked_layout(comp_id: str, items) -> str:
    """Fallback nav: stack every demo (no selector)."""
    return "\n".join(body for _label, body in items)


_LAYOUTS = {
    "left_rail": C.left_rail_layout,
    "top_tabs": C.variant_tabs,      # top tabs == variant_tabs (two-row via flex-wrap)
    "stacked": _stacked_layout,
}
```

In `build_layout`, delete the early style validation (the block that raises `unknown layout style`, ~340-343) — `nav_shell` validates now. Then replace the nav-selection tail (from `n = len(glossary_items)` through the `if style == "left_rail": … else: …` block, ~363-368) with:

```python
    n = len(glossary_items)
    nav = C.nav_shell("lab", items, style=style, leading=n,
                      selected=(n if n < len(items) else 0))
```

Note: this task keeps the existing `glossary_items` loop intact so the file stays runnable and today's pages stay byte-identical; Task 6 replaces that loop with `_build_sidebar` and renames `glossary_items` → `sidebar_items` in this same tail. The two tasks touch the same `build_layout`; if executing inline, committing them together is fine (noted at the bottom of this task).

- [ ] **Step 4: Run test + the byte-identical guard**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestBuildLayoutNav cpp_ptr_lab/yaml_engine/test_render_page.py::TestNavShell -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py
git commit -m "refactor(engine): build_layout dispatches via nav_shell; drop _LAYOUTS" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: `sidebar:` keyword-block parsing + Demonstration Concept; migrate 2 rail YAMLs (Section D)

**Files:**
- Modify: `cpp_ptr_lab/yaml_engine/render_page.py` (`build_layout`: replace the `glossaries` loop with a `sidebar` loop, ~349-361)
- Modify: `cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml`, `cpp_ptr_lab/op_overload/layouts/op_overload.rail.yaml`
- Test: `cpp_ptr_lab/yaml_engine/test_render_page.py`

- [ ] **Step 1: Write the failing tests**

Add to `cpp_ptr_lab/yaml_engine/test_render_page.py`. These test the `sidebar` parsing helper directly (no g++), so factor the loop into a helper `_build_sidebar(sidebar, base) -> list[(label, body)]` in Step 3:

```python
class TestSidebar:
    def test_mixed_glossary_and_concept_entries_in_order(self, tmp_path):
        from cpp_ptr_lab.yaml_engine import render_page as R
        g = tmp_path / "v.glossary.yaml"
        g.write_text("title: Vocab\nterms:\n  - {term: ptr, def: an address}\n", encoding="utf-8")
        sidebar = [
            {"concept": {"id": "obj", "text": "What this teaches."}},
            {"glossary": {"id": "g", "source": "v.glossary.yaml", "label": "Vocabulary"}},
        ]
        items = R._build_sidebar(sidebar, tmp_path)
        assert [label for label, _ in items] == ["Concept", "Vocabulary"]
        assert "What this teaches." in items[0][1] and "<details" not in items[0][1]
        assert "an address" in items[1][1]

    def test_unknown_sidebar_entry_raises(self, tmp_path):
        from cpp_ptr_lab.yaml_engine import render_page as R
        import pytest
        with pytest.raises(KeyError, match="unknown sidebar entry"):
            R._build_sidebar([{"legend": {"id": "x"}}], tmp_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py::TestSidebar -q`
Expected: FAIL — `AttributeError: module 'cpp_ptr_lab.yaml_engine.render_page' has no attribute '_build_sidebar'`.

- [ ] **Step 3: Add `_build_sidebar` and call it from `build_layout`**

In `cpp_ptr_lab/yaml_engine/render_page.py`, add:

```python
def _build_sidebar(sidebar: list, base: Path) -> list:
    """Turn a layout's ``sidebar:`` keyword-block list into (label, body) items.

    Each entry is a single-key mapping: ``glossary`` (loads a *.glossary.yaml)
    or ``concept`` (inline prose). Order is preserved (= rail order).
    """
    items = []
    for entry in sidebar or []:
        (kind, a), = entry.items()
        if kind == "glossary":
            gs = load_spec(Path(base) / a["source"])
            terms = [(t["term"], t["def"]) for t in gs.get("terms", [])]
            label = a.get("label", gs.get("title", "Glossary"))
            body = C.glossary(a.get("id", "glossary"), gs.get("title", "Glossary"), terms)
        elif kind == "concept":
            label = a.get("label", "Concept")
            body = C.concept_panel(a.get("id", "concept"), a["text"], title=label)
        else:
            raise KeyError(f"unknown sidebar entry type: {kind!r}")
        items.append((label, body))
    return items
```

In `build_layout`, replace the `glossary_items` loop (the `for g in spec.get("glossaries", []):` block, ~349-354) and the `items = list(glossary_items)` line with:

```python
    sidebar_items = _build_sidebar(spec.get("sidebar", []), base)
    items = list(sidebar_items)
```

Then in the nav tail (from Task 5), rename the count reference `n = len(glossary_items)` → `n = len(sidebar_items)`. After this, `glossary_items` no longer appears anywhere in the file.

- [ ] **Step 4: Migrate the two rail layouts to `sidebar:`**

Replace the `glossaries:` block in `cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml` with a `sidebar:` block that also adds a Demonstration Concept as the first entry:

```yaml
sidebar:
  - concept:  { id: obj,   text: "Pointers hold addresses; references are permanent aliases. This lab shows how each behaves, when the compiler stops you, and the classic gotchas." }
  - glossary: { id: g-ptr, source: ../glossaries/pointers.glossary.yaml,  label: "Vocabulary" }
  - glossary: { id: g-ref, source: ../glossaries/references.glossary.yaml, label: "Reference Terms" }
```

Replace the `glossaries:` block in `cpp_ptr_lab/op_overload/layouts/op_overload.rail.yaml` with (glossary-only, no demonstration concept — keeps that page byte-identical):

```yaml
sidebar:
  - glossary: { id: g-ops, source: ../glossaries/op_overload.glossary.yaml, label: "Vocabulary" }
```

- [ ] **Step 5: Run the non-g++ tests**

Run: `python -m pytest cpp_ptr_lab/yaml_engine/test_render_page.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cpp_ptr_lab/yaml_engine/render_page.py cpp_ptr_lab/yaml_engine/test_render_page.py cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml cpp_ptr_lab/op_overload/layouts/op_overload.rail.yaml
git commit -m "feat(engine): unified sidebar list (glossary/concept); demonstration concept" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Integration — rebuild pages, fix any stale assertions, full suite, visual check

**Files:**
- Possibly modify: any test asserting `class="callout"` on a demo/page (update to `class="concept"`)
- Test: whole suite; g++-gated page builds

- [ ] **Step 1: Find stale `callout` assertions in demo/page tests**

Run: `grep -rn "callout" cpp_ptr_lab --include=*.py | grep -i test`
Expected: review each hit. Tests for the standalone `basic_ptr`/`function_args` pages (which still use `callout_note`) stay as-is. Any test asserting a `callout` in a **rail demo** or op_overload page must change to `concept` (the disclosure). Update those assertions to match `class="concept"` / `>Concept</summary>`.

- [ ] **Step 2: Rebuild both rail pages (needs g++)**

Run:
```bash
python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml dist
python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/op_overload/layouts/op_overload.rail.yaml dist
```
Expected: exit 0, `Wrote dist/pointers_refs.rail/pointers_refs.rail.html` and `Wrote dist/op_overload.rail/op_overload.rail.html`.

- [ ] **Step 3: Assert the new structure landed**

Run:
```bash
grep -c "<details" dist/pointers_refs.rail/pointers_refs.rail.html   # example Concepts collapsed
grep -c ">Objective<\|Pointers hold addresses" dist/pointers_refs.rail/pointers_refs.rail.html  # demonstration concept entry
grep -c "class=\"callout\"" dist/pointers_refs.rail/pointers_refs.rail.html  # expect 0
```
Expected: first ≥ 8 (one collapsed Concept per example), second ≥ 1, third `0`.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest cpp_ptr_lab/ -q`
Expected: PASS. Count should be the prior 423 plus the new tests from Tasks 1–6 (roughly 423 → ~435). No failures.

- [ ] **Step 5: Visual check (serve over HTTP; `file://` is blocked for Playwright)**

Run: `python3 -m http.server -d dist 8123` (then open `http://localhost:8123/pointers_refs.rail/pointers_refs.rail.html`). Confirm: the rail shows *Objective* (or the demonstration concept label) + *Vocabulary* + *Reference Terms* as italic leading entries; each example panel opens with a collapsed "Concept" line that expands in place; the big always-open blue box is gone; op_overload page unchanged except its Vocabulary entry.

- [ ] **Step 6: Commit any test fixups**

```bash
git add -A cpp_ptr_lab
git commit -m "test(integration): update rail-demo assertions for collapsed Concept" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

(If Step 1 found nothing to change, skip this commit.)

---

### Task 8: Docs — document `nav_shell`, the `concept` block, and the `sidebar:` list

**Files:**
- Modify: `COURSE_VIA_TOPICS.md`, `usage/USAGE.md`, `cpp_ptr_lab/pointers_refs/YAML_GUIDE.md`
- Modify: `JOURNAL.md` (new entry, committed last)

- [ ] **Step 1: Update the authoring guides**

In `cpp_ptr_lab/pointers_refs/YAML_GUIDE.md` and `usage/USAGE.md`: replace any `- callout_note: { … label: Concept … }` example with `- concept: { id: …, text: "${x.explanation}" }`; replace the `glossaries:` layout example with the `sidebar:` keyword-block list (mixed `- concept:` / `- glossary:`); note `nav_shell` as the single nav interface and the locked vocabulary (demonstration / example / gotcha / concept). Keep all Markdown paragraphs single-line.

- [ ] **Step 2: Update the architecture note**

In `COURSE_VIA_TOPICS.md` §7 (Known gaps): mark gap #2 ("topic layout is a fixed recipe") progress and note the nav interface is now uniform via `nav_shell`; document the `sidebar:` list and the two Concept levels.

- [ ] **Step 3: Add a JOURNAL entry**

Prepend a dated entry to `JOURNAL.md` (newest first, `## YYYY-MM-DD HH:MM — …` header) summarizing: unified `nav_shell`; shared `_prose_box`; Example Concept as collapsed `<details>`; Demonstration Concept + `sidebar:` list; suite count; both pages rebuilt. Single-line paragraphs.

- [ ] **Step 4: Commit docs, then JOURNAL last**

```bash
git add COURSE_VIA_TOPICS.md usage/USAGE.md cpp_ptr_lab/pointers_refs/YAML_GUIDE.md
git commit -m "docs: nav_shell, concept block, and sidebar list; vocabulary" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git add JOURNAL.md
git commit -m "docs(journal): reusability seam — nav_shell, prose box, concept, sidebar" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-review notes (for the executor)

- **Byte-identical guards** are the safety net: Task 1 (`glossary` unchanged) and Task 4 (`nav_shell` left_rail == `left_rail_layout`). If either fails, the refactor changed output — stop and diff, do not "fix" the test.
- **op_overload page changes only where intended:** its example Concepts become collapsed `<details>` (Task 3) and its one glossary moves under `sidebar:` (Task 6), but it gains **no** demonstration concept — so its rail (1 leading glossary + 4 examples, `selected=1`) is structurally identical to today. The `nav_shell`/`glossary` byte-identical guards (component level) are the real losslessness proof.
- **Deviation from spec §3.B (confirmed by user):** the plan routes `glossary` + both Concept renderers through `_prose_box` but leaves `callout_note` untouched. `callout_note` stays a fully supported, backward-compatible YAML block (still in `_DISPATCH`) — authors can keep using `- callout_note: {...}` for an always-visible aside whenever they want. Only the *default* per-example Concept changes: the 12 existing demos switch to the collapsed `concept:` block. `callout_note` is neither removed nor deprecated.
- **Tasks 5 + 6 touch the same `build_layout` tail** — if executing inline, doing them as one commit is cleaner (noted in Task 5, Step 3).
