"""Test the basic_ptr topic page reconstructed from the component library.

Demonstrates assembling a real topic page purely from cpp_ptr_lab.components,
baking real g++ output. Requires g++ (the page bakes compiler output).
"""

from __future__ import annotations

import re
import shutil

import pytest

from cpp_ptr_lab import topic_page

HAS_GPP = shutil.which("g++") is not None


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake topic output")
class TestBasicPtrPage:
    def _page(self, tmp_path):
        out = topic_page.build_basic_ptr_page(tmp_path)
        return out.read_text(encoding="utf-8")

    def test_file_written(self, tmp_path):
        out = topic_page.build_basic_ptr_page(tmp_path)
        assert out.exists()

    def test_self_contained_wcag_doc(self, tmp_path):
        page = self._page(tmp_path)
        assert 'lang="en"' in page
        assert 'id="main"' in page
        assert "<script" not in page
        assert "http://" not in page and "https://" not in page
        assert "src=" not in page

    def test_one_tab_per_type(self, tmp_path):
        page = self._page(tmp_path)
        for t in ("int", "double", "float"):
            assert f">{t}<" in page  # appears as a tab label

    def test_assembled_from_components(self, tmp_path):
        page = self._page(tmp_path)
        # signatures of the components used
        assert 'class="legend"' in page        # color_legend
        assert 'class="badge"' in page          # compile_status_badge
        assert 'class="byte-grid"' in page      # byte_grid
        assert "vt-tabs" in page                 # variant_tabs
        assert "qfb" in page                     # predict_reveal_quiz
        assert "<details" in page                # progressive_steps
        assert 'class="callout"' in page         # callout_note

    def test_real_output_baked(self, tmp_path):
        page = self._page(tmp_path)
        # real g++ stdout from the instrumented program
        assert "PTRDATA" in page

    def test_no_duplicate_ids(self, tmp_path):
        page = self._page(tmp_path)
        ids = re.findall(r'\bid="([^"]+)"', page)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"

    def test_missing_gpp_fails_clearly(self, tmp_path, monkeypatch):
        monkeypatch.setattr(topic_page.shutil, "which", lambda name: None)
        with pytest.raises(RuntimeError, match="g\\+\\+"):
            topic_page.build_basic_ptr_page(tmp_path)
