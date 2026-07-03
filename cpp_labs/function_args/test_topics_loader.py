"""Loader tests + golden-equivalence guard for function_args topic YAML."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cpp_labs.tests.topic_equiv import serialize_all
from cpp_labs.topic_yaml import load_topics

_HERE = Path(__file__).parent
_SNAPSHOT = _HERE / "topics_snapshot.json"


@pytest.fixture(scope="module")
def loaded():
    return load_topics(_HERE / "topics")


def test_single_topic_loaded(loaded):
    assert list(loaded.keys()) == ["function_args"]


def test_mode_dropdown_value_map(loaded):
    ctrl = loaded["function_args"].controls[0]
    assert ctrl.id == "mode"
    assert list(ctrl.value_map) == ["by value", "by pointer", "by reference"]
    assert "*x = 99" in ctrl.value_map["by pointer"]


def test_yaml_matches_legacy(loaded):
    """Equivalence guard: YAML reproduces the frozen Python snapshot exactly."""
    golden = json.loads(_SNAPSHOT.read_text())
    actual = serialize_all(loaded.values())
    assert actual == golden
