"""Compiler runner module for the C++ Pointer Lab.

Wraps ``g++`` so the rest of the lab can compile and run generated C++
snippets and read back the memory bytes and pointer data they print.

Public API
----------
- :class:`GppStatus`     — result of probing the local toolchain.
- :class:`RunResult`     — result of compiling + running one snippet.
- :func:`probe_gpp`      — detect ``g++``, verify C++20 support, probe ASan.
- :func:`compile_only`   — compile a source string without running it.
- :func:`compile_and_run` — compile a source string and run the binary.
- :func:`build_compile_command` — build the g++ command string for a source.
- :func:`parse_membytes` — extract the ``MEMBYTES:`` line from stdout.
- :func:`parse_ptrdata`  — extract the ``PTRDATA:`` line from stdout.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class GppStatus:
    """Outcome of probing the local ``g++`` toolchain."""

    status: str
    version: str
    message: str
    asan_available: bool = False


@dataclass
class RunResult:
    """Outcome of compiling and running a single C++ source string."""

    stdout: str
    stderr: str
    exit_code: int | None
    memory_bytes: str
    status: str
    command: str = ""
    compiler_stderr: str = ""
    ptrdata: dict | None = None


# ---------------------------------------------------------------------------
# MEMBYTES parsing
# ---------------------------------------------------------------------------

_MEMBYTES_RE = re.compile(r"^\s*MEMBYTES:\s*(.*)$", re.MULTILINE)


def parse_membytes(stdout: str) -> str:
    """Extract the hex bytes from a ``MEMBYTES:`` line in ``stdout``."""
    match = _MEMBYTES_RE.search(stdout)
    if not match:
        return "n/a"
    raw = match.group(1).strip()
    if not raw:
        return "n/a"
    return " ".join(raw.split())


# ---------------------------------------------------------------------------
# PTRDATA parsing
# ---------------------------------------------------------------------------

_PTRDATA_RE = re.compile(r"^\s*PTRDATA:\s*(.+)$", re.MULTILINE)


def parse_ptrdata(stdout: str) -> dict | None:
    """Extract key=value pairs from a ``PTRDATA:`` line in ``stdout``.

    Returns a dict of str→str, or ``None`` if no ``PTRDATA:`` line is found.
    """
    match = _PTRDATA_RE.search(stdout)
    if not match:
        return None
    line = match.group(1).strip()
    result = {}
    for token in line.split():
        if "=" in token:
            key, _, value = token.partition("=")
            result[key] = value
    return result if result else None


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
    """Detect ``g++``, verify C++20 support, and probe ASan availability."""
    if shutil.which("g++") is None:
        return GppStatus(
            status="missing",
            version="",
            message=(
                "g++ was not found on your PATH. Install a C++ compiler "
                "(e.g. Xcode Command Line Tools on macOS, or build-essential "
                "on Debian/Ubuntu)."
            ),
            asan_available=False,
        )

    try:
        ver_proc = _run(["g++", "--version"], timeout=5.0)
        version_str = ver_proc.stdout.splitlines()[0].strip() if ver_proc.stdout else ""
    except (subprocess.TimeoutExpired, OSError):
        version_str = ""

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
                asan_available=False,
            )
        if proc.returncode != 0:
            return GppStatus(
                status="too-old",
                version=version_str,
                message=(
                    "g++ is installed but does not support -std=c++20. "
                    "Install a newer compiler (GCC >= 11 or a recent clang)."
                ),
                asan_available=False,
            )

        # Probe ASan availability.
        asan_src = os.path.join(tmpdir, "asan_probe.cpp")
        asan_exe = os.path.join(tmpdir, "asan_probe")
        with open(asan_src, "w") as f:
            f.write("int main() { return 0; }\n")
        try:
            asan_proc = _run(
                ["g++", "-std=c++20", "-fsanitize=address", asan_src, "-o", asan_exe],
                timeout=10.0,
            )
            asan_available = asan_proc.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            asan_available = False

        return GppStatus(
            status="available",
            version=version_str,
            message="g++ is available and supports -std=c++20.",
            asan_available=asan_available,
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
    """Run ``cmd`` capturing output as text, with optional cancellation."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + timeout
    try:
        while True:
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
                out, err = proc.communicate(timeout=2.0)
                raise subprocess.TimeoutExpired(
                    cmd=cmd, timeout=timeout, output=out, stderr=err
                )
        out, err = proc.communicate()
        return subprocess.CompletedProcess(
            args=cmd, returncode=proc.returncode, stdout=out, stderr=err
        )
    except BaseException:
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
    extra_flags: list[str] | None = None,
) -> tuple[str, subprocess.CompletedProcess[str] | None, str, str]:
    """Shared compile step used by :func:`compile_only` and :func:`compile_and_run`."""
    flags = extra_flags or []
    compile_cmd = ["g++", "-std=c++20"] + flags + [src_path, "-o", exe_path]
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
    extra_flags: list[str] | None = None,
) -> RunResult:
    """Compile ``source`` with ``g++ -std=c++20`` but do NOT run the binary."""
    tmpdir = tempfile.mkdtemp(prefix="cpp_lab_")
    try:
        src_path = os.path.join(tmpdir, "snippet.cpp")
        exe_path = os.path.join(tmpdir, "snippet")
        with open(src_path, "w") as f:
            f.write(source)

        cmd_str, compile_proc, status, compiler_stderr = _compile(
            src_path, exe_path, timeout, cancel_event, extra_flags
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


def build_compile_command(
    source: str,
    extra_flags: list[str] | None = None,
) -> str:
    """Return the g++ command string that would compile ``source``."""
    flags = extra_flags or []
    tmpdir = tempfile.mkdtemp(prefix="cpp_lab_")
    try:
        src_path = os.path.join(tmpdir, "snippet.cpp")
        exe_path = os.path.join(tmpdir, "snippet")
        with open(src_path, "w") as f:
            f.write(source)
        compile_cmd = ["g++", "-std=c++20"] + flags + [src_path, "-o", exe_path]
        return " ".join(compile_cmd)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def compile_and_run(
    source: str,
    timeout: float = 5.0,
    cancel_event: threading.Event | None = None,
    extra_flags: list[str] | None = None,
) -> RunResult:
    """Compile ``source`` with ``g++ -std=c++20`` and run the resulting binary."""
    tmpdir = tempfile.mkdtemp(prefix="cpp_lab_")
    try:
        src_path = os.path.join(tmpdir, "snippet.cpp")
        exe_path = os.path.join(tmpdir, "snippet")
        with open(src_path, "w") as f:
            f.write(source)

        compile_cmd_str, compile_proc, compile_status, compiler_stderr = _compile(
            src_path, exe_path, timeout, cancel_event, extra_flags
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
            return RunResult(
                stdout="",
                stderr=str(exc),
                exit_code=None,
                memory_bytes="n/a",
                status="execution-error",
                command=compile_cmd_str,
                compiler_stderr=compiler_stderr,
            )

        ptrdata = parse_ptrdata(run_proc.stdout)

        if run_proc.returncode != 0:
            return RunResult(
                stdout=run_proc.stdout,
                stderr=run_proc.stderr,
                exit_code=run_proc.returncode,
                memory_bytes=parse_membytes(run_proc.stdout),
                status="execution-error",
                command=compile_cmd_str,
                compiler_stderr=compiler_stderr,
                ptrdata=ptrdata,
            )

        return RunResult(
            stdout=run_proc.stdout,
            stderr=run_proc.stderr,
            exit_code=run_proc.returncode,
            memory_bytes=parse_membytes(run_proc.stdout),
            status="success",
            command=compile_cmd_str,
            compiler_stderr=compiler_stderr,
            ptrdata=ptrdata,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
