# opencode — Journal

Chronological log of features, bug fixes, and architectural decisions.

## 2026-07-01 18:47 — Demos & layouts system built (data-over-code); left-rail + top-tabs pages

Executed the 10-task demos/layouts plan end-to-end via **subagent-driven development** (fresh implementer
per task; spec+quality review on the substantive ones). The **data-over-code North Star holds**: the whole
Pointers & References lab now renders as *one standalone page where one demo shows at a time*, and authoring
it added **only YAML — zero per-demo Python**. Engine stays a thin fixed core — `render_fragment` split from
`render_page`; `_build_topic` reduced to a one-line adapter over a new reusable `demo_panel`; new `glossary`
+ `left_rail_layout` components; `build_layout` composes N demo fragments under a chosen nav `style:` + a
once-rendered `header:` (legend + shared glossary from `*.glossary.yaml`), CLI-routed on the `demos:` key.
Content is data: 8 `*.demo.yaml`, one `pointers.glossary.yaml`, two layouts (`.rail`=left_rail phase a,
`.tabs`=top_tabs phase b) — the second is a **one-file, zero-Python** style swap over the *same* demos.
**Open decision resolved: full class-namespacing** (not child combinators) — every structural class carries
its component id (`.vt-panel-{p}`, `.lr-panel-{p}`), so nested `variant_tabs` can't bleed. Suite **357 →
381** (24 new tests, TDD RED→GREEN throughout). Branch `feat/demos-and-layouts` (12 commits, not yet merged).

### Details

- **Build:** `python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml`
  (and `…/pointers_refs.tabs.yaml`) → `dist/<stem>/<stem>.html`.
- **Nesting-safety proof (tabs page):** outer top-tabs nav uses comp-id `lab` → `vt-*-lab`; inner demos use
  `vt-*-bp/ct/…` — disjoint class sets, **0 duplicate ids** across 162 ids.
- **WCAG 1.1.1 (asserted test) verified on both built pages:** 19 `<svg>` = 19 `role="img"`, non-empty
  `<title>`, no `<img>` without `alt`. Both self-contained: 0 `<script>`, 0 `https://`, real baked g++
  output (30× `PTRDATA`, const `read-only` error ×2).
- **Final polish (2-reviewer consensus):** `build_layout` now raises a friendly `ValueError` listing valid
  styles on an unknown `style:` (fail-fast before g++), instead of a raw `KeyError`.
- **Deferred (non-goals):** move C++ source Python→YAML; unify the old standalone basic_ptr/function_args
  pages; add `references.glossary.yaml`; clean the base-CSS `100vh/overflow:hidden` holdover in
  `html_renderer.py` (currently overridden by `page_shell`, harmless).

## 2026-07-01 14:57 — Design spec + implementation plan: demos & layouts (no code yet)

Brainstormed and specced a **data-over-code** restructuring: separate reusable **demos** (demo = one
whole topic) from **layouts** (author-chosen subset of demos + a `header:` rendered once + a nav
`style:`), with **glossaries** as reusable minimal YAML the author attaches per subset (no built-in
"family"). North Star: authoring content adds **YAML, never Python**. Two artifacts written + committed,
**no implementation code yet**: `docs/superpowers/specs/2026-07-01-demos-and-layouts-design.md` (design,
WCAG 1.1.1 text-alts made a tested requirement) and `docs/superpowers/plans/2026-07-01-demos-and-layouts.md`
(10 TDD tasks: fragment split, `glossary`/`demo_panel`/`left_rail_layout` components, layout loader + CLI
routing, 8 YAML demos + glossary + left-rail page [phase a], nesting-safe `variant_tabs` + top-tabs page
[phase b]). Plan self-review caught a real nested-`variant_tabs` CSS-bleed bug (Task 9 fixes it via child
combinators; open decision: adopt full class-namespacing instead). Also: `README.md` added (`fb4aa12`);
two global feedback memories (plain-language, reporting-python-commands). Handoff:
`handoffs/HANDOFF_2026-07-01_14h57mEST.md`. Suite unchanged at **357 passed** (no code touched). Next:
user picks execution mode (subagent-driven vs inline) after `/clear`, then execute the plan RED→GREEN.

## 2026-07-01 10:39 — Combined Pointers & References lab page (new-engine equivalent of the old lab file)

Rebuilt the old `dist/lab_pointers_refs.html` (the whole basic-pointers lab on one page) using the YAML
engine — no new engine code, pure composition. Added `cpp_ptr_lab/pointers_refs/pointers_refs.page.yaml`:
one page that bakes 7 topics (`basic_ptr`, `const_taxonomy`, `ref_must_bind`, `ref_no_null`,
`ref_rebind_illusion`, `ref_const`, `null_deref`) and stacks a heading + concept callout + `topic` block
per demo. Each `topic` block is a variant_tabs cluster over that topic's baked variants — so basic_ptr
shows int/double/float tabs and const_taxonomy shows its 4 declaration types, each with the 2×2 stacked
sub-cases (real g++ `read-only` error) now that gap 1 is wired. `pointers_refs/` becomes a uniform subject
package (adds the page spec + `test_pointers_refs.py`). Builds to `dist/pointers_refs/pointers_refs.html`
(81 KB, self-contained, no duplicate ids across all 7 topics). TDD: 7 RED-first build tests. Suite **357
passed** (350 + 7). Build: `python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/pointers_refs.page.yaml`.

## 2026-07-01 10:15 — Engine gap 1: wire cases-topics through the YAML engine

Closed the first known engine gap: a `cases`-topic (independently-compiled sub-cases per variant) now
renders through the subject-agnostic engine instead of being flattened to an empty program. Two surgical
changes in `cpp_ptr_lab/yaml_engine/render_page.py`: (1) `_bake_one` now branches on `v.get("cases")` and
preserves each sub-case as its own baked program (`entry[label] = {"cases": [...]}`), via a new
`_bake_program(v)` helper shared by the variant and sub-case paths; (2) `_build_topic` branches on
`"cases" in v` and wraps the sub-programs in the existing `stacked_subcases` component (each with its own
`code_diagram_panel` + `compile_status_badge` + `output_console` + `byte_grid`), via a new
`_panel_program(pid, v, caption)` helper factored out of the old inline body. Non-cases topics are
unchanged (backward compatible). Proven on the real `const_taxonomy` topic: **4 declaration-type tabs, each
2 stacked sub-cases (write / rebind), one genuinely failing per tab with an authentic g++ `read-only`
diagnostic**, no duplicate ids, self-contained. TDD: 6 RED tests first (`_bake_one` shape via monkeypatch,
pure cases-render, dup-ids, + a g++-gated end-to-end class), then GREEN. Suite **350 passed** (344 + 6).
Gap 2 (configurable `topic` layout) and a `const_taxonomy` subject page.yaml remain open.

## 2026-06-30 21:55 — Session handoff

Wrote `handoffs/HANDOFF_2026-06-30_21h55mEST.md` closing out this session (function_args subject +
engine/subject split). Next focus: engine gaps 1–2 (cases-topics → `stacked_subcases`, configurable
`topic` layout) and the now-unblocked course manifest. Also captured a small correction for the reader —
run the engine CLI from the project root; the moved basic_ptr spec is now at
`cpp_ptr_lab/basic_ptr/basic_ptr.page.yaml` (old `basic_ptr_yaml/` path is gone). Suite still **344
passed**. Committing the working-tree refinements (doc path refs, general CLI, split tests) via `/git`.

## 2026-06-30 21:40 — Split YAML engine from subject packages (uniform structure)

Refactor for consistent structure: the subject-agnostic engine no longer lives inside a subject-named
package. `cpp_ptr_lab/basic_ptr_yaml/` is gone, replaced by two packages: `yaml_engine/` (the engine —
`render_page.py` + `test_render_page.py`, pure-render tests only) and `basic_ptr/` (a subject page package
— `basic_ptr.page.yaml` + `topics.py` + `test_basic_ptr.py`). Now every subject folder has the **identical
shape** `{__init__.py, topics.py, <subject>.page.yaml, test_<subject>.py}` (basic_ptr + function_args).
`basic_ptr/topics.py` re-exports the `basic_ptr` TopicTemplate from `pointers_refs` (single source of
truth, no duplication) — answering "why did only function_args have topics.py". Engine changes: dropped
the basic_ptr-specific `SPEC_PATH`/`main()`; `main()` is now general (`python -m
cpp_ptr_lab.yaml_engine.render_page <page.yaml> [dist]`), and `build_page` writes `dist/<stem>/<stem>.html`.
Updated the 2 import sites + `COURSE_VIA_TOPICS.md` path refs. Behavior-preserving: **344 passed**
(unchanged); both pages rebuild via the new CLI. No `basic_ptr_yaml` refs remain in code.

## 2026-06-30 21:15 — `function_args` subject: end-to-end new-subject proof

First new subject built through the YAML engine — validates "new subject = new topic module + page spec,
no new diagram components" (handoff step 3). New package `cpp_ptr_lab/function_args/`: one `function_args`
`TopicTemplate` with a `mode` dropdown (by value / pointer / reference) → three tabs via the existing
`topic` builder + a `function_args.page.yaml`. `memory_diagram` reused unchanged: pointer → `type=raw`
(arrow to `val`), reference → `type=ref` (baked g++ confirms `ref_addr == target_addr`, the alias *is*
val's address), value → no `PTRDATA` (honest "no link"; output console shows `val` stays 42 vs 99). Two
tiny engine touches in `basic_ptr_yaml/render_page.py`: register the topic; generalize `build_page`'s
output subdir to the spec stem (→ `dist/function_args/function_args.html`). TDD: 11 RED-first tests.
Suite **344 passed** (333 + 11); page self-contained, no dup ids. Handoff:
`handoffs/HANDOFF_2026-06-30_18h32mEST.md`.

### Details

Modelling move that made one dropdown drive four co-varying spots (signature, assignment, probe, call
arg) without a Cartesian variant blow-up and with **zero change to `generate_source`**: each `mode`
option maps to a **complete program body** in a single `<<mode>>` placeholder. The three bodies are built
in Python from one `_SKELETON` via `.replace()` of four `<<...>>` fragments; the literal `<<HARNESS>>`
stays for the code generator's multi-pass replace loop to fill. Baked addresses confirm the pedagogy:
pointer `ptr_addr=0x…9c8 ≠ target_addr=0x…a18` (param is a distinct pointer holding val's address);
reference `ref_addr == target_addr` (same address = alias).

Tests (`test_function_args.py`): 3-mode topic shape + per-mode generated source (value has no `PTRDATA`,
pointer `*x=99`/`type=raw`, reference `type=ref`); pure page render with FAKE baked data (three tabs,
raw+ref diagrams present, self-contained, no dup ids); g++-gated integration (real output baked,
`after: val = 42` for value vs `= 99` for the other two, no dup ids).

Known rough edge: the value tab's diagram is `_svg_unknown` ("No diagram available") — truthful (no
pointer link) but reads as a gap; a future `separate-copy` diagram or a friendlier no-link render would
sharpen it. Engine gaps 1–2 (cases-topics, configurable `topic` layout) remain untouched — deferred as
separate steps.

## 2026-06-30 18:30 — YAML-driven page renderer + curriculum-expansion design

New subpackage `cpp_ptr_lab/basic_ptr_yaml/`: a YAML page spec (`basic_ptr.page.yaml`) drives a thin
translator (`render_page.py`) that maps a flat `blocks:` list to component calls — each block is
`{component_or_builder: {args}}`, the translator pops `id` and forwards the rest as kwargs, resolving
`${a.b.c}` refs from baked data. Two smart builders compose multiple components: `topic` (a
`variant_tabs` cluster over a baked topic) and `heading`/`html`. The YAML page is component-signature-
identical to the imperative `dist/topics_v2/basic_ptr.html`, self-contained, no dup ids; "same template
twice on a page" works via per-block id namespacing (two passing tests). Suite **333 passed** (320 +
13). Discussed scaling to a full C++ curriculum (initializers, pointers, stack frames, classes, function
args, templates, STL): decided on a 4-layer architecture — course manifest → YAML page specs →
per-subject topic modules (10–15 each, NOT a flat 30–50) → components — with the insight that ~10/15
components are a reusable subject-agnostic spine while the 4 diagram components are pointer-specific, so
a new subject = new topic module + 1–3 new diagram components + YAML pages. The flat block list = DOM
order = reading order is the ADA mechanism (WCAG 1.3.2 by construction). Known engine gaps (both in
`_build_topic`/`_bake_one`): cases-topics (`const_taxonomy`) unhandled, and the `topic` layout is a fixed
recipe. Handoff: `handoffs/HANDOFF_2026-06-30_18h32mEST.md`; next focus = prototype `function_args` + close
the two gaps.

## 2026-06-30 15:05 — Reconstruct basic_ptr topic page from the component library

Worked example of *consuming* the new component library: new `cpp_ptr_lab/topic_page.py`
assembles the `basic_ptr` topic page entirely from components (no bespoke HTML/CSS beyond
`<h2>` headings), baking real g++ output for all three type variants. Composition: `page_shell`
wraps `callout_note` (concept) + `color_legend` + `variant_tabs` (int/double/float) — each tab a
`code_diagram_panel` (`memory_diagram` + source) plus `compile_status_badge`, `output_console`,
and `byte_grid` — then `progressive_steps` and a `predict_reveal_quiz`. 9 of 15 components in one
page; each variant is an independent compile. Output → `dist/topics_v2/basic_ptr.html` (342 lines,
self-contained: 0 script/network/src refs, no duplicate ids). The point: assembling a topic page
is now ~40 lines of glue (`build_basic_ptr_page`) that bakes data and arranges vetted components,
vs extending the monolithic `render_fragment` template — the inversion the change was designed for,
and it adds the reveal-steps + quiz interactions for free. TDD: `tests/test_topic_page.py` (7
tests: self-containment, one tab per type, component signatures, real baked output, no dup ids,
missing-g++ guard). Suite: **320 passed** (313 + 7).

## 2026-06-30 14:49 — Fix code_line_link CSS-combinator bug + session handoff

While explaining how `code_line_link` works, found its hover/focus highlight was dead: the
rule used the `~` general-sibling combinator, but the linked `<code>` line was trapped inside
a `<pre>`, so it was never a sibling of `.cll-diagram` and the selector never matched. Fix
(`components.py`): emit the code lines as **direct children** of the namespaced `#{comp_id}`
container (no `<pre>` wrapper), styled with a shared `var(--code-bg)` background + first/last
rounding so they still read as one code block; linked lines get a `cll-link` dotted-underline
affordance. Added `TestCodeLineLink::test_linked_line_and_diagram_share_a_parent`, which
**parses** the fragment (html.parser) and asserts the line and diagram share the `#{comp_id}`
parent — a structural check string-matching tests can't make. Suite: **313 passed** (312 +
this regression test); gallery rebuilt; user confirmed all 15 pages work. Handoff written to
`handoffs/HANDOFF_2026-06-30_14h49mEST.md`. The `interactive-ptr-components` change is
feature-complete and user-confirmed — next action is `/opsx:verify` → `/opsx:archive`.

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
