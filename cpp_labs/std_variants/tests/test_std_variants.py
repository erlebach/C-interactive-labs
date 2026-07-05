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


def test_three_standard_tabs(html):
    for label in ("C++11", "C++17", "C++20"):
        assert label in html, f"missing standard tab {label!r}"


def test_cpp11_shows_compile_failure(html):
    # The C++11 variant must not compile std::optional.
    assert "Compile failed" in html


def test_modern_standard_shows_output(html):
    # C++17 / C++20 compile and print "value: 42".
    assert "value: 42" in html


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ("<script src", "<link", 'href="http'):
        assert bad not in html
