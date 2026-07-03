"""Shared helper for the per-subject topic-YAML equivalence guards.

Each subject's ``test_topics_loader.py`` proves its ``topics/*.topic.yaml``
reproduces a frozen ``topics_snapshot.json`` byte-for-byte. That proof needs a
canonical way to turn a ``TopicTemplate`` into plain JSON-comparable data; this
module is that single home, so no subject's tests import another subject's tests.
"""
from __future__ import annotations

from cpp_labs.code_generator import ControlDef, TopicTemplate


def serialize_control(c: ControlDef) -> dict:
    """Return a ``ControlDef`` as a plain dict (JSON-comparable)."""
    return {
        "id": c.id, "label": c.label, "kind": c.kind,
        "options": list(c.options), "default": c.default,
        "placeholder": c.placeholder, "value_map": c.value_map,
    }


def serialize_topic(t: TopicTemplate) -> dict:
    """Return a ``TopicTemplate`` as a plain dict, including its controls/cases."""
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
    """Return ``{id: serialized topic}`` for an iterable of ``TopicTemplate``."""
    return {t.id: serialize_topic(t) for t in topics}
