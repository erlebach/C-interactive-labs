"""Lab 1 — Pointers & References topic definitions."""

from __future__ import annotations

from cpp_ptr_lab.code_generator import ControlDef, TopicTemplate

# ---------------------------------------------------------------------------
# Topic 1: Basic raw pointer
# ---------------------------------------------------------------------------

basic_ptr = TopicTemplate(
    id="basic_ptr",
    name="Basic Pointer",
    group="Raw",
    explanation=(
        "A raw pointer holds the memory address of another variable. "
        "Dereferencing it (*ptr) accesses the value at that address. "
        "The pointer variable itself occupies sizeof(void*) bytes on the stack."
    ),
    template="""\
#include <iostream>
#include <cstdio>
int main() {
    <<type>> val = (<<type>>)<<value>>;
    <<type>>* ptr = &val;
    printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%g\\n",
           (void*)&ptr, (void*)ptr, (double)val);
    <<HARNESS>>
}
""",
    controls=[
        ControlDef(
            id="type",
            label="Type",
            kind="dropdown",
            options=["int", "double", "float"],
            default="int",
            placeholder="<<type>>",
        ),
        ControlDef(
            id="value",
            label="Value",
            kind="text",
            default="42",
            placeholder="<<value>>",
        ),
    ],
    target_var="ptr",
)

# ---------------------------------------------------------------------------
# Topic 2: const taxonomy
# ---------------------------------------------------------------------------

const_taxonomy = TopicTemplate(
    id="const_taxonomy",
    name="const Taxonomy",
    group="Raw",
    explanation=(
        "const modifies the pointer or the pointee — or both. "
        "Read the declaration right-to-left: "
        "int* = pointer to int (both mutable); "
        "const int* = pointer to const int (value immutable via this ptr); "
        "int* const = const pointer to int (address immutable); "
        "const int* const = both immutable."
    ),
    template="""\
#include <iostream>
#include <cstdio>
int main() {
    int val = 42;
    <<decl>>
    <<mutate>>
    printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%d\\n",
           (void*)&ptr, (void*)ptr, *ptr);
    <<HARNESS>>
}
""",
    controls=[
        ControlDef(
            id="variant",
            label="Pointer type",
            kind="dropdown",
            options=[
                "int* (pointer and value both mutable)",
                "const int* (value immutable, pointer mutable)",
                "int* const (pointer immutable, value mutable)",
                "const int* const (both immutable)",
            ],
            default="int* (pointer and value both mutable)",
            placeholder="<<decl>>",
            value_map={
                "int* (pointer and value both mutable)":
                    "int* ptr = &val;",
                "const int* (value immutable, pointer mutable)":
                    "const int* ptr = &val;",
                "int* const (pointer immutable, value mutable)":
                    "int* const ptr = &val;",
                "const int* const (both immutable)":
                    "const int* const ptr = &val;",
            },
        ),
        ControlDef(
            id="mutate",
            label="Attempt mutation through pointer",
            kind="checkbox",
            default=False,
            placeholder="<<mutate>>",
            value_map={
                "false": "// no mutation attempted",
                "true": "*ptr = 99;  // attempt mutation through pointer",
            },
        ),
    ],
    target_var="val",
)

# ---------------------------------------------------------------------------
# Topic 3: ref_must_bind — intentional compile error
# ---------------------------------------------------------------------------

ref_must_bind = TopicTemplate(
    id="ref_must_bind",
    name="Ref: Must Bind",
    group="Refs",
    explanation=(
        "Invariant 1: a reference must be bound to an object at the point "
        "of declaration — it cannot be declared uninitialized. "
        "Contrary to pointers (int* p; is valid), int& r; is a compile error."
    ),
    template="""\
#include <iostream>
// Contrary to pointers (int* p; is valid uninitialized),
// a reference must be bound at declaration.
int main() {
    int& r;  // compile error: 'r' declared as reference but not initialized
}
""",
    controls=[],
    target_var="r",
    has_ptrdata=False,
)

# ---------------------------------------------------------------------------
# Topic 4: ref_no_null — null pointer vs null reference
# ---------------------------------------------------------------------------

ref_no_null = TopicTemplate(
    id="ref_no_null",
    name="Ref: No Null",
    group="Refs",
    explanation=(
        "Invariant 2: a reference cannot be null — there is no null reference. "
        "Contrary to pointers (int* p = nullptr; is valid), attempting to form "
        "a null reference is undefined behaviour. "
        "Choose 'Show null ptr' to see a valid null pointer; "
        "'Attempt null ref' triggers UB (shown safely via ASan)."
    ),
    template="""\
#include <iostream>
#include <cstdio>
int main() {
    <<variant>>
}
""",
    controls=[
        ControlDef(
            id="variant",
            label="Variant",
            kind="dropdown",
            options=["Show null ptr", "Attempt null ref"],
            default="Show null ptr",
            placeholder="<<variant>>",
            value_map={
                "Show null ptr": (
                    '    int* ptr = nullptr;\n'
                    '    printf("PTRDATA: type=null ptr_addr=%p\\n", (void*)ptr);\n'
                    '    printf("MEMBYTES: 00\\n");\n'
                    '    std::cout << "ptr is null: " << (ptr == nullptr ? "true" : "false") << std::endl;'
                ),
                "Attempt null ref": (
                    '    int* raw = nullptr;\n'
                    '    int& r = *raw;  // UB: null reference — run with ASan for safe output\n'
                    '    printf("PTRDATA: type=ref ref_addr=%p target_addr=%p target_val=%d\\n",\n'
                    '           (void*)&r, (void*)raw, r);'
                ),
            },
        ),
    ],
    target_var="ptr",
    sanitize=True,
)

# ---------------------------------------------------------------------------
# Topic 5: ref_rebind_illusion
# ---------------------------------------------------------------------------

ref_rebind_illusion = TopicTemplate(
    id="ref_rebind_illusion",
    name="Ref: Rebind Illusion",
    group="Refs",
    explanation=(
        "Invariant 3: a reference cannot be rebound after initialization. "
        "r = b does NOT rebind r to b — it assigns b's value through r to a. "
        "Contrary to pointers (p = &b rebinds the pointer), references are "
        "permanently bound to their initial target. "
        "&r == &a remains true after the assignment."
    ),
    template="""\
#include <iostream>
#include <cstdio>
int main() {
    int a = 10;
    int b = 20;
    int& r = a;
    r = b;  // assigns b's value to a, does NOT rebind r
    printf("&r == &a: %s\\n", (&r == &a ? "true" : "false"));
    printf("a=%d, b=%d, r=%d\\n", a, b, r);
    printf("PTRDATA: type=ref ref_addr=%p target_addr=%p target_val=%d\\n",
           (void*)&r, (void*)&a, a);
    <<HARNESS>>
}
""",
    controls=[],
    target_var="a",
)

# ---------------------------------------------------------------------------
# Topic 6: ref_const
# ---------------------------------------------------------------------------

ref_const = TopicTemplate(
    id="ref_const",
    name="Ref: const Ref",
    group="Refs",
    explanation=(
        "T& allows reading and writing through the reference. "
        "const T& (where T is the type of the referred-to object, e.g. int, double) "
        "allows only reading — attempting modification is a compile error. "
        "const T& also extends the lifetime of temporaries."
    ),
    template="""\
#include <iostream>
#include <cstdio>
int main() {
    int x = 42;
    <<ref_decl>>
    <<modify>>
    printf("PTRDATA: type=ref ref_addr=%p target_addr=%p target_val=%d\\n",
           (void*)&r, (void*)&x, x);
    <<HARNESS>>
}
""",
    controls=[
        ControlDef(
            id="ref_type",
            label="Reference type",
            kind="dropdown",
            options=["int&", "const int&"],
            default="int&",
            placeholder="<<ref_decl>>",
            value_map={
                "int&": "int& r = x;",
                "const int&": "const int& r = x;",
            },
        ),
        ControlDef(
            id="modify",
            label="Attempt modification through reference",
            kind="checkbox",
            default=False,
            placeholder="<<modify>>",
            value_map={
                "false": "// no modification",
                "true": "r = 99;  // attempt modification",
            },
        ),
    ],
    target_var="x",
)

# ---------------------------------------------------------------------------
# Topic 7: null_deref (Gotcha — ASan)
# ---------------------------------------------------------------------------

null_deref = TopicTemplate(
    id="null_deref",
    name="Gotcha: Null Deref",
    group="Gotchas",
    explanation=(
        "Dereferencing a null pointer is undefined behaviour. "
        "Without AddressSanitizer the program typically crashes with SIGSEGV. "
        "With ASan, you get a detailed diagnostic showing the exact instruction. "
        "Run this topic to see the ASan output."
    ),
    template="""\
#include <iostream>
#include <cstdio>
int main() {
    int* ptr = nullptr;
    printf("PTRDATA: type=null ptr_addr=%p\\n", (void*)ptr);
    int val = *ptr;  // null dereference — UB, caught by ASan
    std::cout << "val=" << val << std::endl;
    <<HARNESS>>
}
""",
    controls=[],
    target_var="ptr",
    sanitize=True,
)

# ---------------------------------------------------------------------------
# Topic 8: dangling_ptr (Gotcha — ASan)
# ---------------------------------------------------------------------------

dangling_ptr = TopicTemplate(
    id="dangling_ptr",
    name="Gotcha: Dangling Ptr",
    group="Gotchas",
    explanation=(
        "A pointer to a local variable becomes dangling when the variable goes "
        "out of scope. Using it is undefined behaviour. "
        "Contrary to what the output might show, the memory may have been reused. "
        "AddressSanitizer reliably catches this."
    ),
    template="""\
#include <iostream>
#include <cstdio>

// Helper returns a pointer to its local variable — dangling after return.
int* make_dangling() {
    int local = 99;
    return &local;
}

int main() {
    int* ptr = make_dangling();  // ptr is now dangling — UB
    printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%d\\n",
           (void*)&ptr, (void*)ptr, *ptr);
    <<HARNESS>>
}
""",
    controls=[],
    target_var="ptr",
    sanitize=True,
)

# ---------------------------------------------------------------------------
# Exported list
# ---------------------------------------------------------------------------

TOPICS: list[TopicTemplate] = [
    basic_ptr,
    const_taxonomy,
    ref_must_bind,
    ref_no_null,
    ref_rebind_illusion,
    ref_const,
    null_deref,
    dangling_ptr,
]

TOPIC_BY_ID: dict[str, TopicTemplate] = {t.id: t for t in TOPICS}
