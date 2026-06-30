## ADDED Requirements

### Requirement: Per-component standalone demo pages

The gallery build SHALL emit one standalone, self-contained HTML demo page per component
in the library, each demonstrating that component rendered on real pointer content
(including, where relevant, real baked g++ output). Each demo page MUST be a complete WCAG
AA document (skip link, `lang`, landmarks) that references no external or network resource,
so it can be pasted directly into Canvas.

#### Scenario: Each component gets a self-contained demo page
- **WHEN** the gallery build runs
- **THEN** it produces one HTML file per component, each a complete document with inlined CSS and no external/script/network references

#### Scenario: Demo pages show real captured output
- **WHEN** a component that displays program output is demoed
- **THEN** its demo page contains real g++-captured stdout/stderr baked at build time, not placeholder text

### Requirement: Gallery index page

The gallery build SHALL emit an index page linking to every component demo page, naming
each component and summarising what page-element type it provides, so the catalog is
browsable as a component library.

#### Scenario: Index links every component
- **WHEN** the gallery build runs
- **THEN** an index page is produced that links to every generated component demo page by name

### Requirement: Gallery build degrades without a compiler

The gallery build SHALL fail clearly and early if g++ is unavailable at build time, since
output is baked, not computed at view time; component demos that need no compiled output
SHALL still be expressible from pure data.

#### Scenario: Missing compiler reported at build time
- **WHEN** the gallery build runs and g++ is not available
- **THEN** the build reports the missing compiler dependency clearly rather than emitting pages with empty output
