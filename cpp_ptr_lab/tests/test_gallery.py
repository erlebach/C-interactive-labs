"""Tests for the component gallery build (cpp_ptr_lab.gallery).

RED-first (overrides OpenSpec tests-last ordering, per feedback/testing.md).
The gallery bakes real g++ output, so the build tests require a compiler; the
missing-compiler behavior is tested separately with a monkeypatched ``which``.
"""

from __future__ import annotations

import shutil

import pytest

from cpp_ptr_lab import gallery

HAS_GPP = shutil.which("g++") is not None


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake gallery output")
class TestGalleryBuild:
    def test_one_self_contained_page_per_component(self, tmp_path):
        gallery.build_gallery(tmp_path)
        gdir = tmp_path / "gallery"
        for name in gallery.COMPONENT_NAMES:
            f = gdir / f"{name}.html"
            assert f.exists(), f"missing demo page for {name}"
            t = f.read_text(encoding="utf-8")
            assert "<script" not in t
            assert "http://" not in t and "https://" not in t
            assert "src=" not in t
            assert 'lang="en"' in t
            assert 'id="main"' in t  # complete WCAG AA doc

    def test_index_links_every_component_by_name(self, tmp_path):
        gallery.build_gallery(tmp_path)
        idx = (tmp_path / "gallery" / "index.html").read_text(encoding="utf-8")
        for name in gallery.COMPONENT_NAMES:
            assert f"{name}.html" in idx, f"index missing link to {name}"

    def test_index_is_self_contained(self, tmp_path):
        gallery.build_gallery(tmp_path)
        idx = (tmp_path / "gallery" / "index.html").read_text(encoding="utf-8")
        assert "<script" not in idx
        assert 'lang="en"' in idx

    def test_output_components_bake_real_gpp_output(self, tmp_path):
        gallery.build_gallery(tmp_path)
        console = (tmp_path / "gallery" / "output_console.html").read_text(encoding="utf-8")
        # The error variant shows REAL g++ stderr (contains "error:"), not a
        # placeholder string.
        assert "error:" in console
        assert "PLACEHOLDER" not in console


class TestGalleryDegradesWithoutCompiler:
    def test_missing_gpp_fails_clearly_and_early(self, tmp_path, monkeypatch):
        monkeypatch.setattr(gallery.shutil, "which", lambda name: None)
        with pytest.raises(RuntimeError, match="g\\+\\+"):
            gallery.build_gallery(tmp_path)
