# stackframes UX Improvements — Design Spec

**Date:** 2026-07-05
**Branch:** `feat/stackframes-ux`
**Status:** Approved (design), pending implementation plan.

## Motivation

Three improvements requested after reviewing the shipped `stackframes` demonstration
(`dist_labs/stackframes.rail/`):

1. **Bug:** "Show full frame anatomy" only displays `main()`, not all frames live at the
   selected step.
2. The Process Memory Map uses jargon (`text`, `data`, `bss`, `heap`, `stack`) with no
   on-page definitions.
3. The stack-frame diagram renders too small in the narrow (1/4-width) diagram column.

All three preserve the project's **zero-JS / WCAG-AA North Star** (one accepted trade-off in #3:
no ESC-to-close). The six existing pointer renderers and all current tests must stay green.

---

## Item 1 — Step-synced frame anatomy (bug fix)

### Root cause
In `components._demo_variant_body` (the `len(frame_steps) > 1` branch), the anatomy disclosure is
built with `frames_anatomy_details(f"{pid}-fa", pd if pd else frame_steps[-1])`. `pd`
(`v["ptrdata"]`) is the **first** `PTRDATA` snapshot — step 1, when only `main()` is live — so the
anatomy always shows just `main()`. The `<details>` also lives *outside* the `stepped_frames`
container, so its content cannot be driven by the step radios.

### Design
Fold the anatomy into `stepped_frames` so it lives inside the same `#{p}` container as the step
radios, and render **one anatomy view per step**, gated by the same radios.

- `stepped_frames(comp_id, steps, *, with_anatomy: bool = False)`:
  - When `with_anatomy`, after the `.sf-views` block, emit a native `<details>`
    ("Show full frame anatomy") whose body holds one `_svg_frames_anatomy(steps[i], …)` per step
    inside `.sf-an{i}` divs.
  - Add CSS mirroring the existing view gating:
    `#{p} #{p}-s{i}:checked ~ .sf-anwrap .sf-an{i} {{ display:block }}` (all `.sf-an` default
    `display:none`). Because the `<details>` (`.sf-anwrap`) is a sibling of the radio `<input>`s,
    the general-sibling combinator reaches it.
  - Each step's anatomy shows exactly the frames live at that step (`steps[i]["live"]`), no ghost
    rows. The default-checked step is the deepest (existing behavior), so opening the disclosure
    shows the full stack. The final unwound step (empty `live`) renders an empty anatomy (acceptable).
- `_demo_variant_body`'s stepped branch calls `stepped_frames(..., with_anatomy=True)` and **no
  longer** appends a separate `frames_anatomy_details(...)`.
- The single-snapshot `elif ptype == "frames"` path is unchanged (keeps calling
  `frames_anatomy_details(f"{pid}-fa", pd)` — correct there, since `pd` is the only snapshot).
- `frames_anatomy_details` is retained for that single-snapshot path.

### Verification
- Unit: `stepped_frames(..., with_anatomy=True)` emits one `.sf-an{i}` per step and the gating CSS;
  the deepest step's anatomy contains every frame name (`main`, all `countdown`, etc.).
- Subject test (`test_stackframes.py`): the built rail's recursion demo anatomy contains
  `countdown()` (previously it did not — it only had `main()`). Keep `Show full frame anatomy`
  present and `svg==role` invariant.

---

## Item 2 — General inline-glossary chip

### Design
A reusable per-example glossary toggle, matching the "Concept" chip exactly.

- **New component** `glossary_note(comp_id, terms, *, label: str = "Memory glossary",
  open_: bool = False)`:
  - Same `<details class="concept">` chip structure as `concept_note` (button-like summary with the
    rotating caret), but the body is the `<dl>` produced by the existing `glossary` term renderer
    (reuse `_prose_box` + the `<dt>/<dd>` markup).
  - `terms` is a sequence of `(term, definition)` pairs.
- **New block type** `glossary_note` in `render_page._BUILDERS` (a sibling of `concept`):
  `_build_glossary_note(args, data)` → `C.glossary_note(args["id"], args["terms"], label=…, open_=…)`.
  Terms are authored inline in the demo YAML as a list of `{term, def}` maps (resolved like other
  block args). This is a **general** mechanism any demo can use.
- **Chip-row layout:** a small CSS rule so consecutive chips (`concept` + `glossary_note`) sit on
  **one row** rather than stacking. Approach: mark both chip `<details>` with a shared class (e.g.
  `class="concept chip-inline"`) and add `.chip-inline {{ display:inline-block; vertical-align:top;
  margin-right:.6rem }}` to `_CSS`. Each opens its own panel below its own chip. (If inline-block
  proves visually awkward when open, fall back to a flex wrapper — decided during implementation;
  the authored YAML is unaffected.)

### Authoring (memory-map demo)
`cpp_labs/stackframes/demos/sf_memmap.demo.yaml` gains a `glossary_note` block placed with the
`concept` block, e.g.:
```yaml
blocks:
  - concept:       { id: mm-note, text: "${mm.explanation}" }
  - glossary_note: { id: mm-gloss, label: "Memory glossary", terms: [
      { term: "text",  def: "The machine code (instructions); read-only, lowest addresses." },
      { term: "data",  def: "Initialized globals/statics." },
      { term: "bss",   def: "Uninitialized globals/statics (zero-filled at start)." },
      { term: "heap",  def: "Dynamic allocations (new/malloc); grows upward." },
      { term: "stack", def: "Call frames: parameters and locals; grows downward." },
      { term: "segment", def: "A named region of the process's address space." } ] }
  - topic:         { id: mm, source: mm }
```

### Verification
- Unit: `glossary_note` returns a `<details>` chip whose summary shows the label and whose body
  contains each term and definition.
- Subject test: the memmap demo HTML contains `Memory glossary` and the `bss`/`heap` definitions.

---

## Item 3 — CSS lightbox + bigger default (zero-JS)

### 3a. Bigger default
`code_diagram_panel(comp_id, code_html, diagram_html, *, ratio: tuple[int, int] = (3, 1))`.
`_demo_variant_body` passes `ratio=(2, 1)` for `frames`/`memmap` diagrams (diagram column 25% → 33%);
all other callers keep the current `(3, 1)`. Pointer subjects are unaffected.

### 3b. Lightbox
**New component** `zoomable(comp_id, inner_html, *, label: str = "⤢ Enlarge")` wraps any HTML in a
zero-JS click-to-fullscreen container **without duplicating the inner DOM** (so the WCAG
`svg==role` invariant is preserved and stepper state survives):

```
<div id="{z}" class="zoomwrap"><style>…</style>
  <input type="checkbox" id="{z}-cb" class="zoom-cb">      <!-- visually hidden, still focusable -->
  <label for="{z}-cb" class="zoom-open">⤢ Enlarge</label>
  <div class="zoom-body">
    {inner_html}
    <label for="{z}-cb" class="zoom-close" aria-hidden="true">✕</label>
    <label for="{z}-cb" class="zoom-backdrop"></label>
  </div>
</div>
```

CSS:
- `.zoom-cb` is hidden with the clip pattern (NOT `display:none`) so it stays keyboard-focusable;
  `.zoom-open` is the visible affordance.
- `#{z}-cb:checked ~ .zoom-body` (or `.zoom-body` when checked) → `position:fixed; inset:0;
  z-index:1000; background:#fff; overflow:auto; padding:2rem`. The enlarged SVG scales to the wide
  overlay, so it renders large.
- `.zoom-close` (fixed top-right) and `.zoom-backdrop` (full-area, behind content) are shown only
  when checked; both toggle the same checkbox off.

**Applied in `_demo_variant_body`:** the assembled `diagram_html` (stepper + anatomy, or the
memmap diagram) is wrapped in `zoomable(...)` before being handed to `code_diagram_panel`. The
"⤢ Enlarge" chip is a **separate** control (not the diagram body) to avoid wrapping a `<label>`
around the stepper's own radios/labels (which would fire the enlarge toggle on step clicks).

**Accessibility:** the checkbox is focusable and operable by keyboard (Space toggles open/closed);
✕ and backdrop provide pointer close. No ESC (accepted trade-off). The diagram SVGs keep their
existing `role="img"` + `aria-labelledby` title/desc.

### Verification
- Unit: `zoomable` returns a container with exactly one checkbox, a `zoom-open` label, and the
  inner HTML appearing once (no duplication); `code_diagram_panel(..., ratio=(2,1))` emits
  `2fr` / `1fr` tracks.
- Subject test: the stackframes rail contains `⤢ Enlarge` / `zoom-body`, `svg==role` counts stay
  equal, and DOM ids stay unique.

---

## Engine inventory (files touched)

- `cpp_labs/components.py` — modify `stepped_frames` (add `with_anatomy`), `code_diagram_panel`
  (add `ratio`), `_demo_variant_body` (rewire: `with_anatomy=True`, `zoomable` wrap, ratio);
  add `glossary_note`, `zoomable`; small `_CSS` chip-row rule.
- `cpp_labs/yaml_engine/render_page.py` — add `_build_glossary_note` + register `glossary_note`
  in `_BUILDERS`.
- `cpp_labs/stackframes/demos/sf_memmap.demo.yaml` — add the `glossary_note` block.
- Tests: extend `cpp_labs/tests/test_stepped_frames.py` (anatomy-per-step, zoomable) + new
  `cpp_labs/tests/test_glossary_note.py`; extend `cpp_labs/stackframes/tests/test_stackframes.py`
  (memory-glossary terms, step-synced anatomy shows `countdown()`, `⤢ Enlarge` present).
- If the interface catalog introspects `glossary_note`/`zoomable` (they are internal helpers, not
  `_DISPATCH` block keywords — `glossary_note` is a `_BUILDERS` entry), regenerate
  `usage/INTERFACE_ELEMENTS.md` and rely on the freshness test.

## Non-goals / YAGNI

- No ESC-to-close (would require JS).
- No draggable partition (janky in pure CSS; deferred).
- No change to the six pointer renderers or their pages.
- The lightbox is applied to `frames`/`memmap` diagrams only (where smallness is the complaint),
  not to pointer memory diagrams.
