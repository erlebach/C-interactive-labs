"""Tests for the YAML-driven page renderer (cpp_ptr_lab.basic_ptr_yaml).

A page is a flat YAML `blocks:` list; each block names a component (or a smart
builder like `topic`) plus its inputs and an id. `render_page` translates the
list to HTML by dispatching each block to the matching component. The pure path
(`render_page` with pre-baked data) needs no g++; `build_page` bakes real g++
output and is gated on a compiler.

TDD: RED before GREEN (feedback/testing.md).
"""

from __future__ import annotations

import re
import shutil

import pytest

from cpp_ptr_lab.basic_ptr_yaml import render_page as R

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


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestBuildFromYamlFile:
    def _html(self, tmp_path):
        out = R.build_page(R.SPEC_PATH, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_file_written(self, tmp_path):
        out, _ = self._html(tmp_path)
        assert out.exists()

    def test_reproduces_component_set(self, tmp_path):
        _, html = self._html(tmp_path)
        for sig in ('class="legend"', 'class="badge"', 'class="byte-grid"',
                    "vt-tabs", "qfb", "<details", 'class="callout"', 'role="img"'):
            assert sig in html, f"missing {sig}"

    def test_one_tab_per_type(self, tmp_path):
        _, html = self._html(tmp_path)
        for t in ("int", "double", "float"):
            assert f">{t}<" in html

    def test_real_output_baked(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "PTRDATA" in html

    def test_no_duplicate_ids(self, tmp_path):
        _, html = self._html(tmp_path)
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"

    def test_self_contained(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "<script" not in html and "http://" not in html
        assert "https://" not in html and "src=" not in html

    def test_missing_gpp_fails_clearly(self, tmp_path, monkeypatch):
        monkeypatch.setattr(R.shutil, "which", lambda name: None)
        with pytest.raises(RuntimeError, match="g\\+\\+"):
            R.build_page(R.SPEC_PATH, tmp_path)
