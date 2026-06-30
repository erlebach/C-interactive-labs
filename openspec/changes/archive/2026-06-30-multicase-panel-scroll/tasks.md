<!--
  Applying memory rule feedback/testing.md: RED test written BEFORE implementation.
-->

## 1. RED

- [x] 1.1 `test_html_renderer.py` `test_multicase_panel_scrolls`: assemble a page with a multi-case fragment; assert the `.panel` CSS rule contains `overflow-y: auto`. Confirm it fails.

## 2. GREEN

- [x] 2.1 Add `overflow-y: auto` to the `.panel` rule in `_CSS`
- [x] 2.2 Add `.case` spacing, `.case .panel-grid { height: auto }`, and `.case .diagram-col figure { flex: 0 0 auto; min-height: 200px }`

## 3. Verification

- [x] 3.1 Full `cpp_ptr_lab` suite green (126 passed)
- [x] 3.2 Rebuild `dist/`; confirm `.panel` carries `overflow-y: auto` and const_taxonomy sub-cases scroll
- [x] 3.3 `openspec validate multicase-panel-scroll` passes
