"""Tests for the subject-agnostic YAML page engine (cpp_labs.yaml_engine).

A page is a flat YAML `blocks:` list; each block names a component (or a smart
builder like `topic`) plus its inputs and an id. `render_page` translates the
list to HTML by dispatching each block to the matching component. These tests
cover the pure engine (`render_page` with pre-baked data — no g++). Per-subject
`build_page` integration tests live with each subject (e.g. basic_ptr,
function_args).

TDD: RED before GREEN (feedback/testing.md).
"""

from __future__ import annotations

import re
import shutil

import pytest

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None


class TestTopicDiscovery:
    """The registry auto-discovers every subject's ``topics/`` dir, so a new
    subject needs no Python — just a folder of YAML. No per-subject import."""

    def _root(self):
        import cpp_labs
        from pathlib import Path
        return Path(cpp_labs.__file__).parent

    def test_discover_merges_all_subjects(self):
        from cpp_labs.topic_yaml import discover_topics
        reg = discover_topics(self._root())
        # ids from several independent subjects are all present, keyed by id
        assert "const_taxonomy" in reg   # pointers_refs
        assert "op_plus" in reg          # op_overload
        assert "unique_basics" in reg    # smart_ptrs

    def test_registry_equals_discovery(self):
        from cpp_labs.topic_yaml import discover_topics
        assert set(R._topic_registry()) == set(discover_topics(self._root()))


# Pre-baked data so the pure renderer can be tested without invoking g++.
FAKE = {
    "bp": {
        "explanation": "A raw pointer holds the address of another variable.",
        "variants": ["int", "double"],
        "int": {
            "code_html": "<pre><code>int* ptr</code></pre>",
            "ptrdata": {"type": "raw", "ptr_addr": "0x1", "target_addr": "0x2", "target_val": "42"},
            "stdout": "PTRDATA: type=raw ...", "stderr": "", "ok": True, "failed": False,
            "bytes": ["18", "5a"], "target_val": "42", "source": "s",
        },
        "double": {
            "code_html": "<pre><code>double* ptr</code></pre>",
            "ptrdata": {"type": "raw", "ptr_addr": "0x3", "target_addr": "0x4", "target_val": "42"},
            "stdout": "PTRDATA: type=raw ...", "stderr": "", "ok": True, "failed": False,
            "bytes": ["aa", "bb"], "target_val": "42", "source": "s",
        },
    }
}


def _ids(html):
    return re.findall(r'\bid="([^"]+)"', html)


class TestPureRender:
    def test_same_component_twice_no_id_collision(self):
        # The whole point: one template instantiated twice on a page. Per-block
        # ids namespace everything, so no collision.
        spec = {"title": "T", "blocks": [
            {"memory_diagram": {"id": "d1", "ptrdata": "${bp.int.ptrdata}"}},
            {"memory_diagram": {"id": "d2", "ptrdata": "${bp.int.ptrdata}"}},
        ]}
        html = R.render_page(spec, FAKE)
        assert html.count("<svg") == 2
        ids = _ids(html)
        assert len(ids) == len(set(ids)), f"dup ids: {[i for i in ids if ids.count(i) > 1]}"

    def test_topic_template_twice_no_id_collision(self):
        spec = {"title": "T", "blocks": [
            {"topic": {"id": "types", "source": "bp"}},
            {"topic": {"id": "types2", "source": "bp"}},
        ]}
        html = R.render_page(spec, FAKE)
        assert html.count("vt-tabs") >= 2  # two variant_tabs instances
        ids = _ids(html)
        assert len(ids) == len(set(ids)), f"dup ids: {[i for i in ids if ids.count(i) > 1]}"

    def test_ref_resolution_whole_value_and_embedded(self):
        spec = {"title": "T", "blocks": [
            {"predict_reveal_quiz": {
                "id": "q", "question": "Q?",
                "options": ["a", "${bp.int.target_val}", "c"],
                "correct_index": 1,
                "explanation": "reads ${bp.int.target_val}",
            }},
        ]}
        html = R.render_page(spec, FAKE)
        assert "42" in html              # embedded ref interpolated
        assert "✓" in html and "✗" in html

    def test_list_of_pairs_adapter_for_steps(self):
        spec = {"title": "T", "blocks": [
            {"progressive_steps": {"id": "st", "steps": [
                {"summary": "S1", "content": "<p>a</p>"},
                {"summary": "S2", "content": "<p>b</p>"},
            ]}},
        ]}
        html = R.render_page(spec, FAKE)
        assert html.count("<details") == 2
        assert "S1" in html and "<p>a</p>" in html

    def test_heading_and_html_builders(self):
        spec = {"title": "T", "blocks": [
            {"heading": {"text": "Try each type"}},
            {"html": {"content": "<p>raw passthrough</p>"}},
        ]}
        html = R.render_page(spec, FAKE)
        assert "<h2>Try each type</h2>" in html
        assert "<p>raw passthrough</p>" in html

    def test_page_is_self_contained(self):
        spec = {"title": "T", "blocks": [{"color_legend": {"id": "lg"}}]}
        html = R.render_page(spec, FAKE)
        assert 'lang="en"' in html and 'id="main"' in html
        assert "<script" not in html
        assert "http://" not in html and "https://" not in html
        assert "src=" not in html


# ---------------------------------------------------------------------------
# Gap 1: cases-topics (a `cases` topic → per-variant stacked sub-cases).
# `const_taxonomy` is the canonical example: each declaration type compiles two
# operations (write / rebind) independently, one of which genuinely fails.
# ---------------------------------------------------------------------------

# Pre-baked data for a two-variant cases-topic. Each variant carries a `cases`
# list of independently-compiled sub-programs (no g++ needed to render this).
FAKE_CASES = {
    "ct": {
        "explanation": "const has two independent axes.",
        "variants": ["int*", "const int*"],
        "int*": {"cases": [
            {"label": "write", "code_html": "<pre>*ptr=99</pre>",
             "ptrdata": {"type": "raw", "ptr_addr": "0x1", "target_addr": "0x2", "target_val": "99"},
             "stdout": "PTRDATA ...", "stderr": "", "ok": True, "failed": False,
             "bytes": ["01"], "target_val": "99"},
            {"label": "rebind", "code_html": "<pre>ptr=&amp;other</pre>",
             "ptrdata": {"type": "raw", "ptr_addr": "0x1", "target_addr": "0x3", "target_val": "7"},
             "stdout": "PTRDATA ...", "stderr": "", "ok": True, "failed": False,
             "bytes": ["02"], "target_val": "7"},
        ]},
        "const int*": {"cases": [
            {"label": "write", "code_html": "<pre>*ptr=99</pre>",
             "ptrdata": None, "stdout": "",
             "stderr": "error: assignment of read-only location", "ok": False, "failed": True,
             "bytes": [], "target_val": "?"},
            {"label": "rebind", "code_html": "<pre>ptr=&amp;other</pre>",
             "ptrdata": {"type": "raw", "ptr_addr": "0x1", "target_addr": "0x3", "target_val": "7"},
             "stdout": "PTRDATA ...", "stderr": "", "ok": True, "failed": False,
             "bytes": ["02"], "target_val": "7"},
        ]},
    }
}


class TestCasesBake:
    """`_bake_one` must preserve a variant's `cases` (not flatten them away)."""

    def test_bake_one_preserves_cases(self, monkeypatch):
        class _T:
            explanation = "expl"

        fake_variant = {"label": "int*", "cases": [
            {"label": "write", "source": "w", "ptrdata": {"target_val": "99"},
             "stdout": "o1", "stderr": "", "failed": False, "membytes": "01 02"},
            {"label": "rebind", "source": "r", "ptrdata": None,
             "stdout": "", "stderr": "error: read-only", "failed": True, "membytes": "n/a"},
        ]}
        monkeypatch.setattr(R, "expand_variants", lambda topic: [{}])
        monkeypatch.setattr(R, "capture_variant", lambda topic, cs: fake_variant)

        entry = R._bake_one(_T())

        assert entry["variants"] == ["int*"]
        v = entry["int*"]
        assert "cases" in v and len(v["cases"]) == 2
        write, rebind = v["cases"]
        assert write["label"] == "write"
        assert write["ok"] is True and write["failed"] is False
        assert write["bytes"] == ["01", "02"]
        assert "code_html" in write  # per-program fields present on each sub-case
        assert rebind["failed"] is True and rebind["ok"] is False
        assert rebind["stderr"] == "error: read-only"


class TestCasesRender:
    """`_build_topic` must render a cases-variant as stacked sub-cases."""

    def test_topic_with_cases_renders_stacked_subcases(self):
        spec = {"title": "T", "blocks": [{"topic": {"id": "ct", "source": "ct"}}]}
        html = R.render_page(spec, FAKE_CASES)

        assert "vt-tabs" in html                       # two variant tabs
        assert html.count('class="ssc"') == 2          # one stacked_subcases per tab
        assert html.count("ssc-case") == 4             # two sub-cases per tab
        assert "write" in html and "rebind" in html    # sub-case labels
        # the failing sub-case shows its real compiler error via the error console
        assert "console--err" in html
        assert "assignment of read-only location" in html

    def test_cases_topic_no_duplicate_ids(self):
        spec = {"title": "T", "blocks": [{"topic": {"id": "ct", "source": "ct"}}]}
        html = R.render_page(spec, FAKE_CASES)
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestCasesEndToEnd:
    """Prove the whole path on the real `const_taxonomy` topic (bakes g++)."""

    def _html(self):
        spec = {"title": "const Taxonomy",
                "blocks": [{"topic": {"id": "ct", "source": "ct"}}]}
        data = R.bake_all({"ct": "const_taxonomy"})
        return R.render_page(spec, data)

    def test_four_tabs_each_with_two_subcases(self):
        html = self._html()
        # 4 declaration types → 4 variant tabs → 4 stacked_subcases blocks.
        assert html.count('class="ssc"') == 4
        assert html.count("ssc-case") == 8            # 4 types × 2 ops

    def test_real_compiler_error_baked(self):
        html = self._html()
        assert "PTRDATA" in html                       # the passing sub-cases ran
        assert "console--err" in html                  # a forbidden op failed
        assert "read-only" in html                     # authentic g++ diagnostic

    def test_no_dup_ids_self_contained(self):
        html = self._html()
        assert "<script" not in html and "https://" not in html
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"


class TestSourceLanguageClass:
    """Source blocks may carry a syntax-highlight hook: a `language:` field from
    the demo/page YAML becomes `<code class="language-XXX">`. Omitting it keeps
    the classless `<pre><code>` (backward compat)."""

    def test_pre_emits_language_class(self):
        assert R._pre("int* p", language="cpp") == \
            '<pre><code class="language-cpp">int* p</code></pre>'

    def test_pre_without_language_is_classless(self):
        assert R._pre("int* p") == "<pre><code>int* p</code></pre>"

    def test_bake_program_threads_language(self):
        html = R._bake_program({"source": "int* p"}, language="cpp")["code_html"]
        assert 'class="language-cpp"' in html

    def test_bake_program_without_language_classless(self):
        html = R._bake_program({"source": "int* p"})["code_html"]
        assert "<pre><code>" in html and "language-" not in html

    @pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
    def test_bake_all_threads_language_end_to_end(self):
        data = R.bake_all({"bp": "basic_ptr"}, language="cpp")
        # every baked program's code block carries the language class
        assert 'class="language-cpp"' in data["bp"]["int"]["code_html"]


class TestFragment:
    def test_render_fragment_has_no_html_shell(self):
        spec = {"title": "T", "blocks": [{"color_legend": {"id": "lg"}}]}
        frag = R.render_fragment(spec, FAKE)
        assert "<html" not in frag and "<head" not in frag and "<!DOCTYPE" not in frag
        assert 'class="legend"' in frag  # the block itself is present

    def test_render_page_still_wraps_shell(self):
        spec = {"title": "T", "blocks": [{"color_legend": {"id": "lg"}}]}
        html = R.render_page(spec, FAKE)
        assert "<!DOCTYPE html>" in html and 'lang="en"' in html
        assert 'class="legend"' in html


class TestRegistry:
    def test_dangling_ptr_is_registered(self):
        reg = R._topic_registry()
        assert "dangling_ptr" in reg
        assert reg["dangling_ptr"].id == "dangling_ptr"


class TestDemoPanel:
    def test_demo_panel_variant_tabs_and_details_bytes(self):
        from cpp_labs import components as C
        html = C.demo_panel("dp", FAKE["bp"])
        assert "vt-tabs" in html                 # int/double variant tabs
        assert "<details" in html                # byte grid collapsed
        assert 'class="badge"' in html and 'class="byte-grid"' in html
        ids = _ids(html)
        assert len(ids) == len(set(ids)), "dup ids in demo_panel"

    def test_no_byte_data_omits_byte_grid(self):
        # The byte box is data-driven: render it only when byte data exists.
        # A variant with no bytes (e.g. a failed compile -> no MEMBYTES) must NOT
        # emit an empty byte-grid (which collapses and wraps its caption).
        from cpp_labs import components as C
        entry = {
            "explanation": "e", "variants": ["default"],
            "default": {
                "code_html": "<pre><code>int&amp; r;</code></pre>", "ptrdata": None,
                "stdout": "", "stderr": "compile error", "ok": False,
                "failed": True, "bytes": [], "target_val": "?", "source": "int& r;",
            },
        }
        html = C.demo_panel("mb", entry)
        assert "byte-grid" not in html          # no empty table
        assert "Raw bytes" not in html          # no dangling details/caption
        assert "console--err" in html           # the error output is still shown

    def test_demo_panel_cases_topic_stacks_subcases(self):
        from cpp_labs import components as C
        html = C.demo_panel("dp", FAKE_CASES["ct"])
        assert html.count('class="ssc"') == 2    # one per decl-type tab
        assert "console--err" in html            # the failing sub-case

    def test_single_variant_demo_has_no_default_tab(self):
        # A single-variant topic (no categorical controls) has nothing to switch
        # between: the lone "default" tab is noise. Render the body, no tab chrome.
        from cpp_labs import components as C
        entry = {
            "explanation": "e", "variants": ["default"],
            "default": {
                "code_html": "<pre><code>int x = 1;</code></pre>", "ptrdata": None,
                "stdout": "ran", "stderr": "", "ok": True, "failed": False,
                "bytes": [], "target_val": "?", "source": "int x = 1;",
            },
        }
        html = C.demo_panel("solo", entry)
        assert ">default<" not in html           # no lone tab label
        assert "vt-tabs" not in html             # no tab strip
        assert 'type="radio"' not in html        # nothing to switch → no radio
        assert "int x = 1;" in html              # the body is still rendered


class TestGlossary:
    def test_glossary_renders_dl_with_terms(self):
        from cpp_labs import components as C
        html = C.glossary("g1", "Pointers", [("dereference (*)", "reads the pointee")])
        assert "<dl" in html and "</dl>" in html
        assert "<dt" in html and "dereference (*)" in html
        assert "<dd" in html and "reads the pointee" in html
        assert 'id="g1"' in html

    def test_glossary_block_via_engine_pairs_adapter(self):
        spec = {"title": "T", "blocks": [
            {"glossary": {"id": "g", "title": "Vocab",
                          "terms": [{"term": "pointee", "def": "the object pointed to"}]}},
        ]}
        html = R.render_page(spec, FAKE)
        assert "pointee" in html and "the object pointed to" in html
        assert "<dl" in html


class TestLeftRailLayout:
    def test_left_rail_one_panel_per_item_first_checked(self):
        from cpp_labs import components as C
        html = C.left_rail_layout("lab", [("Basic", "<p>a</p>"), ("const", "<p>b</p>")])
        assert html.count('class="lr-panel') == 2      # two panel divs
        assert "lr-panel-lab" in html                  # classes are id-namespaced
        assert html.count("<input") == 2
        assert "checked" in html                       # first item checked
        assert "@media" in html                        # single-column reflow rule
        assert 'aria-label' in html                    # nav group has a name
        ids = _ids(html)
        assert len(ids) == len(set(ids)), "dup ids in left_rail_layout"

    def test_left_rail_no_external_script(self):
        # The mobile-menu enhancement adds an INLINE script; nothing external/networked.
        from cpp_labs import components as C
        html = C.left_rail_layout("lab", [("A", "<p>a</p>")])
        assert "<script src" not in html and "src=" not in html and "https://" not in html


class TestLeftRailGlossaryNav:
    """Option D: a glossary is a pressable rail entry (italic, to distinguish it from
    demos), while a demo — not the glossary — stays the panel shown on load."""

    def _html(self):
        from cpp_labs import components as C
        return C.left_rail_layout(
            "lab", [("Vocabulary", "<p>g</p>"), ("Basic", "<p>d</p>")],
            italic_count=1, selected=1)

    def test_leading_labels_italic_others_not(self):
        html = self._html()
        assert re.search(r'<label for="lab-r0"[^>]*font-style:italic', html)      # glossary
        assert not re.search(r'<label for="lab-r1"[^>]*font-style:italic', html)  # demo

    def test_selected_demo_is_the_shown_panel(self):
        html = self._html()
        assert re.search(r'id="lab-r1"[^>]*checked', html)       # first demo shown on load
        assert not re.search(r'id="lab-r0"[^>]*checked', html)   # glossary not auto-shown

    def test_no_italic_by_default(self):
        from cpp_labs import components as C
        html = C.left_rail_layout("lab", [("A", "<p>a</p>"), ("B", "<p>b</p>")])
        assert "font-style:italic" not in html


class TestVariantTabsNesting:
    def test_classes_are_id_namespaced(self):
        from cpp_labs import components as C
        html = C.variant_tabs("outer", [("A", "x"), ("B", "y")])
        # every structural class carries the component id — nothing shared across instances
        assert "vt-panels-outer" in html
        assert "vt-tabs-outer" in html
        assert "vt-panel-outer" in html and "vt-p0-outer" in html

    def test_single_panel_renders_body_without_tab_chrome(self):
        # One panel has nothing to switch: emit just the body in its bordered
        # container, with no radios and no tab labels.
        from cpp_labs import components as C
        html = C.variant_tabs("solo", [("default", "<p>only</p>")])
        assert "<p>only</p>" in html
        assert 'type="radio"' not in html
        assert "vt-tabs-solo" not in html
        assert ">default<" not in html
        assert "vt-panels-solo" in html          # still framed like a panel

    def test_nested_variant_tabs_isolated_and_no_dup_ids(self):
        from cpp_labs import components as C
        inner = C.variant_tabs("inner", [("i0", "a"), ("i1", "b")])
        outer = C.variant_tabs("outer", [("o0", inner), ("o1", "z")])
        # inner and outer use disjoint namespaced classes → no selector collision
        assert "vt-p0-inner" in outer and "vt-p0-outer" in outer
        # outer's show selector targets only outer-namespaced panels
        assert "~ .vt-panels-outer .vt-p0-outer" in outer
        ids = _ids(outer)
        assert len(ids) == len(set(ids)), "dup ids across nested variant_tabs"


class TestHeader:
    def test_render_header_inline_and_legend(self, tmp_path):
        blocks = [
            {"color_legend": {"id": "lg"}},
            {"glossary": {"id": "g", "title": "V",
                          "terms": [{"term": "t1", "def": "d1"}]}},
        ]
        html = R._render_header(blocks, tmp_path)
        assert 'class="legend"' in html
        assert "t1" in html and "d1" in html and "<dl" in html

    def test_render_header_glossary_from_file(self, tmp_path):
        (tmp_path / "g.glossary.yaml").write_text(
            "title: Pointers\nterms:\n  - {term: pointee, def: the object pointed to}\n",
            encoding="utf-8")
        blocks = [{"glossary": {"id": "g", "source": "g.glossary.yaml"}}]
        html = R._render_header(blocks, tmp_path)
        assert "Pointers" in html and "pointee" in html and "the object pointed to" in html


class TestGlossaryFromSource:
    """The shared helper both _render_header and _build_sidebar use to load a
    ``source:`` glossary file and render it: returns ``(title, html)``."""

    def test_returns_title_and_rendered_html(self, tmp_path):
        (tmp_path / "g.glossary.yaml").write_text(
            "title: Pointers\nterms:\n  - {term: pointee, def: the object pointed to}\n",
            encoding="utf-8")
        title, html = R._glossary_from_source(
            {"id": "g", "source": "g.glossary.yaml"}, tmp_path)
        assert title == "Pointers"
        assert "pointee" in html and "the object pointed to" in html and "<dl" in html

    def test_defaults_when_title_and_id_absent(self, tmp_path):
        (tmp_path / "g.glossary.yaml").write_text(
            "terms:\n  - {term: ptr, def: an address}\n", encoding="utf-8")
        title, html = R._glossary_from_source({"source": "g.glossary.yaml"}, tmp_path)
        assert title == "Glossary"
        assert 'id="glossary"' in html and "an address" in html


class TestMobileOverflow:
    """Grid tracks must be shrinkable (minmax(0,...)+min-width:0) so a wide code
    line scrolls inside its box instead of blowing the page wider than the phone."""

    def test_code_diagram_panel_columns_shrinkable(self):
        from cpp_labs import components as C
        html = C.code_diagram_panel("cdp", "<pre>x</pre>", "<svg></svg>")
        assert "minmax(0" in html          # 1fr -> minmax(0,1fr)
        assert "min-width:0" in html        # .cdp-code can shrink; overflow:auto engages

    def test_left_rail_columns_shrinkable(self):
        from cpp_labs import components as C
        html = C.left_rail_layout("lab", [("A", "<p>a</p>")])
        assert "minmax(0" in html
        assert "min-width:0" in html


class TestLeftRailMobileMenu:
    """Route J: at narrow widths the rail becomes a tap-to-open menu (JS), layered
    on the zero-JS radio baseline so it degrades gracefully with JS disabled."""

    def test_menu_toggle_and_progressive_script_present(self):
        from cpp_labs import components as C
        html = C.left_rail_layout("lab", [("A", "<p>a</p>"), ("B", "<p>b</p>")])
        assert "<button" in html and "aria-expanded" in html   # accessible toggle
        assert "<script" in html                               # progressive enhancement
        assert "lr-js" in html                                 # menu CSS gated on JS-added class
        assert "lr-open" in html                               # open/closed state hook

    def test_baseline_still_works_without_js(self):
        from cpp_labs import components as C
        html = C.left_rail_layout("lab", [("A", "<p>a</p>"), ("B", "<p>b</p>")])
        # radios + rail present regardless of JS (graceful degradation)
        assert html.count("<input") == 2
        assert "lr-rail-lab" in html
        assert "checked" in html

    def test_no_external_script_or_network(self):
        from cpp_labs import components as C
        html = C.left_rail_layout("lab", [("A", "<p>a</p>")])
        # inline JS is allowed now, but nothing external / networked
        assert "<script src" not in html and "https://" not in html and "src=" not in html


class TestOptionalDiagram:
    """`topic: {diagram: false}` renders code+output but no memory diagram.

    For subjects with no memory-model picture (operator overloading, classes,
    templates), the panel must not force a "?" placeholder SVG. Default stays on
    so pointer pages are unchanged.
    """

    def test_diagram_false_omits_memory_diagram(self):
        spec = {"title": "T", "blocks": [
            {"topic": {"id": "t", "source": "bp", "diagram": False}}]}
        html = R.render_page(spec, FAKE)
        assert 'role="img"' not in html            # no memory diagram at all
        assert "int* ptr" in html and "double* ptr" in html  # code still shown
        assert "<pre" in html                       # code block present

    def test_diagram_default_keeps_memory_diagram(self):
        spec = {"title": "T", "blocks": [
            {"topic": {"id": "t", "source": "bp"}}]}
        html = R.render_page(spec, FAKE)
        assert 'role="img"' in html                 # diagram present by default


class TestConceptBlock:
    def test_concept_block_renders_disclosure_with_resolved_text(self):
        from cpp_labs.yaml_engine import render_page as R
        spec = {"blocks": [
            {"concept": {"id": "n1", "text": "${x.explanation}"}},
        ]}
        data = {"x": {"explanation": "A reference is an alias."}}
        html = R.render_fragment(spec, data)
        assert "<details" in html and "class=\"concept\"" in html
        assert ">Concept</summary>" in html
        assert "A reference is an alias." in html

    def test_concept_block_open_flag(self):
        from cpp_labs.yaml_engine import render_page as R
        spec = {"blocks": [{"concept": {"id": "n2", "text": "hi", "open": True}}]}
        html = R.render_fragment(spec, {})
        assert "class=\"concept\" open" in html


class TestNavShell:
    ITEMS = [("A", "<p>a</p>"), ("B", "<p>b</p>"), ("C", "<p>c</p>")]

    def test_left_rail_is_byte_identical_to_left_rail_layout(self):
        from cpp_labs import components as C
        got = C.nav_shell("lab", self.ITEMS, style="left_rail", leading=1, selected=1)
        want = C.left_rail_layout("lab", self.ITEMS, italic_count=1, selected=1)
        assert got == want

    def test_stacked_ignores_leading_and_selected(self):
        from cpp_labs import components as C
        html = C.nav_shell("lab", self.ITEMS, style="stacked", leading=2, selected=2)
        assert "<p>a</p>" in html and "<p>b</p>" in html and "<p>c</p>" in html
        assert "type=\"radio\"" not in html and "font-style:italic" not in html

    def test_top_tabs_honors_selected(self):
        from cpp_labs import components as C
        html = C.nav_shell("lab", self.ITEMS, style="top_tabs", selected=2)
        # the third tab's radio is the checked one
        assert 'id="lab-t2" style=' in html and 'id="lab-t2"' in html
        import re
        checked = re.search(r'id="lab-t(\d)"[^>]*checked', html)
        assert checked and checked.group(1) == "2"

    def test_unknown_style_raises(self):
        from cpp_labs import components as C
        import pytest
        with pytest.raises(ValueError, match="unknown nav style"):
            C.nav_shell("lab", self.ITEMS, style="carousel")


class TestBuildLayoutNav:
    def test_layouts_dict_and_stacked_layout_are_gone(self):
        # The leaky per-style dispatch is removed; nav_shell is the single seam.
        from cpp_labs.yaml_engine import render_page as R
        assert not hasattr(R, "_LAYOUTS")
        assert not hasattr(R, "_stacked_layout")


class TestSidebar:
    def test_mixed_glossary_and_concept_entries_in_order(self, tmp_path):
        from cpp_labs.yaml_engine import render_page as R
        g = tmp_path / "v.glossary.yaml"
        g.write_text("title: Vocab\nterms:\n  - {term: ptr, def: an address}\n", encoding="utf-8")
        sidebar = [
            {"concept": {"id": "obj", "text": "What this teaches."}},
            {"glossary": {"id": "g", "source": "v.glossary.yaml", "label": "Vocabulary"}},
        ]
        items = R._build_sidebar(sidebar, tmp_path)
        assert [label for label, _ in items] == ["Concept", "Vocabulary"]
        assert "What this teaches." in items[0][1] and "<details" not in items[0][1]
        assert "an address" in items[1][1]

    def test_unknown_sidebar_entry_raises(self, tmp_path):
        from cpp_labs.yaml_engine import render_page as R
        import pytest
        with pytest.raises(KeyError, match="unknown sidebar entry"):
            R._build_sidebar([{"legend": {"id": "x"}}], tmp_path)

    def test_multi_key_sidebar_entry_raises(self, tmp_path):
        from cpp_labs.yaml_engine import render_page as R
        import pytest
        with pytest.raises(ValueError, match="exactly one key"):
            R._build_sidebar([{"glossary": {"id": "g"}, "concept": {"id": "c"}}], tmp_path)
