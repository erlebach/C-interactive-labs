## Why

The current static HTML output stacks all topics in a single scrolling page and displays the memory diagram at a fixed small height (~130 px), making it hard to read and forcing students to scroll through unrelated topics to find the one they need.

## What Changes

- `assemble_page` gains a `topics: list[tuple[str, str]] | None` parameter; when supplied, it generates a topic-navigation tab bar (one label per topic) using the zero-JS CSS `:checked` pattern so only the selected topic's content is visible at a time.
- `render_fragment` output is restructured so variant-selection tabs appear at the top of the topic panel (above the code/diagram grid), and the diagram column stretches to fill the full viewport height.
- The global CSS in `_CSS` is rewritten for a no-outer-scroll viewport layout (flex column, `height: 100vh`, `overflow: hidden` on `body`); only the code column scrolls internally when content is long.
- Font sizes are reviewed and set to legible values throughout (body ≥ 16 px, code 14 px, SVG labels proportional to a larger display area).
- `build_html.py` passes `topics=[(t.id, t.name) for t in topics]` to `assemble_page` for lab files; per-topic standalone files pass `topics=None` (no nav bar needed since there is only one topic).
- No changes to `build_html.py` logic, `topics.py`, `code_generator.py`, or `compiler_runner.py`.

## Capabilities

### New Capabilities

- `tab-layout-renderer`: Layout requirements for the static HTML renderer — topic-level tab navigation, viewport-filling diagram column, no-scroll body, and legible font scale.

### Modified Capabilities

*(none — `static-html-renderer` and `static-html-build` specs are in the completed `cpp-ptr-lab-static-html` change, not in global `openspec/specs/`; the layout changes are additive and do not break the existing renderer contract)*

## Impact

- `cpp_ptr_lab/html_renderer.py` — primary change file.
- `cpp_ptr_lab/build_html.py` — one-line change: pass `topics` kwarg to `assemble_page` in `build_lab`.
- `cpp_ptr_lab/tests/test_html_renderer.py` — existing tests all pass unchanged; new tests cover tab-nav and viewport layout assertions.
- `dist/` output files are regenerated after the build but are derived artifacts, not source.
