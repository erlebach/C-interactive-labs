# Authoring a Demonstration in `cpp_labs/` — Preparation Guide

Static reference for building a "demonstration" (one HTML teaching page for a C++
subject) from YAML. It captures the pattern that recurs across every subject so it
does not have to be rediscovered each time. This is the precursor to a future
`demonstration` skill; keep it in sync when the engine changes.

> Vocabulary (locked): **Demonstration** = one HTML file = one subject.
> **Example** = one topic (one rail/section entry). **Gotcha** = an example whose
> point is a failure. **Concept** = the prose stating what an example should impart.

Related docs: `usage/USAGE.md`, `usage/INTERFACE_ELEMENTS.md` (generated block catalog),
`docs/superpowers/specs/2026-07-04-vertical-memory-diagrams-design.md` (the SVG diagrams).

---

## 0. Mental model

The engine bakes **real g++ output at build time** — nothing is faked. Two layers:

- **Topic** — `cpp_labs/<subject>/topics/<id>.topic.yaml`: one C++ template + controls/cases +
  metadata. The only place that knows the topic YAML shape (loader: `cpp_labs/topic_yaml.py`;
  dataclasses `cpp_labs/code_generator.py`).
- **Page / Layout** — wires baked topics into an HTML page (engine:
  `cpp_labs/yaml_engine/render_page.py`). Two flavors:
  - **Flat page** `*.page.yaml` (a `blocks:` list) → `build_page`. Used by `function_args`,
    `basic_ptr`. Simplest; no rail.
  - **Layout** `<subject>/layouts/*.yaml` (a `demos:` list + a `style:`) → `build_layout`.
    Used by `pointers_refs`, `op_overload`, `class_structure`. Each demo is a tiny
    `<subject>/demos/<id>.demo.yaml` mini-page-spec.

`discover_topics` scans `cpp_labs/*/topics` and merges every id into one registry, so a brand
new subject is **pure YAML** — drop a folder with a `topics/` dir + a page spec, no code change.

Full-subject folder shape (minimal subjects omit `demos/ layouts/ glossaries/`):
```
<subject>/
  topics/     *.topic.yaml        the C++ templates
  demos/      *.demo.yaml         mini page-spec: bake one topic + concept + topic block
  layouts/    *.rail.yaml / *.tabs.yaml / *.page.yaml   assemble demos with a nav style
  glossaries/ *.glossary.yaml     shared vocabulary panels
  tests/      test_*.py
  __init__.py
```

---

## 1. `*.topic.yaml` anatomy

Required fields: `id, name, template, explanation, group`. Everything else has a default;
an unknown top-level key is silently ignored.

| Field | Type | Req | Default | Purpose |
|---|---|---|---|---|
| `id` | str | ✔ | — | Unique key; matches filename `<id>.topic.yaml`; referenced from `bake:`. |
| `name` | str | ✔ | — | Display name (tab / section heading). |
| `template` | str (block `\|`) | ✔ | — | C++ source with `<<placeholder>>` slots. |
| `explanation` | str | ✔ | — | Concept prose; surfaced via `${x.explanation}`. |
| `group` | str | ✔ | — | Category label (`Raw`, `Operators`, `Class Structure`, …). |
| `target_var` | str | — | `"x"` | Variable whose bytes `<<HARNESS>>` hex-dumps. |
| `sanitize` | bool | — | `false` | Compile with AddressSanitizer (`-fsanitize=address -g`). |
| `has_ptrdata` | bool | — | `true` | Advisory: program emits a `PTRDATA:` line. **Not** the column switch — see §7. |
| `doc_url` | str | — | `""` | cppreference link. |
| `controls` | list | — | `[]` | Dropdown/text/checkbox inputs → placeholder fills (§3). |
| `cases` | list \| null | — | `None` | Independently-compiled sub-cases (§4). |

Minimal real example (`pointers_refs/topics/basic_ptr.topic.yaml`):
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
      // emit the memory picture the diagram will draw
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

## 2. Placeholders in `template`

Syntax `<<name>>` (double angle brackets, to avoid clashing with C++ `{}`). Substitution:
`code_generator.py::generate_source` runs up to **8 replace passes**, so a placeholder may
expand into text containing another placeholder.

- **Control placeholders** (`<<type>>`, `<<value>>`, `<<mode>>`, `<<decl>>`, …): filled from the
  resolved control value (each control's `placeholder:` string).
- **Case placeholders** (`<<op>>`, `<<member_op>>`, `<<free_op>>`, `<<copy_ctor>>`, …): filled from
  a sub-case's `subs:` dict (§4). No control owns them.
- **`<<HARNESS>>`**: ALWAYS injected last. `_build_harness(target_var)` emits a `MEMBYTES:` line
  hex-dumping `sizeof(target_var)` bytes → parsed into the collapsible "Raw bytes" grid
  (`compiler_runner.py::parse_membytes`). Omit the placeholder (as diagram:false subjects do) to
  suppress the byte grid.

---

## 3. `controls:` + `value_map` (dropdown → program body)

Per control: `id`, `label`, `kind` (`dropdown` | `text` | `checkbox`), `options` (dropdown),
`default`, `placeholder` (the `<<name>>` it fills), optional `value_map`.

Without `value_map` the raw option string is substituted verbatim (`<<type>>` ← `int`). With
`value_map`, each option string is a **key** to an arbitrary C++ fragment — this swaps whole
program bodies from one dropdown. Checkbox keys are `"true"`/`"false"`.

Tabs-via-`value_map` (`function_args/topics/function_args.topic.yaml`) — the whole `main()`
differs per tab, so the template is just `<<mode>>`:
```yaml
template: |
  #include <iostream>
  #include <cstdio>
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

**Variant expansion:** one variant per dropdown *option* (Cartesian product across multiple
dropdowns). `text`/`checkbox` controls bake at their default and do NOT expand. No dropdown ⇒
exactly one variant. The human tab label = dropdown values joined with `" / "`.

---

## 4. Sub-cases (`cases:`)

A `CaseDef` is `label` (str) + `subs` (dict `placeholder → C++`). Each case is **compiled
independently** and stacked inside the variant panel (`stacked_subcases`). `subs` fill
placeholders no control owns (`<<op>>`, `<<member_op>>`, …).

Two idioms:

**(a) Compile-error gotcha** — a wrong/empty fragment that genuinely fails to compile; the
failure surfaces as a real red compiler-error box (`error_kind: "compile"`).
`op_overload/topics/op_stream.topic.yaml`:
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

**(b) Runtime gotcha** (`sanitize: true`) — the mistake compiles but faults at runtime; ASan
produces the diagnostic (`error_kind: "runtime"`, amber badge). `class_structure/cls_copy_ctor`
(empty `<<copy_ctor>>` → default shallow copy → double free); `cls_move_ops` (read a moved-from
buffer → null deref).

**Combine `cases:` + `controls:`** — `const_taxonomy` has a 4-option `value_map` dropdown filling
`<<decl>>` AND 2 cases filling `<<op>>` → a 4×2 matrix where the forbidden cell fails to compile.

---

## 5. PTRDATA convention (drives the memory diagram)

A program prints ONE line to stdout to drive the diagram:
```
printf("PTRDATA: type=<kind> key1=%... key2=%... ...\n", ...);
```
Parsed by `compiler_runner.py::parse_ptrdata` (regex `^\s*PTRDATA:\s*(.+)$`, split on whitespace
and `=` into a `{key: value}` string dict; only the first match is read). Dispatched to an SVG by
`html_renderer.py::svg_renderer` on `type`; missing keys degrade to `"?"` (never raises). No
PTRDATA line ⇒ `ptrdata=None` ⇒ empty right cell (§7).

| `type=` | Required keys (fallback `"?"`) |
|---|---|
| `raw` | `ptr_addr`, `target_addr`, `target_val` |
| `null` | `ptr_addr` (fallback `0x0`) |
| `ref` | `ref_addr`, `target_addr`, `target_val` |
| `unique` | `ptr_addr`, `target_addr`, `val`, `is_null` (`"0"`/`"1"`) |
| `shared` | `ptr_addr`, `target_addr`, `val`, `use_count`, optional `ptr2_addr` (draws 2 owners) |
| `weak` | `ptr_addr`, `expired`, `use_count` |
| *(other / none)* | renders nothing meaningful — leave PTRDATA out instead |

Exact emit formats:
```cpp
// raw
printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%g\n",
       (void*)&ptr, (void*)ptr, (double)val);
// ref  (a reference has no storage of its own, so ref_addr == target_addr == &x)
printf("PTRDATA: type=ref ref_addr=%p target_addr=%p target_val=%d\n",
       (void*)&r, (void*)&x, x);
// null
printf("PTRDATA: type=null ptr_addr=%p\n", (void*)ptr);
```

Diagrams are **vertical** (tall + narrow): source box on top, arrow pointing down, target below;
with two aliases (`shared` + `ptr2_addr`) the two boxes sit side-by-side and converge. Box text is
14px to match the code panel. See the diagram design spec for the layout rules.

---

## 6. `sanitize: true`

`build_html.py::_compile_one` passes `extra_flags=["-fsanitize=address","-g"]` when the topic sets
`sanitize`. Use it for runtime-fault gotchas whose lesson IS the crash: double free (shallow copy),
use-after-move / null deref of a moved-from buffer, plain null deref.

**Caveat:** the build sets no `ASAN_OPTIONS`, so `detect_stack_use_after_return` is OFF — a
stack-use-after-return gotcha (returning a reference to a local) is NOT reliably caught. Prefer
heap-based faults (double-free, use-after-move), which ASan catches with defaults. Runtime is
capped by a 5s timeout.

---

## 7. Diagram gating (two independent mechanisms)

Both live in `components.py::_demo_variant_body`, threaded from the **page-block** arg `diagram:`
(on a `topic` block; default `True`). Note the naming: the topic YAML's `has_ptrdata:` is advisory;
the actual column behavior is the page block's `diagram:`.

- **Per-topic `diagram: false`** (page-block arg — every `op_overload`/`class_structure` demo):
  no two-column split, code is full-width. If a `concept` is also supplied, it fills the otherwise
  empty right column via `code_concept_panel`.
- **Per-variant, `diagram:true` but no ptrdata** (a compile-error sub-case, or the by-value tab):
  the two-column `code_diagram_panel` grid is **KEPT** (so the code column width never jitters
  between tabs) but the right cell is left **EMPTY** — never the "no diagram" debug placeholder.

Layout rule (locked): **keep the code column a constant width across variants.** Empty column when
there is nothing to draw; never a placeholder box, never a full-width reflow mid-subject.

---

## 8. Page / layout wiring

### Block vocabulary (what you may write under `blocks:`)
Smart builders: `heading`, `html`, `topic`, `concept`. Component blocks: `callout_note`,
`color_legend`, `memory_diagram`, `hover_link_diagram`, `before_after_toggle`,
`predict_reveal_quiz`, `compile_status_badge`, `output_console`, `byte_grid`, `code_line_link`,
`variant_tabs`, `code_diagram_panel`, `stacked_subcases`, `progressive_steps`, `glossary`. Each
block is a one-key mapping `{blockname: {args}}`; component blocks require `id`. The generated
catalog of all blocks (args + minimal snippets) is `usage/INTERFACE_ELEMENTS.md`.

`${a.b.c}` references pull from baked data: `${bp.explanation}`, `${bp.int.target_val}` (the `int`
variant's `target_val`). Whole-value refs substitute the real object; inline refs stringify.

### Flat page (`build_page`) — `function_args`, `basic_ptr`
```yaml
title: "Function Arguments — value, pointer, reference"
language: cpp
bake:
  fa: function_args          # compile topic id `function_args`, expose as ${fa.*}
blocks:
  - callout_note: { id: intro, label: Concept, text: "${fa.explanation}" }
  - color_legend: { id: legend }
  - heading: { text: "Pass the same variable three ways" }
  - html: { content: "<p>…</p>" }
  - topic: { id: modes, source: fa }        # variant_tabs cluster over fa (diagram: true default)
  - predict_reveal_quiz: { id: quiz, question: …, options: [...], correct_index: 1, explanation: … }
```
Output path: `<dist>/<stem>/<stem>.html`, stem = filename minus `.page`.

### Layout page (`build_layout`) — `pointers_refs`, `op_overload`, `class_structure`
Detected by a `demos:` key. Has a `style:` and a list of `*.demo.yaml` paths:
```yaml
title: "Pointers & References — Lab 1"
style: left_rail                 # left_rail | top_tabs | stacked
header:
  - color_legend: { id: legend }
sidebar:                         # only `concept` and `glossary` allowed here
  - concept:  { id: obj, text: "…" }
  - glossary: { id: g-ptr, source: ../glossaries/pointers.glossary.yaml, label: "Vocabulary" }
demos:
  - ../demos/basic_ptr.demo.yaml
  - ../demos/const_taxonomy.demo.yaml
```
A `demo.yaml` is a mini page-spec:
```yaml
title: "Basic Pointer"
language: cpp
bake: { bp: basic_ptr }
blocks:
  - concept: { id: bp-note, text: "${bp.explanation}" }
  - topic:   { id: bp, source: bp }
```
**`style:`** — `left_rail` (clickable list down the left, one panel visible), `top_tabs` (tab row
across the top, one panel visible), `stacked` (all panels shown, no switching). The same demo set
can be rendered under all three (`pointers_refs.rail.yaml` / `.tabs.yaml` / flat `.page.yaml`).

A `glossary.yaml` is `title:` + `terms:` list of `{term, def}`.

---

## 9. Tests per subject

Each `<subject>/tests/test_*.py` is compiler-gated
(`skipif(shutil.which("g++") is None)`), with a module-scoped `html` fixture that calls
`build_layout`/`build_page` into a tmp dir; asserts are substring checks against baked HTML.
Families to cover:

- **Self-contained:** `"<!DOCTYPE html>" in html`, `lang=` present, no `<script src`/`<link`/
  `href="http"`/`src="http"`.
- **Real baked stdout (byte-for-byte):** assert exact program output strings (e.g.
  `"a + b = (4, 6)"`, `"copy ctor: deep-copied 3 ints"`). This is the primary correctness gate —
  outputs must be deterministic.
- **Diagram gating:** `'role="img"' not in html` for diagram:false; and the WCAG invariant
  `html.count("<svg") == html.count('role="img"')`.
- **Gotcha surfaces a real box:** `"out--err" in html` (compiler-error console).
- **Correct/Mistake pairing:** both case labels present (HTML-escaped — `&lt;&lt;` for `<<`).
- **Style locks:** `"class Vec2" in html and "struct Vec2" not in html`; `"friend std::ostream"`.
- **Id uniqueness:** regex `id="([^"]+)"` then `len(ids) == len(set(ids))` (no dup DOM ids).
- **Pure (no g++) tests:** drive `generate_source`/`render_page` with FAKE pre-baked data
  (RED-before-GREEN), e.g. by-value source has `"PTRDATA" not in src`, by-pointer has
  `"PTRDATA: type=raw"`.

---

## 10. Locked C++ style inside templates

- **`class`, never `struct`** for encapsulation examples (private members model good practice);
  non-member operators declared `friend` to reach privates.
- **Comments on their own line ABOVE the code**, never trailing. (Tiny one-line `subs` fragments may
  carry a short inline `// …`.)
- **Long `std::cout` / `return os` chains broken at `<<`, continuations aligned** under the first
  operand. Rule of thumb: break stream statements with 3+ `<<` or > ~55 chars.
- Tests assert **byte-identical** stdout, so any reformatting must preserve exact output.

---

## 11. Build & verify commands

```bash
# rebuild every page (auto-discovers cpp_labs/*/layouts/*.yaml + cpp_labs/*/*.page.yaml)
./build_labs.sh                     # or: ./build_labs.sh <subject-filter>
# build one page/layout by hand
python -m cpp_labs.yaml_engine.render_page cpp_labs/<subject>/layouts/<x>.rail.yaml dist_labs
# run one subject's tests (auto-skips if g++ absent; full suite ~3-4 min)
pytest cpp_labs/<subject>/tests/ -q
# regenerate the block catalog after changing a components.py signature it introspects
python -m cpp_labs.yaml_engine.interface_catalog     # writes usage/INTERFACE_ELEMENTS.md
# serve for a visual check (file:// is blocked for Playwright)
python3 -m http.server -d dist_labs 8000
```
`dist_labs/` (and `dist/`) are **gitignored** — HTML output is a build artifact, regenerate from
YAML, never commit it.

---

## 12. Checklists

### A. Add ONE new example/topic to an existing subject
1. Create `cpp_labs/<subject>/topics/<new_id>.topic.yaml` (required `id/name/template/explanation/
   group`). Set `target_var` + include `<<HARNESS>>` if you want the byte grid.
2. Choose the interaction: **variants** → a `dropdown` control (+ `value_map` for whole-body swaps);
   **Correct/Mistake or matrix** → `cases:` with `subs` filling `<<…>>` placeholders.
3. Memory picture? emit a `PTRDATA:` line (§5) matching one of the six `type=` renderers. No memory
   model? leave PTRDATA out — the diagram cell stays empty.
4. Runtime-fault gotcha? add `sanitize: true`.
5. Write C++ in locked style (§10).
6. Wire into the page: **layout subject** → add `demos/<new_id>.demo.yaml` (`bake` + `concept` +
   `topic`) and its path to `demos:`; set the `topic` block `diagram: false` if the subject has no
   diagram. **Flat-page subject** → add `<new_id>` to `bake:` and a `topic:` block (+ heading/concept).
7. Extend `tests/`: exact baked stdout, Correct/Mistake labels, diagram presence/absence, id uniqueness.
8. `./build_labs.sh <subject>` then `pytest cpp_labs/<subject>/tests/ -q`.

### B. Create a whole new subject from scratch (pure YAML — no engine code)
1. `mkdir cpp_labs/<subject>/topics` (+ `demos/ layouts/ glossaries/ tests/` for the layout style);
   add `__init__.py`. Ids auto-register via `discover_topics` — no code change.
2. Author `topics/<id>.topic.yaml` (§1).
3. Write the page: **flat** `<subject>.page.yaml` (copy `function_args`/`basic_ptr`), or **layout**
   `layouts/<subject>.rail.yaml` (`style:`, optional `header:`/`sidebar:`, `demos:` → tiny
   `demos/*.demo.yaml`; optional `glossaries/*.glossary.yaml`).
4. Set `diagram: false` on `topic` blocks with no memory diagram (put the concept in the right
   column via the block's `concept:` arg).
5. Add `tests/test_<subject>.py` (§9).
6. `./build_labs.sh` (auto-discovers the new spec) → verify `dist_labs/<stem>/<stem>.html`; run the
   subject tests; regen `usage/INTERFACE_ELEMENTS.md` if you introduced new block usage.

---

### Key source references
- Topic loader / dataclasses: `cpp_labs/topic_yaml.py`, `cpp_labs/code_generator.py` (`TopicTemplate`, `ControlDef`, `CaseDef`).
- Placeholder + `<<HARNESS>>` substitution: `cpp_labs/code_generator.py::generate_source`, `_build_harness`.
- Variant/case baking + `sanitize` flags: `cpp_labs/build_html.py` (`expand_variants`, `capture_variant`, `_compile_one`).
- Compile/run + PTRDATA/MEMBYTES parsing: `cpp_labs/compiler_runner.py` (`parse_ptrdata`, `parse_membytes`, `compile_and_run`).
- SVG dispatch + the six vertical renderers: `cpp_labs/html_renderer.py` (`svg_renderer`, `_svg_*`, `_stack_svg`).
- Diagram gating: `cpp_labs/components.py::_demo_variant_body`, `demo_panel`.
- Page engine (blocks, builders, bake, `build_page`/`build_layout`, CLI): `cpp_labs/yaml_engine/render_page.py`.
- Block catalog generator: `cpp_labs/yaml_engine/interface_catalog.py` → `usage/INTERFACE_ELEMENTS.md`.
- Build script: `build_labs.sh`.
