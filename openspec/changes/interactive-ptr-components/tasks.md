<!-- TDD ordering: every component's RED test precedes its implementation.
     Applies memory rule feedback/testing.md, overriding OpenSpec's default
     tests-last task ordering. Each "test" task must be RED (failing) before the
     paired "impl" task makes it GREEN. -->

## 1. Foundation: module scaffold + semantic color tokens

- [x] 1.1 Create the pure component module (beside `html_renderer.py`) with an empty public surface and a docstring stating the purity + zero-JS + id-namespacing contract
- [x] 1.2 RED: write tests for the semantic `:root` color tokens — `--c-addr/--c-val/--c-type/--c-const/--c-err` exist, each documented contrast ≥4.5:1 on the page background, and the SVG palette resolves to the same values
- [x] 1.3 GREEN: add the semantic color tokens to the theme `:root` and reuse the identical values in the SVG palette (satisfies `static-html-renderer` delta)

## 2. Cross-component shared-invariant tests (RED first)

- [x] 2.1 RED: parametrized purity test — every component function returns a string and performs no I/O/subprocess
- [x] 2.2 RED: parametrized id-namespacing test — two instances of a component with different ids in one document produce no duplicate `id` and no cross-instance selector leakage
- [x] 2.3 RED: parametrized CSS-id-safety test — punctuated input (`( ) , * /`) yields only `[A-Za-z0-9_-]` ids and selectors still match
- [x] 2.4 RED: parametrized zero-JS/zero-network test — no `<script>` and no external `src/href/http` reference in any fragment
- [x] 2.5 RED: parametrized focus-preservation test — state-driving radios/checkboxes are hidden by clip/off-screen, never `display:none`/`visibility:hidden`
- [x] 2.6 RED: parametrized color-not-alone test — components with a colored state also carry text and a border/icon cue
- [x] 2.7 Register each component in the shared-invariant fixture as it is implemented (running task, revisited per component below)

## 3. Chrome components

- [x] 3.1 RED: `page_shell` test — `lang`, skip link to existing `#main`, `<main>` landmark, inlined CSS, no external refs
- [x] 3.2 GREEN: implement `page_shell`
- [x] 3.3 RED: `color_legend` test — each semantic role appears as a swatch paired with its text name
- [x] 3.4 GREEN: implement `color_legend`
- [x] 3.5 RED: `callout_note` test — semantic `<aside>`/note region with text label + border, not color alone
- [x] 3.6 GREEN: implement `callout_note`

## 4. Diagram core: memory-diagram (foundation for diagram interactions)

- [x] 4.1 RED: `memory_diagram` test — inline SVG with `role="img"`, `<title>`/`<desc>` referenced by `aria-labelledby`, desc narrates pointer→target, missing keys degrade to `"?"` without raising
- [x] 4.2 GREEN: implement `memory_diagram` (reuse the 500×160 viewBox coordinate vocabulary)

## 5. High-value interactions

- [x] 5.1 RED: `hover_link_diagram` test — hover/focus on the pointer highlights target + arrow via CSS, redundant non-color cue (stroke-width), no JS
- [x] 5.2 GREEN: implement `hover_link_diagram`
- [x] 5.3 RED: `before_after_toggle` test — 2-option radio swaps between two baked SVG states via `:checked ~`, both states present, keyboard-accessible
- [x] 5.4 GREEN: implement `before_after_toggle`
- [x] 5.5 RED: `predict_reveal_quiz` test — selecting a radio answer reveals correct/incorrect feedback via `:checked ~`, text+icon as well as color, real answer baked
- [x] 5.6 GREEN: implement `predict_reveal_quiz`

## 6. Output + status components

- [x] 6.1 RED: `compile_status_badge` test — pass/fail shown by text + border/icon in addition to color
- [x] 6.2 GREEN: implement `compile_status_badge`
- [x] 6.3 RED: `output_console` test — monospaced stdout block; error variant distinguished by text+border, output preserved verbatim
- [x] 6.4 GREEN: implement `output_console`

## 7. Secondary diagram interactions

- [x] 7.1 RED: `byte_grid` test — byte sequence renders as labelled cells with textual values and an accessible caption
- [x] 7.2 GREEN: implement `byte_grid`
- [x] 7.3 RED: `code_line_link` test — hover/focus a source line highlights the corresponding diagram element via shared namespaced id, CSS only
- [x] 7.4 GREEN: implement `code_line_link`

## 8. Layout + stepped components

- [x] 8.1 RED: `variant_tabs` test — N radio/label panels, exactly one `checked`, `:checked ~` shows matching panel, `:focus-visible` outline
- [x] 8.2 GREEN: implement `variant_tabs`
- [x] 8.3 RED: `code_diagram_panel` test — two columns present, code column scrolls internally, reflow breakpoint to one column
- [x] 8.4 GREEN: implement `code_diagram_panel`
- [x] 8.5 RED: `stacked_subcases` test — multiple sub-cases present and panel scrolls to reveal all
- [x] 8.6 GREEN: implement `stacked_subcases`
- [x] 8.7 RED: `progressive_steps` test — ordered `<details>/<summary>` reveals, each keyboard-operable, no JS
- [x] 8.8 GREEN: implement `progressive_steps`

## 9. Component gallery build

- [x] 9.1 RED: gallery test — build emits one self-contained demo page per component (complete WCAG AA doc, inlined CSS, no external refs) and an index linking every demo by name
- [x] 9.2 RED: gallery test — components that show output bake real g++-captured stdout/stderr (not placeholders); missing-g++ build fails clearly and early
- [x] 9.3 GREEN: implement gallery orchestration (beside `build_html.py`) emitting per-component demo pages + index into `dist/`
- [x] 9.4 GREEN: wire each component's demo (pointer content; real baked output where relevant)

## 10. Verification

- [x] 10.1 Run the full suite — all new component/gallery tests green and the existing 130 tests still pass
- [x] 10.2 Build the gallery and confirm every demo page is self-contained (zero external/script/network refs) and pastes into a Canvas-like context
- [x] 10.3 Spot-check contrast of the semantic tokens and confirm no state relies on color alone
- [x] 10.4 Update JOURNAL.md (and SNAPSHOT.md if present) and prepare the change for `/opsx:verify` → archive
