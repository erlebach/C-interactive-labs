## ADDED Requirements

### Requirement: Absent memory diagram leaves the column empty

When a rendered case has no pointer data, the renderer SHALL leave the diagram column empty rather than drawing a placeholder diagram. "No pointer data" means the case's `ptrdata` is present but empty, which covers compile-failed cases and topics declared with `has_ptrdata=False`. For such cases the "Memory diagram" heading, the `<figure>`, the caption, and any `_svg_unknown` placeholder MUST be omitted; cases that do carry pointer data render their diagram unchanged.

#### Scenario: no-data case renders an empty diagram column

- **WHEN** a fragment is rendered for two variants where one carries `ptrdata` and the other has `ptrdata` empty (e.g. a compile failure)
- **THEN** the output contains exactly one `<svg>` and one "Memory diagram" heading, no "no diagram" placeholder text, and the empty case's diagram column is present but contains no figure
