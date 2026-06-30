## Why

The `cpp_ptr_lab` Dear PyGui app is dark, low-contrast, and unusable by students
who rely on screen readers or keyboard navigation — it fails ADA / WCAG AA and
cannot run inside Canvas (which blocks JavaScript and arbitrary native apps).
The pedagogical content (topics, C++ templates, real g++ output) is sound; only
the *delivery* is inaccessible. Migrating to standalone, build-time-rendered
static HTML makes the same lessons WCAG AA compliant and Canvas-pasteable with
zero JavaScript, zero network, and zero backend at student runtime.

## What Changes

- Add a build-time renderer that turns each topic's real g++ output into a
  self-contained, accessible HTML page — no DPG, no JS, no server at runtime.
- Variant switching (e.g. `int` / `double` / `float`) uses the native-radio
  **CSS `:checked` sibling pattern** — keyboard- and screen-reader-accessible
  for free, and functional in Canvas where JS is stripped.
- Port the six DPG `_draw_*` diagrams (raw, null, ref, unique, shared, weak) to
  inline SVG with `<title>`/`<desc>` and `role="img"`; the 500×160 DPG coord
  space becomes the SVG `viewBox` 1:1.
- Bake real compiler/runtime output in at build time: for each topic and each
  variant, `generate_source` → `g++` compile+run → parse `PTRDATA:`/`MEMBYTES:`
  → render into HTML. Compile-failure variants capture and display stderr.
- Emit **two groupings** from the same fragments: per-topic standalone files
  (`dist/topics/*.html`, Canvas-paste granularity) and per-lab combined files
  (`dist/lab_pointers_refs.html`, `dist/lab_smart_ptrs.html`, offline single-file).
- Light, high-contrast WCAG AA theme with 44px target sizes, visible focus,
  and a skip link — replacing the original dark/low-contrast complaint.
- All ids / `name`s / CSS selectors are namespaced by topic id so multiple
  topics can share one combined file without `:checked` cross-contamination.

## Capabilities

### New Capabilities

- `static-html-renderer`: Pure functions that turn parsed run data into
  accessible static HTML — `svg_renderer(ptrdata)` (per-type inline SVG diagram),
  `render_fragment(topic, variants)` (one self-contained, namespaced topic
  section with zero-JS radio variant switching), and `assemble_page(fragments)`
  (a complete WCAG AA document with skip link, `lang`, and no id collisions).
- `static-html-build`: Build-time orchestration that, for each topic and each
  variant, generates source, compiles and runs it via the existing
  `compiler_runner`, captures stdout/stderr (including compile failures), parses
  it into render data, and writes both per-topic (`dist/topics/*.html`) and
  per-lab combined (`dist/lab_*.html`) output files.

### Modified Capabilities

<!-- None. Topic content (pointers-refs-lab, smart-ptrs-lab, topic-content),
     code-generation, and compiler-runner are reused unchanged; the static HTML
     is a purely additive delivery path. -->

## Impact

- **New module(s)** in `cpp_ptr_lab/` (e.g. `html_renderer.py`, `build_html.py`)
  plus a `dist/` output tree. The DPG `app_base.py` and launchers are left intact
  but are superseded as the accessible delivery path.
- **Reused unchanged**: `code_generator.py`, `compiler_runner.py`, both
  `topics.py` topic lists (`TopicTemplate` / `ControlDef`).
- **Toolchain**: build step requires `g++` (already required); runtime requires
  only a web browser. No new Python dependencies for rendering (stdlib only).
- **No breaking changes** to existing code; `cpp_initializer_lab/` untouched.
