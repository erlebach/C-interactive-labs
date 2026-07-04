"""Tests for cpp_labs.compiler_runner."""
import pytest
from cpp_labs.compiler_runner import RunResult, build_compile_command, parse_ptrdata


def test_parse_ptrdata_raw():
    stdout = "PTRDATA: type=raw ptr_addr=0x7fff10 target_addr=0x7fff04 target_val=42\n"
    result = parse_ptrdata(stdout)
    assert result is not None
    assert result["type"] == "raw"
    assert result["ptr_addr"] == "0x7fff10"
    assert result["target_addr"] == "0x7fff04"
    assert result["target_val"] == "42"


def test_parse_ptrdata_null():
    stdout = "PTRDATA: type=null ptr_addr=0x0\n"
    result = parse_ptrdata(stdout)
    assert result is not None
    assert result["type"] == "null"
    assert result["ptr_addr"] == "0x0"


def test_parse_ptrdata_ref():
    stdout = "PTRDATA: type=ref ref_addr=0x7fff10 target_addr=0x7fff04 target_val=42\n"
    result = parse_ptrdata(stdout)
    assert result is not None
    assert result["type"] == "ref"
    assert result["ref_addr"] == "0x7fff10"
    assert result["target_addr"] == "0x7fff04"
    assert result["target_val"] == "42"


def test_parse_ptrdata_unique():
    stdout = "PTRDATA: type=unique ptr_addr=0x7fff10 target_addr=0x12340 val=42 is_null=0\n"
    result = parse_ptrdata(stdout)
    assert result is not None
    assert result["type"] == "unique"
    assert result["val"] == "42"
    assert result["is_null"] == "0"


def test_parse_ptrdata_shared():
    stdout = "PTRDATA: type=shared ptr_addr=0x7fff10 target_addr=0x12340 val=99 use_count=2\n"
    result = parse_ptrdata(stdout)
    assert result is not None
    assert result["type"] == "shared"
    assert result["use_count"] == "2"
    assert result["val"] == "99"


def test_parse_ptrdata_weak():
    stdout = "PTRDATA: type=weak ptr_addr=0x7fff10 expired=0 use_count=1\n"
    result = parse_ptrdata(stdout)
    assert result is not None
    assert result["type"] == "weak"
    assert result["expired"] == "0"
    assert result["use_count"] == "1"


def test_parse_ptrdata_none_when_absent():
    result = parse_ptrdata("no ptrdata here\n")
    assert result is None


def test_parse_ptrdata_empty_string():
    result = parse_ptrdata("")
    assert result is None


def test_run_result_ptrdata_default():
    r = RunResult(
        stdout="",
        stderr="",
        exit_code=0,
        memory_bytes="n/a",
        status="success",
    )
    assert r.ptrdata is None


def test_build_compile_command_includes_extra_flags():
    source = "int main() {}\n"
    cmd = build_compile_command(source, extra_flags=["-fsanitize=address"])
    assert "-fsanitize=address" in cmd


def test_build_compile_command_no_extra_flags():
    source = "int main() {}\n"
    cmd = build_compile_command(source)
    assert "g++" in cmd
    assert "-std=c++20" in cmd
