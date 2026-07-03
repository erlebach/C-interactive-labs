"""Build integration for the basic_ptr page.

Bakes real g++ output for the basic_ptr.page.yaml spec through the shared
engine and asserts the rendered page's component set, per-type tabs, real
baked output, id uniqueness, and self-containment. Compiler-gated.

TDD: RED before GREEN (feedback/testing.md).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
SPEC = Path(__file__).parent / "basic_ptr.page.yaml"


def _ids(html):
    return re.findall(r'\bid="([^"]+)"', html)


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestBuildFromYamlFile:
    def _html(self, tmp_path):
        out = R.build_page(SPEC, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_file_written_under_stem_subdir(self, tmp_path):
        out, _ = self._html(tmp_path)
        assert out.exists() and out.parent.name == "basic_ptr"

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
            R.build_page(SPEC, tmp_path)
