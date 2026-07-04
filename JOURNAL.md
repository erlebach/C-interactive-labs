# opencode — Journal

Chronological log of features, bug fixes, and architectural decisions.

## 2026-07-03 21:00 — cpp_labs migration + North-Star auto-discovery + folder consistency

Renamed the lab tree `cpp_ptr_lab/ → cpp_labs/` (the subject is no longer pointer-specific) and drove it to the data-over-code North Star: **a new subject is now pure data — a folder with a `topics/` dir of YAML plus a layout, zero Python, no registry edit.** Seven commits (`15da2d0..9f502d0` on `fix/glossary-loader-dry`); `cpp_ptr_lab/` left frozen, output now targets `dist_labs/`. The keystone: `_topic_registry` auto-discovers `cpp_labs/*/topics` via a new `discover_topics()` instead of importing each subject by name, so all five `topics.py` shims were deleted and the redundant `order:` key retired (render order lives in the layout's `demos:` list). Also migrated the last two Python-defined subjects to YAML, moved each subject's tests into a `tests/` subfolder, made `pointers_refs` and `op_overload` byte-identical in shape (`demos/ glossaries/ layouts/ tests/ topics/`), and retired the Python→YAML migration scaffolding (snapshots + equivalence guards). Registry resolves the same **21** topic ids as before (asserted against a captured baseline); full `cpp_labs/` suite **428 passed**, all five pages rebuild self-contained. Deferred known-legacy gaps: `function_args`/`smart_ptrs` still lack `demos/ glossaries/ layouts/`; `smart_ptrs` has no layout. Handoff: `handoffs/HANDOFF_2026-07-03_20h59mEST.md`.

### Details

The seven commits, in order: (1) `15da2d0` extracted a `_glossary_from_source` engine helper (deduped `_render_header`/`_build_sidebar`). (2) `9948195` copied only the files reachable from HTML construction into `cpp_labs/` (traced from the build entry point; dropped the DPG-era modules — `app_base`, `gallery`, `topic_page`, `yaml_config`, run scripts). (3) `5367609` migrated `function_args` + `smart_ptrs` to `topics/*.topic.yaml`. (4) `1a9d039` added `discover_topics()`, pointed the registry at it, deleted all five `topics.py`, and removed `order:` — safe because the registry is an id-keyed lookup (load order never reached output) and baking is demand-driven from the page's `bake:` map (unused discovered topics are never compiled). (5) `e419027` de-duplicated the loader tests behind a shared serializer, removing subject-test-imports-another-subject coupling. (6) `0809966` moved each subject's tests into `tests/` (with `__init__.py` so the three same-named `test_topics_loader.py` files stay distinct packages; `.parent → .parents[1]` path fixes). (7) `9f502d0` relocated `pointers_refs.page.yaml → layouts/` and `YAML_GUIDE.md → usage/`, and deleted `topics_snapshot.json` ×3 + the `test_yaml_matches_legacy` guards + the now-dead `topic_equiv.py` — the snapshots only proved the migration was lossless (already in git history) and would nag on every intentional YAML edit; `op_overload` (born-YAML) never had one.

## 2026-07-03 14:30 — Reusability seam: nav_shell, prose box, concept disclosure, sidebar

Factored the demo_panel/nav_shell reusability seam so the engine dispatches navigation and prose uniformly, entirely as data. New **`nav_shell(comp_id, items, *, style="left_rail", leading=0, selected=None)`** is the single uniform nav interface: `build_layout` routes every layout `style:` (`left_rail`/`top_tabs`/`stacked`) through it with no per-style branching, and an unknown style raises `ValueError`. A shared **`_prose_box`** helper now backs the glossary and both concept renderers. The per-**Example** Concept that opens each demo is now a collapsed native `<details>` disclosure — the new **`concept`** block (`concept_note`, zero-JS/keyboard/SR-operable, optional `open: true`) — replacing the old always-open `callout_note: {label: Concept}` across all **12 demos**; `callout_note` stays valid for always-visible asides (backward compatible). Layouts gained a unified **`sidebar:`** list (replacing the old `glossaries:`): an ordered set of single-key keyword blocks (`- glossary: {id, source, label}` or `- concept: {id, text, [label]}`) rendered as leading italic rail entries in list order — where `concept` is the optional whole-**Demonstration** Concept (`concept_panel`, a leading rail panel, not selected on load). Suite now **438 passing**; both rail pages (`pointers_refs`, `op_overload`) rebuilt clean, self-contained, WCAG-AA.

### Details

**Locked vocabulary:** Demonstration = one HTML file/topic; Example = one rail entry (one `.demo.yaml`); Gotcha = an Example whose point is a failure; Concept = prose stating what is imparted (one `text:` field), at two levels — Demonstration (whole page, in `sidebar:`) and Example (per demo, the `concept` block).

TDD RED→GREEN throughout, guarded by **two byte-identical guards**: one asserts `nav_shell(..., style="left_rail")` reproduces the previous `left_rail_layout` output byte-for-byte; the other asserts the migrated pages match the pre-refactor bytes — proving the seam is a pure refactor, not a behaviour change. Specs: `docs/superpowers/specs/2026-07-03-reusability-seam-design.md`, `docs/superpowers/plans/2026-07-03-reusability-seam.md`.

## 2026-07-03 00:30 — Operator-overloading demo (op_overload) + optional-diagram flag

Added the first **non-pointer subject**, operator overloading, almost entirely as YAML data — validating
that a subject outside the memory-diagram domain is cheap. New engine capability: `topic: { diagram: false }`
suppresses the per-program memory diagram (the `COURSE_VIA_TOPICS.md §7` "topic layout is a fixed recipe"
fix); default stays **on** so pointer pages are byte-unchanged. Threaded `_build_topic → demo_panel →
_demo_variant_body` (all default `diagram=True`). New subject `cpp_ptr_lab/op_overload/` mirrors
`pointers_refs/`: 4 topics (op_plus/op_scale/op_equal/op_stream), 4 demos, 1 glossary, 1 `left_rail`
layout → **4 rail entries** (one operator each; the `<<` entry stacks the correct non-member version + the
member-`<<` compile-error gotcha). Wired via an op_overload `topics.py` shim reusing the generic
`load_topics(topics_dir)` + one line in `_topic_registry`. Real g++ output baked (`a + b = (4, 6)`,
`2 * a = (2, 4)`, `a == b: false`, `a = (1, 2)`); the member-`<<` case genuinely fails to compile.
Self-contained, no memory diagram, WCAG AA. TDD RED→GREEN: 2 diagram-flag tests + 7 op_overload build
tests. Suite **412 → 421**. Known cosmetic: single-variant topics still show a lone "default" tab —
slated for the reusability pass. Build: `python -m cpp_ptr_lab.yaml_engine.render_page
cpp_ptr_lab/op_overload/layouts/op_overload.rail.yaml dist`.

## 2026-07-02 19:30 — pointers_refs C++ source migrated Python → YAML (data-over-code North Star)

Final data-over-code North-Star step for pointers_refs: all 8 topics' C++ source (templates,
controls, value_maps, cases) moved from `topics.py` Python literals into `topics/<id>.topic.yaml`;
`topics.py` is now a ~17-line re-export shim. TDD-ordered across 4 tasks: frozen
`topics_snapshot.json` → `topics_loader.load_topics()` built + tested against snapshot →
equivalence-guard `test_yaml_matches_legacy` asserts byte-for-byte reproduction (non-vacuous:
fails on any corruption) → Python literals deleted. Scalar-style discipline: `|` for templates,
`>-` for prose, block scalars for multi-line value_map C++; a review-driven fix converted
ref_no_null's value_map from a 200-char escaped one-liner to block scalars. **Result:** suite
**412 passed, 0 failures**; rail rebuilt cleanly (exit 0); diff vs `main` showed only runtime
stack-address variation in SVG diagrams (expected), structural equivalence proven by the guard.
smart_ptrs/function_args deferred. Spec: `docs/superpowers/specs/2026-07-02-source-to-yaml-design.md`.

### Details

Plan: `docs/superpowers/plans/2026-07-02-source-to-yaml.md`. Worktree diff excluded from the
identity check because each g++ run produces fresh stack addresses in SVG `<desc>` nodes; the
equivalence guard (objects match snapshot) is the authoritative structural proof.

## 2026-07-02 18:25 — WCAG AA fix: highlight.js comment colour #5c6370 → #9199a8

Closed the contrast caveat from the previous entry. atom-one-dark's comment/quote colour `#5c6370` is
only **2.32:1** on its `#282c34` background — below WCAG AA 1.4.3 (4.5:1). Fixed to **`#9199a8`** (**4.88:1**),
which stays muted (dimmer than the `#abb2bf` code text) so comments still read as de-emphasized. Applied as
an override in **our** layer (`_HLJS_OVERRIDE_CSS`, inlined AFTER the theme so it wins) — **not** by editing
the vendored theme, so a future re-fetch keeps the fix. TDD RED→GREEN: `test_comment_color_meets_wcag_aa`
parses the effective (last-wins) `.hljs-comment` colour and asserts ≥4.5:1 vs `#282c34` via a WCAG-relative-
luminance helper (was 2.32 → now 4.88). Verified computed colour `rgb(145,153,168)` in Playwright. Suite
**404 → 405**. Rail rebuilt.

## 2026-07-02 18:14 — Syntax highlighting on the rail page via inlined highlight.js (self-contained)

Added real syntax highlighting to the rail/layout pages using **highlight.js**, vendored + inlined so the
page stays self-contained (no CDN/network). Source blocks already carried `class="language-cpp"` (from the
earlier language-class work), so no markup change — highlight.js colours them on load. **Decision path:**
user weighed CDN (option 2) vs inline (option 1); the tiebreaker was accessibility, and AT is **identical**
across both (hljs token `<span>`s are presentational — no role/aria — so screen readers read the plain code
text regardless), so option 1 (inline, self-contained, graceful JS-off fallback) won. **Scoping:** gated
behind `page_shell(..., highlight=True)`, default **off**; only `build_layout` opts in — so the ~30 other
pages' self-containment tests stay green; only 2 layout assertions needed updating. Vendored
`cpp_ptr_lab/vendor/highlightjs/` (highlight.min.js v11.9.0 common bundle incl. C++, atom-one-dark theme,
BSD-3-Clause; + README with provenance). **Self-containment invariant refined:** the crude `"https://" not
in html` check was wrong (the inlined lib carries URL *text* in comments); tests now assert no external
*load* (`<script src`, `<link`, `src=`, `href="http"`). Program output (`<pre><samp>`) stays unhighlighted.
Rail page 96KB → 218KB (the inlined 122KB lib). TDD RED→GREEN: `test_highlight_flag_inlines_hljs_no_external`,
`test_no_highlight_by_default`, `test_source_highlighted_with_hljs`. Suite **401 → 404**. Verified in
Playwright: 19 highlighted blocks, `window.hljs` defined, zero console errors. **Caveat (noted, not fixed):**
atom-one-dark's comment gray (~#5c6370 on #282c34) is ~3:1, below WCAG AA 4.5:1 — revisit theme/comment colour.

## 2026-07-02 15:50 — Second glossary on the rail page (0..N glossaries, data-only)

Exercised the 0..N-glossaries-per-page capability by adding a **second** glossary to the pointers_refs rail
page — **zero engine changes**, pure YAML, the data-over-code North Star in practice. New data file
`glossaries/references.glossary.yaml` (title "Vocabulary — Reference Semantics", 7 reference-focused terms:
lvalue, rvalue, bind, alias, lvalue reference, const reference, pass-by-reference) chosen to **complement,
not duplicate**, the general "Vocabulary" glossary. Wired by one line in the layout's `glossaries:` list
(`{id: g-ref, label: "Reference Terms"}`). The engine's existing loop renders it as a full rail panel and
`italic_count = len(glossaries)` auto-bumps to 2, so both leading rail labels are italic; `selected` logic
still lands on the first **demo** (Basic Pointer) at load. Verified in Playwright: two italic entries
("Vocabulary", "Reference Terms") above the 8 bold demos, the new panel renders its `<dl>`. TDD RED→GREEN:
`test_second_reference_glossary_present`. Suite **400 → 401**. Rail rebuilt.

## 2026-07-02 15:40 — Byte box is data-driven: omit empty byte-grid on no-byte variants

User screenshot (Ref: Must Bind — a failing-compile topic) showed a broken "Raw bytes of ptr" box: an
empty grid with just the `byte`/`value` row-headers, collapsing to minimum width so its `<caption>` wrapped
one word per line. **Root cause (user's framing):** the box-generating code was already the *same* single
path for pass/fail — `_demo_variant_body` emitted the details+`byte_grid` **unconditionally**; only the
*data* differed (failed compile → no `MEMBYTES` → `v["bytes"] == []`). Feeding that path an empty list made a
degenerate table. **Fix (option 1, user-chosen):** keep one code path, make it **data-driven** — emit the
byte box only `if v["bytes"]`. Keys off byte-data presence, never the `failed`/`ok` flag; renders identically
whenever data exists (success), omits the meaningless table otherwise. A failed compile now shows code +
"✗ Compile failed" + error output and nothing else (verified in Playwright). TDD RED→GREEN:
`test_no_byte_data_omits_byte_grid`; positive `test_demo_panel_variant_tabs_and_details_bytes` still green.
Suite **399 → 400**. Rail rebuilt.

## 2026-07-02 15:30 — Byte-grid readability: cell text 13px → 15px (user report)

User screenshot showed the "Raw bytes of ptr" table cramped — its `byte`/`value` cells rendered at
**13px**, the smallest text on the page (body 16px, console 14px), so the hex bytes looked tiny. Grounded
the fix with Playwright (served over `http://localhost`): measured cell `font-size:13px`, `cellW:33px`.
**Fix (one CSS rule):** `.byte-grid td,th` font `13px → 15px` and padding `.3rem .5rem → .35rem .6rem` for
breathing room. Re-measured after reload: 15px, cellW 38px; screenshot confirms the table now matches the
surrounding content's readability. TDD RED→GREEN: `test_byte_cells_are_readable_size` (guards the byte-grid
rule is not 13px and is ≥15px — a regression guard tied to the report). Suite **398 → 399**. Rail page
rebuilt. No behavioral/layout change beyond the larger cells.

## 2026-07-02 15:18 — Legacy sweep: compiler stderr `<pre>` → `<pre><samp>` (SIA-R79)

Finished carrying the `<samp>` accessibility rule into the **legacy** `html_renderer.py` so *every*
generated page satisfies the no-bare-`<pre>` invariant, not just the current rail page. The failed-compile
path emitted a bare `<pre style="margin-top:.5rem">{stderr}</pre>` — compiler error output is program
output, so it belongs in `<samp>` (sample output), same as the current `output_console`. **Fix (one line):**
`<pre><samp>{stderr}</samp></pre>`. The adjacent source block was already `<pre><code>` (correct). TDD
RED→GREEN: `test_no_bare_pre_stderr_wrapped_in_samp` on `TestRenderFragmentMultiCase` (its failed-case
fragment exercises the path) — guards every `<pre>` carries a `<code>`/`<samp>` child **and** stderr is in
`<samp>`. Suite **397 → 398**. **Noted, not fixed (out of scope):** `html_renderer.py:576` interpolates
`{source}` unescaped into `<pre><code>` — verify it's escaped upstream when legacy is unified.

## 2026-07-02 15:05 — Scope the DPG-era viewport lock off document pages (base-CSS holdover)

Cleaned the `body { height:100vh; overflow:hidden; display:flex; flex-direction:column }` holdover in the
shared `_CSS`. It was DPG-era app-shell layout — right for the legacy `assemble_page` (header + internally
scrolling panels), **wrong for a document**. The current `page_shell` pages already neutralized it with an
inline `<body style="height:auto;overflow:auto">` **workaround**, so the base rule was dead weight there and
a patch here. **Fix:** moved the four viewport-lock properties out of the base `body{}` into a scoped
`body.lab-shell {…}`; legacy `assemble_page` opts in via `<body class="lab-shell">`; `page_shell` now emits a
plain `<body>` (base body is document-flow by default — inline workaround deleted). Behavior-preserving both
ways: document pages were already document-flow via the inline patch; legacy pages get identical properties
via the class. One inert `.lab-shell` rule still ships in the shared stylesheet (removed fully when legacy is
unified). TDD RED→GREEN: rewrote the two `assemble_page` body-CSS tests to assert the **scoped** rule +
`lab-shell` class; added `test_document_flow_no_viewport_lock` (page_shell body tag == `<body>`). Suite
**396 → 397**. Rail page rebuilt: plain `<body>`, single inert `100vh`.

## 2026-07-02 14:40 — Source blocks: `language:` field → `<code class="language-XXX">` (data-over-code)

Closed the item deferred from the `<samp>` session: source code now carries a syntax-highlight hook.
**Data-over-code holds** — the language is authored in YAML, not hardcoded: a new top-level `language:`
field on each demo/page spec is threaded `bake_all → _bake_one → _bake_program → _pre`, and `_pre`
emits `<pre><code class="language-XXX">` when set (else the classless `<pre><code>` — full backward
compat). Wired `spec.get("language")` at both `build_page` and `build_layout` call sites (per-demo in a
layout, since each demo spec is loaded independently). Kept the engine subject-agnostic: `_pre` never
mentions `cpp`; the 8 pointers_refs demos + 3 page YAMLs (basic_ptr, function_args, pointers_refs) each
declare `language: cpp` as data. Rebuilt rail page now has **19** `class="language-cpp"` blocks and
**0** classless `<pre><code>`; program output stays `<pre><samp>` (SIA-R79, untouched). TDD RED→GREEN:
`TestSourceLanguageClass` (5 tests — `_pre` with/without language, `_bake_program` threading both ways,
g++-gated end-to-end via `bake_all`). Suite **391 → 396**.

## 2026-07-02 14:02 — Accessibility: wrap program output in `<samp>` (no bare `<pre>`)

ADA scan (Siteimprove Alfa **SIA-R79** "Improper use of preformatted text element") flagged the rail
page. **Root cause:** `output_console` emitted a **bare `<pre>`** for program/compiler output — a
`<pre>` needs a semantic child (source code already used `<pre><code>`). **Fix (one line):** program
output is now `<pre><samp>…</samp></pre>` — `<samp>` = "sample output from a program", the correct
element for stdout/stderr, distinct from code input; clears SIA-R79 and the underlying WCAG 1.4.12
Text-Spacing concern, changes nothing visually. TDD RED→GREEN: `test_output_wrapped_in_samp_not_bare_pre`
(component) + `test_no_bare_pre_semantic_child` (rail-page guard: every `<pre>` carries `<code>`/`<samp>`).
**Rejected** `aria-label` on `<code>`/`<samp>` for language/output labels — those elements are
`role=generic`, so `aria-label` is not announced (invalid per ARIA-in-HTML); the console's visible
"Program output"/"Error output" span already provides the accessible distinction. Saved the general rule
(applies to *any* generated HTML) to `~/.claude/memory/domain/html-accessibility.md`. **Deferred (user):**
adding `<code class="language-XXX">` with the real language — `_pre` lives in the subject-agnostic engine,
so it needs a `language:` field threaded from YAML; not needed for SIA-R79. Suite **389 → 391**.

## 2026-07-02 13:20 — Option D: glossary becomes an italic "Vocabulary" rail entry (not a header block)

Moved the pointers glossary out of the always-on header into the left rail as its own pressable entry
(the locked-but-unbuilt "Option D" from the 2026-07-01 handoff). **Data-over-code holds:** authored via a
new top-level `glossaries:` list in the layout YAML (parallel to `demos:`), each `{id, source, label}`;
the header now carries only the color legend. Engine: `build_layout` renders each glossary as a full rail
panel and **prepends** them as leading entries; `left_rail_layout` gained two optional kwargs —
`italic_count` (first N labels italic, to set vocab apart from demos; no underline) and `selected` (which
panel shows on load). **Default view stays a demo:** glossary sits first in the rail but **Basic Pointer**
is the on-load panel (`selected = len(glossaries)`); the mobile menu button labels the shown panel. Tabs
page untouched (keeps its header glossary); italic is left_rail-only. TDD RED→GREEN: `TestLeftRailGlossaryNav`
(unit: italic + selected + no-italic-default) + `test_glossary_is_italic_rail_entry_not_header` (replaced
`test_glossary_in_header`). Suite **386 → 389**.

## 2026-07-01 23:14 — Mobile: fix horizontal-overflow blowout + Route J tap-to-open nav menu

Fixed the rail page rendering broken on mobile (user screenshot: giant stacked nav buttons, code
clipped off the right). **Root cause, found via Playwright at 375px:** the page was 700px wide at any
viewport because a `1fr` grid track's `min-width:auto` can't shrink below its widest child's
min-content — the code `<pre>` (`white-space:pre`, 74-char `printf`/PTRDATA line ≈ 673px) — so the
single-column media query fired but couldn't take effect. **Fix (CSS):** `minmax(0,1fr)` tracks +
`min-width:0` in `code_diagram_panel` and `left_rail_layout`, letting the code box's `overflow-x:auto`
engage (long code scrolls in-box); verified `document.scrollWidth == 375` (was 719). **Route J nav
menu:** at ≤760px the left rail collapses to one tap-to-open `<button>`; picking a demo shows it,
**closes the menu, and updates the button label** — a scoped inline `<script>` gated on a JS-added
`lr-js` class, so with JS off the rail just shows (graceful degradation). This relaxes the project's
**zero-JS invariant** to "**works without JS + no external/network**" (user approved; not using Canvas).
Also wrote `cpp_ptr_lab/pointers_refs/YAML_GUIDE.md` (plain-language authoring guide, incl. a cases-topic
worked example). Suite **381 → 386** (RED→GREEN; 3 committed "no `<script>`" assertions relaxed to forbid
only external script/network). Verified in Playwright: open→pick→close, label update, desktop unchanged.

### Details

- **Files:** `cpp_ptr_lab/components.py` (`left_rail_layout` +menu/CSS, `code_diagram_panel` CSS),
  `cpp_ptr_lab/yaml_engine/test_render_page.py` (+`TestMobileOverflow`, +`TestLeftRailMobileMenu`,
  `test_left_rail_zero_js`→`test_left_rail_no_external_script`), `cpp_ptr_lab/pointers_refs/test_layouts.py`
  (2 self-contained assertions relaxed), `YAML_GUIDE.md`, `.gitignore` (+`.playwright-cli/`).
- **Playwright gotcha:** `file://` is blocked — serve via `python3 -m http.server` and use `http://localhost:PORT/…`.
- **Open (next session):** implement **Option D** for glossary compactness (move glossary out of the
  always-on header into the nav as its own italic "Vocabulary" entry — user's chosen approach, not yet
  built); then integrate branch `feat/demos-and-layouts` (~14 commits, unmerged). Handoff:
  `handoffs/HANDOFF_2026-07-01_23h14mEST.md`.
- **Build/verify:** `python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml`
  (and `…/pointers_refs.tabs.yaml`); `python -m pytest cpp_ptr_lab/ -q` → 386 passed.

## 2026-07-01 18:47 — Demos & layouts system built (data-over-code); left-rail + top-tabs pages

Executed the 10-task demos/layouts plan end-to-end via **subagent-driven development** (fresh implementer
per task; spec+quality review on the substantive ones). The **data-over-code North Star holds**: the whole
Pointers & References lab now renders as *one standalone page where one demo shows at a time*, and authoring
it added **only YAML — zero per-demo Python**. Engine stays a thin fixed core — `render_fragment` split from
`render_page`; `_build_topic` reduced to a one-line adapter over a new reusable `demo_panel`; new `glossary`
+ `left_rail_layout` components; `build_layout` composes N demo fragments under a chosen nav `style:` + a
once-rendered `header:` (legend + shared glossary from `*.glossary.yaml`), CLI-routed on the `demos:` key.
Content is data: 8 `*.demo.yaml`, one `pointers.glossary.yaml`, two layouts (`.rail`=left_rail phase a,
`.tabs`=top_tabs phase b) — the second is a **one-file, zero-Python** style swap over the *same* demos.
**Open decision resolved: full class-namespacing** (not child combinators) — every structural class carries
its component id (`.vt-panel-{p}`, `.lr-panel-{p}`), so nested `variant_tabs` can't bleed. Suite **357 →
381** (24 new tests, TDD RED→GREEN throughout). Branch `feat/demos-and-layouts` (12 commits, not yet merged).

### Details

- **Build:** `python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/layouts/pointers_refs.rail.yaml`
  (and `…/pointers_refs.tabs.yaml`) → `dist/<stem>/<stem>.html`.
- **Nesting-safety proof (tabs page):** outer top-tabs nav uses comp-id `lab` → `vt-*-lab`; inner demos use
  `vt-*-bp/ct/…` — disjoint class sets, **0 duplicate ids** across 162 ids.
- **WCAG 1.1.1 (asserted test) verified on both built pages:** 19 `<svg>` = 19 `role="img"`, non-empty
  `<title>`, no `<img>` without `alt`. Both self-contained: 0 `<script>`, 0 `https://`, real baked g++
  output (30× `PTRDATA`, const `read-only` error ×2).
- **Final polish (2-reviewer consensus):** `build_layout` now raises a friendly `ValueError` listing valid
  styles on an unknown `style:` (fail-fast before g++), instead of a raw `KeyError`.
- **Deferred (non-goals):** move C++ source Python→YAML; unify the old standalone basic_ptr/function_args
  pages; add `references.glossary.yaml`; clean the base-CSS `100vh/overflow:hidden` holdover in
  `html_renderer.py` (currently overridden by `page_shell`, harmless).

## 2026-07-01 14:57 — Design spec + implementation plan: demos & layouts (no code yet)

Brainstormed and specced a **data-over-code** restructuring: separate reusable **demos** (demo = one
whole topic) from **layouts** (author-chosen subset of demos + a `header:` rendered once + a nav
`style:`), with **glossaries** as reusable minimal YAML the author attaches per subset (no built-in
"family"). North Star: authoring content adds **YAML, never Python**. Two artifacts written + committed,
**no implementation code yet**: `docs/superpowers/specs/2026-07-01-demos-and-layouts-design.md` (design,
WCAG 1.1.1 text-alts made a tested requirement) and `docs/superpowers/plans/2026-07-01-demos-and-layouts.md`
(10 TDD tasks: fragment split, `glossary`/`demo_panel`/`left_rail_layout` components, layout loader + CLI
routing, 8 YAML demos + glossary + left-rail page [phase a], nesting-safe `variant_tabs` + top-tabs page
[phase b]). Plan self-review caught a real nested-`variant_tabs` CSS-bleed bug (Task 9 fixes it via child
combinators; open decision: adopt full class-namespacing instead). Also: `README.md` added (`fb4aa12`);
two global feedback memories (plain-language, reporting-python-commands). Handoff:
`handoffs/HANDOFF_2026-07-01_14h57mEST.md`. Suite unchanged at **357 passed** (no code touched). Next:
user picks execution mode (subagent-driven vs inline) after `/clear`, then execute the plan RED→GREEN.

## 2026-07-01 10:39 — Combined Pointers & References lab page (new-engine equivalent of the old lab file)

Rebuilt the old `dist/lab_pointers_refs.html` (the whole basic-pointers lab on one page) using the YAML
engine — no new engine code, pure composition. Added `cpp_ptr_lab/pointers_refs/pointers_refs.page.yaml`:
one page that bakes 7 topics (`basic_ptr`, `const_taxonomy`, `ref_must_bind`, `ref_no_null`,
`ref_rebind_illusion`, `ref_const`, `null_deref`) and stacks a heading + concept callout + `topic` block
per demo. Each `topic` block is a variant_tabs cluster over that topic's baked variants — so basic_ptr
shows int/double/float tabs and const_taxonomy shows its 4 declaration types, each with the 2×2 stacked
sub-cases (real g++ `read-only` error) now that gap 1 is wired. `pointers_refs/` becomes a uniform subject
package (adds the page spec + `test_pointers_refs.py`). Builds to `dist/pointers_refs/pointers_refs.html`
(81 KB, self-contained, no duplicate ids across all 7 topics). TDD: 7 RED-first build tests. Suite **357
passed** (350 + 7). Build: `python -m cpp_ptr_lab.yaml_engine.render_page cpp_ptr_lab/pointers_refs/pointers_refs.page.yaml`.

## 2026-07-01 10:15 — Engine gap 1: wire cases-topics through the YAML engine

Closed the first known engine gap: a `cases`-topic (independently-compiled sub-cases per variant) now
renders through the subject-agnostic engine instead of being flattened to an empty program. Two surgical
changes in `cpp_ptr_lab/yaml_engine/render_page.py`: (1) `_bake_one` now branches on `v.get("cases")` and
preserves each sub-case as its own baked program (`entry[label] = {"cases": [...]}`), via a new
`_bake_program(v)` helper shared by the variant and sub-case paths; (2) `_build_topic` branches on
`"cases" in v` and wraps the sub-programs in the existing `stacked_subcases` component (each with its own
`code_diagram_panel` + `compile_status_badge` + `output_console` + `byte_grid`), via a new
`_panel_program(pid, v, caption)` helper factored out of the old inline body. Non-cases topics are
unchanged (backward compatible). Proven on the real `const_taxonomy` topic: **4 declaration-type tabs, each
2 stacked sub-cases (write / rebind), one genuinely failing per tab with an authentic g++ `read-only`
diagnostic**, no duplicate ids, self-contained. TDD: 6 RED tests first (`_bake_one` shape via monkeypatch,
pure cases-render, dup-ids, + a g++-gated end-to-end class), then GREEN. Suite **350 passed** (344 + 6).
Gap 2 (configurable `topic` layout) and a `const_taxonomy` subject page.yaml remain open.

## 2026-06-30 21:55 — Session handoff

Wrote `handoffs/HANDOFF_2026-06-30_21h55mEST.md` closing out this session (function_args subject +
engine/subject split). Next focus: engine gaps 1–2 (cases-topics → `stacked_subcases`, configurable
`topic` layout) and the now-unblocked course manifest. Also captured a small correction for the reader —
run the engine CLI from the project root; the moved basic_ptr spec is now at
`cpp_ptr_lab/basic_ptr/basic_ptr.page.yaml` (old `basic_ptr_yaml/` path is gone). Suite still **344
passed**. Committing the working-tree refinements (doc path refs, general CLI, split tests) via `/git`.

## 2026-06-30 21:40 — Split YAML engine from subject packages (uniform structure)

Refactor for consistent structure: the subject-agnostic engine no longer lives inside a subject-named
package. `cpp_ptr_lab/basic_ptr_yaml/` is gone, replaced by two packages: `yaml_engine/` (the engine —
`render_page.py` + `test_render_page.py`, pure-render tests only) and `basic_ptr/` (a subject page package
— `basic_ptr.page.yaml` + `topics.py` + `test_basic_ptr.py`). Now every subject folder has the **identical
shape** `{__init__.py, topics.py, <subject>.page.yaml, test_<subject>.py}` (basic_ptr + function_args).
`basic_ptr/topics.py` re-exports the `basic_ptr` TopicTemplate from `pointers_refs` (single source of
truth, no duplication) — answering "why did only function_args have topics.py". Engine changes: dropped
the basic_ptr-specific `SPEC_PATH`/`main()`; `main()` is now general (`python -m
cpp_ptr_lab.yaml_engine.render_page <page.yaml> [dist]`), and `build_page` writes `dist/<stem>/<stem>.html`.
Updated the 2 import sites + `COURSE_VIA_TOPICS.md` path refs. Behavior-preserving: **344 passed**
(unchanged); both pages rebuild via the new CLI. No `basic_ptr_yaml` refs remain in code.

## 2026-06-30 21:15 — `function_args` subject: end-to-end new-subject proof

First new subject built through the YAML engine — validates "new subject = new topic module + page spec,
no new diagram components" (handoff step 3). New package `cpp_ptr_lab/function_args/`: one `function_args`
`TopicTemplate` with a `mode` dropdown (by value / pointer / reference) → three tabs via the existing
`topic` builder + a `function_args.page.yaml`. `memory_diagram` reused unchanged: pointer → `type=raw`
(arrow to `val`), reference → `type=ref` (baked g++ confirms `ref_addr == target_addr`, the alias *is*
val's address), value → no `PTRDATA` (honest "no link"; output console shows `val` stays 42 vs 99). Two
tiny engine touches in `basic_ptr_yaml/render_page.py`: register the topic; generalize `build_page`'s
output subdir to the spec stem (→ `dist/function_args/function_args.html`). TDD: 11 RED-first tests.
Suite **344 passed** (333 + 11); page self-contained, no dup ids. Handoff:
`handoffs/HANDOFF_2026-06-30_18h32mEST.md`.

### Details

Modelling move that made one dropdown drive four co-varying spots (signature, assignment, probe, call
arg) without a Cartesian variant blow-up and with **zero change to `generate_source`**: each `mode`
option maps to a **complete program body** in a single `<<mode>>` placeholder. The three bodies are built
in Python from one `_SKELETON` via `.replace()` of four `<<...>>` fragments; the literal `<<HARNESS>>`
stays for the code generator's multi-pass replace loop to fill. Baked addresses confirm the pedagogy:
pointer `ptr_addr=0x…9c8 ≠ target_addr=0x…a18` (param is a distinct pointer holding val's address);
reference `ref_addr == target_addr` (same address = alias).

Tests (`test_function_args.py`): 3-mode topic shape + per-mode generated source (value has no `PTRDATA`,
pointer `*x=99`/`type=raw`, reference `type=ref`); pure page render with FAKE baked data (three tabs,
raw+ref diagrams present, self-contained, no dup ids); g++-gated integration (real output baked,
`after: val = 42` for value vs `= 99` for the other two, no dup ids).

Known rough edge: the value tab's diagram is `_svg_unknown` ("No diagram available") — truthful (no
pointer link) but reads as a gap; a future `separate-copy` diagram or a friendlier no-link render would
sharpen it. Engine gaps 1–2 (cases-topics, configurable `topic` layout) remain untouched — deferred as
separate steps.

## 2026-06-30 18:30 — YAML-driven page renderer + curriculum-expansion design

New subpackage `cpp_ptr_lab/basic_ptr_yaml/`: a YAML page spec (`basic_ptr.page.yaml`) drives a thin
translator (`render_page.py`) that maps a flat `blocks:` list to component calls — each block is
`{component_or_builder: {args}}`, the translator pops `id` and forwards the rest as kwargs, resolving
`${a.b.c}` refs from baked data. Two smart builders compose multiple components: `topic` (a
`variant_tabs` cluster over a baked topic) and `heading`/`html`. The YAML page is component-signature-
identical to the imperative `dist/topics_v2/basic_ptr.html`, self-contained, no dup ids; "same template
twice on a page" works via per-block id namespacing (two passing tests). Suite **333 passed** (320 +
13). Discussed scaling to a full C++ curriculum (initializers, pointers, stack frames, classes, function
args, templates, STL): decided on a 4-layer architecture — course manifest → YAML page specs →
per-subject topic modules (10–15 each, NOT a flat 30–50) → components — with the insight that ~10/15
components are a reusable subject-agnostic spine while the 4 diagram components are pointer-specific, so
a new subject = new topic module + 1–3 new diagram components + YAML pages. The flat block list = DOM
order = reading order is the ADA mechanism (WCAG 1.3.2 by construction). Known engine gaps (both in
`_build_topic`/`_bake_one`): cases-topics (`const_taxonomy`) unhandled, and the `topic` layout is a fixed
recipe. Handoff: `handoffs/HANDOFF_2026-06-30_18h32mEST.md`; next focus = prototype `function_args` + close
the two gaps.

## 2026-06-30 15:05 — Reconstruct basic_ptr topic page from the component library

Worked example of *consuming* the new component library: new `cpp_ptr_lab/topic_page.py`
assembles the `basic_ptr` topic page entirely from components (no bespoke HTML/CSS beyond
`<h2>` headings), baking real g++ output for all three type variants. Composition: `page_shell`
wraps `callout_note` (concept) + `color_legend` + `variant_tabs` (int/double/float) — each tab a
`code_diagram_panel` (`memory_diagram` + source) plus `compile_status_badge`, `output_console`,
and `byte_grid` — then `progressive_steps` and a `predict_reveal_quiz`. 9 of 15 components in one
page; each variant is an independent compile. Output → `dist/topics_v2/basic_ptr.html` (342 lines,
self-contained: 0 script/network/src refs, no duplicate ids). The point: assembling a topic page
is now ~40 lines of glue (`build_basic_ptr_page`) that bakes data and arranges vetted components,
vs extending the monolithic `render_fragment` template — the inversion the change was designed for,
and it adds the reveal-steps + quiz interactions for free. TDD: `tests/test_topic_page.py` (7
tests: self-containment, one tab per type, component signatures, real baked output, no dup ids,
missing-g++ guard). Suite: **320 passed** (313 + 7).

## 2026-06-30 14:49 — Fix code_line_link CSS-combinator bug + session handoff

While explaining how `code_line_link` works, found its hover/focus highlight was dead: the
rule used the `~` general-sibling combinator, but the linked `<code>` line was trapped inside
a `<pre>`, so it was never a sibling of `.cll-diagram` and the selector never matched. Fix
(`components.py`): emit the code lines as **direct children** of the namespaced `#{comp_id}`
container (no `<pre>` wrapper), styled with a shared `var(--code-bg)` background + first/last
rounding so they still read as one code block; linked lines get a `cll-link` dotted-underline
affordance. Added `TestCodeLineLink::test_linked_line_and_diagram_share_a_parent`, which
**parses** the fragment (html.parser) and asserts the line and diagram share the `#{comp_id}`
parent — a structural check string-matching tests can't make. Suite: **313 passed** (312 +
this regression test); gallery rebuilt; user confirmed all 15 pages work. Handoff written to
`handoffs/HANDOFF_2026-06-30_14h49mEST.md`. The `interactive-ptr-components` change is
feature-complete and user-confirmed — next action is `/opsx:verify` → `/opsx:archive`.

## 2026-06-30 14:00 — Interactive component library + gallery (OpenSpec: interactive-ptr-components)

Built a catalog of **15 pure, accessible, zero-JS page-element components** in a new
`cpp_ptr_lab/components.py` (beside `html_renderer.py`, additive — existing 130 tests
untouched), plus a `cpp_ptr_lab/gallery.py` build target that emits one standalone,
Canvas-pasteable demo page per component + an index into `dist/gallery/` (16 files,
zero external/script/network refs). Components: `page_shell`, `color_legend`,
`callout_note`, `memory_diagram`, `hover_link_diagram`, `before_after_toggle`,
`predict_reveal_quiz`, `compile_status_badge`, `output_console`, `byte_grid`,
`code_line_link`, `variant_tabs`, `code_diagram_panel`, `stacked_subcases`,
`progressive_steps`. Interactivity is baked-state + CSS only (`:checked`, `:hover`,
`:focus`, `<details>`) — survives Canvas's `<script>`/`fetch` stripping; native controls
give keyboard/SR a11y; state-driving radios hidden by clip (never `display:none`).
Added a single-source **semantic color palette** `SEMANTIC_PALETTE` in `html_renderer.py`
(`--c-addr/val/type/const/err`, all ≥4.5:1 on white — amber tightest at 4.87:1), injected
into the theme `:root` and reused verbatim by the SVG palette so chrome and diagrams share
one contrast-vetted language; color is always redundant with text + border/icon.
TDD throughout (RED before GREEN, per feedback/testing.md): parametrized shared-invariant
tests (purity, id-namespacing, CSS-id-safety, zero-JS/network, focus-preservation,
color-not-alone) run across every registered component; the gallery bakes **real
g++-captured** stdout/stderr and fails early if `g++` is missing. Suite: **312 passed**
(130 prior + 177 component + 5 gallery). Ready for `/opsx:verify` → archive.

## 2026-06-29 22:19 — Lessons-learned analysis + session handoff

Produced two reference artifacts (no code change). `LESSONS_LEARNED_2026-06-29_22h11mEST.md`
(repo root): synthesized from a parallel deep read of the DPG interface (`app_base.py`) and the
HTML/build pipeline — HTML-page idioms, a WCAG AA technique→success-criterion table, the
build-time bake architecture, the DPG accessibility limitations (architectural, why migration was
necessary), pitfalls (CSS-unsafe ids, stringified bools, duplicate SVG ids, panel scroll), and a
quick-start checklist. `handoffs/HANDOFF_2026-06-29_22h19mEST.md`: focus = apply the multi-sub-case
`cases` pattern to remaining gotcha topics + the deferred vetted-C++ diff; references, locked
decisions, constraints, suggested skills. No tests affected (130 still green).

## 2026-06-29 22:03 — Leave diagram column empty when there is no diagram

No-data cases (compile-failed sub-cases, `has_ptrdata=False` topics) drew a placeholder SVG
box "type=? — no diagram" under a "Memory diagram" heading — visual noise that appeared next
to every forbidden `const_taxonomy` cell. Now `_case_block` emits an empty
`<div class="diagram-col diagram-col--empty">` (no heading/figure/caption) when
`ptrdata` is present-but-empty; cases with real pointer data are unchanged, as are legacy
pre-rendered-svg variants. TDD: `TestNoDiagramLeavesEmptySpace`. Recorded + archived as
OpenSpec `2026-06-30-empty-diagram-when-absent` (ADDED requirement on `static-html-renderer`).
Suite: **130 passed**; `dist/` rebuilt → 0 placeholders; `const_taxonomy` = 4 empty + 4 real
diagram columns; 0 active changes.

## 2026-06-29 21:35 — Fix multi-case panel scroll regression

The multi-sub-case panels stacked two `.panel-grid`s inside `.panel`, but `.panels` is
`overflow:hidden` and `.panel` never scrolled — so `const_taxonomy`/`weak_cycle` clipped
their second sub-case with no scrollbar (single-case fit because code scrolls inside
`.code-col`). Fix (CSS only): `.panel { overflow-y:auto }`, plus `.case .panel-grid {
height:auto }` and `.case` diagram `min-height:200px` so each stacked sub-case keeps a
usable diagram height; single-case unaffected. TDD: `test_multicase_panel_scrolls`.
Recorded + archived as OpenSpec change `2026-06-30-multicase-panel-scroll` (ADDED
"Stacked sub-cases remain scrollable" to the `multi-subcase-panels` capability). Suite:
**126 passed**; `dist/` rebuilt; 0 active changes.

## 2026-06-29 20:50 — Multi-sub-case panels, const-taxonomy redesign, two bug fixes, OpenSpec reconciliation

Static-HTML C++ ptr lab. Two root-caused bug fixes: blank variant panels (CSS-unsafe
`(`/`)`/`,` in element ids broke the `:checked ~` selector) and a bare `False` in generated
C++ (checkbox default stringified instead of resolving via `value_map`). Added a reusable
**multi-sub-case panel** capability — one panel holds N independently-compiled cases, each
with its own code/verdict/output/diagram; failing cases get a red-bordered output box.
Applied it to redesign `const_taxonomy` from 4 inert near-identical programs into the real
const **2×2 truth table** (type × {write, rebind}) with authentic g++ errors. Then
reconciled OpenSpec: archived two stale-but-implemented changes and authored+archived
`2026-06-29-multi-subcase-panels` recording the capability plus both fixes as spec
invariants. All work TDD (RED→GREEN). Suite: **125 passed**; `dist/` rebuilt; `openspec
validate --specs` → 11 passed; 0 active changes.

### Details

**Bug fixes (regression-tested):**
- *Empty panels* — `_vid` left `(` `)` `,` in ids; unescaped these are CSS `#id`-selector
  errors (`(` parse error, `,` splits selector), silently dropping `:checked ~ .panels`
  for `const_taxonomy`/`weak_cycle`. Fix: map non-`[A-Za-z0-9_-]` → `_`. Test:
  `test_ids_are_css_safe_with_punctuated_labels`.
- *Bare `False`* — `expand_variants` seeded checkbox defaults via `str(ctrl.default)` →
  `"False"`, bypassing `_resolve_control_value`'s bool branch + lowercase `value_map` →
  undeclared identifier (compile failure on `const_taxonomy`/`ref_const`). Fix: preserve
  the default's type. Test: `test_checkbox_default_false_resolves_via_value_map`.

**Feature — multi-sub-case panels (additive, backward-compatible):** `CaseDef(label, subs)`
+ `TopicTemplate.cases`; `generate_source(extra_subs=)`; `capture_variant` compiles one
program per case (`_compile_one` extracted); `_panel_body` renders per case (`_case_block`
extracted, unique svg-id prefix `-c{j}`); failing case adds `.out--err` (2px red border).

**Content — `const_taxonomy`:** 4 type tabs (`<<decl>>`) × 2 ops (`*ptr=99` / `ptr=&other`)
compiled independently; `int other = 7;` added; `mutate` checkbox dropped; explanation
rewritten around the two const axes. Truth table verified by
`test_lab1_const_taxonomy_truth_table` (real g++, no `-Werror` so unused `other` is fine).

**OpenSpec reconciliation:** archived `cpp-ptr-lab-static-html` + `html-renderer-tab-layout`
(fixed a `SHALL`-on-second-line parser error in the latter). Authored+archived
`2026-06-29-multi-subcase-panels`: new `multi-subcase-panels` capability (5 reqs) + ADDED
invariants on `static-html-renderer` (CSS-safe ids) and `static-html-build` (bool default
resolution).

## 2026-06-28 21:28 — Project initialized

- Project created at `/Users/erlebach/src/2026/isc5305_f2026/opencode`
