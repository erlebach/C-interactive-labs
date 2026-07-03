"""Lab 1 — Pointers & References topics.

Source of truth is now ``topics/*.topic.yaml`` (loaded by ``topics_loader``).
This module is a thin re-export shim so existing importers keep working:
the C++ source lives in YAML, not here.
"""
from __future__ import annotations

from cpp_ptr_lab.code_generator import TopicTemplate

from .topics_loader import load_topics

TOPIC_BY_ID: dict[str, TopicTemplate] = load_topics()
TOPICS: list[TopicTemplate] = list(TOPIC_BY_ID.values())

basic_ptr = TOPIC_BY_ID["basic_ptr"]
const_taxonomy = TOPIC_BY_ID["const_taxonomy"]
ref_must_bind = TOPIC_BY_ID["ref_must_bind"]
ref_no_null = TOPIC_BY_ID["ref_no_null"]
ref_rebind_illusion = TOPIC_BY_ID["ref_rebind_illusion"]
ref_const = TOPIC_BY_ID["ref_const"]
null_deref = TOPIC_BY_ID["null_deref"]
dangling_ptr = TOPIC_BY_ID["dangling_ptr"]
