# cpp_labs/tests/test_extra_compile_flags.py
from cpp_labs.code_generator import TopicTemplate


def test_topic_has_extra_compile_flags_default_empty():
    t = TopicTemplate(
        id="x",
        name="X",
        template="int main(){}",
        controls=[],
        explanation="e",
        group="g",
    )
    assert t.extra_compile_flags == []
