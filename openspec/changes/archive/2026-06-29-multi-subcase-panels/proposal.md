## Why

The `const_taxonomy` topic rendered four near-identical programs that differed only in the
declaration line and attempted no mutation, so every variant compiled and printed the same
thing — the lesson (which `const` qualification forbids which operation) was never
demonstrated. A single program cannot show both an allowed and a forbidden operation,
because a `const` violation is a compile-time, all-or-nothing event per translation unit.

To teach the real 2×2 truth table (const-pointee blocks `*ptr = …`; const-pointer blocks
`ptr = …`) with *authentic* compiler errors rather than asserted comments, the panel model
needs to hold more than one independently-compiled program. This change adds a reusable
**multi-sub-case panel** capability and applies it to `const_taxonomy`.

It also records two correctness fixes made while investigating the topic, and the
long-standing request that a failing case's compiler-output box carry a visible error
border (not merely red text).

## What Changes

- **New build-time sub-case model.** `TopicTemplate` gains an optional `cases: list[CaseDef]`;
  each `CaseDef(label, subs)` is compiled independently and shown stacked inside one variant
  panel. `generate_source` gains an `extra_subs` argument to fill per-case placeholders
  (e.g. `<<op>>`).
- **Independent per-case compilation.** `capture_variant` compiles one program per `CaseDef`
  and returns the variant with a `cases` list; topics without `cases` are unchanged.
- **Multi-case rendering.** `html_renderer._panel_body` renders one labelled block per
  sub-case (own code, real compile verdict, output, diagram, unique svg ids), via an
  extracted `_case_block`; single-case variants render exactly as before.
- **`const_taxonomy` redesign.** Drops the `mutate` checkbox; four type tabs (`<<decl>>`)
  × two cases (`*ptr = 99` / `ptr = &other`) produce the full const truth table with real
  g++ errors and real diagrams for the allowed cells.
- **Failing-case error border.** A sub-case that fails to compile renders its
  compiler-output box with a distinct red border.
- **Fix (recorded):** generated element `id`s are sanitised to valid CSS identifiers, so
  variant labels containing `(` `)` `,` no longer silently break the `:checked ~` selector.
- **Fix (recorded):** boolean (checkbox) control defaults resolve through `value_map`
  instead of being stringified to a bare `False`, which had injected an undeclared
  identifier into the generated C++.

## Capabilities

### New Capabilities

- `multi-subcase-panels`: a panel may hold several independently-compiled sub-cases, each
  labelled with its own code, compile verdict, output and diagram; used to demonstrate
  passing-and-failing snippet pairs (first consumer: `const_taxonomy`).

### Modified Capabilities

- `static-html-renderer`: adds the invariant that generated element ids are CSS-identifier-safe.
- `static-html-build`: adds the invariant that boolean control defaults resolve via `value_map`.

## Impact

- `cpp_ptr_lab/code_generator.py` — `CaseDef`, `TopicTemplate.cases`, `generate_source(extra_subs=)`.
- `cpp_ptr_lab/build_html.py` — `_compile_one` extracted; `capture_variant` cases branch; bool-default seeding fix.
- `cpp_ptr_lab/html_renderer.py` — `_case_block` extracted; multi-case `_panel_body`; CSS-safe `_vid`; failing-case border CSS.
- `cpp_ptr_lab/pointers_refs/topics.py` — `const_taxonomy` redesigned around `cases`.
- Tests across `test_code_generator.py`, `test_build_html.py`, `test_html_renderer.py`, `test_integration.py`.
- `dist/` regenerated (derived artifact).
