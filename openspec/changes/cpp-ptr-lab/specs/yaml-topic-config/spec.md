## ADDED Requirements

### Requirement: YAML file controls topic visibility per lab
The system SHALL read `lab_config.yaml` from the package root at startup. Each lab
section SHALL have an `enabled` boolean and a `topics` map of topic-id to boolean.
A topic absent from the map SHALL default to enabled. A lab with `enabled: false`
SHALL not open a window.

#### Scenario: Topic set to false is hidden
- **WHEN** `lab_config.yaml` contains `basic_ptr: false` under `pointers_refs.topics`
- **THEN** the Pointers & References lab window opens without the Basic Pointer tab

#### Scenario: Topic absent from YAML defaults to enabled
- **WHEN** `lab_config.yaml` does not mention `ref_const`
- **THEN** the ref_const tab appears in the lab window

#### Scenario: Entire lab disabled
- **WHEN** `pointers_refs.enabled: false` in `lab_config.yaml`
- **THEN** `python -m cpp_ptr_lab.run_ptrs` exits immediately without opening a window

### Requirement: YAML parse errors produce a clear message
If `lab_config.yaml` is missing or malformed, the app SHALL print a human-readable
error to stderr and fall back to enabling all topics rather than crashing.

#### Scenario: Missing YAML file
- **WHEN** `lab_config.yaml` does not exist
- **THEN** app prints "lab_config.yaml not found — all topics enabled" to stderr
  and opens with all topics visible

#### Scenario: Malformed YAML
- **WHEN** `lab_config.yaml` contains invalid YAML syntax
- **THEN** app prints a parse error message to stderr and opens with all topics enabled
