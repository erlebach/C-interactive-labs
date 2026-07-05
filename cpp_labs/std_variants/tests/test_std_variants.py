import shutil
import pytest
from pathlib import Path

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "std_variants.rail.yaml"

pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_all_standard_tabs_present(html):
    # optional/auto_return/make_unique span C++11/14/17; spaceship adds 17/20.
    for label in ("C++11", "C++14", "C++17", "C++20"):
        assert label in html, f"missing standard tab {label!r}"


def test_old_standard_shows_compile_failure(html):
    # Every demo's oldest tab is a genuine compile error (red), not a warning.
    assert "Compile failed" in html


def test_each_demo_runs_on_its_modern_standard(html):
    # The green tabs actually run and print their result (one string per demo).
    for out in (
        "square(7) = 49",     # auto_return
        "*p = 42",            # make_unique
        "value: 42",          # optional
        "now holds: hello",   # variant
        "filename: hw1.cpp",  # filesystem
        "sum = 10",           # span
        "twice(21) = 42",     # concepts
        "a is older: true",   # spaceship
    ):
        assert out in html, f"missing baked output {out!r}"


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ("<script src", "<link", 'href="http'):
        assert bad not in html
