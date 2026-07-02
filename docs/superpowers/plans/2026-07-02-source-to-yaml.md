# pointers_refs Source → YAML Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the 8 `pointers_refs` topics' C++ source (and controls/cases) out of Python literals in `topics.py` into one `*.topic.yaml` file per topic, loaded by a generic `load_topics()`, with `topics.py` reduced to a thin re-export shim — so authoring a topic never touches Python.

**Architecture:** The `TopicTemplate`/`ControlDef`/`CaseDef` dataclasses (in `code_generator.py`) stay as the engine's in-memory schema. A new `topics_loader.py` reads YAML → builds those objects. `topics.py` becomes a ~12-line shim re-exporting the same names (`basic_ptr`, …, `TOPICS`, `TOPIC_BY_ID`), so every consumer and test stays green. A frozen JSON snapshot of the *current* Python values is the golden reference; an equivalence-guard test proves the YAML reproduces it losslessly before the literals are gone.

**Tech Stack:** Python 3, PyYAML, pytest. g++ is build-time only (not needed by loader unit tests).

**Spec:** `docs/superpowers/specs/2026-07-02-source-to-yaml-design.md`

---

## File Structure

- **Create** `cpp_ptr_lab/pointers_refs/topics_loader.py` — `load_topics(dir=None) -> dict[str, TopicTemplate]`; the only new logic.
- **Create** `cpp_ptr_lab/pointers_refs/topics/*.topic.yaml` — 8 data files (the migrated source).
- **Create** `cpp_ptr_lab/pointers_refs/test_topics_loader.py` — serialize helpers + unit tests + equivalence guard.
- **Create** `cpp_ptr_lab/pointers_refs/topics_snapshot.json` — frozen golden reference (committed).
- **Modify** `cpp_ptr_lab/pointers_refs/topics.py` — rewrite as the shim (Task 3).

## YAML scalar-style rules (critical — the guard enforces these)

| Field | Python value shape | YAML style | Why |
|---|---|---|---|
| `template` | literal `\n` (backslash+n) + one trailing newline | `\|` (literal, clip) | preserves backslashes & the single trailing newline verbatim |
| `explanation` **with** real newlines (e.g. `const_taxonomy` bullet list) | real `\n` chars, no trailing newline | `\|-` (literal, strip) | keeps intentional line breaks, drops trailing newline |
| `explanation` single-paragraph prose (no newlines) | one logical line, no trailing newline | `>-` (folded, strip) | folds wrapped lines back to single spaces → matches the one-line Python string |
| `value_map` C++ snippet (multi-line) | real `\n` chars | `\|-` | literal C++ lines |
| booleans, ids, options | scalars | plain | — |

Blank lines inside a `>-` block fold to a newline — never leave a blank line inside a folded prose block.

---

### Task 1: Freeze the golden snapshot from the current Python topics

**Files:**
- Create: `cpp_ptr_lab/pointers_refs/test_topics_loader.py` (helpers only, this task)
- Create: `cpp_ptr_lab/pointers_refs/topics_snapshot.json`

- [ ] **Step 1: Write the serialize helpers** in `cpp_ptr_lab/pointers_refs/test_topics_loader.py`

```python
"""Loader tests + golden-equivalence guard for pointers_refs topic YAML."""
from __future__ import annotations

import json
from pathlib import Path

from cpp_ptr_lab.code_generator import TopicTemplate

_HERE = Path(__file__).parent
_SNAPSHOT = _HERE / "topics_snapshot.json"


def serialize_control(c) -> dict:
    return {
        "id": c.id, "label": c.label, "kind": c.kind,
        "options": list(c.options), "default": c.default,
        "placeholder": c.placeholder, "value_map": c.value_map,
    }


def serialize_topic(t: TopicTemplate) -> dict:
    return {
        "id": t.id, "name": t.name, "group": t.group, "doc_url": t.doc_url,
        "explanation": t.explanation, "target_var": t.target_var,
        "template": t.template, "sanitize": t.sanitize,
        "has_ptrdata": t.has_ptrdata,
        "controls": [serialize_control(c) for c in t.controls],
        "cases": ([{"label": c.label, "subs": c.subs} for c in t.cases]
                  if t.cases else None),
    }


def serialize_all(topics) -> dict:
    return {t.id: serialize_topic(t) for t in topics}
```

- [ ] **Step 2: Generate the frozen snapshot from the CURRENT Python `topics.py`** (before any change)

Run:
```bash
python -c "
import json
from cpp_ptr_lab.pointers_refs.topics import TOPICS
from cpp_ptr_lab.pointers_refs.test_topics_loader import serialize_all, _SNAPSHOT
_SNAPSHOT.write_text(json.dumps(serialize_all(TOPICS), indent=2, ensure_ascii=False) + '\n')
print('wrote', _SNAPSHOT, 'with', len(TOPICS), 'topics')
"
```
Expected: `wrote .../topics_snapshot.json with 8 topics`

- [ ] **Step 3: Sanity-check the snapshot** captured all 8 in order and includes the tricky fields

Run: `python -c "import json,pathlib; d=json.loads(pathlib.Path('cpp_ptr_lab/pointers_refs/topics_snapshot.json').read_text()); print(list(d)); print('cases:', d['const_taxonomy']['cases'] is not None); print('value_map:', d['ref_no_null']['controls'][0]['value_map'] is not None)"`
Expected: the 8 ids in legacy order, `cases: True`, `value_map: True`

- [ ] **Step 4: Commit**

```bash
git add cpp_ptr_lab/pointers_refs/test_topics_loader.py cpp_ptr_lab/pointers_refs/topics_snapshot.json
git commit -m "test(topics): freeze golden snapshot of pointers_refs Python topics"
```

---

### Task 2: Author the 8 topic YAMLs + the loader (RED → GREEN against the snapshot)

**Files:**
- Create: `cpp_ptr_lab/pointers_refs/topics_loader.py`
- Create: `cpp_ptr_lab/pointers_refs/topics/*.topic.yaml` (8)
- Modify: `cpp_ptr_lab/pointers_refs/test_topics_loader.py` (add tests)

- [ ] **Step 1: Write the failing tests** — append to `test_topics_loader.py`

```python
import pytest

from cpp_ptr_lab.pointers_refs.topics_loader import load_topics

_LEGACY_ORDER = [
    "basic_ptr", "const_taxonomy", "ref_must_bind", "ref_no_null",
    "ref_rebind_illusion", "ref_const", "null_deref", "dangling_ptr",
]


@pytest.fixture(scope="module")
def loaded():
    return load_topics()


def test_order_preserved(loaded):
    assert list(loaded.keys()) == _LEGACY_ORDER


def test_load_basic_ptr_roundtrips(loaded):
    t = loaded["basic_ptr"]
    assert t.target_var == "ptr"
    assert "<<type>>" in t.template and "<<HARNESS>>" in t.template
    assert [c.id for c in t.controls] == ["type", "value"]


def test_value_map_loaded(loaded):
    ctrl = loaded["ref_no_null"].controls[0]
    assert ctrl.value_map is not None
    assert "nullptr" in ctrl.value_map["Show null ptr"]


def test_cases_loaded(loaded):
    cases = loaded["const_taxonomy"].cases
    assert cases is not None and len(cases) == 2
    assert "*ptr = 99" in cases[0].subs["<<op>>"]      # case[0] = write
    assert "ptr = &other" in cases[1].subs["<<op>>"]   # case[1] = rebind


def test_defaults_applied(loaded):
    t = loaded["ref_must_bind"]
    assert t.sanitize is False
    assert t.has_ptrdata is False   # ref_must_bind sets this explicitly
    assert loaded["basic_ptr"].has_ptrdata is True
    assert loaded["basic_ptr"].cases is None


def test_yaml_matches_legacy(loaded):
    """Equivalence guard: YAML reproduces the frozen Python snapshot exactly."""
    golden = json.loads(_SNAPSHOT.read_text())
    actual = serialize_all(loaded.values())
    assert actual == golden
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_topics_loader.py -q`
Expected: FAIL — `ModuleNotFoundError: cpp_ptr_lab.pointers_refs.topics_loader`

- [ ] **Step 3: Write the loader** `cpp_ptr_lab/pointers_refs/topics_loader.py`

```python
"""Load pointers_refs topic definitions from YAML into TopicTemplate objects.

Source of truth for each topic's C++ template, controls, and sub-cases is a
``topics/<id>.topic.yaml`` file next to this module.  This loader is the only
place that knows the YAML shape; ``topics.py`` is a thin re-export shim over it.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from cpp_ptr_lab.code_generator import CaseDef, ControlDef, TopicTemplate

_TOPICS_DIR = Path(__file__).parent / "topics"

# Fields consumed by TopicTemplate beyond the always-required ones.
_REQUIRED = ("id", "name", "template", "explanation", "group")


def _control(d: dict) -> ControlDef:
    return ControlDef(
        id=d["id"],
        label=d["label"],
        kind=d["kind"],
        options=list(d.get("options", [])),
        default=d.get("default", ""),
        placeholder=d.get("placeholder", ""),
        value_map=d.get("value_map"),
    )


def _case(d: dict) -> CaseDef:
    return CaseDef(label=d["label"], subs=dict(d.get("subs", {})))


def _topic(d: dict) -> TopicTemplate:
    for key in _REQUIRED:
        if key not in d:
            raise ValueError(f"topic YAML missing required field {key!r}: {d.get('id', '?')}")
    cases = d.get("cases")
    return TopicTemplate(
        id=d["id"],
        name=d["name"],
        template=d["template"],
        controls=[_control(c) for c in d.get("controls", [])],
        explanation=d["explanation"],
        group=d["group"],
        target_var=d.get("target_var", "x"),
        sanitize=d.get("sanitize", False),
        has_ptrdata=d.get("has_ptrdata", True),
        doc_url=d.get("doc_url", ""),
        cases=[_case(c) for c in cases] if cases else None,
    )


def load_topics(dir: Path | None = None) -> dict[str, TopicTemplate]:
    """Return ``{id: TopicTemplate}`` for all ``*.topic.yaml`` in *dir*.

    Ordered by each file's ``order:`` integer (falls back to id for ties),
    so the returned dict preserves the intended nav order.
    """
    directory = dir or _TOPICS_DIR
    docs = []
    for path in directory.glob("*.topic.yaml"):
        data = yaml.safe_load(path.read_text())
        docs.append(data)
    docs.sort(key=lambda d: (d.get("order", 1_000_000), d["id"]))
    return {d["id"]: _topic(d) for d in docs}
```

- [ ] **Step 4: Author `topics/basic_ptr.topic.yaml`** (exemplar: `>-` prose, `|` template, dropdown + text controls)

```yaml
id: basic_ptr
order: 1
name: Basic Pointer
group: Raw
doc_url: https://en.cppreference.com/w/cpp/language/pointer
target_var: ptr
explanation: >-
  A raw pointer holds the memory address of another variable. Dereferencing it
  (*ptr) accesses the value at that address. The pointer variable itself
  occupies sizeof(void*) bytes on the stack.
template: |
  #include <iostream>
  #include <cstdio>
  int main() {
      <<type>> val = (<<type>>)<<value>>;
      <<type>>* ptr = &val;
      printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%g\n",
             (void*)&ptr, (void*)ptr, (double)val);
      <<HARNESS>>
  }
controls:
  - id: type
    label: Type
    kind: dropdown
    options: [int, double, float]
    default: int
    placeholder: <<type>>
  - id: value
    label: Value
    kind: text
    default: "42"
    placeholder: <<value>>
```

- [ ] **Step 5: Author `topics/const_taxonomy.topic.yaml`** (exemplar: `|-` bulleted explanation, `value_map`, `cases`)

```yaml
id: const_taxonomy
order: 2
name: const Taxonomy
group: Raw
doc_url: https://en.cppreference.com/w/cpp/language/cv
target_var: val
explanation: |-
  - const has two independent axes — read the declaration right-to-left:
  - const int* = pointer to const int → can't write *ptr (the pointee is const);
  - int* const = const pointer to int → can't rebind ptr (the pointer is const);
  - const int* const = both are const → neither operation is allowed.
  - Each type below attempts BOTH operations as separate compilations: write through the pointer (*ptr = 99) and rebind it (ptr = &other). The forbidden one genuinely fails to compile — read the error.
template: |
  #include <iostream>
  #include <cstdio>
  int main() {
      int val = 42;
      int other = 7;
      <<decl>>
      <<op>>
      printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%d\n",
             (void*)&ptr, (void*)ptr, *ptr);
      <<HARNESS>>
  }
controls:
  - id: variant
    label: Pointer type
    kind: dropdown
    options:
      - "int* (pointer and value both mutable)"
      - "const int* (value immutable, pointer mutable)"
      - "int* const (pointer immutable, value mutable)"
      - "const int* const (both immutable)"
    default: "int* (pointer and value both mutable)"
    placeholder: <<decl>>
    value_map:
      "int* (pointer and value both mutable)": "int* ptr = &val;"
      "const int* (value immutable, pointer mutable)": "const int* ptr = &val;"
      "int* const (pointer immutable, value mutable)": "int* const ptr = &val;"
      "const int* const (both immutable)": "const int* const ptr = &val;"
cases:
  - label: "Write through pointer:  *ptr = 99;"
    subs:
      "<<op>>": "*ptr = 99;  // write through the pointer"
  - label: "Rebind pointer:  ptr = &other;"
    subs:
      "<<op>>": "ptr = &other;  // repoint to another int"
```

- [ ] **Step 6: Author the remaining 6 YAMLs by verbatim transcription from `topics.py`**

For each topic below, create `topics/<id>.topic.yaml`. Transcribe every field **verbatim** from the cited `cpp_ptr_lab/pointers_refs/topics.py` lines, applying the scalar-style table above. Do **not** paraphrase. The equivalence guard (`test_yaml_matches_legacy`) fails until each is byte-exact — that test is the completeness check for this step.

| id | order | topics.py lines | Notes / non-default keys |
|---|---|---|---|
| `ref_must_bind` | 3 | 127–148 | `explanation` = `>-` (single paragraph); `controls: []`; `target_var: r`; `has_ptrdata: false`. No value_map/cases. |
| `ref_no_null` | 4 | 154–199 | `explanation` = `>-`; one dropdown with `value_map` (2 keys, each a multi-line C++ snippet → `\|-`); `target_var: ptr`; `sanitize: true`. |
| `ref_rebind_illusion` | 5 | 205–234 | `explanation` = `>-`; `controls: []`; `target_var: a`. Defaults otherwise. |
| `ref_const` | 6 | 240–289 | `explanation` = `>-`; two controls — a dropdown (`ref_type`, value_map `int&`/`const int&`) and a **checkbox** (`modify`, `default: false`, value_map keys `"false"`/`"true"`); `target_var: x`. |
| `null_deref` | 7 | 295–320 | `explanation` = `>-`; `controls: []`; `target_var: ptr`; `sanitize: true`. |
| `dangling_ptr` | 8 | 326–357 | `explanation` = `>-`; `controls: []`; `target_var: ptr`; `sanitize: true`. Template defines a `make_dangling()` helper — copy exactly. |

Checkbox `default: false` must be the YAML boolean `false` (not the string `"false"`) — the resolver keys booleans to `"true"`/`"false"` (see `code_generator._resolve_control_value`). The snapshot preserves the bool, so the guard catches a stringified default.

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/test_topics_loader.py -q`
Expected: PASS (all unit tests + `test_yaml_matches_legacy`). If the guard fails, it prints the first differing field — fix that YAML and rerun. Do not edit the snapshot.

- [ ] **Step 8: Commit**

```bash
git add cpp_ptr_lab/pointers_refs/topics_loader.py cpp_ptr_lab/pointers_refs/topics/ cpp_ptr_lab/pointers_refs/test_topics_loader.py
git commit -m "feat(topics): load pointers_refs topics from YAML (equivalence-guarded)"
```

---

### Task 3: Reduce `topics.py` to the re-export shim

**Files:**
- Modify: `cpp_ptr_lab/pointers_refs/topics.py`

- [ ] **Step 1: Replace the whole file** with the shim

```python
"""Lab 1 — Pointers & References topics.

Source of truth is now ``topics/*.topic.yaml`` (loaded by ``topics_loader``).
This module is a thin re-export shim so existing importers keep working:
the C++ source lives in YAML, not here.
"""
from __future__ import annotations

from cpp_ptr_lab.code_generator import TopicTemplate

from .topics_loader import load_topics

TOPIC_BY_ID: dict[str, TopicTemplate] = load_topics()
TOPICS: list[TopicTemplate] = list(TOPIC_BY_ID.values())

basic_ptr = TOPIC_BY_ID["basic_ptr"]
const_taxonomy = TOPIC_BY_ID["const_taxonomy"]
ref_must_bind = TOPIC_BY_ID["ref_must_bind"]
ref_no_null = TOPIC_BY_ID["ref_no_null"]
ref_rebind_illusion = TOPIC_BY_ID["ref_rebind_illusion"]
ref_const = TOPIC_BY_ID["ref_const"]
null_deref = TOPIC_BY_ID["null_deref"]
dangling_ptr = TOPIC_BY_ID["dangling_ptr"]
```

- [ ] **Step 2: Verify the named imports still resolve**

Run: `python -c "from cpp_ptr_lab.pointers_refs.topics import basic_ptr, const_taxonomy, ref_must_bind, ref_no_null, ref_rebind_illusion, ref_const, null_deref, dangling_ptr, TOPICS, TOPIC_BY_ID; print(len(TOPICS), basic_ptr.id, TOPICS[1].id)"`
Expected: `8 basic_ptr const_taxonomy`

- [ ] **Step 3: Run the loader tests + the fast (non-g++) pointers_refs tests**

Run: `python -m pytest cpp_ptr_lab/pointers_refs/ -q`
Expected: PASS (layouts/integration g++ tests may skip without g++; loader tests pass).

- [ ] **Step 4: Commit**

```bash
git add cpp_ptr_lab/pointers_refs/topics.py
git commit -m "refactor(topics): reduce topics.py to a YAML-backed re-export shim"
```

---

### Task 4: Full-suite verification + rail-page byte-identity + JOURNAL

**Files:**
- Modify: `JOURNAL.md` (prepend one entry)

- [ ] **Step 1: Snapshot the current rail HTML** (pre-change reference already on disk from `main`)

Run: `test -f dist/pointers_refs.rail/pointers_refs.rail.html && cp dist/pointers_refs.rail/pointers_refs.rail.html /tmp/rail_before.html && echo saved || echo "no prior build — will compare after rebuild only"`
Expected: `saved` (or the no-prior message)

- [ ] **Step 2: Run the full suite** (g++ present)

Run: `python -m pytest cpp_ptr_lab/ -q`
Expected: PASS — same count as before the change (≈405), zero failures. The equivalence guard adds ~6 tests; net count rises accordingly.

- [ ] **Step 3: Rebuild the rail page and confirm byte-identical output**

Run:
```bash
python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml dist
diff /tmp/rail_before.html dist/pointers_refs.rail/pointers_refs.rail.html && echo "IDENTICAL"
```
Expected: `IDENTICAL` (no diff) — the migration changed the *source of* the topics, not their rendered output. If `/tmp/rail_before.html` didn't exist, skip the diff; the equivalence guard already proves output-driving data is unchanged.

- [ ] **Step 4: Prepend a JOURNAL entry** to `JOURNAL.md` (one entry, latest-first) summarizing: the 8 pointers_refs topics moved Python→YAML; `topics.py` now a shim; equivalence guard; suite count; rail byte-identical. Follow the existing entry format.

- [ ] **Step 5: Commit**

```bash
git add JOURNAL.md
git commit -m "docs(journal): pointers_refs C++ source migrated Python → YAML"
```

---

## Self-Review

- **Spec coverage:** loader (Task 2) ✓; one-file-per-topic YAML (Task 2) ✓; shim re-exporting all named symbols (Task 3) ✓; thin faithful constructor with clear errors on missing required fields (`_topic` raises `ValueError`) ✓; per-file `order:` (loader sort + `test_order_preserved`) ✓; equivalence guard (`test_yaml_matches_legacy` + snapshot) ✓; full-suite green + rail byte-identity (Task 4) ✓. All six spec test items are present.
- **Placeholder scan:** none — every code/YAML/command step is complete. The 6 mechanical YAMLs (Task 2 Step 6) are specified by exact source lines + non-default-key table + scalar rules, and mechanically gated by the equivalence guard rather than paraphrased (deliberate DRY: `topics.py` is the single authoritative source to transcribe from, and the guard makes any transcription error a hard test failure, not a silent one).
- **Type consistency:** `load_topics()` / `serialize_topic` / `serialize_all` / `_SNAPSHOT` / `TOPIC_BY_ID` / `TOPICS` names match across Tasks 1–4; `ControlDef`/`CaseDef`/`TopicTemplate` signatures match `code_generator.py`.
