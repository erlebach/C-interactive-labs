"""Tests for the `function_args` subject — the end-to-end "new subject" proof.

A single topic (`function_args`) with a `mode` dropdown renders as a three-tab
cluster (value / pointer / reference) through the existing YAML page engine,
reusing `memory_diagram` with ZERO new diagram components. The pure paths need
no g++; the integration test bakes real g++ output and is compiler-gated.

TDD: RED before GREEN (feedback/testing.md).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from cpp_labs.yaml_engine import render_page as R
from cpp_labs.code_generator import generate_source
from cpp_labs.function_args.topics import function_args

HAS_GPP = shutil.which("g++") is not None
FA_SPEC = Path(__file__).parent / "function_args.page.yaml"


def _ids(html):
    return re.findall(r'\bid="([^"]+)"', html)


# ---------------------------------------------------------------------------
# Cycle 1 — the topic module (pure; no g++)
# ---------------------------------------------------------------------------


class TestTopicDefinition:
    def test_three_modes(self):
        assert function_args.id == "function_args"
        (mode,) = [c for c in function_args.controls if c.kind == "dropdown"]
        assert mode.options == ["by value", "by pointer", "by reference"]

    def test_source_by_value_is_a_copy(self):
        src = generate_source(function_args, {"mode": "by value"})
        assert "int x" in src and "modify(val)" in src
        assert "PTRDATA" not in src  # a copy has no link back — no diagram

    def test_source_by_pointer_writes_through(self):
        src = generate_source(function_args, {"mode": "by pointer"})
        assert "int* x" in src and "modify(&val)" in src
        assert "*x = 99" in src
        assert "PTRDATA: type=raw" in src

    def test_source_by_reference_aliases(self):
        src = generate_source(function_args, {"mode": "by reference"})
        assert "int& x" in src and "modify(val)" in src
        assert "PTRDATA: type=ref" in src


# ---------------------------------------------------------------------------
# Cycle 2a — page render (pure; FAKE pre-baked data, no g++)
# ---------------------------------------------------------------------------

_VARIANT = {
    "code_html": "<pre><code>x</code></pre>",
    "stdout": "before: val = 42\nafter:  val = 99",
    "stderr": "", "ok": True, "failed": False, "bytes": ["63", "00"],
}
FAKE = {
    "fa": {
        "explanation": "Passing an argument by value, pointer, or reference.",
        "variants": ["by value", "by pointer", "by reference"],
        "by value": {**_VARIANT, "ptrdata": None, "target_val": "?"},
        "by pointer": {**_VARIANT, "ptrdata": {"type": "raw", "ptr_addr": "0x1",
                       "target_addr": "0x2", "target_val": "99"}, "target_val": "99"},
        "by reference": {**_VARIANT, "ptrdata": {"type": "ref", "ref_addr": "0x2",
                         "target_addr": "0x2", "target_val": "99"}, "target_val": "99"},
    }
}


class TestPageRender:
    def _html(self):
        return R.render_page(R.load_spec(FA_SPEC), FAKE)

    def test_three_tabs_from_the_spec(self):
        html = self._html()
        for label in ("by value", "by pointer", "by reference"):
            assert f">{label}<" in html

    def test_pointer_and_reference_get_a_diagram(self):
        # memory_diagram reuse: raw + ref both render an SVG; value has no link.
        html = self._html()
        assert "raw pointer diagram" in html
        assert "reference diagram" in html

    def test_self_contained_no_dup_ids(self):
        html = self._html()
        assert 'lang="en"' in html and "<script" not in html
        assert "http://" not in html and "src=" not in html
        ids = _ids(html)
        assert len(ids) == len(set(ids)), f"dup ids: {[i for i in ids if ids.count(i) > 1]}"


# ---------------------------------------------------------------------------
# Cycle 2b — integration (bakes real g++ output)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestBuild:
    def _html(self, tmp_path):
        out = R.build_page(FA_SPEC, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_file_written_under_stem_subdir(self, tmp_path):
        out, _ = self._html(tmp_path)
        assert out.exists() and out.parent.name == "function_args"

    def test_three_tabs_and_real_output(self, tmp_path):
        _, html = self._html(tmp_path)
        for label in ("by value", "by pointer", "by reference"):
            assert f">{label}<" in html
        assert "PTRDATA" in html

    def test_value_leaves_caller_unchanged_others_mutate(self, tmp_path):
        _, html = self._html(tmp_path)
        # Every mode prints the before/after; only value keeps val at 42.
        assert "before: val = 42" in html
        assert "after:  val = 99" in html   # pointer + reference mutate
        assert "after:  val = 42" in html   # value does not

    def test_no_dup_ids_self_contained(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "<script" not in html and "https://" not in html
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"
