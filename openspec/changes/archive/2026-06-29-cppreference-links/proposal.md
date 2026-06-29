## Why

Students using the lab tabs have no in-context reference when they encounter unfamiliar syntax or want to read further. Adding a per-topic cppreference.com link lets them jump directly to the authoritative C++ documentation for the exact concept shown on each tab, without leaving their workflow to search manually.

## What Changes

- Each topic tab gains a clickable, colored "cppreference" link in the left control column, below the explanation text
- Clicking the link opens the relevant cppreference.com page in the system default browser
- The link is rendered as a styled DPG button (not plain text) to make it obviously interactive
- Each `TopicTemplate` gains a `doc_url: str = ""` field; empty string means no link is shown

## Capabilities

### New Capabilities

- `topic-doc-link`: Per-topic clickable documentation link widget rendered in the left column of each tab; uses `webbrowser.open()` to launch the URL; styled with a distinct color to signal interactivity; absent when `doc_url` is empty

### Modified Capabilities

- `pointers-refs-lab`: Each of the 8 Lab 1 topics gains a `doc_url` pointing to the relevant cppreference page (e.g., pointer declarations, `const` qualifier, references, `nullptr`, AddressSanitizer guidance)
- `smart-ptrs-lab`: Each of the 7 Lab 2 topics gains a `doc_url` pointing to the relevant cppreference page (e.g., `unique_ptr`, `shared_ptr`, `weak_ptr`, `make_unique`, `make_shared`)

## Impact

- `cpp_ptr_lab/code_generator.py`: add `doc_url: str = ""` field to `TopicTemplate`
- `cpp_ptr_lab/app_base.py`: add `_build_doc_link()` call inside `_build_topic_tab()`; add `_on_doc_link_clicked()` callback using `webbrowser.open()`
- `cpp_ptr_lab/pointers_refs/topics.py`: add `doc_url` to all 8 topic definitions
- `cpp_ptr_lab/smart_ptrs/topics.py`: add `doc_url` to all 7 topic definitions
- No new dependencies (Python `webbrowser` is stdlib)
- No breaking changes to existing `cpp_initializer_lab/`
