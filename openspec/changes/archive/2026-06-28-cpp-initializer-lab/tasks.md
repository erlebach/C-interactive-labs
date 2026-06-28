## 1. Project Setup

- [x] 1.1 Create Python package directory `cpp_initializer_lab/` with `__init__.py`
- [x] 1.2 Add `requirements.txt` with `dearpygui` dependency
- [x] 1.3 Add `README.md` with install/run instructions for students (pip install, g++ requirement)
- [x] 1.4 Verify `dearpygui` installs and a minimal "hello window" launches

## 2. Compiler Runner Module (`compiler_runner.py`)

- [x] 2.1 Implement `probe_gpp()` — returns status (available/missing/too-old) and version string
- [x] 2.2 Implement `compile_and_run(source: str, timeout: float = 5.0)` — writes source to temp dir, invokes `g++ -std=c++20`, runs binary, returns a result dataclass (stdout, stderr, exit_code, memory_bytes, status)
- [x] 2.3 Implement `MEMBYTES:` line parsing from stdout to extract hex bytes
- [x] 2.4 Implement temp directory creation and cleanup (success + failure paths)
- [x] 2.5 Handle compile failure (return stderr, no run, memory = "n/a")
- [x] 2.6 Handle execution timeout (kill process, return timeout status)
- [x] 2.7 Write unit tests for compile success, compile failure, timeout, and memory parsing

## 3. Code Generation Module (`code_generator.py`)

- [x] 3.1 Define a `TopicTemplate` dataclass: name, template string, control-to-placeholder mapping, explanatory text
- [x] 3.2 Implement `generate_source(topic: TopicTemplate, control_state: dict) -> str` — substitutes placeholders into the template
- [x] 3.3 Implement the memory-dump harness injection — wraps the student-visible init line with instrumentation that prints `MEMBYTES:` and is delimited by `// --- instrumentation ---` comments
- [x] 3.4 Write unit tests verifying generated source for at least 3 topics (value init, copy init with explicit, list init with narrowing)

## 4. Topic Content Module (`topics.py`)

- [x] 4.1 Define the 6 core topic definitions (default, value, direct, copy, list/brace, aggregate) with their templates, controls, and explanatory text
- [x] 4.2 Define the 3 gotcha topic definitions (most vexing parse, explicit-vs-implicit, initializer_list hijacking)
- [x] 4.3 For each topic, verify the template + control mapping produces the expected C++ per the spec scenarios
- [x] 4.4 Verify explanatory text is 2-4 sentences per topic and displayed in the UI

## 5. UI Module (`app.py`)

- [x] 5.1 Create the main Dear PyGui window with a tab bar
- [x] 5.2 Add 9 tabs grouped under "Core" and "Gotchas" headers
- [x] 5.3 Implement the per-topic control panel — render controls from the topic definition, wire changes to regenerate source and update the code panel
- [x] 5.4 Implement the read-only code display panel (updates on control change and tab switch)
- [x] 5.5 Implement the output panel (stdout, stderr, exit code)
- [x] 5.6 Implement the memory panel (hex bytes display, "n/a" on compile failure)
- [x] 5.7 Implement the Run button — calls `compile_and_run`, populates output and memory panels, handles async so UI doesn't freeze
- [x] 5.8 Implement g++ availability check on startup — disable Run button with message if g++ missing/too-old
- [x] 5.9 Implement per-topic state retention (switching tabs preserves last-run results)

## 6. Integration & Polish

- [x] 6.1 Wire all modules together in `app.py` entry point (`__main__`)
- [x] 6.2 End-to-end manual test: visit each of the 9 tabs, toggle controls, run, verify output matches expectations
- [x] 6.3 Verify the narrowing-rejection scenario (list init with `3.14` into `int`) shows a compile error
- [x] 6.4 Verify the explicit-ctor copy-init failure scenario shows a compile error
- [x] 6.5 Verify the most-vexing-parse tab shows the function-declaration vs object distinction
- [x] 6.6 Test on a clean environment (fresh venv, g++ present) following the README instructions
- [x] 6.7 Final review of explanatory text for clarity and correctness
