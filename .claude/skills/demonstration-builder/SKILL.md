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

# demonstration-builder

Interactive workflow for authoring a new cpp_labs teaching page (a **demonstration**).
Read this once to get the workflow; open the `reference/` docs for detail as you need it.

---

## What a demonstration is

Locked vocabulary (use these terms consistently):

| Term | Meaning |
|---|---|
| **Demonstration** | One HTML page = one subject (e.g. *Operator Overloading*). The unit of nav. |
| **Example** | One rail entry inside a demonstration (*Basic Vec2*, *Commutative multiply*). |
| **Gotcha** | An example whose point is a deliberate failure (*Null Deref*, *Double Free*). |
| **Concept** | The prose imparted — one `concept:` field per example, one per demonstration. |

Two-layer content model: a **Topic YAML** (`*.topic.yaml`) holds the C++ source and
compilation metadata for each example; a **Demo/Layout YAML** wires topics into nav
and sets per-page structure. See `reference/PATTERN.md` for the full anatomy of both
layers and how they compose.

---

## The interactive workflow

Work through these six steps in order. Offer suggestions at each gate — the author
should never face a blank page.

### Step 1 — Elicit

Ask the author for:
- Subject name and a one-line goal (what should a student *understand* after reading this page?)
- The C++ concepts to cover (e.g. `std::variant`, move semantics, RAII)
- Any example code they already have — invite a paste
- Any images or diagrams they want to incorporate

If they only give a subject name, propose a goal and concept list yourself and confirm.

### Step 2 — Shape the examples

Propose 2–4 named examples + at least one gotcha. For each, sketch one sentence on
what it demonstrates and why it earns its own rail entry. Offer suggestions when the
author is unsure — a good gotcha shows what happens when the rule is violated.

Confirm the list before generating any files.

### Step 3 — Diagram triage

Read `reference/DIAGRAMS.md` before deciding. Ask: does a diagram clarify the memory
model, object graph, or control flow better than prose or code alone? If yes, propose
the diagram type and its content. Offer the zero-JS interaction layer (stepper /
enlarge / detail-reveal) only when it adds genuine pedagogical value — it is always
optional. Set `diagram: false` on examples where prose + code is clearer.

### Step 4 — Generate the files

Copy the `templates/` skeletons and fill them:

```
cpp_labs/<subject>/topics/          # one *.topic.yaml per example
cpp_labs/<subject>/demos/           # one *.demo.yaml (wires topics → page)
cpp_labs/<subject>/layouts/         # one *.rail.yaml (sets nav style + demo list)
cpp_labs/tests/test_<subject>.py    # copy templates/test_subject.py, update paths
```

Apply the C++ style guardrails (see **Guardrails** below) while filling placeholders.
The worked exemplar at `cpp_labs/template_subject/` shows a complete 2-example +
1-gotcha set with `diagram: false` — copy its shape.

### Step 5 — Build and verify

Follow `reference/CHECKLIST.md` for the exact commands. The key loop is:

```bash
python -m cpp_labs.build_html <layout-yaml>   # bake to dist_labs/
pytest cpp_labs/tests/test_<subject>.py -q    # green = content correct
```

Report the REAL baked stdout/stderr — do not summarise or paraphrase compiler output.

### Step 6 — Iterate to green

Fix any compile errors, YAML validation failures, or test failures. Re-run the checklist
until all tests pass and the baked page renders correctly in a browser. Then hand off to
the author for a content review.

---

## The worked exemplar

`cpp_labs/template_subject/` is a complete worked example (2 examples + 1 gotcha,
`diagram: false`). Open it and copy its shape when starting a new subject. The
`templates/` directory contains the raw copy-me skeletons with `TODO` placeholders.

---

## Guardrails

These rules exist for good reasons — don't skip them.

| Rule | Why |
|---|---|
| Use `class`, not `struct` | `class` defaults to private — models encapsulation; `struct` lets sloppy direct-member access compile "by accident", hiding missing `friend`/accessor lessons. |
| Comments on their own line above the code they describe | Trailing end-of-line comments are easy to miss; above-the-line comments read as natural prose. Tests assert byte-identical stdout — trailing comments can shift column widths. |
| Break long `<<` chains at `<<` boundaries, aligned | Long stream statements on one line are unreadable at course font sizes. Rule: break when 3+ `<<` or >~55 chars; align continuation lines under the first `<<`. |
| Never commit `dist_labs/` | It is gitignored — the baked HTML is always regenerated from YAML. Committing it creates merge conflicts and bloats the repo. |
| Do NOT modify engine code | v1 of this skill works purely with YAML content. Engine changes (`cpp_labs/` Python) require their own TDD cycle and are out of scope here. |

---

## Reference map

| Doc | What it covers |
|---|---|
| `reference/PATTERN.md` | Full YAML anatomy of topic/demo/layout files + test families |
| `reference/DIAGRAMS.md` | Diagram triage guide + zero-JS interaction layer options |
| `reference/CHECKLIST.md` | Build/verify commands + ordered pre-commit checklist |
| `templates/` | Copy-me skeletons (`topic.topic.yaml`, `demo.demo.yaml`, `layout.rail.yaml`, `test_subject.py`) |
| `cpp_labs/template_subject/` | Worked exemplar (2 examples + 1 gotcha, diagram:false) |
