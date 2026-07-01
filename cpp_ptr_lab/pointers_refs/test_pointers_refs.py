"""Build integration for the combined Pointers & References lab page.

One self-contained page stacking every pointers_refs demo (each with its own
variant tabs) — the new-engine equivalent of the old ``dist/lab_pointers_refs.html``.
Bakes real g++ output through the shared engine and asserts the full topic set,
per-type tabs (basic_ptr), the const 2x2 stacked sub-cases (gap 1), real baked
output, id uniqueness across all topics, and self-containment. Compiler-gated.

TDD: RED before GREEN (feedback/testing.md).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from cpp_ptr_lab.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
SPEC = Path(__file__).parent / "pointers_refs.page.yaml"

# The demos the combined page must present, by display name (tab/section heading).
TOPIC_NAMES = [
    "Basic Pointer",
    "const Taxonomy",
    "Ref: Must Bind",
    "Ref: No Null",
    "Ref: Rebind Illusion",
    "Ref: const Ref",
    "Gotcha: Null Deref",
]


def _ids(html):
    return re.findall(r'\bid="([^"]+)"', html)


@pytest.mark.skipif(not HAS_GPP, reason="g++ required to bake real output")
class TestBuildCombinedPage:
    def _html(self, tmp_path):
        out = R.build_page(SPEC, tmp_path)
        return out, out.read_text(encoding="utf-8")

    def test_file_written_under_stem_subdir(self, tmp_path):
        out, _ = self._html(tmp_path)
        assert out.exists() and out.parent.name == "pointers_refs"

    def test_every_topic_present(self, tmp_path):
        _, html = self._html(tmp_path)
        for name in TOPIC_NAMES:
            assert name in html, f"missing topic: {name}"

    def test_basic_ptr_has_type_tabs(self, tmp_path):
        _, html = self._html(tmp_path)
        for t in ("int", "double", "float"):
            assert f">{t}<" in html

    def test_const_taxonomy_stacked_subcases_with_real_error(self, tmp_path):
        _, html = self._html(tmp_path)
        # gap 1: the const 2x2 renders as stacked sub-cases and one op fails.
        assert 'class="ssc"' in html
        assert "console--err" in html
        assert "read-only" in html

    def test_real_output_baked(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "PTRDATA" in html

    def test_no_duplicate_ids_across_all_topics(self, tmp_path):
        _, html = self._html(tmp_path)
        ids = _ids(html)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        assert not dups, f"duplicate ids: {dups}"

    def test_self_contained(self, tmp_path):
        _, html = self._html(tmp_path)
        assert "<script" not in html and "http://" not in html
        assert "https://" not in html and "src=" not in html
