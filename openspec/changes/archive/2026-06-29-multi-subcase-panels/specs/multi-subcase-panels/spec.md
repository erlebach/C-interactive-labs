## ADDED Requirements

### Requirement: Build-time sub-case model

A `TopicTemplate` SHALL support an optional `cases: list[CaseDef]` field where each `CaseDef` has a `label` and a `subs` mapping of additional template placeholders to values. When `cases` is absent the topic behaves as a single-program topic. `generate_source` SHALL accept an `extra_subs` argument, applied after control resolution, so per-case placeholders such as `<<op>>` are filled.

#### Scenario: extra_subs fills a per-case placeholder

- **WHEN** `generate_source(topic, {}, extra_subs={"<<op>>": "*ptr = 99;"})` is called on a template containing `<<op>>`
- **THEN** the generated source contains `*ptr = 99;` and no longer contains the literal `<<op>>`

#### Scenario: cases defaults to None

- **WHEN** a `TopicTemplate` is constructed without a `cases` argument
- **THEN** its `cases` attribute is `None`

### Requirement: Independent per-case compilation

When `topic.cases` is set, `capture_variant` SHALL compile one program per `CaseDef` and return the variant as a dict carrying a `cases` list, one render-data entry per case, each labelled with its `CaseDef.label` and reflecting that case's own `subs`. When `topic.cases` is absent the returned dict MUST NOT contain a `cases` key and MUST retain the prior single-program shape.

#### Scenario: multi-case variant bundles one result per case

- **WHEN** `capture_variant` runs on a topic with two `CaseDef`s
- **THEN** the returned dict has a `cases` list of length two, each entry has `label`, `source`, `failed`, and `svg`, and each source reflects its own case `subs`

#### Scenario: single-case topic is unchanged

- **WHEN** `capture_variant` runs on a topic whose `cases` is `None`
- **THEN** the returned dict has no `cases` key

### Requirement: Multi-case panel rendering

When a variant carries a `cases` list, `_panel_body` SHALL render one labelled block per sub-case, each with its own code, compile verdict, program output, and memory diagram, using a unique svg-id prefix per case so no two diagrams share an `id`. A variant without `cases` SHALL render identically to the prior single-case layout.

#### Scenario: each sub-case is rendered with its label

- **WHEN** a fragment is rendered for two variants that each carry two cases
- **THEN** each case label appears in the output, there are four code blocks total, and all element ids are unique

#### Scenario: failing and passing sub-cases show their own results

- **WHEN** one sub-case failed to compile and another succeeded
- **THEN** the failing block shows the compile-failure message and its stderr, and the passing block shows its stdout

### Requirement: const taxonomy demonstrates the const truth table

The `const_taxonomy` topic SHALL present four pointer-type tabs, each compiling two sub-cases — a write through the pointer (`*ptr = 99`) and a rebind (`ptr = &other`) — such that the operation forbidden by each type genuinely fails to compile. The allowed cells SHALL compile, run, and show a memory diagram.

#### Scenario: 2x2 truth table holds

- **WHEN** all four `const_taxonomy` type variants are built
- **THEN** `int*` compiles both cases; `const int*` fails the write and compiles the rebind; `int* const` compiles the write and fails the rebind; `const int* const` fails both

### Requirement: Failing sub-case error border

A sub-case (or single-case panel) that fails to compile SHALL render its compiler-output box with a distinct error border, so the failure is visible beyond the red "Compile failed." text. Boxes for successfully compiled cases SHALL retain the neutral border.

#### Scenario: failed compiler-output box gets the error border

- **WHEN** a panel body is rendered for a sub-case whose `failed` is true
- **THEN** that case's compiler-output box carries the error-border marker class, and the inlined CSS gives that class a red border
