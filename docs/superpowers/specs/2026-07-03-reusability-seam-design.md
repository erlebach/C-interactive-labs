# Reusability seam — unified nav + shared prose panels

**Date:** 2026-07-03
**Status:** Approved (design); ready for implementation plan.
**Depends on / follows:** the demos-and-layouts engine (`2026-07-01-demos-and-layouts-design.md`),
the source→YAML migration (`2026-07-02-source-to-yaml-design.md`), and the two reusability
quick-wins already landed on `feat/op-overload` (single-variant tab suppression; loader promotion
to `cpp_ptr_lab/topic_yaml.py`).

## 1. Purpose

Close the reusability wart the engine still carries and act on a UI observation from the
pointers_refs page:

1. **The nav interface is leaky.** `build_layout` special-cases `if style == "left_rail":`
   because `left_rail_layout` takes extra kwargs (`italic_count`, `selected`) that the other
   two nav styles do not. The three styles have inconsistent signatures, so choosing a layout
   style is not yet a pure data decision.
2. **The per-example "Concept" box eats vertical space.** Each `*.demo.yaml` opens with an
   always-open `callout_note: {label: Concept, …}` rendered inline above the demo. It is useful
   but bulky.
3. **Vocabulary and Concept are the same kind of thing** — reusable prose/reference panels —
   and should share one rendering behavior instead of being two unrelated components.

Non-goals (YAGNI): authoring a `top_tabs`/`stacked` page now (we only make the seam honest so
one is a one-line change later); a separate `objective` field; JS modal pop-ups; a new file
type for demonstration-concept text.

## 2. Locked vocabulary

Precise terms, user-locked 2026-07-03 (supersedes the older "demo = one whole topic" wording):

- **Demonstration** — one HTML file = one topic (e.g. *Pointers*). Always contains several
  examples and gotchas. (Earlier notes called this the "layout / page / subject".)
- **Example** — one rail entry inside a demonstration (*Basic Pointer*, *const Taxonomy* …).
  (Earlier called a "demo".)
- **Gotcha** — an example whose point is a failure (*Null Deref*, *Dangling Ptr*).
- **Concept** — prose stating *what this is meant to impart* (subsumes "objective" — **one**
  field, not two). Two levels:
  - **Demonstration Concept** — the objective of the whole file (one per demonstration,
    optional). **New — does not exist today.**
  - **Example Concept** — the reason a given example exists (per rail entry, optional). This is
    today's inline `callout_note` box.

## 3. Design

Four cohesive changes, all on the demo/nav seam. Every rendered artifact stays **self-contained,
zero-JS at runtime, WCAG-AA**; svg-count still equals `role="img"`-count; no bare `<pre>`.

### A. Unified nav interface — `nav_shell`

Add one component in `components.py`, beside the existing nav functions:

```
nav_shell(comp_id, items, *, style="left_rail", leading=0, selected=None) -> str
```

- `items` — the existing `list[(label, body_html)]` (leading reference entries first, then examples).
- `style` — `"left_rail"` (default) | `"top_tabs"` | `"stacked"`. Unknown → `ValueError` listing
  valid choices (moved out of `build_layout`).
- `leading` — count of leading reference entries (glossaries + demonstration concept) to set apart;
  `left_rail` renders them italic, other styles ignore it.
- `selected` — index shown on load; `left_rail` and `top_tabs` honor it, `stacked` ignores it.

Every style accepts the identical signature and ignores what it does not use. `nav_shell`
dispatches internally to the concrete renderers (`left_rail_layout`, `variant_tabs` for top_tabs,
a stacked fallback). `build_layout` computes `leading` and `selected` **once** and calls
`nav_shell(...)` with **no per-style branch**. The `_LAYOUTS` dict and the `if style ==
"left_rail":` block in `render_page.build_layout` are removed; `_stacked_layout` moves into
`components.py` as the stacked branch of `nav_shell` (or a private helper it calls).

**Invariant:** for the existing pointers_refs and op_overload layouts (both `left_rail`), the
generated HTML is **byte-identical** to today (same `italic_count`, same `selected`). This is the
regression guard for Section A.

### B. Shared prose-panel behavior (Vocabulary + Concept)

Both `callout_note` and `glossary` already draw a bordered box; factor the shared container into
one private helper (e.g. `_prose_box(comp_id, *, title=None, body_html, aria=…)`) that both
delegate to, so Vocabulary (glossary) and Concept render through **one** behavior. This is the
"behavior class that Vocabulary and Concept inherit" — honestly, in this functional codebase it is
a **shared renderer/helper (composition)**, not literal Python class inheritance; the effect
(one place defines the prose-panel look/semantics) is the same.

No visual change is required for glossary; the helper simply captures what both already do so a
future prose entry type is free.

### C. Example Concept → `<details>` disclosure

Add a `concept` block builder to `render_page` (`_BUILDERS`) and a matching component:

```
concept_note(comp_id, text, *, label="Concept", open=False) -> str
```

renders a native `<details>` whose `<summary>` is the label and whose body is the prose (through
the Section-B shared box). Default **collapsed** (D1). Placed as the first block of each example
panel.

Each `*.demo.yaml` changes its opening block from
`- callout_note: { id: …, label: Concept, text: "${x.explanation}" }`
to
`- concept: { id: …, text: "${x.explanation}" }`
(the `label` defaults to `Concept`; `open: true` is available per example). Applies to all
pointers_refs demos (8) and op_overload demos (4).

Accessibility: `<details>/<summary>` is natively keyboard- and screen-reader-operable
("Concept, collapsed"); no ARIA needed, no JS.

### D. Demonstration Concept (new, optional)

The layout YAML gains an optional top-level `concept:` block with inline `text:` (D3 — inline, no
new file type). `build_layout` renders it through the Section-B shared box and prepends it to the
leading rail entries (alongside `glossaries:`), italic-labeled and set apart from the examples. It
is **not** selected on load (D2 — the first example stays the on-load panel); it is a clickable
leading entry like Vocabulary. Absent `concept:` → nothing changes (backward compatible).

`leading` passed to `nav_shell` today is `len(glossary_items)` (e.g. 2 for pointers_refs:
*Vocabulary* + *Reference Terms*); it becomes `len(demonstration_concept) + len(glossary_items)`.
`selected` stays "first example" = that leading count. When no demonstration `concept:` is
present, `leading` is unchanged from today and the output is byte-identical.

## 4. Components / files touched

- `cpp_ptr_lab/components.py` — add `nav_shell`, `concept_note`, `_prose_box`; refactor
  `callout_note`/`glossary` onto `_prose_box` (no output change). `variant_tabs`,
  `left_rail_layout` unchanged in signature.
- `cpp_ptr_lab/yaml_engine/render_page.py` — add `concept` to `_BUILDERS`; `build_layout` renders
  optional `concept:`, computes `leading`/`selected`, calls `nav_shell`; delete `_LAYOUTS` and the
  `left_rail` branch; `_stacked_layout` folds into `nav_shell`.
- `cpp_ptr_lab/pointers_refs/demos/*.demo.yaml` (8) + `cpp_ptr_lab/op_overload/demos/*.demo.yaml`
  (4) — `callout_note` Concept block → `concept` block.
- `cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml` — optional: add a demonstration
  `concept:` (demonstrates the new capability; content is authoring, not engine).
- Docs: `COURSE_VIA_TOPICS.md`, `usage/USAGE.md`, `cpp_ptr_lab/pointers_refs/YAML_GUIDE.md` —
  document `nav_shell`, the `concept` block, and demonstration `concept:`; update the locked
  vocabulary.

## 5. Testing (TDD, RED→GREEN)

- **`nav_shell` uniform dispatch** — one signature drives all three styles; unknown style raises;
  `stacked` ignores `leading`/`selected`; `top_tabs` honors `selected`.
- **left_rail regression guard** — `nav_shell(items, style="left_rail", leading=n, selected=s)`
  returns exactly what `left_rail_layout(items, italic_count=n, selected=s)` returns today
  (byte-for-byte), so the refactor is provably lossless.
- **`concept_note`** — emits `<details>`, `<summary>Concept`, collapsed by default; `open=True`
  adds the `open` attribute; body escapes text.
- **shared prose box** — `glossary` output is unchanged after the `_prose_box` refactor
  (guard test); `concept_note` and `glossary` share the container class/border.
- **`concept` block builder** — a demo spec with a `concept:` block renders the disclosure at the
  top of the example; `${x.explanation}` resolves.
- **Demonstration Concept** — a layout with `concept:` yields an extra italic leading rail entry;
  `leading` increments; first example still selected on load; absent `concept:` is byte-identical
  to today.
- **Integration** — pointers_refs and op_overload pages rebuild self-contained, WCAG-AA, svg-count
  == `role="img"`-count; full suite green (currently 423). g++-gated build tests skip without g++.

## 6. Rollout

Single implementation plan, TDD-ordered. Section A (nav_shell) first with its byte-identical guard;
then B (shared box, guarded); then C (concept disclosure + demo YAML edits); then D (demonstration
concept). Rebuild both pages and eyeball via `python3 -m http.server -d dist` (Playwright `file://`
is blocked). Commit in the four logical groups above.
