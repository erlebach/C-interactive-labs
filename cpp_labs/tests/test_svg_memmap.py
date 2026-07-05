# cpp_labs/tests/test_svg_memmap.py
from cpp_labs.html_renderer import svg_renderer


def test_memmap_renders_all_regions():
    pd = {"type": "memmap",
          "regions": "text:0x55f180:main,data:0x5601a4:g_seed,"
                     "bss:0x5601c8:g_count,heap:0x561a20:new_int,"
                     "stack:0x7ffe40:local"}
    html = svg_renderer(pd, "mm")
    assert 'role="img"' in html
    for region in ("text", "data", "bss", "heap", "stack"):
        assert region in html
    assert "0x7ffe40" in html and "0x55f180" in html
    assert html.count("<rect") >= 5


def test_memmap_missing_regions_degrade():
    assert 'role="img"' in svg_renderer({"type": "memmap"}, "mm")
