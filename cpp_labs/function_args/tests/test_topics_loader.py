"""Loader tests for function_args topic YAML."""
from __future__ import annotations

from pathlib import Path

import pytest

from cpp_labs.topic_yaml import load_topics

_HERE = Path(__file__).parents[1]


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
