## Context

`html_renderer.py` was implemented in the `cpp-ptr-lab-static-html` change. Its
`assemble_page` function currently stacks all topic `<section>` elements vertically,
producing a single long scrolling page. The memory diagram SVG is displayed with
`width: 100%; height: auto`, which on a typical laptop (1366 × 768) renders it at
roughly 400 × 130 px — too small to read. Students must scroll to find the topic
they want and the diagram adds little visual value at that size.

The fix is entirely within `html_renderer.py` (one file, ~300 lines). `build_html.py`
needs a one-line change to pass topic metadata to `assemble_page`.

## Goals / Non-Goals

**Goals:**
- Topic navigation tabs at top of page, one per topic, wrapping to a second row if needed.
- Clicking a tab shows that topic's content and hides all others — zero JS.
- Variant-type tabs (int / double / float) appear immediately above the content area for the selected topic.
- Memory diagram SVG fills the right column's full available height, making it much larger.
- Body has `height: 100vh; overflow: hidden` — no outer-page vertical scroll. Only the code column scrolls internally when content is long.
- Font sizes legible: body 16 px, variant-tab labels 15 px bold, code/output 14 px monospace, topic-tab labels 14 px bold.
- Backward compatibility: `assemble_page(fragments)` called without `topics` continues to work (no topic nav bar, wraps content in main).

**Non-Goals:**
- Changes to the SVG coordinate space / viewBox geometry.
- Changes to `build_html.py` orchestration beyond passing `topics` kwarg.
- Changes to `topics.py`, `code_generator.py`, `compiler_runner.py`, or test fixtures other than new test assertions.
- JavaScript-based interactions.

## Decisions

### D1: Topic radio inputs before `<header>` in the DOM

The CSS sibling combinator (`#t-basic_ptr:checked ~ .topic-nav label[for="t-basic_ptr"]`)
requires the radio to be an earlier sibling of both the topic-nav and the main content.
Placing topic radios as the very first children of `<body>`, before `<header>`, satisfies
this without any JS.
**Alternative considered:** Putting radios inside `<main>`. Rejected — the `:checked ~`
combinator cannot reach ancestors, only later siblings.

### D2: `assemble_page` gets optional `topics` parameter (not a new function)

Signature: `assemble_page(fragments, title="...", topics: list[tuple[str,str]] | None = None)`.
When `topics` is `None` or a single-entry list, no topic nav is generated (backward compat).
**Alternative considered:** A new `assemble_lab_page` function. Rejected — two functions
sharing 90 % of their body is worse than one function with a conditional.

### D3: `render_fragment` keeps the `<section class="topic" id="{tid}">` outer wrapper

`assemble_page` wraps each fragment in `<div id="tp-{tid}" class="topic-panel">` (distinct
prefix `tp-`) so the CSS hides/shows the outer div while the inner section retains its id
for skip-link and landmark purposes. No id collision since `"tp-basic_ptr" ≠ "basic_ptr"`.
**Alternative considered:** Removing the outer section from `render_fragment` entirely.
Rejected — breaks existing tests and removes the semantic landmark role.

### D4: SVG fills column height via flex, no viewBox changes

The diagram column is a flex column (`display: flex; flex-direction: column`). The
`<figure>` inside it gets `flex: 1 1 0; min-height: 0`. The SVG gets `width: 100%;
height: 100%; min-height: 0`. With `preserveAspectRatio="xMidYMid meet"` (SVG default),
the SVG letter-boxes within the column — on a 1366 × 768 screen the diagram renders at
roughly 600 × 200 px, versus the previous 400 × 130 px. No coordinate-space edits needed.
**Alternative considered:** Changing viewBox to `0 0 500 300` and repositioning elements.
Rejected — higher risk, more code, same visual result from the layout change alone.

### D5: TDD ordering preserved (feedback/testing.md rule)

RED tests written before implementation, per the user-confirmed TDD constraint from
`feedback/testing.md`. New tests cover: topic tab generation, topic panels hidden/shown,
backward compat (no topics arg), diagram-column flex CSS present, no-scroll body CSS.

### D6: `build_html.py` passes `topics` for lab files, `None` for per-topic files

```python
# build_lab (lab HTML — add topics kwarg)
topic_meta = [(t.id, t.name) for t in topics]
lab_html = assemble_page(all_fragments, title=..., topics=topic_meta)

# per-topic file — unchanged (topics=None → no nav bar)
per_topic_html = assemble_page([fragment], title=topic.name)
```

## Risks / Trade-offs

- CSS `height: 100vh` on `body` breaks if the page is embedded in an `<iframe>` with a fixed height set by the host (Canvas). The `<iframe>` will scroll its own viewport while the body tries to fill 100 vh. **Mitigation:** canvas embeds per-topic standalone files (single fragment); the topic nav bar is not present in those files, so the scrolling issue is moot — the single-topic layout can safely remain `height: auto` (no outer scroll because there is only one topic). Only the lab combined files use `100vh`.
- Topic radio inputs as first children of `<body>` are slightly unusual HTML. Screen readers encounter them first; they are `aria-hidden="true"` (added) so they are invisible to AT. The visible labels in the nav bar are what AT reads. **Already handled by the existing `.vtopic` class.**
- `height: 100vh` on mobile may conflict with browser chrome. **Mitigation:** `height: 100dvh` fallback not needed for the lab's desktop target audience. Noted as a known limitation.

## Migration Plan

1. Write RED tests in `test_html_renderer.py` for the new layout.
2. Implement changes in `html_renderer.py`.
3. Add `topics` kwarg to `assemble_page` call in `build_html.py`.
4. Run full test suite green.
5. Rebuild `dist/` and visually verify in browser.
6. No rollback needed — additive change, `dist/` is a derived artifact.

## Open Questions

- None blocking. Tab wrapping to two rows happens naturally with `flex-wrap: wrap` on `.topic-nav`.
