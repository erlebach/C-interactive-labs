# topic-content Specification

## Purpose
TBD - created by archiving change cpp-initializer-lab. Update Purpose after archive.
## Requirements
### Requirement: Topic definitions for 6 core initialization forms
The system SHALL define topic content for the following 6 core forms, each specifying: a display name, the set of UI controls exposed, the C++ template with placeholders, and a short explanatory text shown in the tab.

Topics:
1. **Default initialization** — `int x;` (uninitialized, garbage value)
2. **Value initialization** — `int x{};` (zero-initialized)
3. **Direct initialization** — `int x(5);` (constructor call form)
4. **Copy initialization** — `int x = 5;` (conversion then construct)
5. **List/brace initialization** — `int x{5};` / `std::vector<int> v{1,2,3};` (no narrowing)
6. **Aggregate initialization** — `struct S { int a; int b; }; S s{1, 2};`

#### Scenario: Default init topic exposes type control
- **WHEN** the "Default initialization" tab is active
- **THEN** the control panel shows a type dropdown (int, double, char, etc.) and the generated code contains `<type> x;` with no initializer

#### Scenario: Value init topic exposes type and form controls
- **WHEN** the "Value initialization" tab is active
- **THEN** the control panel shows a type dropdown and the generated code contains `<type> x{};`

#### Scenario: List/brace init topic demonstrates narrowing rejection
- **WHEN** the "List/brace initialization" tab is active and the type is "int" and the value is "3.14"
- **THEN** the generated code contains `int x{3.14};` and running it produces a compile error about narrowing

### Requirement: Topic definitions for 3 gotcha topics
The system SHALL define topic content for the following 3 gotcha topics:

1. **Most vexing parse** — `Widget w();` (declares a function!) vs `Widget w{};` (value-initialized object)
2. **Explicit vs implicit constructor** — toggling `explicit` on a single-argument ctor to show copy-init (`Foo f = 42;`) fails when explicit
3. **initializer_list hijacking** — a class with both `Foo(int)` and `Foo(std::initializer_list<int>)` constructors, showing `Foo f{5};` picks the init_list ctor

#### Scenario: Most vexing parse topic shows function declaration
- **WHEN** the "Most vexing parse" tab is active and the form control is set to parentheses
- **THEN** the generated code contains `Widget w();` and the explanatory text notes this declares a function, not an object

#### Scenario: Explicit ctor topic shows copy-init failure
- **WHEN** the "Explicit vs implicit" tab is active and the "explicit" checkbox is checked and the form is copy-init
- **THEN** the generated code contains an explicit constructor and `Foo f = 42;`, and running it produces a compile error

#### Scenario: initializer_list hijack topic shows ctor selection
- **WHEN** the "initializer_list hijacking" tab is active and the form is brace-init with a single value
- **THEN** the generated code contains `Foo f{5};` and the explanatory text notes this selects the initializer_list constructor, not the int constructor

### Requirement: Explanatory text per topic
Each topic SHALL include a short explanatory text (2-4 sentences) displayed in the tab, describing what the topic demonstrates and what the student should observe when toggling controls.

#### Scenario: Explanatory text visible
- **WHEN** any topic tab is active
- **THEN** a text block displays the topic's explanatory text above or beside the control panel

