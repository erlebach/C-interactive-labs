<!--
  Applying memory rule feedback/testing.md: RED tests written BEFORE implementation.
  Items [x] were completed in the 2026-06-29 session; the red-border items were
  authored as this change and implemented test-first after it.
-->

## 1. RED — sub-case model tests

- [x] 1.1 `test_code_generator.py`: `CaseDef` holds label/subs; `TopicTemplate.cases` defaults `None`; `generate_source(extra_subs=)` fills `<<op>>`
- [x] 1.2 `test_build_html.py` `TestCaptureVariantCases`: variant gains `cases` list; each case has label + result keys; source reflects its subs; no `cases` key when topic has none
- [x] 1.3 `test_html_renderer.py` `TestRenderFragmentMultiCase`: case labels present; one code block per case; failing case shows compile-failure + stderr; passing case shows stdout; no duplicate ids
- [x] 1.4 `test_integration.py` `test_lab1_const_taxonomy_truth_table`: 4 variants × 2 cases, forbidden combos fail to compile
- [x] 1.5 Confirm all the above FAIL for the right reason before implementing

## 2. GREEN — data model (`code_generator.py`)

- [x] 2.1 Add `CaseDef(label, subs)` dataclass and `TopicTemplate.cases` field
- [x] 2.2 Add `extra_subs` param to `generate_source`, applied after control resolution

## 3. GREEN — build (`build_html.py`)

- [x] 3.1 Extract `_compile_one(topic, control_state, extra_subs)`
- [x] 3.2 `capture_variant` compiles one program per `CaseDef` and bundles `cases`; single-case path unchanged

## 4. GREEN — render (`html_renderer.py`)

- [x] 4.1 Extract `_case_block(result, svg_id_prefix)` from the former panel body
- [x] 4.2 `_panel_body` renders one labelled block per case with a unique svg-id prefix; single-case unchanged

## 5. GREEN — `const_taxonomy` content (`pointers_refs/topics.py`)

- [x] 5.1 Drop `mutate` checkbox; template uses `<<decl>>` + `<<op>>`, declares `int other = 7;`
- [x] 5.2 Add two `CaseDef`s (write `*ptr = 99`, rebind `ptr = &other`); rewrite explanation around the two const axes

## 6. Recorded correctness fixes (regression-tested)

- [x] 6.1 `_vid` sanitises ids to `[A-Za-z0-9_-]`; test `test_ids_are_css_safe_with_punctuated_labels`
- [x] 6.2 `expand_variants` preserves bool default type; test `test_checkbox_default_false_resolves_via_value_map`

## 7. Failing-case error border (red/green — this change)

- [x] 7.1 RED: `test_html_renderer.py` — assert a failed sub-case's compiler-output box carries an error-border marker class, and the inlined CSS defines that class with a red border; assert a passing case keeps the neutral border. Confirm it fails.
- [x] 7.2 GREEN: in `_case_block`, add the error-border modifier class to the `.out` box when `failed`; add the CSS rule
- [x] 7.3 Run full suite green

## 8. Verification

- [x] 8.1 Full `cpp_ptr_lab` suite green
- [x] 8.2 Rebuild `dist/`; spot-check `const_taxonomy`: each type tab shows two sub-cases, forbidden ones show a red-bordered compiler-output box, allowed ones show output + diagram
- [x] 8.3 `openspec validate multi-subcase-panels` passes
