"""Tests for cpp_ptr_lab.code_generator."""
import pytest
from cpp_ptr_lab.code_generator import ControlDef, TopicTemplate, generate_source


def _make_topic(**kwargs) -> TopicTemplate:
    defaults = dict(
        id="test",
        name="Test",
        template="<<HARNESS>>",
        controls=[],
        explanation="",
        group="Core",
    )
    defaults.update(kwargs)
    return TopicTemplate(**defaults)


def test_topic_template_sanitize_default():
    t = _make_topic()
    assert t.sanitize is False


def test_topic_template_has_ptrdata_default():
    t = _make_topic()
    assert t.has_ptrdata is True


def test_topic_template_sanitize_set():
    t = _make_topic(sanitize=True)
    assert t.sanitize is True


def test_topic_template_has_ptrdata_false():
    t = _make_topic(has_ptrdata=False)
    assert t.has_ptrdata is False


def test_generate_source_substitutes_placeholder():
    ctrl = ControlDef(
        id="val",
        label="Value",
        kind="text",
        default="42",
        placeholder="<<val>>",
    )
    t = _make_topic(
        template="#include <iostream>\nint main() { int x = <<val>>; <<HARNESS>> }",
        controls=[ctrl],
        target_var="x",
    )
    src = generate_source(t, {"val": "99"})
    assert "99" in src
    assert "<<val>>" not in src


def test_generate_source_injects_harness():
    t = _make_topic(
        template="int main() { int x = 0; <<HARNESS>> }",
        controls=[],
        target_var="x",
    )
    src = generate_source(t, {})
    assert "MEMBYTES" in src
    assert "<<HARNESS>>" not in src


def test_generate_source_uses_default_when_not_in_state():
    ctrl = ControlDef(
        id="val",
        label="Value",
        kind="text",
        default="77",
        placeholder="<<val>>",
    )
    t = _make_topic(
        template="int main() { int x = <<val>>; <<HARNESS>> }",
        controls=[ctrl],
        target_var="x",
    )
    src = generate_source(t, {})
    assert "77" in src


def test_topic_template_doc_url_default():
    t = _make_topic()
    assert t.doc_url == ""


def test_topic_template_doc_url_set():
    t = _make_topic(doc_url="https://example.com")
    assert t.doc_url == "https://example.com"
