"""Reconstruct the `basic_ptr` topic page from the component library.

A worked example of *consuming* :mod:`cpp_ptr_lab.components`: it bakes the real
g++ output for each type variant of the `basic_ptr` topic and assembles a single
self-contained WCAG AA page purely from components — no bespoke HTML/CSS beyond
section headings.  Compare with the renderer-driven `dist/topics/basic_ptr.html`
produced by :mod:`build_html`.

Entry point: ``python -m cpp_ptr_lab.topic_page``
"""

from __future__ import annotations

import html as _html
import shutil
import sys
from pathlib import Path

from . import components as C
from .build_html import capture_variant, expand_variants
from .pointers_refs.topics import basic_ptr


def _pre(text: str) -> str:
    return f"<pre><code>{_html.escape(text)}</code></pre>"


def _variant_panel(v: dict) -> str:
    """Assemble one type-variant panel from components (code + diagram + I/O)."""
    t = C._safe(v["label"])  # int / double / float — already CSS-safe
    pid = f"bp-{t}"
    diagram = C.memory_diagram(f"{pid}-md", v.get("ptrdata"))
    membytes = v.get("membytes", "")
    byte_vals = membytes.split() if membytes and membytes != "n/a" else []
    return (
        C.code_diagram_panel(f"{pid}-cdp", _pre(v["source"]), diagram)
        + '<div style="margin-top:.8rem">'
        + C.compile_status_badge(f"{pid}-badge", not v.get("failed", False))
        + "</div>"
        + C.output_console(f"{pid}-out", v.get("stdout") or v.get("stderr", ""),
                           error=v.get("failed", False))
        + C.byte_grid(f"{pid}-bytes", byte_vals,
                      caption=f"Raw bytes of ptr for {v['label']} (little-endian)")
    )


def build_basic_ptr_page(dist_dir: Path) -> Path:
    """Bake basic_ptr's variants and write a component-assembled page.

    Raises ``RuntimeError`` (before baking) if g++ is unavailable.  Returns the
    written file path (``<dist>/topics_v2/basic_ptr.html``).
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. This page bakes real compiler output at "
            "build time; install a C++ compiler first."
        )

    variants = [capture_variant(basic_ptr, cs) for cs in expand_variants(basic_ptr)]
    panels = [(v["label"], _variant_panel(v)) for v in variants]
    correct_val = variants[0].get("ptrdata", {}).get("target_val", "42")

    body = (
        C.callout_note("bp-intro", basic_ptr.explanation, label="Concept")
        + C.color_legend("bp-legend")
        + "<h2>Try each type</h2>\n"
        + "<p>Each tab compiles and runs a real program; the diagram, output, and "
        "raw bytes are baked from that run.</p>\n"
        + C.variant_tabs("bp-types", panels)
        + "<h2>How it works</h2>\n"
        + C.progressive_steps("bp-steps", [
            ("Step 1 — declare a value",
             "<p><code>int val = 42;</code> stores the value 42 at some stack address.</p>"),
            ("Step 2 — take its address",
             "<p><code>int* ptr = &val;</code> makes <code>ptr</code> hold the address "
             "of <code>val</code>. <code>ptr</code> itself lives in 8 bytes (see the byte grid).</p>"),
            ("Step 3 — dereference",
             f"<p><code>*ptr</code> follows the stored address and reads the value back: "
             f"{_html.escape(str(correct_val))}.</p>"),
        ])
        + "<h2>Check yourself</h2>\n"
        + C.predict_reveal_quiz(
            "bp-quiz",
            "Given int val = 42; int* ptr = &val; — what does *ptr evaluate to?",
            ["the address of val", str(correct_val), "0"],
            1,
            explanation=f"*ptr follows the address ptr holds and reads the value: {correct_val}.",
        )
    )

    page = C.page_shell("bp-page", body, title=f"{basic_ptr.name} — built from components")
    out = Path(dist_dir) / "topics_v2" / "basic_ptr.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def main() -> None:
    if shutil.which("g++") is None:
        print("ERROR: g++ not found on PATH; this page bakes real compiler output.",
              file=sys.stderr)
        sys.exit(1)
    out = build_basic_ptr_page(Path(__file__).parent.parent / "dist")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
