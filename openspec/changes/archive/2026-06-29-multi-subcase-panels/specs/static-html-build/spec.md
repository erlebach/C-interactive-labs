## ADDED Requirements

### Requirement: Boolean control defaults resolve through value_map

When `expand_variants` seeds a non-dropdown control's default into the variant control-state, it SHALL preserve the default's type rather than stringifying it. A checkbox default of `False` MUST reach `generate_source` as a boolean so `_resolve_control_value` keys the control's `value_map` on `"false"`/`"true"`, instead of emitting the stringified `"False"` (an undeclared identifier) into the generated C++.

#### Scenario: checkbox default maps to its value_map entry

- **WHEN** a topic has a checkbox control with `default=False` and a `value_map` keyed by `"false"`/`"true"`, and its variants are expanded and their source generated
- **THEN** the generated source contains the `value_map["false"]` text and does not contain a bare `False`
