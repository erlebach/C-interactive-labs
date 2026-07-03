"""Operator Overloading topics.

Source of truth is ``topics/*.topic.yaml`` (loaded by the generic
``topics_loader.load_topics``). This module is a thin re-export shim so the
engine's topic registry can import the topics by id — the C++ lives in YAML.

(The loader currently lives under ``pointers_refs``; promoting it to a shared
module is the planned reusability step, after which this import shortens.)
"""
from __future__ import annotations

from pathlib import Path

from cpp_ptr_lab.code_generator import TopicTemplate

from ..pointers_refs.topics_loader import load_topics

TOPIC_BY_ID: dict[str, TopicTemplate] = load_topics(Path(__file__).parent / "topics")
TOPICS: list[TopicTemplate] = list(TOPIC_BY_ID.values())
