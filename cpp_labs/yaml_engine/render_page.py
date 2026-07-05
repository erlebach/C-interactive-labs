"""Translate a YAML page spec into a self-contained HTML page of components.

A page spec is a flat list of *blocks*:

    title: Basic Pointer
    bake:                 # compile these TopicTemplates; expose variants as data
      bp: basic_ptr
    blocks:
      - callout_note: { id: intro, label: Concept, text: "${bp.explanation}" }
      - topic:        { id: types, source: bp }     # reusable topic-template cluster
      - memory_diagram: { id: d, ptrdata: ${bp.int.ptrdata} }

Each block is a single-key mapping ``{component_name: {args}}``.  The translator
pops ``id`` and forwards the rest as keyword args to the matching component in
:mod:`cpp_labs.components` — so the YAML key names *are* the component
parameters and the same component can appear any number of times (each instance
namespaced by its own ``id``).  ``${a.b.c}`` references resolve against the baked
data.  Two "smart" builders compose multiple components: ``topic`` (a variant_tabs
cluster over a baked topic) and ``heading``/``html`` (chrome).

`render_page(spec, data)` is pure (no g++); `build_page` bakes real output first.

This module is the subject-agnostic engine: it dispatches any page spec to the
component library and bakes any topic in the registry.  Per-subject page specs
live in their own packages (e.g. ``cpp_labs/basic_ptr/basic_ptr.page.yaml``).

Entry point: ``python -m cpp_labs.yaml_engine.render_page <page.yaml> [dist]``
"""

from __future__ import annotations

import html as _html
import re
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from .. import components as C
from ..build_html import capture_variant, expand_variants

_REF_RE = re.compile(r"\$\{([^}]+)\}")


# ---------------------------------------------------------------------------
# Topic registry (resolve a bake name -> TopicTemplate)
# ---------------------------------------------------------------------------


def _topic_registry() -> dict[str, Any]:
    """Every subject's topics, auto-discovered from ``cpp_labs/*/topics``.

    No subject is named here: dropping in a new subject folder (a ``topics/``
    dir of YAML plus a layout) is enough for the engine to bake and render it.
    """
    from ..topic_yaml import discover_topics
    return discover_topics(Path(__file__).resolve().parents[1])


# ---------------------------------------------------------------------------
# Baking (impure — runs g++)
# ---------------------------------------------------------------------------


def _pre(text: str, language: str | None = None) -> str:
    cls = f' class="language-{language}"' if language else ""
    return f"<pre><code{cls}>{_html.escape(text)}</code></pre>"


def _bake_program(v: dict[str, Any], language: str | None = None) -> dict[str, Any]:
    """Render-data for one compiled program (a variant or a sub-case)."""
    mem = v.get("membytes", "")
    return {
        "source": v.get("source", ""),
        "code_html": _pre(v.get("source", ""), language),
        "ptrdata": v.get("ptrdata"),
        "ptrdata_steps": v.get("ptrdata_steps", []),
        "stdout": v.get("stdout", ""),
        "stderr": v.get("stderr", ""),
        "ok": not v.get("failed", False),
        "failed": v.get("failed", False),
        "error_kind": v.get("error_kind"),
        "bytes": mem.split() if mem and mem != "n/a" else [],
        "target_val": (v.get("ptrdata") or {}).get("target_val", "?"),
    }


def _bake_one(topic: Any, language: str | None = None) -> dict[str, Any]:
    variants = [capture_variant(topic, cs) for cs in expand_variants(topic)]
    entry: dict[str, Any] = {
        "explanation": topic.explanation,
        "variants": [v.get("label") or "default" for v in variants],
    }
    for v in variants:
        label = v.get("label") or "default"
        if v.get("cases"):
            # A cases-topic: each variant bundles independently-compiled
            # sub-cases. Preserve them (each keeps its own compile verdict)
            # so the renderer can stack them; don't flatten to one program.
            entry[label] = {
                "cases": [{**_bake_program(c, language), "label": c.get("label", "")}
                          for c in v["cases"]],
            }
        else:
            entry[label] = _bake_program(v, language)
    return entry


def bake_all(bake: dict[str, str], language: str | None = None) -> dict[str, Any]:
    """Compile each ``name: topic_id`` and return ``{name: baked-entry}``.

    *language* (from the demo/page YAML) tags each source block with a
    ``language-XXX`` class for syntax highlighting; ``None`` keeps it classless.
    """
    registry = _topic_registry()
    data: dict[str, Any] = {}
    for name, topic_id in (bake or {}).items():
        if topic_id not in registry:
            raise KeyError(f"unknown topic id in bake: {topic_id!r}")
        data[name] = _bake_one(registry[topic_id], language)
    return data


# ---------------------------------------------------------------------------
# Reference resolution  ${a.b.c}
# ---------------------------------------------------------------------------


def _lookup(path: str, data: dict) -> Any:
    cur: Any = data
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur[part]
        else:
            cur = getattr(cur, part)
    return cur


def _resolve(value: Any, data: dict) -> Any:
    if isinstance(value, str):
        m = _REF_RE.fullmatch(value.strip())
        if m:  # whole-value ref → substitute the real object (may be dict/list)
            return _lookup(m.group(1), data)
        return _REF_RE.sub(lambda mo: str(_lookup(mo.group(1), data)), value)
    if isinstance(value, dict):
        return {k: _resolve(v, data) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, data) for v in value]
    return value


# ---------------------------------------------------------------------------
# Dispatch: block name -> component / builder
# ---------------------------------------------------------------------------

_DISPATCH = {
    "callout_note": C.callout_note,
    "color_legend": C.color_legend,
    "memory_diagram": C.memory_diagram,
    "hover_link_diagram": C.hover_link_diagram,
    "before_after_toggle": C.before_after_toggle,
    "predict_reveal_quiz": C.predict_reveal_quiz,
    "compile_status_badge": C.compile_status_badge,
    "output_console": C.output_console,
    "byte_grid": C.byte_grid,
    "code_line_link": C.code_line_link,
    "variant_tabs": C.variant_tabs,
    "code_diagram_panel": C.code_diagram_panel,
    "stacked_subcases": C.stacked_subcases,
    "progressive_steps": C.progressive_steps,
    "glossary": C.glossary,
}

# Components whose one arg is a list of pair-dicts → list of tuples.
_PAIR_ARGS = {
    "progressive_steps": ("steps", ("summary", "content")),
    "variant_tabs": ("panels", ("label", "html")),
    "stacked_subcases": ("subcases", ("label", "html")),
    "glossary": ("terms", ("term", "def")),
}


def _adapt(name: str, args: dict) -> dict:
    if name in _PAIR_ARGS:
        key, (k1, k2) = _PAIR_ARGS[name]
        if key in args:
            args[key] = [(d[k1], d[k2]) for d in args[key]]
    if name == "before_after_toggle" and isinstance(args.get("labels"), list):
        args["labels"] = tuple(args["labels"])
    return args


# ---------------------------------------------------------------------------
# Smart builders (compose multiple components)
# ---------------------------------------------------------------------------


def _build_heading(args: dict, data: dict) -> str:
    level = int(args.get("level", 2))
    return f"<h{level}>{_html.escape(str(args['text']))}</h{level}>\n"


def _build_html(args: dict, data: dict) -> str:
    return str(args.get("content", ""))


def _build_topic(args: dict, data: dict) -> str:
    """A demo_panel over a baked topic (thin adapter; content lives in components).

    ``diagram: false`` suppresses the memory diagram for subjects with no
    memory-model picture (operator overloading, classes, templates); default on.
    """
    return C.demo_panel(args["id"], data[args["source"]],
                        diagram=args.get("diagram", True),
                        concept=args.get("concept"),
                        concept_title=args.get("concept_title", "Concept"))


def _build_concept(args: dict, data: dict) -> str:
    """Build one example's fold-away Concept note from its YAML block.

    Any ``${...}`` references in the block's text have already been filled in
    with real values before this runs.

    Args:
        args: The concept block's fields, already filled in: ``id`` and ``text``,
            plus optional ``label`` (the clickable line) and ``open`` (start
            already open).
        data: The page's baked data. Not needed here, because the text is already
            filled in; kept so every builder has the same shape.

    Returns:
        The Concept note as a piece of HTML.
    """
    return C.concept_note(args["id"], args["text"],
                          label=args.get("label", "Concept"),
                          open_=args.get("open", False))


_BUILDERS = {
    "heading": _build_heading,
    "html": _build_html,
    "topic": _build_topic,
    "concept": _build_concept,
}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _render_block(block: dict, data: dict) -> str:
    if len(block) != 1:
        raise ValueError(f"a block must have exactly one key, got {list(block)}")
    (name, raw_args), = block.items()
    args = _resolve(raw_args or {}, data)
    if name in _BUILDERS:
        return _BUILDERS[name](args, data)
    if name not in _DISPATCH:
        raise KeyError(f"unknown block type: {name!r}")
    args = _adapt(name, dict(args))
    cid = args.pop("id")
    return _DISPATCH[name](cid, **args)


def _glossary_from_source(args: dict, base: Path) -> tuple[str, str]:
    """Load a shared ``*.glossary.yaml`` file and render it to HTML.

    Both a layout's ``header:`` and its ``sidebar:`` can name a glossary by
    file (``source:``) rather than writing its terms inline; this is the one
    place that turns such a reference into rendered HTML.

    Args:
        args: The glossary block's arguments. ``source`` (required) is the
            glossary file's path relative to *base*; ``id`` (optional, default
            ``"glossary"``) becomes the section's HTML id.
        base: The folder the layout file lives in, used to resolve ``source``.

    Returns:
        A ``(title, html)`` pair — *title* is the file's ``title:`` (default
        ``"Glossary"``), *html* is the rendered glossary section. Callers that
        need a label (e.g. the sidebar) reuse *title* as the default label.
    """
    g = load_spec(Path(base) / args["source"])
    terms = [(t["term"], t["def"]) for t in g.get("terms", [])]
    title = g.get("title", "Glossary")
    html = C.glossary(args.get("id", "glossary"), title, terms)
    return title, html


def _render_header(blocks: list, base_dir: Path) -> str:
    """Render a layout's ``header:`` blocks once.

    A ``glossary`` block with a ``source:`` key loads a shared
    ``*.glossary.yaml`` file (relative to *base_dir*) and renders it; all
    other blocks (color_legend, heading, html, or an inline glossary without
    ``source:``) are dispatched through ``_render_block`` as normal.
    """
    out = []
    for block in blocks or []:
        (name, raw), = block.items()
        args = dict(raw or {})
        if name == "glossary" and "source" in args:
            _, html = _glossary_from_source(args, base_dir)
            out.append(html)
        else:
            out.append(_render_block(block, {}))
    return "\n".join(out)


def render_fragment(spec: dict, data: dict) -> str:
    """Translate *spec*'s blocks to HTML — no page shell. Pure (no g++)."""
    return "\n".join(_render_block(b, data) for b in spec.get("blocks", []))


def render_page(spec: dict, data: dict) -> str:
    """Translate *spec* (with pre-baked *data*) into a self-contained page.

    Pure — no I/O, no g++.  Use :func:`build_page` to bake and write.
    """
    body = render_fragment(spec, data)
    return C.page_shell("page", body, title=spec.get("title", "Topic"))


def load_spec(path: Path | str) -> dict:
    if yaml is None:  # pragma: no cover
        raise RuntimeError("pyyaml not installed — run: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_page(spec_path: Path | str, dist_dir: Path) -> Path:
    """Load *spec_path*, bake its topics with g++, render, and write the page.

    Raises ``RuntimeError`` (before baking) if g++ is unavailable.  Returns the
    written file path (``<dist>/<stem>/<stem>.html``, one subdir per page).
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. This page bakes real compiler output at "
            "build time; install a C++ compiler first."
        )
    spec = load_spec(spec_path)
    data = bake_all(spec.get("bake", {}), spec.get("language"))
    page = render_page(spec, data)
    stem = Path(spec_path).stem.replace(".page", "")
    out = Path(dist_dir) / stem / f"{stem}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def _build_sidebar(sidebar: list, base: Path) -> list:
    """Build the page's side-list entries from a layout's ``sidebar:`` list.

    Each item in the list names one kind of entry:

    - ``glossary``: opens a vocabulary file and shows its terms.
    - ``concept``: a short "what this page teaches" note written right there in
      the layout.

    The entries keep the order they were written in, which is the order they
    appear in the side list.

    Args:
        sidebar: The layout's list of side entries. Each entry is a mapping with
            exactly one key naming its kind (``glossary`` or ``concept``).
        base: The folder the layout file lives in, used to find any files a
            ``glossary`` entry points to.

    Returns:
        One ``(label, html)`` pair per side entry, in order.

    Raises:
        ValueError: If an entry has more than one key.
        KeyError: If an entry names a kind other than ``glossary`` or ``concept``.
    """
    items = []
    for entry in sidebar or []:
        if len(entry) != 1:
            raise ValueError(f"a sidebar entry must have exactly one key, got {list(entry)}")
        (kind, a), = entry.items()
        if kind == "glossary":
            title, body = _glossary_from_source(a, base)
            label = a.get("label", title)
        elif kind == "concept":
            label = a.get("label", "Concept")
            body = C.concept_panel(a.get("id", "concept"), a["text"], title=label)
        else:
            raise KeyError(f"unknown sidebar entry type: {kind!r}")
        items.append((label, body))
    return items


def build_layout(layout_path: "Path | str", dist_dir: Path) -> Path:
    """Bake+compose a layout spec into one standalone page.

    Writes ``<dist>/<layout-stem>/<layout-stem>.html``. Raises before baking if
    g++ is unavailable.
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. This page bakes real compiler output at "
            "build time; install a C++ compiler first.")
    layout_path = Path(layout_path)
    base = layout_path.parent
    spec = load_spec(layout_path)

    style = spec.get("style", "left_rail")

    header_html = _render_header(spec.get("header", []), base)

    # Sidebar entries declared on the layout become leading rail entries (rendered
    # in full as a panel), set apart from the demos by an italic label.
    sidebar_items = _build_sidebar(spec.get("sidebar", []), base)
    items = list(sidebar_items)
    for demo_ref in spec.get("demos", []):
        demo_spec = load_spec(base / demo_ref)
        data = bake_all(demo_spec.get("bake", {}), demo_spec.get("language"))
        fragment = render_fragment(demo_spec, data)
        items.append((demo_spec.get("title", "Demo"), fragment))

    n = len(sidebar_items)
    nav = C.nav_shell("lab", items, style=style, leading=n,
                      selected=(n if n < len(items) else 0))
    body = f"{header_html}\n{nav}" if header_html else nav
    page = C.page_shell("page", body, title=spec.get("title", "Lab"), highlight=True)

    stem = layout_path.stem
    out = Path(dist_dir) / stem / f"{stem}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def main() -> None:
    if shutil.which("g++") is None:
        print("ERROR: g++ not found on PATH; these pages bake real compiler output.",
              file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print("usage: python -m cpp_labs.yaml_engine.render_page "
              "<page.yaml> [dist_dir]", file=sys.stderr)
        sys.exit(2)
    spec_path = Path(sys.argv[1])
    dist = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parents[2] / "dist_labs"
    spec_probe = load_spec(spec_path)
    out = build_layout(spec_path, dist) if "demos" in spec_probe else build_page(spec_path, dist)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
