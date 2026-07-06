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

## Self-contained engine

This skill **carries its own copy** of the baking engine under `engine/` (the shared
`cpp_labs` Python package + `build_labs.sh` + `requirements.txt`). It does not depend
on any pre-existing `cpp_labs/` in the project, so it works in **any** folder.

The engine discovers subjects relative to its own physical location and `build_labs.sh`
runs from the project root, so the engine must live as a `cpp_labs/` package **at the
target project root**. Step 0 installs it there.

Requirements: Python 3.10+, a C++ compiler on `PATH` (`g++`/`clang++`), and PyYAML
(`pip install -r engine/requirements.txt`).

## The interactive workflow

Work through these steps in order. Offer suggestions at each gate — the author
should never face a blank page.

### Step 0 — Install the engine (once per project)

If the target project has no `cpp_labs/` engine yet (no `build_labs.sh` at its root),
install the bundled engine into it. Safe to re-run — it merges engine files and never
touches existing subject folders:

```bash
<skill-dir>/scripts/install_engine.sh          # installs into $PWD (the project root)
```

`<skill-dir>` is wherever this skill lives — e.g. `.claude/skills/demonstration-builder`
(project-local) or `~/.claude/skills/demonstration-builder` (global). All scripts below
target the **current directory** as the project root (override with a trailing path arg
or `PROJECT_ROOT=`), so run them from the project you are authoring in.

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

Start from a consistent, buildable skeleton — don't hand-create the paths (that is
where id/filename references drift out of sync):

```bash
<skill-dir>/scripts/scaffold_subject.sh <subject>    # writes into $PWD/cpp_labs/<subject>
```

This creates the package below with ONE working example (`<subject>_ex1`, printing
`x = 42`) that builds and tests green immediately — a known-good baseline to grow from:

```
cpp_labs/<subject>/topics/                       # one *.topic.yaml per example
cpp_labs/<subject>/demos/                         # one *.demo.yaml (wires topics → page)
cpp_labs/<subject>/layouts/<subject>.rail.yaml    # nav style + demo list
cpp_labs/<subject>/tests/test_<subject>.py        # exact-baked-stdout assertions
```

Then grow it: duplicate the example topic/demo per example, add at least one gotcha,
and list every demo in the layout. Apply the C++ style guardrails (see **Guardrails**
below) while filling placeholders. The worked exemplar at `cpp_labs/template_subject/`
shows a complete 2-example + 1-gotcha set with `diagram: false` — copy its shape.

### Step 5 — Build and verify

Follow `reference/CHECKLIST.md` for the exact commands. The key loop is:

```bash
./build_labs.sh <subject>                              # bake to dist_labs/ (real g++)
pytest cpp_labs/<subject>/tests/test_<subject>.py -q   # green = content correct
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
`templates/` directory contains the raw copy-me skeletons with fill-in markers
(`my_topic`, `Human name`, `my_subject`) to replace.

---

## Guardrails

These rules exist for good reasons — don't skip them.

| Rule | Why |
|---|---|
| Use `class`, not `struct` | `class` defaults to private — models encapsulation; `struct` lets sloppy direct-member access compile "by accident", hiding missing `friend`/accessor lessons. |
| Comments on their own line above the code they describe | Trailing end-of-line comments are easy to miss; above-the-line comments read as natural prose. Tests assert byte-identical stdout — trailing comments can shift column widths. |
| Break long `<<` chains at `<<` boundaries, aligned | Long stream statements on one line are unreadable at course font sizes. Rule: break when 3+ `<<` or >~55 chars; align continuation lines under the first `<<`. |
| Never commit `dist_labs/` | It is gitignored — the baked HTML is always regenerated from YAML. Committing it creates merge conflicts and bloats the repo. |
| Do NOT modify engine code | Authoring is purely YAML content. The bundled `engine/cpp_labs/` Python is a vendored copy — editing it here diverges from upstream. Engine changes belong in the source repo with their own TDD cycle. |

---

## Reference map

| Doc | What it covers |
|---|---|
| `INSTALL.md` | Plain-language setup guide (prerequisites, install, first build) |
| `reference/PATTERN.md` | Full YAML anatomy of topic/demo/layout files + test families |
| `reference/DIAGRAMS.md` | Diagram triage guide + zero-JS interaction layer options |
| `reference/CHECKLIST.md` | Build/verify commands + ordered pre-commit checklist |
| `engine/` | Vendored baking engine: `cpp_labs/` package + `build_labs.sh` + `requirements.txt` |
| `scripts/install_engine.sh` | Install the bundled engine into a target project (Step 0) |
| `scripts/sync_engine.sh` | Maintainer-only: re-vendor `engine/` from a live source engine |
| `scripts/scaffold_subject.sh` | Create a consistent, buildable `<subject>` skeleton to grow from |
| `templates/` | Copy-me skeletons (`topic.topic.yaml`, `demo.demo.yaml`, `layout.rail.yaml`, `test_subject.py`) |
| `cpp_labs/template_subject/` | Worked exemplar (2 examples + 1 gotcha, diagram:false) — in the source repo |
