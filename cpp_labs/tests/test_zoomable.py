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


def test_zoomable_has_five_zoom_levels_default_1_5x():
    html = zoomable("z", "<svg></svg>")
    assert html.count('type="radio"') == 5           # 0.5x / 0.75x / 1x / 1.5x / 2x
    for lab in ("0.5×", "0.75×", "1×", "1.5×", "2×"):
        assert lab in html
    # exactly one preselected zoom level (1.5x); the open checkbox is NOT checked
    assert html.count(" checked") == 1


def test_zoomable_scales_whole_panel_via_css_zoom():
    # a single CSS `zoom` on the whole .zoom-content panel — not per-SVG resizing
    html = zoomable("z", "<svg></svg>")
    assert "zoom:0.5" in html and "zoom:1.5" in html and "zoom:2" in html
    # no per-SVG height/max-width overrides remain (that broke the layout)
    assert "!important" not in html


def test_zoomable_zoom_buttons_have_visible_keyboard_focus():
    # WCAG 2.4.7: the hidden zoom-level radios forward a focus ring to their labels
    html = zoomable("z", "<svg></svg>")
    assert ":focus-visible ~ .zoom-bar label[for=z-zl0]" in html
    assert "outline:3px solid var(--accent)" in html
