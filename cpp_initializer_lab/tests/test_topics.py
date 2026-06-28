"""Tests for the topic content module — verifies spec scenarios per topic."""

from __future__ import annotations

from cpp_initializer_lab.code_generator import generate_source
from cpp_initializer_lab.topics import (
    AGGREGATE_INIT,
    COPY_INIT,
    DEFAULT_INIT,
    DIRECT_INIT,
    EXPLICIT_VS_IMPLICIT,
    INIT_LIST_HIJACK,
    LIST_INIT,
    MOST_VEXING_PARSE,
    TOPICS,
    TOPIC_BY_ID,
    VALUE_INIT,
)


# ---------------------------------------------------------------------------
# 4.1 — 6 core topics exist and are in the "Core" group
# ---------------------------------------------------------------------------


def test_six_core_topics_present():
    core_ids = [t.id for t in TOPICS if t.group == "Core"]
    assert core_ids == ["default", "value", "direct", "copy", "list", "aggregate"]


def test_three_gotcha_topics_present():
    gotcha_ids = [t.id for t in TOPICS if t.group == "Gotchas"]
    assert gotcha_ids == [
        "most-vexing-parse",
        "explicit-vs-implicit",
        "initializer-list-hijack",
    ]


def test_topic_by_id_lookup():
    assert TOPIC_BY_ID["list"] is LIST_INIT
    assert TOPIC_BY_ID["most-vexing-parse"] is MOST_VEXING_PARSE


# ---------------------------------------------------------------------------
# 4.3 — Spec scenarios
# ---------------------------------------------------------------------------


def test_default_init_exposes_type():
    """Default init with type=double → 'double x;' with no initializer."""
    src = generate_source(DEFAULT_INIT, {"type": "double"})
    assert "double x;" in src
    # No initializer braces
    assert "double x{}" not in src
    assert "double x(" not in src


def test_value_init_exposes_type():
    """Value init with type=int → 'int x{};'."""
    src = generate_source(VALUE_INIT, {"type": "int"})
    assert "int x{};" in src


def test_list_init_narrowing_int_double():
    """List/brace init with type=int, value=3.14 → 'int x{3.14};'."""
    src = generate_source(LIST_INIT, {"type": "int", "value": "3.14"})
    assert "int x{3.14};" in src


def test_direct_init_form():
    src = generate_source(DIRECT_INIT, {"type": "int", "value": "5"})
    assert "int x(5);" in src


def test_copy_init_form():
    src = generate_source(COPY_INIT, {"type": "int", "value": "5"})
    assert "int x = 5;" in src


def test_aggregate_init_two_fields():
    src = generate_source(AGGREGATE_INIT, {"field_count": "2", "values": "1, 2"})
    assert "S s{1, 2};" in src
    assert "int c;" not in src  # no extra fields


def test_aggregate_init_four_fields():
    src = generate_source(AGGREGATE_INIT, {"field_count": "4", "values": "1, 2, 3, 4"})
    assert "S s{1, 2, 3, 4};" in src
    assert "int c;" in src
    assert "int d;" in src


def test_most_vexing_parse_parentheses():
    """MVP with parentheses → 'Widget w();' (function declaration)."""
    src = generate_source(MOST_VEXING_PARSE, {"form": "parentheses"})
    assert "Widget w();" in src


def test_most_vexing_parse_braces():
    """MVP with braces → 'Widget w{};' (object)."""
    src = generate_source(MOST_VEXING_PARSE, {"form": "braces"})
    assert "Widget w{};" in src


def test_explicit_copy_init_produces_explicit_keyword():
    """Explicit + copy-init → 'explicit' keyword and 'Foo f = 42;'."""
    src = generate_source(EXPLICIT_VS_IMPLICIT, {"explicit": True, "form": "copy"})
    assert "explicit Foo(int v)" in src
    assert "Foo f = 42;" in src


def test_initializer_list_hijack_brace_single_value():
    """Init-list hijack with brace + single value → 'Foo f{5};'."""
    src = generate_source(INIT_LIST_HIJACK, {"form": "brace", "value": "5"})
    assert "Foo f{5};" in src


def test_initializer_list_hijack_paren_single_value():
    """Init-list hijack with paren + single value → 'Foo f(5);'."""
    src = generate_source(INIT_LIST_HIJACK, {"form": "paren", "value": "5"})
    assert "Foo f(5);" in src


# ---------------------------------------------------------------------------
# 4.4 — Explanatory text is 2-4 sentences per topic
# ---------------------------------------------------------------------------


def test_explanations_are_2_to_4_sentences():
    for topic in TOPICS:
        # Count sentence-ending periods (rough heuristic).
        count = topic.explanation.count(".")
        assert 2 <= count <= 4, (
            f"Topic '{topic.id}' explanation has {count} sentence-ending "
            f"periods; expected 2-4.\nExplanation: {topic.explanation!r}"
        )


# ---------------------------------------------------------------------------
# Harness presence in every topic
# ---------------------------------------------------------------------------


def test_every_topic_has_harness_marker():
    for topic in TOPICS:
        assert "<<HARNESS>>" in topic.template, f"Topic '{topic.id}' missing <<HARNESS>>"


def test_every_topic_generates_membytes_line():
    """Every topic, with its default controls, produces a MEMBYTES: line."""
    for topic in TOPICS:
        src = generate_source(topic, {})
        assert "MEMBYTES:" in src, f"Topic '{topic.id}' missing MEMBYTES: in output"
        assert "// --- instrumentation" in src
