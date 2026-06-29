## Context

`cpp_initializer_lab/` is the reference implementation: Dear PyGui tabbed app, each
tab driven by a `TopicTemplate` dataclass, C++ templates with `<<placeholder>>`
markers, `compile_and_run()` in a background thread, result polled via DPG frame
callbacks. The new `cpp_ptr_lab/` follows the same architecture with three targeted
extensions: ASan compile flags, PTRDATA diagram parsing, and a DPG drawlist canvas.

## Goals / Non-Goals

**Goals:**
- Reuse initializer-lab infrastructure verbatim wherever possible
- Add ASan support and PTRDATA diagram without changing the existing module interfaces
- Keep each lab's topic list in a single, easy-to-edit Python file
- YAML config is the only file instructors need to touch

**Non-Goals:**
- Modifying `cpp_initializer_lab/` in any way
- Supporting compilers other than g++
- Animating the diagram (static redraw per Run only)
- Persisting lab results across sessions

## Decisions

### D1: Single package with shared infrastructure, two topic sub-packages
`cpp_ptr_lab/` contains shared modules at its root (`code_generator.py`,
`compiler_runner.py`, `app_base.py`, `yaml_config.py`) and two sub-packages
(`pointers_refs/`, `smart_ptrs/`) each containing only `topics.py`.
**Alternative considered**: two fully separate packages. Rejected because it would
duplicate ~500 lines of infrastructure with no user-visible benefit.

### D2: PTRDATA emitted inline in C++ templates, not auto-generated
Each topic template contains its own `printf("PTRDATA: ...")` line rather than a
generic harness. This keeps `code_generator.py` unchanged from the initializer lab
and avoids the complexity of per-topic harness dispatch.
**Alternative considered**: a `<<PTR_HARNESS>>` marker auto-expanded by the generator.
Rejected because pointer types differ too much (raw vs ref vs shared_ptr) to unify
cleanly.

### D3: `TopicTemplate` extended with two optional fields
```python
sanitize: bool = False      # add ASan flags to compile command
has_ptrdata: bool = True    # whether diagram canvas is shown for this topic
```
`_compile()` gains `extra_flags: list[str] = []`. When `sanitize=True` the caller
passes `["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]`.
**Alternative considered**: per-topic compile override lambda. Rejected as over-engineering.

### D4: `PtrLabApp` is a single parametric class, not a subclass
`app_base.py` defines `PtrLabApp(topics: list[TopicTemplate], lab_title: str)`.
Both launchers instantiate it directly with their topic list.
**Alternative considered**: base class with subclass per lab. Rejected — no
per-lab override behaviour exists; a constructor parameter is sufficient.

### D5: Diagram drawn entirely in DPG drawlist, no third-party graph library
DPG's `draw_rectangle`, `draw_arrow`, and `draw_text` cover all needed shapes.
A 500×160 px canvas fits the two-box pointer diagram and the two-source shared_ptr
diagram without scrolling.
**Alternative considered**: matplotlib embedded in DPG. Rejected — heavyweight dep,
no benefit over native DPG drawing for simple box+arrow diagrams.

### D6: `RunResult` carries `ptrdata: dict | None`
`parse_ptrdata(stdout)` is called inside `compile_and_run()` alongside the existing
`parse_membytes()`. The result is stored in `RunResult.ptrdata`. The app reads it in
`_display_result()` and passes it to `_render_diagram()`.

### D7: Warning detection is simple: non-empty compiler_stderr AND status != "compile-failed"
No regex parsing of warning lines. If g++ emits anything to stderr and compilation
succeeded, it is treated as a warning and the orange border is shown. This is
conservative (some g++ informational messages aren't warnings) but sufficient for
the pedagogical goal and avoids fragile regex maintenance.

## Package Layout

```
cpp_ptr_lab/
├── __init__.py
├── code_generator.py      # TopicTemplate (+ sanitize, has_ptrdata), ControlDef, generate_source
├── compiler_runner.py     # RunResult (+ ptrdata), compile/run (+ extra_flags), parse_ptrdata
├── app_base.py            # PtrLabApp class with diagram panel
├── yaml_config.py         # load_enabled_topics(yaml_path, lab_key, all_topics)
├── pointers_refs/
│   ├── __init__.py
│   └── topics.py          # 8 TopicTemplate instances
├── smart_ptrs/
│   ├── __init__.py
│   └── topics.py          # 7 TopicTemplate instances
├── run_ptrs.py            # __main__ for Lab 1
├── run_smart.py           # __main__ for Lab 2
├── _smoke_test.py
├── lab_config.yaml
└── tests/
    ├── test_code_generator.py
    ├── test_compiler_runner.py
    ├── test_yaml_config.py
    └── test_integration.py
```

## PTRDATA Wire Format

Emitted by C++ templates via `printf`; parsed by `parse_ptrdata(stdout)`:

```
PTRDATA: type=raw  ptr_addr=0x7fff10 target_addr=0x7fff04 target_val=42
PTRDATA: type=null ptr_addr=0x0
PTRDATA: type=ref  ref_addr=0x7fff10 target_addr=0x7fff04 target_val=42
PTRDATA: type=unique ptr_addr=0x7fff10 target_addr=0x12340 val=42 is_null=0
PTRDATA: type=shared ptr_addr=0x7fff10 target_addr=0x12340 val=99 use_count=2
PTRDATA: type=weak  ptr_addr=0x7fff10 expired=0 use_count=1
```

## Risks / Trade-offs

- **ASan unavailable on some macOS setups** → probe ASan support in `probe_gpp()`
  and disable gotcha Run buttons with tooltip if absent
- **Addresses differ every run** → diagram shows real addresses from each run;
  students should be told in the explanation that addresses are non-deterministic
- **DPG drawlist tag collision** → use the same `_tag(topic_id, suffix)` scheme as
  the initializer lab; diagram canvas tag is `cpl_{topic_id}_diagram`
- **pyyaml not installed** → caught at import time in `yaml_config.py` with a clear
  message directing to `pip install pyyaml`

## Open Questions

- None — all decisions resolved during the explore/design session.
