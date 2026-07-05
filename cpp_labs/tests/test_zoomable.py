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


def test_zoomable_has_five_zoom_levels_with_fit_default():
    html = zoomable("z", "<svg></svg>")
    assert html.count('type="radio"') == 5           # 0.5x / 0.75x / Fit / 1.5x / 2x
    for lab in ("0.5×", "0.75×", "Fit", "1.5×", "2×"):
        assert lab in html
    # exactly one preselected zoom level (Fit); the open checkbox is NOT checked
    assert html.count(" checked") == 1


def test_zoomable_enlarges_svg_beating_inline_cap():
    # the wrapped SVG's inline max-width cap is overridden so it actually grows
    html = zoomable("z", "<svg></svg>")
    assert "max-width:none !important" in html
    assert "height:40vh !important" in html      # Fit = 40% of window height (base)
    assert "height:20vh !important" in html      # 0.5x of the 40vh base
    assert "height:80vh !important" in html      # 2x of the 40vh base
