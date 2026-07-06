import re
import shutil

import pytest
from pathlib import Path

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "template_subject.rail.yaml"

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
    # Deterministic g++ stdout, byte-for-byte — the primary correctness gate.
    assert "x = 42" in html          # ts_value (both int and double tabs)
    assert "count = 2" in html       # ts_method
    assert "count = 1" in html       # ts_gotcha, Correct case


def test_no_diagram(html):
    # Every topic is diagram:false → no figure at all; WCAG svg/role invariant holds.
    assert 'role="img"' not in html
    assert html.count("<svg") == html.count('role="img"')


def test_gotcha_error_box(html):
    # The Mistake case fails to compile → a real red compiler-error console.
    assert "out--err" in html


def test_correct_mistake_labels(html):
    assert "Correct: provide the accessor" in html
    assert "Mistake: omit the accessor" in html


def test_id_uniqueness(html):
    ids = re.findall(r'id="([^"]+)"', html)
    assert len(ids) == len(set(ids))
