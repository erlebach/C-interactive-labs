## ADDED Requirements

### Requirement: Topic navigation tab bar

When `assemble_page` is called with a `topics` list of two or more `(id, name)` tuples, the returned document SHALL include a topic navigation bar containing one labelled tab
per topic, implemented using native radio inputs and the CSS `:checked` sibling pattern
with zero JavaScript. Topic radio inputs SHALL be placed as the first children of `<body>`
so the CSS sibling combinator can reach both the nav bar and the content panels. The nav
bar labels SHALL be styled as 44 px-minimum-height clickable elements. The first topic's
radio SHALL be `checked` by default so a topic is always visible on load.

#### Scenario: Topic tabs present for multi-topic page

- **WHEN** `assemble_page` is called with `topics=[("basic_ptr","Basic Pointer"),("const_taxonomy","const Taxonomy")]` and two corresponding fragments
- **THEN** the returned HTML contains one radio input and one label per topic, the first radio carries the `checked` attribute, and each label's `for` attribute matches its radio's `id`

#### Scenario: Clicking a topic tab shows only that topic

- **WHEN** the CSS `:checked` rule for a given topic radio is active
- **THEN** only the corresponding `<div class="topic-panel">` has a non-`none` display value; all other topic panels remain hidden

#### Scenario: Single-topic page has no topic tab bar

- **WHEN** `assemble_page` is called with `topics=None` or a single-element topics list
- **THEN** the returned HTML contains no elements with class `topic-nav` and no `vtopic` radio inputs

### Requirement: Backward-compatible `assemble_page` signature

`assemble_page(fragments, title, topics=None)` SHALL behave identically to its prior
behaviour when `topics` is `None`: it wraps fragments in `<main id="main">` with the
WCAG AA shell but generates no topic navigation. Existing callers that omit `topics`
MUST continue to work without modification.

#### Scenario: Omitting topics produces no nav bar

- **WHEN** `assemble_page([frag1, frag2])` is called without the `topics` kwarg
- **THEN** the returned page contains both fragments, has `<html lang="en">` and a skip link, and contains no `class="topic-nav"` element

### Requirement: Viewport-filling no-scroll layout

The assembled page SHALL use a full-viewport flex-column layout (`height: 100vh;
overflow: hidden` on `body`) so the outer page does not scroll. Only the code column
SHALL scroll internally. The topic panel area SHALL fill the remaining viewport height
after the header and topic-nav tabs.

#### Scenario: Body CSS prevents outer scroll

- **WHEN** `assemble_page` is called with the `topics` kwarg
- **THEN** the inlined `<style>` block contains `height:100vh` and `overflow:hidden` applied to `body`

#### Scenario: Code column scrolls, diagram column does not

- **WHEN** a panel is rendered
- **THEN** the code column carries `overflow-y:auto` in the inlined CSS, and the diagram column carries `display:flex;flex-direction:column` to allow the SVG to fill height

### Requirement: Diagram column fills available height

The diagram column within each variant panel SHALL be a flex column whose `<figure>`
child has `flex: 1 1 0; min-height: 0`, allowing the SVG to grow to fill the available
vertical space rather than being constrained by the SVG's intrinsic aspect-ratio height.

#### Scenario: Diagram column CSS allows SVG to fill height

- **WHEN** a fragment is rendered via `render_fragment`
- **THEN** the fragment's CSS or inline style for the diagram column includes `display:flex` and the figure includes `flex:1` so the SVG scales beyond its natural ~130 px height

### Requirement: Variant tabs appear above the content grid

Within a topic panel, the variant-type selector (e.g. int / double / float radio tabs) SHALL appear above the code-and-diagram grid, not interleaved with the explanation text.
The topic explanation SHALL appear in a compact header area above the variant tabs.

#### Scenario: Variant tabs precede the panel grid in the DOM

- **WHEN** `render_fragment` is called for a multi-variant topic
- **THEN** the `.tabs` div appears before the `.panels` div and after any explanation text, maintaining the sibling relationship required for CSS `:checked ~ .panels` to work

### Requirement: Legible font sizes

The inlined CSS SHALL set body font size to at least 16 px, code/output blocks to 14 px
monospace, and topic/variant tab labels to at least 14 px bold. SVG `<text>` element
`font-size` attributes SHALL remain expressed in SVG-user-unit values (13–18) that scale
proportionally when the SVG is displayed larger.

#### Scenario: Body font size is at least 16 px

- **WHEN** `assemble_page` is called
- **THEN** the inlined `<style>` block sets `font-size` for `body` to `16px` or larger
