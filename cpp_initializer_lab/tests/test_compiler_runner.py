"""Unit tests for :mod:`cpp_initializer_lab.compiler_runner`.

Run with::

    python -m pytest cpp_initializer_lab/tests/test_compiler_runner.py -v
"""

from __future__ import annotations

import shutil

import pytest

from cpp_initializer_lab.compiler_runner import (
    GppStatus,
    RunResult,
    build_compile_command,
    compile_and_run,
    compile_only,
    parse_membytes,
    probe_gpp,
)

# Skip the g++-dependent tests entirely if no compiler is available on this
# machine (e.g. CI without a toolchain). The pure-Python parser tests still run.
GPP_AVAILABLE = shutil.which("g++") is not None
gpp_required = pytest.mark.skipif(
    not GPP_AVAILABLE, reason="g++ not available on this machine"
)


# ---------------------------------------------------------------------------
# parse_membytes — pure function, always runs
# ---------------------------------------------------------------------------


class TestParseMembytes:
    def test_simple_line(self) -> None:
        stdout = "hello\nMEMBYTES: 41 42 43 44\nworld\n"
        assert parse_membytes(stdout) == "41 42 43 44"

    def test_no_line(self) -> None:
        assert parse_membytes("just some output\nno membytes here") == "n/a"

    def test_empty_bytes(self) -> None:
        # MEMBYTES: with nothing after it -> treat as n/a
        assert parse_membytes("MEMBYTES:\n") == "n/a"

    def test_leading_whitespace_and_extra_spaces(self) -> None:
        stdout = "   MEMBYTES:    00   01  02  03  \n"
        assert parse_membytes(stdout) == "00 01 02 03"

    def test_only_line(self) -> None:
        assert parse_membytes("MEMBYTES: 41 42 43 44") == "41 42 43 44"

    def test_single_byte(self) -> None:
        assert parse_membytes("MEMBYTES: 05") == "05"

    def test_case_sensitive_label(self) -> None:
        # The label is case-sensitive; "membytes:" should NOT match.
        assert parse_membytes("membytes: 41 42") == "n/a"

    def test_empty_stdout(self) -> None:
        assert parse_membytes("") == "n/a"


# ---------------------------------------------------------------------------
# probe_gpp — requires g++
# ---------------------------------------------------------------------------


@gpp_required
class TestProbeGpp:
    def test_returns_dataclass(self) -> None:
        status = probe_gpp()
        assert isinstance(status, GppStatus)
        assert status.status in {"available", "missing", "too-old"}

    def test_available_on_dev_machine(self) -> None:
        # On the dev machine (macOS with Xcode CLT) g++ should be available
        # and support C++20.
        status = probe_gpp()
        assert status.status == "available"
        assert status.version  # non-empty
        assert status.message


# ---------------------------------------------------------------------------
# compile_and_run — requires g++
# ---------------------------------------------------------------------------


@gpp_required
class TestCompileAndRun:
    def test_compile_success(self) -> None:
        result = compile_and_run("int main() { return 0; }")
        assert isinstance(result, RunResult)
        assert result.status == "success"
        assert result.exit_code == 0
        assert result.memory_bytes == "n/a"
        # New fields: command populated, compiler_stderr is a string (often
        # empty for a clean compile but may contain warnings).
        assert result.command
        assert "g++" in result.command
        assert "-std=c++20" in result.command
        assert isinstance(result.compiler_stderr, str)

    def test_compile_failure(self) -> None:
        # Invalid C++ — g++ should reject it.
        result = compile_and_run("int main() { syntax error }")
        assert result.status == "compile-failed"
        assert result.exit_code != 0
        # Compiler diagnostics now live in compiler_stderr (stderr is the
        # *program's* runtime stderr, empty on compile failure).
        assert result.compiler_stderr  # compiler diagnostics
        assert result.stderr == ""
        assert result.stdout == ""
        assert result.memory_bytes == "n/a"
        # The command string should be populated on a compile attempt.
        assert result.command
        assert "g++" in result.command
        assert "-std=c++20" in result.command

    def test_membytes_parsing_from_program(self) -> None:
        source = (
            "#include <cstdio>\n"
            "int main() {\n"
            '    std::printf("MEMBYTES: 41 42 43 44\\n");\n'
            "    return 0;\n"
            "}\n"
        )
        result = compile_and_run(source)
        assert result.status == "success"
        assert result.memory_bytes == "41 42 43 44"

    def test_stdout_captured(self) -> None:
        source = (
            "#include <cstdio>\n"
            "int main() {\n"
            '    std::printf("hello world\\n");\n'
            "    return 0;\n"
            "}\n"
        )
        result = compile_and_run(source)
        assert result.status == "success"
        assert "hello world" in result.stdout


# ---------------------------------------------------------------------------
# Cancellation — requires g++
# ---------------------------------------------------------------------------


@gpp_required
class TestCancellation:
    def test_cancel_event_aborts_run(self) -> None:
        """A pre-set cancel_event should yield status='cancelled' promptly."""
        import threading

        cancel = threading.Event()
        cancel.set()  # already cancelled before we start
        result = compile_and_run(
            "int main() { return 0; }", cancel_event=cancel
        )
        assert result.status == "cancelled"
        assert result.exit_code is None
        assert result.memory_bytes == "n/a"
        # The command string is still recorded (compile was attempted).
        assert result.command

    def test_cancel_event_during_long_run(self) -> None:
        """Cancelling mid-run of a sleeping program returns 'cancelled'."""
        import threading
        import time

        cancel = threading.Event()
        # A program that sleeps long enough to be cancelled mid-flight.
        source = (
            "#include <chrono>\n"
            "#include <thread>\n"
            "int main() {\n"
            "    std::this_thread::sleep_for(std::chrono::seconds(30));\n"
            "    return 0;\n"
            "}\n"
        )

        result_holder: dict = {}

        def worker() -> None:
            result_holder["result"] = compile_and_run(
                source, timeout=60.0, cancel_event=cancel
            )

        t = threading.Thread(target=worker)
        t.start()
        # Give the compile step time to finish and the run to start.
        time.sleep(1.0)
        cancel.set()
        t.join(timeout=10.0)
        assert not t.is_alive(), "worker thread did not finish after cancel"
        result = result_holder["result"]
        assert result.status == "cancelled"
        assert result.exit_code is None


# ---------------------------------------------------------------------------
# compile_only — requires g++
# ---------------------------------------------------------------------------


@gpp_required
class TestCompileOnly:
    def test_compile_only_success(self) -> None:
        """A valid program compiles with status='compile-ok' and no run."""
        result = compile_only("int main() { return 0; }")
        assert isinstance(result, RunResult)
        assert result.status == "compile-ok"
        assert result.exit_code == 0
        # No program was run, so stdout/stderr are empty.
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.memory_bytes == "n/a"
        # Command string is populated.
        assert result.command
        assert "g++" in result.command
        assert "-std=c++20" in result.command
        # compiler_stderr is a string (often empty for a clean compile).
        assert isinstance(result.compiler_stderr, str)

    def test_compile_only_failure(self) -> None:
        """An invalid program yields status='compile-failed' with diagnostics."""
        result = compile_only("int main() { syntax error }")
        assert result.status == "compile-failed"
        assert result.exit_code != 0
        # Diagnostics live in compiler_stderr; program stderr is empty.
        assert result.compiler_stderr  # non-empty diagnostics
        assert result.stderr == ""
        assert result.stdout == ""
        assert result.memory_bytes == "n/a"
        assert result.command
        assert "g++" in result.command

    def test_compile_only_does_not_execute(self) -> None:
        """compile_only must NOT run the binary — a program that would print
        to stdout must produce empty stdout."""
        source = (
            "#include <cstdio>\n"
            "int main() {\n"
            '    std::printf("THIS SHOULD NOT RUN\\n");\n'
            "    return 0;\n"
            "}\n"
        )
        result = compile_only(source)
        assert result.status == "compile-ok"
        assert result.stdout == ""  # binary was never executed


# ---------------------------------------------------------------------------
# build_compile_command — pure function, always runs
# ---------------------------------------------------------------------------


class TestBuildCompileCommand:
    def test_returns_string_with_gpp_and_std(self) -> None:
        cmd = build_compile_command("int main() {}")
        assert isinstance(cmd, str)
        assert "g++" in cmd
        assert "-std=c++20" in cmd

    def test_contains_real_temp_paths(self) -> None:
        """The command should reference real-looking temp file paths."""
        cmd = build_compile_command("int main() {}")
        # The source and exe paths should appear in the string.
        assert ".cpp" in cmd
        # On macOS temp dirs live under /var or /tmp; on Linux /tmp. Just
        # assert there's a path-like component.
        assert "/" in cmd

    def test_does_not_invoke_gpp(self) -> None:
        """build_compile_command must not actually run g++ — it should work
        even if g++ is missing (we can't easily remove g++ from PATH, but we
        can at least confirm it returns quickly and is a pure string build)."""
        cmd = build_compile_command("int main() {}")
        # The returned string is just a string, not a CompletedProcess.
        assert not hasattr(cmd, "returncode")
