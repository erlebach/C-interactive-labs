# cpp_labs/tests/test_svg_frames.py
from cpp_labs.html_renderer import svg_renderer, _parse_frames


def test_parse_frames_splits_live():
    pb, frames = _parse_frames(
        {"ptrbytes": "8", "live": "main:0x40:r:4:0,foo:0x20:t:4:4"}
    )
    assert pb == 8
    assert [f["name"] for f in frames] == ["main", "foo"]
    assert frames[1]["addr"] == "0x20" and frames[1]["local"] == "t"
    assert frames[1]["bytes"] == 4 and frames[1]["pbytes"] == 4


def test_frames_renders_one_box_per_frame():
    pd = {"type": "frames", "ptrbytes": "8",
          "live": "main:0x40:r:4:0,foo:0x20:t:4:4"}
    html = svg_renderer(pd, "sf")
    assert 'role="img"' in html          # accessible
    assert html.count("<rect") >= 2      # a box per frame
    assert "main()" in html and "foo()" in html
    assert "0x40" in html and "0x20" in html   # real addresses drawn
    assert "SP" in html                  # stack-pointer marker on innermost


def test_frames_missing_keys_degrade():
    # No 'live' at all -> no crash, still an accessible svg.
    html = svg_renderer({"type": "frames"}, "sf")
    assert 'role="img"' in html
