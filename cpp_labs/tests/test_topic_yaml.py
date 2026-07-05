import pytest

from cpp_labs.topic_yaml import _topic


def _base(**over):
    d = {
        "id": "t",
        "name": "T",
        "template": "int main(){}",
        "explanation": "e",
        "group": "g",
    }
    d.update(over)
    return d


def test_standards_defaults_empty():
    assert _topic(_base()).standards == []


def test_standards_parsed():
    t = _topic(_base(standards=[11, 17, 20]))
    assert t.standards == [11, 17, 20]


def test_standards_with_dropdown_control_is_rejected():
    d = _base(
        standards=[11, 17],
        controls=[{"id": "ty", "label": "Type", "kind": "dropdown",
                   "options": ["int", "double"]}],
    )
    with pytest.raises(ValueError, match="standards"):
        _topic(d)


def test_standards_with_freetext_control_is_allowed():
    d = _base(
        standards=[11, 17],
        controls=[{"id": "v", "label": "Value", "kind": "text", "default": "0"}],
    )
    assert _topic(d).standards == [11, 17]


def test_duplicate_standards_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        _topic(_base(standards=[11, 11, 17]))
