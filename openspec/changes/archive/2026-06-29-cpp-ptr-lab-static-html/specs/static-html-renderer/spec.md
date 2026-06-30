## ADDED Requirements

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
