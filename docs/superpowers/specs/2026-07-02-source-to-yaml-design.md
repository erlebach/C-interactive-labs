# Design: move pointers_refs C++ source from Python → YAML

**Date:** 2026-07-02
**Status:** approved (awaiting spec review)
**Scope:** `cpp_ptr_lab/pointers_refs` only (8 topics). `smart_ptrs` and `function_args` are out of scope; the loader is written generically so they can migrate later.

## Goal (the North Star, final step)

Make the C++ topic source **pure YAML data**. Authoring or editing a topic's C++ program, its
controls, or its sub-cases must never touch Python. After this change, `pointers_refs` Python holds
**zero C++ source** — only generic wiring.

## Background: where the source lives today

Each topic is a hand-written `TopicTemplate` dataclass instance in
`cpp_ptr_lab/pointers_refs/topics.py` (8 instances). A `TopicTemplate` carries:

- `id`, `name`, `group`, `doc_url`, `explanation`, `target_var`
- `template` — the C++ source with `<<placeholder>>` slots and a `<<HARNESS>>` marker
- `controls` — list of `ControlDef` (dropdown / text / checkbox), each with an optional `value_map`
  (option-string → C++ snippet)
- `cases` — optional list of `CaseDef` (`label` + `subs: {<<placeholder>>: snippet}`) for the
  multi-sub-case truth tables (e.g. `const_taxonomy`)
- flags: `sanitize` (bool), `has_ptrdata` (bool)

The dataclasses live in `cpp_ptr_lab/code_generator.py`. The engine
(`generate_source`, `expand_variants`, `capture_variant`) and every consumer read `TopicTemplate`
objects. `render_page._topic_registry()` imports the named instances; legacy DPG consumers
(`gallery.py`, `topic_page.py`, `run_ptrs.py`, `build_html.py`, `basic_ptr/topics.py`) import
`basic_ptr` / `TOPICS`. Several of these have passing tests, so the named exports must survive.

## Architecture

**Unchanged.** The `TopicTemplate` / `ControlDef` / `CaseDef` dataclasses remain the engine's
in-memory schema. `generate_source`, `expand_variants`, `capture_variant`, and the whole
render/bake pipeline are untouched — they still consume `TopicTemplate` objects.

**New.** A loader builds those dataclass objects from YAML. Source of truth for C++ moves from
Python literals to YAML block scalars.

**Shim.** `pointers_refs/topics.py` shrinks to generic wiring that re-exports the identical names.
Every current consumer imports the same names and stays green. Python holds zero C++.

```
topics/*.topic.yaml ──load_topics()──▶ {id: TopicTemplate} ──▶ topics.py shim re-exports
                                                                  │  basic_ptr, TOPICS, …
                                                                  ▼
                              render_page._topic_registry() / build_html / gallery / …
```

### Components

- **`pointers_refs/topics/*.topic.yaml`** (8 new files) — one per topic, mirroring the existing
  `demos/` and `glossaries/` one-file-per-item convention. Each is self-contained and
  independently reviewable.
- **`pointers_refs/topics_loader.py`** (new) — `load_topics(dir=None) -> dict[str, TopicTemplate]`.
  Globs `topics/*.topic.yaml`, orders by each file's `order:` int, builds
  `ControlDef` / `CaseDef` / `TopicTemplate`. Kept separate from the shim so it is independently
  testable and reusable by the other packages later.
- **`pointers_refs/topics.py`** (rewritten as shim, ~12 lines):
  ```python
  from .topics_loader import load_topics
  TOPIC_BY_ID = load_topics()
  TOPICS = list(TOPIC_BY_ID.values())          # ordered by each file's `order:` int
  basic_ptr = TOPIC_BY_ID["basic_ptr"]
  const_taxonomy = TOPIC_BY_ID["const_taxonomy"]
  ref_must_bind = TOPIC_BY_ID["ref_must_bind"]
  ref_no_null = TOPIC_BY_ID["ref_no_null"]
  ref_rebind_illusion = TOPIC_BY_ID["ref_rebind_illusion"]
  ref_const = TOPIC_BY_ID["ref_const"]
  null_deref = TOPIC_BY_ID["null_deref"]
  dangling_ptr = TOPIC_BY_ID["dangling_ptr"]
  ```

## YAML schema

Every `TopicTemplate` field maps to a YAML key; the multi-line C++ becomes a `|` block scalar with
backslashes and `<<placeholders>>` preserved verbatim. Example — `basic_ptr.topic.yaml`:

```yaml
id: basic_ptr
order: 1
name: Basic Pointer
group: Raw
doc_url: https://en.cppreference.com/w/cpp/language/pointer
target_var: ptr
explanation: >-
  A raw pointer holds the memory address of another variable. Dereferencing
  it (*ptr) accesses the value at that address. The pointer variable itself
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

- **`value_map`** (e.g. `const_taxonomy`, `ref_no_null`, `ref_const`) — a YAML mapping of
  option-string → C++ snippet; multi-line snippets use `|-`.
- **`cases`** (e.g. `const_taxonomy`) — a `cases:` list of `{label, subs: {<<op>>: "..."}}`, in the
  order the truth table requires (write, then rebind).
- **Booleans** — `sanitize: true`, `has_ptrdata: false` map directly.
- **Omitted keys** fall back to dataclass defaults (`sanitize=False`, `has_ptrdata=True`,
  `cases=None`, `controls=[]`, `target_var="x"`, `doc_url=""`).

### Validation

The loader is a **thin, faithful constructor**: it builds the dataclasses and lets a missing
required field (`id` / `name` / `template` / `explanation` / `group`) raise a clear
`KeyError` / `ValueError`. No schema framework (no pydantic / jsonschema) — matches the repo's
existing lightweight YAML handling.

### Ordering

`TOPICS` order (asserted by tests, drives nav) is preserved by a per-file `order:` integer; the
loader sorts by it. Ordering stays data, not a Python list. Legacy order:

1 basic_ptr, 2 const_taxonomy, 3 ref_must_bind, 4 ref_no_null, 5 ref_rebind_illusion,
6 ref_const, 7 null_deref, 8 dangling_ptr.

## Testing plan (TDD RED → GREEN)

New `pointers_refs/test_topics_loader.py`:

1. **`test_load_basic_ptr_roundtrips`** — loaded `basic_ptr`: `id`, `template` contains `<<type>>`
   and `<<HARNESS>>`, two controls, `target_var == "ptr"`.
2. **`test_value_map_loaded`** — `ref_no_null` / `const_taxonomy` value_maps map option → C++
   snippet correctly.
3. **`test_cases_loaded`** — `const_taxonomy` has 2 `CaseDef`s in the right order (write, then
   rebind — an existing integration test depends on this).
4. **`test_defaults_applied`** — a topic omitting `sanitize` / `has_ptrdata` / `cases` gets
   `False` / `True` / `None`.
5. **`test_order_preserved`** — `TOPICS` ids equal the exact legacy order above.
6. **`test_yaml_matches_legacy` (equivalence guard)** — every field of all 8 loaded topics matches
   a frozen snapshot of the current Python values, proving the migration is lossless. The snapshot
   is captured from the current `topics.py` **before** conversion.
7. **Full suite green** — all existing tests (they import the same names via the shim) plus a
   rebuild of the rail page confirming byte-identical HTML output.

The equivalence guard (#6) is the key discipline: it proves the YAML reproduces the Python exactly,
variant-for-variant, before the Python literals are deleted.

## Non-goals

- Migrating `smart_ptrs` or `function_args` (loader is generic; they follow later).
- Changing the dataclasses, the engine, the demo/glossary/layout YAMLs, or any rendered output.
- Deleting `topics.py` (it stays as the shim so every consumer stays green).

## Risks & mitigations

- **Backslash / newline fidelity in `template`.** The C++ needs literal `\n` (backslash + n).
  YAML block scalars preserve backslashes verbatim, so `\n` written in the block stays `\n`.
  The equivalence guard (#6) catches any drift.
- **Ordering drift.** Alphabetical filename order ≠ legacy order; the `order:` int fixes this and
  `test_order_preserved` guards it.
- **Legacy consumer breakage.** The shim re-exports every named symbol; the full suite (incl.
  `test_gallery`, `test_topic_page`, `test_integration`) is the guard.
