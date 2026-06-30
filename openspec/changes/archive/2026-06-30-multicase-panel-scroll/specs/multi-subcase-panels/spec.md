## ADDED Requirements

### Requirement: Stacked sub-cases remain scrollable

When a panel holds more than one sub-case, the panel SHALL be vertically scrollable so every stacked sub-case is reachable rather than clipped by the bordered panel box. Each sub-case SHALL retain a usable diagram height instead of depending on the single-case full-height fill, and single-case panels MUST continue to fit without introducing a redundant scrollbar.

#### Scenario: multi-case panel scrolls

- **WHEN** the assembled page CSS is generated for a topic whose variants carry multiple sub-cases
- **THEN** the `.panel` rule includes `overflow-y: auto`, and each sub-case diagram has a non-zero minimum height
