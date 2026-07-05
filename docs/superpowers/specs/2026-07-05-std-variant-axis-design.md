# C++ Standard as a Variant Axis — Design

**Date:** 2026-07-05
**Status:** Approved (awaiting spec review)

## Problem

`compiler_runner.py` hardcodes `-std=c++20` in four places. Students never see that
the *same* C++ source compiles and behaves differently under different language
standards (e.g. structured bindings, `auto` return deduction, designated
initializers). We want a topic to compile one program under several standards and
present them as zero-JS, CSS-radio selectable tabs — the same mechanism
`const_taxonomy` already uses for its type tabs.

## North Star fit

- **Data-over-code:** authoring a standards demonstration adds YAML only (one new
  field), no new Python per topic.
- **Minimize-JS / WCAG-AA:** reuses the existing CSS-radio variant tabs — no new
  JS, no new rendering code.
- **Static build:** each standard is compiled at build time; its baked output
  (green "compiled" or red "compile error") is frozen into the page.

## Design

### 1. Authoring — one new field

A topic YAML opts in with:

```yaml
standards: [11, 17, 20]     # any subset/order of 11 / 14 / 17 / 20
```

Absent or empty ⇒ today's behavior, unchanged. The list order is the tab order.

`TopicTemplate` gains `standards: list[int] = field(default_factory=list)`;
`topic_yaml._topic` reads `d.get("standards", [])`.

### 2. Compile plumbing

The hardcoded `-std=c++20` in `compiler_runner.py` becomes a parameter
`std: str = "c++20"` on `_compile`, `compile_only`, and `compile_and_run`. The
compile command builds `["g++", f"-std={std}", ...]`. The default `"c++20"` keeps
every existing caller byte-for-byte identical.

### 3. Variant expansion

`build_html.expand_variants(topic)`: when `topic.standards` is non-empty, return one
control-state per standard, each carrying a synthetic key:

```python
[{"__std__": "11"}, {"__std__": "17"}, {"__std__": "20"}]
```

This reuses the existing per-variant pipeline, so the tabs render with **zero
rendering-code change**. `__std__` is a reserved control id — it is never a real
`ControlDef` and never substituted into the template.

### 4. Label + compile

- `capture_variant`: when `__std__` is present in the state, the variant label is
  `f"C++{state['__std__']}"` (e.g. `C++17`). (Standards topics have no dropdown
  controls — see §5 — so there is no other label source to merge with.)
- `_compile_one`: reads `control_state.get("__std__")`; if present, passes
  `std=f"c++{n}"` to `compile_and_run`. Absent ⇒ omit (defaults to `c++20`).

A C++17-only program then shows a **red compile-error badge** under `C++11` and a
**green compiled badge** under `C++17` / `C++20`, using the existing
compile-vs-runtime `error_kind` classification.

### 5. The rule — standards-only (Q2)

Load-time validation in `topic_yaml._topic`: a topic with a non-empty `standards`
must have **no dropdown controls** (`kind == "dropdown"`). Violation raises
`ValueError` naming the topic id and the offending control. Free-text and checkbox
controls remain allowed (they bake to a single value and don't create a competing
tab row). This guarantees a topic shows exactly one tab row — its content tabs *or*
the standard tabs, never two. The Cartesian (N standards × M types) combination is
deliberately deferred; add it only if a real lesson needs it.

### 6. Demonstration (Q3)

One new topic demonstrates the axis end-to-end with **structured bindings**:

```cpp
#include <utility>
#include <iostream>
int main() {
    auto [a, b] = std::pair{1, 2};   // C++17 structured bindings
    std::cout << a << " " << b << "\n";
}
```

- `standards: [11, 17, 20]`, `diagram: false`, no memory harness (template omits
  `<<HARNESS>>`), `has_ptrdata: false`.
- Expected baked result: **C++11 → compile error (red)**; **C++17 / C++20 →
  compiled, output `1 2` (green)**.
- Hosting: the plan chooses the lightest option — a minimal new subject folder
  (`topics/` + one rail layout, the standard "drop a folder" pattern) or adding the
  topic to a fitting existing subject. Either way it is YAML + layout only.

## Testing (TDD)

1. **compiler_runner** — `compile_and_run(src, std="c++11")` (and `compile_only`)
   put `-std=c++11` in the command; default call still uses `-std=c++20`.
2. **topic_yaml** — loading a topic with `standards: [11, 17, 20]` sets
   `.standards == [11, 17, 20]`; loading a topic with both `standards` and a
   dropdown control raises `ValueError`.
3. **expand_variants** — a standards topic yields one state per standard, each with
   the correct `__std__`; a non-standards topic is unchanged.
4. **capture_variant / _compile_one** — label is `C++17`; the compile uses the
   matching `-std` (assert via a std-sensitive snippet, e.g. structured bindings
   failing on C++11 and passing on C++17).
5. **integration** — build the demo page; assert three tabs labeled
   `C++11 / C++17 / C++20`, with the C++11 variant a compile failure (red) and the
   C++20 variant green.

## Out of scope

- Cartesian combination of standards with other dropdown axes (deferred; §5).
- Per-standard *different* source (rejected — overlaps with cases/controls).
- Changing the default standard for non-opted-in topics (stays `c++20`).

## Files expected to change

- `cpp_labs/compiler_runner.py` — `std` param on `_compile` / `compile_only` /
  `compile_and_run`.
- `cpp_labs/code_generator.py` — `TopicTemplate.standards` field.
- `cpp_labs/topic_yaml.py` — read `standards`; standards-only validation.
- `cpp_labs/build_html.py` — `expand_variants` `__std__` states; `capture_variant`
  label; `_compile_one` std flag.
- New demo topic YAML + minimal layout (subject TBD by plan).
- Tests across `cpp_labs/tests/` (compiler_runner, build_html, topic_yaml,
  integration).

No interface-catalog change (no new block keyword or component signature).
