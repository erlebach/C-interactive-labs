"""Loader tests for function_args topic YAML."""
from __future__ import annotations

from pathlib import Path

import pytest

from cpp_labs.topic_yaml import load_topics

_HERE = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def loaded():
    return load_topics(_HERE / "topics")


def test_all_topics_loaded(loaded):
    # the core "pass three ways" topic plus the four added examples
    assert set(loaded) == {
        "function_args", "fa_const_ref", "fa_swap", "fa_out_param", "fa_copy_cost",
    }


def test_mode_dropdown_value_map(loaded):
    ctrl = loaded["function_args"].controls[0]
    assert ctrl.id == "mode"
    assert list(ctrl.value_map) == ["by value", "by pointer", "by reference"]
    assert "*x = 99" in ctrl.value_map["by pointer"]
