"""Build integration for the Operator Overloading page.

One self-contained page: a ``Vec2`` with member / non-member operators shown as
independently-compiled stacked cases — four compile and print real output; the
last (``operator<<`` written as a member) is the classic mistake and genuinely
fails to compile. This is the first subject with NO memory-model diagram, so the
demo sets ``diagram: false``. Compiler-gated (bakes real g++ output).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from cpp_labs.yaml_engine import render_page as R

HAS_GPP = shutil.which("g++") is not None
LAYOUT = Path(__file__).parents[1] / "layouts" / "op_overload.rail.yaml"

pytestmark = pytest.mark.skipif(not HAS_GPP, reason="needs g++ to bake real output")


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    out = R.build_layout(LAYOUT, tmp_path_factory.mktemp("dist"))
    return out.read_text(encoding="utf-8")


def test_builds_and_is_self_contained(html):
    assert "<!DOCTYPE html>" in html
    assert "lang=" in html and "skip" in html.lower()
    # inline JS/CSS allowed; nothing external / networked
    assert not any(x in html for x in ['<script src', '<link', 'href="http', 'src="http'])


def test_no_memory_diagram(html):
    # operator overloading has no memory picture — diagram: false must be honored
    assert 'role="img"' not in html


def test_real_output_is_baked(html):
    assert "a + b = (4, 6)" in html      # operator+ (member)
    assert "2 * a = (2, 4)" in html      # operator* (non-member)
    assert "a == b: false" in html       # operator== (member)
    assert "a = (1, 2)" in html          # operator<< (non-member)


def test_examples_use_class_not_struct(html):
    # Locked course convention (project memory 2026-07-04): every example models
    # encapsulation with `class` (private by default), never `struct`.
    assert "class Vec2" in html
    assert "struct Vec2" not in html


def test_non_member_operators_use_friend(html):
    # With private members, the non-member operator<< must be declared a `friend`
    # to read them — the concept the class switch is meant to teach. (Assert the
    # specific declaration, not the bare word "friend" which the bundled
    # highlight.js keyword list would satisfy trivially.)
    assert "friend std::ostream" in html


def test_member_stream_gotcha_fails_to_compile(html):
    # the member-<< case must surface a real compiler-error box, not fake text
    assert "out--err" in html


def test_four_rail_entries_present(html):
    # demo = one nav entry: one left-rail item per operator
    for title in ["operator+  (member)", "operator*  (non-member)",
                  "operator==  (member)", "operator&lt;&lt;  (stream)"]:
        assert title in html


def test_stream_entry_pairs_correct_and_mistake(html):
    # the << entry stacks the correct friend non-member version + the member mistake
    assert "Correct: friend non-member operator&lt;&lt;" in html
    assert "Mistake: operator&lt;&lt; as a member" in html


def test_scale_entry_pairs_correct_and_mistake(html):
    # the * entry stacks the correct friend non-member version + the member mistake
    # (a member operator* cannot be commutative: 2.0 * a fails to compile).
    assert "Correct: friend non-member operator*" in html
    assert "Mistake: operator* as a member" in html


def test_vocabulary_glossary_present(html):
    assert "Vocabulary — Operator Overloading" in html
    assert "non-member operator" in html


def test_concept_shown_in_right_panel(html):
    # On a diagram:false page the per-example Concept fills the right column as a
    # titled, scrollable aside (option 3) — not a collapsed <details> toggle.
    assert "ccp-title" in html                          # right-panel Concept title
    assert "left operand is the object itself" in html  # op_plus concept text
    assert 'class="concept"' not in html                # the old toggle is gone
