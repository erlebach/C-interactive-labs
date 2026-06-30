## Context

`cpp_ptr_lab` is a Dear PyGui app: `app_base.py` (743 lines, the only DPG-coupled
file) builds tabbed windows, runs `compile_and_run()` on a background thread, and
draws pointer diagrams with `dpg.draw_*` calls into a 500×160 drawlist. The topic
content (`pointers_refs/topics.py`, `smart_ptrs/topics.py`), code generation
(`code_generator.py`), and compilation (`compiler_runner.py`) are decoupled from
DPG and already unit-tested. The app's dark, low-contrast UI fails WCAG AA and
cannot run in Canvas, which strips JavaScript and blocks native apps.

A throwaway prototype (`prototype/basic_ptr.html`) proves the target pattern with
real g++ output: zero JS, native-radio `:checked` variant switching, inline SVG
with `<title>`/`<desc>`, and a light WCAG AA theme. This change generalizes that
prototype into a build pipeline driven by the existing topic dataclasses.

## Goals / Non-Goals

**Goals:**
- Reuse `code_generator.py`, `compiler_runner.py`, and both `topics.py` verbatim.
- Render real, build-time g++ output into self-contained, accessible HTML.
- Zero JavaScript, zero network, zero backend at student runtime; Canvas-pasteable.
- WCAG AA: light high-contrast theme, 44px targets, visible focus, skip link,
  SVG diagrams labelled for screen readers.
- Emit both per-topic and per-lab files from one set of fragments.

**Non-Goals:**
- Removing or rewriting the DPG app — `app_base.py` and the launchers stay intact
  as a superseded path; this change is additive.
- Modifying `cpp_initializer_lab/`.
- Client-side interactivity beyond variant switching (no re-compilation in browser).
- Supporting compilers other than `g++`.

## Decisions

### D1: Pure render functions, separate from build orchestration
Rendering lives in `html_renderer.py` as pure functions —
`svg_renderer(ptrdata) -> str`, `render_fragment(topic, variants) -> str`,
`assemble_page(fragments) -> str` — with no I/O and no compilation. Build I/O
(compile, run, write files) lives in `build_html.py`.
**Why:** pure functions are directly unit-testable (the confirmed TDD plan tests
each in isolation) and keep the slow g++ work out of the render tests.
**Alternative considered:** one monolithic builder that compiles and emits HTML
inline. Rejected — untestable without invoking g++ on every test.

### D2: Variant switching via native-radio CSS `:checked` sibling pattern
Radios are visually hidden but focusable and in tab order; `:checked ~ .panels`
selectors reveal the matching panel. No ARIA-JS tabs.
**Why:** keyboard + screen-reader accessible for free (announces "radio button,
int, 1 of 3"), and works in Canvas where JS is stripped.
**Alternative considered:** ARIA `role="tablist"` with JS. Rejected — fails the
zero-JS / Canvas constraint.

### D3: Namespace every id/name/selector by topic id
`render_fragment` prefixes all `id`, radio `name`, `for`, and CSS selector tokens
with the topic id (e.g. `basic_ptr-type`, `basic_ptr-panel-int`).
**Why:** combined per-lab files put many topics in one document; without
namespacing, `:checked` selectors and duplicate ids cross-contaminate. This is
impossible to retrofit by hand, which is the core reason a generator is required.
**Alternative considered:** per-topic files only. Rejected — loses the offline
single-file-per-lab grouping the instructor wants.

### D4: Fragment is the atomic unit; both groupings emitted from it
`build_html.py` builds one fragment per topic, then writes each fragment alone
(`dist/topics/<id>.html` via `assemble_page([fragment])`) and all fragments of a
lab together (`dist/lab_<lab>.html` via `assemble_page(fragments)`).
**Why:** single source of truth — per-topic and per-lab content cannot diverge;
marginal cost over emitting one grouping.

### D5: Port the six `_draw_*` methods to SVG 1:1
Each DPG `_draw_*` method maps to an SVG branch in `svg_renderer`, reusing the
same coordinates in `viewBox="0 0 500 160"`. `draw_rectangle`→`<rect>`,
`draw_arrow`→`<line>`+`<polygon>`, `draw_text`→`<text>`.
**Why:** the geometry is already designed and reviewed; a 1:1 port minimizes risk
and review surface. `<title>`/`<desc>` + `role="img"` add the accessibility the
DPG drawlist never had.

### D6: Variants are derived from a topic's categorical controls
A "variant" is one option of a topic's pedagogically meaningful categorical
control (type dropdown, compile-mode/illusion selector). Free-text controls are
dropped (per the static-HTML decision); topics with no such control yield a
single variant.
**Why:** the build must enumerate a finite, baked set; free-text entry cannot be
pre-baked and was the least pedagogically load-bearing control.

### D7: Reuse `parse_ptrdata` / `parse_membytes`; do not re-test them
The build calls the already-tested parsers in `compiler_runner.py`. New tests
cover only the renderer functions and build orchestration, not the parsers or
`generate_source`.

## Risks / Trade-offs

- Addresses are non-deterministic per run → bake real addresses and state in a
  `figcaption` that addresses are frozen real output, as the prototype does.
- Compile-failure variants (e.g. `ref_must_bind`) produce no program output →
  build must branch on compile status and render the captured stderr instead.
- Combined-file id collisions → enforced by D3 namespacing; an `assemble_page`
  test asserts no duplicate ids.
- `g++` absent at build time → build fails loudly with a clear message rather
  than emitting empty HTML (covered by a build spec scenario).
- ASan "gotcha" topics print diagnostics to stderr on a crashing run → treat
  their captured stderr as the displayed output, same as compile failures.

## Migration Plan

1. Add `html_renderer.py` and `build_html.py` under `cpp_ptr_lab/` with RED tests
   first (per the confirmed TDD plan), then implement to green.
2. Generate `dist/` and spot-check per-topic and per-lab files in a browser and,
   if possible, pasted into Canvas.
3. Keep the DPG launchers during transition; once the static build is validated,
   point course materials at `dist/` files. No rollback needed — additive.

## Open Questions

- None blocking. Exact `dist/` filenames per lab follow the proposal
  (`lab_pointers_refs.html`, `lab_smart_ptrs.html`); adjust if the instructor
  prefers different lab keys.
