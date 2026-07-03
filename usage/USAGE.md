# USAGE — Authoring a new HTML lesson page (worked example: Function Arguments)

This guide is a **step-by-step recipe** for building a new self-contained HTML lesson
from scratch, listing **every file you create** and the one small code touch that
registers a new subject. The running example is a **Function Arguments** lesson
(pass by *value* / *pointer* / *reference*).

> This is a **description only** — it does not create the function_args files. It
> shows *what* to author and *where*. The **reference implementation** to copy from
> is the pointer subject under `cpp_ptr_lab/pointers_refs/` (fully built this way).
>
> Companion docs: `cpp_ptr_lab/pointers_refs/YAML_GUIDE.md` (per-file format
> reference) and `COURSE_VIA_TOPICS.md` (the layered architecture + rationale).

---

## 1. Mental model: data you author vs. engine you reuse

You **author YAML data**. You almost never write Python.

```
   YOU AUTHOR (YAML data)                    ENGINE (Python, already built — reuse)
   ─────────────────────                     ─────────────────────────────────────
   topics/*.topic.yaml   the C++ programs    yaml_engine/render_page.py   the engine
   demos/*.demo.yaml     one lesson slide    components.py                the widgets
   glossaries/*.yaml     vocabulary boxes    topics_loader.py             YAML → TopicTemplate
   layouts/*.yaml        the whole page      g++                          bakes real output
```

**Two phases at build time:**

```
  *.topic.yaml ──load──▶ TopicTemplate ──g++ compile+run──▶ real stdout/stderr/bytes
                                                                     │
  layout.yaml ─┬─ header (rendered once)                            ▼
               ├─ glossaries[]                          render_page assembles ONE
               └─ demos[] ── each bakes a topic ───────▶ self-contained WCAG-AA .html
```

The student opens a single HTML file: **zero JavaScript, zero network, zero backend**
— it works pasted into Canvas or opened offline.

---

## 2. The files you create for a new subject

For a subject with a handful of topics, you create one folder with four kinds of YAML
plus a two-line Python shim. Proposed layout for Function Arguments:

```
cpp_ptr_lab/function_args/
  topics/                          ← the C++ source, one file per topic (DATA)
    by_value.topic.yaml
    by_pointer.topic.yaml
    by_reference.topic.yaml
  demos/                           ← one "slide" per topic (DATA)
    by_value.demo.yaml
    by_pointer.demo.yaml
    by_reference.demo.yaml
  glossaries/                      ← optional vocabulary box(es) (DATA)
    function_args.glossary.yaml
  layouts/                         ← the page: header + glossaries + demos + nav style (DATA)
    function_args.rail.yaml
  topics.py                        ← 2-line shim: load the topic YAML (only Python you touch)
  test_function_args.py            ← build integration test (recommended, TDD)
```

| File | Kind | What it holds | How many |
|---|---|---|---|
| `topics/<id>.topic.yaml` | data | one C++ program + its controls/variants + explanation | one per topic |
| `demos/<id>.demo.yaml` | data | a lesson slide: bakes one topic, adds prose blocks | one per topic |
| `glossaries/<name>.glossary.yaml` | data | `{title, terms:[{term,def}]}` | 0..N |
| `layouts/<name>.rail.yaml` | data | the whole page (nav + which demos/glossaries) | one per page |
| `topics.py` | code (tiny) | shim that loads `topics/` into the registry | one |

> **Naming:** the topic `id:` inside each `*.topic.yaml` is the key everything else
> references (the demo's `bake:` and the registry). Keep it stable.

---

## 3. Step by step (with real Function-Arguments content)

### Step A — Write each topic's C++ as YAML (`topics/*.topic.yaml`)

A topic is a real C++ program with `<<placeholder>>` slots and a `<<HARNESS>>` marker
(the engine injects the byte-dump instrumentation there). `target_var:` names the
variable whose raw bytes are shown. Example — `topics/by_value.topic.yaml`:

```yaml
id: fa_by_value
order: 1
name: By Value
group: Function Args
doc_url: https://en.cppreference.com/w/cpp/language/functions
target_var: val
explanation: >-
  Passing by value copies the argument into the parameter. The function mutates
  its own copy, so the caller's variable is unchanged after the call.
template: |
  #include <iostream>
  #include <cstdio>
  void modify(int x) { x = 99; }        // x is a copy
  int main() {
      int val = 42;
      modify(val);
      printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%d\n",
             (void*)&val, (void*)&val, val);
      <<HARNESS>>
  }
controls: []
```

- **Variants (tabs):** to show value/pointer/reference as *tabs of one topic* instead
  of three separate topics, give the topic a `dropdown` control whose `value_map` maps
  each option to a C++ snippet (see `pointers_refs/topics/const_taxonomy.topic.yaml`
  and `ref_const.topic.yaml` for `value_map` and checkbox examples). Either shape works;
  three small topics → three nav entries, one topic-with-tabs → one nav entry.
- **Scalar styles matter** (the loader checks them byte-for-byte against real output):
  `|` for `template` (preserves literal `\n` and trailing newline), `>-` for
  single-paragraph `explanation`, `|-` for an explanation with intentional line breaks.
- **Optional keys:** `sanitize: true` (compile+run under AddressSanitizer, for UB
  demos), `has_ptrdata: false` (topic prints no `PTRDATA:` line), `cases:` (independently
  compiled sub-cases stacked in one panel — the const 2×2 truth table).

### Step B — Wrap each topic in a demo (`demos/*.demo.yaml`)

A demo is the composition unit a page lists. It **bakes** one topic (compiles it) and
lays out blocks. Minimal form — `demos/by_value.demo.yaml`:

```yaml
title: "By Value"
language: cpp
bake: { v: fa_by_value }        # compile topic id fa_by_value; expose as ${v.*}
blocks:
  - callout_note: { id: v-note, label: Concept, text: "${v.explanation}" }
  - topic: { id: v, source: v } # the variant cluster: code + diagram + output + bytes
```

You can add richer blocks (`heading`, `html`, `progressive_steps`,
`predict_reveal_quiz`, `color_legend`) — see the existing
`cpp_ptr_lab/function_args/function_args.page.yaml` for a fully fleshed single-page
example, and `YAML_GUIDE.md` for the full block catalog.

### Step C — (Optional) a glossary (`glossaries/*.glossary.yaml`)

```yaml
title: "Vocabulary — Function Arguments"
terms:
  - { term: "pass by value", def: "the parameter is a copy; caller's variable is untouched" }
  - { term: "pass by pointer", def: "the parameter is a copy of an address; *p writes through it" }
  - { term: "pass by reference", def: "the parameter is an alias for the caller's variable" }
  - { term: "out-parameter", def: "a pointer/reference param a function writes results into" }
```

Glossaries are reusable and 0..N per page; add as many as make sense.

### Step D — Compose the page (`layouts/function_args.rail.yaml`)

The layout is the whole page: a `header` rendered once, optional `glossaries`, the
ordered `demos`, and a nav `style` (`left_rail` today; `top_tabs` / `stacked` planned).

```yaml
title: "Function Arguments — value, pointer, reference"
style: left_rail
header:
  - color_legend: { id: legend }
glossaries:
  - { id: g-fa, source: ../glossaries/function_args.glossary.yaml, label: "Vocabulary" }
demos:
  - ../demos/by_value.demo.yaml
  - ../demos/by_pointer.demo.yaml
  - ../demos/by_reference.demo.yaml
```

Paths are relative to the layout file. Each demo becomes one nav entry; glossaries
appear as leading (italic) rail entries; the first demo is shown on load.

### Step E — Register the subject (the one small code touch)

The engine's topic registry must know your topic ids. Two lines:

1. **`function_args/topics.py`** — a shim that loads the YAML topics (mirror
   `pointers_refs/topics.py`):
   ```python
   from .topics_loader import load_topics          # the generic loader
   TOPIC_BY_ID = load_topics()                      # globs this subject's topics/*.topic.yaml
   TOPICS = list(TOPIC_BY_ID.values())
   ```
2. **`cpp_ptr_lab/yaml_engine/render_page.py::_topic_registry()`** — add
   `from ..function_args.topics import TOPICS as FUNC_ARGS` and splice `*FUNC_ARGS`
   into the aggregated list (it already does this for the existing subjects).

> **One-time engine generalization:** the generic loader currently lives at
> `cpp_ptr_lab/pointers_refs/topics_loader.py` and defaults to that subject's
> `topics/` dir, but it already takes a `topics_dir` argument. To use it from a
> second subject, promote it to a shared module (e.g. `cpp_ptr_lab/topics_loader.py`)
> and have each subject's shim call `load_topics(Path(__file__).parent / "topics")`.
> This is a small refactor done **once**, then every future subject is pure YAML +
> the two-line shim. (Until then, the existing `function_args/topics.py` holds its
> one topic in Python — the older style this guide replaces.)

---

## 4. Build the HTML

From the project root, run the engine on the layout (or any page spec):

```bash
python -m cpp_ptr_lab.yaml_engine.render_page \
  cpp_ptr_lab/function_args/layouts/function_args.rail.yaml dist
```

Output: `dist/function_args.rail/function_args.rail.html` — one self-contained file.
`g++` must be on PATH at build time (it compiles and runs every topic to capture real
output); it is **not** needed at view time.

You can build any number of layouts/pages from the same demos — e.g. a per-topic
standalone page for Canvas paste and a combined page for offline download, from the
same underlying files.

---

## 5. Verify (recommended, TDD)

Follow the repo's test-first convention. A build-integration test (model it on
`cpp_ptr_lab/pointers_refs/test_layouts.py` / `test_pointers_refs.py`) should assert,
on the rendered HTML: every expected demo/section is present, real baked output
appears, ids are unique across topics, and the page is self-contained (no external
`src=`/`href="http"`, every `<pre>` has a `<code>`/`<samp>` child, and SVG diagrams
carry `role="img"` text alternatives for WCAG 1.1.1). These tests are `g++`-gated
(skip cleanly where g++ is absent).

---

## 6. Checklist for a new subject

- [ ] `topics/<id>.topic.yaml` for each topic (C++ template + controls/variants + explanation)
- [ ] `demos/<id>.demo.yaml` for each topic (bakes it, adds prose)
- [ ] `glossaries/<name>.glossary.yaml` (optional, 0..N)
- [ ] `layouts/<name>.rail.yaml` (header + glossaries + ordered demos + nav style)
- [ ] `topics.py` shim loading `topics/` (+ splice into `_topic_registry()`)
- [ ] `test_<subject>.py` build-integration test (TDD, g++-gated)
- [ ] Build: `python -m cpp_ptr_lab.yaml_engine.render_page <layout>.yaml dist`
- [ ] Open `dist/<layout>/<layout>.html`, confirm it renders and is self-contained

---

## 7. Where to look for real examples

| You want… | Copy from |
|---|---|
| A topic YAML with a plain program | `cpp_ptr_lab/pointers_refs/topics/basic_ptr.topic.yaml` |
| A topic with variant tabs (`value_map`) / sub-cases (`cases`) | `.../topics/const_taxonomy.topic.yaml`, `.../topics/ref_const.topic.yaml` |
| A demo slide | `cpp_ptr_lab/pointers_refs/demos/ref_const.demo.yaml` |
| A glossary | `cpp_ptr_lab/pointers_refs/glossaries/pointers.glossary.yaml` |
| A rail layout | `cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml` |
| A rich single-page spec (headings/steps/quiz) | `cpp_ptr_lab/function_args/function_args.page.yaml` |
| The block/format reference | `cpp_ptr_lab/pointers_refs/YAML_GUIDE.md` |
| The architecture + rationale | `COURSE_VIA_TOPICS.md` |
