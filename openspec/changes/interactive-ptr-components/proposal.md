## Why

The current static-HTML pointer lab is accessible (WCAG AA) but **static** — it
adds little over `cppreference` because it dropped the interactivity that made the
original DearPyGui app didactic (TODO.md:7-10). Rather than bolt interactions onto
15 topic pages one at a time, we build each interactive page-element **once** as a
reusable, independently-demoed component. Inverting the work this way (N components
proven once, instead of 15 topics × N interactions) gives us a vetted **component
library** to assemble future topic pages from, and a gallery to review each
interaction in isolation.

## What Changes

- Add a catalog of **10–15 CSS-only, zero-JS, accessible page-element components**,
  each a pure renderer function returning a self-contained HTML fragment. Every
  component is demoed on pointer content. Initial catalog:
  - **Structure:** `page-shell` (skip-link + landmarks + `lang`), `variant-tabs`
    (radio `:checked` switcher), `code-diagram-panel` (two-column split),
    `stacked-subcases` (2×2 truth-table panel).
  - **Diagram:** `memory-diagram` (static SVG), `hover-link-diagram` (hover lights
    target + arrow in a shared color), `before-after-toggle` (2-state SVG switch),
    `byte-grid` (little-endian MEMBYTES grid), `code-line-link` (hover a source line
    ↔ highlight its diagram box).
  - **Feedback/output:** `compile-status-badge` (pass/fail by text+border+color),
    `output-console` (stdout, with error variant), `predict-reveal-quiz` (radio
    answer → reveal real g++ output + ✓/✗), `progressive-steps` (`<details>` reveal
    sequence).
  - **Chrome:** `color-legend` (semantic key), `callout-note` (pedagogical aside).
- Add a **component gallery build**: one standalone, Canvas-pasteable demo page per
  component, plus an index page. Each demo shows the rendered component, its
  accessible behavior, and (where relevant) real baked g++ output. Components are the
  atomic unit; pages assemble later.
- Extend the renderer's semantic **color system**: per-role `:root` tokens
  (`--c-addr`/`--c-val`/`--c-type`/`--c-const`/`--c-err`, all ≥4.5:1 on white) reused
  identically in prose, code, and SVG. Color is always redundant with text/shape/icon
  (never color-alone — WCAG 1.4.1).
- Interactivity is limited to **static baked states switched by CSS** (`:checked`,
  `:hover`, `:target`, `<details>`). No JS, no network, no animation in the initial
  catalog (keyframe motion deferred — adds reduced-motion surface for least core gain).

## Capabilities

### New Capabilities
- `interactive-components`: A library of pure, accessible, zero-JS renderer functions —
  one per page-element type — each producing a self-contained, id-namespaced HTML
  fragment with WCAG AA semantics (keyboard, screen-reader, contrast, color-not-alone).
- `component-gallery`: A build target that emits one standalone demo page per component
  plus an index, so each interaction is reviewable in isolation and reusable for later
  page assembly.

### Modified Capabilities
- `static-html-renderer`: The theme's `:root` color tokens gain a semantic per-role
  palette (address/value/type/const/error) that is reused unchanged in the SVG diagram
  palette, so chrome and diagrams share one contrast-vetted color language.

## Impact

- **Code:** new renderer functions added alongside `html_renderer.py` (pure, unit-
  testable without g++); new gallery build orchestration alongside `build_html.py`.
  Existing topic rendering and the variant/`cases` contract are unchanged (additive).
- **Tests:** new RED-first unit tests per component (renderer is pure → no compiler
  needed); gallery build covered by an integration test. Existing 130 tests unaffected.
- **Build deps:** g++ still build-only; no new runtime dependency. Output stays fully
  static and Canvas-embeddable.
- **Docs:** component catalog becomes the reference vocabulary for migrating the
  remaining TODO.md topics (initializers, stack frames, class special members, etc.).
