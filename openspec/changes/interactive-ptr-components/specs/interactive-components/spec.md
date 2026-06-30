## ADDED Requirements

### Requirement: Components are pure, self-contained, and id-namespaced

Every component function SHALL be pure — it takes plain data (dicts/strings) and a
caller-supplied component id, and returns an HTML-fragment string with no file, network,
or subprocess I/O. Every `id`, `name`, and CSS selector the fragment emits SHALL be
prefixed by the component id and SHALL be CSS-identifier-safe (`[A-Za-z0-9_-]`), so that
multiple components — even several instances of the same component — coexist in one
document without id collision or `:checked ~` cross-contamination.

#### Scenario: Two instances in one document do not collide
- **WHEN** the same component is rendered twice with different component ids and concatenated into one document
- **THEN** the document contains no duplicate `id` values and each instance's CSS rules reference only its own ids

#### Scenario: Punctuated input is sanitised
- **WHEN** a component is given a label containing `(`, `)`, `,`, `*`, or `/`
- **THEN** every emitted id is restricted to `[A-Za-z0-9_-]` and the component's CSS selectors still match

### Requirement: Interactivity is zero-JS and zero-network

All component interactivity SHALL be expressed with CSS only (`:checked`, `:hover`,
`:target`, `<details>/<summary>`). A rendered fragment MUST NOT contain `<script>` or any
reference to an external script, stylesheet, or network resource. Any hidden radio/checkbox
that drives state MUST remain keyboard-focusable (hidden by clip/off-screen, never
`display:none`).

#### Scenario: Fragment references nothing external
- **WHEN** any component fragment is rendered
- **THEN** it contains no `<script>` tag and no `http`/`https`/`src=`/`href=` reference to an external resource

#### Scenario: State-driving inputs stay focusable
- **WHEN** a component hides a radio or checkbox that drives a CSS state
- **THEN** that input is hidden via clip/off-screen positioning and not via `display:none` or `visibility:hidden`

### Requirement: Color is never the sole signal

Any state or category a component conveys with color SHALL also be conveyed by text and/or
a non-color visual cue (border, shape, icon), satisfying WCAG 1.4.1.

#### Scenario: Pass/fail conveyed redundantly
- **WHEN** a component renders a success or failure state
- **THEN** the state is indicated by text and a border/icon in addition to any color

### Requirement: page-shell component

The library SHALL provide a `page_shell` component that wraps body content in a complete
WCAG AA document scaffold: `<html lang=...>`, a skip link targeting `#main`, and semantic
`header`/`main` landmarks.

#### Scenario: Shell is accessible and self-contained
- **WHEN** `page_shell` wraps arbitrary content
- **THEN** the output declares `lang`, contains a skip link whose target id exists in the document, exposes a `<main id="main">` landmark, and inlines all CSS

### Requirement: variant-tabs component

The library SHALL provide a `variant_tabs` component that switches between N labelled
panels using native `<input type="radio">` + `<label for>` + the CSS `:checked ~`
combinator, with the first variant selected by default and a visible `:focus-visible`
outline on tab labels.

#### Scenario: Radio tabs switch panels
- **WHEN** `variant_tabs` is rendered with several labelled panels
- **THEN** each panel has a radio/label pair, exactly one radio is `checked`, and a `:checked ~` rule shows the matching panel

### Requirement: code-diagram-panel component

The library SHALL provide a `code_diagram_panel` component arranging a code column and a
diagram column side by side, reflowing to a single column at narrow widths, with the code
column independently scrollable.

#### Scenario: Two-column panel reflows
- **WHEN** `code_diagram_panel` is rendered with code and a diagram
- **THEN** both columns are present, the code column scrolls internally, and a reflow breakpoint collapses them to one column

### Requirement: stacked-subcases component

The library SHALL provide a `stacked_subcases` component that stacks multiple independent
sub-cases (each its own code + compile verdict + output + optional diagram) inside one
scrollable panel.

#### Scenario: Stacked sub-cases remain scrollable
- **WHEN** `stacked_subcases` renders two or more sub-cases taller than the panel
- **THEN** every sub-case is present and the panel scrolls to reveal all of them

### Requirement: memory-diagram component

The library SHALL provide a `memory_diagram` component rendering pointer state as inline
SVG with `role="img"` and `aria-labelledby` referencing a `<title>` and `<desc>` generated
from the real data; missing keys degrade to `"?"` and never raise.

#### Scenario: Diagram has a data-derived accessible name
- **WHEN** `memory_diagram` is given pointer data
- **THEN** the SVG has `role="img"`, a `<title>`/`<desc>` whose ids are referenced by `aria-labelledby`, and the desc narrates the pointer→target relationship

### Requirement: hover-link-diagram component

The library SHALL provide a `hover_link_diagram` component in which hovering (or focusing)
the pointer element highlights its target element and the connecting arrow in a shared
color, redundantly reinforced by a non-color cue (e.g. stroke-width), using CSS only.

#### Scenario: Hover links pointer to target
- **WHEN** the pointer element is hovered or focused
- **THEN** a CSS rule highlights both the target element and the arrow, with a non-color cue in addition to color, and no JavaScript is used

### Requirement: before-after-toggle component

The library SHALL provide a `before_after_toggle` component that switches one diagram
between two pre-baked states (e.g. before/after an assignment) via a 2-option radio switch,
keyboard-accessible and JS-free.

#### Scenario: Toggle swaps baked states
- **WHEN** the "after" option is selected
- **THEN** a `:checked ~` rule hides the "before" SVG and shows the "after" SVG, with both states baked into the fragment

### Requirement: byte-grid component

The library SHALL provide a `byte_grid` component rendering a sequence of memory bytes as a
labelled grid (e.g. little-endian pointer bytes), with each cell's value shown as text and
addresses labelled.

#### Scenario: Bytes render as a labelled grid
- **WHEN** `byte_grid` is given a byte sequence
- **THEN** each byte appears as a labelled cell with its textual value and the grid has an accessible caption

### Requirement: code-line-link component

The library SHALL provide a `code_line_link` component in which hovering or focusing a
source line highlights the diagram element it corresponds to, associated by a shared id and
implemented with CSS only.

#### Scenario: Hovering a line highlights its diagram element
- **WHEN** a linked source line is hovered or focused
- **THEN** a CSS rule highlights the corresponding diagram element, linked by a shared namespaced id, without JavaScript

### Requirement: compile-status-badge component

The library SHALL provide a `compile_status_badge` component showing compile success or
failure using text plus a border/icon in addition to color (never color alone).

#### Scenario: Status shown by text and border
- **WHEN** `compile_status_badge` renders a failed compile
- **THEN** the badge contains failure text and a distinguishing border/icon as well as a color

### Requirement: output-console component

The library SHALL provide an `output_console` component rendering captured stdout in a
monospaced block, with a visually distinct error variant for stderr/compile failures
(distinguished by text and border, not color alone).

#### Scenario: Error output is distinguishable
- **WHEN** `output_console` renders an error variant
- **THEN** the block is marked as an error by text and border in addition to color and preserves the captured output verbatim

### Requirement: predict-reveal-quiz component

The library SHALL provide a `predict_reveal_quiz` component offering radio answer options
whose selection reveals feedback (correct/incorrect) using CSS `:checked ~`, with
correctness signalled by text + icon in addition to color, and the real answer/output
baked in.

#### Scenario: Selecting an answer reveals baked feedback
- **WHEN** an answer option is selected
- **THEN** a `:checked ~` rule reveals feedback that marks the choice correct or incorrect using text and an icon as well as color, with no JavaScript

### Requirement: progressive-steps component

The library SHALL provide a `progressive_steps` component presenting an ordered sequence of
student-paced reveals using native `<details>/<summary>`, each step keyboard-operable.

#### Scenario: Steps reveal on demand
- **WHEN** a step's `<summary>` is activated
- **THEN** that step's content is revealed using native `<details>` semantics with no JavaScript

### Requirement: color-legend component

The library SHALL provide a `color_legend` component that documents the semantic color
palette, pairing each color swatch with its role name as text.

#### Scenario: Legend pairs swatch with text
- **WHEN** `color_legend` is rendered
- **THEN** each semantic role appears as a color swatch alongside its textual name

### Requirement: callout-note component

The library SHALL provide a `callout_note` component rendering a pedagogical aside as a
semantic `<aside>`/note region distinguished by text label and border, not color alone.

#### Scenario: Note is a labelled aside
- **WHEN** `callout_note` renders a note
- **THEN** the output is a semantic aside/note region with a text label and a border in addition to color
