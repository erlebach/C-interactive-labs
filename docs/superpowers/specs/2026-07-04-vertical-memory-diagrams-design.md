# Vertical Memory Diagrams — Design

**Date:** 2026-07-04
**Status:** approved for implementation
**Scope:** Re-orient the `cpp_labs` SVG memory diagrams from horizontal to vertical so the
code column can widen on diagram pages. Implementation only — **no skill authoring** in this
change (see Roadmap).

## Problem

Every memory diagram renders into a fixed wide box: `svg_renderer` → `_svg_*` →
`_wrap_svg` hardcodes `viewBox="0 0 500 160"` (~3:1). Boxes are placed left→right and
`_arrow()` only ever draws a horizontal line + a hand-built `<polygon>` arrowhead
(`mid_y = y1`). On a `diagram: true` page the diagram column (`code_diagram_panel`, currently
`2fr:1fr`) is therefore forced wide-and-short, wasting its own height and capping how much
width the code column can take.

## Goal

A **tall + narrow** diagram (~2:3) so the diagram column can shrink and the code column widen
(`3fr:1fr`), with the diagram's height lining up with multi-line code instead of floating in
white. Accessibility (`role="img"` + `<title>`/`<desc>`) and all data (addresses, values,
`NULL`, `use_count`) are preserved.

## Decisions (locked with user)

1. **Vertical stacked orientation ("style B"):** source box on top, arrow pointing **down**,
   target box below.
2. **Source-count layout rule** (lives in ONE place, not per-type):
   - **≤2 sources** → boxes side-by-side on top, arrows **converge** down onto the target.
   - **≥3 sources** → single stacked column, arrows route down one side into the target.
   - **Build both branches now.** Today only the ≤2 branch has real callers (max is
     `shared_ptr` with `sp1`+`sp2`); the ≥3 branch is exercised by synthetic tests and
     future-proofs multi-alias diagrams.
3. **Real arrowheads:** replace hand-drawn `<line>`+`<polygon>` with a reusable
   `<marker orient="auto">` referenced via `marker-end`, so vertical / diagonal (converging) /
   any future curved arrows all get correct auto-rotated heads.
4. **Typography = code panel:** box text is **`14px ui-monospace, monospace`** — identical to
   the code panel (`14px/1.5 ui-monospace, monospace`) — replacing the current 11/12/16/18 mix,
   for both label and address lines.
5. **Grid ratio:** `code_diagram_panel` widens `2fr:1fr` → **`3fr:1fr`** (tunable in-browser).

## Architecture

Introduce one vertical-layout helper that encodes the source-count rule:

```
_stack_svg(p, title, desc, sources, target) -> str
```

- `p` — unique id prefix (unchanged accessibility contract).
- `sources` — list of box descriptors (text lines + stroke color). One entry for
  `raw`/`ref`/`unique`/`null`/`weak`; two for aliased `shared_ptr`.
- `target` — one box descriptor **or `None`** (`weak_ptr` has no target box).
- Computes coordinates, picks converge (`len(sources) <= 2`) vs stacked (`>= 3`) arrow layout,
  computes its own tall+narrow `viewBox`, then wraps via existing `_wrap_svg`.

Each `_svg_raw/null/ref/unique/shared/weak` becomes a thin adapter: build its box list +
target, call `_stack_svg`. The six renderers stop owning geometry (data-over-code).

### Per-type mapping

| Type | Sources | Target | Shape |
|------|---------|--------|-------|
| `raw` | `ptr` | `val=…` + addr | 1 box → arrow down → target |
| `null` | `ptr` | `NULL` (red) | 1 box → **red** arrow down → red box |
| `ref` | `ref` | `val=…` + addr | 1 box → arrow down → target |
| `unique` | `unique_ptr` | target **or** `NULL` (red) | 1 box → arrow down → target/NULL |
| `shared` (1 owner) | `shared_ptr` | `val` + addr + `use_count` | 1 box → arrow down → target |
| `shared` (2 owners) | `sp1`, `sp2` | `val` + addr + `use_count` | **2 boxes side-by-side → converge down** |
| `weak` | `weak_ptr` (expired, use_count) | **None** | single box, no arrow |
| `unknown` | fallback text | — | unchanged |

## Accessibility & typography

- Box text `14px ui-monospace, monospace` (matches code) for label and address lines.
- SVG scales its user units when `width:100%`. To keep text visually ≈14px, the diagram gets an
  **intrinsic px width equal to its `viewBox` width, capped with `max-width`**, so in the common
  case 1 user-unit ≈ 1px. It scales down gracefully on very narrow screens (mobile reflow already
  handles this).
- Contrast: labels `#1a1a1a` on light box fill (~15:1); addresses in existing dim gray (≥7:1);
  both clear WCAG AA. `NULL`/error red is an accent only — the word "NULL" carries the meaning.
- `role="img"` + `<title>`/`<desc>` via `_wrap_svg` unchanged → tested invariant
  `svg-count == role=img-count` holds.

## Testing (TDD, RED→GREEN)

- Rewrite the single geometry test (`test_html_renderer.py::test_has_viewbox`, pins
  `viewBox="0 0 500 160"`) to assert the new vertical `viewBox`.
- Add tests for the source-count branch: 1 source and 2 sources → converge; a synthetic 3-source
  input → stacked. Assert arrow count and rough box positions (top row vs bottom).
- Keep green: all `role="img"` / `<title>` / `<desc>` / address / value / `NULL` assertions and
  the `pointers_refs` `svg-count == role=img-count` invariant.
- Rebuild all pages (`./build_labs.sh`); run full `cpp_labs` suite.

## Out of scope / Roadmap (future, separate brainstorms)

Three-level skill hierarchy, to be built **leaf-first, each against working code**:

1. **Diagram-generation skill** (leaf) — box/arrow/marker primitives, the source-count rule, the
   14px-matches-code + `max-width` ADA convention, the `_wrap_svg` accessibility contract.
   Authored immediately *after* this implementation is proven.
2. **Demonstration skill** (composite) — construct a whole demonstration HTML file for a new
   subject (e.g. `stackframes`): generate its glossary(ies), concepts, demos, topics, and
   diagrams. Composes the diagram skill.
3. **Course skill** (top) — assemble many demonstration HTML files into a course, linked via an
   `index.html` or similar.

Rationale for deferring: a skill should document *working reality*, not intent; the diagram
implementation is a tight TDD unit, whereas the composite skills involve glossary/concept/topic
generation that deserves its own design.
