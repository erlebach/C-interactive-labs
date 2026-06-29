"""Integration tests: compile and run each topic template with defaults."""
import pytest

from cpp_ptr_lab.compiler_runner import compile_and_run
from cpp_ptr_lab.code_generator import generate_source


# ---------------------------------------------------------------------------
# Lab 1 — Pointers & References
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def lab1_topics():
    from cpp_ptr_lab.pointers_refs.topics import TOPICS
    return {t.id: t for t in TOPICS}


def _run(topic):
    return compile_and_run(generate_source(topic, {}))


def test_lab1_basic_ptr(lab1_topics):
    result = _run(lab1_topics["basic_ptr"])
    assert "PTRDATA:" in result.stdout


def test_lab1_const_taxonomy_no_mutation(lab1_topics):
    result = _run(lab1_topics["const_taxonomy"])
    assert "PTRDATA:" in result.stdout


def test_lab1_const_taxonomy_mutation_const_int_ptr(lab1_topics):
    topic = lab1_topics["const_taxonomy"]
    state = {
        "variant": "const int* (value immutable, pointer mutable)",
        "mutate": True,
    }
    result = compile_and_run(generate_source(topic, state))
    assert result.status == "compile-failed"


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
    from cpp_ptr_lab.smart_ptrs.topics import TOPICS
    return {t.id: t for t in TOPICS}


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


def test_lab2_shared_copy(lab2_topics):
    result = _run(lab2_topics["shared_copy"])
    assert "use_count after copy: 2" in result.stdout


def test_lab2_weak_basics(lab2_topics):
    result = _run(lab2_topics["weak_basics"])
    assert "use_count with weak_ptr: 1" in result.stdout


def test_lab2_weak_expired(lab2_topics):
    result = _run(lab2_topics["weak_expired"])
    assert "expired: true" in result.stdout


def test_lab1_all_topics_have_doc_url():
    from cpp_ptr_lab.pointers_refs.topics import TOPICS
    for topic in TOPICS:
        assert topic.doc_url != "", f"Topic {topic.id!r} is missing doc_url"


def test_lab2_all_topics_have_doc_url():
    from cpp_ptr_lab.smart_ptrs.topics import TOPICS
    for topic in TOPICS:
        assert topic.doc_url != "", f"Topic {topic.id!r} is missing doc_url"
