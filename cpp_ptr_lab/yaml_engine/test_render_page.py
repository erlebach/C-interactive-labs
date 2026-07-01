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

from cpp_ptr_lab.yaml_engine import render_page as R


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
