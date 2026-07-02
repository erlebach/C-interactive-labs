# How the YAML files fit together

A plain-language guide to authoring the C++ lab pages. If you can edit a text file,
you can add or change a lab page here — **you never touch Python to add content.**

---

## 1. The one big idea

There are two worlds in this project:

- **A small, fixed set of Python** (the "engine" + a library of "components"). You
  rarely change this. Think of it as the *machine*.
- **A growing pile of YAML files** (the demos, glossaries, and layouts). This is the
  *material* you feed the machine. Adding a new lab page = adding YAML.

You run one command. The engine reads your YAML, compiles the real C++ it points at,
and writes **one self-contained `.html` file** you can open in a browser or paste into
Canvas. No JavaScript, no server, no internet needed at view time.

```
   YOU WRITE                 THE ENGINE DOES                    YOU GET
  ┌──────────┐   one command  ┌───────────────────────┐      ┌──────────────┐
  │  *.yaml  │ ─────────────▶ │ read YAML → run g++ →  │ ───▶ │  one .html   │
  │  (data)  │                │ build HTML             │      │  (open it)   │
  └──────────┘                └───────────────────────┘      └──────────────┘
```

---

## 2. The three kinds of YAML file

Everything you author is one of exactly three things:

| File type | Ends in | In one sentence | Analogy |
|-----------|---------|-----------------|---------|
| **demo** | `.demo.yaml` | One whole topic (e.g. "Basic Pointer"), with its concept note + its interactive code panel. | One **slide**. |
| **glossary** | `.glossary.yaml` | A reusable list of term → definition pairs. | A **vocabulary box**. |
| **layout** | `.rail.yaml` / `.tabs.yaml` | A page: which demos to show, in what navigation style, with a header on top. | The **slideshow** that arranges the slides. |

A **layout is the only thing you "build"** into a page. It *points at* demos and a
glossary; they are reusable ingredients it pulls in.

---

## 3. Where the files live

```
cpp_ptr_lab/pointers_refs/
│
├── demos/                         ← the reusable "slides" (one topic each)
│     basic_ptr.demo.yaml
│     const_taxonomy.demo.yaml
│     ref_must_bind.demo.yaml
│     ref_no_null.demo.yaml
│     ref_rebind_illusion.demo.yaml
│     ref_const.demo.yaml
│     null_deref.demo.yaml
│     dangling_ptr.demo.yaml
│
├── glossaries/                    ← reusable vocabulary boxes
│     pointers.glossary.yaml
│
├── layouts/                       ← the pages (each picks demos + a style)
│     pointers_refs.rail.yaml      (left-rail navigation)
│     pointers_refs.tabs.yaml      (top-tabs navigation)
│
└── topics.py                      ← the actual C++ source lives here (Python)
```

Only `topics.py` is Python — and you only touch it when you want a *brand-new C++
topic* that doesn't exist yet. Everything under `demos/`, `glossaries/`, `layouts/`
is plain YAML.

---

## 4. Reading each file type (with the real files)

### 4a. A demo file — `demos/basic_ptr.demo.yaml`

```yaml
title: "Basic Pointer"                                    # ① name of this slide
bake: { bp: basic_ptr }                                   # ② compile this C++ topic
blocks:                                                    # ③ what to show, top to bottom
  - callout_note: { id: bp-note, label: Concept, text: "${bp.explanation}" }
  - topic:        { id: bp,      source: bp }
```

Line by line:

1. **`title:`** — the human name. Shows up in the page's navigation ("Basic Pointer").
2. **`bake:`** — "compile some C++ before rendering." It's a little dictionary of
   `nickname: topic_id`. Here `bp` is a nickname *you* pick, and `basic_ptr` is the id
   of a real C++ topic defined in `topics.py`. The engine finds that topic, runs `g++`
   on it, and stashes the results (compiled code, real program output, the memory
   diagram data) under the nickname `bp`.
3. **`blocks:`** — an ordered list of things to render down the page. Each block is
   `{ block_type: {its settings} }`. This demo has two:
   - **`callout_note`** — a small concept box. Its `text` is `"${bp.explanation}"`.
     The `${bp.explanation}` part means *"look up the baked topic nicknamed `bp` and
     insert its explanation text here."* (More on `${…}` in §5.)
   - **`topic`** — the interactive panel: the code, a compile ✓/✗ badge, the real
     program output, and a memory diagram, with tabs for each variant (for `basic_ptr`
     those tabs are `int` / `double` / `float`). `source: bp` tells it which baked
     nickname to draw from.

That's a whole demo: **compile one C++ topic, show a concept note + its live panel.**
Every other `.demo.yaml` follows the identical shape — only the nickname and topic id
change.

### 4b. A glossary file — `glossaries/pointers.glossary.yaml`

```yaml
title: "Vocabulary — Pointers & References"
terms:
  - { term: "address-of (&)", def: "operator that yields the memory address of an object" }
  - { term: "dereference (*)", def: "operator that accesses the object a pointer points to" }
  - { term: "pointee",         def: "the object a pointer refers to" }
  # … more term/def pairs …
```

That's the *entire* format: a `title` and a list of `{term, def}` pairs. Nothing is
compiled; it's pure text. It's deliberately dead-simple so a future tool could even
generate one automatically. One glossary can be reused by many pages.

### 4c. A layout file — `layouts/pointers_refs.rail.yaml`

This is the page. It doesn't contain content itself — it **references** demos and a
glossary and says how to arrange them.

```yaml
title: "Pointers & References — Lab 1"   # ① the page's <title> and top heading
style: left_rail                         # ② navigation style (see table below)
header:                                  # ③ shown ONCE at the top of the page
  - color_legend: { id: legend }
  - glossary: { id: g-ptr, source: ../glossaries/pointers.glossary.yaml }
demos:                                   # ④ which demos appear, in this order
  - ../demos/basic_ptr.demo.yaml
  - ../demos/const_taxonomy.demo.yaml
  - ../demos/ref_must_bind.demo.yaml
  - ../demos/ref_no_null.demo.yaml
  - ../demos/ref_rebind_illusion.demo.yaml
  - ../demos/ref_const.demo.yaml
  - ../demos/null_deref.demo.yaml
  - ../demos/dangling_ptr.demo.yaml
```

1. **`title:`** — the page title.
2. **`style:`** — how the reader moves between demos. Only this differs between the two
   page files we ship:

| `style:` | What the reader sees |
|----------|----------------------|
| `left_rail` | A vertical list of demo names on the left; click one to show it on the right. |
| `top_tabs`  | A row of tabs across the top; click a tab to show that demo. |
| `stacked`   | No navigation — every demo stacked down one long page. |

3. **`header:`** — blocks rendered **once**, above all the demos. Here: a color legend
   and the shared glossary (pulled in from the glossary file via `source:`).
4. **`demos:`** — the list of demo files to include, in display order. The paths start
   with `../` because the layout file sits in `layouts/`, and the demos sit one level
   up in `demos/`.

**The key insight:** `pointers_refs.tabs.yaml` is *byte-for-byte identical* to the rail
file except one line — `style: top_tabs` instead of `style: left_rail`. That's the whole
payoff: **a completely different page navigation is a one-word change, zero Python.**

### 4d. Worked example: when a demo's output isn't obvious (a *cases*-topic)

Most demos are like `basic_ptr`: the panel shows a few simple tabs (`int`/`double`/`float`).
But `const_taxonomy.demo.yaml` looks *identical in shape* yet renders something far richer —
because the richness lives in the **topic** (`topics.py`), never in the demo file:

```yaml
title: "const Taxonomy"
bake: { ct: const_taxonomy }
blocks:
  - callout_note: { id: ct-note, label: Concept, text: "${ct.explanation}" }
  - topic: { id: ct, source: ct }
```

The `const_taxonomy` topic multiplies **two things** together:

- a **dropdown** with 4 options → 4 *variants* (the four declaration types), and
- a **`cases:` list** with 2 entries → 2 *sub-cases* (two operations to attempt).

So baking runs **4 × 2 = 8 independent `g++` compilations**. The topic's code template is
filled in twice per type — `<<decl>>` comes from the dropdown, `<<op>>` from each case:

```
    <<decl>>      ← e.g. "const int* ptr = &val;"   (from the dropdown)
    <<op>>        ← case 0: *ptr = 99;   case 1: ptr = &other;   (from cases:)
```

The panel nests: **outer tabs = the 4 types; inside each tab, 2 stacked sub-cases**, each
with its own code + a *real* compile verdict (a ✗ shows the genuine red-bordered g++ error):

```
[ int* ] [ const int* ] [ int* const ] [ const int* const ]   ← 4 variant tabs
   ▸ Write through pointer:  *ptr = 99;      ✓ / ✗ error box
   ▸ Rebind pointer:         ptr = &other;   ✓ / ✗ error box
```

The 8 compilations produce the const-correctness truth table — proven by the compiler,
not asserted:

| declaration | `*ptr = 99` (write) | `ptr = &other` (rebind) |
|---|:---:|:---:|
| `int*` — both mutable | ✓ | ✓ |
| `const int*` — pointee const | ✗ *read-only* | ✓ |
| `int* const` — pointer const | ✓ | ✗ *read-only* |
| `const int* const` — both const | ✗ | ✗ |

**The lesson:** a demo file's job is only to *pick a topic and lay out its note + panel*.
Whether that topic yields three simple tabs or an 8-compilation error matrix is decided in
`topics.py` — the one place C++ content lives — so the YAML stays trivial either way.

---

## 5. How the files point at each other

A layout is the root. Follow the arrows:

```
   layouts/pointers_refs.rail.yaml
   ┌───────────────────────────────────────────┐
   │ style: left_rail                           │
   │ header:                                    │
   │   - color_legend                           │
   │   - glossary  ── source: ──────────────────┼──▶ glossaries/pointers.glossary.yaml
   │ demos:                                     │        (title + term/def pairs)
   │   - ../demos/basic_ptr.demo.yaml ──────────┼──▶ demos/basic_ptr.demo.yaml
   │   - ../demos/const_taxonomy.demo.yaml ─────┼──▶      │ bake: { bp: basic_ptr }
   │   - … 6 more demos …                       │        │        └──── nickname → topic id
   └───────────────────────────────────────────┘        ▼
                                                   topics.py
                                                   ┌─────────────────────────┐
                                                   │ basic_ptr = TopicTemplate│  ← the real C++
                                                   │   (source code, variants,│     source + its
                                                   │    explanation text)     │     explanation
                                                   └─────────────────────────┘
```

Three hops: **layout → demo → topic (real C++)**, plus **layout → glossary (text)**.
The `${bp.explanation}` reference inside a demo is a *fourth* kind of link: it pulls a
piece of the baked topic data into the text of a block.

### What `${…}` means

`${nickname.field}` = "substitute the value of `field` from the baked topic you nicknamed
`nickname`." So in `basic_ptr.demo.yaml`, `bake: { bp: basic_ptr }` compiles the topic and
makes fields available under `bp`, and `"${bp.explanation}"` drops that topic's explanation
sentence into the concept note. You're wiring the compiled result into your prose without
copy-pasting it.

---

## 6. What actually happens when you build (bake, then render)

One command builds a page:

```bash
python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml
# → Wrote .../dist/pointers_refs.rail/pointers_refs.rail.html
```

Under the hood it runs in **two phases**:

```
  ┌─ PHASE 1: BAKE (the slow part — runs the C++ compiler) ─────────────────┐
  │  For every demo the layout lists:                                       │
  │    read its `bake:` map  →  find each topic in topics.py  →             │
  │    run g++ to COMPILE and RUN the real C++  →                           │
  │    capture: the highlighted code, the ✓/✗ compile result, the real      │
  │    program output, the memory-diagram numbers.                          │
  │  Result: a big data bundle keyed by your nicknames (bp, ct, …).         │
  └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─ PHASE 2: RENDER (fast — pure text assembly, no compiler) ──────────────┐
  │  Render the `header:` once (legend + glossary).                         │
  │  For each demo: walk its `blocks:`, resolve every ${…} reference        │
  │    against the baked bundle, turn each block into HTML.                  │
  │  Arrange the demo panels using the chosen `style:` navigation.          │
  │  Wrap it all in one accessible, self-contained HTML page.               │
  └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                     dist/<name>/<name>.html   ← open this
```

Why split it this way? Phase 2 is pure text with no compiler, so the engine's behaviour
can be tested with fake baked data — fast and without needing g++. Phase 1 is the only
part that touches the compiler, which is also why building a page takes a few seconds
(it's really running `g++` several times).

The engine picks bake-vs-render automatically: a spec file with a `demos:` list is a
layout (build the whole page); a spec without one is a single standalone topic page.

---

## 7. "I want to…" recipes

**…fix a typo in a concept note or glossary term.**
Edit the `.demo.yaml` or `.glossary.yaml` text, rebuild the layout. Done — no Python.

**…add an existing topic as a new demo on the page.**
1. Create `demos/<topic>.demo.yaml`, copying `basic_ptr.demo.yaml` and changing the three
   names: `title:`, the `bake:` nickname, and the topic id (must match an id in
   `topics.py`), plus the `id:`/`source:` in the blocks.
2. Add one line to the layout's `demos:` list: `- ../demos/<topic>.demo.yaml`.
3. Rebuild. It appears in the navigation.

**…make the same lab in a different navigation style.**
Copy the layout file, change one line — `style: left_rail` → `top_tabs` (or `stacked`) —
and rebuild. (This is exactly how `.tabs.yaml` was made from `.rail.yaml`.) A typo in
`style:` gives you a clear error listing the valid choices.

**…reword or reorder the vocabulary.**
Edit `glossaries/pointers.glossary.yaml` (add/remove/reorder `{term, def}` lines). Every
page that references it updates on the next build.

**…add a brand-new C++ topic that doesn't exist yet.**
*This* is the one case that needs Python: add a `TopicTemplate` to `topics.py` (the C++
source, its variants, its explanation), register its id, then author a `.demo.yaml` for
it as above. From then on it's YAML again.

---

## 8. Vocabulary quick-reference

| Word | Means |
|------|-------|
| **topic** | One C++ concept with real source code, defined in `topics.py`. The compilable unit. |
| **demo** | One whole topic packaged as a page section (concept note + interactive panel). A `.demo.yaml`. One nav entry. |
| **variant** | A switchable version *inside* one demo's panel (e.g. `int`/`double`/`float` tabs). Comes from the topic. |
| **glossary** | A reusable term/definition box. A `.glossary.yaml`. |
| **layout** | A whole page: chosen demos + a header + a navigation `style:`. A `.rail.yaml`/`.tabs.yaml`. The thing you build. |
| **block** | One item in a demo's or header's list — `callout_note`, `topic`, `color_legend`, `glossary`, `heading`, `html`, … |
| **header** | Blocks a layout shows once at the top (legend + glossary), above all demos. |
| **bake** | Phase 1: run g++ on the referenced topics and capture real output. |
| **render** | Phase 2: turn blocks (with `${…}` filled in) into the final HTML. |
| **`${nick.field}`** | Insert `field` from the baked topic nicknamed `nick` into this text. |

---

*Where the machine lives (rarely edited): the engine is `cpp_ptr_lab/yaml_engine/render_page.py`
and the component library is `cpp_ptr_lab/components.py`. You should not need either to add
or change lab content — that's the whole point of this design.*
