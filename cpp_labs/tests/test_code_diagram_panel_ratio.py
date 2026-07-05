# cpp_labs/tests/test_code_diagram_panel_ratio.py
from cpp_labs.components import code_diagram_panel


def test_default_ratio_is_3_to_1():
    html = code_diagram_panel("cdp", "<pre>c</pre>", "<svg></svg>")
    assert "minmax(0,3fr) minmax(0,1fr)" in html


def test_custom_ratio_2_to_1():
    html = code_diagram_panel("cdp", "<pre>c</pre>", "<svg></svg>", ratio=(2, 1))
    assert "minmax(0,2fr) minmax(0,1fr)" in html
    assert "<pre>c</pre>" in html and "<svg></svg>" in html
