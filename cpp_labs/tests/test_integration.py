"""Integration tests: compile and run each topic template with defaults."""
from pathlib import Path

import pytest

import cpp_labs
from cpp_labs.compiler_runner import compile_and_run
from cpp_labs.code_generator import generate_source
from cpp_labs.topic_yaml import load_topics

_ROOT = Path(cpp_labs.__file__).parent


def _subject_topics(name: str) -> list:
    """Load one subject's topics straight from its YAML (no ``topics.py`` shim)."""
    return list(load_topics(_ROOT / name / "topics").values())


# ---------------------------------------------------------------------------
# Lab 1 — Pointers & References
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def lab1_topics():
    return {t.id: t for t in _subject_topics("pointers_refs")}


def _run(topic):
    return compile_and_run(generate_source(topic, {}))


def test_lab1_basic_ptr(lab1_topics):
    result = _run(lab1_topics["basic_ptr"])
    assert "PTRDATA:" in result.stdout


def test_lab1_const_taxonomy_truth_table(lab1_topics):
    """const taxonomy is a 2x2: const-pointee blocks *ptr=…; const-pointer
    blocks ptr=…. Each of the 4 types compiles two sub-cases (write, rebind);
    the forbidden combinations must genuinely fail to compile."""
    from cpp_labs.build_html import capture_variant, expand_variants

    topic = lab1_topics["const_taxonomy"]
    variants = [capture_variant(topic, cs) for cs in expand_variants(topic)]
    assert len(variants) == 4
    for v in variants:
        assert len(v["cases"]) == 2  # write, rebind

    # case[0] = write *ptr, case[1] = rebind ptr  (CaseDef order)
    table = {v["label"]: (v["cases"][0]["failed"], v["cases"][1]["failed"])
             for v in variants}
    assert table["int* (pointer and value both mutable)"] == (False, False)
    assert table["const int* (value immutable, pointer mutable)"] == (True, False)
    assert table["int* const (pointer immutable, value mutable)"] == (False, True)
    assert table["const int* const (both immutable)"] == (True, True)


def test_lab1_ref_must_bind(lab1_topics):
    result = _run(lab1_topics["ref_must_bind"])
    assert result.status == "compile-failed"


def test_lab1_ref_no_null(lab1_topics):
    result = _run(lab1_topics["ref_no_null"])
    assert "PTRDATA:" in result.stdout


def test_lab1_ref_rebind_illusion(lab1_topics):
    result = _run(lab1_topics["ref_rebind_illusion"])
    assert "&r == &a: true" in result.stdout


def test_lab1_ref_const_no_modification(lab1_topics):
    result = _run(lab1_topics["ref_const"])
    assert "PTRDATA:" in result.stdout


def test_lab1_null_deref(lab1_topics):
    # Without ASan, null deref → crash or UB. Just verify it compiles.
    result = _run(lab1_topics["null_deref"])
    assert result.status in ("execution-error", "success")


def test_lab1_dangling_ptr(lab1_topics):
    result = _run(lab1_topics["dangling_ptr"])
    assert result.status != "compile-failed"


# Task 9.3 — explicit rebind illusion check
def test_ref_rebind_illusion_address_proof(lab1_topics):
    result = _run(lab1_topics["ref_rebind_illusion"])
    assert "&r == &a: true" in result.stdout


# ---------------------------------------------------------------------------
# Lab 2 — Smart Pointers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def lab2_topics():
    return {t.id: t for t in _subject_topics("smart_ptrs")}


def test_lab2_unique_basics(lab2_topics):
    result = _run(lab2_topics["unique_basics"])
    assert "PTRDATA:" in result.stdout


def test_lab2_unique_move(lab2_topics):
    result = _run(lab2_topics["unique_move"])
    assert "p is null after move: true" in result.stdout


def test_lab2_unique_copy_err(lab2_topics):
    result = _run(lab2_topics["unique_copy_err"])
    assert result.status == "compile-failed"


def test_lab2_shared_basics(lab2_topics):
    result = _run(lab2_topics["shared_basics"])
    assert "PTRDATA:" in result.stdout
    assert "(1 owner)" in result.stdout
    assert "(2 owners)" in result.stdout
    assert "0 owners" in result.stdout
    assert "expired:   true" in result.stdout


def test_lab2_shared_copy(lab2_topics):
    result = _run(lab2_topics["shared_copy"])
    assert "use_count after copy: 2" in result.stdout


def test_lab2_weak_basics(lab2_topics):
    result = _run(lab2_topics["weak_basics"])
    assert "use_count with weak_ptr: 1" in result.stdout


def test_lab2_weak_expired(lab2_topics):
    result = _run(lab2_topics["weak_expired"])
    assert "expired: true" in result.stdout


def test_lab2_weak_cycle_leaks(lab2_topics):
    result = _run(lab2_topics["weak_cycle"])  # default: shared_ptr cycle
    assert "a.use_count: 2" in result.stdout
    assert "A destroyed" not in result.stdout
    assert "B destroyed" not in result.stdout


def test_lab2_weak_cycle_fix(lab2_topics):
    topic = lab2_topics["weak_cycle"]
    result = compile_and_run(generate_source(topic, {"variant": "Fix (weak_ptr)"}))
    assert "a.use_count: 1" in result.stdout
    assert "A destroyed" in result.stdout
    assert "B destroyed" in result.stdout


def test_lab1_all_topics_have_doc_url():
    for topic in _subject_topics("pointers_refs"):
        assert topic.doc_url != "", f"Topic {topic.id!r} is missing doc_url"


def test_lab2_all_topics_have_doc_url():
    for topic in _subject_topics("smart_ptrs"):
        assert topic.doc_url != "", f"Topic {topic.id!r} is missing doc_url"
