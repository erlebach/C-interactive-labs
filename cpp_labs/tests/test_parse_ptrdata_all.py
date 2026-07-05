# cpp_labs/tests/test_parse_ptrdata_all.py
from cpp_labs.compiler_runner import parse_ptrdata_all


def test_returns_empty_when_none():
    assert parse_ptrdata_all("hello\nworld\n") == []


def test_reads_every_line_in_order():
    out = (
        "enter main\n"
        "PTRDATA: type=frames step=1 ptrbytes=8 live=main:0x10:r:4:0\n"
        "enter foo\n"
        "PTRDATA: type=frames step=2 ptrbytes=8 live=main:0x10:r:4:0,foo:0x8:t:4:4\n"
    )
    steps = parse_ptrdata_all(out)
    assert len(steps) == 2
    assert steps[0]["step"] == "1"
    assert steps[1]["live"] == "main:0x10:r:4:0,foo:0x8:t:4:4"


def test_single_line_matches_parse_ptrdata_shape():
    out = "PTRDATA: type=memmap regions=text:0x1:main\n"
    steps = parse_ptrdata_all(out)
    assert steps == [{"type": "memmap", "regions": "text:0x1:main"}]
