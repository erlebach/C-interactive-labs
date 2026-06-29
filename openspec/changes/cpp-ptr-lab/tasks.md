## 1. Package Scaffold

- [x] 1.1 Create `cpp_ptr_lab/` directory with `__init__.py`
- [x] 1.2 Create `cpp_ptr_lab/pointers_refs/__init__.py` and `cpp_ptr_lab/smart_ptrs/__init__.py`
- [x] 1.3 Create `cpp_ptr_lab/tests/__init__.py`
- [x] 1.4 Add `pyyaml` to `requirements.txt`
- [x] 1.5 Copy `_smoke_test.py` from `cpp_initializer_lab/` verbatim

## 2. code_generator.py — RED

- [x] 2.1 Write `tests/test_code_generator.py`: test `TopicTemplate` accepts `sanitize` and `has_ptrdata` fields with correct defaults
- [x] 2.2 Write test: `generate_source` substitutes all `<<placeholder>>` markers and injects `<<HARNESS>>`
- [x] 2.3 Confirm tests fail (`pytest tests/test_code_generator.py` → RED)

## 3. code_generator.py — GREEN

- [x] 3.1 Copy `ControlDef`, `generate_source`, `_HARNESS_TEMPLATE`, `_build_harness` verbatim from `cpp_initializer_lab/code_generator.py`
- [x] 3.2 Copy `TopicTemplate` and add `sanitize: bool = False` and `has_ptrdata: bool = True` fields
- [x] 3.3 Run `pytest tests/test_code_generator.py` → GREEN

## 4. compiler_runner.py — RED

- [x] 4.1 Write `tests/test_compiler_runner.py`: test `parse_ptrdata` returns correct dict for all 6 PTRDATA types (`raw`, `null`, `ref`, `unique`, `shared`, `weak`)
- [x] 4.2 Write test: `parse_ptrdata` returns `None` when no `PTRDATA:` line present
- [x] 4.3 Write test: `RunResult` has `ptrdata` field defaulting to `None`
- [x] 4.4 Write test: `build_compile_command` includes `extra_flags` when provided
- [x] 4.5 Confirm tests fail → RED

## 5. compiler_runner.py — GREEN

- [x] 5.1 Copy all of `cpp_initializer_lab/compiler_runner.py` verbatim as starting point
- [x] 5.2 Add `ptrdata: dict | None = None` field to `RunResult`
- [x] 5.3 Implement `parse_ptrdata(stdout: str) -> dict | None`
- [x] 5.4 Add `extra_flags: list[str] = []` to `_compile()` and thread through to g++ command list
- [x] 5.5 Add `extra_flags` parameter to `compile_only()`, `compile_and_run()`, `build_compile_command()`
- [x] 5.6 Call `parse_ptrdata()` inside `compile_and_run()` and store in `RunResult.ptrdata`
- [x] 5.7 Add ASan availability probe to `probe_gpp()` — compile trivial snippet with `-fsanitize=address`; store boolean in `GppStatus`
- [x] 5.8 Run `pytest tests/test_compiler_runner.py` → GREEN

## 6. yaml_config.py — RED

- [x] 6.1 Write `tests/test_yaml_config.py`: test topic disabled in YAML is excluded from returned list
- [x] 6.2 Write test: topic absent from YAML defaults to enabled
- [x] 6.3 Write test: `enabled: false` at lab level returns empty list
- [x] 6.4 Write test: missing YAML file returns all topics (no exception raised)
- [x] 6.5 Write test: malformed YAML returns all topics (no exception raised)
- [x] 6.6 Confirm tests fail → RED

## 7. yaml_config.py — GREEN

- [x] 7.1 Implement `load_enabled_topics(yaml_path, lab_key, all_topics) -> list[TopicTemplate]`
- [x] 7.2 Handle missing file: print warning to stderr, return all topics
- [x] 7.3 Handle malformed YAML: print parse error to stderr, return all topics
- [x] 7.4 Run `pytest tests/test_yaml_config.py` → GREEN

## 8. app_base.py

- [x] 8.1 Copy `TopicState`, `_initial_state`, tag helpers, status banner, and all callbacks from `cpp_initializer_lab/app.py`; rename class to `PtrLabApp(topics, lab_title)`
- [x] 8.2 Add diagram canvas widget in `_build_topic_tab()` below the hex-bytes panel (500×160 px DPG drawlist)
- [x] 8.3 Implement `_has_warnings(compiler_stderr, status) -> bool`
- [x] 8.4 Implement `_render_diagram(topic_id, ptrdata, status, has_warnings)` — clears canvas, draws border, dispatches by type
- [x] 8.5 Implement `_draw_raw_ptr`, `_draw_null_ptr`, `_draw_ref` (two-box + arrow diagrams)
- [x] 8.6 Implement `_draw_unique`, `_draw_shared` (ownership diagrams with use_count annotation)
- [x] 8.7 Implement `_draw_weak` (single box with expired + use_count)
- [x] 8.8 Extend `_display_result()` to call `_render_diagram()` with result data
- [x] 8.9 Extend `_start_action()` to pass ASan `extra_flags` when `topic.sanitize` is True
- [x] 8.10 Disable Run/Compile for `sanitize=True` topics when ASan is unavailable; show tooltip
- [x] 8.11 Run `python -m cpp_ptr_lab._smoke_test` → OK

## 9. Lab 1 Topics — RED

- [x] 9.1 Write `tests/test_integration.py`: for each of the 8 Lab 1 topic templates, write a test that calls `compile_and_run(generate_source(topic, defaults))` and asserts expected stdout substring (e.g., `"PTRDATA:"`, `"MEMBYTES:"`, or `"&r == &a"`)
- [x] 9.2 Write test: `const_taxonomy` with mutation on `const int*` → `compile_and_run` returns `status == "compile-failed"`
- [x] 9.3 Write test: `ref_rebind_illusion` stdout contains `&r == &a: true`
- [x] 9.4 Confirm Lab 1 integration tests fail (topics don't exist yet) → RED

## 10. Lab 1 Topics — GREEN

- [x] 10.1 Write `pointers_refs/topics.py`: `basic_ptr` topic (dropdown for type, text for value; PTRDATA type=raw)
- [x] 10.2 Write `const_taxonomy` topic (4-variant dropdown × mutation checkbox; all variants fully spelled out with mutability parenthetical)
- [x] 10.3 Write `ref_must_bind` topic (shows `int& r;` compile error; explanation uses "Contrary to pointers")
- [x] 10.4 Write `ref_no_null` topic (dropdown: show null ptr / attempt null ref; `sanitize=True` for null-ref variant; PTRDATA type=null or ref)
- [x] 10.5 Write `ref_rebind_illusion` topic (fixed template; prints `&r == &a: true`; PTRDATA type=ref)
- [x] 10.6 Write `ref_const` topic (dropdown `int&` / `const int&` × modification checkbox; T defined inline; PTRDATA type=ref)
- [x] 10.7 Write `null_deref` gotcha topic (`sanitize=True`; PTRDATA type=null)
- [x] 10.8 Write `dangling_ptr` gotcha topic (`sanitize=True`; helper fn returns pointer to local)
- [x] 10.9 Run `pytest tests/test_integration.py -k lab1` → GREEN

## 11. Lab 2 Topics — RED

- [x] 11.1 Write integration tests for each of the 7 Lab 2 topic templates: expected stdout substrings, `unique_copy_err` → `compile-failed`, `shared_copy` stdout contains `use_count after copy: 2`, `weak_expired` stdout contains `expired: true`
- [x] 11.2 Confirm Lab 2 integration tests fail → RED

## 12. Lab 2 Topics — GREEN

- [x] 12.1 Write `smart_ptrs/topics.py`: `unique_basics` topic (text for value; PTRDATA type=unique)
- [x] 12.2 Write `unique_move` topic (fixed template; prints `p is null after move: true`; PTRDATA type=unique)
- [x] 12.3 Write `unique_copy_err` topic (`auto q = p;` compile error; `has_ptrdata=False`)
- [x] 12.4 Write `shared_basics` topic (text for value; PTRDATA type=shared use_count=1)
- [x] 12.5 Write `shared_copy` topic (fixed template; two shared_ptrs; PTRDATA type=shared use_count=2)
- [x] 12.6 Write `weak_basics` topic (text for value; PTRDATA type=weak; prints use_count=1 unchanged)
- [x] 12.7 Write `weak_expired` topic (fixed template; sp dies in inner scope; PTRDATA type=weak expired=1)
- [x] 12.8 Run `pytest tests/test_integration.py -k lab2` → GREEN

## 13. Launchers and Config

- [x] 13.1 Write `lab_config.yaml` with all 15 topics set to `true`
- [x] 13.2 Write `run_ptrs.py` (`__main__` loads YAML, filters topics, instantiates `PtrLabApp`, calls `.run()`)
- [x] 13.3 Write `run_smart.py` (same for smart-ptrs lab)

## 14. Full Test Suite and Manual Verification

- [x] 14.1 Run `pytest cpp_ptr_lab/tests/ -v` → all tests GREEN
- [ ] 14.2 `python -m cpp_ptr_lab.run_ptrs` — 8 tabs; run `basic_ptr` value=99 → diagram arrow and hex bytes appear
- [ ] 14.3 Run `const_taxonomy` with `const int*` + mutation checked → red border; uncheck → neutral
- [ ] 14.4 Run `ref_rebind_illusion` → diagram arrow still points to `a` box after `r = b`
- [ ] 14.5 Run `null_deref` → ASan output visible in stderr panel
- [ ] 14.6 `python -m cpp_ptr_lab.run_smart` — 7 tabs; run `shared_copy` → `use_count=2` in diagram
- [ ] 14.7 Run `unique_copy_err` → red border on canvas
- [ ] 14.8 Set `basic_ptr: false` in `lab_config.yaml`, relaunch → tab absent
