# opencode — Journal

Chronological log of features, bug fixes, and architectural decisions.

## 2026-06-30 14:00 — Interactive component library + gallery (OpenSpec: interactive-ptr-components)

Built a catalog of **15 pure, accessible, zero-JS page-element components** in a new
`cpp_ptr_lab/components.py` (beside `html_renderer.py`, additive — existing 130 tests
untouched), plus a `cpp_ptr_lab/gallery.py` build target that emits one standalone,
Canvas-pasteable demo page per component + an index into `dist/gallery/` (16 files,
zero external/script/network refs). Components: `page_shell`, `color_legend`,
`callout_note`, `memory_diagram`, `hover_link_diagram`, `before_after_toggle`,
`predict_reveal_quiz`, `compile_status_badge`, `output_console`, `byte_grid`,
`code_line_link`, `variant_tabs`, `code_diagram_panel`, `stacked_subcases`,
`progressive_steps`. Interactivity is baked-state + CSS only (`:checked`, `:hover`,
`:focus`, `<details>`) — survives Canvas's `<script>`/`fetch` stripping; native controls
give keyboard/SR a11y; state-driving radios hidden by clip (never `display:none`).
Added a single-source **semantic color palette** `SEMANTIC_PALETTE` in `html_renderer.py`
(`--c-addr/val/type/const/err`, all ≥4.5:1 on white — amber tightest at 4.87:1), injected
into the theme `:root` and reused verbatim by the SVG palette so chrome and diagrams share
one contrast-vetted language; color is always redundant with text + border/icon.
TDD throughout (RED before GREEN, per feedback/testing.md): parametrized shared-invariant
tests (purity, id-namespacing, CSS-id-safety, zero-JS/network, focus-preservation,
color-not-alone) run across every registered component; the gallery bakes **real
g++-captured** stdout/stderr and fails early if `g++` is missing. Suite: **312 passed**
(130 prior + 177 component + 5 gallery). Ready for `/opsx:verify` → archive.

## 2026-06-29 22:19 — Lessons-learned analysis + session handoff

Produced two reference artifacts (no code change). `LESSONS_LEARNED_2026-06-29_22h11mEST.md`
(repo root): synthesized from a parallel deep read of the DPG interface (`app_base.py`) and the
HTML/build pipeline — HTML-page idioms, a WCAG AA technique→success-criterion table, the
build-time bake architecture, the DPG accessibility limitations (architectural, why migration was
necessary), pitfalls (CSS-unsafe ids, stringified bools, duplicate SVG ids, panel scroll), and a
quick-start checklist. `handoffs/HANDOFF_2026-06-29_22h19mEST.md`: focus = apply the multi-sub-case
`cases` pattern to remaining gotcha topics + the deferred vetted-C++ diff; references, locked
decisions, constraints, suggested skills. No tests affected (130 still green).

## 2026-06-29 22:03 — Leave diagram column empty when there is no diagram

No-data cases (compile-failed sub-cases, `has_ptrdata=False` topics) drew a placeholder SVG
box "type=? — no diagram" under a "Memory diagram" heading — visual noise that appeared next
to every forbidden `const_taxonomy` cell. Now `_case_block` emits an empty
`<div class="diagram-col diagram-col--empty">` (no heading/figure/caption) when
`ptrdata` is present-but-empty; cases with real pointer data are unchanged, as are legacy
pre-rendered-svg variants. TDD: `TestNoDiagramLeavesEmptySpace`. Recorded + archived as
OpenSpec `2026-06-30-empty-diagram-when-absent` (ADDED requirement on `static-html-renderer`).
Suite: **130 passed**; `dist/` rebuilt → 0 placeholders; `const_taxonomy` = 4 empty + 4 real
diagram columns; 0 active changes.

## 2026-06-29 21:35 — Fix multi-case panel scroll regression

The multi-sub-case panels stacked two `.panel-grid`s inside `.panel`, but `.panels` is
`overflow:hidden` and `.panel` never scrolled — so `const_taxonomy`/`weak_cycle` clipped
their second sub-case with no scrollbar (single-case fit because code scrolls inside
`.code-col`). Fix (CSS only): `.panel { overflow-y:auto }`, plus `.case .panel-grid {
height:auto }` and `.case` diagram `min-height:200px` so each stacked sub-case keeps a
usable diagram height; single-case unaffected. TDD: `test_multicase_panel_scrolls`.
Recorded + archived as OpenSpec change `2026-06-30-multicase-panel-scroll` (ADDED
"Stacked sub-cases remain scrollable" to the `multi-subcase-panels` capability). Suite:
**126 passed**; `dist/` rebuilt; 0 active changes.

## 2026-06-29 20:50 — Multi-sub-case panels, const-taxonomy redesign, two bug fixes, OpenSpec reconciliation

Static-HTML C++ ptr lab. Two root-caused bug fixes: blank variant panels (CSS-unsafe
`(`/`)`/`,` in element ids broke the `:checked ~` selector) and a bare `False` in generated
C++ (checkbox default stringified instead of resolving via `value_map`). Added a reusable
**multi-sub-case panel** capability — one panel holds N independently-compiled cases, each
with its own code/verdict/output/diagram; failing cases get a red-bordered output box.
Applied it to redesign `const_taxonomy` from 4 inert near-identical programs into the real
const **2×2 truth table** (type × {write, rebind}) with authentic g++ errors. Then
reconciled OpenSpec: archived two stale-but-implemented changes and authored+archived
`2026-06-29-multi-subcase-panels` recording the capability plus both fixes as spec
invariants. All work TDD (RED→GREEN). Suite: **125 passed**; `dist/` rebuilt; `openspec
validate --specs` → 11 passed; 0 active changes.

### Details

**Bug fixes (regression-tested):**
- *Empty panels* — `_vid` left `(` `)` `,` in ids; unescaped these are CSS `#id`-selector
  errors (`(` parse error, `,` splits selector), silently dropping `:checked ~ .panels`
  for `const_taxonomy`/`weak_cycle`. Fix: map non-`[A-Za-z0-9_-]` → `_`. Test:
  `test_ids_are_css_safe_with_punctuated_labels`.
- *Bare `False`* — `expand_variants` seeded checkbox defaults via `str(ctrl.default)` →
  `"False"`, bypassing `_resolve_control_value`'s bool branch + lowercase `value_map` →
  undeclared identifier (compile failure on `const_taxonomy`/`ref_const`). Fix: preserve
  the default's type. Test: `test_checkbox_default_false_resolves_via_value_map`.

**Feature — multi-sub-case panels (additive, backward-compatible):** `CaseDef(label, subs)`
+ `TopicTemplate.cases`; `generate_source(extra_subs=)`; `capture_variant` compiles one
program per case (`_compile_one` extracted); `_panel_body` renders per case (`_case_block`
extracted, unique svg-id prefix `-c{j}`); failing case adds `.out--err` (2px red border).

**Content — `const_taxonomy`:** 4 type tabs (`<<decl>>`) × 2 ops (`*ptr=99` / `ptr=&other`)
compiled independently; `int other = 7;` added; `mutate` checkbox dropped; explanation
rewritten around the two const axes. Truth table verified by
`test_lab1_const_taxonomy_truth_table` (real g++, no `-Werror` so unused `other` is fine).

**OpenSpec reconciliation:** archived `cpp-ptr-lab-static-html` + `html-renderer-tab-layout`
(fixed a `SHALL`-on-second-line parser error in the latter). Authored+archived
`2026-06-29-multi-subcase-panels`: new `multi-subcase-panels` capability (5 reqs) + ADDED
invariants on `static-html-renderer` (CSS-safe ids) and `static-html-build` (bool default
resolution).

## 2026-06-28 21:28 — Project initialized

- Project created at `/Users/erlebach/src/2026/isc5305_f2026/opencode`
