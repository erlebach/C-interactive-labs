# cpp_labs/tests/test_zoomable.py
from cpp_labs.components import zoomable


def test_zoomable_wraps_without_duplicating_inner():
    inner = "<svg id='the-only-svg'></svg>"
    html = zoomable("z", inner)
    assert html.count("the-only-svg") == 1          # inner appears exactly once
    assert html.count('type="checkbox"') == 1       # one control
    assert "Enlarge" in html                         # visible open affordance
    assert "zoom-body" in html


def test_zoomable_default_state_is_not_fixed_overlay():
    # The overlay styling is gated behind :checked — the checkbox is unchecked
    # by default, so no ' checked' attribute is emitted on the input.
    html = zoomable("z", "<svg></svg>")
    assert " checked" not in html
