"""Tests for the subject-agnostic YAML page engine (cpp_ptr_lab.yaml_engine).

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

from cpp_ptr_lab.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None


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
        from cpp_ptr_lab import components as C
        html = C.demo_panel("dp", FAKE["bp"])
        assert "vt-tabs" in html                 # int/double variant tabs
        assert "<details" in html                # byte grid collapsed
        assert 'class="badge"' in html and 'class="byte-grid"' in html
        ids = _ids(html)
        assert len(ids) == len(set(ids)), "dup ids in demo_panel"

    def test_demo_panel_cases_topic_stacks_subcases(self):
        from cpp_ptr_lab import components as C
        html = C.demo_panel("dp", FAKE_CASES["ct"])
        assert html.count('class="ssc"') == 2    # one per decl-type tab
        assert "console--err" in html            # the failing sub-case


class TestGlossary:
    def test_glossary_renders_dl_with_terms(self):
        from cpp_ptr_lab import components as C
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
