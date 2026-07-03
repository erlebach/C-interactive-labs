"""Build orchestrator for the C++ Pointer Lab static HTML output.

Entry point: ``python -m cpp_labs.build_html``

For each lab (pointers_refs, smart_ptrs) and each topic in that lab:
  1. Expand variants from the topic's categorical controls.
  2. For each variant: generate source → compile+run → parse output.
  3. Render a fragment via :func:`html_renderer.render_fragment`.
  4. Write ``dist/topics/<topic_id>.html`` (one fragment, standalone).
  5. Write ``dist/lab_<lab>.html`` (all fragments for the lab, combined).

Only categorical (dropdown) controls produce variants; free-text controls are
dropped (their default is baked in).  Topics with no categorical controls
yield a single variant.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from .code_generator import ControlDef, TopicTemplate, generate_source
from .compiler_runner import compile_and_run, parse_membytes
from .html_renderer import assemble_page, render_fragment, svg_renderer


# ---------------------------------------------------------------------------
# Variant expansion
# ---------------------------------------------------------------------------


def expand_variants(topic: TopicTemplate) -> list[dict[str, str]]:
    """Return a list of control-state dicts, one per categorical variant.

    Categorical controls are those with ``kind == "dropdown"``.  For every
    combination of dropdown options (there is at most one dropdown per topic
    in the current set), one dict is produced.  Free-text controls always use
    their default value.  If no dropdown control exists, one dict (all
    defaults) is returned.
    """
    # Seed all controls with their defaults
    base: dict[str, str | bool] = {}
    dropdowns: list[ControlDef] = []
    for ctrl in topic.controls:
        if ctrl.kind == "dropdown":
            dropdowns.append(ctrl)
        else:
            # Free-text / checkbox — bake in the default. Preserve the
            # default's type (notably bool for checkboxes) so the resolver
            # keys on "true"/"false", not the stringified bare "False".
            base[ctrl.id] = ctrl.default

    if not dropdowns:
        return [dict(base)]

    # Enumerate combinations (currently only one dropdown per topic)
    # If multiple dropdowns existed we'd take the Cartesian product, but the
    # current topic set has at most one, so a simple loop suffices.
    results = []
    for combo in _cartesian(dropdowns):
        state = dict(base)
        state.update(combo)
        results.append(state)
    return results


def _cartesian(dropdowns: list[ControlDef]) -> list[dict[str, str]]:
    """Return the Cartesian product of dropdown option lists as dicts."""
    if not dropdowns:
        return [{}]
    ctrl = dropdowns[0]
    rest = _cartesian(dropdowns[1:])
    result = []
    for option in ctrl.options:
        for suffix in rest:
            d = {ctrl.id: option}
            d.update(suffix)
            result.append(d)
    return result


# ---------------------------------------------------------------------------
# Per-variant capture
# ---------------------------------------------------------------------------


def capture_variant(topic: TopicTemplate, control_state: dict[str, str]) -> dict[str, Any]:
    """Compile and run one variant; return a render-data dict.

    Keys:
      label      — human-readable label from the control options
      source     — generated C++ source
      svg        — inline SVG string
      stdout     — program stdout (or "" on compile failure)
      membytes   — parsed MEMBYTES hex string (or "n/a")
      failed     — True if compilation failed
      stderr     — compiler stderr (non-empty when failed)
    """
    # Build a human-readable label from the categorical control values
    label_parts = []
    for ctrl in topic.controls:
        if ctrl.kind == "dropdown":
            label_parts.append(control_state.get(ctrl.id, ctrl.default))
    label = " / ".join(str(p) for p in label_parts) if label_parts else ""

    # Multi-case topics: compile one independent sub-case per CaseDef and
    # bundle them under this variant.  The variant itself carries only the
    # label; each sub-case carries its own source / compile result / svg.
    if topic.cases:
        cases = []
        for case in topic.cases:
            sub = _compile_one(topic, control_state, case.subs)
            sub["label"] = case.label
            cases.append(sub)
        return {"label": label, "cases": cases}

    return {"label": label, **_compile_one(topic, control_state, None)}


def _compile_one(
    topic: TopicTemplate,
    control_state: dict,
    extra_subs: dict[str, str] | None,
) -> dict[str, Any]:
    """Compile+run a single program and return its render-data dict (no label)."""
    source = generate_source(topic, control_state, extra_subs)
    result = compile_and_run(source)

    if result.status == "compile-failed":
        return {
            "source": source,
            "ptrdata": None,
            "svg": svg_renderer(None),
            "stdout": "",
            "membytes": "n/a",
            "failed": True,
            "stderr": result.compiler_stderr,
        }

    ptrdata = result.ptrdata
    membytes = result.memory_bytes or parse_membytes(result.stdout)

    return {
        "source": source,
        "ptrdata": ptrdata,
        "svg": svg_renderer(ptrdata),
        "stdout": result.stdout,
        "membytes": membytes,
        "failed": False,
        "stderr": "",
    }


# ---------------------------------------------------------------------------
# Lab build
# ---------------------------------------------------------------------------


def build_lab(lab_id: str, topics: list[TopicTemplate], dist_dir: Path) -> None:
    """Build all HTML outputs for one lab into *dist_dir*.

    Raises ``RuntimeError`` if ``g++`` is not available.
    Writes:
      - ``dist_dir/topics/<topic_id>.html`` for each topic
      - ``dist_dir/lab_<lab_id>.html`` combining all topics
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. "
            "Install a C++ compiler before running the static build."
        )

    topics_dir = dist_dir / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    all_fragments: list[str] = []

    for topic in topics:
        control_states = expand_variants(topic)
        variants = [capture_variant(topic, cs) for cs in control_states]
        fragment = render_fragment(topic, variants)
        all_fragments.append(fragment)

        # Per-topic standalone file
        per_topic_html = assemble_page([fragment], title=topic.name)
        (topics_dir / f"{topic.id}.html").write_text(per_topic_html, encoding="utf-8")

    # Per-lab combined file
    topic_meta = [(t.id, t.name) for t in topics]
    lab_html = assemble_page(all_fragments, title=f"C++ Lab — {lab_id}", topics=topic_meta)
    (dist_dir / f"lab_{lab_id}.html").write_text(lab_html, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Build both labs into ``dist/`` in the project root."""
    if shutil.which("g++") is None:
        print(
            "ERROR: g++ not found on PATH. "
            "Install a C++ compiler (e.g. Xcode Command Line Tools on macOS, "
            "or build-essential on Debian/Ubuntu) before running the static build.",
            file=sys.stderr,
        )
        sys.exit(1)

    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist_labs"

    from .pointers_refs.topics import (
        basic_ptr,
        const_taxonomy,
        null_deref,
        ref_const,
        ref_must_bind,
        ref_no_null,
        ref_rebind_illusion,
    )
    from .smart_ptrs.topics import TOPICS as SMART_TOPICS

    pointers_refs_topics = [
        basic_ptr,
        const_taxonomy,
        ref_must_bind,
        ref_no_null,
        ref_rebind_illusion,
        ref_const,
        null_deref,
    ]

    print("Building lab: pointers_refs …")
    build_lab("pointers_refs", pointers_refs_topics, dist_dir)

    print("Building lab: smart_ptrs …")
    build_lab("smart_ptrs", SMART_TOPICS, dist_dir)

    print(f"Done. Output in {dist_dir}/")


if __name__ == "__main__":
    main()
