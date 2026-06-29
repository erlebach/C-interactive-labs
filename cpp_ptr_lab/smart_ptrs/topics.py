"""Lab 2 — Smart Pointers topic definitions."""

from __future__ import annotations

from cpp_ptr_lab.code_generator import ControlDef, TopicTemplate

# ---------------------------------------------------------------------------
# Topic 1: unique_basics
# ---------------------------------------------------------------------------

unique_basics = TopicTemplate(
    id="unique_basics",
    name="unique_ptr: Basics",
    group="unique_ptr",
    explanation=(
        "std::unique_ptr<T> is a move-only smart pointer that owns its object. "
        "make_unique<T>(args) allocates on the heap and returns a unique_ptr. "
        ".get() returns the raw pointer; *ptr dereferences it; .reset() releases. "
        "When the unique_ptr goes out of scope, the heap object is automatically freed."
    ),
    template="""\
#include <iostream>
#include <cstdio>
#include <memory>
int main() {
    auto ptr = std::make_unique<int>(<<value>>);
    printf("PTRDATA: type=unique ptr_addr=%p target_addr=%p val=%d is_null=0\\n",
           (void*)&ptr, (void*)ptr.get(), *ptr);
    std::cout << "val=" << *ptr << std::endl;
    std::cout << "addr=" << ptr.get() << std::endl;
    <<HARNESS>>
}
""",
    controls=[
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
# Topic 2: unique_move
# ---------------------------------------------------------------------------

unique_move = TopicTemplate(
    id="unique_move",
    name="unique_ptr: Move",
    group="unique_ptr",
    explanation=(
        "unique_ptr cannot be copied — ownership is transferred with std::move(). "
        "After the move, the source unique_ptr is null. "
        "This enforces exclusive ownership: exactly one unique_ptr owns the object."
    ),
    template="""\
#include <iostream>
#include <cstdio>
#include <memory>
int main() {
    auto p = std::make_unique<int>(99);
    auto q = std::move(p);  // transfer ownership; p is now null
    printf("p is null after move: %s\\n", (p == nullptr ? "true" : "false"));
    printf("PTRDATA: type=unique ptr_addr=%p target_addr=%p val=%d is_null=%d\\n",
           (void*)&q, (void*)q.get(), *q, (q == nullptr ? 1 : 0));
    <<HARNESS>>
}
""",
    controls=[],
    target_var="q",
)

# ---------------------------------------------------------------------------
# Topic 3: unique_copy_err — intentional compile error
# ---------------------------------------------------------------------------

unique_copy_err = TopicTemplate(
    id="unique_copy_err",
    name="unique_ptr: Copy Error",
    group="unique_ptr",
    explanation=(
        "unique_ptr's copy constructor is deleted — it cannot be copied. "
        "auto q = p; is a compile error: 'call to deleted function'. "
        "Use std::move(p) to transfer ownership instead. "
        "This guarantees that only one owner exists at any point."
    ),
    template="""\
#include <iostream>
#include <memory>
int main() {
    auto p = std::make_unique<int>(42);
    auto q = p;  // compile error: copy constructor is deleted
    (void)q;
}
""",
    controls=[],
    target_var="p",
    has_ptrdata=False,
)

# ---------------------------------------------------------------------------
# Topic 4: shared_basics
# ---------------------------------------------------------------------------

shared_basics = TopicTemplate(
    id="shared_basics",
    name="shared_ptr: Basics",
    group="shared_ptr",
    explanation=(
        "std::shared_ptr<T> uses reference counting: multiple shared_ptrs can "
        "own the same object. The object is freed when the last owner is destroyed. "
        "use_count() returns the current reference count. "
        "make_shared<T>(args) is preferred — it allocates object and control block together."
    ),
    template="""\
#include <iostream>
#include <cstdio>
#include <memory>
int main() {
    auto sp = std::make_shared<int>(<<value>>);
    printf("PTRDATA: type=shared ptr_addr=%p target_addr=%p val=%d use_count=%ld\\n",
           (void*)&sp, (void*)sp.get(), *sp, (long)sp.use_count());
    std::cout << "use_count=" << sp.use_count() << std::endl;
    <<HARNESS>>
}
""",
    controls=[
        ControlDef(
            id="value",
            label="Value",
            kind="text",
            default="99",
            placeholder="<<value>>",
        ),
    ],
    target_var="sp",
)

# ---------------------------------------------------------------------------
# Topic 5: shared_copy
# ---------------------------------------------------------------------------

shared_copy = TopicTemplate(
    id="shared_copy",
    name="shared_ptr: Copy",
    group="shared_ptr",
    explanation=(
        "Copying a shared_ptr increments the reference count. "
        "Both sp1 and sp2 own the same heap object. "
        "use_count() is 2 while both are alive; drops to 1 when sp2 goes out of scope."
    ),
    template="""\
#include <iostream>
#include <cstdio>
#include <memory>
int main() {
    auto sp1 = std::make_shared<int>(42);
    {
        auto sp2 = sp1;  // copy: use_count becomes 2
        std::cout << "use_count after copy: " << sp1.use_count() << std::endl;
        printf("PTRDATA: type=shared ptr_addr=%p ptr2_addr=%p target_addr=%p val=%d use_count=%ld\\n",
               (void*)&sp1, (void*)&sp2, (void*)sp1.get(), *sp1, (long)sp1.use_count());
    }
    std::cout << "use_count after sp2 scope: " << sp1.use_count() << std::endl;
    <<HARNESS>>
}
""",
    controls=[],
    target_var="sp1",
)

# ---------------------------------------------------------------------------
# Topic 6: weak_basics
# ---------------------------------------------------------------------------

weak_basics = TopicTemplate(
    id="weak_basics",
    name="weak_ptr: Basics",
    group="weak_ptr",
    explanation=(
        "std::weak_ptr<T> observes a shared_ptr without contributing to its "
        "reference count. Creating a weak_ptr does not increase use_count(). "
        "To access the object, call .lock() which returns a shared_ptr (or empty if expired). "
        "use_count() of the shared_ptr remains 1 after creating the weak_ptr."
    ),
    template="""\
#include <iostream>
#include <cstdio>
#include <memory>
int main() {
    auto sp = std::make_shared<int>(<<value>>);
    std::weak_ptr<int> wp = sp;
    std::cout << "use_count with weak_ptr: " << sp.use_count() << std::endl;
    printf("PTRDATA: type=weak ptr_addr=%p expired=%d use_count=%ld\\n",
           (void*)&wp, (int)wp.expired(), (long)sp.use_count());
    if (auto locked = wp.lock()) {
        std::cout << "locked val=" << *locked << std::endl;
    }
    <<HARNESS>>
}
""",
    controls=[
        ControlDef(
            id="value",
            label="Value",
            kind="text",
            default="77",
            placeholder="<<value>>",
        ),
    ],
    target_var="sp",
)

# ---------------------------------------------------------------------------
# Topic 7: weak_expired
# ---------------------------------------------------------------------------

weak_expired = TopicTemplate(
    id="weak_expired",
    name="weak_ptr: Expired",
    group="weak_ptr",
    explanation=(
        "When the last shared_ptr owning an object is destroyed, the weak_ptr "
        "that observed it becomes expired. "
        "wp.expired() returns true; wp.lock() returns an empty shared_ptr. "
        "This is how weak_ptr breaks shared_ptr cycles safely."
    ),
    template="""\
#include <iostream>
#include <cstdio>
#include <memory>
int main() {
    std::weak_ptr<int> wp;
    {
        auto sp = std::make_shared<int>(55);
        wp = sp;
        std::cout << "use_count inside scope: " << sp.use_count() << std::endl;
    }  // sp destroyed here — wp becomes expired
    printf("PTRDATA: type=weak ptr_addr=%p expired=%d use_count=%ld\\n",
           (void*)&wp, (int)wp.expired(), (long)wp.use_count());
    std::cout << "expired: " << (wp.expired() ? "true" : "false") << std::endl;
    std::cout << "lock empty: " << (!wp.lock() ? "true" : "false") << std::endl;
    <<HARNESS>>
}
""",
    controls=[],
    target_var="wp",
)

# ---------------------------------------------------------------------------
# Exported list
# ---------------------------------------------------------------------------

TOPICS: list[TopicTemplate] = [
    unique_basics,
    unique_move,
    unique_copy_err,
    shared_basics,
    shared_copy,
    weak_basics,
    weak_expired,
]

TOPIC_BY_ID: dict[str, TopicTemplate] = {t.id: t for t in TOPICS}
