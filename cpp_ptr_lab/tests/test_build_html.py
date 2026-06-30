"""Tests for cpp_ptr_lab.build_html (RED phase — all will fail until implemented)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from unittest import mock

import pytest

from cpp_ptr_lab.build_html import build_lab, capture_variant, expand_variants
from cpp_ptr_lab.code_generator import CaseDef, ControlDef, TopicTemplate, generate_source


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_topic(tid: str = "basic_ptr", controls=None, **kwargs) -> TopicTemplate:
    defaults = dict(
        id=tid,
        name="Test",
        template="#include<iostream>\nint main(){}",
        controls=controls or [],
        explanation="",
        group="Core",
        target_var="x",
    )
    defaults.update(kwargs)
    return TopicTemplate(**defaults)


def _dropdown(cid: str, options: list[str], default: str | None = None) -> ControlDef:
    return ControlDef(
        id=cid,
        label=cid.title(),
        kind="dropdown",
        options=options,
        default=default or options[0],
        placeholder=f"<<{cid}>>",
    )


def _text_ctrl(cid: str, default: str = "42") -> ControlDef:
    return ControlDef(
        id=cid,
        label=cid.title(),
        kind="text",
        default=default,
        placeholder=f"<<{cid}>>",
    )


# ---------------------------------------------------------------------------
# expand_variants
# ---------------------------------------------------------------------------


class TestExpandVariants:
    def test_no_controls_yields_one_variant(self):
        topic = _make_topic(controls=[])
        vs = expand_variants(topic)
        assert len(vs) == 1

    def test_dropdown_yields_one_per_option(self):
        topic = _make_topic(controls=[_dropdown("type", ["int", "double", "float"])])
        vs = expand_variants(topic)
        assert len(vs) == 3

    def test_free_text_control_uses_default(self):
        topic = _make_topic(controls=[
            _dropdown("type", ["int", "double"]),
            _text_ctrl("value", "99"),
        ])
        vs = expand_variants(topic)
        assert all(v["value"] == "99" for v in vs)

    def test_free_text_not_multiplied(self):
        topic = _make_topic(controls=[
            _dropdown("type", ["int", "double"]),
            _text_ctrl("value", "42"),
            _text_ctrl("extra", "0"),
        ])
        vs = expand_variants(topic)
        assert len(vs) == 2  # only from the dropdown, not 2×∞

    def test_checkbox_default_false_resolves_via_value_map(self):
        # A checkbox with default=False must seed a value the resolver maps
        # through its lowercase value_map ("false"), NOT the stringified bool
        # "False" — which would land as a bare `False` statement in the C++.
        checkbox = ControlDef(
            id="mutate", label="Mutate", kind="checkbox", default=False,
            placeholder="<<mutate>>",
            value_map={"false": "// no mutation", "true": "*ptr = 99;"},
        )
        topic = _make_topic(
            controls=[_dropdown("type", ["int", "double"]), checkbox],
            template="int main(){ <<mutate>> }",
        )
        for cs in expand_variants(topic):
            src = generate_source(topic, cs)
            assert "False" not in src, f"bare bool leaked: {src!r}"
            assert "// no mutation" in src


# ---------------------------------------------------------------------------
# capture_variant — mocked g++
# ---------------------------------------------------------------------------


_FAKE_STDOUT = (
    "PTRDATA: type=raw ptr_addr=0xabc target_addr=0xdef target_val=42\n"
    "MEMBYTES: c8 9a 94 6b 01 00 00 00\n"
    "ptr  (int*) = 0xabc\n"
)

_FAKE_RESULT_OK = mock.MagicMock()
_FAKE_RESULT_OK.status = "success"
_FAKE_RESULT_OK.stdout = _FAKE_STDOUT
_FAKE_RESULT_OK.stderr = ""
_FAKE_RESULT_OK.compiler_stderr = ""
_FAKE_RESULT_OK.memory_bytes = "c8 9a 94 6b 01 00 00 00"
_FAKE_RESULT_OK.ptrdata = {
    "type": "raw",
    "ptr_addr": "0xabc",
    "target_addr": "0xdef",
    "target_val": "42",
}

_FAKE_RESULT_FAIL = mock.MagicMock()
_FAKE_RESULT_FAIL.status = "compile-failed"
_FAKE_RESULT_FAIL.stdout = ""
_FAKE_RESULT_FAIL.stderr = ""
_FAKE_RESULT_FAIL.compiler_stderr = "error: 'r' declared as reference but not initialized"
_FAKE_RESULT_FAIL.memory_bytes = "n/a"
_FAKE_RESULT_FAIL.ptrdata = None


class TestCaptureVariantSuccess:
    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_returns_dict(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert isinstance(result, dict)

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_failed_is_false(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert result["failed"] is False

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_stdout_captured(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert _FAKE_STDOUT in result["stdout"] or result["stdout"] == _FAKE_STDOUT

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_membytes_captured(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert result["membytes"] == "c8 9a 94 6b 01 00 00 00"

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_svg_present(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert "<svg" in result["svg"]

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_source_present(self, mock_run):
        topic = _make_topic(template="int main(){}")
        result = capture_variant(topic, {})
        assert result["source"]


class TestCaptureVariantCases:
    def _topic(self):
        return _make_topic(
            template="int main(){ <<op>> <<HARNESS>> }",
            cases=[
                CaseDef("Write *ptr", {"<<op>>": "*ptr = 99;"}),
                CaseDef("Rebind ptr", {"<<op>>": "ptr = &other;"}),
            ],
        )

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_variant_has_cases_list(self, mock_run):
        v = capture_variant(self._topic(), {})
        assert isinstance(v.get("cases"), list)
        assert len(v["cases"]) == 2

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_each_case_has_label_and_result_keys(self, mock_run):
        v = capture_variant(self._topic(), {})
        assert [c["label"] for c in v["cases"]] == ["Write *ptr", "Rebind ptr"]
        for c in v["cases"]:
            assert "source" in c and "failed" in c and "svg" in c

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_each_case_source_reflects_its_subs(self, mock_run):
        v = capture_variant(self._topic(), {})
        assert "*ptr = 99;" in v["cases"][0]["source"]
        assert "ptr = &other;" in v["cases"][1]["source"]

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_no_cases_key_when_topic_has_none(self, mock_run):
        v = capture_variant(_make_topic(), {})
        assert "cases" not in v


class TestCaptureVariantFailure:
    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_FAIL)
    def test_failed_is_true(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert result["failed"] is True

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_FAIL)
    def test_stderr_captured(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert result["stderr"]

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_FAIL)
    def test_stdout_empty(self, mock_run):
        topic = _make_topic()
        result = capture_variant(topic, {})
        assert result["stdout"] == ""


# ---------------------------------------------------------------------------
# build_lab — file emission
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dist(tmp_path):
    return tmp_path / "dist"


class TestBuildLabOutputFiles:
    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_per_topic_file_written(self, mock_run, tmp_dist):
        topic = _make_topic("tp1", controls=[])
        build_lab("testlab", [topic], tmp_dist)
        assert (tmp_dist / "topics" / "tp1.html").exists()

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_per_lab_file_written(self, mock_run, tmp_dist):
        topic = _make_topic("tp1", controls=[])
        build_lab("testlab", [topic], tmp_dist)
        assert (tmp_dist / "lab_testlab.html").exists()

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_multiple_topics_all_written(self, mock_run, tmp_dist):
        topics = [_make_topic(f"t{i}", controls=[]) for i in range(3)]
        build_lab("lab", topics, tmp_dist)
        for i in range(3):
            assert (tmp_dist / "topics" / f"t{i}.html").exists()

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_combined_contains_all_topics(self, mock_run, tmp_dist):
        topics = [_make_topic(f"t{i}", controls=[]) for i in range(3)]
        build_lab("lab", topics, tmp_dist)
        combined = (tmp_dist / "lab_lab.html").read_text()
        for i in range(3):
            assert f"t{i}" in combined

    @mock.patch("cpp_ptr_lab.build_html.compile_and_run", return_value=_FAKE_RESULT_OK)
    def test_per_topic_files_are_self_contained(self, mock_run, tmp_dist):
        topic = _make_topic("tp1", controls=[])
        build_lab("lab", [topic], tmp_dist)
        html = (tmp_dist / "topics" / "tp1.html").read_text()
        assert "<html" in html
        assert "<style" in html


# ---------------------------------------------------------------------------
# build_lab — missing g++ fails loudly
# ---------------------------------------------------------------------------


class TestBuildLabMissingGpp:
    def test_raises_when_gpp_missing(self, tmp_dist):
        with mock.patch("shutil.which", return_value=None):
            with pytest.raises((RuntimeError, SystemExit)):
                build_lab("lab", [_make_topic()], tmp_dist)
