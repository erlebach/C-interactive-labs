"""Load a subject's topic definitions from YAML into TopicTemplate objects.

Shared across subjects: the source of truth for each topic's C++ template,
controls, and sub-cases is a ``<subject>/topics/<id>.topic.yaml`` file. This
loader is the only place that knows the YAML shape; each subject's ``topics.py``
is a thin re-export shim that calls :func:`load_topics` with its own topics dir.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from cpp_labs.code_generator import CaseDef, ControlDef, TopicTemplate

_REQUIRED = ("id", "name", "template", "explanation", "group")


def _control(d: dict) -> ControlDef:
    return ControlDef(
        id=d["id"],
        label=d["label"],
        kind=d["kind"],
        options=list(d.get("options", [])),
        default=d.get("default", ""),
        placeholder=d.get("placeholder", ""),
        value_map=d.get("value_map"),
    )


def _case(d: dict) -> CaseDef:
    return CaseDef(label=d["label"], subs=dict(d.get("subs", {})))


def _topic(d: dict) -> TopicTemplate:
    for key in _REQUIRED:
        if key not in d:
            raise ValueError(f"topic YAML missing required field {key!r}: {d.get('id', '?')}")
    cases = d.get("cases")
    return TopicTemplate(
        id=d["id"],
        name=d["name"],
        template=d["template"],
        controls=[_control(c) for c in d.get("controls", [])],
        explanation=d["explanation"],
        group=d["group"],
        target_var=d.get("target_var", "x"),
        sanitize=d.get("sanitize", False),
        has_ptrdata=d.get("has_ptrdata", True),
        doc_url=d.get("doc_url", ""),
        cases=[_case(c) for c in cases] if cases else None,
    )


def load_topics(topics_dir: Path) -> dict[str, TopicTemplate]:
    """Return ``{id: TopicTemplate}`` for all ``*.topic.yaml`` in *topics_dir*.

    Keyed by id and sorted by id for a stable, reproducible order. The order in
    which examples actually appear in a demonstration is set by the layout's
    ``demos:`` list — not here — so a topic file needs no ``order:`` field.
    """
    docs = [yaml.safe_load(p.read_text()) for p in topics_dir.glob("*.topic.yaml")]
    docs.sort(key=lambda d: d.get("id", ""))
    return {d["id"]: _topic(d) for d in docs}


def discover_topics(root: Path) -> dict[str, TopicTemplate]:
    """Return one ``{id: TopicTemplate}`` registry for every subject under *root*.

    Scans ``root/*/topics`` — each subject folder that owns a ``topics/`` dir
    contributes its topic files — and merges them into a single id-keyed
    registry. A subject that only *reuses* another's topics (no ``topics/`` dir
    of its own) is skipped; its page still resolves those ids from this merged
    set. This is what lets a brand-new subject be pure YAML: drop a folder with
    a ``topics/`` dir and a layout, and the engine finds it with no code change.

    Args:
        root: The package root holding the subject folders (i.e. ``cpp_labs/``).

    Returns:
        A ``{id: TopicTemplate}`` mapping across all subjects. If two subjects
        define the same id, the last one scanned (by sorted path) wins.
    """
    reg: dict[str, TopicTemplate] = {}
    for topics_dir in sorted(root.glob("*/topics")):
        reg.update(load_topics(topics_dir))
    return reg
