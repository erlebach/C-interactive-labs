## ADDED Requirements

### Requirement: Lab window with 8 topic tabs
The lab SHALL open a single Dear PyGui viewport titled "C++ Pointers & References Lab"
containing a tab bar with one tab per enabled topic, ordered as defined in
`pointers_refs/topics.py`. Tabs disabled via `lab_config.yaml` SHALL be absent from
the tab bar entirely.

#### Scenario: All topics enabled
- **WHEN** `lab_config.yaml` has all 8 pointers-refs topics set to `true`
- **THEN** the tab bar shows exactly 8 tabs in declaration order

#### Scenario: Topic disabled in YAML
- **WHEN** `basic_ptr: false` is set in the `pointers_refs` section
- **THEN** the tab bar shows 7 tabs and the Basic Pointer tab is absent

### Requirement: Per-topic two-column layout
Each topic tab SHALL use the same two-column layout as `cpp_initializer_lab`: left
column with explanation text and controls, right column with code panel, compiler
command box, output panel, hex-bytes panel, and diagram canvas.

#### Scenario: Tab switch restores state
- **WHEN** the user runs a topic, then switches to another tab and back
- **THEN** the output, hex-bytes, and diagram panels show the previous result

### Requirement: const_taxonomy topic control matrix
The `const_taxonomy` topic SHALL provide a dropdown with four fully-spelled-out options
and a checkbox labelled "Attempt mutation through pointer". The dropdown options SHALL
be: `int*`, `const int*`, `int* const`, `const int* const`. Each option SHALL include
a parenthetical explaining mutability (e.g., "int* (pointer and value both mutable)").

#### Scenario: const int* with mutation attempted
- **WHEN** dropdown is `const int*` and mutation checkbox is checked
- **THEN** the generated C++ does not compile; output panel shows g++ error;
  diagram canvas shows a red border

#### Scenario: int* with mutation attempted
- **WHEN** dropdown is `int*` and mutation checkbox is checked
- **THEN** the generated C++ compiles and runs successfully; diagram shows neutral border

### Requirement: ref_const topic uses T& / const T& with T defined
The `ref_const` topic SHALL provide a dropdown with options `int&` and `const int&`.
The explanation text SHALL define T inline: "where T is the type of the referred-to
object (e.g., `int`, `double`)." A checkbox labelled "Attempt modification through
reference" SHALL be provided.

#### Scenario: const int& modification attempted
- **WHEN** dropdown is `const int&` and modification checkbox is checked
- **THEN** compilation fails; diagram canvas shows red border

#### Scenario: int& modification succeeds
- **WHEN** dropdown is `int&` and modification checkbox is checked
- **THEN** compilation succeeds; diagram shows arrow from r to x with updated value

### Requirement: Three reference-invariant topics
The lab SHALL include three topics that each isolate one reference invariant and
contrast it with pointer behaviour:

1. `ref_must_bind` — reference must be bound at declaration (Invariant 1)
2. `ref_no_null` — reference cannot validly be null (Invariant 2)
3. `ref_rebind_illusion` — assigning through a reference does not rebind it (Invariant 3)

Each topic explanation SHALL use the phrase "Contrary to pointers" to make the
contrast explicit.

#### Scenario: ref_must_bind compile error
- **WHEN** the `ref_must_bind` topic shows `int& r;` (no initializer)
- **THEN** compilation fails with a g++ error about uninitialized reference;
  contrast code showing `int* p;` is shown in the explanation as valid

#### Scenario: ref_rebind_illusion address proof
- **WHEN** the `ref_rebind_illusion` topic is run with default values
- **THEN** program stdout prints `&r == &a: true` even after `r = b` executes;
  diagram shows arrow from r still pointing to box a

### Requirement: Gotcha topics use AddressSanitizer
The `null_deref` and `dangling_ptr` topics SHALL compile with
`-fsanitize=address,undefined -fno-omit-frame-pointer -g`. The output panel SHALL
display the ASan diagnostic in the compiler/program stderr section.

#### Scenario: null_deref ASan output
- **WHEN** the `null_deref` topic is run
- **THEN** the output panel contains "AddressSanitizer" or "SEGV" in the stderr section

#### Scenario: ASan unavailable graceful degradation
- **WHEN** g++ does not support `-fsanitize=address`
- **THEN** the Run button for gotcha topics is disabled with a tooltip explaining why
