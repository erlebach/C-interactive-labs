## ADDED Requirements

### Requirement: Semantic per-role color tokens shared by chrome and SVG

The renderer's theme SHALL define semantic per-role color tokens in `:root` —
address, value, type, const/immutable, and error — each meeting WCAG AA contrast
(≥4.5:1 against the page background). The **same** token values SHALL be used in the
inline SVG diagram palette, so prose, code, and diagrams share one contrast-vetted color
language. Every use of a token to convey meaning MUST be redundant with text and/or a
non-color cue (WCAG 1.4.1).

#### Scenario: Tokens are defined once and reused in SVG
- **WHEN** the renderer emits the page theme and an SVG diagram
- **THEN** the address/value/type/const/error roles resolve to the same token values in the CSS `:root` and in the SVG palette

#### Scenario: Semantic colors meet AA contrast
- **WHEN** any semantic color token is used as a foreground against the page background
- **THEN** the contrast ratio is at least 4.5:1

#### Scenario: Color is paired with a non-color cue
- **WHEN** a semantic token colors a meaningful element (e.g. an address or an error)
- **THEN** the element's meaning is also conveyed by text and/or a border/icon, not by color alone
