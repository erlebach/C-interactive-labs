# opencode — Journal

Chronological log of features, bug fixes, and architectural decisions.

## 2026-07-06 07:14 — demonstration-builder skill-creator polish + failed description optimizer

Post-build best-practice pass on the `demonstration-builder` skill (via `skill-creator`). **Fixed two
real correctness bugs in `SKILL.md`** (`42b8f53`): Step 5's build command was the non-runnable
`python -m cpp_labs.build_html` (→ `./build_labs.sh <subject>`), and Step 4's test path was
`cpp_labs/tests/` instead of the subject-local `cpp_labs/<subject>/tests/` (both contradicted the
skill's own `CHECKLIST.md` and the `templates/test_subject.py` path math). **Bundled
`scripts/scaffold_subject.sh`** (`a190853`) — deterministic scaffolding of a new subject that produces a
consistent, immediately buildable+green minimal page (`<subject>_ex1` → `x = 42`), refuses to clobber;
verified end-to-end on a throwaway (`built 1, failed 0`, 4 tests pass, guard refuses). Also removed a
stray untracked `demonstration-builder_bak/` duplicate. **The skill-creator description optimizer
(`run_loop.py`) FAILED and was killed:** it measured **recall=0% on every description/iteration** (the
skill never triggered under the `claude -p` eval harness → degenerate 50% accuracy everywhere, nothing
distinguishable), after ~6.5 h for 4 iterations. **No description change applied** — the committed
`SKILL.md` keeps its original hand-written pushy description. Lesson: the automated
triggering-optimizer's signal is broken here; improve the description as a reviewed manual edit (the one
good idea from the run: add an explicit "Do NOT use for engine edits / build-script fixes / engine unit
tests / diff review / general C++ Qs" negative-scope clause). Handoff:
`handoffs/HANDOFF_2026-07-06_07h14mEST.md`. Next: finish the branch.

## 2026-07-06 00:18 — demonstration-builder skill + template_subject exemplar

Built `.claude/skills/demonstration-builder/`: lean `SKILL.md` (pushy trigger + 6-step authoring
workflow), three reference docs (`PATTERN.md` = YAML anatomy + test families; `DIAGRAMS.md` = renderer
triage + two renderer families + zero-JS interaction layer; `CHECKLIST.md` = ordered build/verify
commands), and copy-me `templates/` skeletons. Zero engine code change — skill references the existing
`cpp_labs/` engine. Validated by authoring the worked exemplar `cpp_labs/template_subject/` (examples
`ts_value` dropdown-variants + `ts_method` plain class; gotcha `ts_gotcha` Correct/Mistake pair; all
`diagram: false`; TDD against exact baked g++ stdout). Guard test
`cpp_labs/tests/test_demonstration_skill.py` checks skeletons parse, reference files present, frontmatter
valid. Deferred: case-2 SVG-redraw engine block, interactive-diagram template components, engine bundling,
skill-creator eval loop. Verification: **built 10, failed 0**; targeted suite **9 passed**; full engine
suite **391 passed**; interface-catalog **4 passed**. Spec/plan: `docs/superpowers/specs/` and
`docs/superpowers/plans/` dated 2026-07-05.

### Details

- Skill structure: `SKILL.md` + `reference/{PATTERN,DIAGRAMS,CHECKLIST}.md` + `templates/{topic.yaml,
  test_topic.py, layout.rail.yaml}`. Authoring intent: user drafts YAML, agent polishes; no Python touch.
- `ts_value`: 3 dropdown variants (stack/heap/init) showing value-category mechanics.
- `ts_method`: single-variant class with member function, plain concept aside.
- `ts_gotcha`: compile-error gotcha using Correct/Mistake `sub_cases` pattern.
- Spec: `docs/superpowers/specs/2026-07-05-demonstration-builder-skill-design.md`
- Plan: `docs/superpowers/plans/2026-07-05-demonstration-builder-skill.md`

## 2026-07-05 20:43 — C++ standard variant axis + std_variants subject (PR opened)

Built the long-deferred **per-C++-standard axis** (brainstorm → spec → plan → subagent-driven, 13
commits on `feat/std-variant-axis`, PR opened). A topic declares `standards: [11,17,20]` and the engine
compiles the SAME source under each `-std`, rendering zero-JS CSS-radio tabs (`C++11 | C++17 | C++20`)
— red compile-error badge on the old standard, green output on the new. Engine is +40 lines threading a
`std="c++20"` param through `compiler_runner.py` and a `standards` field + `__std__` variant states
through `code_generator`/`topic_yaml`/`build_html`; **default stays `c++20`, so every pre-existing page
is byte-for-byte unchanged.** New subject `cpp_labs/std_variants/` = **8 demos** (C++14/17/20, language
+ library) + a **Main Takeaway** demonstration concept. Also unified the per-example concept label on
`diagram:false` pages "Concept"→**"Key Idea"**. Full suite **539 passed**; std_variants integration
**4/4**; `./build_labs.sh` **built 9, failed 0**. Handoff:
`handoffs/HANDOFF_2026-07-05_20h43mEST.md`; spec/plan under `docs/superpowers/`.

### Details

**KEY GOTCHA (locked):** Apple clang only *warns* (compiles green) on many "modern" features —
structured bindings, `string_view`, `if constexpr`, fold expressions, designated init, variable
templates, inline static vars — so they are **unusable** for the red/green demo; `std::bit_cast` and
`std::ranges` are **unsupported even at C++20** on this libc++. Every candidate feature must be
**empirically verified to hard-error in `/tmp` before authoring** (compile under old `-std` → expect
failure; under new → expect compile + expected stdout).

**The 8 demos:** auto-return (C++14 lang), make_unique (C++14 lib), optional (C++17 lib), variant
(C++17 lib), filesystem (C++17 lib), span (C++20 lib), concepts (C++20 lang), `<=>` (C++20 lang).

**Decisions:** teach C++20 as the baseline; keep the axis as ONE small standards-awareness subject, not
sprinkled across every demo (standards-sensitive code is the exception, so tabs elsewhere = noise).
Standards-only rule (no competing dropdown; duplicates rejected). Label taxonomy: demonstration
objective = **Main Takeaway** (`concept_panel`), per-example = **Key Idea** (both `concept_note` toggle
and `code_concept_panel` aside). Changing a component *default value* (not signature) needs no interface
-catalog regen — `test_interface_catalog` stayed green.

**Key commits:** `d2f99c3` (-std param) · `df91bc7` (standards field + validation) · `d74282f`/`d4d8415`
(variant expansion + label/compile) · `3c2186b` (optional demo) · `31fcacc`/`6c4085f` (6 more demos) ·
`b34af25` (Main Takeaway) · `8f15755` (Key Idea unify).

## 2026-07-05 17:33 — stackframes-ux merged (PR #5); branch cleaned

Closes out the stackframes UX + accessibility work. Final tweak before merge: aligned the header
Keyboard/Monochrome chips (reset `details.kbd-help{margin:0}` — the global `details{margin-top:.5rem}`
had nudged the `<details>`-based chip down vs the `<label>`) and bumped both chips to 16px (+23%). Full
`cpp_labs` suite **522 passed** (a final run caught 3 stale `yaml_engine/test_render_page.py` assertions
from the label rename + the always-on keyboard-help `<details>` — updated). **PR #5 merged** into `main`
(`eb60c2b`); `feat/stackframes-ux` deleted local + remote. Supersedes the prior entry's "not merged"
note. Stackframes is done for now. Handoff: `handoffs/HANDOFF_2026-07-05_17h18mEST.md`.


## 2026-07-05 14:10 — Accessibility pass: contrast, monochrome toggle, focus, keyboard help, labels

Series of a11y improvements on `feat/stackframes-ux` (browser-verified with Playwright), prompted by
SiteImprove/keyboard review. **(1) Contrast (real AA fix):** green `#2a8a5a`→`#2a7f54` (white-on-green
4.3→4.9:1) for active step/zoom buttons + the diagram axis. **(2) Monochrome code toggle:** zero-JS
header-row chip (`page_shell`, gated on highlight) that forces every hljs token to inherit the base
colour — an accessible single-colour view (best-practice accommodation; the SIA-R79 badge itself is an
Alfa over-eager heuristic on highlighted code, not a real failure — see MEMORY note). **(3) Focus
visible (WCAG 2.4.7):** the stepper step buttons and zoom-level buttons hid their radios and weren't
showing keyboard focus; added `:focus-visible ~ label` outlines (rail/tabs already had them). Verified
by real Tab navigation. **(4) Keyboard help:** a visible zero-JS `<details>` "⌨ Keyboard" chip in the
header (floats open → no vertical space) documenting Tab/arrows/Enter — for sighted keyboard users.
**(5) Group semantics:** `role="group"`+`aria-label` on the stepper and zoom bars (the rail already had
it) so screen readers announce the group purpose natively. **(6) Labels:** per-example concept chip
"Concept"→**"Key Idea"**; sidebar demonstration concept "Concept"→**"Main Takeaway"**. Full suite 374
passed; all 8 pages build. Branch kept (not merged).

### Details

Files: `components.py` (`page_shell` header tools + `_KBD_HELP_HTML` + `_MONO_TOGGLE_CSS` + COMPONENT_CSS
header/kbd CSS; `stepped_frames` focus + `role=group`; `zoomable` focus + `role=group`; `concept_note`
default label), `html_renderer.py` (`_ADDR_AXIS` colour), `render_page.py` (`_build_concept` +
sidebar-concept label defaults). Design notes: keyboard-nav hints are for SIGHTED keyboard users (SR
users get the model from roles/names), so the help is VISIBLE, not sr-only. The mono toggle does NOT
clear SIA-R79 (spans persist) — it provides the accessible view. Zero-JS throughout except the existing
highlight.js. All new controls: 3px accent focus ring, ≥36px targets, `:has()`/`~` CSS only.


## 2026-07-05 12:38 — zoom simplified: scale the whole right panel as one unit (CSS `zoom`)

Karpathy pass on user feedback: the enlarge overlay had been resizing each SVG by height, which changed
the frame↔anatomy relationship and caused per-step shifts. Replaced all of that with the simplest thing
that works — a single CSS `zoom:N` on the whole `.zoom-content` panel (the entire right panel, already
one wrapper). Levels are now plain multipliers 0.5× / 0.75× / 1× / 1.5× / 2× (default 1.5×); the panel
scales as one unit so every internal relationship and the Image-5 layout are preserved. Net **removed**
~5 CSS rules (per-SVG height `!important`, block-centering, sf-steps centering). **Playwright-verified
(1400×900):** frame/anatomy width ratio identical at 1× and 2× (1.07), 2× is exactly 2× on both,
switching steps at 2× shifts 0px. Engine suite 367 green. Branch `feat/stackframes-ux` (kept). Note:
uses the CSS `zoom` property (Chrome/Safari always; Firefox 126+, fine in 2026).


## 2026-07-05 12:24 — fix: no per-step horizontal shift in the zoom overlay

User saw the stack-frame diagram + anatomy jump horizontally when clicking step radios in enlarged
mode (not in normal mode). Cause: the overlay forces SVG *height* with `width:auto`, so each step's
per-step anatomy (different frame count → different viewBox aspect) got a different auto width; with
`.zoom-content { width:fit-content; margin:0 auto }` that width change re-centered the whole block.
Fix: stable `width:100%` content box + block-center each SVG (`margin-inline:auto`) and center
`.sf-steps`, so all steps share one center axis. **Playwright-verified (1280×900):** frame diagram
left/center identical across steps (267/640), anatomy center stable at 640 even as its width changes
(1064→637px). Engine suite 367 green. Branch `feat/stackframes-ux` (kept).


## 2026-07-05 12:12 — zoom: 5 levels (0.5×–2×), Fit=40% base, mobile-verified

Per user follow-up on the zoomable lightbox: added 0.5×/0.75× levels, changed Fit to **40% of window
height** (was 60%), and verified mobile. Zoom levels are now 0.5× / 0.75× / **Fit** / 1.5× / 2× =
20/30/40/60/80 vh — all multiples of the fixed 40vh Fit base (never compounding off an enlarged state).
Toolbar `flex-wrap`s with 44px touch targets; refactored to a `levels` list. **Playwright-verified on a
390×844 phone:** no horizontal overflow (scrollWidth == viewport), code/diagram panel reflows to one
column, Fit=338px (40% of 844), 0.5×=169 / 2×=675, all buttons ≥44px, toolbar within viewport, stepper
works in the overlay, backdrop closes. Engine suite 367 green. Branch `feat/stackframes-ux` (kept).


## 2026-07-05 11:51 — zoomable fix: actually enlarges (fill-to-fit + 1.5×/2×), stepper works in overlay

Follow-up on user feedback that the ⤢ Enlarge lightbox opened but the diagram **didn't grow** and the
stepper was **dead** in the overlay. Two real defects, both fixed: (1) every wrapped SVG carries an
inline `max-width:{viewBox}px` cap that beat the overlay stylesheet, so the diagram never scaled — now
overridden with `width:auto/max-width:none !important` and sized to the viewport; (2) the full-area
`.zoom-backdrop` sat above the content, so every click closed the overlay — now the diagram lives in a
`.zoom-content` stacked ABOVE the backdrop (z-index), so the stepper radios work and only clicks in the
surrounding backdrop / the ✕ close it. Added zero-JS **Fit / 1.5× / 2×** zoom-level radios (Fit fills
the viewport, default). **Verified in a real browser (Playwright, 1280×800):** frame diagram 155px →
**688px** (Fit) → **1376px** (2×); clicking a step in the overlay switches the view and keeps it open;
backdrop click closes. Engine suite 367 + stackframes subject 13 green. Branch `feat/stackframes-ux`
(kept, not merged).


## 2026-07-05 11:34 — stackframes UX: step-synced anatomy, memory glossary, zoom lightbox

Three post-review improvements to the shipped `stackframes` demonstration, brainstorm → spec → plan →
**subagent-driven** execution (Sonnet implementers, per-task diff review + a final holistic review
subagent). **(1) Bug fix:** "Show full frame anatomy" only showed `main()` — it was fed the *first*
PTRDATA snapshot. Now folded into `stepped_frames(..., with_anatomy=True)`: one anatomy table per step,
gated by the same step radios, so it shows exactly the frames live at the selected step. **(2) Memory
glossary:** new general `glossary_note` inline chip (same look as the Concept chip) + `glossary_note`
YAML block; the memory-map demo defines text/data/bss/heap/stack/segment. **(3) Zoom + size:** new
zero-JS `zoomable` CSS lightbox (checkbox promotes the *same* container to a fixed overlay — no DOM
duplication, WCAG `svg==role` preserved; click/✕ to close, no ESC) and a wider `(2,1)` diagram column
for frames/memmap via a new `code_diagram_panel(ratio=)` arg. **Verification:** full `cpp_labs` suite
**512 passed**; all 8 pages build; built page svg==role 53/53, unique ids, chips gap correctly. Six
pointer renderers unaffected (final `else` path, 3:1, no zoomable). Branch `feat/stackframes-ux`.
Handoff: `handoffs/HANDOFF_2026-07-05_11h34mEST.md`.

### Details

**Files:** `components.py` (`code_diagram_panel` +`ratio`; `stepped_frames` +`with_anatomy`;
`_demo_variant_body` rewire; new `glossary_note`, `zoomable`), `html_renderer.py` (chip-row `:has()`
CSS, scoped so lone Concept chips are untouched), `render_page.py` (`_build_glossary_note` +`_BUILDERS`),
`interface_catalog.py` (registered `glossary_note` in `_TIER` + `_BUILDER_INFO` — the drift guard caught
the missing rows; `INTERFACE_ELEMENTS.md` regenerated), `sf_memmap.demo.yaml`. **Final-review finding
fixed:** the chip-row gap (`margin-right` in the stylesheet) was defeated by the chips' inline
`margin` shorthand; moved the gap to the glossary chip's inline left-margin (`.6rem`) and dropped the
dead rule. Added a `_demo_variant_body` unit test locking the pointer path (3:1, no zoom-body).
**Plan gap noted:** the plan didn't anticipate `_BUILDERS` additions requiring `interface_catalog`
rows, and the per-task `cpp_labs/tests/` runs excluded the catalog test — caught at the Task 7
full-suite gate; fixed with a dedicated commit.

## 2026-07-05 09:08 — stackframes subject shipped (2 SVG families + zero-JS stepper)

Executed the approved 14-task TDD plan **subagent-driven** (fresh subagent per task, controller-reviewed
each diff for scope — no contamination). New pure-YAML `stackframes` demonstration on the `left_rail`
layout with **two new SVG families** (`type=frames` stacked call-stack + anatomy table, `type=memmap`
process map) and a **zero-JS CSS-radio push/pop stepper** driven by real g++ output baked at build time.
6 rail examples (`sf_single_call`, `sf_nested`, `sf_locals` 2-tab, `sf_recursion`, `sf_dangling_local`
gotcha, `sf_memmap`) share an inlined frame-tracer printing deterministic enter/leave traces + one
PTRDATA snapshot per call/return (addresses drawn, never asserted). Engine additions are all additive —
the six pointer renderers are untouched. **Verification:** full `cpp_labs` suite **500 passed** (prior
476 + 24 new); all 8 pages rebuild (`built 8, failed 0`); built page = 36 stepper radios, 5 anatomy
disclosures, svg==role 32/32 (WCAG), self-contained. Branch `feat/stackframes`.
Handoff: `handoffs/HANDOFF_2026-07-05_09h08mEST.md`.

### Details

**Phase 1 (engine, 5 commits):** `parse_ptrdata_all` reads EVERY `PTRDATA:` line (additive; first-line
`parse_ptrdata` untouched). `html_renderer`: `_svg_frames`/`_frames_core` (vertical stack, main on top at
highest address, SP marker on innermost, **dual axis — addresses increase upward / stack grows downward**,
`solid=` prefix count ghosts reclaimed frames), `_svg_frames_anatomy` (per-frame slot·address·size table,
measured local red, schematic param/retaddr/saved-FP grey), `_svg_memmap` (text→stack). `components.py`:
`stepped_frames` CSS-radio stepper + `frames_anatomy_details` `<details>`; `_demo_variant_body` branches
frames/steps, pointer subjects (no `ptrdata_steps`) keep the old path. `ptrdata_steps` baked through
`build_html._compile_one` (all 3 return branches) + `render_page._bake_program`. New additive
`TopicTemplate.extra_compile_flags` threaded via `topic_yaml` → `_compile_one`.

**Phase 2 (pure YAML, 8 commits):** the 6 topics/demos + glossary + rail layout.

**Host notes (Apple clang aliased as g++):** dangling gotcha compiles with `-Werror=return-local-addr` →
real red compile-error box; the host diagnostic reads `reference to stack memory associated with local
variable` (the subject test asserts that OR the GNU `return-local-addr`/`reference to local` spellings).
`sf_memmap` loads the five addresses into `uintptr_t` locals before comparing to dodge the
`<`-parsed-as-template-bracket error; all four ordering booleans (`text<data<bss<heap<stack`) print `1`.
Interface-catalog regen produced no diff (`stepped_frames`/`frames_anatomy_details` are internal, not
`_DISPATCH` block keywords).

## 2026-07-04 23:59 — stackframes: brainstorm → spec → plan (design only, no code)

Design session for a new `stackframes` demonstration on the **left_rail** layout. Brainstormed
with the visual companion, wrote the spec, wrote a 14-task TDD implementation plan — **no
implementation code yet**; both artifacts committed on `feat/stackframes` (spec `3136437`, plan
`4297919`). Design locks 6 rail examples, **two new SVG families** (`type=frames`, `type=memmap`),
and a **zero-JS push/pop stepper**. Next: execute the plan **subagent-driven** from Task 1.
Spec: `docs/superpowers/specs/2026-07-04-stackframes-design.md`; plan:
`docs/superpowers/plans/2026-07-04-stackframes.md`; handoff:
`handoffs/HANDOFF_2026-07-04_23h59mEST.md`.

### Details

- **Examples:** `sf_single_call`, `sf_nested`, `sf_locals` (two tabs), `sf_recursion`,
  `sf_dangling_local` (gotcha), `sf_memmap`.
- **Stepper:** program emits one `PTRDATA` line per call/return → `parse_ptrdata_all` (additive;
  first-line `parse_ptrdata` untouched) → one SVG per step behind a CSS-radio control. A reusable
  C++ **frame-tracer** snippet produces the deterministic trace.
- **Diagram convention:** high-memory-on-top / SP-at-bottom, dual axis (**addresses ↑ / stack ↓**),
  clean real-address default + **full frame anatomy** in `<details>` with per-slot byte sizes and
  per-row addresses (measured local red, schematic slots grey).
- **Determinism contract:** traces + `sizeof`-derived sizes + memmap ordering booleans baked &
  asserted; raw addresses drawn but never asserted.
- **Gotcha** via `-Werror=return-local-addr` (no ASan run-env) → red compile-error box; needs one
  additive `extra_compile_flags` field on `TopicTemplate`.
- **Open issue flagged in handoff:** `-std=c++20` is hardcoded in `compiler_runner.py` (9 sites);
  a per-standard variant axis (11/14/17/20) remains deferred future work — stackframes itself is
  C++11-agnostic, so not a blocker.

## 2026-07-04 22:49 — Vertical memory diagrams, SKILL_PREPARATION.md, +4 function_args examples

Three merged workstreams. **(1)** Re-oriented every SVG memory diagram horizontal→vertical via one `_stack_svg(sources, target)` helper encoding the **source-count rule** (≤2 converge, ≥3 stack); native `<marker>` arrowheads; 14px box text matching the code panel; `code_diagram_panel` **2fr:1fr → 3fr:1fr**; `hover_link_diagram` reuses `_stack_svg`; ptrdata-less variants get an **empty right cell (not the `type=? — no diagram` placeholder) with the code-column width held constant** (merge `c27444b`). **(2)** `cpp_labs/SKILL_PREPARATION.md` — the reusable demonstration-authoring guide, precursor to the future *demonstration* skill (`04c129e`). **(3)** Four new `function_args` examples — const ref (+compile-error gotcha), swap (works vs no-op), output params, copy cost — the guide's first use (merge `221607f`, commit `e2387fb`). Full `cpp_labs` suite **476 passed**; all 7 pages rebuilt. Next (brainstorm first): a `stackframes` demonstration on the **left_rail** layout. Handoff: `handoffs/HANDOFF_2026-07-04_22h49mEST.md`.

### Details

- **Vertical diagrams:** the seven hand-placed `_svg_*` renderers became thin adapters over `_stack_svg`; arrowheads use `<marker orient="auto-start-reverse">` (SVG has no arrow primitive — the old code hand-drew a horizontal polygon locked at `mid_y=y1`). The SVG is capped at its intrinsic width (`max-width` + `height:auto`) so 14 user-units ≈ 14px. `hover_link_diagram` overlay CSS got WCAG fixes: `:focus:not(:focus-visible)` preserves the keyboard focus ring; the focusable `<figure>` gained an `aria-label`. Spec `docs/superpowers/specs/2026-07-04-vertical-memory-diagrams-design.md`; plan `docs/superpowers/plans/2026-07-04-vertical-memory-diagrams.md`. Executed subagent-driven with two-stage (spec + quality) review — a fix-subagent committed a regression from a contaminated working tree (`e3e0062`, reverted the vertical refactor) that the spec reviewer's viewBox test caught and `7c5e9ea` corrected. Layout rule locked as feedback `~/.claude/memory/feedback/lab-layout-stability.md`.
- **SKILL_PREPARATION.md** covers: topic anatomy, `<<placeholder>>`/`<<HARNESS>>` substitution, controls+`value_map`, `cases:` sub-cases (compile + runtime/ASan gotchas), the PTRDATA type/keys table, `sanitize`, the two diagram-gating mechanisms, page-vs-layout wiring + block vocabulary, per-subject test conventions, locked C++ style, build commands, and add-example / new-subject checklists. Corrected one prior misconception: the topic YAML flag is `has_ptrdata` (advisory); the column-dropping `diagram:` is a **page-block** arg, not a topic field.
- **function_args examples:** `fa_const_ref`/`fa_out_param` are `diagram:true` (ref/raw diagrams; const_ref's Mistake case → empty cell); `fa_swap`/`fa_copy_cost` are `diagram:false` (full-width code + concept in the right column). All programs verified to compile with deterministic output before baking; tests assert exact stdout, Correct/Mistake pairing, the compile-error box, diagrams, and the svg==role=img invariant. Page kept **stacked** (user chose not to convert to a rail). `test_topics_loader` updated (subject is no longer single-topic); `TestPageRender` FAKE data gained stubs for the 4 new topic blocks.
- **Deferred (unchanged):** `dangling_ptr` needs `ASAN_OPTIONS=detect_stack_use_after_return=1` at run time; `cls_copy_assign` self-assignment gotcha (gated on it) — same stack-use-after-return machinery a stackframes dangling-local gotcha would need.

## 2026-07-04 16:56 — Layout space fixes, code-style pass, build script

Three coupled improvements from user screenshots. **Layout (CSS):** the whole page was capped by `.demo-wrap { max-width: 70rem }` and centered — jamming content into a narrow column with big empty margins on wide screens; bumped to **100rem**. Code `<pre>` now `white-space: pre-wrap; overflow-wrap: anywhere` so long lines wrap — **the full code is always visible, no horizontal scroll**. Widened the code column: both `code_concept_panel` and `code_diagram_panel` grids went **50/50 → 2fr:1fr** (code two-thirds, right column — concept or diagram — one-third). Removed the fixed `max-height` caps on `stacked_subcases` (32rem) and `code_diagram_panel` code col (28rem) that boxed code into small scroll-regions floating in white. **Code-style pass:** reformatted all 9 op_overload + class_structure topic templates to the locked convention — comments on their own line **above** the code (never trailing), long `std::cout`/`return os` chains **broken at `<<`** with continuations aligned; output verified **byte-identical** (subject tests assert exact stdout). **`build_labs.sh`** (new, repo root): one command rebuilds every page in `dist_labs/`, auto-discovering `cpp_labs/*/layouts/*.yaml` + `cpp_labs/*/*.page.yaml`, echoing the exact `python …` command per spec (`./build_labs.sh <filter>` for a subset). Updated the two tests that pinned the removed caps; regenerated `usage/INTERFACE_ELEMENTS.md`. Full `cpp_labs` **458 passed**. **Next (brainstorm first):** re-orient the SVG memory diagrams vertically so the code column can widen further on diagram pages, and create a skill for that work. Handoff: `handoffs/HANDOFF_2026-07-04_16h56mEST.md`.

## 2026-07-04 15:45 — Concept fills the empty right column on diagram:false pages (option 3)

On `diagram: false` subjects the right column (where a memory diagram would go) was wasted space. New component `components.code_concept_panel(main_html, concept_text, *, title="Concept")` puts the demo in the left column and the per-example **Concept** in the right as a bold-titled aside, **capped to the left column's height and scrolling internally** (`overflow-y:auto`; the aside inner is `position:absolute inset:0` so the row height is driven by the code, not the concept — reflows below on ≤760px). `demo_panel(..., concept=, concept_title=)` wraps the whole cluster **only when `concept and not diagram`** (diagram:true keeps its per-variant diagram + the concept toggle). `_build_topic` forwards `concept=args.get("concept")`. Authoring change: the 9 diagram:false demos moved the concept from the separate `- concept:` toggle block into the topic block — `- topic: { id, source, diagram: false, concept: "${src.explanation}" }` — so the old `concept_note` `<details>` toggle now serves only diagram:true demos (pointers_refs). TDD: new `TestCodeConceptPanel` (2) + `test_concept_shown_in_right_panel`; full `cpp_labs` suite **458 passed**. `code_concept_panel` is internal (not in `_DISPATCH`), so the catalog didn't need regen. Not yet committed.

## 2026-07-04 15:17 — Compile-vs-runtime failure rendering + ASan wiring; struct→class migration + gotchas

Two coupled thrusts, both driven by "make gotchas display honestly." **Engine (TDD):** **(B)** `build_html._compile_one` now classifies `error_kind` `None|"compile"|"runtime"` — a program that COMPILES but crashes/times out (`execution-error`/`execution-timeout`) is flagged `failed=True error_kind="runtime"` and rendered as an amber **⚠ Runtime error** badge + console, distinct from the red **✗ Compile failed** (was a false green "✓ Compiled" with the crash report discarded). `render_page._bake_program` threads `error_kind`; `_demo_variant_body`/`compile_status_badge`/`output_console` gained a `kind=` axis. **(C)** `output_console` folds output beyond `_OUTPUT_LINE_LIMIT=12` lines into a native `<details class="console-more">` caret disclosure (tames template/STL/ASan walls). **(sanitize)** `TopicTemplate.sanitize` was a **dead flag** — `_compile_one` never passed compiler flags; now it passes `extra_flags=["-fsanitize=address","-g"]` when `sanitize`, so runtime gotchas emit real ASan diagnostics (fixed the long-broken `null_deref`, which now shows "AddressSanitizer: SEGV…"). Also: concept toggle became a button-chip + rotating caret (cleared a `<pre>` ADA flag). **Content:** migrated every example from `struct`→`class` (locked convention: encapsulation is safer) — `op_overload` `Vec2` and `class_structure` `Point`/`Buffer` now `class` with private `x_`/`data_`/`n_`; non-member operators (`operator<<`, non-member `operator*`) are **`friend`s** (the idiom the user chose over accessors), and the `op_stream`/`op_scale` explanations now teach *why* private data forces a friend. **Gotchas (approach B, Correct/Mistake sub-case pairs):** `op_overload` — member `operator<<` + non-commutative `2.0*a` (compile errors); `class_structure` — shallow-copy **double-free** (`cls_copy_ctor`) + **use-after-move** (`cls_move_ops`), both `sanitize: true`, rendering ⚠ Runtime error with full ASan reports. New `cpp_labs/class_structure/tests/` (7); `op_overload` tests → 10. Full `cpp_labs` suite **455 passed**. **Deferred (next session):** (1) `dangling_ptr` needs `ASAN_OPTIONS=detect_stack_use_after_return=1` at *run* time to crash (run-env plumbing, separate from the compile-flag fix); (2) `cls_copy_assign` self-assignment gotcha, gated on (1). Handoff: `handoffs/HANDOFF_2026-07-04_15h17mEST.md`.

## 2026-07-04 12:15 — class_structure subject (YAML) + generated interface-element catalog

Two deliverables, both flowing from the data-over-code North Star. **(1)** Authored a new subject `cpp_labs/class_structure/` — the Rule-of-Five special members as pure YAML (5 topics `cls_ctor`/`cls_copy_ctor`/`cls_copy_assign`/`cls_move_ops`/`cls_init_list` + 5 demos + 1 glossary + 1 `left_rail` layout), structured identically to `op_overload` (`diagram: false`, `has_ptrdata: false`, real g++ output baked at build time). **Authored only — not yet built or tested** (user asked for YAML). **(2)** Built the interface-element **catalog** (option 1) TDD: new `cpp_labs/yaml_engine/interface_catalog.py` generates `usage/INTERFACE_ELEMENTS.md` by introspecting `render_page._DISPATCH`/`_BUILDERS` + `components.py` signatures/docstrings; new `test_interface_catalog.py` is the drift guard (completeness · freshness · every keyword tiered). Added a **reuse-tier** column — `generic` (12 + both sidebar), `code` (3), `cpp-memory` (4) — so a future course on another language/domain can see which elements to pilfer. Plus a plain-language design doc `usage/INTERFACE_ELEMENTS_DESIGN.md` capturing the (1)-vs-(3) distinction. `pytest cpp_labs/yaml_engine` **61 passed**. New feedback memory `feedback/spelling.md` (American spelling; correct the user's misspellings) — corrected all `catalogue`→`catalog`. Deferred: option (3) single in-code `Element` registry (kept in project memory). Handoff: `handoffs/HANDOFF_2026-07-04_12h15mEST.md`.

### Details

**class_structure** — each example is a self-contained program instrumented so g++ output *is* the lesson (which special member fires). `cls_ctor` uses a `Point` with a member-initializer list; the other four share a heap-owning `Buffer` (copy ctor deep-copies; copy assign guards self-assignment + returns `*this`; `cls_move_ops` shows move ctor **and** move assignment stealing + nulling the source; `cls_init_list` is a `std::initializer_list<int>` ctor with the brace-preference gotcha noted). Topic ids prefixed `cls_` for registry uniqueness. Interpretation locked with the user: "move operator" = both move members; "initializer operator" = initializer_list ctor.

**Catalog** — `components.py` was already the single file holding all HTML/CSS/ADA output; what was missing was an *index*. The generator is drift-proof: the catalog is never hand-edited (edit code → regenerate → `test_interface_catalog.py` fails if the committed file is stale or a keyword/tier is missing). Three tiers surfaced a real seam: `components.py` is secretly a domain-agnostic kit (`generic`) + C++ packs (`code`, `cpp-memory`). `code_line_link` tagged `code` by mechanism though its data is pointer-specific — a one-word `_TIER` flip if data-based tagging is preferred later. Option (3) (collapse the four scattered dispatch tables into one `Element` list the engine reads directly, catalog then generates from it) is designed but deferred until the scatter causes friction; staged, always-green migration path is in project MEMORY.md (2026-07-04). RST `` `` ``→`` ` `` normalization in `_purpose` keeps the generated Markdown clean.

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
