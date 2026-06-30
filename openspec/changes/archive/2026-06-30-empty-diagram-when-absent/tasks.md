<!--
  Applying memory rule feedback/testing.md: RED tests written BEFORE implementation.
-->

## 1. RED

- [x] 1.1 `test_html_renderer.py` `TestNoDiagramLeavesEmptySpace`: render two variants (one with `ptrdata`, one failed/`ptrdata=None`); assert exactly one `<svg`, one "Memory diagram" heading, no "no diagram" text, and a `diagram-col--empty` marker. Confirm it fails.

## 2. GREEN

- [x] 2.1 In `_case_block`, compute `no_diagram = "ptrdata" in v and not ptrdata`; when true, emit `<div class="diagram-col diagram-col--empty"></div>` and omit heading/figure/caption
- [x] 2.2 Otherwise render the diagram column as before

## 3. Verification

- [x] 3.1 Full `cpp_ptr_lab` suite green (130 passed)
- [x] 3.2 Rebuild `dist/`; confirm 0 "no diagram" placeholders and `const_taxonomy` shows 4 empty + 4 real diagram columns
- [x] 3.3 `openspec validate empty-diagram-when-absent` passes
