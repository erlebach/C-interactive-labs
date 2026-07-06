# Copy to cpp_labs/<subject>/tests/test_<subject>.py and adapt the assertions.
# Tests are compiler-gated; assert EXACT baked stdout (the primary correctness gate).
import re
import shutil

import pytest
from pathlib import Path

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "my_subject.rail.yaml"

pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ("<script src", "<link", 'href="http', 'src="http'):
        assert bad not in html


def test_exact_baked_output(html):
    assert "x = 42" in html          # replace with your program's real stdout


def test_diagram_invariant(html):
    # WCAG: every <svg> carries role="img". For diagram:false subjects both are 0.
    assert html.count("<svg") == html.count('role="img"')


def test_id_uniqueness(html):
    ids = re.findall(r'id="([^"]+)"', html)
    assert len(ids) == len(set(ids))
