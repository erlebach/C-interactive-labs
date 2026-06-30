# Lessons Learned — Building Accessible C++ Demos

*Generated 2026-06-29 22:11 EST. Source: analysis of `cpp_ptr_lab/` (the C++ Pointers/References
and Smart Pointers labs). Audience: a future author building demo interfaces for a C++ course,
targeting **ADA Title II / WCAG 2.x Level AA**.*

This repo contains **two** demo backends for the same content: a DearPyGui (DPG) desktop app
(`app_base.py`) and a static-HTML generator (`html_renderer.py` + `build_html.py`). The HTML
backend exists *because* the DPG one cannot be made WCAG AA compliant. The single most important
lesson is structural and is stated first.

---

## 0. The meta-lesson: separate content/engine, choose the accessible engine

The domain model is GUI-agnostic and lives apart from any renderer:

- `code_generator.py` — `TopicTemplate`, `ControlDef`, `CaseDef`, `generate_source()` (templating only).
- `compiler_runner.py` — all g++ subprocess/parse concerns; returns dataclasses.
- `pointers_refs/topics.py`, `smart_ptrs/topics.py` — pure declarative topic data.
- `yaml_config.py` + `lab_config.yaml` — fail-open topic enable/disable.

Only the **engine** differs: `app_base.py` (DPG, 743 lines) vs `html_renderer.py`/`build_html.py`
(HTML). Because the model was decoupled, migrating from the inaccessible DPG app to accessible
HTML cost *one file* — the diagram primitives, topic data, templating, and compiler backend all
carried over unchanged.

**Takeaway:** Build the content as data and keep all domain logic out of the GUI file. Then the
accessibility decision becomes "swap the engine," not "rewrite the app." For anything that must
be ADA-compliant, the engine must be **semantic HTML**, not an immediate-mode GPU canvas.

---

## Part 1 — Constructing accessible HTML demo pages

### 1.1 Build-time bake architecture (zero JS / zero backend / zero network)

Compile and run real C++ at **build** time; freeze the results into a self-contained HTML file.
Nothing is computed at view time.

```
topic template → expand_variants() → generate_source() → g++ compile+run
  → parse stdout (PTRDATA:/MEMBYTES:) → svg_renderer(dict) → render_fragment()
  → assemble_page() (all CSS inlined) → dist/*.html
```
(`build_html.py:161-193` orchestrates; `html_renderer.py:576-578` guarantees no external refs.)

Why it matters for this audience:
- **Survives an LMS.** Canvas strips `<script>` and blocks `fetch`; a fully static page with
  inlined CSS and zero JS pastes in and just works.
- **Deterministic.** Addresses are captured once and frozen ("real output from a 64-bit build;
  frozen here for stable study," `html_renderer.py:514`) — stable for study and grading.
- **No runtime dependency.** g++ is a *build*-only requirement (guarded at `build_html.py:169-173`).

Keep the renderer **pure** — no I/O, no subprocess (`html_renderer.py:1-4`). It takes dicts and
returns strings, so every diagram and page is unit-testable without invoking a compiler.

### 1.2 Zero-JS interactivity: native radios + CSS `:checked` sibling combinator

Tabs (variant switching and topic switching) use real `<input type="radio">` + `<label for>` +
CSS `~` selectors — **no JavaScript**.

```css
#{vid}:checked ~ .tabs label[for="{vid}"] { background: var(--accent); color: var(--accent-fg); }
#{vid}:focus-visible ~ .tabs label[for="{vid}"] { outline: 3px solid var(--accent); }
#{vid}:checked ~ .panels #{panel_id} { display: block; }
```
(`_css_checked_rules`, `html_renderer.py:371-389`; topic-nav variant `_topic_nav_css:553-565`.)

Why this is the right idiom for WCAG AA:
- Native radios give **keyboard roving (arrow keys), Space-to-select, focus, and correct
  screen-reader semantics for free** — no ARIA-widget JS to get wrong.
- Works where JS is blocked (Canvas).
- **Hide the radios with clip/off-screen, never `display:none`** (`.vradio`/`.vtopic`,
  `html_renderer.py:286-289, 315-318`) — `display:none` removes them from the focus order.
- Surface focus with `:focus-visible` outlines.

Two load-bearing constraints (both learned the hard way — see §1.6):
- **Namespace every `name`/`id`/selector by topic id** (`name="{tid}-type"`, `id="t-{tid}"`),
  or multiple topics in one combined file share a radio group and cross-switch.
- **Sanitize ids to valid CSS identifiers** before interpolating into `#id` selectors.

### 1.3 Accessible inline SVG diagrams

Every diagram is inline SVG with a text alternative generated from the **real captured data**:

```python
f'<svg viewBox="0 0 500 160" role="img" aria-labelledby="{title_id} {desc_id}">'
f'  <title id="{title_id}">{title}</title>'
f'  <desc id="{desc_id}">{desc}</desc>'           # e.g. "ptr at 0x… → val=42 at 0x…"
```
(`_wrap_svg`, `html_renderer.py:65-77`; per-type desc at `:98-99, :192-193`.)

- `role="img"` + `aria-labelledby` (referencing *both* title and desc ids) gives the SVG an
  accessible name that **narrates the pointer state**, not just "diagram."
- **Unique id prefix per SVG instance** (`{tid}-svg-v{i}`, `-c{j}` per case) — duplicate
  `title`/`desc` ids across SVGs in one document corrupt `aria-labelledby` resolution.
- Fixed `viewBox="0 0 500 160"` (mirrors the old DPG canvas) keeps integer coordinates
  resolution-independent; the SVG scales to `width:100%`.
- Degrade gracefully: missing keys → `"?"`, unknown type → `_svg_unknown`, never raise
  (`html_renderer.py:236-247`). When there is genuinely no data, render the column **empty**
  rather than a misleading placeholder (`no_diagram = "ptrdata" in v and not ptrdata`,
  `html_renderer.py:500-503`).

### 1.4 The WCAG AA theme (`_CSS`, `html_renderer.py:254-368`)

Concrete AA techniques actually present, with the success criteria they satisfy:

| Technique | Where | WCAG AA SC |
|---|---|---|
| Contrast tokens (`--fg:#1a1a1a` on `#fff` ≈16:1; `--accent:#0b5394` + white; dark `--ok`/error) | `:root` `255-266`, SVG palette `17-23` | 1.4.3 |
| 44×44 px target sizes on all controls | `.topic-nav`/`.tabs`/`summary` `296-365` | 2.5.5 / 2.5.8 |
| Skip link (off-screen, slides in on focus) → `#main` | `.skip` `277-282`, emitted `632` | 2.4.1 |
| `<html lang="en">` | `622` | 3.1.1 |
| Visible focus (`:focus-visible { outline:3px }`) | `276`, per-tab `382-384` | 2.4.7 |
| 16px body, 1.5 line-height, system font | `269` | 1.4.4 |
| No-outer-scroll shell + inner panel scroll + 760px reflow | `272-275, 335, 347-348` | 1.4.10 |
| Semantic landmarks `header/main/nav/section/figure` + headings | `600-634, 440-453, 512-515` | 1.3.1 |
| Non-text content has text alt (SVG title/desc) | §1.3 | 1.1.1 |
| Failure shown by **text + border**, not color alone ("Compile failed." red box) | `out--err` `363, 519-525` | 1.4.1 |

Centralize color in `:root` tokens chosen to clear 4.5:1, and **reuse the same palette in the
SVG** so chrome and diagrams stay consistent and compliant.

### 1.5 Data-shape & extensibility idioms

- **Variant/case dict contract** (`build_html.py:89-100`): `label, source, svg, stdout, membytes,
  failed, stderr, ptrdata`. A variant either carries one case's keys or a `"cases"` list.
- **Multi-sub-case panels** (`CaseDef`, `code_generator.py:42-53`): one topic, compiled *N* times,
  each filling an extra `<<placeholder>>`. `const_taxonomy` uses this to compile the
  write-vs-rebind 2×2 truth table as independent programs, so the forbidden operation *genuinely
  fails to compile* and shows the real g++ error (`pointers_refs/topics.py:108-119`).
- **`<<placeholder>>` templating** chosen to avoid `str.format` collisions with C++ `{}`; loops to
  a fixed point so substitutions can nest; `<<HARNESS>>` injects byte-dump instrumentation
  (`code_generator.py:9-12, 76-91, 135-142`).
- **`value_map`** separates the human label ("const int* const (both immutable)") from the emitted
  code (`const int* const ptr = &val;`); keys booleans as `"true"/"false"`
  (`_resolve_control_value`, `code_generator.py:99-106`).
- **Extending** = append a `TopicTemplate` (pure data) or add a `_svg_*` function + one dispatch
  entry. Variants come free from a Cartesian product over dropdown controls (`build_html.py:62-81`).

### 1.6 HTML pitfalls (each cost a real bug this project)

- **Unescaped `(` `)` `,` `*` `/` in `#id` selectors are *silent* CSS parse errors** that kill the
  `:checked ~` rule with no console warning → blank panels. Sanitize every id to `[A-Za-z0-9_-]`
  (`html_renderer.py:409-415`).
- **Stringified booleans** leak into generated code: `str(False)` → `"False"` bypassed the
  `value_map` and emitted a bare `False` into C++. Preserve the bool so `value_map["false"]`
  resolves.
- **Duplicate SVG `title`/`desc` ids** across a combined document break `aria-labelledby` — always
  prefix per instance.
- **Stacked panels need a scroll container**: a layout built for one full-height grid clips
  multiple stacked sub-cases unless the panel itself scrolls (`.panel { overflow-y:auto }`).
- **`display:none` on hidden radios** removes keyboard focus — use clip/off-screen.

---

## Part 2 — Constructing DearPyGui interfaces (and why they fail WCAG AA)

DPG is excellent for fast desktop prototypes and instructor-side exploration. Treat it as a
**prototyping/desktop tool, not an accessible deliverable.**

### 2.1 Idioms worth keeping

- **Parametric controller** (`PtrLabApp`, `app_base.py:83-108`): one engine, parameterized by a
  topic list + title; launchers differ only in data (`run_ptrs.py`, `run_smart.py`).
- **Generic widget builder dispatched on `ctrl.kind`** (`_build_control`, `app_base.py:325-354`):
  dropdown→combo, text→input, checkbox; raises on unknown kinds (fail-fast).
- **UI state in plain Python keyed by id** (`TopicState`, `self.states`, `app_base.py:61-75,
  405-414`) — tab switch restores prior output trivially.
- **Never block the UI thread**: compile/run on a daemon thread + `queue.Queue` + frame-callback
  polling (`set_frame_callback(...)`) + a `threading.Event` cancel + single-flight guard
  (`app_base.py:422-501`).
- **Fail-open config** (`yaml_config.py:27-57`): missing file/YAML/dep → all topics enabled.
- **Drawing primitives**: a small box/label/arrow vocabulary on a **fixed 500×160 coordinate
  space** (`app_base.py:54`), with a clear-then-redraw cycle dispatched on `ptrdata["type"]`
  (`_render_diagram`, `app_base.py:578-613`). This maps almost 1:1 to SVG (`<rect>`/`<text>`/
  `<line>`, `viewBox="0 0 500 160"`) — author the primitives to *target SVG* and the diagram is
  accessible and portable from day one.

### 2.2 Idioms to avoid

- **Reverse-parsing widget tags to recover ids** (`app_base.py:391`,
  `tag[len(prefix):-len(suffix)]`) is brittle — carry the id in `user_data` or a side map.
- A single flat global tag namespace forces the `_tag()` discipline everywhere; it is mandatory,
  not optional.
- **Look-alike controls**: the "doc link" is a recolored *button* (`app_base.py:205-211`), not a
  real link — no link semantics, no AT role.

### 2.3 Why DPG cannot reach WCAG AA (architectural, not configurable)

DPG/Dear ImGui renders to a GPU canvas with no OS accessibility tree. Every barrier below is
structural:

1. **No accessibility tree / no screen-reader support.** Widgets are not OS-native; they expose no
   UIA/AX/AT-SPI API. All `add_text`/`add_combo`/`add_button` are invisible to NVDA/JAWS/VoiceOver.
   *(Fails 1.1.1, 1.3.1, 4.1.2.)*
2. **Diagram text is rasterized pixels.** `draw_text`/`draw_rectangle`/`draw_arrow`
   (`app_base.py:635-733`) produce glyphs with no text node, no alt, nothing selectable. The
   biggest barrier. *(1.1.1.)*
3. **State by color only.** Compile status = border color (red/orange/gray,
   `app_base.py:43-45, 553-558`) with no icon/text on the diagram itself. *(1.4.1.)*
4. **Low contrast.** Dim hex addresses `(120,120,140)` on `(40,40,60)` fill and `(180,180,180)`
   headers fall below 4.5:1; the palette was not contrast-checked. *(1.4.3.)*
5. **Weak keyboard model.** ImGui's mouse-centric immediate-mode focus has no standards-compliant
   tab order, focus ring, or skip links. *(2.1.1, 2.4.3, 2.4.7.)*
6. **Fixed pixels defeat zoom/reflow.** Viewport 1280×860, fixed widths and font sizes, absolute
   500×160 diagram — no reflow, no honoring of 200% zoom / OS text scaling. *(1.4.4, 1.4.10.)*
7. **No programmatic label/relationship** between section headers and the inputs they describe.
   *(1.3.1, 3.3.2.)*
8. **Dynamic results aren't announced** — `set_value` pushes async compile output with no
   `aria-live` equivalent.

**Conclusion:** these are properties of the rendering architecture, unfixable by theming. For an
ADA-compliant deliverable, migrate to static HTML + inline SVG + native form controls + `aria-live`.
The clean model/engine split makes that migration cheap (see §0).

---

## Quick-start checklist for the next accessible demo

1. **Model first.** Define content as data (templates + control defs); keep zero GUI logic in it.
2. **Engine = static HTML** if it must be accessible or embedded in an LMS. Bake real output at
   build time; inline all CSS; reference nothing external.
3. **Tabs = native radio + `<label>` + CSS `:checked ~`.** Hide radios with clip, not
   `display:none`. Add `:focus-visible` outlines.
4. **Namespace every id by a stable content id; sanitize ids to `[A-Za-z0-9_-]`** before they
   reach a `#id` selector.
5. **Diagrams = inline SVG** with `role="img"`, `<title>`/`<desc>` generated from real data,
   unique id prefix per instance, fixed `viewBox`. No data → empty space, not a placeholder.
6. **Theme to AA:** `:root` color tokens ≥4.5:1 (reused in SVG), 44px targets, skip link,
   `lang`, visible focus, 16px body, scroll inside panels + reflow at ~760px, semantic landmarks.
7. **Never signal state by color alone** — pair every color with text and/or a border.
8. **Keep the renderer pure** so it is unit-testable without a compiler; let one module own all I/O.
9. **DPG is fine for prototypes**, but design its drawing primitives to also emit SVG so the
   accessible build is a port, not a rewrite.
