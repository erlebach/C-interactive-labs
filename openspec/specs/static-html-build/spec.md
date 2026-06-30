# static-html-build Specification

## Purpose
TBD - created by archiving change cpp-ptr-lab-static-html. Update Purpose after archive.
## Requirements
### Requirement: Build-time variant capture

For each topic and each of its variants, the build SHALL generate the C++ source
via the existing `generate_source`, compile and run it via the existing
`compiler_runner`, and capture the result into render data: parsed `PTRDATA:`
(via `parse_ptrdata`), parsed `MEMBYTES:` (via `parse_membytes`), program stdout,
and the generated source. Variants whose template is expected to fail compilation
MUST capture and retain the compiler stderr instead of program output, so the
failure can be shown in the rendered HTML.

#### Scenario: Successful variant captures output and diagram data
- **WHEN** a variant compiles and runs successfully
- **THEN** the build records its parsed `PTRDATA` dict, its `MEMBYTES` hex string, its program stdout, and its generated source for rendering

#### Scenario: Compile-failure variant captures stderr
- **WHEN** a variant is a deliberate compile error (e.g. `ref_must_bind`)
- **THEN** the build records the compiler stderr and marks the variant as a compile failure rather than discarding it

#### Scenario: Variant expansion covers each control combination
- **WHEN** a topic exposes a categorical control (e.g. a type dropdown or compile-mode selector)
- **THEN** the build produces one captured variant per pedagogically meaningful option of that control

### Requirement: Dual output grouping

From the same captured fragments, the build SHALL emit two groupings: per-topic
standalone files under `dist/topics/<topic_id>.html` (Canvas-paste granularity)
and per-lab combined files under `dist/lab_<lab>.html` (single offline file per
lab). Both groupings MUST be produced from the identical underlying fragments so
their content does not diverge.

#### Scenario: Per-topic files are emitted
- **WHEN** the build runs for a lab's topic list
- **THEN** one standalone, self-contained HTML file is written per topic under `dist/topics/`

#### Scenario: Per-lab combined file is emitted
- **WHEN** the build runs for a lab
- **THEN** a single combined HTML file containing every topic of that lab is written as `dist/lab_<lab>.html`, with all topic ids namespaced so no `:checked` state leaks between topics

#### Scenario: Build degrades when the toolchain is unavailable
- **WHEN** `g++` is not available at build time
- **THEN** the build reports the missing toolchain clearly and does not emit silently-empty or partially-baked output

### Requirement: Boolean control defaults resolve through value_map

When `expand_variants` seeds a non-dropdown control's default into the variant control-state, it SHALL preserve the default's type rather than stringifying it. A checkbox default of `False` MUST reach `generate_source` as a boolean so `_resolve_control_value` keys the control's `value_map` on `"false"`/`"true"`, instead of emitting the stringified `"False"` (an undeclared identifier) into the generated C++.

#### Scenario: checkbox default maps to its value_map entry

- **WHEN** a topic has a checkbox control with `default=False` and a `value_map` keyed by `"false"`/`"true"`, and its variants are expanded and their source generated
- **THEN** the generated source contains the `value_map["false"]` text and does not contain a bare `False`

