"""Lab 2 — Smart Pointers topics (unique_ptr / shared_ptr / weak_ptr).

Source of truth is now ``topics/*.topic.yaml`` (loaded by the shared
``cpp_labs.topic_yaml.load_topics``). This module is a thin re-export shim so
the engine's topic registry and the integration tests keep importing
``TOPICS`` / ``TOPIC_BY_ID`` — the C++ source lives in YAML, not here.
"""
from __future__ import annotations

from pathlib import Path

from cpp_labs.code_generator import TopicTemplate
from cpp_labs.topic_yaml import load_topics

TOPIC_BY_ID: dict[str, TopicTemplate] = load_topics(Path(__file__).parent / "topics")
TOPICS: list[TopicTemplate] = list(TOPIC_BY_ID.values())
