# demonstration-builder Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a project-local `demonstration-builder` skill that turns the `cpp_labs` authoring pattern into an interactive workflow, validated by using the pattern to build one real `template_subject` demonstration that builds clean and whose tests pass.

**Architecture:** Build the validating deliverable FIRST (`cpp_labs/template_subject/` — 2 examples + 1 gotcha, all `diagram:false`), TDD-style against exact baked g++ stdout. THEN author the skill files (`.claude/skills/demonstration-builder/`: `SKILL.md` + `reference/` + `templates/`) by distilling the now-working subject, guarded by a lightweight structural test. The skill references the in-repo `cpp_labs/` engine (no engine code change in v1); the case-2 author-image path and the interactive-diagram layer are documented in `reference/DIAGRAMS.md`, not built.

**Tech Stack:** Python 3.12, pytest (compiler-gated on `g++`), PyYAML, the existing `cpp_labs` YAML engine (`cpp_labs.yaml_engine.render_page.build_layout`), Markdown skill files.

---

## File Structure

**Deliverable subject (built first, becomes the copy-me exemplar):**
- `cpp_labs/template_subject/__init__.py` — package marker
- `cpp_labs/template_subject/topics/ts_value.topic.yaml` — Example 1 (dropdown variants)
- `cpp_labs/template_subject/topics/ts_method.topic.yaml` — Example 2 (plain class)
- `cpp_labs/template_subject/topics/ts_gotcha.topic.yaml` — Gotcha (`cases:` compile-error)
- `cpp_labs/template_subject/demos/ts_value.demo.yaml`
- `cpp_labs/template_subject/demos/ts_method.demo.yaml`
- `cpp_labs/template_subject/demos/ts_gotcha.demo.yaml`
- `cpp_labs/template_subject/layouts/template_subject.rail.yaml`
- `cpp_labs/template_subject/tests/__init__.py`
- `cpp_labs/template_subject/tests/test_template_subject.py`

**Skill files (authored second):**
- `.claude/skills/demonstration-builder/SKILL.md`
- `.claude/skills/demonstration-builder/reference/PATTERN.md`
- `.claude/skills/demonstration-builder/reference/DIAGRAMS.md`
- `.claude/skills/demonstration-builder/reference/CHECKLIST.md`
- `.claude/skills/demonstration-builder/templates/topic.topic.yaml`
- `.claude/skills/demonstration-builder/templates/demo.demo.yaml`
- `.claude/skills/demonstration-builder/templates/layout.rail.yaml`
- `.claude/skills/demonstration-builder/templates/test_subject.py`

**Skill guard test:**
- `cpp_labs/tests/test_demonstration_skill.py` — asserts the skill files exist, `SKILL.md` frontmatter is valid, and the YAML skeletons parse with required keys.

---

## Task 1: Scaffold `template_subject` package + RED integration test

**Files:**
- Create: `cpp_labs/template_subject/__init__.py`
- Create: `cpp_labs/template_subject/tests/__init__.py`
- Test: `cpp_labs/template_subject/tests/test_template_subject.py`

- [ ] **Step 1: Create the two empty package markers**

```bash
mkdir -p cpp_labs/template_subject/topics cpp_labs/template_subject/demos \
         cpp_labs/template_subject/layouts cpp_labs/template_subject/tests
: > cpp_labs/template_subject/__init__.py
: > cpp_labs/template_subject/tests/__init__.py
```

- [ ] **Step 2: Write the failing integration test**

Create `cpp_labs/template_subject/tests/test_template_subject.py`:

```python
import re
import shutil

import pytest
from pathlib import Path

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "template_subject.rail.yaml"

pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ("<script src", "<link", 'href="http', 'src="http'):
        assert bad not in html


def test_exact_baked_output(html):
    # Deterministic g++ stdout, byte-for-byte — the primary correctness gate.
    assert "x = 42" in html          # ts_value (both int and double tabs)
    assert "count = 2" in html       # ts_method
    assert "count = 1" in html       # ts_gotcha, Correct case


def test_no_diagram(html):
    # Every topic is diagram:false → no figure at all; WCAG svg/role invariant holds.
    assert 'role="img"' not in html
    assert html.count("<svg") == html.count('role="img"')


def test_gotcha_error_box(html):
    # The Mistake case fails to compile → a real red compiler-error console.
    assert "out--err" in html


def test_correct_mistake_labels(html):
    assert "Correct: provide the accessor" in html
    assert "Mistake: omit the accessor" in html


def test_id_uniqueness(html):
    ids = re.findall(r'id="([^"]+)"', html)
    assert len(ids) == len(set(ids))
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest cpp_labs/template_subject/tests/test_template_subject.py -q`
Expected: FAIL / ERROR — the layout `template_subject.rail.yaml` does not exist yet (FileNotFoundError from `build_layout`).

- [ ] **Step 4: Commit**

```bash
git add cpp_labs/template_subject/__init__.py \
        cpp_labs/template_subject/tests/__init__.py \
        cpp_labs/template_subject/tests/test_template_subject.py
git commit -m "test(template_subject): failing integration test for the exemplar demonstration"
```

---

## Task 2: Author the two examples (`ts_value`, `ts_method`) + demos + layout

**Files:**
- Create: `cpp_labs/template_subject/topics/ts_value.topic.yaml`
- Create: `cpp_labs/template_subject/topics/ts_method.topic.yaml`
- Create: `cpp_labs/template_subject/demos/ts_value.demo.yaml`
- Create: `cpp_labs/template_subject/demos/ts_method.demo.yaml`
- Create: `cpp_labs/template_subject/layouts/template_subject.rail.yaml`

- [ ] **Step 1: Write `ts_value` topic (Example 1 — dropdown variants, diagram:false)**

Create `cpp_labs/template_subject/topics/ts_value.topic.yaml`:

```yaml
id: ts_value
name: "Value types"
group: Examples
doc_url: https://en.cppreference.com/w/cpp/language/types
explanation: >-
  A variable has a type chosen at declaration. Switch the Type tab to compile the
  SAME program as int and as double. This example shows the variant-tabs mechanism:
  one dropdown control produces one tab per option.
template: |
  #include <iostream>
  int main() {
      // a value of the chosen type
      <<type>> x = <<value>>;
      std::cout << "x = " << x << "\n";
  }
controls:
  - id: type
    label: Type
    kind: dropdown
    options: [int, double]
    default: int
    placeholder: <<type>>
  - id: value
    label: Value
    kind: text
    default: "42"
    placeholder: <<value>>
```

- [ ] **Step 2: Write `ts_method` topic (Example 2 — plain class, diagram:false)**

Create `cpp_labs/template_subject/topics/ts_method.topic.yaml`:

```yaml
id: ts_method
name: "A small class"
group: Examples
doc_url: https://en.cppreference.com/w/cpp/language/classes
explanation: >-
  A class bundles data with the functions that act on it. Counter keeps a private
  count and exposes tick() and value(). This example has no controls, so it renders
  as a single variant.
template: |
  #include <iostream>
  // A small class with one accessor.
  class Counter {
      // running count, starts at zero
      int n_ = 0;
  public:
      void tick() { ++n_; }
      int value() const { return n_; }
  };
  int main() {
      Counter c;
      c.tick();
      c.tick();
      std::cout << "count = " << c.value() << "\n";
  }
```

- [ ] **Step 3: Write the two demos (diagram:false + concept in the right column)**

Create `cpp_labs/template_subject/demos/ts_value.demo.yaml`:

```yaml
title: "Value types"
language: cpp
bake: { v: ts_value }
blocks:
  - topic: { id: v, source: v, diagram: false, concept: "${v.explanation}" }
```

Create `cpp_labs/template_subject/demos/ts_method.demo.yaml`:

```yaml
title: "A small class"
language: cpp
bake: { m: ts_method }
blocks:
  - topic: { id: m, source: m, diagram: false, concept: "${m.explanation}" }
```

- [ ] **Step 4: Write the layout (2 examples only, for now)**

Create `cpp_labs/template_subject/layouts/template_subject.rail.yaml`:

```yaml
title: "Template Subject — a minimal demonstration"
style: left_rail
header:
  - heading: { text: "Template Subject" }
sidebar:
  - concept:
      id: obj
      text: >-
        A minimal, generic demonstration used as the copy-me template for authoring
        new cpp_labs subjects. It has two examples and one gotcha, and no memory
        diagram (diagram:false throughout).
demos:
  - ../demos/ts_value.demo.yaml
  - ../demos/ts_method.demo.yaml
```

- [ ] **Step 5: Build the page and run the two example assertions**

Run:
```bash
./build_labs.sh template_subject
pytest cpp_labs/template_subject/tests/test_template_subject.py::test_exact_baked_output -q
```
Expected: `test_exact_baked_output` still FAILS on `"count = 1"` (the gotcha isn't wired yet), but the build reports `built 1, failed 0` and the log shows the `x = 42` and `count = 2` outputs baked. This confirms the two examples compile and render.

Run the always-passing structural checks to confirm the page is well-formed:
```bash
pytest cpp_labs/template_subject/tests/test_template_subject.py::test_self_contained \
       cpp_labs/template_subject/tests/test_template_subject.py::test_no_diagram \
       cpp_labs/template_subject/tests/test_template_subject.py::test_id_uniqueness -q
```
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add cpp_labs/template_subject/topics/ts_value.topic.yaml \
        cpp_labs/template_subject/topics/ts_method.topic.yaml \
        cpp_labs/template_subject/demos/ts_value.demo.yaml \
        cpp_labs/template_subject/demos/ts_method.demo.yaml \
        cpp_labs/template_subject/layouts/template_subject.rail.yaml
git commit -m "feat(template_subject): two examples (value types, small class)"
```

---

## Task 3: Add the gotcha (`ts_gotcha`) — Correct/Mistake compile-error pair

**Files:**
- Create: `cpp_labs/template_subject/topics/ts_gotcha.topic.yaml`
- Create: `cpp_labs/template_subject/demos/ts_gotcha.demo.yaml`
- Modify: `cpp_labs/template_subject/layouts/template_subject.rail.yaml` (add the demo)

- [ ] **Step 1: Write the gotcha topic (`cases:` — Correct compiles, Mistake fails)**

Create `cpp_labs/template_subject/topics/ts_gotcha.topic.yaml`:

```yaml
id: ts_gotcha
name: "Missing accessor"
group: Gotchas
doc_url: https://en.cppreference.com/w/cpp/language/member_functions
explanation: >-
  main() calls c.value(). The Correct case provides that accessor and prints the
  count. The Mistake case omits it, so c.value() names a member that does not exist
  and the program fails to COMPILE — surfaced here as a real red compiler error.
template: |
  #include <iostream>
  class Counter {
      // running count, starts at zero
      int n_ = 0;
  public:
      void tick() { ++n_; }
      <<accessor>>
  };
  int main() {
      Counter c;
      c.tick();
      std::cout << "count = " << c.value() << "\n";
  }
cases:
  - label: "Correct: provide the accessor"
    subs:
      "<<accessor>>": |-
        // a const accessor returns the current count
        int value() const { return n_; }
  - label: "Mistake: omit the accessor  (compile error)"
    subs:
      "<<accessor>>": ""
```

- [ ] **Step 2: Write the gotcha demo**

Create `cpp_labs/template_subject/demos/ts_gotcha.demo.yaml`:

```yaml
title: "Missing accessor"
language: cpp
bake: { g: ts_gotcha }
blocks:
  - topic: { id: g, source: g, diagram: false, concept: "${g.explanation}" }
```

- [ ] **Step 3: Wire the gotcha into the layout**

In `cpp_labs/template_subject/layouts/template_subject.rail.yaml`, change the `demos:` list from:

```yaml
demos:
  - ../demos/ts_value.demo.yaml
  - ../demos/ts_method.demo.yaml
```

to:

```yaml
demos:
  - ../demos/ts_value.demo.yaml
  - ../demos/ts_method.demo.yaml
  - ../demos/ts_gotcha.demo.yaml
```

- [ ] **Step 4: Build and run the full test file (GREEN)**

Run:
```bash
./build_labs.sh template_subject
pytest cpp_labs/template_subject/tests/test_template_subject.py -q
```
Expected: build reports `built 1, failed 0`; all 6 tests PASS (`test_exact_baked_output` now finds `count = 1`; `test_gotcha_error_box` finds `out--err`; `test_correct_mistake_labels` finds both labels).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/template_subject/topics/ts_gotcha.topic.yaml \
        cpp_labs/template_subject/demos/ts_gotcha.demo.yaml \
        cpp_labs/template_subject/layouts/template_subject.rail.yaml
git commit -m "feat(template_subject): add missing-accessor gotcha (Correct/Mistake compile pair)"
```

---

## Task 4: Skill templates (`templates/`) + RED skeleton test

**Files:**
- Test: `cpp_labs/tests/test_demonstration_skill.py`
- Create: `.claude/skills/demonstration-builder/templates/topic.topic.yaml`
- Create: `.claude/skills/demonstration-builder/templates/demo.demo.yaml`
- Create: `.claude/skills/demonstration-builder/templates/layout.rail.yaml`
- Create: `.claude/skills/demonstration-builder/templates/test_subject.py`

- [ ] **Step 1: Write the failing skeleton-parse test**

Create `cpp_labs/tests/test_demonstration_skill.py`:

```python
from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "demonstration-builder"


def test_template_skeletons_parse():
    topic = yaml.safe_load((SKILL / "templates" / "topic.topic.yaml").read_text())
    for k in ("id", "name", "template", "explanation", "group"):
        assert k in topic, f"template topic missing required key {k!r}"

    demo = yaml.safe_load((SKILL / "templates" / "demo.demo.yaml").read_text())
    assert "bake" in demo and "blocks" in demo

    layout = yaml.safe_load((SKILL / "templates" / "layout.rail.yaml").read_text())
    assert layout.get("style") and "demos" in layout
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest cpp_labs/tests/test_demonstration_skill.py::test_template_skeletons_parse -q`
Expected: FAIL — the `templates/` files do not exist yet (FileNotFoundError).

- [ ] **Step 3: Create the four template skeletons**

Create `.claude/skills/demonstration-builder/templates/topic.topic.yaml`:

```yaml
# A topic = one C++ template + metadata. Required: id, name, template, explanation, group.
# Copy this file to cpp_labs/<subject>/topics/<id>.topic.yaml and edit.
# Use `class` (not struct); comments on their OWN line above the code; break long
# `<<` stream chains aligned. Omit <<HARNESS>> unless you want the raw-bytes grid.
id: my_topic                       # unique; matches filename <id>.topic.yaml
name: "Human name"                 # tab / section heading
group: Examples                    # category label (Examples, Gotchas, ...)
doc_url: https://en.cppreference.com/w/cpp/language/types
explanation: >-
  One-paragraph concept: what this example should impart. Surfaced in the right
  column via ${<bake-key>.explanation}.
template: |
  #include <iostream>
  int main() {
      // describe the line above it
      <<type>> x = <<value>>;
      std::cout << "x = " << x << "\n";
  }
# OPTIONAL — a dropdown control makes one variant tab per option:
controls:
  - id: type
    label: Type
    kind: dropdown              # dropdown | text | checkbox
    options: [int, double]
    default: int
    placeholder: <<type>>
  - id: value
    label: Value
    kind: text
    default: "42"
    placeholder: <<value>>
# OPTIONAL — a Correct/Mistake (or matrix) gotcha via independently-compiled cases:
#   Each case fills placeholders no control owns. An empty/wrong fragment that fails
#   to compile surfaces as a real red error box. Add `sanitize: true` (top level) for
#   a runtime-fault gotcha caught by AddressSanitizer instead.
# cases:
#   - label: "Correct: ..."
#     subs: { "<<slot>>": "..." }
#   - label: "Mistake: ...  (compile error)"
#     subs: { "<<slot>>": "" }
```

Create `.claude/skills/demonstration-builder/templates/demo.demo.yaml`:

```yaml
# A demo = a mini page-spec baking ONE topic. Copy to cpp_labs/<subject>/demos/<id>.demo.yaml.
# For subjects with no memory diagram, set diagram:false and put the concept in the
# right column via the topic block's `concept:` arg.
title: "Human name"
language: cpp
bake: { d: my_topic }            # compile topic id `my_topic`, expose as ${d.*}
blocks:
  - topic: { id: d, source: d, diagram: false, concept: "${d.explanation}" }
```

Create `.claude/skills/demonstration-builder/templates/layout.rail.yaml`:

```yaml
# A layout assembles demos with a nav style. Copy to
# cpp_labs/<subject>/layouts/<subject>.rail.yaml. style: left_rail | top_tabs | stacked.
title: "My Subject — one-line goal"
style: left_rail
header:
  - heading: { text: "My Subject" }
sidebar:
  # Only `concept` and `glossary` are allowed in the sidebar.
  - concept:
      id: obj
      text: >-
        The demonstration-level Main Takeaway: what the whole subject teaches.
demos:
  - ../demos/my_topic.demo.yaml
```

Create `.claude/skills/demonstration-builder/templates/test_subject.py`:

```python
# Copy to cpp_labs/<subject>/tests/test_<subject>.py and adapt the assertions.
# Tests are compiler-gated; assert EXACT baked stdout (the primary correctness gate).
import re
import shutil

import pytest
from pathlib import Path

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "my_subject.rail.yaml"

pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ("<script src", "<link", 'href="http', 'src="http'):
        assert bad not in html


def test_exact_baked_output(html):
    assert "x = 42" in html          # replace with your program's real stdout


def test_diagram_invariant(html):
    # WCAG: every <svg> carries role="img". For diagram:false subjects both are 0.
    assert html.count("<svg") == html.count('role="img"')


def test_id_uniqueness(html):
    ids = re.findall(r'id="([^"]+)"', html)
    assert len(ids) == len(set(ids))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest cpp_labs/tests/test_demonstration_skill.py::test_template_skeletons_parse -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/tests/test_demonstration_skill.py \
        .claude/skills/demonstration-builder/templates/
git commit -m "feat(skill): demonstration-builder YAML/test templates + skeleton guard test"
```

---

## Task 5: Skill reference docs (`reference/PATTERN.md`, `DIAGRAMS.md`, `CHECKLIST.md`)

**Files:**
- Test: `cpp_labs/tests/test_demonstration_skill.py` (add `test_reference_files_present`)
- Create: `.claude/skills/demonstration-builder/reference/PATTERN.md`
- Create: `.claude/skills/demonstration-builder/reference/DIAGRAMS.md`
- Create: `.claude/skills/demonstration-builder/reference/CHECKLIST.md`

- [ ] **Step 1: Add the failing reference-present test**

Append to `cpp_labs/tests/test_demonstration_skill.py`:

```python
def test_reference_files_present():
    for f in ("PATTERN.md", "DIAGRAMS.md", "CHECKLIST.md"):
        assert (SKILL / "reference" / f).read_text(encoding="utf-8").strip(), \
            f"reference/{f} is missing or empty"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest cpp_labs/tests/test_demonstration_skill.py::test_reference_files_present -q`
Expected: FAIL — the reference files do not exist yet.

- [ ] **Step 3: Write `reference/PATTERN.md`**

Distill `cpp_labs/SKILL_PREPARATION.md` into an authoring reference. It MUST cover, with the real field tables and one worked snippet each:
- The Topic / Page-or-Layout two-layer mental model; `discover_topics` auto-registration (new subject = pure YAML).
- `*.topic.yaml` anatomy (required `id/name/template/explanation/group`; `target_var`, `sanitize`, `doc_url`, `controls`, `cases`).
- `<<placeholder>>` substitution + `<<HARNESS>>` (omit to suppress the byte grid).
- `controls:` + `value_map`; variant expansion (one variant per dropdown option; text/checkbox bake at default).
- `cases:` (Correct/Mistake compile-error; `sanitize:true` runtime-fault gotcha).
- Page vs Layout wiring (`bake:`, `${a.b}` refs, `demos:`, `style:` left_rail/top_tabs/stacked, `demo.yaml`, `glossary.yaml`).
- The locked C++ style (`class` not `struct`; comments above code; break long `<<` chains).
- The §9 test families.
Point to `../../../../cpp_labs/SKILL_PREPARATION.md` as the fuller source and to `cpp_labs/template_subject/` as the worked exemplar. Include a table of contents (file will exceed 300 lines).

- [ ] **Step 4: Write `reference/DIAGRAMS.md`**

Write the diagram guide, keyed on the spec's decisions 3 + 3b:
- The **3-case triage** (renderer availability, NOT pointers): Case 1 = a built-in renderer fits; Case 2 = no renderer yet → redraw an author image as a hand-authored `_wrap_svg` SVG, else `diagram:false`; Case 3 = `diagram:false`.
- The **renderer catalog — two families**: memory (`raw/null/ref/unique/shared/weak`, with the required PTRDATA keys per type) and stackframe (`frames`/`anatomy`/`memmap`). Reference `cpp_labs/html_renderer.py::svg_renderer`.
- The **PTRDATA convention** (the `printf("PTRDATA: type=... key=...")` line, one per program).
- The **optional zero-JS interaction layer** (diagram-agnostic): `stepped_frames` (stepper + ghosting), `zoomable` (enlarge + 0.5×–2× zoom), `frames_anatomy_details`/`progressive_steps` (detail reveal), `before_after_toggle`/`variant_tabs`. State clearly it is OPTIONAL and wraps ANY SVG.
- The **case-2 seam**: mark where the future `diagram-generation` sub-skill plugs in, and that the author-image engine block is deferred.

- [ ] **Step 5: Write `reference/CHECKLIST.md`**

Write the build+verify checklist (from `SKILL_PREPARATION.md` §11–§12), with exact commands:
```bash
./build_labs.sh <subject>
pytest cpp_labs/<subject>/tests/ -q
python -m cpp_labs.yaml_engine.interface_catalog   # only if a components signature changed
python3 -m http.server -d dist_labs 8000           # visual check
```
Plus the "Add ONE example" and "Create a whole subject" ordered checklists, and the reminder that `dist_labs/` is gitignored (never commit built HTML).

- [ ] **Step 6: Run the test to verify it passes**

Run: `pytest cpp_labs/tests/test_demonstration_skill.py::test_reference_files_present -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add cpp_labs/tests/test_demonstration_skill.py \
        .claude/skills/demonstration-builder/reference/
git commit -m "feat(skill): demonstration-builder reference docs (pattern, diagrams, checklist)"
```

---

## Task 6: `SKILL.md` — the interactive workflow + triggering frontmatter

**Files:**
- Test: `cpp_labs/tests/test_demonstration_skill.py` (add `test_skill_md_frontmatter`)
- Create: `.claude/skills/demonstration-builder/SKILL.md`

- [ ] **Step 1: Add the failing frontmatter test**

Append to `cpp_labs/tests/test_demonstration_skill.py`:

```python
def test_skill_md_frontmatter():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---"), "SKILL.md must start with YAML frontmatter"
    fm = yaml.safe_load(text.split("---", 2)[1])
    assert fm["name"] == "demonstration-builder"
    assert "demonstration" in fm["description"].lower()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest cpp_labs/tests/test_demonstration_skill.py::test_skill_md_frontmatter -q`
Expected: FAIL — `SKILL.md` does not exist yet.

- [ ] **Step 3: Write `SKILL.md`**

Create `.claude/skills/demonstration-builder/SKILL.md`. Keep it lean (well under 500 lines); push detail into `reference/`. Structure:

Frontmatter (the `description` is the trigger — write it "pushy" so it fires whenever an author starts/drafts/asks to build a new cpp_labs teaching page, even without naming the skill):

```markdown
---
name: demonstration-builder
description: >-
  Build a new cpp_labs C++ teaching "demonstration" (one HTML page for a subject)
  from YAML — topics, examples, gotchas, concepts, and optional diagrams — then build
  and verify it with the real g++-at-build-time engine. Use this whenever the author
  wants to create, draft, scaffold, or add a new cpp_labs subject / demonstration /
  topic / example / gotcha, or asks to turn a C++ concept into an interactive lab
  page, even if they don't name this skill. Also use it to polish an author's draft
  topic/demo/layout YAML.
---
```

Body (imperative, explain the WHY, minimal rigid MUSTs):
- **What a demonstration is** (vocabulary: Demonstration / Example / Gotcha / Concept) and the two-layer model, pointing to `reference/PATTERN.md`.
- **The interactive workflow** (the 6 steps from the spec): (1) elicit subject name + one-line goal + concepts, invite the author to paste example code and/or images; (2) propose 2–4 examples + ≥1 gotcha, offering suggestions when the author doesn't; (3) diagram triage — read `reference/DIAGRAMS.md`, suggest whether + what kind, offer the optional interaction layer; (4) generate `topics/ demos/ layouts/ tests/` from `templates/`, in the locked C++ style; (5) build + verify per `reference/CHECKLIST.md`, reporting REAL baked output; (6) iterate to green.
- **The worked exemplar:** tell the reader to open `cpp_labs/template_subject/` and copy its shape.
- **Guardrails to state briefly with reasons:** `class` not `struct` (models encapsulation); comments above code + broken `<<` chains (readability; tests assert byte-identical stdout); `dist_labs/` is gitignored (regenerate, never commit); v1 references the in-repo engine and does not modify it.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest cpp_labs/tests/test_demonstration_skill.py -q`
Expected: PASS (all three skill-guard tests green).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/tests/test_demonstration_skill.py \
        .claude/skills/demonstration-builder/SKILL.md
git commit -m "feat(skill): demonstration-builder SKILL.md (interactive workflow + triggering)"
```

---

## Task 7: Full verification + journal entry

**Files:**
- Modify: `JOURNAL.md` (prepend a dated entry)

- [ ] **Step 1: Rebuild every page and confirm no regression**

Run: `./build_labs.sh`
Expected: `built 10, failed 0` (the 9 pre-existing pages + `template_subject`).

- [ ] **Step 2: Run the new tests + a broad sanity sweep**

Run:
```bash
pytest cpp_labs/template_subject/tests/ cpp_labs/tests/test_demonstration_skill.py -q
pytest cpp_labs/tests -q
```
Expected: the first command PASSES (6 + 3 = 9 tests); the second PASSES with no regressions in the engine-level tests.

- [ ] **Step 3: Confirm the interface catalog did not drift**

Run: `pytest cpp_labs -k interface_catalog -q`
Expected: PASS — no `components.py` signature changed, so no regen is required.

- [ ] **Step 4: Write the JOURNAL entry**

Prepend a dated entry to `JOURNAL.md` summarizing: the `demonstration-builder` skill (SKILL.md + reference + templates, in-repo-engine reference), the `template_subject` exemplar (2 examples + 1 gotcha, diagram:false), the deferred seams (case-2 image block, interactive-diagram components, engine bundling, skill-creator eval loop), and the verification numbers. Reference the spec and this plan.

- [ ] **Step 5: Commit**

```bash
git add JOURNAL.md
git commit -m "docs(journal): demonstration-builder skill + template_subject exemplar"
```

---

## Notes / deferred (do NOT implement in v1)

- **Case-2 author-image engine block** — embedding/redrawing an author image needs a small new diagram block; deferred until a real case-2 subject needs it (documented in `reference/DIAGRAMS.md`).
- **Interactive-diagram components in the template** — the exemplar is `diagram:false`; the interaction layer is documented, not exercised.
- **Engine bundling (portability)** — v1 references the in-repo engine; vendoring a copy is a later revision.
- **skill-creator eval loop** — optional empirical validation after v1 is green (multiple "build me a demonstration for X" prompts, benchmark, iterate).
