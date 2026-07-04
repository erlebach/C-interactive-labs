"""Build integration for the Class Structure (Rule of Five) page.

One self-contained page: an instrumented ``Point``/``Buffer`` shown across the
special member functions (constructor, copy ctor, copy assignment, move ops,
initializer_list). Two topics carry a Correct/Mistake pair whose mistake is a
runtime fault caught by AddressSanitizer (shallow-copy double free; reading a
moved-from buffer). All examples are written with ``class`` (never ``struct``).
Compiler-gated (bakes real g++ output).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "class_structure.rail.yaml"

pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++ to bake real output")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_builds_and_is_self_contained(html):
    assert "<!DOCTYPE html>" in html
    assert "lang=" in html and "skip" in html.lower()
    assert not any(x in html for x in ['<script src', '<link', 'href="http', 'src="http'])


def test_no_memory_diagram(html):
    assert 'role="img"' not in html


def test_examples_use_class_not_struct(html):
    # Locked course convention (project memory 2026-07-04): every example models
    # encapsulation with `class`, never `struct`.
    assert "class Point" in html
    assert "class Buffer" in html
    assert "struct Point" not in html
    assert "struct Buffer" not in html


def test_real_output_is_baked(html):
    assert "ctor: Point(3, 4)" in html
    assert "p = (3, 4)" in html
    assert "copy ctor: deep-copied 3 ints" in html
    assert "copy assign: replaced contents (3 ints)" in html
    assert "move ctor: stole buffer" in html
    assert "init-list ctor: 4 ints" in html
    assert "b = {10, 20, 30, 40}" in html


def test_copy_ctor_gotcha_double_free(html):
    # cls_copy_ctor pairs the deep-copy correct version with the default
    # shallow-copy mistake, which double-frees at runtime (ASan-reported).
    assert "Correct: deep copy" in html
    assert "Mistake: default shallow copy" in html
    assert "AddressSanitizer" in html
    assert "double-free" in html


def test_move_gotcha_use_after_move(html):
    # cls_move_ops pairs the safe version with reading a moved-from buffer,
    # a null dereference at runtime (ASan-reported).
    assert "Mistake: read a moved-from buffer" in html
    assert "SEGV" in html


def test_runtime_gotchas_show_runtime_badge(html):
    # The B engine change renders a runtime crash as an amber "Runtime error"
    # badge, distinct from a compile failure.
    assert "Runtime error" in html
