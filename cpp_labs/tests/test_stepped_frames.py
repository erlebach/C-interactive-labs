# cpp_labs/tests/test_stepped_frames.py
from cpp_labs.components import stepped_frames, frames_anatomy_details, _demo_variant_body


def _steps():
    return [
        {"type": "frames", "ptrbytes": "8", "step": "1", "live": "main:0x40:r:4:0"},
        {"type": "frames", "ptrbytes": "8", "step": "2",
         "live": "main:0x40:r:4:0,foo:0x20:t:4:4"},
        {"type": "frames", "ptrbytes": "8", "step": "3", "live": "main:0x40:r:4:0"},
    ]


def test_stepped_frames_makes_one_view_and_radio_per_step():
    html = stepped_frames("sf", _steps())
    assert html.count('type="radio"') == 3
    assert html.count("<svg") >= 3            # one frame svg per step
    # deepest step (2 frames) is selected by default
    assert "checked" in html


def test_stepped_frames_ghosts_reclaimed_frame():
    # step 3 has only main live but foo was live at step 2 -> foo drawn ghost
    html = stepped_frames("sf", _steps())
    assert "reclaimed on return" in html


def test_frames_anatomy_details_is_a_disclosure():
    pd = {"type": "frames", "ptrbytes": "8", "live": "main:0x40:r:4:0"}
    html = frames_anatomy_details("sf-an", pd)
    assert "<details" in html and "Show full frame anatomy" in html
    assert 'role="img"' in html


def test_demo_variant_body_uses_stepper_when_steps_present():
    v = {"code_html": "<pre>x</pre>", "ok": True, "failed": False,
         "stdout": "enter main", "stderr": "", "bytes": [],
         "ptrdata": {"type": "frames", "ptrbytes": "8", "live": "main:0x40:r:4:0"},
         "ptrdata_steps": _steps(), "error_kind": None}
    html = _demo_variant_body("t", v, "cap", diagram=True)
    assert html.count('type="radio"') == 3        # stepper rendered
    assert "Show full frame anatomy" in html      # anatomy details present
