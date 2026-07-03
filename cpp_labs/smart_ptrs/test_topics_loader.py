"""Loader tests + golden-equivalence guard for smart_ptrs topic YAML."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cpp_labs.pointers_refs.test_topics_loader import serialize_all
from cpp_labs.topic_yaml import load_topics

_HERE = Path(__file__).parent
_SNAPSHOT = _HERE / "topics_snapshot.json"

_LEGACY_ORDER = [
    "unique_basics", "unique_move", "unique_copy_err",
    "shared_basics", "shared_copy",
    "weak_basics", "weak_expired", "weak_cycle",
]


@pytest.fixture(scope="module")
def loaded():
    return load_topics(_HERE / "topics")


def test_order_preserved(loaded):
    assert list(loaded.keys()) == _LEGACY_ORDER


def test_copy_error_has_no_ptrdata(loaded):
    assert loaded["unique_copy_err"].has_ptrdata is False
    assert loaded["unique_basics"].has_ptrdata is True


def test_cycle_break_value_map(loaded):
    ctrl = loaded["weak_cycle"].controls[0]
    assert list(ctrl.value_map) == ["Cycle (leak)", "Fix (weak_ptr)"]
    assert "weak_ptr" in ctrl.value_map["Fix (weak_ptr)"]


def test_yaml_matches_legacy(loaded):
    """Equivalence guard: YAML reproduces the frozen Python snapshot exactly."""
    golden = json.loads(_SNAPSHOT.read_text())
    actual = serialize_all(loaded.values())
    assert actual == golden
