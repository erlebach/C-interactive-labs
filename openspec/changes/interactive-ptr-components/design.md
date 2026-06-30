## Context

The pointer lab has migrated from DearPyGui to static HTML for WCAG AA compliance
(`LESSONS_LEARNED_2026-06-29_22h11mEST.md`). The HTML pages are accessible but static,
adding little over `cppreference` (TODO.md:7-10). We want the didactic interactivity the
DPG app had, but under the migration's hard constraints: **zero JS, zero network, fully
self-contained, Canvas-pasteable**. The existing renderer (`html_renderer.py`) is already
**pure** (dict/str in, str out — no I/O, no subprocess), which makes per-component unit
testing without g++ possible. The build (`build_html.py`) owns all g++ I/O and the bake.

Rather than retrofit interactions onto 15 topic pages, build each page-element type once as
a reusable component, demo it in isolation, and assemble topic pages later from the catalog.

## Goals / Non-Goals

**Goals:**
- A catalog of 10–15 pure, accessible, zero-JS component renderer functions.
- One standalone Canvas-pasteable demo page per component + a browsable index.
- A single semantic color language shared by prose, code, and SVG, all ≥4.5:1, color-never-alone.
- TDD: a RED unit test precedes every component (renderer is pure → no compiler in tests).
- Preserve all existing behavior; additions only (existing 130 tests stay green).

**Non-Goals:**
- No JavaScript, no runtime computation, no network — interactivity is baked-state + CSS only.
- No keyframe animation in this change (deferred; adds reduced-motion surface for least gain).
- Not assembling finished topic pages yet — that consumes the library in a later change.
- Not porting the remaining TODO.md topics (initializers, stack frames, …) here.

## Decisions

**D1 — Components are pure functions returning fragment strings, id-namespaced by a caller
component id.** Mirrors the existing renderer contract, so components are unit-testable
without g++ and compose into one document. *Alternative:* a templating/Jinja layer —
rejected: adds a dependency and an impure I/O surface for no gain over f-strings, which the
codebase already uses.

**D2 — Interactivity = pre-baked states switched by CSS** (`:checked` for toggles/quizzes,
`:hover`/`:focus-within` for linking, `<details>` for stepped reveals, `:target` where an
anchor fits). This is the only interactivity model that survives Canvas (which strips
`<script>` and blocks `fetch`). *Alternative:* progressive-enhancement JS — rejected: Canvas
removes it, so the baseline must already be complete; JS would be dead weight.

**D3 — Keyboard/SR accessibility comes from native controls, not ARIA-JS.** Radios give
arrow-key roving, Space-select, focus, and correct SR semantics for free; `<details>` is
natively operable. Hidden state-driving radios are hidden by **clip/off-screen, never
`display:none`** (which drops focus order). *Alternative:* ARIA tablist/tabpanel with JS —
rejected: more code, more ways to get a11y wrong, dies in Canvas.

**D4 — One semantic color token set in `:root`, reused verbatim in the SVG palette.**
`--c-addr` (blue `#0b5394`), `--c-val` (green `#0b7d3e`), `--c-type` (purple `#6b3fa0`),
`--c-const` (amber `#9a6700`), `--c-err` (red `#b00020`) — all ≥4.5:1 on white. A blue
address in the code is a blue box in the diagram. Every colored meaning is redundant with
text/border/icon (WCAG 1.4.1). *Alternative:* decorative/per-component palettes — rejected:
inconsistent color teaches nothing and risks failing contrast.

**D5 — Gallery emits one standalone demo page per component + an index**, baking real g++
output where the component shows output. The component fragment is the atomic unit; demo
pages and (later) topic pages are both assembled from fragments — marginal cost. *Alternative:*
one big gallery page — rejected: harder to paste a single component into Canvas and noisier
to review in isolation.

**D6 — New code lives alongside existing modules, additive.** A component module of pure
render functions next to `html_renderer.py`; gallery orchestration next to `build_html.py`.
The variant/`cases` contract and topic rendering are untouched.

**D7 — TDD order, RED before GREEN, tests-before-impl** (overrides OpenSpec's default
tests-last task ordering, per `~/.claude/memory/feedback/testing.md`). Shared invariants
(purity, id-namespacing, zero-JS, color-not-alone) get cross-component tests applied to
every component via parametrization.

## Risks / Trade-offs

- **15 components is a large surface for one change.** → Front-load the 3 shared-invariant
  tests + the 3 highest-value components (hover-link, before/after, predict-reveal) as the
  proof; the remaining components follow the identical pure-function + namespaced-id template,
  so each is cheap and independently testable. Tasks are ordered so value lands early.
- **CSS-only state can leak across instances** (the original `:checked` cross-contamination
  bug). → Mandatory per-instance id namespacing + CSS-id sanitisation, enforced by a shared
  test rendering two instances in one document and asserting no id collision.
- **Hidden radios hidden with `display:none` drop keyboard focus.** → Shared test asserts
  state-driving inputs use clip/off-screen, not `display:none`.
- **Contrast regressions when picking colors.** → Tokens chosen ≥4.5:1; a test asserts the
  documented contrast for each token against the background.
- **Scope creep into topic assembly.** → Explicit Non-Goal; this change ends at the catalog
  + gallery.

## Migration Plan

Purely additive — no migration. New modules and a new gallery build target; existing
`dist/` topic/lab output and all current tests are unaffected. Rollback = delete the new
module + gallery target; nothing else depends on them.

## Open Questions

- Final module/file name for the component library (resolved during apply; pure-function
  module beside `html_renderer.py`).
- Whether `code-line-link` and `byte-grid` share the SVG-coordinate helper with
  `memory-diagram` or get their own — decide when implementing `memory-diagram` first.
