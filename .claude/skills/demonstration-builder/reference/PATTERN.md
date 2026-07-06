# Authoring Pattern Reference

Distilled from `cpp_labs/SKILL_PREPARATION.md` (421 lines — read it for fuller detail).
Worked exemplar: `cpp_labs/template_subject/` (copy-me starting point).

---

## Table of Contents

1. [Mental model — two layers](#1-mental-model--two-layers)
2. [`*.topic.yaml` anatomy](#2-topicyaml-anatomy)
3. [Placeholders: `<<name>>` and `<<HARNESS>>`](#3-placeholders-name-and-harness)
4. [`controls:` — variants and `value_map`](#4-controls--variants-and-value_map)
5. [`cases:` — Correct/Mistake and runtime gotchas](#5-cases--correctmistake-and-runtime-gotchas)
6. [PTRDATA convention](#6-ptrdata-convention)
7. [Diagram gating (`diagram: true/false`)](#7-diagram-gating-diagram-truefalse)
8. [Page / layout wiring](#8-page--layout-wiring)
9. [Locked C++ style](#9-locked-c-style)
10. [Test families](#10-test-families)
11. [Key source files](#11-key-source-files)

---

## 1. Mental model — two layers

The engine bakes **real g++ output at build time** — nothing is faked.

### Layer 1: Topic (`*.topic.yaml`)
Lives at `cpp_labs/<subject>/topics/<id>.topic.yaml`. One C++ template with
`<<placeholder>>` slots, controls/cases, and metadata. Loaded by `topic_yaml.py`;
dataclasses in `code_generator.py` (`TopicTemplate`, `ControlDef`, `CaseDef`).

### Layer 2: Page or Layout (wires topics into HTML)
Two flavors, both handled by `yaml_engine/render_page.py`:

- **Flat page** (`*.page.yaml`) — a `blocks:` list. Used by `function_args`, `basic_ptr`.
  No nav rail; simplest shape.
- **Layout** (`layouts/*.yaml` with a `demos:` key) — a list of `*.demo.yaml` mini-pages
  plus a `style:`. Used by `pointers_refs`, `op_overload`, `class_structure`, `template_subject`.

### Auto-registration
`discover_topics` scans all `cpp_labs/*/topics` and merges every `id` into one registry.
**A brand-new subject is pure YAML** — drop a folder with `topics/` and a page spec; no
engine code changes.

### Subject folder shape
```
<subject>/
  topics/     *.topic.yaml        C++ templates
  demos/      *.demo.yaml         mini page-specs (one per nav entry)
  layouts/    *.rail.yaml / *.tabs.yaml / *.page.yaml
  glossaries/ *.glossary.yaml
  tests/      test_*.py
  __init__.py
```
Minimal subjects (flat page, no diagram) omit `demos/`, `layouts/`, and `glossaries/`.

---

## 2. `*.topic.yaml` anatomy

Required fields: `id`, `name`, `template`, `explanation`, `group`. All others have
defaults; unknown top-level keys are silently ignored.

| Field | Type | Req | Default | Purpose |
|---|---|---|---|---|
| `id` | str | ✔ | — | Unique key; matches filename `<id>.topic.yaml`; referenced from `bake:`. |
| `name` | str | ✔ | — | Display name (tab / section heading). |
| `template` | str (block `\|`) | ✔ | — | C++ source with `<<placeholder>>` slots. |
| `explanation` | str | ✔ | — | Concept prose; surfaced via `${x.explanation}`. |
| `group` | str | ✔ | — | Category label (`Raw`, `Operators`, `Class Structure`, …). |
| `target_var` | str | — | `"x"` | Variable whose bytes `<<HARNESS>>` hex-dumps. |
| `sanitize` | bool | — | `false` | Compile with AddressSanitizer (`-fsanitize=address -g`). |
| `has_ptrdata` | bool | — | `true` | Advisory: program emits a `PTRDATA:` line. NOT the column switch — that is the page block's `diagram:` arg. |
| `doc_url` | str | — | `""` | cppreference link. |
| `controls` | list | — | `[]` | Dropdown/text/checkbox inputs → placeholder fills. |
| `cases` | list\|null | — | `None` | Independently-compiled sub-cases. |

### Minimal real example
(`cpp_labs/pointers_refs/topics/basic_ptr.topic.yaml`):
```yaml
id: basic_ptr
name: Basic Pointer
group: Raw
doc_url: https://en.cppreference.com/w/cpp/language/pointer
target_var: ptr
explanation: >-
  A raw pointer holds the memory address of another variable...
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

---

## 3. Placeholders: `<<name>>` and `<<HARNESS>>`

Syntax: `<<name>>` (double angle brackets — avoids clash with C++ `{}`).

`code_generator.py::generate_source` runs up to **8 replace passes**, so a placeholder
may expand into text containing another placeholder (e.g. a `value_map` entry that
itself contains `<<HARNESS>>`).

- **Control placeholders** (`<<type>>`, `<<value>>`, `<<mode>>`, `<<decl>>`, …): filled
  from the resolved control value (each control's `placeholder:` string).
- **Case placeholders** (`<<op>>`, `<<member_op>>`, `<<free_op>>`, …): filled from a
  sub-case's `subs:` dict. No control owns them.
- **`<<HARNESS>>`**: injected last. `_build_harness(target_var)` emits a `MEMBYTES:` line
  hex-dumping `sizeof(target_var)` bytes → parsed into the collapsible "Raw bytes" grid
  by `compiler_runner.py::parse_membytes`. **Omit `<<HARNESS>>`** (as diagram:false
  subjects do) to suppress the byte grid entirely.

---

## 4. `controls:` — variants and `value_map`

Per control fields: `id`, `label`, `kind` (`dropdown` | `text` | `checkbox`),
`options` (dropdown only), `default`, `placeholder` (the `<<name>>` it fills),
optional `value_map`.

Without `value_map`: the raw option string substitutes verbatim (`<<type>>` ← `int`).

With `value_map`: each option string is a **key** mapping to an arbitrary C++ fragment
— this swaps whole program bodies from one dropdown. Checkbox keys are `"true"`/`"false"`.

### Tabs-via-`value_map` snippet
```yaml
template: |
  #include <iostream>
  <<mode>>
controls:
  - id: mode
    label: Passing convention
    kind: dropdown
    options: [by value, by pointer, by reference]
    default: by value
    placeholder: <<mode>>
    value_map:
      by value: |
        void modify(int x) { ... }
        int main() { ... <<HARNESS>> }
      by pointer: |
        void modify(int* x) { ... PTRDATA: type=raw ... }
        int main() { ... }
      by reference: |
        void modify(int& x) { ... PTRDATA: type=ref ... }
        int main() { ... }
```

### Variant expansion rules
- One variant per dropdown **option** (Cartesian product across multiple dropdowns).
- `text` and `checkbox` controls bake at their default and do **not** expand variants.
- No dropdown → exactly one variant.
- The human tab label = dropdown values joined with `" / "`.

---

## 5. `cases:` — Correct/Mistake and runtime gotchas

A `CaseDef` has `label` (str) + `subs` (dict `placeholder → C++`). Each case is
**compiled independently** and stacked inside the variant panel (`stacked_subcases`).
`subs` fills placeholders that no control owns.

### (a) Compile-error gotcha
A wrong/empty fragment that genuinely fails to compile. Surfaces as a real red
compiler-error box (`error_kind: "compile"`).

```yaml
cases:
  - label: "Correct: friend non-member operator<<"
    subs:
      "<<member_op>>": "friend std::ostream& operator<<(std::ostream& os, const Vec2& v);"
      "<<free_op>>":   "std::ostream& operator<<(std::ostream& os, const Vec2& v) { return os << ...; }"
  - label: "Mistake: operator<< as a member  (compile error)"
    subs:
      "<<member_op>>": "std::ostream& operator<<(std::ostream& os) { ... }"
      "<<free_op>>": ""
```

### (b) Runtime gotcha (`sanitize: true`)
The mistake compiles but faults at runtime; ASan produces the diagnostic
(`error_kind: "runtime"`, amber badge). Examples: empty `<<copy_ctor>>` → default
shallow copy → double free; read a moved-from buffer → null deref.

Set `sanitize: true` at the topic level. ASan is compiled with
`-fsanitize=address -g`. Runtime is capped at 5 s.

**Caveat:** no `ASAN_OPTIONS` is set at build time, so `detect_stack_use_after_return`
is OFF. Prefer heap-based faults (double-free, use-after-move) which ASan catches with
defaults over stack-use-after-return.

### Combining `cases:` + `controls:`
`const_taxonomy` has a 4-option `value_map` dropdown filling `<<decl>>` AND 2 cases
filling `<<op>>` → a 4×2 matrix where the forbidden cell fails to compile.

---

## 6. PTRDATA convention

A program prints ONE line to stdout to drive the memory diagram:
```
printf("PTRDATA: type=<kind> key1=%... key2=%...\n", ...);
```
Parsed by `compiler_runner.py::parse_ptrdata` (regex `^\s*PTRDATA:\s*(.+)$`; only
the first match is read). Dispatched to an SVG by `html_renderer.py::svg_renderer`
on `type`; missing keys degrade to `"?"` and never raise.

No PTRDATA line → `ptrdata=None` → empty right cell (diagram column is kept but empty).

| `type=` | Required keys (fallback `"?"`) |
|---|---|
| `raw` | `ptr_addr`, `target_addr`, `target_val` |
| `null` | `ptr_addr` (fallback `0x0`) |
| `ref` | `ref_addr`, `target_addr`, `target_val` |
| `unique` | `ptr_addr`, `target_addr`, `val`, `is_null` (`"0"`/`"1"`) |
| `shared` | `ptr_addr`, `target_addr`, `val`, `use_count`, optional `ptr2_addr` |
| `weak` | `ptr_addr`, `expired`, `use_count` |
| *(other / none)* | renders nothing useful — omit PTRDATA instead |

### Exact emit formats
```cpp
// raw
printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%g\n",
       (void*)&ptr, (void*)ptr, (double)val);
// ref  (ref_addr == target_addr == &x because a reference has no storage)
printf("PTRDATA: type=ref ref_addr=%p target_addr=%p target_val=%d\n",
       (void*)&r, (void*)&x, x);
// null
printf("PTRDATA: type=null ptr_addr=%p\n", (void*)ptr);
```

---

## 7. Diagram gating (`diagram: true/false`)

Controlled by the **page-block** arg `diagram:` on a `topic` block (default `true`).
The topic YAML's `has_ptrdata:` is only advisory metadata.

- **`diagram: false`** (all `op_overload`/`class_structure`/`template_subject` demos):
  no two-column split; code is full-width. If a `concept` string is also supplied, it
  fills the otherwise-empty right column via `code_concept_panel`.
- **`diagram: true` but no PTRDATA** (e.g. compile-error sub-case, or the by-value
  tab): the `code_diagram_panel` grid is kept (code column width stays stable) but the
  right cell is left empty. Never show a placeholder.

**Layout rule (locked):** keep the code column a constant width across variants. Empty
column when there is nothing to draw; never a full-width reflow mid-subject.

---

## 8. Page / layout wiring

### `${}` references
`${a.b.c}` pulls from baked data: `${bp.explanation}`, `${bp.int.target_val}` (the
`int` variant's `target_val`). Whole-value refs substitute the real object; inline
refs stringify.

### Flat page (`build_page`) — `function_args`, `basic_ptr`
```yaml
title: "Function Arguments — value, pointer, reference"
language: cpp
bake:
  fa: function_args        # compile topic id, expose as ${fa.*}
blocks:
  - callout_note: { id: intro, label: Concept, text: "${fa.explanation}" }
  - color_legend: { id: legend }
  - heading: { text: "Pass the same variable three ways" }
  - topic: { id: modes, source: fa }   # diagram: true by default
  - predict_reveal_quiz: { id: quiz, question: …, options: […], correct_index: 1, explanation: … }
```
Output path: `dist_labs/<stem>/<stem>.html`.

### Layout (`build_layout`) — `pointers_refs`, `op_overload`, `class_structure`
Detected by a `demos:` key. Specify `style:` and `demos:` paths:
```yaml
title: "Pointers & References — Lab 1"
style: left_rail           # left_rail | top_tabs | stacked
header:
  - color_legend: { id: legend }
sidebar:
  - concept:  { id: obj, text: "…" }
  - glossary: { id: g-ptr, source: ../glossaries/pointers.glossary.yaml, label: "Vocabulary" }
demos:
  - ../demos/basic_ptr.demo.yaml
  - ../demos/const_taxonomy.demo.yaml
```

A `demo.yaml` mini-page:
```yaml
title: "Basic Pointer"
language: cpp
bake: { bp: basic_ptr }
blocks:
  - concept: { id: bp-note, text: "${bp.explanation}" }
  - topic:   { id: bp, source: bp, diagram: false }
```

`style:` options:
- `left_rail` — clickable list on the left, one panel visible at a time.
- `top_tabs` — tab row across the top, one panel visible.
- `stacked` — all panels shown, no switching.

The same demo set can be rendered under all three styles (three separate `*.yaml` files
pointing at the same `demos/`).

A `glossary.yaml` is `title:` + `terms:` list of `{term, def}`.

### Block vocabulary (in `blocks:`)
Smart builders: `heading`, `html`, `topic`, `concept`. Component blocks:
`callout_note`, `color_legend`, `memory_diagram`, `hover_link_diagram`,
`before_after_toggle`, `predict_reveal_quiz`, `compile_status_badge`, `output_console`,
`byte_grid`, `code_line_link`, `variant_tabs`, `code_diagram_panel`, `stacked_subcases`,
`progressive_steps`, `glossary`. Each block is a one-key mapping `{blockname: {args}}`;
component blocks require `id`. Full catalog: `usage/INTERFACE_ELEMENTS.md`.

---

## 9. Locked C++ style

All C++ inside `*.topic.yaml` templates must follow these rules:

1. **`class`, never `struct`** for encapsulation examples. Private members model good
   practice; `struct` lets sloppy direct-member access compile by accident. Non-member
   operators that read private members must be declared `friend`.
2. **Comments go on their own line ABOVE** the code they describe — never trailing
   end-of-line. (Tiny one-line `subs` fragments may carry a short inline `// …`.)
3. **Break long `std::cout` / `return os` chains at `<<`, continuations aligned** under
   the first operand. Rule of thumb: break stream statements with 3+ `<<` or > ~55 chars.
4. Tests assert **byte-identical** stdout, so any reformatting must preserve exact output.

---

## 10. Test families

Each `<subject>/tests/test_*.py` is compiler-gated
(`@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ required")`), with a
module-scoped `html` fixture calling `build_layout`/`build_page` into a tmp dir.

| Family | What to assert |
|---|---|
| Self-contained | `"<!DOCTYPE html>" in html`; `lang=` present; no `<script src`, `<link`, `href="http"`, `src="http"`. |
| Real baked stdout | Exact program output strings (e.g. `"a + b = (4, 6)"`). Primary correctness gate; must be deterministic. |
| Diagram gating | `'role="img"' not in html` for `diagram:false`; WCAG invariant `html.count("<svg") == html.count('role="img"')`. |
| Gotcha surfaces | `"out--err" in html` (compiler-error console). |
| Correct/Mistake labels | Both case labels present (HTML-escaped: `&lt;&lt;` for `<<`). |
| Style locks | `"class Vec2" in html and "struct Vec2" not in html`; `"friend std::ostream"`. |
| Id uniqueness | `re.findall(r'id="([^"]+)"', html)` then `len(ids) == len(set(ids))`. |
| Pure (no g++) tests | Drive `generate_source`/`render_page` with fake pre-baked data to verify source generation logic independently of the compiler. |

---

## 11. Key source files

| Purpose | File |
|---|---|
| Topic loader / dataclasses | `cpp_labs/topic_yaml.py`, `cpp_labs/code_generator.py` |
| `<<HARNESS>>` substitution | `cpp_labs/code_generator.py::generate_source`, `_build_harness` |
| Variant / case baking, `sanitize` | `cpp_labs/build_html.py` (`expand_variants`, `capture_variant`, `_compile_one`) |
| Compile/run + PTRDATA/MEMBYTES | `cpp_labs/compiler_runner.py` (`parse_ptrdata`, `parse_membytes`, `compile_and_run`) |
| SVG dispatch + renderers | `cpp_labs/html_renderer.py` (`svg_renderer`, `_svg_*`, `_stack_svg`) |
| Diagram gating | `cpp_labs/components.py::_demo_variant_body`, `demo_panel` |
| Page engine | `cpp_labs/yaml_engine/render_page.py` |
| Block catalog generator | `cpp_labs/yaml_engine/interface_catalog.py` → `usage/INTERFACE_ELEMENTS.md` |
| Full authoring guide | `cpp_labs/SKILL_PREPARATION.md` |
| Worked exemplar | `cpp_labs/template_subject/` |
