## ADDED Requirements

### Requirement: Generated element ids are CSS-identifier-safe

Every `id` the renderer emits that is referenced from an unescaped CSS `#id` selector (variant radios, panels, svg ids) SHALL contain only characters valid in a CSS identifier (`[A-Za-z0-9_-]`). Variant labels that contain `(`, `)`, `,`, or other punctuation MUST be sanitised when forming ids, because an unescaped `(` is a CSS parse error and an unescaped `,` splits the selector, which would silently drop the `:checked ~` rule and leave the panel empty.

#### Scenario: punctuated variant labels still produce switchable panels

- **WHEN** `render_fragment` runs for a topic whose variant labels contain parentheses and commas
- **THEN** every emitted `id` matches `[A-Za-z0-9_-]+`, so the corresponding `#id:checked ~ .panels #…` rule is valid CSS
