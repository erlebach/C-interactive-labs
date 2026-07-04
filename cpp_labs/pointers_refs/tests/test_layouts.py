"""Build integration for demo/layout composition. Compiler-gated."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None


def _ids(html):
    return re.findall(r'\bid="([^"]+)"', html)


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestBuildLayoutMinimal:
    def _mini(self, tmp_path):
        demo = tmp_path / "basic.demo.yaml"
        demo.write_text(
            "title: Basic Pointer\nbake: {bp: basic_ptr}\n"
            "blocks:\n  - topic: {id: bp, source: bp}\n", encoding="utf-8")
        layout = tmp_path / "mini.rail.yaml"
        layout.write_text(
            "title: Mini Lab\nstyle: left_rail\n"
            "header:\n  - color_legend: {id: lg}\n"
            "demos:\n  - basic.demo.yaml\n", encoding="utf-8")
        out = R.build_layout(layout, tmp_path / "dist")
        return out, out.read_text(encoding="utf-8")

    def test_writes_standalone_page_under_stem(self, tmp_path):
        out, html = self._mini(tmp_path)
        assert out.exists() and out.parent.name == "mini.rail"
        assert "<!DOCTYPE html>" in html and 'lang="en"' in html

    def test_left_rail_and_header_present(self, tmp_path):
        _, html = self._mini(tmp_path)
        assert "lr-rail" in html and 'class="legend"' in html
        assert "Basic Pointer" in html and "PTRDATA" in html

    def test_no_duplicate_ids(self, tmp_path):
        _, html = self._mini(tmp_path)
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"


LAYOUT = Path(__file__).parents[1] / "layouts" / "pointers_refs.rail.yaml"

TOPIC_NAMES = [
    "Basic Pointer", "const Taxonomy", "Ref: Must Bind", "Ref: No Null",
    "Ref: Rebind Illusion", "Ref: const Ref", "Gotcha: Null Deref",
    "Gotcha: Dangling Ptr",
]


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestPointersRefsRailPage:
    def _html(self, tmp_path):
        out = R.build_layout(LAYOUT, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_all_eight_demos_present(self, tmp_path):
        _, html = self._html(tmp_path)
        for name in TOPIC_NAMES:
            assert name in html, f"missing demo: {name}"

    def test_basic_ptr_type_tabs_and_const_2x2(self, tmp_path):
        _, html = self._html(tmp_path)
        for t in ("int", "double", "float"):
            assert f">{t}<" in html
        assert 'class="ssc"' in html and "read-only" in html   # const 2x2 + real error

    def test_glossary_is_italic_rail_entry_not_header(self, tmp_path):
        # Option D: the glossary lives in the rail as an italic "Vocabulary" entry,
        # not as an always-on header block above the rail.
        _, html = self._html(tmp_path)
        before_rail = html.split('class="lr"')[0]           # everything before the rail div
        assert 'class="glossary"' not in before_rail        # no longer a header block
        assert re.search(r'<label[^>]*font-style:italic[^>]*>\s*Vocabulary', html)
        assert "<dl" in html and "dereference" in html      # its terms still present (in a panel)

    def test_second_reference_glossary_present(self, tmp_path):
        # 0..N glossaries per page: a second, reference-semantics glossary joins the
        # general "Vocabulary" as another leading italic rail entry (a demo still shows on load).
        _, html = self._html(tmp_path)
        assert re.search(r'<label[^>]*font-style:italic[^>]*>\s*Reference Terms', html)
        assert "lvalue" in html and "rvalue" in html    # its distinctive terms
        # both glossary labels are italic; demos (e.g. Basic Pointer) are not
        assert re.search(r'<label[^>]*font-style:italic[^>]*>\s*Vocabulary', html)

    def test_no_dup_ids_self_contained(self, tmp_path):
        _, html = self._html(tmp_path)
        # Self-contained: the page LOADS nothing external. Inlined JS (mobile-menu +
        # highlight.js) is allowed, and may carry URL *text* in comments — so assert no
        # external *load* (no <script src>, <link>, src=, href="http"), not bare "https://".
        assert "<script src" not in html and "<link" not in html and "src=" not in html
        assert 'href="http' not in html
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"

    def test_source_highlighted_with_hljs(self, tmp_path):
        # Rail page uses highlight.js (inlined, self-contained): the library runs on
        # load over the language-cpp source blocks; degrades to plain code with JS off.
        _, html = self._html(tmp_path)
        assert "hljs.highlightAll" in html and ".hljs" in html
        assert 'class="language-cpp"' in html

    def test_no_bare_pre_semantic_child(self, tmp_path):
        # SIA-R79: every <pre> carries a semantic child (<code> for source, <samp> for output).
        _, html = self._html(tmp_path)
        assert not re.search(r'<pre\b[^>]*>(?!\s*<(?:code|samp)\b)', html)

    def test_every_svg_has_accessible_name(self, tmp_path):
        _, html = self._html(tmp_path)
        # WCAG 1.1.1: every inline svg must be role="img" with a non-empty <title>.
        assert html.count("<svg") == html.count('role="img"'), "an svg lacks role=img"
        assert "<title></title>" not in html and "<title/>" not in html
        # no <img> without alt (there should be no <img> at all)
        assert not re.search(r"<img(?![^>]*\balt=)", html), "an <img> lacks alt"


TABS = Path(__file__).parents[1] / "layouts" / "pointers_refs.tabs.yaml"


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestPointersRefsTabsPage:
    def _html(self, tmp_path):
        out = R.build_layout(TABS, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_top_tabs_all_demos_and_real_output(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "vt-tabs" in html                       # outer top tabs present
        for name in TOPIC_NAMES:
            assert name in html
        assert "PTRDATA" in html and "read-only" in html

    def test_no_dup_ids_self_contained(self, tmp_path):
        _, html = self._html(tmp_path)
        # No external load — inlined JS (mobile-menu + highlight.js) may carry URL text.
        assert "<script src" not in html and "<link" not in html and "src=" not in html
        assert 'href="http' not in html
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"


@pytest.mark.skipif(not HAS_GPP, reason="g++ required by build_layout's compiler guard")
def test_unknown_style_raises_valueerror(tmp_path):
    """A typo in a layout's `style:` must fail fast with an author-friendly error
    listing the valid choices — not a raw KeyError (data-over-code: YAML authors)."""
    layout = tmp_path / "bad.rail.yaml"
    layout.write_text("title: Bad\nstyle: leftrail\nheader: []\ndemos: []\n",
                      encoding="utf-8")
    with pytest.raises(ValueError, match="unknown nav style"):
        R.build_layout(layout, tmp_path / "dist")
