"""Generate ``usage/INTERFACE_ELEMENTS.md`` — a browsable catalog of every
author-usable interface element.

The catalog is derived, not written: it reads the engine's dispatch tables in
:mod:`cpp_labs.yaml_engine.render_page` (``_DISPATCH``, ``_BUILDERS``) plus the
signatures and docstrings of the components in :mod:`cpp_labs.components`, and
renders them to Markdown. Because it is generated, it can never drift from the
code — a drift-guard test (``test_interface_catalog.py``) asserts the committed
file matches this generator's output.

This is option (1) — an *index* of what interface elements exist. It does not
change how the engine dispatches; it only reads the same tables the engine reads.
See ``usage/INTERFACE_ELEMENTS_DESIGN.md`` for how (1) relates to the possible
future single in-code registry (3).

Run ``python -m cpp_labs.yaml_engine.interface_catalog`` to (re)write the file.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Callable, Sequence

from .. import components as C
from . import render_page as R

# Where the generated catalog lives (repo-root/usage/INTERFACE_ELEMENTS.md).
CATALOG_PATH = Path(__file__).parents[2] / "usage" / "INTERFACE_ELEMENTS.md"

# Reuse tier per element — how portable it is to a course on another subject.
# A drift-guard test asserts every author-usable keyword is classified here, so a
# new element cannot be added without deciding which courses it serves.
#   generic    — any course, any domain (including non-programming, e.g. LLMs)
#   code       — any compiled/run programming language (swap the toolchain)
#   cpp-memory — pointer / memory-model visuals; only memory-teaching languages
_TIER: dict[str, str] = {
    "callout_note": "generic", "before_after_toggle": "generic",
    "predict_reveal_quiz": "generic", "output_console": "generic",
    "variant_tabs": "generic", "code_diagram_panel": "generic",
    "stacked_subcases": "generic", "progressive_steps": "generic",
    "glossary": "generic", "heading": "generic", "html": "generic",
    "concept": "generic",
    "compile_status_badge": "code", "code_line_link": "code", "topic": "code",
    "color_legend": "cpp-memory", "memory_diagram": "cpp-memory",
    "hover_link_diagram": "cpp-memory", "byte_grid": "cpp-memory",
}

# The four smart builders (``_BUILDERS``) compose components rather than wrapping
# one, so their author-facing fields are not a single component signature. This
# table names, per builder keyword, what it renders through and which YAML fields
# it reads. Keeping it here (one place, in code) is deliberate: the completeness
# test fails if a builder is added to ``_BUILDERS`` without a row here, which is
# the drift guard doing its job.
_BUILDER_INFO: dict[str, tuple[str, str, str]] = {
    "heading": ("(inline <hN>)", "text, level",
                "A section heading (h2 by default)."),
    "html": ("(raw passthrough)", "content",
             "Author-supplied HTML inserted verbatim."),
    "topic": ("demo_panel", "source, diagram",
              "A compiled topic: code + real g++ output, with an optional "
              "memory diagram (diagram: false to suppress)."),
    "concept": ("concept_note", "text, label, open",
                "One example's fold-away Concept note (native <details>)."),
}

# Sidebar entry kinds accepted by ``render_page._build_sidebar`` (a layout's
# ``sidebar:`` list). Enumerated there as an if/elif rather than a table, so they
# are listed here explicitly.
_SIDEBAR_INFO: dict[str, tuple[str, str, str]] = {
    "glossary": ("glossary", "id, source, label",
                 "A reusable vocabulary file shown as a leading rail panel."),
    "concept": ("concept_panel", "id, text, label",
                "The whole-page Concept, shown as a leading rail panel."),
}


def _purpose(fn: Callable) -> str:
    """Return the one-line purpose of *fn* — the first line of its docstring.

    Args:
        fn: Any component function from :mod:`cpp_labs.components`.

    Returns:
        The first non-empty docstring line, stripped; ``""`` if undocumented.
    """
    doc = inspect.getdoc(fn) or ""
    # Docstrings use RST inline-literal markup (``x``); collapse to single
    # backticks so the line renders as clean Markdown in the catalog.
    return doc.split("\n", 1)[0].strip().replace("``", "`")


def _args(fn: Callable) -> str:
    """Return *fn*'s author-facing arguments as a comma-separated string.

    The first positional parameter is always the caller-supplied ``comp_id``/
    ``id`` (the engine injects it), so it is dropped; the rest are the fields an
    author writes in YAML.

    Args:
        fn: A component function whose first parameter is the component id.

    Returns:
        The remaining parameter names joined by ``", "``; ``"—"`` if there are
        none.
    """
    params = list(inspect.signature(fn).parameters.values())
    names = [p.name.rstrip("_") for p in params[1:]]
    return ", ".join(names) if names else "—"


def _table(header: Sequence[str], rows: list[Sequence[str]]) -> str:
    """Render a Markdown table with any number of columns.

    Args:
        header: The column titles.
        rows: One row per element; each is a sequence of cells matching *header*
            in length. The first cell is wrapped in backticks so the completeness
            test can find each keyword.

    Returns:
        The table as Markdown text ending in a newline.
    """
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for keyword, *rest in rows:
        out.append("| " + " | ".join([f"`{keyword}`", *rest]) + " |")
    return "\n".join(out) + "\n"


def generate_catalog() -> str:
    """Build the full catalog Markdown from the live dispatch tables.

    Returns:
        The complete ``INTERFACE_ELEMENTS.md`` text (deterministic; no I/O).
    """
    block_rows: list[Sequence[str]] = []
    for name, fn in R._DISPATCH.items():
        block_rows.append((name, _TIER[name], f"`{fn.__name__}()`", _args(fn), _purpose(fn)))
    for name in R._BUILDERS:
        via, args, purpose = _BUILDER_INFO[name]
        block_rows.append((name, _TIER[name], via, args, purpose))

    sidebar_rows = [(name, _TIER[name], f"`{via}()`", args, purpose)
                    for name, (via, args, purpose) in _SIDEBAR_INFO.items()]

    parts = [
        "# Interface Elements — catalog",
        "",
        "<!-- GENERATED by cpp_labs/yaml_engine/interface_catalog.py — do NOT edit by hand.",
        "     Regenerate: python -m cpp_labs.yaml_engine.interface_catalog",
        "     A drift-guard test (test_interface_catalog.py) keeps this in sync with the code. -->",
        "",
        "Every interface element an author may name in YAML, one row each. All HTML/CSS/ADA",
        "output lives in `cpp_labs/components.py`; this page is the *index* of what is on the",
        "shelf. It is generated from the engine's dispatch tables, so it is always current.",
        "",
        "**Reuse tier** — how portable each element is to a course on another subject:",
        "",
        "- `generic` — any course, any domain (including non-programming, e.g. an LLM course).",
        "- `code` — any compiled/run programming language (point the engine at another toolchain).",
        "- `cpp-memory` — pointer / memory-model visuals; only languages that teach memory.",
        "",
        "Starting a course in another language reuses the `generic` + `code` rows and drops",
        "`cpp-memory`; a non-programming course pilfers the `generic` rows and adds its own pack.",
        "",
        "## Block elements",
        "",
        "Use these as single-key entries in a demo's or page's `blocks:` list, e.g.",
        "`- callout_note: { id: n1, text: \"…\" }`. Each also takes an `id`.",
        "",
        _table(("keyword", "tier", "renders via", "args (besides id)", "purpose"), block_rows),
        "## Sidebar entries",
        "",
        "Use these in a layout's `sidebar:` list (they become leading rail panels).",
        "",
        _table(("keyword", "tier", "renders via", "args", "purpose"), sidebar_rows),
        "## Internal chrome (NOT author-callable)",
        "",
        "`page_shell`, `nav_shell`, `left_rail_layout`, and `demo_panel` are assembled by the",
        "engine itself — you never name them in YAML. They exist in `components.py` but are not",
        "part of the authoring vocabulary.",
        "",
        "## See also",
        "",
        "- `usage/INTERFACE_ELEMENTS_DESIGN.md` — why this catalog exists, and how it relates",
        "  to the possible future single in-code registry.",
        "- `usage/YAML_GUIDE.md`, `usage/USAGE.md` — full authoring recipes with worked examples.",
        "",
    ]
    return "\n".join(parts)


def main() -> None:
    """Write the generated catalog to :data:`CATALOG_PATH`."""
    CATALOG_PATH.write_text(generate_catalog(), encoding="utf-8")
    print(f"Wrote {CATALOG_PATH}")


if __name__ == "__main__":
    main()
