<!--
  Applying memory rule feedback/testing.md: overriding OpenSpec's default
  tests-last ordering. RED tests are written BEFORE the implementation they
  cover, per the user-confirmed TDD plan (2026-06-29).
-->

## 1. Scaffolding

- [x] 1.1 Create `cpp_ptr_lab/html_renderer.py` and `cpp_ptr_lab/build_html.py` as empty modules with docstrings and function stubs (`svg_renderer`, `render_fragment`, `assemble_page`; build entry point)
- [x] 1.2 Create `cpp_ptr_lab/tests/test_html_renderer.py` and `cpp_ptr_lab/tests/test_build_html.py`

## 2. RED — renderer tests (write failing tests first)

- [x] 2.1 `test_svg_renderer`: raw → two `<rect>` + arrow + addresses + value + `<title>`/`<desc>` + `role="img"`; null → NULL box; missing keys → safe `?` placeholders; unique/shared/weak dispatch to their diagrams
- [x] 2.2 `test_render_fragment`: one radio+panel per variant; first variant `checked`; all ids/names/`for`/selectors prefixed by topic id; single-variant topic emits no radios
- [x] 2.3 `test_assemble_page`: combined page contains all fragments, `<html lang=...>`, skip link, no duplicate ids, CSS inlined, no external script/style/network references
- [x] 2.4 Run the renderer tests and confirm they FAIL for the right reason (functions not yet implemented)

## 3. GREEN — renderer implementation

- [x] 3.1 Implement `svg_renderer(ptrdata)` porting the six DPG `_draw_*` methods to inline SVG in `viewBox="0 0 500 160"` with `<title>`/`<desc>`/`role="img"` and `?` fallbacks for missing keys
- [x] 3.2 Implement `render_fragment(topic, variants)`: zero-JS `:checked` radio pattern, topic-id namespacing, first variant `checked`, single-variant short-circuit
- [x] 3.3 Implement `assemble_page(fragments)`: WCAG AA document shell (light high-contrast theme, 44px targets, visible focus, skip link, `lang`), inlined CSS, no id collisions
- [x] 3.4 Run renderer tests to green

## 4. RED — build orchestration tests

- [x] 4.1 `test_build_html`: a successful variant captures parsed `PTRDATA` + `MEMBYTES` + stdout + source; a compile-failure variant (e.g. `ref_must_bind`) captures compiler stderr and is marked failed
- [x] 4.2 `test_build_html`: build emits one `dist/topics/<id>.html` per topic AND one `dist/lab_<lab>.html` per lab from the same fragments; missing `g++` fails loudly (no silent/empty output)
- [x] 4.3 Run build tests and confirm they FAIL for the right reason

## 5. GREEN — build implementation

- [x] 5.1 Implement variant expansion from each topic's categorical controls (drop free-text controls; no-control topics → single variant)
- [x] 5.2 Implement per-variant capture: `generate_source` → `compiler_runner` compile+run → parse via reused `parse_ptrdata`/`parse_membytes`; branch on compile-failure to keep stderr
- [x] 5.3 Implement dual output emission (`dist/topics/*.html` and `dist/lab_*.html`) from shared fragments, with loud failure when `g++` is unavailable
- [x] 5.4 Run build tests to green

## 6. Verification

- [x] 6.1 Run the full `cpp_ptr_lab` test suite (existing + new) and confirm green; confirm `parse_*`/`generate_source` were not re-tested
- [x] 6.2 Build `dist/` for both labs and visually verify a per-topic file and a per-lab combined file in a browser (variant switching by keyboard, focus visible, SVG announced)
- [x] 6.3 Spot-check a per-topic file pasted into Canvas (zero-JS variant switching still works)
