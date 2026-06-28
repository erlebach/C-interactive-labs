# code-generation Specification

## Purpose
TBD - created by archiving change cpp-initializer-lab. Update Purpose after archive.
## Requirements
### Requirement: Template-based C++ source generation per topic
The system SHALL generate a C++ source string from a topic-specific template by substituting named placeholders with the current values of the topic's UI controls. Each topic SHALL define its own template.

#### Scenario: Generating a value-init snippet
- **WHEN** the active topic is "value init" and the type control is "int" and the value control is "5"
- **THEN** the generated source contains `int x{5};` (brace form) and the memory-dump harness referencing `x`

#### Scenario: Generating a copy-init snippet with explicit
- **WHEN** the active topic is "copy init", the type is a struct with an explicit constructor, and the "explicit" checkbox is checked
- **THEN** the generated source contains the struct definition with the `explicit` keyword and a copy-initialization line `Foo f = 42;` which is expected to fail compilation

### Requirement: Memory-dump harness injection
The generated source SHALL include an instrumentation harness that, after the target initialization, prints the variable's type name, size in bytes, and raw bytes to stdout in a parseable format (e.g., a line beginning with `MEMBYTES:`). The harness SHALL be clearly delimited by comments marking it as instrumentation.

#### Scenario: Harness output is parseable
- **WHEN** a generated snippet is compiled and run successfully
- **THEN** stdout contains a `MEMBYTES:` line followed by the hex byte representation of the target variable

#### Scenario: Harness is visually distinct from the lesson
- **WHEN** the generated source is displayed in the code panel
- **THEN** the harness code is wrapped in comments such as `// --- instrumentation (not part of the lesson) ---`

### Requirement: Control state to placeholder mapping
The system SHALL maintain a mapping from each UI control's identifier to a template placeholder name. When controls change, the system SHALL re-render the template with the updated placeholder values.

#### Scenario: Changing type control updates placeholder
- **WHEN** the type dropdown changes from "int" to "double"
- **THEN** the `{type}` placeholder in the active topic's template resolves to "double" and the code panel updates accordingly

