"""Tests for the code generation module."""

from __future__ import annotations

from cpp_initializer_lab.code_generator import ControlDef, TopicTemplate, generate_source
from cpp_initializer_lab.topics import (
    COPY_INIT,
    EXPLICIT_VS_IMPLICIT,
    LIST_INIT,
    VALUE_INIT,
)


# ---------------------------------------------------------------------------
# 3.4 (a) — list/brace init with type=int, value=5 → "int x{5};" + harness
# ---------------------------------------------------------------------------


def test_list_init_int_5():
    src = generate_source(LIST_INIT, {"type": "int", "value": "5"})
    assert "int x{5};" in src
    assert "MEMBYTES:" in src
    assert "// --- instrumentation (not part of the lesson) ---" in src
    assert "// --- end instrumentation ---" in src


# ---------------------------------------------------------------------------
# 3.4 (b) — copy init with explicit checkbox → "explicit" + "Foo f = 42;"
# ---------------------------------------------------------------------------


def test_explicit_copy_init():
    src = generate_source(EXPLICIT_VS_IMPLICIT, {"explicit": True, "form": "copy"})
    assert "explicit Foo(int v)" in src
    assert "Foo f = 42;" in src


def test_no_explicit_copy_init():
    """Without explicit, the keyword is absent but the init line remains."""
    src = generate_source(EXPLICIT_VS_IMPLICIT, {"explicit": False, "form": "copy"})
    assert "explicit Foo" not in src
    assert "Foo f = 42;" in src


def test_explicit_direct_init():
    """Direct-init form produces Foo f(42); and compiles even with explicit."""
    src = generate_source(EXPLICIT_VS_IMPLICIT, {"explicit": True, "form": "direct"})
    assert "explicit Foo(int v)" in src
    assert "Foo f(42);" in src


# ---------------------------------------------------------------------------
# 3.4 (c) — list init with type=int, value=3.14 → "int x{3.14};"
# ---------------------------------------------------------------------------


def test_list_init_narrowing():
    src = generate_source(LIST_INIT, {"type": "int", "value": "3.14"})
    assert "int x{3.14};" in src


# ---------------------------------------------------------------------------
# Extra coverage
# ---------------------------------------------------------------------------


def test_value_init_int():
    src = generate_source(VALUE_INIT, {"type": "int"})
    assert "int x{};" in src
    assert "MEMBYTES:" in src


def test_copy_init_double():
    src = generate_source(COPY_INIT, {"type": "double", "value": "3.0"})
    assert "double x = 3.0;" in src


def test_defaults_used_when_state_missing():
    """Missing control values fall back to the control defaults."""
    src = generate_source(LIST_INIT, {})
    # default type=int, default value=5
    assert "int x{5};" in src


def test_harness_references_target_var():
    """The harness must reference the topic's target variable."""
    src = generate_source(EXPLICIT_VS_IMPLICIT, {"explicit": False, "form": "copy"})
    assert "reinterpret_cast<unsigned char*>(&f)" in src
    assert "sizeof(f)" in src


def test_full_program_structure():
    """Generated source is a complete C++ program."""
    src = generate_source(VALUE_INIT, {"type": "int"})
    assert "#include <iostream>" in src
    assert "#include <cstdio>" in src
    assert "int main()" in src
    assert src.rstrip().endswith("}")


def test_custom_topic_placeholder_substitution():
    """A hand-built TopicTemplate with a value_map exercises the resolver."""
    topic = TopicTemplate(
        id="custom",
        name="Custom",
        group="Core",
        target_var="x",
        explanation="Test.",
        controls=[
            ControlDef(
                id="form",
                label="Form",
                kind="dropdown",
                options=["brace", "paren"],
                default="brace",
                placeholder="<<form>>",
                value_map={"brace": "{<<value>>}", "paren": "(<<value>>)"},
            ),
            ControlDef(
                id="value",
                label="Value",
                kind="text",
                default="7",
                placeholder="<<value>>",
            ),
        ],
        template="""\
int main() {
    int x<<form>>;
    <<HARNESS>>
    return 0;
}
""",
    )
    src = generate_source(topic, {"form": "brace", "value": "9"})
    assert "int x{9};" in src
    src2 = generate_source(topic, {"form": "paren", "value": "9"})
    assert "int x(9);" in src2
