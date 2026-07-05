# cpp_labs/stackframes/tests/test_stackframes.py
import re
import shutil
import pytest
from pathlib import Path

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None

LAYOUT = Path(__file__).parents[1] / "layouts" / "stackframes.rail.yaml"


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++")


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ("<script src", "<link", 'href="http', "src="):
        assert bad not in html


def test_traces_present(html):
    for s in (
        "enter main",
        "enter greet",
        "leave greet",
        "enter compute",
        "enter square",
        "leave square",
        "enter countdown",
        "leave countdown",
    ):
        assert s in html, f"missing trace: {s!r}"


def test_single_call_layout_summary(html):
    assert "frame slots: local=4 B, return addr=8 B, saved fp=8 B" in html


def test_locals_two_tabs(html):
    assert "without locals" in html and "with locals" in html


def test_memmap_ordering_booleans(html):
    for s in (
        "text &lt; data? 1",
        "data &lt; bss? 1",
        "bss &lt; heap? 1",
        "heap &lt; stack? 1",
    ):
        assert s in html, f"missing memmap assertion: {s!r}"


def test_dangling_gotcha_surfaces_error(html):
    assert "out--err" in html  # red compile-error console
    assert (
        "reference to stack memory" in html
        or "return-local-addr" in html
        or "reference to local" in html
    ), "expected a dangling-ref compiler diagnostic"


def test_stepper_present(html):
    assert 'type="radio"' in html  # stepped diagrams exist
    assert "Show full frame anatomy" in html  # anatomy disclosures


def test_wcag_svg_role_invariant(html):
    assert html.count("<svg") == html.count('role="img"'), (
        f"svg count {html.count('<svg')} != role=img count {html.count('role=\"img\"')}"
    )


def test_unique_dom_ids(html):
    ids = re.findall(r'id="([^"]+)"', html)
    dups = sorted({i for i in ids if ids.count(i) > 1})
    assert not dups, f"duplicate DOM ids: {dups}"


def test_memory_glossary_present(html):
    assert "Memory glossary" in html
    assert "zero-filled at program start" in html      # the bss definition
    assert "grows toward lower addresses" in html       # the stack definition


def test_anatomy_is_step_synced(html):
    # Before the fix the anatomy only ever showed main() (local: r). The
    # recursion example's deepest step now renders countdown frames, whose
    # local is n -> "local: n" appears only if per-step anatomy works.
    assert "local: n" in html


def test_enlarge_control_present(html):
    assert "Enlarge" in html and "zoom-body" in html


def test_wider_diagram_ratio(html):
    assert "minmax(0,2fr) minmax(0,1fr)" in html
