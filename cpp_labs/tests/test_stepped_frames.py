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
    assert html.count('name="t-md-step"') == 3     # 3 stepper step radios
    assert "zoom-content" in html                   # wrapped in the zoom lightbox
    assert "Show full frame anatomy" in html       # anatomy present (in stepper now)
    assert "Enlarge" in html                        # zoomable lightbox present
    assert "minmax(0,2fr) minmax(0,1fr)" in html    # wider diagram column for frames
    # step-synced anatomy: the deepest step's anatomy names the deeper frame
    assert "foo()" in html


def test_stepped_frames_no_anatomy_by_default():
    html = stepped_frames("sf", _steps())
    assert "Show full frame anatomy" not in html


def test_stepped_frames_anatomy_is_per_step():
    html = stepped_frames("sf", _steps(), with_anatomy=True)
    assert "Show full frame anatomy" in html
    # one anatomy view per step (3), each gated by its radio
    assert html.count("sf-an") >= 3
    # the deepest step (main+foo) anatomy names both frames + real slots
    assert "foo()" in html and "return address" in html


def test_demo_variant_body_pointer_path_unchanged():
    # A pointer variant (ptype not frames/memmap, no ptrdata_steps) must keep the
    # original 3:1 column and NOT get the zoomable lightbox — the six pointer
    # renderers are unaffected by the frame-diagram rewire.
    v = {"code_html": "<pre>x</pre>", "ok": True, "failed": False,
         "stdout": "", "stderr": "", "bytes": [],
         "ptrdata": {"type": "raw", "addr": "0x1", "value": "0x2"},
         "ptrdata_steps": [], "error_kind": None}
    html = _demo_variant_body("t", v, "cap", diagram=True)
    assert "minmax(0,3fr) minmax(0,1fr)" in html      # unchanged ratio
    assert "zoom-body" not in html                      # no lightbox
    assert "Show full frame anatomy" not in html        # no frame anatomy


def test_stepped_frames_step_buttons_have_visible_keyboard_focus():
    # WCAG 2.4.7: the hidden step radios forward a focus ring to their number labels
    html = stepped_frames("sf", _steps())
    assert ":focus-visible ~ .sf-steps label[for=sf-s0]" in html
    assert "outline:3px solid var(--accent)" in html
