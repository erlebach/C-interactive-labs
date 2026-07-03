"""Loader tests + golden-equivalence guard for pointers_refs topic YAML."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cpp_labs.tests.topic_equiv import serialize_all
from cpp_labs.topic_yaml import load_topics

_HERE = Path(__file__).parents[1]
_SNAPSHOT = _HERE / "topics_snapshot.json"


_LEGACY_ORDER = [
    "basic_ptr", "const_taxonomy", "ref_must_bind", "ref_no_null",
    "ref_rebind_illusion", "ref_const", "null_deref", "dangling_ptr",
]


@pytest.fixture(scope="module")
def loaded():
    return load_topics(_HERE / "topics")


def test_all_topics_present(loaded):
    # Render order comes from the layout's demos: list, not the loader, so we
    # assert the id set — not a sequence.
    assert set(loaded) == set(_LEGACY_ORDER)


def test_load_basic_ptr_roundtrips(loaded):
    t = loaded["basic_ptr"]
    assert t.target_var == "ptr"
    assert "<<type>>" in t.template and "<<HARNESS>>" in t.template
    assert [c.id for c in t.controls] == ["type", "value"]


def test_value_map_loaded(loaded):
    ctrl = loaded["ref_no_null"].controls[0]
    assert ctrl.value_map is not None
    assert "nullptr" in ctrl.value_map["Show null ptr"]


def test_cases_loaded(loaded):
    cases = loaded["const_taxonomy"].cases
    assert cases is not None and len(cases) == 2
    assert "*ptr = 99" in cases[0].subs["<<op>>"]      # case[0] = write
    assert "ptr = &other" in cases[1].subs["<<op>>"]   # case[1] = rebind


def test_defaults_applied(loaded):
    t = loaded["ref_must_bind"]
    assert t.sanitize is False
    assert t.has_ptrdata is False   # ref_must_bind sets this explicitly
    assert loaded["basic_ptr"].has_ptrdata is True
    assert loaded["basic_ptr"].cases is None


def test_yaml_matches_legacy(loaded):
    """Equivalence guard: YAML reproduces the frozen Python snapshot exactly."""
    golden = json.loads(_SNAPSHOT.read_text())
    actual = serialize_all(loaded.values())
    assert actual == golden


def test_missing_required_field_raises():
    from cpp_labs.topic_yaml import _topic
    with pytest.raises(ValueError, match="name"):
        _topic({"id": "x", "template": "t", "explanation": "e", "group": "g"})
