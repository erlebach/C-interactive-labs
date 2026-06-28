"""Compiler runner module.

Wraps ``g++`` so the rest of the lab can compile and run generated C++
snippets and read back the memory bytes they print.

Public API
----------
- :class:`GppStatus`  — result of probing the local toolchain.
- :class:`RunResult`  — result of compiling + running one snippet.
- :func:`probe_gpp`   — detect ``g++`` and verify C++20 support.
- :func:`compile_only` — compile a source string without running it.
- :func:`compile_and_run` — compile a source string and run the binary.
- :func:`build_compile_command` — build the g++ command string for a source.
- :func:`parse_membytes` — extract the ``MEMBYTES:`` line from stdout.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class GppStatus:
    """Outcome of probing the local ``g++`` toolchain.

    Fields
    ------
    status:
        One of ``"available"``, ``"missing"``, ``"too-old"``.
    version:
        The first line of ``g++ --version`` (empty if g++ is missing).
    message:
        Human-readable explanation suitable for showing in the GUI.
    """

    status: str
    version: str
    message: str


@dataclass
class RunResult:
    """Outcome of compiling and running a single C++ source string.

    Fields
    ------
    stdout:
        Captured program stdout (empty on compile failure).
    stderr:
        Captured program stderr (runtime). On compile failure this is
        empty — use ``compiler_stderr`` for compiler diagnostics.
    exit_code:
        The program's exit code, or ``None`` if it never ran / timed out.
    memory_bytes:
        Space-separated hex bytes parsed from a ``MEMBYTES:`` line, or
        ``"n/a"`` if no such line was printed.
    status:
        One of ``"success"``, ``"compile-ok"``, ``"compile-failed"``,
        ``"execution-timeout"``, ``"execution-error"``, ``"cancelled"``.
        ``"compile-ok"`` is only produced by :func:`compile_only` (compile
        succeeded but the binary was not executed).
    command:
        The ``g++`` compile command string that was invoked (e.g.
        ``"g++ -std=c++20 /tmp/.../snippet.cpp -o /tmp/.../snippet"``).
        Empty if compilation was never attempted (e.g. cancelled before
        the compile step started).
    compiler_stderr:
        g++'s own stderr output (warnings/errors). On compile failure this
        holds the diagnostics; on success it holds any warnings (often
        empty). Kept separate from the *program's* runtime ``stderr``.
    """

    stdout: str
    stderr: str
    exit_code: int | None
    memory_bytes: str
    status: str
    command: str = ""
    compiler_stderr: str = ""


# ---------------------------------------------------------------------------
# MEMBYTES parsing
# ---------------------------------------------------------------------------

# Matches a line like:   MEMBYTES: 41 42 43 44
# Captures everything after the colon (trimmed).
_MEMBYTES_RE = re.compile(r"^\s*MEMBYTES:\s*(.*)$", re.MULTILINE)


def parse_membytes(stdout: str) -> str:
    """Extract the hex bytes from a ``MEMBYTES:`` line in ``stdout``.

    The generated C++ prints a line of the form::

        MEMBYTES: 41 42 43 44

    This function returns the trailing ``"41 42 43 44"`` portion (already
    whitespace-collapsed and stripped). If no ``MEMBYTES:`` line is present,
    returns ``"n/a"``.

    Parameters
    ----------
    stdout:
        The full captured stdout of the compiled program.

    Returns
    -------
    str
        Space-separated hex bytes, or ``"n/a"``.
    """
    match = _MEMBYTES_RE.search(stdout)
    if not match:
        return "n/a"
    raw = match.group(1).strip()
    if not raw:
        return "n/a"
    # Collapse internal whitespace runs to single spaces for a clean output.
    return " ".join(raw.split())


# ---------------------------------------------------------------------------
# g++ probe
# ---------------------------------------------------------------------------


def _run(cmd: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    """Run ``cmd`` capturing output as text. Raises on timeout."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def probe_gpp() -> GppStatus:
    """Detect ``g++`` and verify it accepts ``-std=c++20``.

    Returns
    -------
    GppStatus
        ``status="available"`` if g++ exists and compiles a trivial
        ``int main(){}`` with ``-std=c++20``; ``"missing"`` if g++ is not on
        PATH; ``"too-old"`` if g++ exists but rejects ``-std=c++20``.
    """
    # 1. Does g++ exist at all?
    if shutil.which("g++") is None:
        return GppStatus(
            status="missing",
            version="",
            message=(
                "g++ was not found on your PATH. Install a C++ compiler "
                "(e.g. Xcode Command Line Tools on macOS, or build-essential "
                "on Debian/Ubuntu)."
            ),
        )

    # Grab a version string for reporting.
    try:
        ver_proc = _run(["g++", "--version"], timeout=5.0)
        version_str = ver_proc.stdout.splitlines()[0].strip() if ver_proc.stdout else ""
    except (subprocess.TimeoutExpired, OSError):
        version_str = ""

    # 2. Does it accept -std=c++20? Compile a trivial snippet in a temp dir.
    tmpdir = tempfile.mkdtemp(prefix="gpp_probe_")
    try:
        src_path = os.path.join(tmpdir, "probe.cpp")
        exe_path = os.path.join(tmpdir, "probe")
        with open(src_path, "w") as f:
            f.write("int main() {}\n")
        try:
            proc = _run(
                ["g++", "-std=c++20", src_path, "-o", exe_path],
                timeout=10.0,
            )
        except subprocess.TimeoutExpired:
            return GppStatus(
                status="too-old",
                version=version_str,
                message="g++ did not respond in time while testing -std=c++20.",
            )
        if proc.returncode != 0:
            return GppStatus(
                status="too-old",
                version=version_str,
                message=(
                    "g++ is installed but does not support -std=c++20. "
                    "Install a newer compiler (GCC >= 11 or a recent clang)."
                ),
            )
        return GppStatus(
            status="available",
            version=version_str,
            message="g++ is available and supports -std=c++20.",
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Compile + run
# ---------------------------------------------------------------------------


class _Cancelled(Exception):
    """Internal sentinel raised by ``_run_cancellable`` when cancelled."""


def _run_cancellable(
    cmd: list[str],
    timeout: float = 5.0,
    cancel_event: threading.Event | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``cmd`` capturing output as text, with optional cancellation.

    If ``cancel_event`` is provided and becomes set while the subprocess is
    running, the subprocess is killed and :class:`_Cancelled` is raised.

    Raises
    ------
    subprocess.TimeoutExpired
        If the process does not finish within ``timeout`` seconds.
    _Cancelled
        If ``cancel_event`` was set during the run.
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + timeout
    try:
        while True:
            # Poll for completion with a short timeout so we can also check
            # the cancel event regularly.
            try:
                proc.wait(timeout=0.05)
                break
            except subprocess.TimeoutExpired:
                pass
            if cancel_event is not None and cancel_event.is_set():
                proc.kill()
                proc.wait(timeout=2.0)
                raise _Cancelled()
            if time.monotonic() >= deadline:
                proc.kill()
                # Reap and raise TimeoutExpired with captured output.
                out, err = proc.communicate(timeout=2.0)
                raise subprocess.TimeoutExpired(
                    cmd=cmd, timeout=timeout, output=out, stderr=err
                )
        out, err = proc.communicate()
        return subprocess.CompletedProcess(
            args=cmd, returncode=proc.returncode, stdout=out, stderr=err
        )
    except BaseException:
        # Ensure the process is reaped on any exit path.
        if proc.poll() is None:
            proc.kill()
            try:
                proc.communicate(timeout=2.0)
            except subprocess.TimeoutExpired:
                pass
        raise


def _compile(
    src_path: str,
    exe_path: str,
    timeout: float,
    cancel_event: threading.Event | None,
) -> tuple[str, subprocess.CompletedProcess[str] | None, str, str]:
    """Shared compile step used by :func:`compile_only` and :func:`compile_and_run`.

    Parameters
    ----------
    src_path:
        Path to the ``.cpp`` file already written to disk.
    exe_path:
        Path for the output executable.
    timeout:
        Seconds to allow for the compile step.
    cancel_event:
        Optional cancellation event.

    Returns
    -------
    tuple of ``(compile_cmd_str, compile_proc_or_None, status_str, compiler_stderr)``
        ``compile_proc`` is ``None`` and ``status_str`` is ``"cancelled"`` or
        ``"compile-failed"`` (timeout) when the compile step did not complete
        normally; otherwise ``compile_proc`` is the
        :class:`subprocess.CompletedProcess` and ``status_str`` is
        ``"compile-ok"`` or ``"compile-failed"`` based on the return code.
    """
    compile_cmd = ["g++", "-std=c++20", src_path, "-o", exe_path]
    compile_cmd_str = " ".join(compile_cmd)
    try:
        compile_proc = _run_cancellable(
            compile_cmd, timeout=timeout, cancel_event=cancel_event
        )
    except _Cancelled:
        return (compile_cmd_str, None, "cancelled", "")
    except subprocess.TimeoutExpired:
        return (compile_cmd_str, None, "compile-failed", "Compilation timed out.")

    if compile_proc.returncode != 0:
        return (
            compile_cmd_str,
            compile_proc,
            "compile-failed",
            compile_proc.stderr,
        )
    return (compile_cmd_str, compile_proc, "compile-ok", compile_proc.stderr)


def compile_only(
    source: str,
    timeout: float = 5.0,
    cancel_event: threading.Event | None = None,
) -> RunResult:
    """Compile ``source`` with ``g++ -std=c++20`` but do NOT run the binary.

    The source is written to a fresh temp directory, compiled, and the temp
    directory is removed afterwards (success or failure). The resulting
    executable (if any) is never executed.

    Parameters
    ----------
    source:
        Full C++ source text.
    timeout:
        Seconds to allow for the compile step.
    cancel_event:
        Optional :class:`threading.Event`. If set during compilation, the
        subprocess is killed and the function returns with
        ``status="cancelled"``.

    Returns
    -------
    RunResult
        ``status`` is ``"compile-ok"`` on success, ``"compile-failed"`` on
        compile error or timeout, or ``"cancelled"``. ``stdout`` and
        ``stderr`` are empty (no program was run); ``exit_code`` is the g++
        return code (or ``None`` on cancel/timeout); ``command`` holds the
        g++ command string; ``compiler_stderr`` holds g++'s diagnostics.
    """
    tmpdir = tempfile.mkdtemp(prefix="cpp_lab_")
    try:
        src_path = os.path.join(tmpdir, "snippet.cpp")
        exe_path = os.path.join(tmpdir, "snippet")
        with open(src_path, "w") as f:
            f.write(source)

        cmd_str, compile_proc, status, compiler_stderr = _compile(
            src_path, exe_path, timeout, cancel_event
        )
        exit_code = compile_proc.returncode if compile_proc is not None else None
        return RunResult(
            stdout="",
            stderr="",
            exit_code=exit_code,
            memory_bytes="n/a",
            status=status,
            command=cmd_str,
            compiler_stderr=compiler_stderr,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def build_compile_command(source: str) -> str:
    """Return the g++ command string that would compile ``source``.

    Writes ``source`` to a fresh temp directory, constructs the
    ``g++ -std=c++20 <src> -o <exe>`` command string using the real temp
    paths, removes the temp directory, and returns the command string. This
    lets the GUI show a realistic command (with real-looking paths) without
    actually invoking g++.
    """
    tmpdir = tempfile.mkdtemp(prefix="cpp_lab_")
    try:
        src_path = os.path.join(tmpdir, "snippet.cpp")
        exe_path = os.path.join(tmpdir, "snippet")
        with open(src_path, "w") as f:
            f.write(source)
        compile_cmd = ["g++", "-std=c++20", src_path, "-o", exe_path]
        return " ".join(compile_cmd)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def compile_and_run(
    source: str,
    timeout: float = 5.0,
    cancel_event: threading.Event | None = None,
) -> RunResult:
    """Compile ``source`` with ``g++ -std=c++20`` and run the resulting binary.

    The source is written to a fresh temp directory, compiled, executed, and
    the temp directory is removed afterwards (success or failure). Reuses
    :func:`_compile` for the compile step so behaviour stays consistent with
    :func:`compile_only`.

    Parameters
    ----------
    source:
        Full C++ source text.
    timeout:
        Seconds to allow for both the compile step and the execute step.
    cancel_event:
        Optional :class:`threading.Event`. If set while the compile or run
        subprocess is in flight, the subprocess is killed and the function
        returns promptly with ``status="cancelled"``. May be ``None`` to
        disable cancellation (the historical behaviour).

    Returns
    -------
    RunResult
        See :class:`RunResult` for field semantics.
    """
    tmpdir = tempfile.mkdtemp(prefix="cpp_lab_")
    try:
        src_path = os.path.join(tmpdir, "snippet.cpp")
        exe_path = os.path.join(tmpdir, "snippet")
        with open(src_path, "w") as f:
            f.write(source)

        # --- Compile (shared with compile_only) ---
        compile_cmd_str, compile_proc, compile_status, compiler_stderr = (
            _compile(src_path, exe_path, timeout, cancel_event)
        )

        if compile_status == "cancelled":
            return RunResult(
                stdout="",
                stderr="",
                exit_code=None,
                memory_bytes="n/a",
                status="cancelled",
                command=compile_cmd_str,
                compiler_stderr="",
            )
        if compile_status == "compile-failed":
            exit_code = compile_proc.returncode if compile_proc is not None else None
            return RunResult(
                stdout="",
                stderr="",
                exit_code=exit_code,
                memory_bytes="n/a",
                status="compile-failed",
                command=compile_cmd_str,
                compiler_stderr=compiler_stderr,
            )

        # --- Execute ---
        run_cmd = [exe_path]
        try:
            run_proc = _run_cancellable(
                run_cmd, timeout=timeout, cancel_event=cancel_event
            )
        except _Cancelled:
            return RunResult(
                stdout="",
                stderr="",
                exit_code=None,
                memory_bytes="n/a",
                status="cancelled",
                command=compile_cmd_str,
                compiler_stderr=compiler_stderr,
            )
        except subprocess.TimeoutExpired as exc:
            # Process was killed by subprocess. Use whatever partial output
            # was captured (TimeoutExpired.output / .stderr may be bytes).
            partial_stdout = ""
            if isinstance(exc.stdout, (bytes, bytearray)):
                partial_stdout = exc.stdout.decode("utf-8", errors="replace")
            elif isinstance(exc.stdout, str):
                partial_stdout = exc.stdout
            return RunResult(
                stdout=partial_stdout,
                stderr="",
                exit_code=None,
                memory_bytes="n/a",
                status="execution-timeout",
                command=compile_cmd_str,
                compiler_stderr=compiler_stderr,
            )
        except OSError as exc:
            # Binary exists but could not be executed (permissions, etc.).
            return RunResult(
                stdout="",
                stderr=str(exc),
                exit_code=None,
                memory_bytes="n/a",
                status="execution-error",
                command=compile_cmd_str,
                compiler_stderr=compiler_stderr,
            )

        if run_proc.returncode != 0:
            return RunResult(
                stdout=run_proc.stdout,
                stderr=run_proc.stderr,
                exit_code=run_proc.returncode,
                memory_bytes=parse_membytes(run_proc.stdout),
                status="execution-error",
                command=compile_cmd_str,
                compiler_stderr=compiler_stderr,
            )

        return RunResult(
            stdout=run_proc.stdout,
            stderr=run_proc.stderr,
            exit_code=run_proc.returncode,
            memory_bytes=parse_membytes(run_proc.stdout),
            status="success",
            command=compile_cmd_str,
            compiler_stderr=compiler_stderr,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
