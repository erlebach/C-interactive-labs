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
from cpp_labs.topic_yaml import load_topics

HAS_GPP = shutil.which("g++") is not None
FA_SPEC = Path(__file__).parents[1] / "function_args.page.yaml"
_TOPICS = load_topics(Path(__file__).parents[1] / "topics")
function_args = _TOPICS["function_args"]


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
# A minimal single-variant stub so the four added topic blocks render from FAKE
# data (their real content is exercised by the g++-baked integration tests below).
_STUB = {
    "explanation": "stub.",
    "variants": ["only"],
    "only": {**_VARIANT, "ptrdata": None, "target_val": "?"},
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
    },
    "cr": _STUB, "sw": _STUB, "op": _STUB, "cc": _STUB,
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


# ---------------------------------------------------------------------------
# Cycle 3a — the four added examples (pure; no g++)
# ---------------------------------------------------------------------------


class TestAddedTopicDefinitions:
    def test_const_ref_pairs_correct_and_mistake(self):
        t = _TOPICS["fa_const_ref"]
        assert [c.label for c in t.cases] == [
            "Correct: read through a const reference",
            "Mistake: assign through it  (compile error)",
        ]
        assert "PTRDATA: type=ref" in t.cases[0].subs["<<body>>"]
        # the mistake writes through a const reference — this must not compile
        mistake = t.cases[1].subs["<<body>>"]
        assert "const int& x" in mistake and "x = 99" in mistake

    def test_swap_pairs_works_and_noop(self):
        t = _TOPICS["fa_swap"]
        assert [c.label for c in t.cases] == [
            "Works: pass by reference",
            "Silent no-op: pass by value",
        ]
        assert "void swap_vals(int& a, int& b)" in t.cases[0].subs["<<body>>"]
        assert "void swap_vals(int a, int b)" in t.cases[1].subs["<<body>>"]

    def test_out_param_is_a_single_pointer_program(self):
        t = _TOPICS["fa_out_param"]
        assert t.cases is None and not t.controls
        assert "int* q, int* r" in t.template
        assert "PTRDATA: type=raw" in t.template

    def test_copy_cost_swaps_value_vs_const_ref(self):
        t = _TOPICS["fa_copy_cost"]
        (mode,) = [c for c in t.controls if c.kind == "dropdown"]
        assert mode.options == ["by value", "by const reference"]
        assert "void use(Big b)" in mode.value_map["by value"]
        assert "const Big& b" in mode.value_map["by const reference"]
        # locked style: examples model encapsulation with `class`, not `struct`
        assert "class Big" in t.template and "struct Big" not in t.template


# ---------------------------------------------------------------------------
# Cycle 3b — the four added examples baked end-to-end (real g++)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestAddedExamplesBuild:
    def test_all_four_examples_bake_real_output(self, tmp_path):
        html = R.build_page(FA_SPEC, tmp_path).read_text(encoding="utf-8")
        # const reference — read-only use + a real compile-error gotcha
        assert "show sees 42 (read-only)" in html
        assert "Correct: read through a const reference" in html
        assert "Mistake: assign through it" in html
        assert "cannot assign to" in html   # genuine g++ error text
        assert "out--err" in html           # the compile-error console box
        assert "reference diagram" in html  # the Correct case draws the alias
        # swap — works vs silent no-op
        assert "after:  x=2 y=1" in html
        assert "(unchanged!)" in html
        # output parameters — one pointer links back to the caller's quotient
        assert "17 / 5 = 3 remainder 2" in html
        assert "raw pointer diagram" in html
        # copy cost — by value copies once, const& copies zero times
        assert "copies made: 1" in html
        assert "copies made: 0" in html

    def test_no_leaked_no_diagram_placeholder(self, tmp_path):
        html = R.build_page(FA_SPEC, tmp_path).read_text(encoding="utf-8")
        assert "no diagram" not in html and "type=?" not in html
        # WCAG: every inline svg is an accessible role="img"
        assert html.count("<svg") == html.count('role="img"')
