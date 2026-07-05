# C++ Standard Variant Axis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a topic compile the *same* C++ source under several language standards (C++11/17/20) and present them as zero-JS, CSS-radio selectable tabs.

**Architecture:** The hardcoded `-std=c++20` in `compiler_runner.py` becomes a `std` parameter (default `"c++20"`, so existing callers are unchanged). A topic opts in with a `standards:` list; `expand_variants` turns each standard into a variant carrying a synthetic `__std__` key, which `_compile_one` reads to pick the compile flag and `capture_variant` turns into a `C++NN` tab label. The existing `variant_tabs` component renders the tabs with no rendering-code change. A load-time rule forbids combining `standards:` with dropdown controls (one tab row only).

**Tech Stack:** Python 3, pytest, `g++` at build time, PyYAML, the `cpp_labs` static-site engine.

**Spec:** `docs/superpowers/specs/2026-07-05-std-variant-axis-design.md`

---

## Preliminary: feature branch

- [ ] **Create the feature branch**

```bash
git switch -c feat/std-variant-axis
```

---

## File Structure

- **Modify** `cpp_labs/compiler_runner.py` — add `std` param to `_compile`, `compile_only`, `compile_and_run`, `build_compile_command`.
- **Modify** `cpp_labs/code_generator.py` — add `TopicTemplate.standards` field.
- **Modify** `cpp_labs/topic_yaml.py` — read `standards`; validate standards-only rule.
- **Modify** `cpp_labs/build_html.py` — `expand_variants` `__std__` states; `capture_variant` label; `_compile_one` std flag.
- **Create** `cpp_labs/std_variants/topics/structured_bindings.topic.yaml`, `.../demos/structured_bindings.demo.yaml`, `.../layouts/std_variants.rail.yaml`, `.../tests/__init__.py`, `.../tests/test_std_variants.py`.
- **Tests:** `cpp_labs/tests/test_compiler_runner.py`, new `cpp_labs/tests/test_topic_yaml.py`, `cpp_labs/tests/test_build_html.py`.

---

## Task 1: `std` parameter in the compiler runner

**Files:**
- Modify: `cpp_labs/compiler_runner.py` (`_compile`, `compile_only`, `compile_and_run`, `build_compile_command`)
- Test: `cpp_labs/tests/test_compiler_runner.py`

- [ ] **Step 1: Write the failing tests**

Append to `cpp_labs/tests/test_compiler_runner.py`:

```python
class TestStdParam:
    def test_default_std_is_cpp20(self):
        # build_compile_command bakes the command string without running g++.
        cmd = build_compile_command("int main(){}")
        assert "-std=c++20" in cmd

    def test_explicit_std_flag_in_command(self):
        cmd = build_compile_command("int main(){}", std="c++11")
        assert "-std=c++11" in cmd
        assert "-std=c++20" not in cmd

    @pytest.mark.skipif(shutil.which("g++") is None, reason="needs g++")
    def test_structured_bindings_fail_under_cpp11(self):
        src = (
            "#include <utility>\n"
            "int main(){ auto [a, b] = std::make_pair(1, 2); (void)a; (void)b; }\n"
        )
        assert compile_only(src, std="c++11").status == "compile-failed"

    @pytest.mark.skipif(shutil.which("g++") is None, reason="needs g++")
    def test_structured_bindings_ok_under_cpp17(self):
        src = (
            "#include <utility>\n"
            "int main(){ auto [a, b] = std::make_pair(1, 2); (void)a; (void)b; }\n"
        )
        assert compile_only(src, std="c++17").status == "compile-ok"
```

Ensure the test module imports `shutil`, `pytest`, and `build_compile_command`, `compile_only` from `cpp_labs.compiler_runner` (add any missing imports at the top of the file).

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_labs/tests/test_compiler_runner.py::TestStdParam -v`
Expected: FAIL — `compile_only()`/`build_compile_command()` got an unexpected keyword argument `std`.

- [ ] **Step 3: Thread `std` through the four functions**

In `cpp_labs/compiler_runner.py`:

`_compile` — add the parameter and use it:

```python
def _compile(
    src_path: str,
    exe_path: str,
    timeout: float,
    cancel_event: threading.Event | None,
    extra_flags: list[str] | None = None,
    std: str = "c++20",
) -> tuple[str, subprocess.CompletedProcess[str] | None, str, str]:
    """Shared compile step used by :func:`compile_only` and :func:`compile_and_run`."""
    flags = extra_flags or []
    compile_cmd = ["g++", f"-std={std}"] + flags + [src_path, "-o", exe_path]
```

`compile_only` — add `std` and forward it:

```python
def compile_only(
    source: str,
    timeout: float = 5.0,
    cancel_event: threading.Event | None = None,
    extra_flags: list[str] | None = None,
    std: str = "c++20",
) -> RunResult:
    ...
        cmd_str, compile_proc, status, compiler_stderr = _compile(
            src_path, exe_path, timeout, cancel_event, extra_flags, std=std
        )
```

`build_compile_command` — add `std` and use it:

```python
def build_compile_command(
    source: str,
    extra_flags: list[str] | None = None,
    std: str = "c++20",
) -> str:
    """Return the g++ command string that would compile ``source``."""
    flags = extra_flags or []
    ...
        compile_cmd = ["g++", f"-std={std}"] + flags + [src_path, "-o", exe_path]
        return " ".join(compile_cmd)
```

`compile_and_run` — add `std` and forward it to `_compile`:

```python
def compile_and_run(
    source: str,
    timeout: float = 5.0,
    cancel_event: threading.Event | None = None,
    extra_flags: list[str] | None = None,
    std: str = "c++20",
) -> RunResult:
    """Compile ``source`` with ``g++ -std=<std>`` and run the resulting binary."""
    ...
        compile_cmd_str, compile_proc, compile_status, compiler_stderr = _compile(
            src_path, exe_path, timeout, cancel_event, extra_flags, std=std
        )
```

(There are two `_compile(...)` call sites inside `compile_and_run`'s body if the sanitizer path differs — search for every `_compile(` call in that function and add `std=std` to each.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest cpp_labs/tests/test_compiler_runner.py -v`
Expected: PASS (all, including the pre-existing tests — default stays `c++20`).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/compiler_runner.py cpp_labs/tests/test_compiler_runner.py
git commit -m "feat(compiler): parameterize the C++ standard (-std), default c++20

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `TopicTemplate.standards` field + load + validation

**Files:**
- Modify: `cpp_labs/code_generator.py` (`TopicTemplate`)
- Modify: `cpp_labs/topic_yaml.py` (`_topic`)
- Test: `cpp_labs/tests/test_topic_yaml.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `cpp_labs/tests/test_topic_yaml.py`:

```python
import pytest

from cpp_labs.topic_yaml import _topic


def _base(**over):
    d = {
        "id": "t",
        "name": "T",
        "template": "int main(){}",
        "explanation": "e",
        "group": "g",
    }
    d.update(over)
    return d


def test_standards_defaults_empty():
    assert _topic(_base()).standards == []


def test_standards_parsed():
    t = _topic(_base(standards=[11, 17, 20]))
    assert t.standards == [11, 17, 20]


def test_standards_with_dropdown_control_is_rejected():
    d = _base(
        standards=[11, 17],
        controls=[{"id": "ty", "label": "Type", "kind": "dropdown",
                   "options": ["int", "double"]}],
    )
    with pytest.raises(ValueError, match="standards"):
        _topic(d)


def test_standards_with_freetext_control_is_allowed():
    d = _base(
        standards=[11, 17],
        controls=[{"id": "v", "label": "Value", "kind": "text", "default": "0"}],
    )
    assert _topic(d).standards == [11, 17]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_labs/tests/test_topic_yaml.py -v`
Expected: FAIL — `TopicTemplate` has no `standards` attribute / no validation raised.

- [ ] **Step 3: Add the field and the load + validation**

In `cpp_labs/code_generator.py`, add to `TopicTemplate` (after `extra_compile_flags`):

```python
    standards: list[int] = field(default_factory=list)
```

In `cpp_labs/topic_yaml.py`, inside `_topic`, after the `_REQUIRED` loop and before building the `TopicTemplate`, add the validation, then pass the field:

```python
    controls = [_control(c) for c in d.get("controls", [])]
    standards = list(d.get("standards", []))
    if standards:
        dropdowns = [c.id for c in controls if c.kind == "dropdown"]
        if dropdowns:
            raise ValueError(
                f"topic {d.get('id', '?')!r} uses standards:{standards} but also "
                f"has dropdown control(s) {dropdowns}; a standards topic may not "
                f"have a competing tab row (see std-variant-axis spec)"
            )
    return TopicTemplate(
        id=d["id"],
        name=d["name"],
        template=d["template"],
        controls=controls,
        explanation=d["explanation"],
        group=d["group"],
        target_var=d.get("target_var", "x"),
        sanitize=d.get("sanitize", False),
        has_ptrdata=d.get("has_ptrdata", True),
        doc_url=d.get("doc_url", ""),
        cases=[_case(c) for c in cases] if cases else None,
        extra_compile_flags=list(d.get("extra_compile_flags", [])),
        standards=standards,
    )
```

(Replace the existing `controls=[_control(c) for c in d.get("controls", [])]` inline arg with the `controls` local defined above, so it is computed once.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest cpp_labs/tests/test_topic_yaml.py cpp_labs/tests/test_code_generator.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/code_generator.py cpp_labs/topic_yaml.py cpp_labs/tests/test_topic_yaml.py
git commit -m "feat(topic): add standards field with standards-only validation

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: `expand_variants` emits one `__std__` state per standard

**Files:**
- Modify: `cpp_labs/build_html.py` (`expand_variants`)
- Test: `cpp_labs/tests/test_build_html.py`

- [ ] **Step 1: Write the failing test**

Append to `cpp_labs/tests/test_build_html.py` (import `TopicTemplate` from `cpp_labs.code_generator` and `expand_variants` from `cpp_labs.build_html` if not already imported):

```python
class TestStandardsExpansion:
    def _topic(self, **over):
        kw = dict(
            id="t", name="T", template="int main(){}",
            controls=[], explanation="e", group="g",
        )
        kw.update(over)
        return TopicTemplate(**kw)

    def test_no_standards_single_default_variant(self):
        states = expand_variants(self._topic())
        assert states == [{}]

    def test_standards_one_state_each(self):
        states = expand_variants(self._topic(standards=[11, 17, 20]))
        assert states == [{"__std__": "11"}, {"__std__": "17"}, {"__std__": "20"}]

    def test_standards_preserve_freetext_defaults(self):
        from cpp_labs.code_generator import ControlDef
        ctrl = ControlDef(id="v", label="V", kind="text", default="7")
        states = expand_variants(self._topic(standards=[17], controls=[ctrl]))
        assert states == [{"v": "7", "__std__": "17"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_build_html.py::TestStandardsExpansion -v`
Expected: FAIL — standards states not produced (`test_standards_one_state_each` returns `[{}]`).

- [ ] **Step 3: Implement in `expand_variants`**

In `cpp_labs/build_html.py`, `expand_variants`, after the `base`/`dropdowns` seed loop and **before** the `if not dropdowns:` block, insert:

```python
    # A standards topic (validated to have no dropdowns) fans out on the C++
    # standard instead: one variant per standard, carrying a synthetic
    # ``__std__`` key that _compile_one turns into the -std flag and
    # capture_variant turns into the "C++NN" tab label.
    if getattr(topic, "standards", None):
        return [{**base, "__std__": str(n)} for n in topic.standards]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_build_html.py::TestStandardsExpansion -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/build_html.py cpp_labs/tests/test_build_html.py
git commit -m "feat(build): expand a standards topic into one __std__ state per standard

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `capture_variant` label + `_compile_one` std flag

**Files:**
- Modify: `cpp_labs/build_html.py` (`capture_variant`, `_compile_one`)
- Test: `cpp_labs/tests/test_build_html.py`

- [ ] **Step 1: Write the failing tests**

Append to `cpp_labs/tests/test_build_html.py`:

```python
class TestStandardsCapture:
    SB = (
        "#include <utility>\n"
        "int main(){ auto [a, b] = std::make_pair(1, 2); (void)a; (void)b; }\n"
    )

    def _topic(self, template):
        return TopicTemplate(
            id="t", name="T", template=template, controls=[],
            explanation="e", group="g", has_ptrdata=False,
            standards=[11, 17, 20],
        )

    @pytest.mark.skipif(shutil.which("g++") is None, reason="needs g++")
    def test_label_is_cpp_version(self):
        v = capture_variant(self._topic("int main(){}"), {"__std__": "17"})
        assert v["label"] == "C++17"

    @pytest.mark.skipif(shutil.which("g++") is None, reason="needs g++")
    def test_cpp11_fails_cpp17_ok(self):
        topic = self._topic(self.SB)
        v11 = capture_variant(topic, {"__std__": "11"})
        v17 = capture_variant(topic, {"__std__": "17"})
        assert v11["failed"] is True and v11["error_kind"] == "compile"
        assert v17["failed"] is False
```

Ensure `shutil` and `capture_variant` are imported in the test module.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_labs/tests/test_build_html.py::TestStandardsCapture -v`
Expected: FAIL — label is `""` (no dropdowns) and both variants compile the same (std ignored).

- [ ] **Step 3: Implement the label and the compile flag**

In `cpp_labs/build_html.py`, `capture_variant`, replace the label construction so a `__std__` state names the tab. After the existing `label = " / ".join(...)` line, add:

```python
    if "__std__" in control_state:
        label = f"C++{control_state['__std__']}"
```

In `_compile_one`, derive the `std` and pass it to `compile_and_run`. Replace the `result = compile_and_run(...)` line with:

```python
    std = control_state.get("__std__")
    std_kw = {"std": f"c++{std}"} if std else {}
    result = compile_and_run(source, extra_flags=extra_flags or None, **std_kw)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest cpp_labs/tests/test_build_html.py -v`
Expected: PASS (whole module, including pre-existing tests).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/build_html.py cpp_labs/tests/test_build_html.py
git commit -m "feat(build): label __std__ variants C++NN and compile each under its -std

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Demonstration subject (structured bindings) + integration test

**Files:**
- Create: `cpp_labs/std_variants/topics/structured_bindings.topic.yaml`
- Create: `cpp_labs/std_variants/demos/structured_bindings.demo.yaml`
- Create: `cpp_labs/std_variants/layouts/std_variants.rail.yaml`
- Create: `cpp_labs/std_variants/tests/__init__.py`
- Create: `cpp_labs/std_variants/tests/test_std_variants.py`

- [ ] **Step 1: Write the topic, demo, and layout YAML**

`cpp_labs/std_variants/topics/structured_bindings.topic.yaml`:

```yaml
id: structured_bindings
name: "Structured Bindings"
group: "Standards"
has_ptrdata: false
doc_url: https://en.cppreference.com/w/cpp/language/structured_binding
standards: [11, 17, 20]
explanation: >-
  Structured bindings — auto [a, b] = ... — unpack a pair, tuple, or struct into
  named variables. They arrived in C++17, so the SAME source fails to compile
  under -std=c++11 and compiles under -std=c++17 and -std=c++20. Switch the tabs
  to watch the compiler's verdict change with the language standard alone.
template: |
  #include <iostream>
  #include <utility>
  int main() {
      // structured bindings unpack the pair — a C++17 feature.
      // make_pair itself is C++11, so the standard is the only variable here.
      auto [a, b] = std::make_pair(1, 2);
      std::cout << a << " " << b << "\n";
  }
```

`cpp_labs/std_variants/demos/structured_bindings.demo.yaml`:

```yaml
title: "Structured Bindings (C++17)"
language: cpp
bake: { sb: structured_bindings }
blocks:
  - topic: { id: sb, source: sb, diagram: false, concept: "${sb.explanation}" }
```

`cpp_labs/std_variants/layouts/std_variants.rail.yaml`:

```yaml
title: "C++ Standards — Same Code, Different Standard"
style: left_rail
header:
  - heading: { text: "C++ Standard Selector" }
demos:
  - ../demos/structured_bindings.demo.yaml
```

- [ ] **Step 2: Write the integration test (and package init)**

`cpp_labs/std_variants/tests/__init__.py`: empty file.

`cpp_labs/std_variants/tests/test_std_variants.py`:

```python
import shutil
import pytest
from pathlib import Path

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "std_variants.rail.yaml"

pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_three_standard_tabs(html):
    for label in ("C++11", "C++17", "C++20"):
        assert label in html, f"missing standard tab {label!r}"


def test_cpp11_shows_compile_failure(html):
    # The C++11 variant must not compile structured bindings.
    assert "Compile failed" in html


def test_modern_standard_shows_output(html):
    # C++17 / C++20 compile and print "1 2".
    assert "1 2" in html


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ("<script src", "<link", 'href="http'):
        assert bad not in html
```

If `test_cpp11_shows_compile_failure`'s `"Compile failed"` string does not match the baked badge text, open the built page (see Step 4) and assert on the exact compile-error badge string emitted by `compile_status_badge(kind="compile")` in `cpp_labs/components.py`.

- [ ] **Step 3: Run the integration test to verify it fails**

Run: `python -m pytest cpp_labs/std_variants/tests/test_std_variants.py -v`
Expected: FAIL initially only if wiring is wrong; since Tasks 1-4 are done it should PASS. If it fails, debug against the built HTML from Step 4 before changing engine code.

- [ ] **Step 4: Build the page and eyeball it**

Run:
```bash
./build_labs.sh std_variants
python3 -m http.server -d dist_labs 8000
```
Open `http://localhost:8000/std_variants_rail.html`. Confirm: three tabs `C++11 / C++17 / C++20`; the `C++11` tab shows a red compile-error badge; `C++17`/`C++20` show green with output `1 2`.

- [ ] **Step 5: Run the full engine suite (catch drift)**

Run: `python -m pytest cpp_labs -q`
Expected: PASS, 0 failed. In particular `cpp_labs/yaml_engine/test_interface_catalog.py` must stay green (no catalog change was needed; this confirms it).

- [ ] **Step 6: Commit**

```bash
git add cpp_labs/std_variants/
git commit -m "feat(std_variants): structured-bindings demo proving the standard axis

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Final verification

- [ ] **Full suite green**

Run: `python -m pytest cpp_labs -q`
Expected: all pass, 0 failed.

- [ ] **All pages build**

Run: `./build_labs.sh`
Expected: `failed 0` (the new `std_variants` page is auto-discovered and built alongside the rest).

---

## Notes for the implementer

- **Default preserved:** every `-std=` default stays `c++20`, so all pre-existing topics/tests are byte-for-byte unchanged. If any existing test changes output, that is a regression — stop and investigate.
- **`__std__` is reserved:** it is never a real `ControlDef`, so `generate_source` never substitutes it into the template (it only iterates `topic.controls`). No template escaping concerns.
- **No interface-catalog change:** no new block keyword or component signature is introduced; `test_interface_catalog` should not need regeneration.
- **Do NOT commit** repo-root scratch (`session-*.md`, `prototype/`, `a.cpp`, `run.x`, etc.); only the files this plan names.
