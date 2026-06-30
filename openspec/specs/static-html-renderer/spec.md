# static-html-renderer Specification

## Purpose
TBD - created by archiving change cpp-ptr-lab-static-html. Update Purpose after archive.
## Requirements
### Requirement: SVG diagram rendering from pointer data

The system SHALL provide `svg_renderer(ptrdata)` that returns a self-contained
inline SVG string for a single topic variant, dispatching on `ptrdata["type"]`
to cover all six diagram kinds ported from the DPG drawlist: `raw`, `null`,
`ref`, `unique`, `shared`, and `weak`. The SVG MUST use `viewBox="0 0 500 160"`
(matching the original DPG coordinate space), carry `role="img"`, and reference
a `<title>` and `<desc>` via `aria-labelledby` so assistive technology can
announce the diagram. Missing or absent `ptrdata` keys MUST degrade to a safe
placeholder (e.g. `?`) rather than raising.

#### Scenario: Raw pointer renders two boxes and an arrow
- **WHEN** `svg_renderer` is called with `{"type": "raw", "ptr_addr": "0x16b949ac0", "target_addr": "0x16b949ac8", "target_val": "42"}`
- **THEN** the returned SVG contains two `<rect>` boxes, an arrow (`<line>` + `<polygon>`) between them, the pointer and target addresses, the value `42`, and `<title>`/`<desc>` referenced by `aria-labelledby` with `role="img"`

#### Scenario: Null pointer renders a NULL target box
- **WHEN** `svg_renderer` is called with `{"type": "null", "ptr_addr": "0x0"}`
- **THEN** the returned SVG shows the pointer box, an arrow to a box labeled `NULL`, and no dereferenced value

#### Scenario: Missing keys degrade safely
- **WHEN** `svg_renderer` is called with `{"type": "raw"}` (no addresses or value)
- **THEN** it returns valid SVG with `?` placeholders in place of the missing fields and does not raise

#### Scenario: Smart-pointer types are dispatched
- **WHEN** `svg_renderer` is called with `ptrdata["type"]` equal to `unique`, `shared`, or `weak`
- **THEN** it returns the corresponding diagram (target/NULL box for `unique`, one-or-two source boxes with `use_count` for `shared`, single box with `expired`/`use_count` for `weak`)

### Requirement: Accessible topic fragment with zero-JS variant switching

The system SHALL provide `render_fragment(topic, variants)` that returns one
self-contained HTML `<section>` for a topic. When a topic has more than one
variant, switching MUST use the native-radio CSS `:checked` sibling pattern with
no JavaScript. Every `id`, radio `name`, and CSS selector in the fragment MUST be
namespaced by the topic id so that fragments combined into one page do not
cross-contaminate. The first variant MUST be rendered `checked`.

#### Scenario: One panel per variant, first selected
- **WHEN** `render_fragment` is called for a topic with variants `["int", "double", "float"]`
- **THEN** the fragment contains one radio input and one panel section per variant, and exactly the first variant's radio carries the `checked` attribute

#### Scenario: Ids and names are namespaced by topic id
- **WHEN** `render_fragment` is called for a topic whose id is `basic_ptr`
- **THEN** every generated `id`, radio `name`, and `for` attribute incorporates `basic_ptr`, so an identically-structured fragment for a different topic id shares no `id` or `name`

#### Scenario: Single-variant topic needs no radios
- **WHEN** `render_fragment` is called for a topic with exactly one variant
- **THEN** the fragment renders that variant's panel directly with no radio controls

### Requirement: Full accessible page assembly

The system SHALL provide `assemble_page(fragments, ...)` that wraps one or more
fragments into a complete WCAG AA HTML document. The document MUST declare a
`lang` attribute, include a skip link targeting the main content, and contain
every supplied fragment with no `id` collisions across fragments.

#### Scenario: Combined page contains all topics without collisions
- **WHEN** `assemble_page` is called with fragments for several distinct topics
- **THEN** the returned document contains every fragment, has a `<html lang=...>` attribute and a skip link, and contains no duplicate `id` values

#### Scenario: Document is self-contained
- **WHEN** a page is assembled
- **THEN** all CSS is inlined in a `<style>` block and the document references no external scripts, stylesheets, or network resources

### Requirement: Generated element ids are CSS-identifier-safe

Every `id` the renderer emits that is referenced from an unescaped CSS `#id` selector (variant radios, panels, svg ids) SHALL contain only characters valid in a CSS identifier (`[A-Za-z0-9_-]`). Variant labels that contain `(`, `)`, `,`, or other punctuation MUST be sanitised when forming ids, because an unescaped `(` is a CSS parse error and an unescaped `,` splits the selector, which would silently drop the `:checked ~` rule and leave the panel empty.

#### Scenario: punctuated variant labels still produce switchable panels

- **WHEN** `render_fragment` runs for a topic whose variant labels contain parentheses and commas
- **THEN** every emitted `id` matches `[A-Za-z0-9_-]+`, so the corresponding `#id:checked ~ .panels #…` rule is valid CSS

### Requirement: Absent memory diagram leaves the column empty

When a rendered case has no pointer data, the renderer SHALL leave the diagram column empty rather than drawing a placeholder diagram. "No pointer data" means the case's `ptrdata` is present but empty, which covers compile-failed cases and topics declared with `has_ptrdata=False`. For such cases the "Memory diagram" heading, the `<figure>`, the caption, and any `_svg_unknown` placeholder MUST be omitted; cases that do carry pointer data render their diagram unchanged.

#### Scenario: no-data case renders an empty diagram column

- **WHEN** a fragment is rendered for two variants where one carries `ptrdata` and the other has `ptrdata` empty (e.g. a compile failure)
- **THEN** the output contains exactly one `<svg>` and one "Memory diagram" heading, no "no diagram" placeholder text, and the empty case's diagram column is present but contains no figure

