"""End-to-end integration tests for the C++ Initializer Lab.

These tests substitute for the manual GUI test that task 6.2 calls for (the
GUI cannot be launched in a headless environment). They exercise the same
code paths the GUI uses:

1. The :mod:`cpp_initializer_lab.app` module imports cleanly (task 6.6).
2. Every one of the 9 topics can generate a non-empty C++ source string
   via :func:`generate_source` (task 6.2b).
3. A generated value-init snippet compiles and runs, returning
   ``status="success"`` with a parseable ``MEMBYTES:`` line (task 6.2c).
4. List-init with a narrowing ``int x{3.14}`` fails to compile
   (task 6.3).
5. The explicit-vs-implicit topic with ``explicit=True`` and ``form=copy``
   fails to compile (task 6.4).
6. The most-vexing-parse topic with ``form=parentheses`` generates source
   containing ``Widget w()`` (task 6.5).

Run with::

    python -m pytest cpp_initializer_lab/tests/test_integration.py -v
"""

from __future__ import annotations

import shutil

import pytest

import re

from cpp_initializer_lab import app as app_module
from cpp_initializer_lab.code_generator import generate_source
from cpp_initializer_lab.compiler_runner import compile_and_run, probe_gpp
from cpp_initializer_lab.topics import TOPICS, TOPIC_BY_ID


# Matches an unresolved <<placeholder>> (double-angle-bracket) marker. We
# deliberately match the full ``<<name>>`` form rather than just ``<<`` so
# that legitimate C++ operators like ``std::cout <<`` do not false-positive.
_PLACEHOLDER_RE = re.compile(r"<<[A-Za-z_][A-Za-z0-9_]*>>")


# Skip the g++-dependent tests entirely if no compiler is available on this
# machine (e.g. CI without a toolchain). The pure-Python tests still run.
GPP_AVAILABLE = shutil.which("g++") is not None
gpp_required = pytest.mark.skipif(
    not GPP_AVAILABLE, reason="g++ not available on this machine"
)


# ---------------------------------------------------------------------------
# Task 6.6 — app module imports cleanly
# ---------------------------------------------------------------------------


def test_app_module_imports() -> None:
    """The GUI entry-point module must import without raising."""
    # Importing already happened at module top; assert it has the expected
    # public surface so a future refactor cannot silently break the entry
    # point.
    assert hasattr(app_module, "main")
    assert callable(app_module.main)
    assert hasattr(app_module, "InitializerLabApp")


# ---------------------------------------------------------------------------
# Task 6.2b — every topic generates source
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("topic", TOPICS, ids=[t.id for t in TOPICS])
def test_every_topic_generates_source(topic) -> None:
    """Each of the 9 topics must produce non-empty C++ source."""
    # Seed control_state from defaults, exactly as the GUI does on startup.
    control_state = {ctrl.id: ctrl.default for ctrl in topic.controls}
    source = generate_source(topic, control_state)
    assert isinstance(source, str)
    assert source.strip(), f"topic {topic.id!r} produced empty source"
    # No leftover placeholders should remain.
    leftover = _PLACEHOLDER_RE.findall(source)
    assert not leftover, (
        f"topic {topic.id!r} left unresolved placeholders {leftover!r}:\n{source}"
    )
    # Every generated program must contain the harness marker output line.
    assert "MEMBYTES:" in source


# ---------------------------------------------------------------------------
# Task 6.2c — value-init snippet compiles and runs successfully
# ---------------------------------------------------------------------------


@gpp_required
def test_value_init_runs_successfully() -> None:
    """A value-init snippet must compile, run, and print MEMBYTES."""
    topic = TOPIC_BY_ID["value"]
    control_state = {"type": "int"}
    source = generate_source(topic, control_state)
    result = compile_and_run(source)
    assert result.status == "success", (
        f"expected success, got {result.status!r}: "
        f"compiler_stderr={result.compiler_stderr!r} stderr={result.stderr!r}"
    )
    # memory_bytes must be a real hex string, not "n/a".
    assert result.memory_bytes != "n/a", (
        f"no MEMBYTES line parsed from stdout: {result.stdout!r}"
    )
    # The bytes should be all zeros for value-init of an int.
    bytes_list = result.memory_bytes.split()
    assert len(bytes_list) >= 1
    for b in bytes_list:
        # Each byte is two hex digits.
        assert len(b) == 2
        int(b, 16)  # must parse as hex


# ---------------------------------------------------------------------------
# Task 6.3 — narrowing rejection in list-init
# ---------------------------------------------------------------------------


@gpp_required
def test_list_init_narrowing_rejected() -> None:
    """``int x{3.14}`` must fail to compile (narrowing forbidden)."""
    topic = TOPIC_BY_ID["list"]
    control_state = {"type": "int", "value": "3.14"}
    source = generate_source(topic, control_state)
    # Sanity check the source shape before running.
    assert "int x{3.14}" in source
    result = compile_and_run(source)
    assert result.status == "compile-failed", (
        f"expected compile-failed, got {result.status!r}; "
        f"compiler_stderr={result.compiler_stderr!r}"
    )
    assert result.memory_bytes == "n/a"


# ---------------------------------------------------------------------------
# Task 6.4 — explicit ctor + copy-init fails
# ---------------------------------------------------------------------------


@gpp_required
def test_explicit_copy_init_fails() -> None:
    """``Foo f = 42`` with an explicit ctor must fail to compile."""
    topic = TOPIC_BY_ID["explicit-vs-implicit"]
    control_state = {"explicit": True, "form": "copy"}
    source = generate_source(topic, control_state)
    # Sanity check the source shape.
    assert "explicit Foo(int v)" in source
    assert "Foo f = 42" in source
    result = compile_and_run(source)
    assert result.status == "compile-failed", (
        f"expected compile-failed, got {result.status!r}; "
        f"compiler_stderr={result.compiler_stderr!r}"
    )


# ---------------------------------------------------------------------------
# Task 6.5 — most-vexing-parse source shape
# ---------------------------------------------------------------------------


def test_most_vexing_parse_parentheses_shape() -> None:
    """The parentheses form must generate ``Widget w()``.

    Running it may compile-fail (that is the lesson), so we only verify the
    source shape here.
    """
    topic = TOPIC_BY_ID["most-vexing-parse"]
    control_state = {"form": "parentheses"}
    source = generate_source(topic, control_state)
    assert "Widget w();" in source, (
        f"expected 'Widget w();' in source:\n{source}"
    )


# ---------------------------------------------------------------------------
# Bonus: probe_gpp sanity (used by the GUI on startup)
# ---------------------------------------------------------------------------


@gpp_required
def test_probe_gpp_reports_available() -> None:
    """On a machine with g++, probe_gpp must report ``available``."""
    status = probe_gpp()
    assert status.status == "available"
    assert status.version  # non-empty version string


# ---------------------------------------------------------------------------
# Guard: never use the non-existent dpg.add_frame_callback API
# ---------------------------------------------------------------------------


def test_app_does_not_use_add_frame_callback() -> None:
    """``dpg.add_frame_callback`` does not exist in dearpygui v2.3.1.

    A prior fixer reintroduced it twice, causing an ``AttributeError`` at
    GUI launch. This test reads ``app.py`` source and fails if the banned
    symbol appears outside of comments/docstrings, preventing regression.
    """
    import pathlib
    import ast

    app_path = (
        pathlib.Path(__file__).resolve().parent.parent / "app.py"
    )
    source = app_path.read_text()
    tree = ast.parse(source)

    banned = "add_frame_callback"
    offenders: list[str] = []

    for node in ast.walk(tree):
        # Detect: <x>.add_frame_callback(...)  (Attribute call)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == banned:
                offenders.append(f"line {node.lineno}: attribute call")
        # Detect: add_frame_callback(...)  (bare name call)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == banned:
                offenders.append(f"line {node.lineno}: bare name call")

    assert not offenders, (
        f"app.py uses the non-existent dpg.add_frame_callback API "
        f"(offenders: {offenders}). Use dpg.set_frame_callback(frame, callback=...) "
        f"with re-arming instead."
    )
