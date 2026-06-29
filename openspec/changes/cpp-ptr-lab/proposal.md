## Why

ISC5305 graduate students need hands-on interactive labs to build concrete intuition
about C++ pointers, references, and smart pointers — concepts they encounter in every
modern C++ codebase but typically only read about in text. The existing
`cpp_initializer_lab` demonstrates that a compile-and-observe Dear PyGui tool is
effective; these two labs extend that approach to cover the most confusion-prone area
of modern C++.

## What Changes

- New `cpp_ptr_lab/` sibling package with shared infrastructure and two distinct labs
- **Lab 1 — Pointers & References**: 8 topics covering raw pointer basics, const
  taxonomy, and three explicit reference invariants (must bind, never null, binding
  immutable)
- **Lab 2 — Smart Pointers**: 7 topics covering `unique_ptr`, `shared_ptr`, and
  `weak_ptr` ownership semantics
- YAML config (`lab_config.yaml`) controls which topics are visible per session —
  instructors can disable topics without modifying code
- Dual right-panel visualization per topic:
  - Panel A (hex bytes): shows raw bytes of the pointer variable and the pointed-to value
  - Panel B (DPG drawlist diagram): annotated arrow diagram from pointer/ref box to
    target box; compile errors → red canvas border, compiler warnings → orange border
- Gotcha topics compile with `-fsanitize=address,undefined` so AddressSanitizer output
  appears in the output panel rather than silent undefined behaviour
- Two separate launchers: `python -m cpp_ptr_lab.run_ptrs` and
  `python -m cpp_ptr_lab.run_smart`

## Capabilities

### New Capabilities

- `pointers-refs-lab`: 8-topic interactive lab (Raw group: basic pointer, const
  taxonomy, null pointer safe display; Refs group: must-bind invariant, no-null
  invariant, rebind-illusion, const-ref; Gotchas: null deref via ASan, dangling pointer
  via ASan)
- `smart-ptrs-lab`: 7-topic interactive lab (unique_ptr: basics, move, copy-error;
  shared_ptr: basics, copy + use_count; weak_ptr: basics, expired)
- `yaml-topic-config`: YAML-driven per-lab topic visibility; topics absent from the
  file default to enabled; entire labs can be disabled with `enabled: false`
- `ptr-diagram-panel`: DPG drawlist canvas panel rendered after each Run, showing
  labelled boxes for pointer/reference variables and targets connected by arrows;
  canvas border color reflects result state (red = compile error, orange = warnings,
  neutral = success); diagram data carried by a `PTRDATA:` line emitted inline in each
  C++ template and parsed by `parse_ptrdata()` in the compiler runner

### Modified Capabilities

- None — `cpp_initializer_lab/` is untouched

## Impact

- **New package**: `cpp_ptr_lab/` alongside `cpp_initializer_lab/` in the repo root
- **New dependency**: `pyyaml` — add to `requirements.txt`
- **Toolchain**: gotcha topics require g++ with ASan support (GCC ≥ 11 or clang ≥ 12);
  lab degrades gracefully if ASan is unavailable (button disabled with tooltip)
- **No breaking changes** to existing code
