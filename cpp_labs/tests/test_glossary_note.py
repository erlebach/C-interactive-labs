# cpp_labs/tests/test_glossary_note.py
from cpp_labs.components import glossary_note


def test_glossary_note_is_a_concept_style_chip():
    html = glossary_note("g", [("bss", "uninitialized globals"),
                               ("heap", "dynamic allocations")])
    assert 'class="concept chip-inline"' in html      # same chip look + inline flag
    assert "Memory glossary" in html                   # default label
    assert "<summary" in html and "caret" in html      # button-like toggle chip
    assert "bss" in html and "uninitialized globals" in html
    assert "heap" in html and "dynamic allocations" in html


def test_glossary_note_custom_label():
    html = glossary_note("g", [("x", "y")], label="Terms")
    assert "Terms" in html
