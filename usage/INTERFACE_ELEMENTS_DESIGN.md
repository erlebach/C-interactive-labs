# Interface Elements — the catalog, and where it points

This is the plain-language companion to `usage/INTERFACE_ELEMENTS.md`. That file is the **catalog** (the index of every interface element you can name in YAML); this file explains what it is, how it stays correct, and the future direction it points at.

## What an "interface element" is

An interface element is one reusable piece of the page — a callout, a glossary, a code+output panel, a fold-away concept note, a tab strip. Every element is one function in **`cpp_labs/components.py`**, and that single file is where all the HTML, CSS, and ADA/WCAG-AA compliance lives. Authoring a new subject (topics, demos, glossaries, layouts) is pure YAML and never touches that file — the elements are the fixed vocabulary the YAML draws on.

So the "one file with all the interface elements" is already real: it is `components.py`. What was missing was a way to **see** what is in it without reading the source.

## Three tiers of element

1. **Author-usable now** — the ~19 keywords you may write in YAML (`callout_note`, `glossary`, `topic`, `concept`, …). These are the catalog.
2. **Internal chrome** — real elements (`page_shell`, `nav_shell`, `left_rail_layout`, `demo_panel`) that the engine assembles for you. They exist but are not part of the authoring vocabulary.
3. **Doesn't exist yet** — anything an example needs that is not a function in `components.py`. The engine catches this: naming an unknown element is a hard build error (`unknown block type`), never a silent skip.

## The catalog (option 1): an index that cannot drift

`usage/INTERFACE_ELEMENTS.md` is **generated**, not hand-written. A small generator (`cpp_labs/yaml_engine/interface_catalog.py`) reads the engine's dispatch tables and the components' signatures and docstrings, and writes the Markdown. Regenerate it with:

```
python -m cpp_labs.yaml_engine.interface_catalog
```

You never edit the catalog by hand. When you add an element you edit the **code**; re-running the generator re-derives the catalog. A drift-guard test (`test_interface_catalog.py`) fails if the committed file is stale or if a dispatched keyword is missing, so the index can never fall out of step with the code.

## Why there is also a "(3)", and how it relates

Option (3) is a possible **future** change: collapse the several small dispatch tables that today live in `render_page.py` into **one declarative in-code list** that the engine reads directly, so adding an element becomes appending a single row. It is not built, and it does **not** replace the catalog — as you put it: **(1) is the index, and (3) is (kind of) where the index points to.** In both worlds the catalog is generated; (3) just makes the thing behind the index a single list instead of four scattered tables, at which point the catalog would generate from that one list.

The key difference is **how many places you touch when you add an element** — and note that in neither case do you ever hand-edit the catalog:

| When you add element X | Today | (1) Generated catalog | (3) Single registry |
|---|---|---|---|
| Write component fn in `components.py` | ✅ | ✅ | ✅ |
| Register in `_DISPATCH` / `_BUILDERS` | ✅ | ✅ | — |
| Maybe a `_PAIR_ARGS` reshape row | ✅ | ✅ | — |
| Maybe a sidebar/header branch | ✅ | ✅ | — |
| Append **one** `Element(...)` row | — | — | ✅ |
| Update the catalog by hand | — | ❌ never (generated) | ❌ never (generated) |
| **Net edits** | 2–4 code | 2–4 code | **1 component + 1 row** |

Put simply: **(1)** lets you *see* every element in one place; **(3)** would let you *define* every element in one place. (1) is done now; (3) is the road it points down, to be taken only once the four-way scatter actually causes friction. See the project memory note (2026-07-04) for the staged migration path that keeps every step green.

## See also

- `usage/INTERFACE_ELEMENTS.md` — the generated catalog itself.
- `usage/YAML_GUIDE.md`, `usage/USAGE.md` — full authoring recipes with worked examples.
