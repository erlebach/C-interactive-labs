# cpp_labs/tests/test_svg_frames_anatomy.py
from cpp_labs.html_renderer import _svg_frames_anatomy


def test_anatomy_lists_every_slot_with_size():
    pd = {"type": "frames", "ptrbytes": "8",
          "live": "main:0x7ffe40:r:4:0,foo:0x7ffe20:t:4:4"}
    html = _svg_frames_anatomy(pd, "sf-an")
    assert 'role="img"' in html
    assert "return address" in html
    assert "saved frame" in html
    assert "8 B" in html and "4 B" in html        # ptr-sized + int-sized slots
    assert "0x7ffe40" in html                     # measured local (red)
    assert "parameter" in html                    # foo has a param (pbytes=4)


def test_anatomy_measured_local_addr_present_for_each_frame():
    pd = {"type": "frames", "ptrbytes": "8",
          "live": "main:0x7ffe40:r:4:0,foo:0x7ffe20:t:4:4"}
    html = _svg_frames_anatomy(pd, "sf-an")
    assert "0x7ffe40" in html and "0x7ffe20" in html
