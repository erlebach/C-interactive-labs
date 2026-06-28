"""Topic Content Module for the C++ Initializer Lab.

Defines the 9 :class:`TopicTemplate` instances — 6 core initialization forms
and 3 gotcha topics — that drive the lab's tabs, control panels, and code
generation.

Each template is a complete, compilable C++20 program containing
``<<placeholder>>`` markers.  The :func:`generate_source` function in
:mod:`cpp_initializer_lab.code_generator` substitutes control values and
injects the memory-dump harness at the ``<<HARNESS>>`` marker.
"""

from __future__ import annotations

from .code_generator import ControlDef, TopicTemplate


# ===========================================================================
# Shared control definitions
# ===========================================================================

_TYPE_OPTIONS = ["int", "double", "char", "bool", "std::string"]

_TYPE_CONTROL = ControlDef(
    id="type",
    label="Type",
    kind="dropdown",
    options=list(_TYPE_OPTIONS),
    default="int",
    placeholder="<<type>>",
)

_VALUE_CONTROL = ControlDef(
    id="value",
    label="Value",
    kind="text",
    default="5",
    placeholder="<<value>>",
)


# ===========================================================================
# Core topics (group = "Core")
# ===========================================================================


DEFAULT_INIT = TopicTemplate(
    id="default",
    name="Default Initialization",
    group="Core",
    target_var="x",
    explanation=(
        "Default initialization leaves a fundamental-type variable with an "
        "indeterminate value — whatever bytes happened to be in memory. "
        "Toggle the type dropdown and run the program; the MEMBYTES panel "
        "will show different garbage bytes each time. Class types with "
        "default constructors are an exception — they run the constructor."
    ),
    controls=[_TYPE_CONTROL],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

int main() {
    <<type>> x;
    <<HARNESS>>
    return 0;
}
""",
)


VALUE_INIT = TopicTemplate(
    id="value",
    name="Value Initialization",
    group="Core",
    target_var="x",
    explanation=(
        "Value initialization with empty braces ``{}`` zero-initializes "
        "fundamental types and invokes the default constructor for class "
        "types. Compare the MEMBYTES output here (all zeros) with the "
        "garbage from default initialization. This form is the modern, safe "
        "default."
    ),
    controls=[_TYPE_CONTROL],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

int main() {
    <<type>> x{};
    <<HARNESS>>
    return 0;
}
""",
)


DIRECT_INIT = TopicTemplate(
    id="direct",
    name="Direct Initialization",
    group="Core",
    target_var="x",
    explanation=(
        "Direct initialization uses parentheses to call a constructor "
        "directly: ``T x(args)``. For fundamental types this is equivalent "
        "to assignment. Change the type and value to see how the bytes "
        "reflect the stored value."
    ),
    controls=[_TYPE_CONTROL, _VALUE_CONTROL],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

int main() {
    <<type>> x(<<value>>);
    <<HARNESS>>
    return 0;
}
""",
)


COPY_INIT = TopicTemplate(
    id="copy",
    name="Copy Initialization",
    group="Core",
    target_var="x",
    explanation=(
        "Copy initialization uses the ``=`` sign: ``T x = value``. The "
        "compiler converts the right-hand side to ``T`` and then "
        "constructs ``x`` from it. For class types this requires a "
        "non-explicit converting constructor."
    ),
    controls=[_TYPE_CONTROL, _VALUE_CONTROL],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

int main() {
    <<type>> x = <<value>>;
    <<HARNESS>>
    return 0;
}
""",
)


LIST_INIT = TopicTemplate(
    id="list",
    name="List/Brace Initialization",
    group="Core",
    target_var="x",
    explanation=(
        "Brace initialization ``T x{value}`` prevents narrowing "
        "conversions — a key safety feature over the older forms. Try "
        "setting the type to ``int`` and the value to ``3.14``: the "
        "program will fail to compile because narrowing ``double`` to "
        "``int`` is forbidden inside braces."
    ),
    controls=[_TYPE_CONTROL, _VALUE_CONTROL],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

int main() {
    <<type>> x{<<value>>};
    <<HARNESS>>
    return 0;
}
""",
)


AGGREGATE_INIT = TopicTemplate(
    id="aggregate",
    name="Aggregate Initialization",
    group="Core",
    target_var="s",
    explanation=(
        "Aggregate initialization brace-initializes the members of a "
        "plain struct in declaration order. Adjust the field count and "
        "values to see how each member maps to a byte region. Extra "
        "members are zero-initialized when fewer values are supplied."
    ),
    controls=[
        ControlDef(
            id="field_count",
            label="Field count",
            kind="dropdown",
            options=["2", "3", "4"],
            default="2",
            placeholder="<<extra_fields>>",
            value_map={
                "2": "",
                "3": "    int c;\n",
                "4": "    int c;\n    int d;\n",
            },
        ),
        ControlDef(
            id="values",
            label="Values (comma-separated)",
            kind="text",
            default="1, 2",
            placeholder="<<values>>",
        ),
    ],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

struct S {
    int a;
    int b;
<<extra_fields>>};

int main() {
    S s{<<values>>};
    <<HARNESS>>
    return 0;
}
""",
)


# ===========================================================================
# Gotcha topics (group = "Gotchas")
# ===========================================================================


MOST_VEXING_PARSE = TopicTemplate(
    id="most-vexing-parse",
    name="Most Vexing Parse",
    group="Gotchas",
    target_var="w",
    explanation=(
        "``Widget w();`` looks like it constructs a default-constructed "
        "object, but the C++ grammar parses it as a *function declaration* "
        "named ``w`` taking no arguments and returning a ``Widget``. "
        "Switch to the braces form ``Widget w{};`` to get an actual object. "
        "The parentheses form will fail to compile because the harness "
        "cannot take ``sizeof`` of a function."
    ),
    controls=[
        ControlDef(
            id="form",
            label="Form",
            kind="dropdown",
            options=["parentheses", "braces"],
            default="parentheses",
            placeholder="<<form>>",
            value_map={"parentheses": "()", "braces": "{}"},
        ),
    ],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

struct Widget {
    Widget() {}
    int data = 0;
};

int main() {
    Widget w<<form>>;
    <<HARNESS>>
    return 0;
}
""",
)


EXPLICIT_VS_IMPLICIT = TopicTemplate(
    id="explicit-vs-implicit",
    name="Explicit vs Implicit Constructor",
    group="Gotchas",
    target_var="f",
    explanation=(
        "Marking a single-argument constructor ``explicit`` forbids the "
        "implicit conversion used by copy initialization. With the "
        "``explicit`` checkbox on and the form set to copy-init, "
        "``Foo f = 42;`` will fail to compile. Switch to direct-init "
        "``Foo f(42);`` or uncheck ``explicit`` to make it compile again."
    ),
    controls=[
        ControlDef(
            id="explicit",
            label="explicit keyword",
            kind="checkbox",
            default=False,
            placeholder="<<explicit_kw>>",
            value_map={"true": "explicit ", "false": ""},
        ),
        ControlDef(
            id="form",
            label="Form",
            kind="dropdown",
            options=["copy", "direct"],
            default="copy",
            placeholder="<<form>>",
            value_map={"copy": " = 42", "direct": "(42)"},
        ),
    ],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>

struct Foo {
    <<explicit_kw>>Foo(int v) : value(v) {}
    int value;
};

int main() {
    Foo f<<form>>;
    <<HARNESS>>
    return 0;
}
""",
)


INIT_LIST_HIJACK = TopicTemplate(
    id="initializer-list-hijack",
    name="initializer_list Hijacking",
    group="Gotchas",
    target_var="f",
    explanation=(
        "When a class has both a constructor taking ``int`` and one taking "
        "``std::initializer_list<int>``, brace initialization strongly "
        "prefers the ``initializer_list`` overload — even for a single "
        "value. Use the parentheses form ``Foo f(5);`` to select the "
        "``int`` constructor. Watch the stdout to see which constructor "
        "runs."
    ),
    controls=[
        ControlDef(
            id="form",
            label="Form",
            kind="dropdown",
            options=["brace", "paren"],
            default="brace",
            placeholder="<<form>>",
            value_map={"brace": "{<<value>>}", "paren": "(<<value>>)"},
        ),
        ControlDef(
            id="value",
            label="Value",
            kind="text",
            default="5",
            placeholder="<<value>>",
        ),
    ],
    template="""\
#include <iostream>
#include <cstdio>
#include <string>
#include <initializer_list>

struct Foo {
    Foo(int x) : value(x) { std::cout << "int ctor\\n"; }
    Foo(std::initializer_list<int> il)
        : value(il.size() == 0 ? 0 : *il.begin()) { std::cout << "init_list ctor\\n"; }
    int value;
};

int main() {
    Foo f<<form>>;
    <<HARNESS>>
    return 0;
}
""",
)


# ===========================================================================
# Public registry
# ===========================================================================

#: All topics in display order (Core first, then Gotchas).
TOPICS: list[TopicTemplate] = [
    DEFAULT_INIT,
    VALUE_INIT,
    DIRECT_INIT,
    COPY_INIT,
    LIST_INIT,
    AGGREGATE_INIT,
    MOST_VEXING_PARSE,
    EXPLICIT_VS_IMPLICIT,
    INIT_LIST_HIJACK,
]

#: Quick lookup by topic id.
TOPIC_BY_ID: dict[str, TopicTemplate] = {t.id: t for t in TOPICS}
