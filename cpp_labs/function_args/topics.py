"""Subject `function_args` — pass a variable by value, pointer, or reference.

One topic, one `mode` dropdown → three variants rendered as tabs. The lesson:
after ``modify(val)``, did the caller's ``val`` change, and does the parameter
link back to it?

  - **by value**    — ``int x``  : a copy; ``x = 99`` leaves ``val`` at 42. No
                       address links the parameter to the caller → no diagram.
  - **by pointer**  — ``int* x`` : a copy of ``&val``; ``*x = 99`` writes THROUGH
                       it → ``memory_diagram`` shows a raw arrow back to ``val``.
  - **by reference**— ``int& x`` : an alias for ``val`` (same address); ``x = 99``
                       changes ``val`` → ``memory_diagram`` shows the ref arrow.

Each mode fills a single ``<<mode>>`` placeholder with a complete program body,
so one dropdown control drives four co-varying spots (signature, assignment,
probe, call arg) without a Cartesian variant blow-up and without touching the
code generator.  The per-mode bodies are built from one skeleton below, so the
only thing that differs between them is the four substituted fragments.
"""

from __future__ import annotations

from cpp_labs.code_generator import ControlDef, TopicTemplate

# One skeleton; each mode substitutes the four <<...>> fragments.  The literal
# <<HARNESS>> is left for generate_source to fill (dumps val's bytes in main).
_SKELETON = """\
void modify(<<param>>) {
    <<assign>>
    <<probe>>
}

int main() {
    int val = 42;
    std::cout << "before: val = " << val << std::endl;
    modify(<<arg>>);
    std::cout << "after:  val = " << val << std::endl;
    <<HARNESS>>
}
"""


def _prog(param: str, assign: str, probe: str, arg: str) -> str:
    return (
        _SKELETON.replace("<<param>>", param)
        .replace("<<assign>>", assign)
        .replace("<<probe>>", probe)
        .replace("<<arg>>", arg)
    )


_BY_VALUE = _prog(
    param="int x",
    assign="x = 99;  // modifies the local copy only",
    probe='std::cout << "(by value: x is a separate copy; nothing links it to val)"\n'
    "              << std::endl;",
    arg="val",
)

_BY_POINTER = _prog(
    param="int* x",
    assign="*x = 99;  // write THROUGH the pointer into the caller's val",
    probe='printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%d\\n",\n'
    "           (void*)&x, (void*)x, *x);",
    arg="&val",
)

_BY_REFERENCE = _prog(
    param="int& x",
    assign="x = 99;  // x is another name for val — same object",
    probe='printf("PTRDATA: type=ref ref_addr=%p target_addr=%p target_val=%d\\n",\n'
    "           (void*)&x, (void*)&x, x);",
    arg="val",
)


function_args = TopicTemplate(
    id="function_args",
    name="Function Arguments",
    group="Functions",
    doc_url="https://en.cppreference.com/w/cpp/language/functions",
    explanation=(
        "How a function receives an argument decides whether it can change the "
        "caller's variable. By value it gets a copy (the caller is untouched). "
        "By pointer it gets a copy of the address, so *x reaches back and writes "
        "the caller's variable. By reference the parameter is an alias for the "
        "caller's variable — same address — so writing it changes the original. "
        "Each tab passes the same val = 42 and prints it after the call."
    ),
    template="""\
#include <iostream>
#include <cstdio>
<<mode>>
""",
    controls=[
        ControlDef(
            id="mode",
            label="Passing convention",
            kind="dropdown",
            options=["by value", "by pointer", "by reference"],
            default="by value",
            placeholder="<<mode>>",
            value_map={
                "by value": _BY_VALUE,
                "by pointer": _BY_POINTER,
                "by reference": _BY_REFERENCE,
            },
        ),
    ],
    target_var="val",
)

TOPICS: list[TopicTemplate] = [function_args]
