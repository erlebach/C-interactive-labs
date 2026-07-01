# Design — Demos & Layouts: separating content units from page layout

*Date: 2026-07-01 · Status: proposed (awaiting review) · Author: session with erlebach*

## Problem

The combined Pointers & References page (`cpp_ptr_lab/pointers_refs/pointers_refs.page.yaml`)
renders every demo stacked vertically — a long scroll, which the user has ruled
out. We want the *same baked content* presented through a compact, navigated
layout where **only one demo is visible at a time** (~one screen), and we want
the freedom to render that content through **more than one layout** (left-rail
now, top-tabs next) without duplicating content or rewriting anything.

Today the seam is in the wrong place: the `topic` smart-builder in
`yaml_engine/render_page.py` hardcodes one presentation recipe, and a page spec
mixes *content* (which demos) with *layout* (how they're arranged) in one file.

## Goals

1. **Separate content from layout.** A *demo* is a reusable, self-contained
   content unit (one topic's presentation). A *layout* composes N demos into one
   standalone HTML page and chooses how they're navigated.
2. **One demo visible at a time**, ~one screen, no long scroll.
3. **Multiple layouts from the same demos**, selected by a `style:` value:
   `left_rail` (build now), `top_tabs` (build next), `stacked` (≈ current, ~free).
4. Preserve every existing constraint: **static, zero-JS, zero-network,
   Canvas-pasteable, WCAG AA**, real g++ output baked at build time.
5. **TDD throughout** (RED before GREEN).

## Guiding principle — data over code (North Star)

**A small, fixed set of Python files must address an unbounded number of demos.**
Python is the *engine + component library* only; **demos, glossaries, and layouts
are data (YAML)**. Authoring new content — a new demo, a new glossary, a new page
layout — must add **YAML files, never Python files**. This keeps the Python small
and maintainable, makes content author-editable and portable, and lets a future
skill generate content mechanically.

This change honors it: all new *content* is YAML; the new *Python* is a one-time
engine addition (`render_fragment`, `demo_panel`, `glossary`, layout components,
loader), not per-demo. The one remaining place Python still grows per-topic is the
C++ source inside `TopicTemplate` — see non-goals for the deferred final step.

## Non-goals (YAGNI)

- Not migrating a *single type variant* (e.g. just `double`) into an independently
  placeable unit. **demo = whole topic**; type/case tabs stay internal.
- Not moving C++ source out of Python `TopicTemplate`s into YAML. This is the
  **final step toward the data-over-code North Star** (a new topic would then be
  pure YAML too), deferred here only to bound scope — not rejected.
- Not migrating the existing standalone subject pages (`basic_ptr`,
  `function_args`) to the new demo/layout files in this change — additive only.
  (Unifying them is a noted follow-up.)
- Not building a `<select>`/popup selector — CSS cannot switch views from an
  `<option>` without JS (zero-JS constraint), independent of ADA.

## Vocabulary (locked)

```
topic     one C++ concept, defined by a Python TopicTemplate (the C++ + variants)
demo      one topic's full presentation = ONE nav entry; CONTAINS its inner tabs
  └─ inner tabs   the variant selector inside a demo (int/double/float; write/rebind)
       └─ tab content   one compiled variant: code + diagram + output + bytes
glossary  a reusable set of term→definition pairs, authored to cover an
          author-chosen SUBSET of demos; not tied to any built-in category
layout    one standalone page = an author-chosen subset of demos + an author-chosen
          header (glossaries, legend, …) + a nav style
```
A layout never reaches inside a demo; a demo never knows how it's navigated.

**No built-in "family."** Both *which demos* and *which glossaries* appear on a
page are explicit author choices in the layout — nothing is auto-derived from the
domain. A glossary's subset and a layout's subset are the same abstraction (*a
subset of topics*), so the design is domain-agnostic: pointers, classes, stack
frames, templates all compose the same way. Different layouts over the same
topics may show different glossaries.

## Architecture

Four layers, three of which already exist:

```
CONTENT           TopicTemplate ──bake──▶ {variants|cases: code_html, ptrdata, stdout, bytes, ok…}
  (unchanged)

PRIMITIVES        code_diagram_panel · memory_diagram · compile_status_badge ·
  (unchanged)     output_console · byte_grid · variant_tabs · stacked_subcases

DEMO  (new unit)  demo_panel(id, topic_data)   one demo's inner content; layout-agnostic
                  demo spec (YAML)             {title, bake, blocks} rendered as a FRAGMENT

GLOSSARY (new)    glossary(id, title, terms)   term→definition list (<dl>); shared, reusable
                  glossary spec (YAML)         {title, terms:[{term, def}]}   referenced by a layout

LAYOUT (new)      left_rail_layout(id, items)  vertical radio rail + panel area   [build now]
                  top_tabs_layout(id, items)   two-row outer tabs                 [build next]
                  layout spec (YAML)           {title, style, header:[…], demos:[…]}
```

The layout's `header:` is a list of blocks rendered **once** at the top of the
page (in order): a color legend, any number of `glossary` blocks (inline or
loaded from a shared `*.glossary.yaml` via `source:`), an intro note, etc. It is
the fixed top area that stays put while the student switches demos.

### Key new engine capability: fragment rendering

`render_page(spec, data)` currently always wraps output in the full `<html>`
shell (`page_shell`). Split it:

- `render_fragment(spec, data) -> str` — the blocks only, no shell.
- `render_page(spec, data) -> str` — `page_shell(render_fragment(...))` (behavior
  preserved for existing standalone pages).

A layout builds one page by rendering each referenced demo spec via
`render_fragment`, wrapping the `(demo.title, fragment)` list in the chosen
layout component, adding page-level chrome (title, one color legend), and
wrapping the whole in `page_shell` → a single standalone HTML file.

### `demo_panel` component

Promote the body currently inlined in `_build_topic` to a real, pure, tested
component `demo_panel(id, topic_data)`: the variant selector (`variant_tabs` /
`stacked_subcases` for cases-topics) with, per variant, `code_diagram_panel`
(code left / diagram right), `compile_status_badge`, `output_console`, and a
`byte_grid` **collapsed inside `<details>`** (keeps a demo to ~one screen).
`_build_topic` becomes a thin adapter over `demo_panel` (existing pages unchanged).

### Layout components (zero-JS, accessible)

Both are radio-backed (`:checked ~` view switching — keyboard + screen-reader
navigable, no JS), desktop-first with a single-column `@media` reflow so content
stays usable at 320px (WCAG 2.1 SC 1.4.10 Reflow). Color is never the only cue.

- `left_rail_layout(id, items)` — a vertical radio list (left) + a panel area
  (right); the selected rail item shows its demo. On narrow screens the rail
  reflows above the panel.
- `top_tabs_layout(id, items)` — outer tab chips in up to two rows; otherwise
  identical switching mechanics. (Built in phase b.)

## File structure

```
cpp_ptr_lab/pointers_refs/
  demos/
    basic_ptr.demo.yaml            one demo spec per topic (all 8, incl. both gotchas:
    const_taxonomy.demo.yaml       null_deref AND dangling_ptr)
    ref_must_bind.demo.yaml
    … (8 total) …
  glossaries/
    pointers.glossary.yaml         shared term→def sets, authored per subset;
    references.glossary.yaml        referenced by any layout that wants them
  layouts/
    pointers_refs.rail.yaml        style: left_rail  → dist/pointers_refs.rail/…html   [a]
    pointers_refs.tabs.yaml        style: top_tabs   → dist/pointers_refs.tabs/…html   [b]
```

Demo and glossary files are referenced by the layout relative to the layout
file's directory. The glossary directory layout above is illustrative — an author
may keep one glossary or several, covering whatever subsets they choose.

### Demo spec schema (same shape as today's page specs)

```yaml
title: "Basic Pointer"          # also the nav label for this demo
bake: { bp: basic_ptr }
blocks:
  - callout_note: { id: bp-note, label: Concept, text: "${bp.explanation}" }
  - topic:        { id: bp, source: bp }
  # optional: progressive_steps, predict_reveal_quiz, …
```
Rendered standalone → full page; referenced by a layout → fragment. (Page-level
chrome like the color legend lives in the layout, not repeated per demo.)

### Glossary spec schema

```yaml
title: "Pointers — vocabulary"
terms:
  - { term: "address-of (&)", def: "yields the memory address of an object" }
  - { term: "dereference (*)", def: "accesses the object a pointer points to" }
  - { term: "pointee",         def: "the object a pointer refers to" }
```

**Why glossaries live in YAML (not Python), and kept minimal:**
1. The schema is intentionally flat (`title` + a `terms` list of `{term, def}`)
   so a **future skill can generate a glossary automatically** — the format must
   be trivial to emit and validate by a generator.
2. YAML is easier for the author (and students-as-authors) to edit than Python.
3. As data/skill output it is more portable than embedded Python.
4. Keeping prose out of Python keeps `topics.py` focused on compiled artifacts,
   so the Python stays readable and maintainable.
Corollary: **do not** add computed/baked fields to a glossary — it is prose only.
(The auto-generation skill itself is out of scope for this change.)

### Layout spec schema

```yaml
title: "Pointers & References — Lab 1"
style: left_rail                 # left_rail | top_tabs | stacked
header:                          # rendered ONCE at the top, in order; 0..N glossaries
  - color_legend: { id: legend }
  - glossary: { id: g-ptr, source: glossaries/pointers.glossary.yaml }
  - glossary: { id: g-ref, source: glossaries/references.glossary.yaml }
demos:
  - demos/basic_ptr.demo.yaml
  - demos/const_taxonomy.demo.yaml
  - …all 8…
```

### CLI / build

Extend the engine entry point to detect a layout spec (has `demos:`) vs a plain
page/demo spec (has `blocks:`) and route accordingly:
`python -m cpp_ptr_lab.yaml_engine.render_page <spec.yaml> [dist]`.
A layout writes `dist/<layout-stem>/<layout-stem>.html`.

## Accessibility

- **Text alternatives for all non-text content (WCAG 1.1.1).** Every graphic
  carries a programmatic text alternative:
  - Inline `<svg>` diagrams use `role="img"` + `<title>`/`<desc>` referenced by
    `aria-labelledby` (the SVG equivalent of `alt`), narrated from the baked data.
  - Any real `<img>` (none planned, but if added) MUST carry a meaningful `alt`;
    purely decorative graphics get `alt=""` / `aria-hidden="true"` so they are not
    announced.
  - Icon-only cues (✓/✗ badges, arrows) always pair with visible text, so meaning
    survives even if the glyph is unread.
- Every interactive grouping has an accessible name: the demo nav (rail/tabs) uses
  `role="group"` + `aria-label`; each demo panel is labelled by its title; tab
  labels use `<label for>`.
- Zero-JS radio switching; hidden radios stay in the focus order (clip, not
  `display:none`).
- WCAG 1.4.10 Reflow: single-column fallback at narrow width (desktop-first, not
  desktop-locked).
- Color never the sole cue (badges/consoles keep text + icon + border).

## Testing (TDD, RED first)

Pure (no g++):
- `render_fragment` emits blocks with **no** `<html>`/`<head>`; `render_page`
  still emits the full shell (regression).
- `demo_panel(fake_data)` — variant tabs + code/diagram + badge + output + a
  `<details>`-wrapped byte grid; cases-topic → stacked sub-cases; ids namespaced.
- `glossary(title, terms)` — a `<dl>` with one term/def pair each; ids namespaced;
  loadable from a `*.glossary.yaml` file.
- `left_rail_layout(items)` — one rail radio + panel per item, first checked, no
  dup ids, zero-JS, single-column `@media` rule present.
- layout loader — resolves demo + glossary file refs, renders the `header:` once
  and each demo as a fragment, composes one shell with no duplicate ids across all
  demos and glossaries.

Accessibility (asserted, not assumed):
- Every `<svg>` in the output has an accessible name (`role="img"` + non-empty
  `<title>` via `aria-labelledby`); any `<img>` has a non-empty `alt` (or is
  explicitly decorative). A build test scans the rendered page and fails on any
  graphic lacking a text alternative.
- Nav groups expose `aria-label`; icon cues (✓/✗) co-occur with visible text.

g++-gated (integration):
- Build `pointers_refs.rail.yaml`: all 8 demos present, basic_ptr type tabs,
  const 2×2 stacked sub-cases with the real `read-only` error, PTRDATA baked,
  no duplicate ids, self-contained, and the accessibility scan above passes.
  Phase b: same for `top_tabs`.

## Delivery phases

- **(a) now:** fragment split, `demo_panel`, `glossary`, `left_rail_layout`,
  layout loader + demo/glossary/layout schemas, 8 demo files, ≥1 shared glossary,
  `pointers_refs.rail.yaml` (header with legend + glossary) → one standalone
  left-rail page. Full suite green.
- **(b) next:** `top_tabs_layout` + `pointers_refs.tabs.yaml` → a second
  standalone page from the *same* demo files, for live side-by-side comparison.

## Open items / deferred

- Unify the existing `basic_ptr`/`function_args` standalone pages onto the
  demo/layout mechanism (follow-up; not in this change).
- Eventual packaging of the generator + scripts for other instructors is a
  separate, later concern; it does not affect this design. HTML output stays
  standalone.
