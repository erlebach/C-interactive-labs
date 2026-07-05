# cpp_labs/tests/test_zoomable.py
from cpp_labs.components import zoomable


def test_zoomable_wraps_without_duplicating_inner():
    inner = "<svg id='the-only-svg'></svg>"
    html = zoomable("z", inner)
    assert html.count("the-only-svg") == 1          # inner appears exactly once
    assert html.count('type="checkbox"') == 1       # one open/close control
    assert "Enlarge" in html                         # visible open affordance
    assert "zoom-body" in html
    assert "zoom-content" in html                    # content wrapper (stacks above backdrop)


def test_zoomable_overlay_checkbox_unchecked_by_default():
    # the open/close checkbox must not start checked (overlay closed by default)
    html = zoomable("z", "<svg></svg>")
    assert 'class="zoom-cb" id="z-zcb" aria-label="Enlarge diagram">' in html


def test_zoomable_has_three_zoom_levels_with_fit_default():
    html = zoomable("z", "<svg></svg>")
    assert html.count('type="radio"') == 3           # Fit / 1.5x / 2x
    assert "Fit" in html and "1.5" in html and "2×" in html
    # exactly one preselected zoom level (Fit); the open checkbox is NOT checked
    assert html.count(" checked") == 1


def test_zoomable_enlarges_svg_beating_inline_cap():
    # the wrapped SVG's inline max-width cap is overridden so it actually grows
    html = zoomable("z", "<svg></svg>")
    assert "max-width:none !important" in html
    assert "height:calc(100vh - 7rem) !important" in html   # Fit fills the viewport
