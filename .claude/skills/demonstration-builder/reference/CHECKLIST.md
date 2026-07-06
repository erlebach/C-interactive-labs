# Build & Verify Checklist

Distilled from `cpp_labs/SKILL_PREPARATION.md` §11–§12.

---

## Build and verify commands

```bash
# Rebuild every page (auto-discovers layouts/*.yaml and *.page.yaml)
./build_labs.sh

# Build one subject only
./build_labs.sh <subject>

# Build a single layout or page by hand
python -m cpp_labs.yaml_engine.render_page \
    cpp_labs/<subject>/layouts/<name>.rail.yaml dist_labs

# Run one subject's tests (auto-skips if g++ is absent; full suite ~3-4 min)
pytest cpp_labs/<subject>/tests/ -q

# Regenerate the block catalog — ONLY needed when a components.py signature changes
python -m cpp_labs.yaml_engine.interface_catalog
# writes usage/INTERFACE_ELEMENTS.md; run test_interface_catalog to confirm no drift

# Serve for a visual check (file:// is blocked for Playwright)
python3 -m http.server -d dist_labs 8000
```

**`dist_labs/` is gitignored.** HTML output is a build artifact. Regenerate from YAML;
never commit built HTML.

---

## A. Add ONE new example to an existing subject

1. Create `cpp_labs/<subject>/topics/<new_id>.topic.yaml` with the five required fields:
   `id`, `name`, `template`, `explanation`, `group`. Set `target_var` and include
   `<<HARNESS>>` if you want the raw-bytes hex grid.

2. Choose the interaction pattern:
   - **Variants** → a `dropdown` control, with `value_map` for whole-body swaps.
   - **Correct/Mistake or matrix** → `cases:` with `subs` filling `<<…>>` placeholders.

3. Diagram decision (see `reference/DIAGRAMS.md`):
   - A built-in renderer fits? emit a `PTRDATA:` line matching one of the six `type=`
     memory renderers or the stackframe family.
   - No built-in renderer? set `diagram: false` on the `topic` block and pass `concept:`
     to fill the right column with prose.

4. Runtime-fault gotcha? Add `sanitize: true` to the topic YAML. Prefer heap-based
   faults (double-free, use-after-move) — ASan catches these reliably. Stack-use-after-
   return requires an `ASAN_OPTIONS` env var not currently set.

5. Write C++ in locked style (`class` not `struct`; comments on own line above code;
   break long `<<` chains aligned).

6. Wire into the page:
   - **Layout subject** → add `demos/<new_id>.demo.yaml` (`bake` + `concept` + `topic`)
     and add its path to `demos:` in the layout YAML.
   - **Flat-page subject** → add the topic id to `bake:` and a `topic:` block in the
     page YAML (plus a `heading:` and `concept:` if needed).

7. Extend `tests/`: assert exact baked stdout, Correct/Mistake labels, diagram presence
   or absence, and DOM id uniqueness.

8. Build and test:
   ```bash
   ./build_labs.sh <subject>
   pytest cpp_labs/<subject>/tests/ -q
   ```

---

## B. Create a whole new subject from scratch (pure YAML — no engine code)

1. Create the folder structure:
   ```bash
   mkdir -p cpp_labs/<subject>/topics \
             cpp_labs/<subject>/demos \
             cpp_labs/<subject>/layouts \
             cpp_labs/<subject>/glossaries \
             cpp_labs/<subject>/tests
   touch cpp_labs/<subject>/__init__.py
   ```
   `discover_topics` auto-registers every id — no engine code change required.

2. Author `topics/<id>.topic.yaml` for each example (see `PATTERN.md §2`).

3. Write the page spec:
   - **Flat page**: create `<subject>.page.yaml` — copy `function_args` or `basic_ptr`
     as a starting point.
   - **Layout**: create `layouts/<subject>.rail.yaml` (`style: left_rail`, optional
     `header:`/`sidebar:`, `demos:` list → tiny `demos/*.demo.yaml`; optional
     `glossaries/*.glossary.yaml`).
   Alternatively, copy from `cpp_labs/template_subject/` (the worked exemplar).

4. For every `topic` block with no memory diagram, set `diagram: false` and pass the
   concept string as `concept:` on the block (fills the right column with prose).

5. Add `tests/test_<subject>.py` covering the test families from `PATTERN.md §10`.

6. Build and verify:
   ```bash
   ./build_labs.sh                   # auto-discovers the new spec
   # confirm dist_labs/<stem>/<stem>.html was created
   pytest cpp_labs/<subject>/tests/ -q
   ```
   Regenerate the block catalog only if you introduced a new block type usage:
   ```bash
   python -m cpp_labs.yaml_engine.interface_catalog
   ```

---

## Reminder: what triggers a catalog regeneration

Run `python -m cpp_labs.yaml_engine.interface_catalog` **only if** you changed a
function signature in `cpp_labs/components.py` that the catalog introspects. Adding
pure content (new YAML, new `controls:`, new `cases:`) never requires it.

The drift-guard test `test_interface_catalog` will fail if the catalog is stale — that
is the signal to run the regen command.
