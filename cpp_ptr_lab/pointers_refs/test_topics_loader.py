"""Loader tests + golden-equivalence guard for pointers_refs topic YAML."""
from __future__ import annotations

import json
from pathlib import Path

from cpp_ptr_lab.code_generator import TopicTemplate

_HERE = Path(__file__).parent
_SNAPSHOT = _HERE / "topics_snapshot.json"


def serialize_control(c) -> dict:
    return {
        "id": c.id, "label": c.label, "kind": c.kind,
        "options": list(c.options), "default": c.default,
        "placeholder": c.placeholder, "value_map": c.value_map,
    }


def serialize_topic(t: TopicTemplate) -> dict:
    return {
        "id": t.id, "name": t.name, "group": t.group, "doc_url": t.doc_url,
        "explanation": t.explanation, "target_var": t.target_var,
        "template": t.template, "sanitize": t.sanitize,
        "has_ptrdata": t.has_ptrdata,
        "controls": [serialize_control(c) for c in t.controls],
        "cases": ([{"label": c.label, "subs": c.subs} for c in t.cases]
                  if t.cases else None),
    }


def serialize_all(topics) -> dict:
    return {t.id: serialize_topic(t) for t in topics}
