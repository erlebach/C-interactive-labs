"""Loader tests for smart_ptrs topic YAML."""
from __future__ import annotations

from pathlib import Path

import pytest

from cpp_labs.topic_yaml import load_topics

_HERE = Path(__file__).parents[1]

_TOPIC_IDS = [
    "unique_basics", "unique_move", "unique_copy_err",
    "shared_basics", "shared_copy",
    "weak_basics", "weak_expired", "weak_cycle",
]


@pytest.fixture(scope="module")
def loaded():
    return load_topics(_HERE / "topics")


def test_all_topics_present(loaded):
    # Render order comes from the layout's demos: list, not the loader, so we
    # assert the id set — not a sequence.
    assert set(loaded) == set(_TOPIC_IDS)


def test_copy_error_has_no_ptrdata(loaded):
    assert loaded["unique_copy_err"].has_ptrdata is False
    assert loaded["unique_basics"].has_ptrdata is True


def test_cycle_break_value_map(loaded):
    ctrl = loaded["weak_cycle"].controls[0]
    assert list(ctrl.value_map) == ["Cycle (leak)", "Fix (weak_ptr)"]
    assert "weak_ptr" in ctrl.value_map["Fix (weak_ptr)"]
