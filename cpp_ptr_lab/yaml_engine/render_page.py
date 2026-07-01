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
:mod:`cpp_ptr_lab.components` — so the YAML key names *are* the component
parameters and the same component can appear any number of times (each instance
namespaced by its own ``id``).  ``${a.b.c}`` references resolve against the baked
data.  Two "smart" builders compose multiple components: ``topic`` (a variant_tabs
cluster over a baked topic) and ``heading``/``html`` (chrome).

`render_page(spec, data)` is pure (no g++); `build_page` bakes real output first.

This module is the subject-agnostic engine: it dispatches any page spec to the
component library and bakes any topic in the registry.  Per-subject page specs
live in their own packages (e.g. ``cpp_ptr_lab/basic_ptr/basic_ptr.page.yaml``).

Entry point: ``python -m cpp_ptr_lab.yaml_engine.render_page <page.yaml> [dist]``
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
    from ..pointers_refs.topics import (
        basic_ptr, const_taxonomy, dangling_ptr, null_deref, ref_const,
        ref_must_bind, ref_no_null, ref_rebind_illusion,
    )
    from ..smart_ptrs.topics import TOPICS as SMART
    from ..function_args.topics import TOPICS as FUNC_ARGS
    topics = [basic_ptr, const_taxonomy, ref_must_bind, ref_no_null,
              ref_rebind_illusion, ref_const, null_deref, dangling_ptr,
              *SMART, *FUNC_ARGS]
    return {t.id: t for t in topics}


# ---------------------------------------------------------------------------
# Baking (impure — runs g++)
# ---------------------------------------------------------------------------


def _pre(text: str) -> str:
    return f"<pre><code>{_html.escape(text)}</code></pre>"


def _bake_program(v: dict[str, Any]) -> dict[str, Any]:
    """Render-data for one compiled program (a variant or a sub-case)."""
    mem = v.get("membytes", "")
    return {
        "source": v.get("source", ""),
        "code_html": _pre(v.get("source", "")),
        "ptrdata": v.get("ptrdata"),
        "stdout": v.get("stdout", ""),
        "stderr": v.get("stderr", ""),
        "ok": not v.get("failed", False),
        "failed": v.get("failed", False),
        "bytes": mem.split() if mem and mem != "n/a" else [],
        "target_val": (v.get("ptrdata") or {}).get("target_val", "?"),
    }


def _bake_one(topic: Any) -> dict[str, Any]:
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
                "cases": [{**_bake_program(c), "label": c.get("label", "")}
                          for c in v["cases"]],
            }
        else:
            entry[label] = _bake_program(v)
    return entry


def bake_all(bake: dict[str, str]) -> dict[str, Any]:
    """Compile each ``name: topic_id`` and return ``{name: baked-entry}``."""
    registry = _topic_registry()
    data: dict[str, Any] = {}
    for name, topic_id in (bake or {}).items():
        if topic_id not in registry:
            raise KeyError(f"unknown topic id in bake: {topic_id!r}")
        data[name] = _bake_one(registry[topic_id])
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
    """A demo_panel over a baked topic (thin adapter; content lives in components)."""
    return C.demo_panel(args["id"], data[args["source"]])


_BUILDERS = {
    "heading": _build_heading,
    "html": _build_html,
    "topic": _build_topic,
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
            g = load_spec(Path(base_dir) / args["source"])
            terms = [(t["term"], t["def"]) for t in g.get("terms", [])]
            out.append(C.glossary(args.get("id", "glossary"),
                                  g.get("title", "Glossary"), terms))
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
    data = bake_all(spec.get("bake", {}))
    page = render_page(spec, data)
    stem = Path(spec_path).stem.replace(".page", "")
    out = Path(dist_dir) / stem / f"{stem}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def _stacked_layout(comp_id: str, items) -> str:
    """Fallback nav: stack every demo (no selector)."""
    return "\n".join(body for _label, body in items)


_LAYOUTS = {
    "left_rail": C.left_rail_layout,
    "top_tabs": C.variant_tabs,      # top tabs == variant_tabs (two-row via flex-wrap)
    "stacked": _stacked_layout,
}


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
    if style not in _LAYOUTS:
        raise ValueError(
            f"unknown layout style {style!r}; valid choices: {sorted(_LAYOUTS)}")

    header_html = _render_header(spec.get("header", []), base)
    items = []
    for demo_ref in spec.get("demos", []):
        demo_spec = load_spec(base / demo_ref)
        data = bake_all(demo_spec.get("bake", {}))
        fragment = render_fragment(demo_spec, data)
        items.append((demo_spec.get("title", "Demo"), fragment))

    nav = _LAYOUTS[style]("lab", items)
    body = f"{header_html}\n{nav}" if header_html else nav
    page = C.page_shell("page", body, title=spec.get("title", "Lab"))

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
        print("usage: python -m cpp_ptr_lab.yaml_engine.render_page "
              "<page.yaml> [dist_dir]", file=sys.stderr)
        sys.exit(2)
    spec_path = Path(sys.argv[1])
    dist = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parents[2] / "dist"
    spec_probe = load_spec(spec_path)
    out = build_layout(spec_path, dist) if "demos" in spec_probe else build_page(spec_path, dist)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
