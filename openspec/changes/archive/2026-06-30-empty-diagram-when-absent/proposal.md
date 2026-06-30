## Why

When a panel had no pointer data — a compile-failed sub-case, or a topic declared with
`has_ptrdata=False` — the renderer still drew a bordered SVG box reading "type=? — no
diagram" under a "Memory diagram" heading. That placeholder is visual noise: it implies a
diagram exists when none is meaningful, and (in the new multi-sub-case panels) it appeared
next to every forbidden `const_taxonomy` cell. The space should simply be left empty.

## What Changes

- `_case_block` leaves the diagram column empty (`<div class="diagram-col diagram-col--empty"></div>`)
  when the case has no pointer data — defined as `ptrdata` being present but empty, which
  covers compile failures and `has_ptrdata=False` topics.
- The "Memory diagram" heading, `<figure>`, caption, and the `_svg_unknown` placeholder are
  omitted for those cases. Cases with real pointer data render unchanged; legacy variants
  that carry a pre-rendered `svg` (no `ptrdata` key) are unaffected.

## Capabilities

### Modified Capabilities

- `static-html-renderer`: adds the requirement that an absent memory diagram leaves the
  diagram column empty instead of drawing a placeholder.

## Impact

- `cpp_ptr_lab/html_renderer.py` — `_case_block` only.
- `cpp_ptr_lab/tests/test_html_renderer.py` — `TestNoDiagramLeavesEmptySpace`.
- `dist/` regenerated (derived artifact): 0 "no diagram" placeholders; e.g. `const_taxonomy`
  shows 4 empty diagram columns (forbidden cells) and 4 real diagrams (allowed cells).
