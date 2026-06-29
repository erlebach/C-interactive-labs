"""Tests for cpp_ptr_lab.yaml_config."""
import pytest
from cpp_ptr_lab.code_generator import ControlDef, TopicTemplate
from cpp_ptr_lab.yaml_config import load_enabled_topics


def _make_topic(id: str) -> TopicTemplate:
    return TopicTemplate(
        id=id,
        name=id,
        template="",
        controls=[],
        explanation="",
        group="Core",
    )


ALL = [_make_topic("a"), _make_topic("b"), _make_topic("c")]


def test_topic_disabled_excluded(tmp_path):
    yaml_file = tmp_path / "lab_config.yaml"
    yaml_file.write_text("pointers_refs:\n  topics:\n    a: false\n    b: true\n")
    result = load_enabled_topics(yaml_file, "pointers_refs", ALL)
    ids = [t.id for t in result]
    assert "a" not in ids
    assert "b" in ids


def test_topic_absent_defaults_enabled(tmp_path):
    yaml_file = tmp_path / "lab_config.yaml"
    yaml_file.write_text("pointers_refs:\n  topics:\n    a: false\n")
    result = load_enabled_topics(yaml_file, "pointers_refs", ALL)
    ids = [t.id for t in result]
    assert "b" in ids
    assert "c" in ids


def test_lab_disabled_returns_empty(tmp_path):
    yaml_file = tmp_path / "lab_config.yaml"
    yaml_file.write_text("pointers_refs:\n  enabled: false\n")
    result = load_enabled_topics(yaml_file, "pointers_refs", ALL)
    assert result == []


def test_missing_file_returns_all(tmp_path, capsys):
    yaml_file = tmp_path / "no_such.yaml"
    result = load_enabled_topics(yaml_file, "pointers_refs", ALL)
    assert result == ALL
    captured = capsys.readouterr()
    assert captured.err != ""


def test_malformed_yaml_returns_all(tmp_path, capsys):
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text(": [\ninvalid yaml{{{\n")
    result = load_enabled_topics(yaml_file, "pointers_refs", ALL)
    assert result == ALL
    captured = capsys.readouterr()
    assert captured.err != ""


def test_all_topics_enabled(tmp_path):
    yaml_file = tmp_path / "lab_config.yaml"
    yaml_file.write_text(
        "pointers_refs:\n  enabled: true\n  topics:\n    a: true\n    b: true\n    c: true\n"
    )
    result = load_enabled_topics(yaml_file, "pointers_refs", ALL)
    assert len(result) == 3
