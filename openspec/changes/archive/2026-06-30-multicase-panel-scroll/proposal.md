## Why

The `multi-subcase-panels` capability stacks several `.panel-grid` blocks inside one
`.panel`, but the surrounding layout (from `tab-layout-renderer`) was designed for exactly
one full-height grid: `.panels` is `overflow:hidden` and `.panel` did not scroll, while
single-case topics fit because long code scrolls internally in `.code-col`. As a result
multi-case topics (`const_taxonomy`, `weak_cycle`) clipped their stacked sub-cases with no
scrollbar — the second sub-case was unreachable. This regresses the capability and must be
corrected with a stated requirement so it does not recur.

## What Changes

- `.panel` becomes vertically scrollable (`overflow-y: auto`) so stacked sub-cases are
  reachable; single-case panels are unaffected (their grid is exactly `height:100%`).
- Within a multi-case panel, each sub-case grid is content-height (`.case .panel-grid {
  height:auto }`) and its diagram keeps a usable `min-height` instead of relying on the
  single-case full-height fill chain.

## Capabilities

### Modified Capabilities

- `multi-subcase-panels`: adds the requirement that stacked sub-cases remain scrollable and
  each retains a usable diagram height.

## Impact

- `cpp_ptr_lab/html_renderer.py` — `_CSS` only (`.panel` overflow + `.case` rules).
- `cpp_ptr_lab/tests/test_html_renderer.py` — `test_multicase_panel_scrolls`.
- `dist/` regenerated (derived artifact).
