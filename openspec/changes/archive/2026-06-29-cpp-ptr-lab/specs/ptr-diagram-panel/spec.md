## ADDED Requirements

### Requirement: DPG drawlist canvas below hex-bytes panel
Each topic tab SHALL contain a DPG drawlist canvas (Panel B) placed directly below
the hex-bytes panel (Panel A). The canvas SHALL be 500 px wide and 160 px tall. It
SHALL be cleared and fully redrawn after every Run or Compile action completes.

#### Scenario: Canvas present in every tab
- **WHEN** any topic tab is active
- **THEN** a drawlist canvas is visible below the "Memory bytes (hex)" panel

### Requirement: PTRDATA line drives diagram content
C++ templates SHALL emit a `PTRDATA:` line to stdout using `printf`. The compiler
runner SHALL expose `parse_ptrdata(stdout: str) -> dict | None` that finds the first
`PTRDATA:` line and returns a dict of key=value pairs, or `None` if absent.
The `RunResult` dataclass SHALL carry a `ptrdata: dict | None` field populated by
`parse_ptrdata`.

Supported PTRDATA types and required keys:

| type | required keys |
|------|--------------|
| `raw` | `ptr_addr`, `target_addr`, `target_val` |
| `null` | `ptr_addr` |
| `ref` | `ref_addr`, `target_addr`, `target_val` |
| `unique` | `ptr_addr`, `target_addr`, `val`, `is_null` |
| `shared` | `ptr_addr`, `target_addr`, `val`, `use_count` |
| `weak` | `ptr_addr`, `expired`, `use_count` |

#### Scenario: parse_ptrdata extracts key-value pairs
- **WHEN** stdout contains `PTRDATA: type=raw ptr_addr=0x7fff10 target_addr=0x7fff04 target_val=42`
- **THEN** `parse_ptrdata` returns `{"type": "raw", "ptr_addr": "0x7fff10", "target_addr": "0x7fff04", "target_val": "42"}`

#### Scenario: parse_ptrdata returns None when absent
- **WHEN** stdout contains no `PTRDATA:` line
- **THEN** `parse_ptrdata` returns `None` and the canvas shows an empty state

### Requirement: Diagram renders labelled boxes and arrows per type
For type `raw` and `ref`: draw two rectangles connected by a right-pointing arrow.
Left box labelled with variable name and address; right box labelled with value and
address. For type `null`: left box with address, right box labelled "NULL" in gray,
arrow in gray. For type `unique` with `is_null=1`: left box, right "NULL" box.
For type `shared`: two left boxes (sp1 addr, sp2 addr if present) both connected to
one right box; annotate with `use_count=N`. For type `weak`: single box showing
`expired=0/1` and `use_count`.

#### Scenario: raw pointer diagram
- **WHEN** `basic_ptr` is run with value 42
- **THEN** canvas shows two labelled boxes connected by an arrow; right box contains "42"

#### Scenario: shared_ptr two-source diagram
- **WHEN** `shared_copy` is run
- **THEN** canvas shows two left boxes both pointing to one right box with `use_count=2`

### Requirement: Canvas border reflects result state
The outermost rectangle of the drawlist canvas SHALL be drawn with a color that
reflects the last action result:

- Compile error (`status == "compile-failed"`): red border `(220, 50, 50, 255)`
- Compiler warnings (non-empty `compiler_stderr` AND status is not `"compile-failed"`):
  orange border `(220, 150, 50, 255)`
- Success or no result yet: neutral border `(80, 80, 80, 255)`

#### Scenario: Red border on compile failure
- **WHEN** a topic fails to compile
- **THEN** the diagram canvas border is red; diagram content area is empty

#### Scenario: Orange border on warning
- **WHEN** compilation succeeds but `compiler_stderr` is non-empty
- **THEN** the diagram canvas border is orange; arrow diagram is drawn normally

#### Scenario: Neutral border on success
- **WHEN** compilation and execution succeed with no warnings
- **THEN** the diagram canvas border is the neutral gray color
