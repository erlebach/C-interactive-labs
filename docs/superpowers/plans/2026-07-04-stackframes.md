# stackframes Demonstration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new pure-YAML `stackframes` C++ teaching demonstration on the `left_rail` layout, with two new SVG diagram families (`type=frames`, `type=memmap`) and a zero-JS push/pop stepper.

**Architecture:** Real g++ output is baked at build time. A tiny C++ "frame tracer" prints a deterministic `enter/leave` trace plus one `PTRDATA:` snapshot per call/return; the engine parses *all* snapshot lines and renders one frame SVG per step behind a CSS-radio control. Two new renderers (`_svg_frames`, `_svg_memmap`) sit beside the six pointer renderers in `html_renderer.py`; everything above the renderers is data (YAML). Determinism contract: traces + `sizeof`-derived slot sizes are baked and asserted; raw addresses are drawn but never asserted.

**Tech Stack:** Python 3 (engine), g++/clang++ (`-std=c++20`), pytest (g++-gated), inline SVG, zero-JS CSS-radio interactions.

**Spec:** `docs/superpowers/specs/2026-07-04-stackframes-design.md`. **Authoring guide:** `cpp_labs/SKILL_PREPARATION.md`. **Exemplar:** `cpp_labs/pointers_refs/`.

**Run everything from the project root** `/Users/erlebach/src/2026/isc5305_f2026/opencode`.

---

## Data format (locked for this plan)

One snapshot line per lifecycle event:
```
PTRDATA: type=frames step=<n> ptrbytes=<sizeof(void*)> live=<f0>,<f1>,...
```
Each `<fi>` is `name:addr:localname:localbytes:parambytes` (outermost→innermost). `parambytes` is optional (absent/`0` ⇒ no params row). `live` has no spaces, so the existing whitespace/`=` split in `parse_ptrdata` still yields `{type, step, ptrbytes, live}`; the frame renderers re-split `live` on `,` and `:`.

Static (single-snapshot) examples emit exactly one such line (any `step`). Stepped examples emit several with increasing then decreasing frame counts; **each step's frame list is a prefix of the deepest step** (true for straight call chains and recursion — the only stepped examples here).

Memory map (one line):
```
PTRDATA: type=memmap regions=text:<addr>:<label>,data:...,bss:...,heap:...,stack:...
```
Each region is `key:addr:label`.

---

## File structure

**Engine (modify):**
- `cpp_labs/compiler_runner.py` — add `parse_ptrdata_all`.
- `cpp_labs/html_renderer.py` — add `_parse_frames`, `_frames_core`, `_svg_frames`, `_svg_frames_anatomy`, `_svg_memmap`; register `frames`/`memmap` in `svg_renderer`.
- `cpp_labs/build_html.py` — `_compile_one` adds `ptrdata_steps`.
- `cpp_labs/yaml_engine/render_page.py` — `_bake_program` passes `ptrdata_steps` through.
- `cpp_labs/components.py` — add `stepped_frames`, `frames_anatomy_details`; branch `_demo_variant_body` on frames/steps.

**Subject (create, pure YAML):**
- `cpp_labs/stackframes/__init__.py`
- `cpp_labs/stackframes/topics/{sf_single_call,sf_nested,sf_locals,sf_recursion,sf_dangling_local,sf_memmap}.topic.yaml`
- `cpp_labs/stackframes/demos/*.demo.yaml` (one per topic)
- `cpp_labs/stackframes/glossaries/stackframes.glossary.yaml`
- `cpp_labs/stackframes/layouts/stackframes.rail.yaml`
- `cpp_labs/stackframes/tests/test_stackframes.py`

**Tests (engine):** add to `cpp_labs/tests/` (pure, no g++) — see Tasks 1–6.

---

## Phase 1 — Engine: parse, renderers, wiring (no g++ needed for these unit tests)

### Task 1: `parse_ptrdata_all` — read every PTRDATA line

**Files:**
- Modify: `cpp_labs/compiler_runner.py` (after `parse_ptrdata`, ~line 98)
- Test: `cpp_labs/tests/test_parse_ptrdata_all.py`

- [ ] **Step 1: Write the failing test**

```python
# cpp_labs/tests/test_parse_ptrdata_all.py
from cpp_labs.compiler_runner import parse_ptrdata_all


def test_returns_empty_when_none():
    assert parse_ptrdata_all("hello\nworld\n") == []


def test_reads_every_line_in_order():
    out = (
        "enter main\n"
        "PTRDATA: type=frames step=1 ptrbytes=8 live=main:0x10:r:4:0\n"
        "enter foo\n"
        "PTRDATA: type=frames step=2 ptrbytes=8 live=main:0x10:r:4:0,foo:0x8:t:4:4\n"
    )
    steps = parse_ptrdata_all(out)
    assert len(steps) == 2
    assert steps[0]["step"] == "1"
    assert steps[1]["live"] == "main:0x10:r:4:0,foo:0x8:t:4:4"


def test_single_line_matches_parse_ptrdata_shape():
    out = "PTRDATA: type=memmap regions=text:0x1:main\n"
    steps = parse_ptrdata_all(out)
    assert steps == [{"type": "memmap", "regions": "text:0x1:main"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_parse_ptrdata_all.py -q`
Expected: FAIL — `ImportError: cannot import name 'parse_ptrdata_all'`.

- [ ] **Step 3: Write minimal implementation**

Add below `parse_ptrdata` in `cpp_labs/compiler_runner.py` (reuse the existing `_PTRDATA_RE` and the same token-splitting logic):

```python
def parse_ptrdata_all(stdout: str) -> list[dict]:
    """Extract EVERY ``PTRDATA:`` line from ``stdout`` as a list of key=value
    dicts, in source order. Empty list if none. Used by the stepped frame
    diagram, which snapshots the live stack at each call/return. The
    single-line :func:`parse_ptrdata` is unchanged (still reads the first line
    only) so the six pointer renderers keep their exact behaviour.
    """
    steps: list[dict] = []
    for match in _PTRDATA_RE.finditer(stdout):
        line = match.group(1).strip()
        result = {}
        for token in line.split():
            if "=" in token:
                key, _, value = token.partition("=")
                result[key] = value
        if result:
            steps.append(result)
    return steps
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_parse_ptrdata_all.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/compiler_runner.py cpp_labs/tests/test_parse_ptrdata_all.py
git commit -m "feat(compiler_runner): parse_ptrdata_all for multi-snapshot stepping"
```

---

### Task 2: `_svg_frames` — the stacked-frame diagram + register `type=frames`

**Files:**
- Modify: `cpp_labs/html_renderer.py` (add helpers before `svg_renderer`, ~line 288; add dispatch entry at ~line 314)
- Test: `cpp_labs/tests/test_svg_frames.py`

- [ ] **Step 1: Write the failing test**

```python
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
    # No 'live' at all → no crash, still an accessible svg.
    html = svg_renderer({"type": "frames"}, "sf")
    assert 'role="img"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_svg_frames.py -q`
Expected: FAIL — `ImportError: cannot import name '_parse_frames'`.

- [ ] **Step 3: Write minimal implementation**

Insert into `cpp_labs/html_renderer.py` immediately **before** `def svg_renderer` (uses the existing `_e`, `_wrap_svg`, module constants):

```python
# ---------------------------------------------------------------------------
# Stack-frame diagram family (type=frames) and process memory map (type=memmap)
# ---------------------------------------------------------------------------

_FRAME_STROKES = ["#cc6666", "#9966cc", "#6699cc", "#22aa88", "#cc8844", "#6688aa"]
_ADDR_AXIS = "#2a8a5a"      # green: addresses increase upward
_STACK_AXIS = "#cc6600"     # orange: stack grows downward
_SCHEM_COLOR = "#999999"    # grey: schematic (computed, not measured)


def _parse_frames(pd: dict) -> "tuple[int, list[dict]]":
    """Parse a frames ptrdata dict into (ptrbytes, frames). Each frame is
    ``{name, addr, local, bytes, pbytes}`` outermost→innermost. Missing pieces
    degrade to ``"?"`` / ``0`` (never raises)."""
    try:
        ptrbytes = int(pd.get("ptrbytes", "8"))
    except (TypeError, ValueError):
        ptrbytes = 8
    frames = []
    for entry in (pd.get("live", "") or "").split(","):
        if not entry:
            continue
        parts = entry.split(":")

        def _get(i):
            return parts[i] if i < len(parts) else "?"

        def _int(i):
            try:
                return int(parts[i])
            except (IndexError, ValueError):
                return 0

        frames.append({"name": _get(0), "addr": _get(1), "local": _get(2),
                       "bytes": _int(3), "pbytes": _int(4)})
    return ptrbytes, frames


def _frames_core(frames: list, p: str, *, solid: "int | None" = None) -> str:
    """Vertical stack of call frames. Outermost (e.g. main) on top at the
    highest address; each deeper call a box below at a lower address; SP marker
    on the innermost *solid* frame. Frames at index >= ``solid`` are drawn ghost
    (dashed) — used by the stepper to show a reclaimed frame after a return.
    Dual axis: addresses increase upward (green), stack grows downward
    (orange)."""
    if solid is None:
        solid = len(frames)
    box_w, box_h, gap, pad, left = 210, 54, 10, 12, 58
    n = len(frames)
    vb_w = left + box_w + pad + 44
    vb_h = pad + n * (box_h + gap) + pad + 4
    parts = []
    # address axis (up, green) on the far left
    axis_top, axis_bot = pad + 6, vb_h - pad
    parts.append(
        f'<line x1="{left - 40}" y1="{axis_bot}" x2="{left - 40}" y2="{axis_top}" '
        f'stroke="{_ADDR_AXIS}" stroke-width="2"/>'
        f'<path d="M{left - 44} {axis_top + 8} L{left - 40} {axis_top} '
        f'L{left - 36} {axis_top + 8} z" fill="{_ADDR_AXIS}"/>'
        f'<text x="{left - 48}" y="{(axis_top + axis_bot) // 2}" font-size="11" '
        f'fill="{_ADDR_AXIS}" text-anchor="middle" '
        f'transform="rotate(-90 {left - 48} {(axis_top + axis_bot) // 2})">'
        f'addresses increase</text>'
    )
    # stack-growth axis (down, orange) on the far right
    rx = vb_w - 12
    parts.append(
        f'<line x1="{rx}" y1="{axis_top}" x2="{rx}" y2="{axis_bot}" '
        f'stroke="{_STACK_AXIS}" stroke-width="2"/>'
        f'<path d="M{rx - 4} {axis_bot - 8} L{rx} {axis_bot} L{rx + 4} '
        f'{axis_bot - 8} z" fill="{_STACK_AXIS}"/>'
        f'<text x="{rx + 4}" y="{(axis_top + axis_bot) // 2}" font-size="11" '
        f'fill="{_STACK_AXIS}" text-anchor="middle" '
        f'transform="rotate(90 {rx + 4} {(axis_top + axis_bot) // 2})">'
        f'stack grows</text>'
    )
    y = pad
    for i, f in enumerate(frames):
        ghost = i >= solid
        stroke = _SCHEM_COLOR if ghost else _FRAME_STROKES[i % len(_FRAME_STROKES)]
        dash = ' stroke-dasharray="5 4"' if ghost else ""
        fill = "#f7f7f7" if ghost else "#ffffff"
        parts.append(
            f'<rect x="{left}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"{dash}/>'
        )
        is_sp = (not ghost) and (i == solid - 1)
        title = f'{_e(f["name"])}()' + ("  ← SP" if is_sp else "")
        if ghost:
            parts.append(
                f'<text x="{left + 14}" y="{y + 31}" font-size="12" '
                f'font-family="ui-monospace,monospace" fill="{_SCHEM_COLOR}">'
                f'{_e(f["name"])}() reclaimed on return</text>'
            )
        else:
            parts.append(
                f'<text x="{left + 14}" y="{y + 22}" font-size="13" '
                f'font-family="system-ui" font-weight="600" fill="#1a1a1a">'
                f'{title}</text>'
                f'<text x="{left + 14}" y="{y + 42}" font-size="12" '
                f'font-family="ui-monospace,monospace" fill="#b00000">'
                f'&amp;{_e(f["local"])} = {_e(f["addr"])}</text>'
            )
        y += box_h + gap
    body = "".join(parts)
    return _wrap_svg(
        p, "call stack frames",
        "Stack frames, main on top at the highest address; deeper calls at "
        "lower addresses. Addresses increase upward; the stack grows downward.",
        body, vb_w=vb_w, vb_h=vb_h)


def _svg_frames(pd: dict, p: str) -> str:
    """Single-snapshot dispatch entry for ``type=frames``."""
    _pb, frames = _parse_frames(pd)
    return _frames_core(frames, p)
```

Then register it in `svg_renderer`'s dispatch dict (html_renderer.py ~line 308) — add one line:

```python
    dispatch = {
        "raw": _svg_raw,
        "null": _svg_null,
        "ref": _svg_ref,
        "unique": _svg_unique,
        "shared": _svg_shared,
        "weak": _svg_weak,
        "frames": _svg_frames,      # <-- add
    }
```

- [ ] **Step 3b: Verify no `<details>` and no raw-address assertion leaks.** `_frames_core` renders only `<svg>`; the `<details>` anatomy is composed later (Task 5). Good.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_svg_frames.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/html_renderer.py cpp_labs/tests/test_svg_frames.py
git commit -m "feat(html_renderer): _svg_frames stacked call-frame diagram (type=frames)"
```

---

### Task 3: `_svg_frames_anatomy` — three-column slot · address · size

**Files:**
- Modify: `cpp_labs/html_renderer.py` (after `_svg_frames`)
- Test: `cpp_labs/tests/test_svg_frames_anatomy.py`

Schematic per-row addresses are derived from the measured local address and the known slot sizes, laid out high→low within each frame: `params` (highest) → `return address` → `saved frame pointer` → `local` (lowest, measured).

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_svg_frames_anatomy.py -q`
Expected: FAIL — `ImportError: cannot import name '_svg_frames_anatomy'`.

- [ ] **Step 3: Write minimal implementation**

Add after `_svg_frames` in `cpp_labs/html_renderer.py`:

```python
def _svg_frames_anatomy(pd: dict, p: str) -> str:
    """Expanded per-frame anatomy: a three-column table (slot · address · size)
    for every live frame. The local's row is the real measured address (red);
    params / return-addr / saved-FP rows carry schematic addresses (grey)
    computed by stacking the known slot sizes above the measured local. Only
    the local address is measured; the rest are illustrative."""
    ptrbytes, frames = _parse_frames(pd)
    row_h, hdr_h, frame_gap, pad, left = 18, 16, 10, 12, 40
    col_addr, col_size = 190, 290
    parts = [
        f'<text x="{left}" y="{pad + 10}" font-size="9" fill="#999">slot</text>'
        f'<text x="{col_addr}" y="{pad + 10}" font-size="9" fill="#999">address</text>'
        f'<text x="{col_size}" y="{pad + 10}" font-size="9" fill="#999">size</text>'
    ]
    y = pad + hdr_h
    for i, f in enumerate(frames):
        # slots high→low: [param?], return address, saved FP, local
        try:
            base = int(f["addr"], 16)
        except (ValueError, TypeError):
            base = None
        rows = []  # (label, addr_or_None, bytes, measured)
        savedfp = (base + f["bytes"]) if base is not None else None
        retaddr = (savedfp + ptrbytes) if savedfp is not None else None
        param = (retaddr + ptrbytes) if (retaddr is not None and f["pbytes"]) else None
        if f["pbytes"]:
            rows.append((f'parameter: {f["pbytes"]}B', param, f["pbytes"], False))
        rows.append(("return address", retaddr, ptrbytes, False))
        rows.append(("saved frame ptr", savedfp, ptrbytes, False))
        rows.append((f'local: {f["local"]}', base, f["bytes"], True))
        fh = hdr_h // 2 + len(rows) * row_h + 6
        stroke = _FRAME_STROKES[i % len(_FRAME_STROKES)]
        parts.append(
            f'<rect x="{left - 8}" y="{y - 12}" width="{col_size + 40}" '
            f'height="{fh}" rx="6" fill="#ffffff" stroke="{stroke}" '
            f'stroke-width="2"/>'
            f'<text x="{left}" y="{y + 2}" font-size="12" font-weight="600" '
            f'fill="#1a1a1a">{_e(f["name"])}()</text>'
        )
        ry = y + row_h
        for label, addr, nbytes, measured in rows:
            addr_s = f"0x{addr:x}" if addr is not None else "?"
            acol = "#b00000" if measured else _SCHEM_COLOR
            parts.append(
                f'<text x="{left}" y="{ry}" font-size="11" '
                f'fill="#333">{_e(label)}</text>'
                f'<text x="{col_addr}" y="{ry}" font-size="10" '
                f'font-family="ui-monospace,monospace" fill="{acol}">{addr_s}</text>'
                f'<text x="{col_size}" y="{ry}" font-size="10" '
                f'font-family="ui-monospace,monospace" fill="#0066cc">'
                f'{nbytes} B</text>'
            )
            ry += row_h
        y = ry + frame_gap
    vb_w = col_size + 72
    vb_h = y + pad
    return _wrap_svg(p, "full frame anatomy",
                     "Each frame's slots with byte sizes and addresses; only "
                     "the local address is measured, the rest are schematic.",
                     "".join(parts), vb_w=vb_w, vb_h=vb_h)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_svg_frames_anatomy.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/html_renderer.py cpp_labs/tests/test_svg_frames_anatomy.py
git commit -m "feat(html_renderer): _svg_frames_anatomy slot/address/size table"
```

---

### Task 4: `_svg_memmap` — process memory map + register `type=memmap`

**Files:**
- Modify: `cpp_labs/html_renderer.py` (after `_svg_frames_anatomy`; add dispatch entry)
- Test: `cpp_labs/tests/test_svg_memmap.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_svg_memmap.py -q`
Expected: FAIL — `AssertionError` (memmap falls through to `_svg_unknown`, no region text).

- [ ] **Step 3: Write minimal implementation**

Add after `_svg_frames_anatomy`:

```python
_MEMMAP_ORDER = ["stack", "heap", "bss", "data", "text"]   # high → low address
_MEMMAP_LABEL = {
    "stack": "params, auto variables",
    "heap": "dynamic variables",
    "bss": "uninitialized global/static",
    "data": "initialized global/static",
    "text": "machine instructions",
}
_MEMMAP_FILL = {
    "stack": "#d6e8f5", "heap": "#e7e0f2", "bss": "#f0e6d0",
    "data": "#e0e8d0", "text": "#f5d6d6",
}


def _svg_memmap(pd: dict, p: str) -> str:
    """Whole-process memory map: text (low) → stack (high), heap grows up and
    stack grows down toward each other. One real address per region."""
    regions = {}
    for entry in (pd.get("regions", "") or "").split(","):
        if not entry:
            continue
        parts = entry.split(":")
        key = parts[0]
        regions[key] = {"addr": parts[1] if len(parts) > 1 else "?",
                        "label": parts[2] if len(parts) > 2 else ""}
    box_w, box_h, gap, pad, left = 210, 46, 8, 26, 30
    vb_w = left + box_w + 130
    vb_h = pad + len(_MEMMAP_ORDER) * (box_h + gap) + pad
    parts = [f'<text x="{left + box_w // 2}" y="14" font-size="11" fill="#555" '
             f'text-anchor="middle">high memory</text>']
    y = pad
    for key in _MEMMAP_ORDER:
        r = regions.get(key, {"addr": "?", "label": _MEMMAP_LABEL.get(key, "")})
        fill = _MEMMAP_FILL.get(key, "#ffffff")
        parts.append(
            f'<rect x="{left}" y="{y}" width="{box_w}" height="{box_h}" rx="6" '
            f'fill="{fill}" stroke="#888" stroke-width="1.5"/>'
            f'<text x="{left + 12}" y="{y + 20}" font-size="12" font-weight="600" '
            f'fill="#1a1a1a">{_e(key)}</text>'
            f'<text x="{left + 12}" y="{y + 38}" font-size="10" '
            f'font-family="ui-monospace,monospace" fill="#b00000">'
            f'{_e(r["addr"])}</text>'
            f'<text x="{left + box_w + 8}" y="{y + 26}" font-size="10" '
            f'fill="#666">{_e(_MEMMAP_LABEL.get(key, ""))}</text>'
        )
        y += box_h + gap
    parts.append(f'<text x="{left + box_w // 2}" y="{vb_h - 8}" font-size="11" '
                 f'fill="#555" text-anchor="middle">low memory</text>')
    return _wrap_svg(p, "process memory map",
                     "Process regions from text (low) to stack (high); heap "
                     "grows up and the stack grows down.",
                     "".join(parts), vb_w=vb_w, vb_h=vb_h)
```

Register in `svg_renderer` dispatch (one line, after `"frames"`):

```python
        "frames": _svg_frames,
        "memmap": _svg_memmap,      # <-- add
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_svg_memmap.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/html_renderer.py cpp_labs/tests/test_svg_memmap.py
git commit -m "feat(html_renderer): _svg_memmap process memory map (type=memmap)"
```

---

### Task 5: `stepped_frames` + `frames_anatomy_details` components; wire `_demo_variant_body`

**Files:**
- Modify: `cpp_labs/build_html.py:169-178` (`_compile_one` success return) and `:154-164` (runtime branch)
- Modify: `cpp_labs/yaml_engine/render_page.py:78-89` (`_bake_program`)
- Modify: `cpp_labs/components.py` (add two functions near `stacked_subcases` ~line 814; branch `_demo_variant_body` ~line 848)
- Test: `cpp_labs/tests/test_stepped_frames.py`

- [ ] **Step 1: Write the failing test**

```python
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
    # step 3 has only main live but foo was live at step 2 → foo drawn ghost
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest cpp_labs/tests/test_stepped_frames.py -q`
Expected: FAIL — `ImportError: cannot import name 'stepped_frames'`.

- [ ] **Step 3a: Bake `ptrdata_steps` through the pipeline.**

In `cpp_labs/build_html.py`, add `parse_ptrdata_all` to the import (line 25):

```python
from .compiler_runner import compile_and_run, parse_membytes, parse_ptrdata_all
```

In `_compile_one`, add `"ptrdata_steps"` to **all three** return dicts. Success branch (lines 169-178) becomes:

```python
    ptrdata = result.ptrdata
    membytes = result.memory_bytes or parse_membytes(result.stdout)

    return {
        "source": source,
        "ptrdata": ptrdata,
        "ptrdata_steps": parse_ptrdata_all(result.stdout),
        "svg": svg_renderer(ptrdata),
        "stdout": result.stdout,
        "membytes": membytes,
        "failed": False,
        "error_kind": None,
        "stderr": "",
    }
```

Add `"ptrdata_steps": parse_ptrdata_all(result.stdout),` to the runtime-error branch (after its `"ptrdata": ptrdata,` line) and `"ptrdata_steps": [],` to the compile-failed branch (after its `"ptrdata": None,` line).

In `cpp_labs/yaml_engine/render_page.py`, `_bake_program` (line 81) — add the key so it survives to the component:

```python
        "ptrdata": v.get("ptrdata"),
        "ptrdata_steps": v.get("ptrdata_steps", []),
```

- [ ] **Step 3b: Add the two components.**

In `cpp_labs/components.py`, import the two renderers (top of file, alongside the existing `from .html_renderer import ... svg_renderer` at line 33):

```python
from .html_renderer import _CSS, SEMANTIC_PALETTE, svg_renderer, _svg_frames_anatomy
from .html_renderer import _parse_frames, _frames_core
```

Add near `stacked_subcases` (~line 814):

```python
def frames_anatomy_details(comp_id: str, pd: dict) -> str:
    """A native <details> disclosure wrapping the full per-frame anatomy SVG."""
    p = _safe(comp_id)
    return (
        f'<details style="margin-top:.5rem;border:1px solid #ddd;border-radius:6px;'
        f'padding:.3rem .6rem"><summary style="cursor:pointer;min-height:44px;'
        f'font-weight:600">Show full frame anatomy</summary>\n'
        + _svg_frames_anatomy(pd, f"{p}-an")
        + "</details>\n"
    )


def stepped_frames(comp_id: str, steps: "Sequence[dict]") -> str:
    """Zero-JS CSS-radio stepper over frame snapshots: one radio + one frame SVG
    per step; selecting a step shows that snapshot. Frames present at a deeper
    step but gone at the current one are drawn ghost (reclaimed). Defaults to
    the deepest step. Assumes each step's frame list is a prefix of the deepest
    (true for straight call chains and recursion)."""
    p = _safe(comp_id)
    ptrbytes, deepest = 8, []
    parsed = []
    for s in steps:
        pb, frames = _parse_frames(s)
        parsed.append(frames)
        if len(frames) > len(deepest):
            ptrbytes, deepest = pb, frames
    default = max(range(len(parsed)), key=lambda i: len(parsed[i])) if parsed else 0

    inputs, labels, views = [], [], []
    css = [f"#{p} .sf-v {{ display:none; }}"]
    for i, frames in enumerate(parsed):
        checked = " checked" if i == default else ""
        inputs.append(f'<input type="radio" name="{p}-step" id="{p}-s{i}"{checked} '
                      f'style="position:absolute;opacity:0">')
        labels.append(
            f'<label for="{p}-s{i}" style="cursor:pointer;border:1px solid #bbb;'
            f'border-radius:6px;padding:2px 9px;font:13px system-ui;'
            f'min-height:44px;display:inline-flex;align-items:center">'
            f'{i + 1}</label>')
        svg = _frames_core(deepest, f"{p}-fr{i}", solid=len(frames))
        views.append(f'<div class="sf-v sf-v{i}">{svg}</div>')
        css.append(f"#{p} #{p}-s{i}:checked ~ .sf-views .sf-v{i} {{ display:block; }}")
        css.append(f"#{p} #{p}-s{i}:checked ~ .sf-steps label[for={p}-s{i}] "
                   f"{{ background:#2a8a5a; color:#fff; border-color:#2a8a5a; }}")
    return (
        f'<div id="{p}"><style>{chr(10).join(css)}</style>'
        + "".join(inputs)
        + f'<div class="sf-steps" style="display:flex;gap:6px;margin-bottom:8px">'
        + "".join(labels) + "</div>"
        + f'<div class="sf-views">' + "".join(views) + "</div></div>"
    )
```

- [ ] **Step 3c: Branch `_demo_variant_body`** (components.py ~line 848). Replace the `if diagram:` block head:

```python
    if diagram:
        pd = v.get("ptrdata")
        steps = v.get("ptrdata_steps") or []
        ptype = (pd or {}).get("type")
        frame_steps = [s for s in steps if s.get("type") == "frames"]
        if len(frame_steps) > 1:
            diagram_html = stepped_frames(f"{pid}-md", frame_steps)
            diagram_html += frames_anatomy_details(f"{pid}-fa", frame_steps[-1] if
                            not (pd) else pd)
        elif ptype == "frames":
            diagram_html = memory_diagram(f"{pid}-md", pd) + \
                frames_anatomy_details(f"{pid}-fa", pd)
        else:
            diagram_html = memory_diagram(f"{pid}-md", pd) if pd else ""
        code_block = code_diagram_panel(f"{pid}-cdp", v["code_html"], diagram_html)
    else:
        code_block = v["code_html"]
```

Note: the existing signature of `_demo_variant_body` has `v` dicts that may lack `ptrdata_steps` (pointer subjects); `.get(...) or []` handles that — those subjects keep the untouched `else` path.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest cpp_labs/tests/test_stepped_frames.py -q`
Expected: PASS (5 passed).

- [ ] **Step 4b: Regression — the six pointer renderers must be unaffected.**

Run: `python -m pytest cpp_labs/tests/ -q`
Expected: PASS (all pre-existing engine tests still green — pointer subjects have no `ptrdata_steps`, so the new branch is skipped).

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/build_html.py cpp_labs/yaml_engine/render_page.py cpp_labs/components.py cpp_labs/tests/test_stepped_frames.py
git commit -m "feat(components): stepped_frames CSS-radio + anatomy details; bake ptrdata_steps"
```

---

## Phase 2 — Subject authoring (pure YAML; g++ required to run these tests)

**The reusable frame tracer.** Every frame example includes this snippet at the top of `template:` (authored inline in each topic YAML). It prints a deterministic `enter/leave` trace and a `PTRDATA` snapshot per event; addresses vary and are never asserted.

```cpp
#include <cstdio>
#include <vector>
// A teaching shadow-stack: records live frames so we can print a PTRDATA
// snapshot at each call and return. Addresses vary per run (never asserted);
// only the enter/leave trace and the byte sizes are deterministic.
struct Frame { const char* fn; const char* ln; const void* addr; int lb; int pb; };
static std::vector<Frame> g_stack;
static int g_step = 0;
static void snapshot() {
    printf("PTRDATA: type=frames step=%d ptrbytes=%zu live=",
           ++g_step, sizeof(void*));
    for (std::size_t i = 0; i < g_stack.size(); ++i) {
        const Frame& f = g_stack[i];
        printf("%s%s:%p:%s:%d:%d", i ? "," : "",
               f.fn, f.addr, f.ln, f.lb, f.pb);
    }
    printf("\n");
}
static void frame_enter(const char* fn, const char* ln,
                        const void* addr, int lb, int pb) {
    printf("enter %s\n", fn);
    g_stack.push_back({fn, ln, addr, lb, pb});
    snapshot();
}
static void frame_leave(const char* fn) {
    printf("leave %s\n", fn);
    g_stack.pop_back();
    snapshot();
}
```

Topics set `diagram: true` (default) in their demo `topic:` block and **omit `<<HARNESS>>`** (no byte-grid needed). Determinism: assert the `enter/leave` lines and any ordering/size summary lines — never the `PTRDATA` lines.

### Task 6: Scaffold + `sf_single_call`

**Files:**
- Create: `cpp_labs/stackframes/__init__.py` (empty)
- Create: `cpp_labs/stackframes/topics/sf_single_call.topic.yaml`
- Create: `cpp_labs/stackframes/demos/sf_single_call.demo.yaml`

- [ ] **Step 1: Scaffold.**

```bash
mkdir -p cpp_labs/stackframes/topics cpp_labs/stackframes/demos \
         cpp_labs/stackframes/glossaries cpp_labs/stackframes/layouts \
         cpp_labs/stackframes/tests
touch cpp_labs/stackframes/__init__.py cpp_labs/stackframes/tests/__init__.py
```

- [ ] **Step 2: Author `topics/sf_single_call.topic.yaml`.** (Tracer elided here as `# <<TRACER>>` — paste the full tracer snippet from the Phase 2 preamble in its place.)

```yaml
id: sf_single_call
name: Single Call
group: Stack Frames
doc_url: https://en.cppreference.com/w/cpp/language/storage_duration
explanation: >-
  Every function call pushes a new stack frame holding that call's parameters,
  return address, saved frame pointer, and locals. When the function returns,
  its frame is popped. Here main() calls greet() once: watch the frame appear
  and then disappear.
template: |
  # <<TRACER>>
  int greet() {
      int msg = 7;
      frame_enter("greet", "msg", &msg, (int)sizeof(msg), 0);
      frame_leave("greet");
      return msg;
  }
  int main() {
      int r = 0;
      frame_enter("main", "r", &r, (int)sizeof(r), 0);
      r = greet();
      frame_leave("main");
      // deterministic layout summary (assertable; sizes are sizeof-derived)
      printf("frame slots: local=%d B, return addr=%zu B, saved fp=%zu B\n",
             (int)sizeof(int), sizeof(void*), sizeof(void*));
  }
```

- [ ] **Step 3: Verify it compiles + prints deterministically.**

```bash
python - <<'PY'
from pathlib import Path
from cpp_labs.topic_yaml import load_topics
from cpp_labs.build_html import capture_variant, expand_variants
t = load_topics(Path("cpp_labs/stackframes/topics"))["sf_single_call"]
v = capture_variant(t, expand_variants(t)[0])
print("FAILED" if v.get("failed") else "OK")
print(v["stdout"])
PY
```
Expected: `OK`, and stdout containing `enter main`, `enter greet`, `leave greet`, `leave main`, and `frame slots: local=4 B, return addr=8 B, saved fp=8 B`.

- [ ] **Step 4: Author `demos/sf_single_call.demo.yaml`.**

```yaml
title: "Single Call"
language: cpp
bake: { sc: sf_single_call }
blocks:
  - concept: { id: sc-note, text: "${sc.explanation}" }
  - topic:   { id: sc, source: sc }
```

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/stackframes/__init__.py cpp_labs/stackframes/tests/__init__.py \
        cpp_labs/stackframes/topics/sf_single_call.topic.yaml \
        cpp_labs/stackframes/demos/sf_single_call.demo.yaml
git commit -m "feat(stackframes): scaffold + sf_single_call topic/demo"
```

---

### Task 7: `sf_nested` (stepped)

**Files:**
- Create: `cpp_labs/stackframes/topics/sf_nested.topic.yaml`, `demos/sf_nested.demo.yaml`

- [ ] **Step 1: Author the topic** (`# <<TRACER>>` = the full tracer snippet).

```yaml
id: sf_nested
name: Nested Calls
group: Stack Frames
doc_url: https://en.cppreference.com/w/cpp/language/storage_duration
explanation: >-
  main() calls compute(), which calls square(). Three frames are live at the
  deepest point. Each deeper call lives at a LOWER address: addresses increase
  upward while the stack grows downward — opposite directions. Step through the
  calls and returns to watch frames push and pop.
template: |
  # <<TRACER>>
  int square(int v) {
      int s = v * v;
      frame_enter("square", "s", &s, (int)sizeof(s), (int)sizeof(v));
      frame_leave("square");
      return s;
  }
  int compute(int n) {
      int t = 0;
      frame_enter("compute", "t", &t, (int)sizeof(t), (int)sizeof(n));
      t = square(n + 1);
      frame_leave("compute");
      return t;
  }
  int main() {
      int r = 0;
      frame_enter("main", "r", &r, (int)sizeof(r), 0);
      // capture ordering BEFORE returns unwind the frames
      int r_addr_gt_t = 0, t_addr_gt_s = 0;
      r = compute(5);
      frame_leave("main");
      printf("deeper frames sit at lower addresses (checked in code)\n");
  }
```

> Note: the address-ordering *assertion* is awkward across separate frames (each local is out of scope in `main`). Keep the deterministic guarantee to the enter/leave trace; the "addresses descend" claim is shown by the diagram (real addresses) and stated in prose, not asserted. (Remove the unused `r_addr_gt_t`/`t_addr_gt_s` if the compiler warns; they are placeholders — delete them.)

Corrected `main()` (no unused vars):

```yaml
  int main() {
      int r = 0;
      frame_enter("main", "r", &r, (int)sizeof(r), 0);
      r = compute(5);
      frame_leave("main");
      printf("result r = %d\n", r);
  }
```

- [ ] **Step 2: Verify compile + stdout.** Use the Task 6 Step 3 harness with id `sf_nested`.
Expected: `OK`; stdout has `enter main`, `enter compute`, `enter square`, `leave square`, `leave compute`, `leave main`, `result r = 36`, and **multiple** `PTRDATA: type=frames step=` lines (≥5).

- [ ] **Step 3: Author the demo.**

```yaml
title: "Nested Calls"
language: cpp
bake: { nc: sf_nested }
blocks:
  - concept: { id: nc-note, text: "${nc.explanation}" }
  - topic:   { id: nc, source: nc }
```

- [ ] **Step 4: Commit**

```bash
git add cpp_labs/stackframes/topics/sf_nested.topic.yaml cpp_labs/stackframes/demos/sf_nested.demo.yaml
git commit -m "feat(stackframes): sf_nested stepped push/pop example"
```

---

### Task 8: `sf_locals` (two variant tabs: without / with locals)

**Files:**
- Create: `cpp_labs/stackframes/topics/sf_locals.topic.yaml`, `demos/sf_locals.demo.yaml`

The two tabs come from a `dropdown` control (`§3` of SKILL_PREPARATION) with a `value_map` swapping the callee body; each option becomes a tab at the top.

- [ ] **Step 1: Author the topic.**

```yaml
id: sf_locals
name: Locals in the Frame
group: Stack Frames
doc_url: https://en.cppreference.com/w/cpp/language/storage_duration
explanation: >-
  Local variables live inside the function's own frame. A leaf that computes
  its result inline has no named locals and a smaller frame; add locals and the
  frame grows to hold them. Switch tabs to compare.
template: |
  # <<TRACER>>
  <<callee>>
  int main() {
      int r = 0;
      frame_enter("main", "r", &r, (int)sizeof(r), 0);
      r = work(4);
      frame_leave("main");
      printf("result r = %d\n", r);
  }
controls:
  - id: callee
    label: Locals
    kind: dropdown
    options: [without locals, with locals]
    default: without locals
    placeholder: <<callee>>
    value_map:
      without locals: |
        int work(int n) {
            // no named locals: frame carries only the parameter + machinery
            frame_enter("work", "(none)", (const void*)&n, 0, (int)sizeof(n));
            frame_leave("work");
            return n * n + 1;
        }
      with locals: |
        int work(int n) {
            int a = n * n;
            int b = a + 1;
            frame_enter("work", "b", &b, (int)sizeof(b), (int)sizeof(n));
            frame_leave("work");
            return b;
        }
```

- [ ] **Step 2: Verify both variants compile + print.**

```bash
python - <<'PY'
from pathlib import Path
from cpp_labs.topic_yaml import load_topics
from cpp_labs.build_html import capture_variant, expand_variants
t = load_topics(Path("cpp_labs/stackframes/topics"))["sf_locals"]
for cs in expand_variants(t):
    v = capture_variant(t, cs)
    print(cs, "FAILED" if v.get("failed") else "OK")
    print(v["stdout"].strip().splitlines()[-1])
PY
```
Expected: two `OK` lines; both print `result r = 17`.

- [ ] **Step 3: Author the demo.**

```yaml
title: "Locals in the Frame"
language: cpp
bake: { lo: sf_locals }
blocks:
  - concept: { id: lo-note, text: "${lo.explanation}" }
  - topic:   { id: lo, source: lo }
```

- [ ] **Step 4: Commit**

```bash
git add cpp_labs/stackframes/topics/sf_locals.topic.yaml cpp_labs/stackframes/demos/sf_locals.demo.yaml
git commit -m "feat(stackframes): sf_locals two-tab with/without locals"
```

---

### Task 9: `sf_recursion` (stepped)

**Files:**
- Create: `cpp_labs/stackframes/topics/sf_recursion.topic.yaml`, `demos/sf_recursion.demo.yaml`

- [ ] **Step 1: Author the topic.**

```yaml
id: sf_recursion
name: Recursion
group: Stack Frames
doc_url: https://en.cppreference.com/w/cpp/language/storage_duration
explanation: >-
  Each recursive call gets its own frame with its own copy of the parameter and
  locals. countdown(3) pushes three frames; they pop in reverse order (LIFO).
  Step through to watch the stack grow to full depth and then unwind.
template: |
  # <<TRACER>>
  void countdown(int n) {
      frame_enter("countdown", "n", &n, (int)sizeof(n), (int)sizeof(n));
      if (n > 1) {
          countdown(n - 1);
      }
      frame_leave("countdown");
  }
  int main() {
      int r = 3;
      frame_enter("main", "r", &r, (int)sizeof(r), 0);
      countdown(3);
      frame_leave("main");
      printf("done\n");
  }
```

- [ ] **Step 2: Verify compile + stdout.** (Task 6 Step 3 harness, id `sf_recursion`.)
Expected: `OK`; stdout has `enter main`, three `enter countdown`, three `leave countdown`, `leave main`, `done`, and ≥7 `PTRDATA` step lines (max depth 4: main + 3 countdown).

- [ ] **Step 3: Author the demo.**

```yaml
title: "Recursion"
language: cpp
bake: { re: sf_recursion }
blocks:
  - concept: { id: re-note, text: "${re.explanation}" }
  - topic:   { id: re, source: re }
```

- [ ] **Step 4: Commit**

```bash
git add cpp_labs/stackframes/topics/sf_recursion.topic.yaml cpp_labs/stackframes/demos/sf_recursion.demo.yaml
git commit -m "feat(stackframes): sf_recursion stepped LIFO example"
```

---

### Task 10: `sf_dangling_local` (gotcha via -Wreturn-local-addr)

**Files:**
- Create: `cpp_labs/stackframes/topics/sf_dangling_local.topic.yaml`, `demos/sf_dangling_local.demo.yaml`

**Decision (locked per spec §6):** surface g++'s deterministic `-Wreturn-local-addr` **as a hard error** so it shows in the red compile-error box via the existing `error_kind="compile"` path — the most robust, deterministic surfacing (a mere warning may or may not be captured on a successful compile). This needs the topic compiled with `-Werror=return-local-addr`.

- [ ] **Step 1: Add a per-topic extra-flags hook.** `_compile_one` currently only adds ASan flags for `sanitize`. Add an optional `extra_compile_flags` list on the topic. In `cpp_labs/code_generator.py` add the field to `TopicTemplate` (find the dataclass; add `extra_compile_flags: list[str] = field(default_factory=list)`), ensure `topic_yaml.py` passes it through (it forwards known keys), and in `build_html._compile_one` merge it:

```python
    extra_flags = ["-fsanitize=address", "-g"] if getattr(topic, "sanitize", False) else []
    extra_flags = list(extra_flags) + list(getattr(topic, "extra_compile_flags", []) or [])
    result = compile_and_run(source, extra_flags=extra_flags or None)
```

Write a focused unit test first:

```python
# cpp_labs/tests/test_extra_compile_flags.py
from cpp_labs.code_generator import TopicTemplate
def test_topic_has_extra_compile_flags_default_empty():
    t = TopicTemplate(id="x", name="X", template="int main(){}", explanation="e", group="g")
    assert t.extra_compile_flags == []
```
Run it (RED → add field → GREEN).

- [ ] **Step 2: Author the topic.**

```yaml
id: sf_dangling_local
name: "Dangling Reference (gotcha)"
group: Gotchas
doc_url: https://en.cppreference.com/w/cpp/language/reference
sanitize: false
extra_compile_flags: ["-Werror=return-local-addr"]
explanation: >-
  A function's frame is destroyed the moment it returns. If it returns a
  reference or pointer to one of its OWN locals, that reference dangles — it
  aliases reclaimed stack memory. g++ catches this at build time; here we make
  the warning an error so the mistake cannot slip through.
template: |
  #include <cstdio>
  // BUG: returns a reference to a local — its frame dies on return.
  int& make() {
      int local = 42;
      return local;
  }
  int main() {
      int& r = make();
      printf("%d\n", r);
  }
```

- [ ] **Step 3: Verify it FAILS to compile with a real diagnostic.**

```bash
python - <<'PY'
from pathlib import Path
from cpp_labs.topic_yaml import load_topics
from cpp_labs.build_html import capture_variant, expand_variants
t = load_topics(Path("cpp_labs/stackframes/topics"))["sf_dangling_local"]
v = capture_variant(t, expand_variants(t)[0])
print("failed:", v.get("failed"), "kind:", v.get("error_kind"))
print(v["stderr"][:400])
PY
```
Expected: `failed: True kind: compile`; stderr mentions `reference to local variable` / `return-local-addr`.

- [ ] **Step 4: Author the demo.**

```yaml
title: "Dangling Reference (gotcha)"
language: cpp
bake: { dl: sf_dangling_local }
blocks:
  - concept: { id: dl-note, text: "${dl.explanation}" }
  - topic:   { id: dl, source: dl }
```

- [ ] **Step 5: Commit**

```bash
git add cpp_labs/code_generator.py cpp_labs/build_html.py cpp_labs/tests/test_extra_compile_flags.py \
        cpp_labs/stackframes/topics/sf_dangling_local.topic.yaml cpp_labs/stackframes/demos/sf_dangling_local.demo.yaml
git commit -m "feat(stackframes): sf_dangling_local gotcha via -Werror=return-local-addr"
```

---

### Task 11: `sf_memmap` (capstone)

**Files:**
- Create: `cpp_labs/stackframes/topics/sf_memmap.topic.yaml`, `demos/sf_memmap.demo.yaml`

- [ ] **Step 1: Author the topic.**

```yaml
id: sf_memmap
name: Process Memory Map
group: Stack Frames
doc_url: https://en.cppreference.com/w/cpp/language/storage_duration
explanation: >-
  The stack is one region of the whole process image. From low to high
  addresses: text (code) < initialized data < uninitialized data (bss) < heap <
  stack. The heap grows up and the stack grows down, toward each other.
template: |
  #include <cstdio>
  int g_seed = 7;          // initialized global -> data
  int g_count;             // uninitialized global -> bss
  int main() {
      int local = 0;                 // -> stack
      int* heap = new int(5);        // -> heap
      // ordering is deterministic and assertable; addresses vary and are only drawn
      printf("text < data? %d\n",  (const void*)&main   < (const void*)&g_seed);
      printf("data < bss? %d\n",   (const void*)&g_seed < (const void*)&g_count);
      printf("bss < heap? %d\n",   (const void*)&g_count < (const void*)heap);
      printf("heap < stack? %d\n", (const void*)heap    < (const void*)&local);
      printf("PTRDATA: type=memmap regions=text:%p:main,data:%p:g_seed,"
             "bss:%p:g_count,heap:%p:new_int,stack:%p:local\n",
             (void*)&main, (void*)&g_seed, (void*)&g_count, (void*)heap,
             (void*)&local);
      delete heap;
  }
```

- [ ] **Step 2: Verify compile + ordering booleans.** (Task 6 Step 3 harness, id `sf_memmap`.)
Expected: `OK`; stdout has `text < data? 1`, `data < bss? 1`, `bss < heap? 1`, `heap < stack? 1`, and one `PTRDATA: type=memmap` line.

> If any ordering boolean is not `1` on the build host, assert only the ones that hold and note it — but on mainstream Linux/macOS ABIs all four hold. Record the observed output before writing the test assertion.

- [ ] **Step 3: Author the demo.**

```yaml
title: "Process Memory Map"
language: cpp
bake: { mm: sf_memmap }
blocks:
  - concept: { id: mm-note, text: "${mm.explanation}" }
  - topic:   { id: mm, source: mm }
```

- [ ] **Step 4: Commit**

```bash
git add cpp_labs/stackframes/topics/sf_memmap.topic.yaml cpp_labs/stackframes/demos/sf_memmap.demo.yaml
git commit -m "feat(stackframes): sf_memmap process memory-map capstone"
```

---

### Task 12: Glossary + rail layout

**Files:**
- Create: `cpp_labs/stackframes/glossaries/stackframes.glossary.yaml`, `layouts/stackframes.rail.yaml`

- [ ] **Step 1: Author the glossary.**

```yaml
title: "Stack Frame Terms"
terms:
  - term: "stack frame"
    def: "The block a function call pushes onto the stack, holding its parameters, return address, saved frame pointer, and locals."
  - term: "SP (stack pointer)"
    def: "Points to the top of the stack — the innermost (most recent) frame, at the lowest address."
  - term: "FP (frame pointer)"
    def: "A fixed anchor into the current frame used to reach its locals and parameters."
  - term: "return address"
    def: "Where execution resumes in the caller after the callee returns; saved in the callee's frame."
  - term: "LIFO"
    def: "Last in, first out — the most recently pushed frame is the first popped."
  - term: "dangling reference"
    def: "A reference or pointer into a frame that has already been destroyed on return; using it is undefined behavior."
```

- [ ] **Step 2: Author the rail layout.**

```yaml
title: "Stack Frames — the Call Stack"
style: left_rail
sidebar:
  - concept:  { id: obj, text: "How the call stack works: every call pushes a frame; every return pops one. Addresses increase upward while the stack grows downward. Watch frames push and pop, see what a frame holds, and meet the classic dangling-local gotcha." }
  - glossary: { id: g-sf, source: ../glossaries/stackframes.glossary.yaml, label: "Vocabulary" }
demos:
  - ../demos/sf_single_call.demo.yaml
  - ../demos/sf_nested.demo.yaml
  - ../demos/sf_locals.demo.yaml
  - ../demos/sf_recursion.demo.yaml
  - ../demos/sf_dangling_local.demo.yaml
  - ../demos/sf_memmap.demo.yaml
```

- [ ] **Step 3: Build the page.**

```bash
python -m cpp_labs.yaml_engine.render_page cpp_labs/stackframes/layouts/stackframes.rail.yaml dist_labs
```
Expected: writes `dist_labs/stackframes.rail/stackframes.rail.html` (stem = filename minus nothing; confirm the printed output path). Open it and click a stepped example's ①..N buttons; confirm frames push/pop and the anatomy `<details>` expands.

- [ ] **Step 4: Commit**

```bash
git add cpp_labs/stackframes/glossaries/stackframes.glossary.yaml cpp_labs/stackframes/layouts/stackframes.rail.yaml
git commit -m "feat(stackframes): glossary + left_rail layout"
```

---

### Task 13: Subject tests

**Files:**
- Create: `cpp_labs/stackframes/tests/test_stackframes.py`

- [ ] **Step 1: Write the tests** (g++-gated; module-scoped `html` fixture builds the rail once). Mirror `cpp_labs/pointers_refs/tests/` structure.

```python
# cpp_labs/stackframes/tests/test_stackframes.py
import re
import shutil
import pytest
from pathlib import Path
from cpp_labs.yaml_engine.render_page import build_layout

pytestmark = pytest.mark.skipif(shutil.which("g++") is None, reason="needs g++")

LAYOUT = Path("cpp_labs/stackframes/layouts/stackframes.rail.yaml")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_self_contained(html):
    assert "<!DOCTYPE html>" in html
    for bad in ('<script src', '<link', 'href="http', 'src="http'):
        assert bad not in html


def test_traces_present(html):
    for s in ("enter main", "enter greet", "leave greet",
              "enter compute", "enter square", "leave square",
              "enter countdown", "leave countdown"):
        assert s in html


def test_single_call_layout_summary(html):
    assert "frame slots: local=4 B, return addr=8 B, saved fp=8 B" in html


def test_locals_two_tabs(html):
    assert "without locals" in html and "with locals" in html


def test_memmap_ordering_booleans(html):
    for s in ("text &lt; data? 1", "data &lt; bss? 1",
              "bss &lt; heap? 1", "heap &lt; stack? 1"):
        assert s in html


def test_dangling_gotcha_surfaces_error(html):
    assert "out--err" in html                 # red compile-error console
    assert "return-local-addr" in html or "reference to local" in html


def test_stepper_present(html):
    assert 'type="radio"' in html             # stepped diagrams exist
    assert "Show full frame anatomy" in html   # anatomy disclosures


def test_wcag_svg_role_invariant(html):
    assert html.count("<svg") == html.count('role="img"')


def test_unique_dom_ids(html):
    ids = re.findall(r'id="([^"]+)"', html)
    assert len(ids) == len(set(ids)), "duplicate DOM ids"
```

- [ ] **Step 2: Run and iterate to green.**

Run: `python -m pytest cpp_labs/stackframes/tests/ -q`
Expected: PASS. Likely fixups: HTML-escaping of `<` in the memmap booleans (`&lt;`), the exact rail output stem, and any duplicate-id from the stepper (ensure per-topic-unique `comp_id` — the `pid` chain already namespaces by topic+label, so `stepped_frames` ids like `{pid}-md-s0` are unique).

> If `test_wcag_svg_role_invariant` fails: every `<svg>` from `_frames_core`, `_svg_frames_anatomy`, and `_svg_memmap` already goes through `_wrap_svg` (which adds `role="img"`), so a mismatch means an SVG was emitted outside `_wrap_svg` — fix that renderer.

- [ ] **Step 3: Commit**

```bash
git add cpp_labs/stackframes/tests/test_stackframes.py
git commit -m "test(stackframes): exact stdout, tabs, gotcha, stepper, WCAG, id-uniqueness"
```

---

### Task 14: Register in build, regen catalog, full suite, docs

**Files:**
- Modify: `build_labs.sh` only if the subject is not auto-discovered (it globs `cpp_labs/*/layouts/*.yaml`, so `stackframes.rail.yaml` is picked up automatically — verify).
- Modify: `usage/INTERFACE_ELEMENTS.md` (regen if the catalog introspects the new components).
- Modify: `JOURNAL.md`, add `handoffs/HANDOFF_<stamp>.md`.

- [ ] **Step 1: Confirm auto-discovery + full rebuild.**

Run: `./build_labs.sh stackframes`
Expected: builds the stackframes rail without error; prints the output path.

- [ ] **Step 2: Regenerate the interface catalog** (in case a new component signature/docstring is introspected):

Run: `python -m cpp_labs.yaml_engine.interface_catalog`
Then: `python -m pytest cpp_labs -k interface_catalog -q`
Expected: PASS (catalog fresh). Commit `usage/INTERFACE_ELEMENTS.md` if it changed.

> Note: `stepped_frames` and `frames_anatomy_details` are internal helpers used inside `_demo_variant_body` (not `_DISPATCH` block keywords), so the *author-facing* catalog likely does not change — but run the regen to be safe (the freshness test is authoritative).

- [ ] **Step 3: Full suite.**

Run: `python -m pytest cpp_labs -q`
Expected: PASS — the prior 476 plus the new engine + subject tests. If a pre-existing pointer test regressed, the culprit is the `_demo_variant_body` branch or `_bake_program` change — revisit Task 5.

- [ ] **Step 4: Rebuild every page + visual check.**

Run: `./build_labs.sh` then `python3 -m http.server -d dist_labs 8000`
Open the stackframes rail; verify: stepper push/pop on `sf_nested`/`sf_recursion`, two tabs on `sf_locals`, red error box on `sf_dangling_local`, memmap regions on `sf_memmap`, dual-axis + anatomy `<details>` on frame diagrams, and that the code column stays a constant width (2/3) across variants.

- [ ] **Step 5: Update JOURNAL + write handoff.** Add a `JOURNAL.md` entry (top) summarizing the subject + two diagram families + stepper; write `handoffs/HANDOFF_<YYYY-MM-DD_HHhMMmEST>.md` per the naming convention. Commit.

```bash
git add JOURNAL.md handoffs/ usage/INTERFACE_ELEMENTS.md
git commit -m "docs(stackframes): JOURNAL entry + handoff; regen interface catalog"
```

- [ ] **Step 6: Finish the branch.** Use superpowers:finishing-a-development-branch to merge `feat/stackframes` → `main` (this project's convention: merge locally, nothing pushed unless asked).

---

## Self-review (completed against the spec)

- **§3 example set (6):** Tasks 6–11 create all six; Task 12 wires them into the rail in spec order. ✔
- **§4 determinism:** traces + `sizeof` layout summary asserted (Tasks 6, 13); addresses only in `PTRDATA`, never asserted; memmap ordering booleans asserted. ✔
- **§5.1 frames + anatomy + per-row addresses + byte sizes:** Tasks 2, 3. ✔
- **§5.2 stepper (multi-PTRDATA → per-step SVG → CSS-radio):** Tasks 1, 5. ✔
- **§5.3 frame tracer:** Phase 2 preamble; used by Tasks 6–9. ✔
- **§5.4 memmap:** Task 4, Task 11. ✔
- **§6 gotcha without ASan:** Task 10 (`-Werror=return-local-addr`, hard-error surfacing chosen). ✔
- **§7 testing families:** Task 13 covers exact stdout, tabs, gotcha, stepper, WCAG svg==role, id-uniqueness, self-contained. ✔
- **§8 engine inventory:** Tasks 1–5 touch exactly the five listed files, no page-engine/loader/vocabulary changes (except the additive `extra_compile_flags` field for §6). ✔
- **§9 risks:** address-ordering determinism flagged (Task 7 note, Task 11 note); warning-surfacing resolved to `-Werror` (Task 10); `parse_ptrdata_all` is additive, first-line path untouched (Task 1). ✔

**Type/name consistency:** `parse_ptrdata_all`, `_parse_frames`, `_frames_core`, `_svg_frames`, `_svg_frames_anatomy`, `_svg_memmap`, `stepped_frames`, `frames_anatomy_details`, `ptrdata_steps`, `extra_compile_flags` used identically across all tasks. Frame dict keys `{name, addr, local, bytes, pbytes}` consistent between `_parse_frames`, `_frames_core`, `_svg_frames_anatomy`. `live` entry format `name:addr:local:localbytes:parambytes` consistent between the tracer (Phase 2) and `_parse_frames` (Task 2).
