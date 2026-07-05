# Design: `stackframes` demonstration

**Date:** 2026-07-04
**Status:** Approved (brainstorm) — ready for implementation plan
**Author:** brainstormed with user (gordon.erlebach@gmail.com)

A new C++ teaching **demonstration** on the call stack, built as a pure-YAML subject
`cpp_labs/stackframes/` on the **`left_rail`** layout (like `pointers_refs`). It introduces
**two new SVG diagram families** (`type=frames`, `type=memmap`) and one new **zero-JS stepped
diagram** capability (watch frames push on call / pop on return). Everything else is YAML.

Reference authoring model: `cpp_labs/SKILL_PREPARATION.md`. Reference exemplar:
`cpp_labs/pointers_refs/`. Inspiration (not to copy): the three textbook figures the user
supplied — a caller/callee frame diagram, a nested func1/func2/func3 stack, and a process
memory map.

> This design captures what the user *currently* wants. Refinements and additional examples
> are explicitly expected; the two diagram families and the stepper are to be built so new
> examples extend them cleanly (data-over-code North Star).

---

## 1. Goal & scope

Teach how the call stack works, grounded in **real g++ output baked at build time**:

- A function call pushes a **frame**; returning pops it (LIFO).
- A frame holds the function's parameters, return address, saved frame pointer, and **locals**.
- Each slot has a **size in bytes** — `sizeof(T)` for parameters/locals, `sizeof(void*)` (8 on
  the 64-bit build) for the return address and saved frame pointer. These sizes are
  deterministic (baked, and assertable); real frames additionally add alignment padding, shown
  as schematic.
- **Addresses increase upward; the stack grows downward** — opposite directions. Each deeper
  call lives at a *lower* address.
- On return a frame is **destroyed** — anything still pointing into it dangles (the gotcha).
- Where the stack sits in the whole process image (text/data/bss/heap/stack), stack↓ vs heap↑.

**In scope (this session):** 6 rail examples + 2 SVG families + the stepped push/pop diagram.
**Out of scope:** ASan stack-use-after-return run-env plumbing (the gotcha uses a compile-time
warning instead); per-`-std` variant axis; converting existing subjects.

---

## 2. Layout & folder structure

`left_rail` layout, 2/3 code : 1/3 diagram column ratio (`code_diagram_panel` at `2fr:1fr`
for this subject — wider diagram column than pointers' `3fr:1fr`, because frames stack
vertically and want the width).

```
cpp_labs/stackframes/
  __init__.py
  topics/       sf_single_call, sf_nested, sf_locals, sf_recursion,
                sf_dangling_local, sf_memmap   (*.topic.yaml)
  demos/        one *.demo.yaml per topic (bake + concept + topic block)
  layouts/      stackframes.rail.yaml   (style: left_rail, sidebar concept + glossary)
  glossaries/   stackframes.glossary.yaml  (frame, SP, FP, return address, LIFO, dangling…)
  tests/        test_stackframes.py
```

Ids auto-register via `discover_topics` — no engine registration needed for the *subject*.
The only engine code is the two SVG renderers + the stepper (§5).

---

## 3. Example set (rail order: simple → deep → gotcha → capstone)

| # | id | Teaches | Diagram |
|---|----|---------|---------|
| 1 | `sf_single_call` | a call pushes a frame; return pops it | `frames`, static (2) |
| 2 | `sf_nested` | `main → outer → inner`; addresses descend | `frames`, **stepped** |
| 3 | `sf_locals` | locals live inside the frame — **two tabs: without / with locals**, diagram changes live | `frames`, static (2) |
| 4 | `sf_recursion` | each call gets its own frame + own copy of the parameter; LIFO | `frames`, **stepped** |
| 5 | `sf_dangling_local` *(gotcha)* | a frame is destroyed on return → returned ref/ptr dangles | `frames`, static (2) + ghost |
| 6 | `sf_memmap` *(capstone)* | where the stack sits in the process; stack↓ vs heap↑ | `memmap`, static |

C++ sketches (final style per SKILL_PREPARATION §10 — `class` where relevant, comments above,
broken `<<` chains):

- **`sf_single_call`** — `main()` calls `greet()`; a frame tracer (§5.3) prints
  `enter greet` / `leave greet`. Two frames.
- **`sf_nested`** — `main() → outer() → inner()`; tracer prints enter/leave for each and the
  ordering `&inner < &outer < &r → 1`. Stepped diagram shows push ×2, pop ×2.
- **`sf_locals`** — a 2-option control (`locals: none / a few`) rendered as **variant tabs at
  the top**. "none" tab: a leaf that computes inline with no named locals; "a few" tab: same
  leaf with several locals. Diagram shows the locals slot appear and the frame grow.
- **`sf_recursion`** — `countdown(int n)` (or `factorial`); prints `enter n=3 … enter n=1`,
  then `leave n=1 … leave n=3`. Stepped diagram grows to depth N then unwinds.
- **`sf_dangling_local`** — `int& make(){ int local=42; return local; }` used from `main`.
  Surfaces the real g++ **`-Wreturn-local-addr`** warning at build time (see §6). Diagram
  reuses the ghost step ("frame reclaimed on return").
- **`sf_memmap`** — prints the address of a function (text), an initialized global (data), an
  uninitialized global (bss), a `new` allocation (heap), and a local (stack), plus the
  deterministic ordering assertion (§4).

---

## 4. Determinism strategy (the correctness gate)

Tests assert **byte-exact stdout**, but raw addresses vary per run. Therefore:

- **stdout prints only deterministic facts:** enter/leave traces, recursion depth counters,
  ordering booleans computed in-program, e.g.
  `printf("deeper frame is lower? %d\n", (&inner < &outer));  // → 1`
  and for memmap `text < data < bss? …`, `heap < stack? …`; plus a **frame-layout summary**
  of the `sizeof`-derived slot sizes (params/locals/return-addr/saved-FP), which is
  deterministic and therefore assertable.
- **Real per-run addresses ride in `PTRDATA:` lines** and are drawn in the diagram but **never
  asserted** — identical to how `pointers_refs` treats `%p` today.
- The dangling gotcha's evidence is a **compile-time warning string**, which is deterministic.

Verify at implementation time (RED→GREEN, compile before baking assertions) that at the build's
optimization level each deeper frame really is at a lower address (true for straight call chains
and recursion at `-O0`; if a chain is unreliable, assert only the trace, not the ordering).

---

## 5. Diagram families (the only engine code)

Added beside the six pointer renderers in `cpp_labs/html_renderer.py`; registered in
`svg_renderer`'s `type` dispatch. Same visual language: vertical, high-memory-on-top, real
addresses in red, growth arrows, `role="img"` + `title`/`desc` (WCAG 1.1.1).

### 5.1 `type=frames` — stacked frame boxes

Orientation (locked, faithful): high memory on top, `main()` (oldest) on top, each new call a
box **below** it at a lower address, **SP** marker on the bottom-most frame. Dual axis in the
gutter: **addresses increase ↑ (green)** and **stack grows ↓ (orange)** — call out that they
point opposite ways.

- **Default view:** clean — one box per frame, function name + the frame's real local address.
- **`<details>` "Show full frame anatomy":** expands to **all** live frames as a three-column
  table (slot · address · size). Every slot shows its **byte size** (`sizeof` for params/locals,
  `sizeof(void*)`=8 for return addr / saved FP) and **its own address**: the local's row is the
  **real measured address** (red); the params / return-addr / saved-FP rows carry **schematic
  addresses** (grey) computed by stacking the known slot sizes above the measured local, in the
  conventional high→low order (params highest, local lowest near SP). A per-frame schematic total
  is shown. The illustrative slots are marked schematic ("not portably observable in C++"; real
  frames add alignment padding) — only the local's address is measured.

**Static** single-snapshot `PTRDATA` (examples 1, 3, 5):
```
PTRDATA: type=frames ptrbytes=8 live=main:0x7ffe40:r:4,compute:0x7ffe20:t:4,square:0x7ffe00:s:4
```
`live=` is a comma list of `name:addr:localname:localbytes`, outermost→innermost; `ptrbytes=`
is `sizeof(void*)` for the return-address and saved-FP slots. Values have no spaces, so the
existing whitespace/`=` split in `parse_ptrdata` keeps working; `_svg_frames` re-splits on `,`
and `:`. Missing pieces degrade to `"?"` (never raise). Slot byte sizes are also printed to
stdout in a deterministic "frame layout" summary so tests can assert them.

### 5.2 `type=frames` stepped — push/pop over time (examples 2, 4)

The program emits **one `PTRDATA` line per lifecycle event** (each call and each return),
snapshotting the live frames at that moment:
```
PTRDATA: type=frames step=1 ptrbytes=8 live=main:0x7ffe40:r:4
PTRDATA: type=frames step=2 ptrbytes=8 live=main:0x7ffe40:r:4,compute:0x7ffe20:t:4
PTRDATA: type=frames step=3 ptrbytes=8 live=main:0x7ffe40:r:4,compute:0x7ffe20:t:4,square:0x7ffe00:s:4
PTRDATA: type=frames step=4 ptrbytes=8 live=main:0x7ffe40:r:4,compute:0x7ffe20:t:4
PTRDATA: type=frames step=5 ptrbytes=8 live=main:0x7ffe40:r:4
```
Engine changes:
- **Parse all `PTRDATA` lines**, not just the first. Add `parse_ptrdata_all` (or a `frames`
  branch) in `compiler_runner.py`; keep the single-line path for the six pointer types
  untouched (backward compatible).
- **`_svg_frames` renders one SVG per step** (reusing the static layout; popped frames drawn
  ghost/dashed with "frame reclaimed on return").
- **Zero-JS CSS-radio step control** (same pattern as `variant_tabs`): N hidden radios + labels
  ①…N; `#stK:checked ~ .views .vK { display:block }`. Defaults to the deepest step. A new small
  component (e.g. `stepped_frames`) in `components.py`; **if its signature is introspected by
  the interface catalog, regenerate `usage/INTERFACE_ELEMENTS.md`.**

Single-snapshot examples render as a stepper with one step (no step buttons) or the static path.

### 5.3 Frame tracer (reusable C++ authoring snippet)

To emit the trace + snapshots deterministically, templates include a tiny shadow-stack helper:
`frame_enter(name, &local)` pushes to a global vector and prints `enter <name>` +
`PTRDATA: type=frames step=K live=…`; `frame_leave()` pops and prints `leave <name>` + the new
snapshot. Deterministic stdout (names/order); addresses only in `PTRDATA`. This snippet is
authored in YAML (no engine support needed) and reused across the frame examples.

### 5.4 `type=memmap` — process memory map (example 6)

Single `PTRDATA`:
```
PTRDATA: type=memmap regions=text:0x55f180:&main,data:0x5601a4:&g_seed,bss:0x5601c8:&g_count,heap:0x561a20:new_int,stack:0x7ffe40:&local
```
`_svg_memmap` draws five stacked regions (text low → stack high), **heap grows ↑**, **stack
grows ↓** toward each other, one real address per region, region purpose labels
(machine instructions / global-static data / dynamic variables / params-auto variables).

---

## 6. The dangling gotcha without ASan

`sf_dangling_local` returns a reference/pointer to a local. Rather than the deferred
`ASAN_OPTIONS=detect_stack_use_after_return` run-env plumbing (SKILL_PREPARATION §6), rely on
g++'s **`-Wreturn-local-addr`** (on by default) — a deterministic build-time **warning**.
Implementation must confirm how the build surfaces warnings (compiler stderr on an otherwise
successful compile). Options, decided at implementation time:
- surface the warning text in the output console (preferred — a real diagnostic, amber), or
- compile this topic with `-Werror=return-local-addr` so it becomes a red compile-error box via
  the existing `error_kind="compile"` path.

Either way: **no ASan, no run-env change.** Prefer showing the warning (keeps the program
runnable so the stepper's "frame reclaimed" ghost still illustrates the point).

---

## 7. Testing (`tests/test_stackframes.py`, g++-gated)

Per SKILL_PREPARATION §9:
- **Exact baked stdout** for each topic (enter/leave traces, ordering booleans, recursion trace).
- **`sf_locals`** — both tab labels present (`without locals` / `with locals`).
- **Stepper** — `sf_nested`/`sf_recursion` emit multiple `step=` snapshots; the rendered page
  contains N step controls and N frame SVGs; deepest step is the default.
- **Gotcha** — the dangling warning/error surfaces (warning text, or `out--err` if `-Werror`).
- **WCAG invariant** — `html.count("<svg") == html.count('role="img"')`.
- **Self-contained** — no `<script src`/`<link`/`href="http"`/`src="http"`.
- **Id uniqueness** — `id="…"` set has no dups (CSS-safe radio ids for the stepper).
- **Pure (no-g++) unit tests** — drive `_svg_frames`/`_svg_memmap`/`parse_ptrdata_all` with
  FAKE pre-baked data (RED-before-GREEN): a 3-frame `live=` renders 3 boxes; 5 `step=` lines
  render 5 steps; a `memmap` line renders 5 regions.

---

## 8. Engine changes (surgical inventory)

1. `html_renderer.py`: `_svg_frames` (static + stepped) and `_svg_memmap`; add `frames`,
   `memmap` to the `svg_renderer` type dispatch.
2. `compiler_runner.py`: `parse_ptrdata_all` (multi-line) for the stepped case; single-line
   path unchanged for the six pointer types.
3. `components.py`: a `stepped_frames` CSS-radio step control (zero-JS); wire into
   `_demo_variant_body`/`demo_panel` so a topic with multi-step ptrdata renders the stepper.
   Regenerate `usage/INTERFACE_ELEMENTS.md` if the catalog introspects the new signature.
4. No changes to the page engine (`render_page.py`), loaders, or author-facing block vocabulary.

---

## 9. Risks & open implementation questions

- **Address-ordering determinism** at the build's `-O0`/default flags — verify empirically
  before asserting ordering booleans; fall back to trace-only assertions if flaky.
- **Warning surfacing** for the gotcha — confirm the build captures compiler stderr on success
  (§6); pick warning-vs-`-Werror` then.
- **`parse_ptrdata_all` backward-compat** — the six pointer renderers must keep reading exactly
  the first line; add a new function rather than changing the existing one.
- **Stepper id collisions** — radios need CSS-safe, per-topic-unique ids (reuse the existing
  id-safety helper used by multi-subcase panels).

---

## 10. Future (expected refinements — design for extension)

- More examples (user anticipates them): pass-by-value copy in the callee frame, tail calls,
  large-array stack cost, stack overflow via deep recursion (once run-env crash handling is in).
- ASan stack-use-after-return run-env plumbing (would let the gotcha *also* fault at runtime).
- The stepper could later animate automatically or add a scrubber — kept zero-JS for now.
