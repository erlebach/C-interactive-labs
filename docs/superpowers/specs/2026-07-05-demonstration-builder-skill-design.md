# Design: `demonstration-builder` skill

**Date:** 2026-07-05
**Status:** approved (brainstorming complete; awaiting implementation plan)
**Branch:** `skill/demonstration-builder`

## Problem

Building one C++ teaching page ("demonstration") in `cpp_labs/` follows a rich,
recurring pattern — topic/demo/layout/glossary YAML shapes, the `<<placeholder>>`
substitution rules, `controls`/`cases`, the `PTRDATA:` memory-diagram convention,
locked C++ style, diagram gating, and a fixed family of tests. That pattern is
currently captured only as static prose in `cpp_labs/SKILL_PREPARATION.md`, so each
new subject re-discovers it by hand. We want that knowledge to become an **executable,
triggerable skill** so authoring a new demonstration is a guided, repeatable workflow.

## Goal

A **project-local skill** that, when invoked, interactively guides the agent + author
to build one new `cpp_labs` demonstration from the locked pattern, then builds and
verifies it with the real g++-at-build-time engine. The first concrete deliverable is
to **use the skill to produce one template demonstration** that builds clean and whose
tests pass.

## Non-goals (v1)

- **Not** a generative diagram engine for new SVG families (linked lists, graphs,
  trees). That is a separate, future **`diagram-generation` sub-skill**; this skill
  documents the seam where it will attach.
- **Not** a course-assembly skill (an index page stitching many demonstrations
  together). That is the layer *above* this one; noted as future work.
- **Not** an engine copy or engine refactor. v1 references the in-repo `cpp_labs/`
  engine as the single source of truth.

## Decisions (from brainstorming)

1. **Engine relationship — reference in-repo (start), bundle later.**
   v1's skill calls the existing `cpp_labs/` engine where it already lives; the skill
   is only usable inside this repo. Once it works, a later revision may vendor a
   self-contained copy under the skill dir for portability to other course repos.

2. **Workflow — interactive author-guide with proactive suggestions.**
   Invoking the skill drives a short dialogue: the author states the subject and may
   paste example code and/or offer images; the skill *proposes* the example set,
   gotchas, and diagram (offering suggestions when the author doesn't), then generates
   the YAML, builds, and verifies. Optimized for the established "user drafts, agent
   polishes" flow.

3. **Diagram triage — a general question, keyed on renderer availability, NOT on
   pointers.** The organizing question is pedagogical: *does this subject have a
   spatial/structural mental model worth drawing?* Pointers are **not** privileged —
   they are simply the only family for which a renderer happens to exist today. The three
   cases are keyed on whether a renderer already exists, and the skill suggests a diagram
   when the author doesn't:
   - **Case 1 — a diagram helps AND a built-in renderer already fits.** The built-in
     inventory currently spans **two families**: (a) the 6 memory renderers
     (`raw`/`null`/`ref`/`unique`/`shared`/`weak`), and (b) the **stackframe family** —
     `_svg_frames` (`type=frames`), per-frame `_svg_frames_anatomy`, and the process
     `_svg_memmap` (`type=memmap`). In practice this covers pointer/reference/
     smart-pointer topics *and* call-stack / memory-layout topics. Skill picks the
     `type=` and emits the `PTRDATA:` line. Works today.
   - **Case 2 — a diagram helps but no renderer exists yet.** This is the *common* case
     for the rest of a C++ course: linked lists, graphs, trees, call/stack frames, array
     & vector memory layout, class composition, iterator ranges, and more. The skill
     suggests the diagram; if the author provides an image (or the agent can sketch one),
     the skill **redraws it as a hand-authored SVG** in the vertical-diagram style
     (wrapped via `_wrap_svg`) — the manual seed of the future diagram-generation
     sub-skill — otherwise it falls back to **`diagram: false`** (concept prose fills the
     right column).
   - **Case 3 — no diagram helps** → `diagram: false`.

   The built-in inventory (memory + stackframe families) is **not** a pedagogical
   ranking — it is just what has been built to date. It is still narrow relative to the
   many structural subjects (lists, graphs, trees, iterator ranges, class composition),
   most of which fall in Case 2 today; growing the inventory is exactly the
   `diagram-generation` sub-skill's job.

3b. **Diagram interactivity is available and OPTIONAL — and it is diagram-agnostic.**
   A static SVG is a perfectly good default; the skill should *offer* interactivity, not
   impose it. The engine already provides a reusable, **zero-JS** interaction layer
   (CSS-radio + native `<details>`, so it degrades gracefully and works JS-off), and
   these compositors wrap *any* SVG — not just the stackframe ones:
   - **Stepper** — `stepped_frames(comp_id, steps, with_anatomy=)`: ordered
     student-paced snapshot reveals; elements present at a deeper step but gone at the
     current one draw **ghosted** (reclaimed). This is the general mechanism for changing
     **emphasis / connectivity / shape across ordered states**.
   - **Enlarge / zoom** — `zoomable(comp_id, inner_html, label=)`: click-to-fullscreen
     overlay with 0.5× / 0.75× / 1× / 1.5× / 2× zoom-level radios that scale the whole
     panel as a unit (the "expanded / zoomed-up figure"). The same `inner_html` is
     promoted, so nested SVGs keep their one-to-one `role="img"` and stay interactive.
   - **More detail below/within** — `frames_anatomy_details(comp_id, pd)` and
     `progressive_steps(comp_id, steps)`: native `<details>` disclosures that reveal an
     expanded, more-detailed view (e.g. full per-frame anatomy) beneath the figure.
   - **Toggle / tabs** — `before_after_toggle`, `variant_tabs`: switch a diagram between
     two or more states (before/after, per-variant).

   Because each is "a radio/`<details>` selects a state, CSS restyles the SVG," the same
   patterns generalize to changing **colors, emphasis, shapes, or connectivity** on a
   Case-2 hand-drawn SVG too. The skill's DIAGRAMS.md catalogs both renderer families
   **and** this interaction layer, and the workflow asks the author whether a diagram
   should be static or gain a stepper / enlarge / detail-reveal.

4. **Case-2 engine support deferred.**
   Injecting a hand-authored/static custom SVG into the diagram column may need a small
   new engine block. Since the v1 deliverable is `diagram:false`, this path is
   **documented, not built** — deferred until a real case-2 subject needs it. Keeps v1
   pure-authoring with zero engine change.

5. **First deliverable — a generic reference template.**
   Run the skill to produce `cpp_labs/template_subject/`: ~2 examples + 1 gotcha + a
   concept, `diagram: false`, full tests. It is the honest proof the generation path
   works, and doubles as the copy-me exemplar the skill points authors to.

## Skill structure

```
.claude/skills/demonstration-builder/
  SKILL.md                 # lean: trigger + the interactive workflow
  reference/
    PATTERN.md             # distilled SKILL_PREPARATION.md — YAML shapes, placeholders,
                           #   controls/cases, PTRDATA, locked C++ style, page/layout wiring
    DIAGRAMS.md            # the 3-case diagram decision; renderer catalog (memory +
                           #   stackframe families); the zero-JS interaction layer
                           #   (stepper / zoom / detail-reveal / toggle); case-2 seam
    CHECKLIST.md           # the build + verify checklist
  templates/
    topic.topic.yaml       # annotated skeletons the agent copies & fills
    demo.demo.yaml
    layout.rail.yaml
    test_subject.py
```

`SKILL.md` stays short; the heavy reference under `reference/` is loaded on demand
(progressive disclosure). The templates are literal starting files the workflow copies
into `cpp_labs/<subject>/` and fills.

## Workflow (what `SKILL.md` drives)

1. **Elicit the subject** — name, one-line goal, the C++ concepts to teach. Author may
   paste example code and/or offer images.
2. **Propose the example set** — skill suggests 2–4 examples + **≥1 gotcha** (a
   deliberate compile or runtime failure), author confirms/adjusts.
3. **Diagram triage** — the 3-case decision above; skill suggests whether a diagram
   helps and what kind.
4. **Generate** `topics/ demos/ layouts/ tests/` YAML into `cpp_labs/<subject>/` from
   the templates, in the locked C++ style (`class` not `struct`; comments above code;
   long `<<` chains broken and aligned).
5. **Build + verify** — `./build_labs.sh <subject>`, then
   `pytest cpp_labs/<subject>/tests/ -q`; report the *real* baked output.
6. **Iterate** until the build is clean and tests are green.

## Authoring methodology (superpowers + borrowed skill-creator guidance)

We build on the **superpowers** track (brainstorm → spec → plan → TDD), because we've
already invested in this design and it fits the repo's `docs/superpowers/` convention.
But `skill-creator` (and `superpowers:writing-skills`) carry skill-specific wisdom the
general brainstorming flow does not, and we fold these in at the build step:

- **SKILL.md anatomy + progressive disclosure** — keep `SKILL.md` lean (< ~500 lines),
  push heavy material into `reference/` loaded on demand, bundle reusable starting files
  under `templates/`. This matches the structure in §"Skill structure" above.
- **A "pushy" `description` field** — the frontmatter `description` is the primary
  trigger mechanism and Claude tends to *under*-trigger. Write it to fire whenever an
  author starts, drafts, or asks to build a new `cpp_labs` demonstration/subject/topic,
  not only when they name the skill.
- **Explain the *why*** — prefer reasoned guidance over rigid ALWAYS/NEVER; the model
  follows a harness better when it understands intent.

## Testing

The generated `template_subject/tests/` follows the §9 families of the prep guide:
self-contained (`<!DOCTYPE html>`, no external `src`/`href`); exact baked stdout
(byte-for-byte); the WCAG diagram-gating invariant `count("<svg") == count('role="img"')`;
the gotcha surfaces a real compiler-error box (`out--err`); DOM id uniqueness.

**The skill is validated when the deliverable `cpp_labs/template_subject/` builds clean
and its tests pass.**

## Future work (documented seams)

- **`diagram-generation` sub-skill** — turns an author concept/image into a new SVG
  renderer family; `demonstration-builder` composes it (DIAGRAMS.md marks the seam).
- **Course-assembly skill** — stitches many demonstration HTMLs into an index/linked
  course.
- **Engine bundling (option 2)** — vendor a self-contained engine copy under the skill
  for portability once v1 is proven.
- **`skill-creator` eval loop (optional validation)** — once v1 is green, optionally run
  `skill-creator`'s empirical harness: give Claude the skill vs. a baseline on several
  realistic "build me a demonstration for X" prompts, benchmark quantitatively, review,
  and iterate. Proves the skill reliably produces a green demonstration across varied
  prompts (not just our single `template_subject` deliverable), and can drive the
  `description`-triggering optimizer.
