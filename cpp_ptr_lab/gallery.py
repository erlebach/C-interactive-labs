"""Component gallery build for the C++ Pointer Lab.

Emits one standalone, Canvas-pasteable demo page per component in
:mod:`cpp_ptr_lab.components`, plus a browsable index, into ``<dist>/gallery/``.
Each demo renders the component on real pointer content; components that show
program output bake **real g++-captured** stdout/stderr at build time (never
placeholders).  Because output is baked rather than computed at view time, the
build fails clearly and early if ``g++`` is unavailable.

Entry point: ``python -m cpp_ptr_lab.gallery``
"""

from __future__ import annotations

import html as _html
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

from . import components as C
from .build_html import capture_variant, expand_variants
from .compiler_runner import compile_and_run
from .html_renderer import svg_renderer
from .pointers_refs.topics import basic_ptr


# ---------------------------------------------------------------------------
# Build-time baking (the only impure part — runs g++)
# ---------------------------------------------------------------------------

# Deliberately ill-typed: writing through a pointer to const is a hard error,
# so g++ emits real stderr containing "error:" for the failure demos.
_FAILING_SRC = (
    "int main() {\n"
    "    const int x = 1;\n"
    "    int* p = &x;   // error: drops const\n"
    "    *p = 2;\n"
    "    return 0;\n"
    "}\n"
)


def bake() -> dict[str, Any]:
    """Compile + run real C++ to capture pointer data and program output."""
    state = expand_variants(basic_ptr)[0]
    ok = capture_variant(basic_ptr, state)
    fail = compile_and_run(_FAILING_SRC)
    return {"ok": ok, "fail": fail}


# ---------------------------------------------------------------------------
# Per-component demo bodies (pure, given baked data)
# ---------------------------------------------------------------------------


def _pre(text: str) -> str:
    return f"<pre><code>{_html.escape(text)}</code></pre>"


def _null_pd(ok_pd: dict) -> dict:
    return {"type": "null", "ptr_addr": ok_pd.get("ptr_addr", "0x0")}


def _demo_page_shell(b: dict) -> str:
    return (
        "<p>This very page is produced by <code>page_shell</code>: it supplies the "
        "<code>lang</code> attribute, the skip link, the <code>&lt;main&gt;</code> "
        "landmark, and all inlined CSS — no external resources.</p>"
        + C.callout_note("ps-note", "Every gallery demo is wrapped by this same shell.")
    )


def _demo_color_legend(b: dict) -> str:
    return C.color_legend("legend") + C.callout_note(
        "legend-note", "The same five tokens color prose, code, and SVG diagrams."
    )


def _demo_callout_note(b: dict) -> str:
    return (
        C.callout_note("note-1", "A pointer stores the address of another object.")
        + C.callout_note("note-2", "Dereferencing reads the value at that address.", label="Tip")
    )


def _demo_memory_diagram(b: dict) -> str:
    return C.memory_diagram("md", b["ok"]["ptrdata"])


def _demo_hover_link(b: dict) -> str:
    return (
        C.callout_note("hl-note", "Hover or keyboard-focus the pointer box.", label="Try it")
        + C.hover_link_diagram("hl", b["ok"]["ptrdata"])
    )


def _demo_before_after(b: dict) -> str:
    pd = b["ok"]["ptrdata"]
    before = svg_renderer(pd, "ba-before")
    after = svg_renderer(_null_pd(pd), "ba-after")
    return C.before_after_toggle(
        "ba", before, after, labels=("ptr = &val", "ptr = nullptr"),
        caption="Toggle the assignment to see where ptr points.",
    )


def _demo_predict_quiz(b: dict) -> str:
    val = b["ok"]["ptrdata"].get("target_val", "?")
    return C.predict_reveal_quiz(
        "quiz",
        "Given int val = 42; int* ptr = &val; — what does *ptr evaluate to?",
        ["0", str(val), "the address of val"],
        1,
        explanation=f"*ptr reads the value at the address it holds, which is {val}.",
    )


def _demo_compile_badge(b: dict) -> str:
    return (
        C.compile_status_badge("badge-ok", True)
        + "<br><br>"
        + C.compile_status_badge("badge-err", False)
    )


def _demo_output_console(b: dict) -> str:
    stdout = b["ok"]["stdout"]
    stderr = b["fail"].compiler_stderr
    return (
        C.output_console("out-ok", stdout)
        + C.output_console("out-err", stderr, error=True)
    )


def _demo_byte_grid(b: dict) -> str:
    membytes = b["ok"]["membytes"]
    values = membytes.split() if membytes and membytes != "n/a" else []
    return (
        C.byte_grid("bytes", values, caption="Raw bytes of ptr (little-endian)")
        + C.callout_note("bg-note", "These 8 bytes are the address &val stored little-endian.")
    )


def _demo_code_line_link(b: dict) -> str:
    pd = b["ok"]["ptrdata"]
    lines = [
        ("int val = 42;", None),
        ("int* ptr = &val;", "ptr"),
        ("std::cout << *ptr;", None),
    ]
    return (
        C.callout_note("cll-note", "Hover or focus the highlighted source line.", label="Try it")
        + C.code_line_link("cll", lines, ptrdata=pd)
    )


def _demo_variant_tabs(b: dict) -> str:
    pd = b["ok"]["ptrdata"]
    panels = [
        ("Diagram", C.memory_diagram("vt-md", pd)),
        ("Source", _pre(b["ok"]["source"])),
    ]
    return C.variant_tabs("vt", panels)


def _demo_code_diagram_panel(b: dict) -> str:
    return C.code_diagram_panel(
        "cdp", _pre(b["ok"]["source"]), C.memory_diagram("cdp-md", b["ok"]["ptrdata"])
    )


def _demo_stacked_subcases(b: dict) -> str:
    ok_body = (
        C.compile_status_badge("ssc-ok-b", True)
        + C.output_console("ssc-ok-o", b["ok"]["stdout"])
    )
    fail_body = (
        C.compile_status_badge("ssc-err-b", False)
        + C.output_console("ssc-err-o", b["fail"].compiler_stderr, error=True)
    )
    return C.stacked_subcases("ssc", [("Writes through *ptr — OK", ok_body),
                                      ("Write through pointer-to-const — error", fail_body)])


def _demo_progressive_steps(b: dict) -> str:
    val = b["ok"]["ptrdata"].get("target_val", "?")
    return C.progressive_steps("ps", [
        ("Step 1 — declare a value", "<p><code>int val = 42;</code> stores 42 in memory.</p>"),
        ("Step 2 — take its address", "<p><code>int* ptr = &val;</code> makes ptr hold val's address.</p>"),
        ("Step 3 — dereference", f"<p><code>*ptr</code> reads the value back: {val}.</p>"),
    ])


# name -> (one-line summary, body builder)
_DEMOS: dict[str, tuple[str, Callable[[dict], str]]] = {
    "page_shell": ("Accessible document scaffold (lang, skip link, landmarks)", _demo_page_shell),
    "color_legend": ("Semantic color key — swatch paired with role name", _demo_color_legend),
    "callout_note": ("Pedagogical aside with text label + border", _demo_callout_note),
    "memory_diagram": ("Static accessible SVG of pointer → target", _demo_memory_diagram),
    "hover_link_diagram": ("Hover/focus the pointer to light its target", _demo_hover_link),
    "before_after_toggle": ("Radio switch between two baked diagram states", _demo_before_after),
    "predict_reveal_quiz": ("Predict-then-reveal quiz with baked feedback", _demo_predict_quiz),
    "compile_status_badge": ("Pass/fail by text + icon + border + color", _demo_compile_badge),
    "output_console": ("Program stdout, with a distinct error variant", _demo_output_console),
    "byte_grid": ("Little-endian byte grid with accessible caption", _demo_byte_grid),
    "code_line_link": ("Hover a source line to highlight its diagram box", _demo_code_line_link),
    "variant_tabs": ("N labelled panels switched by radio :checked", _demo_variant_tabs),
    "code_diagram_panel": ("Two-column code/diagram split that reflows", _demo_code_diagram_panel),
    "stacked_subcases": ("Independent sub-cases stacked in one panel", _demo_stacked_subcases),
    "progressive_steps": ("Student-paced reveals via <details>", _demo_progressive_steps),
}

COMPONENT_NAMES: list[str] = list(_DEMOS.keys())


# ---------------------------------------------------------------------------
# Build orchestration
# ---------------------------------------------------------------------------


def _index_body() -> str:
    items = ""
    for name, (summary, _fn) in _DEMOS.items():
        items += (
            f'<li style="margin:.5rem 0"><a href="{name}.html"><code>{name}</code></a>'
            f' — {_html.escape(summary)}</li>\n'
        )
    return (
        "<p>A catalog of accessible, zero-JS page-element components. Each demo "
        "page is fully self-contained and pastes directly into Canvas.</p>\n"
        f'<ul style="line-height:1.8">\n{items}</ul>\n'
    )


def build_gallery(dist_dir: Path, baked: dict[str, Any] | None = None) -> list[Path]:
    """Build the component gallery into ``dist_dir/gallery/``.

    Raises ``RuntimeError`` (early, before any baking) if ``g++`` is not on
    PATH, since component output is baked at build time.  Returns the list of
    written file paths (demo pages followed by the index).
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. The component gallery bakes real compiler "
            "output at build time; install a C++ compiler before building."
        )

    baked = baked if baked is not None else bake()

    gdir = Path(dist_dir) / "gallery"
    gdir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for name, (summary, fn) in _DEMOS.items():
        body = (
            f'<h2>{_html.escape(name)}</h2>\n'
            f'<p class="explanation" style="border-left:4px solid var(--accent);'
            f'background:var(--panel-bg);padding:.4rem .8rem;border-radius:0 4px 4px 0">'
            f'{_html.escape(summary)}</p>\n'
            f"{fn(baked)}\n"
            f'<p style="margin-top:1.5rem"><a href="index.html">&larr; Back to gallery index</a></p>'
        )
        page = C.page_shell(name, body, title=f"Component — {name}")
        path = gdir / f"{name}.html"
        path.write_text(page, encoding="utf-8")
        written.append(path)

    index = C.page_shell("index", _index_body(), title="Component Gallery")
    index_path = gdir / "index.html"
    index_path.write_text(index, encoding="utf-8")
    written.append(index_path)
    return written


def main() -> None:
    if shutil.which("g++") is None:
        print(
            "ERROR: g++ not found on PATH. The component gallery bakes real "
            "compiler output at build time; install a C++ compiler first.",
            file=sys.stderr,
        )
        sys.exit(1)

    dist_dir = Path(__file__).parent.parent / "dist"
    written = build_gallery(dist_dir)
    print(f"Built {len(written)} gallery pages in {dist_dir / 'gallery'}/")


if __name__ == "__main__":
    main()
