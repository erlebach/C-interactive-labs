"""Load pointers_refs topic definitions from YAML into TopicTemplate objects.

Source of truth for each topic's C++ template, controls, and sub-cases is a
``topics/<id>.topic.yaml`` file next to this module.  This loader is the only
place that knows the YAML shape; ``topics.py`` is a thin re-export shim over it.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from cpp_ptr_lab.code_generator import CaseDef, ControlDef, TopicTemplate

_TOPICS_DIR = Path(__file__).parent / "topics"

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


def load_topics(topics_dir: Path | None = None) -> dict[str, TopicTemplate]:
    """Return ``{id: TopicTemplate}`` for all ``*.topic.yaml`` in *topics_dir*.

    Ordered by each file's ``order:`` integer (falls back to id for ties).
    """
    directory = topics_dir or _TOPICS_DIR
    docs = []
    for path in directory.glob("*.topic.yaml"):
        data = yaml.safe_load(path.read_text())
        docs.append(data)
    docs.sort(key=lambda d: (d.get("order", 1_000_000), d.get("id", "")))
    return {d["id"]: _topic(d) for d in docs}
