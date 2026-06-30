## Context

A panel today maps 1:1 to one compiled program (`capture_variant` → one source → one
stdout/diagram). `const_taxonomy` needs to show, per `const` type, both an allowed and a
forbidden operation — but the forbidden one fails to compile and therefore has no runtime.
So one panel must hold several *independently compiled* programs.

## Key Decision: sub-cases are a build-time axis, not a second dropdown

Two dropdowns (type × operation) would produce 8 flat tabs and lose the per-type
allow/forbid contrast. Instead the operation axis is expressed as `TopicTemplate.cases`
— a build-time list compiled per variant and rendered stacked *inside* each type tab. The
type dropdown remains the tab axis (4 tabs), each showing its 2 sub-cases. `expand_variants`
is untouched; only `capture_variant` and `_panel_body` branch on `cases`.

Rejected alternative (commented-out forbidden line + printed "FORBIDDEN" note): keeps a
diagram on every panel but the error is *asserted by us*, not produced by the compiler, and
can rot. Authentic g++ diagnostics are the pedagogical point, so sub-cases win.

## Data shape

- `CaseDef(label: str, subs: dict[str,str])` — `subs` fills extra placeholders (`<<op>>`).
- `generate_source(topic, control_state, extra_subs=None)` — `extra_subs` applied after
  control resolution.
- `capture_variant` → `{"label": <type>, "cases": [<result>, …]}` when `topic.cases` set,
  else the prior flat `{"label", "source", "failed", …}` dict (backward compatible — the
  renderer keys on presence of `"cases"`).
- Sub-case result dicts reuse the existing render-data shape (`source/ptrdata/svg/stdout/
  membytes/failed/stderr`), built by the extracted `_compile_one`.

## Rendering

`_panel_body` → if `"cases"`: emit one `<div class="case"><h3 class="case-label">…</h3>` +
`_case_block(case, f"{prefix}-c{j}")` per case (unique svg id prefix per case); else
`_case_block(v, prefix)`. `_case_block` is the former single-panel body verbatim.

A failing sub-case adds an `out--err` modifier to its compiler-output box; CSS gives
`.out--err` a 2 px red border so the failure is obvious beyond the red "Compile failed."
text.

## const_taxonomy truth table (verified by integration test)

| type (tab) | `*ptr = 99` | `ptr = &other` |
|---|---|---|
| `int*` | OK | OK |
| `const int*` | FAIL | OK |
| `int* const` | OK | FAIL |
| `const int* const` | FAIL | FAIL |

`int other = 7;` is declared so `ptr = &other;` compiles where allowed; the compile command
is `g++ -std=c++20` (no `-Werror`), so `other` being unused in the write case does not
corrupt the table.

## Recorded fixes (already implemented, regression-tested)

- **CSS-safe ids:** `_vid` maps every non-`[A-Za-z0-9_-]` char to `_`. Unescaped `(` is a
  CSS parse error and `,` splits the selector, so punctuated variant labels had silently
  dropped the `:checked ~ .panels` rule (empty panels).
- **Boolean default resolution:** `expand_variants` seeds checkbox defaults with the real
  value (preserving `bool`) instead of `str(False)`, so `_resolve_control_value` keys on
  `"false"`/`"true"` in `value_map` rather than emitting a bare `False`.
