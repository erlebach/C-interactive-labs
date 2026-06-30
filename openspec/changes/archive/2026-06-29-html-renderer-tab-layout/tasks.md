<!--
  Applying memory rule feedback/testing.md: RED tests written BEFORE implementation.
-->

## 1. RED — new layout tests

- [x] 1.1 In `test_html_renderer.py`, add `TestAssemblePageTopicNav` class: assert topic radio inputs present, first checked, topic-panel divs present (`id="tp-{tid}"`), `.topic-nav` labels present, `height:100vh` and `overflow:hidden` in CSS, no topic nav when `topics=None`
- [x] 1.2 In `test_html_renderer.py`, add `TestAssemblePageBackwardCompat`: call `assemble_page([frag])` without `topics` kwarg; assert no `.topic-nav`, page still has `lang="en"` and skip link
- [x] 1.3 In `test_html_renderer.py`, add `TestRenderFragmentLayout`: assert `.tabs` div appears before `.panels` div in the fragment output; assert diagram column contains `display:flex` or `flex` in style/CSS
- [x] 1.4 Run new tests and confirm they FAIL for the right reason (functions not yet updated)

## 2. GREEN — `assemble_page` with topic navigation

- [x] 2.1 Add `topics: list[tuple[str, str]] | None = None` parameter to `assemble_page`; generate topic radio inputs (`id="t-{tid}"`, `class="vtopic"`, first `checked`) as first children of `<body>` when `topics` has ≥ 2 entries
- [x] 2.2 Generate `<nav class="topic-nav">` with one `<label for="t-{tid}">` per topic, wrapping with `flex-wrap: wrap`
- [x] 2.3 Wrap each fragment in `<div id="tp-{tid}" class="topic-panel">` inside `<main class="lab-content" id="main">`
- [x] 2.4 Generate per-topic CSS `:checked` rules: `#t-{tid}:checked ~ .lab-content #tp-{tid} { display: flex; flex-direction: column; }` and active-tab label styling
- [x] 2.5 Rewrite `_CSS` for the no-scroll viewport layout: `body { height:100vh; overflow:hidden; display:flex; flex-direction:column; }`, compact header, `.lab-content { flex: 1 1 0; overflow:hidden; }`, `.topic-panel { display:none; height:100%; }`, diagram column flex rules, font-size 16px body

## 3. GREEN — `render_fragment` layout restructure

- [x] 3.1 Restructure `_panel_body` to output `<div class="panel-grid">` with `.code-col` (`overflow-y:auto`) and `.diagram-col` (`display:flex; flex-direction:column`); `<figure>` gets `flex:1 1 0; min-height:0`; SVG gets `width:100%; height:100%; min-height:0`
- [x] 3.2 Move the topic explanation to a compact `.topic-header` div above the variant tabs row (inside `render_fragment`); keep `<h2>` but reduce prominence
- [x] 3.3 Ensure `.panels` div gets `flex: 1 1 0; min-height: 0` in the CSS so it fills remaining height within the topic panel

## 4. GREEN — `build_html.py` wiring

- [x] 4.1 In `build_lab`, pass `topics=[(t.id, t.name) for t in topics]` to `assemble_page` for the lab combined file; leave per-topic `assemble_page` call unchanged (no `topics` kwarg)

## 5. Verification

- [x] 5.1 Run the full `cpp_ptr_lab` test suite and confirm all tests green (existing 98 + new layout tests)
- [x] 5.2 Rebuild `dist/` with `python -m cpp_ptr_lab.build_html` and visually verify in browser: topic tabs at top wrap over two rows, clicking a tab shows only that topic, diagram is large, no outer scroll
- [x] 5.3 Spot-check per-topic standalone file (e.g. `dist/topics/basic_ptr.html`): no topic nav bar, variant tabs at top, diagram fills column
