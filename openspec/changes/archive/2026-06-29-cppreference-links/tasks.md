## 1. TopicTemplate — doc_url field (RED)

- [x] 1.1 Write `test_topic_template_doc_url_default`: assert `TopicTemplate(...).doc_url == ""`
- [x] 1.2 Write `test_topic_template_doc_url_set`: assert `TopicTemplate(..., doc_url="https://example.com").doc_url == "https://example.com"`
- [x] 1.3 Confirm tests fail → RED

## 2. TopicTemplate — doc_url field (GREEN)

- [x] 2.1 Add `doc_url: str = ""` field to `TopicTemplate` in `cpp_ptr_lab/code_generator.py`
- [x] 2.2 Run `pytest cpp_ptr_lab/tests/test_code_generator.py` → GREEN

## 3. app_base.py — link theme and button

- [x] 3.1 Add `import webbrowser` to `app_base.py`
- [x] 3.2 Implement `_make_link_theme()` in `PtrLabApp.__init__`: create DPG theme tag `"cpl_link_theme"` with button colors `(100, 180, 255, 255)`, hover `(140, 210, 255, 255)`, active `(70, 150, 220, 255)`
- [x] 3.3 Implement `_on_doc_link_clicked(self, sender, app_data, user_data)`: call `webbrowser.open(user_data)`
- [x] 3.4 In `_build_topic_tab()`, after `dpg.add_text(topic.explanation, ...)`, add: if `topic.doc_url`, render a button tagged `cpl_{topic_id}_doc_link` labeled `"cppreference ↗"` with `callback=self._on_doc_link_clicked, user_data=topic.doc_url`; bind `"cpl_link_theme"` to the button

## 4. Lab 1 — assign doc_url to each topic

- [x] 4.1 Set `doc_url="https://en.cppreference.com/w/cpp/language/pointer"` on `basic_ptr`
- [x] 4.2 Set `doc_url="https://en.cppreference.com/w/cpp/language/cv"` on `const_taxonomy`
- [x] 4.3 Set `doc_url="https://en.cppreference.com/w/cpp/language/reference"` on `ref_must_bind`
- [x] 4.4 Set `doc_url="https://en.cppreference.com/w/cpp/language/reference"` on `ref_no_null`
- [x] 4.5 Set `doc_url="https://en.cppreference.com/w/cpp/language/reference"` on `ref_rebind_illusion`
- [x] 4.6 Set `doc_url="https://en.cppreference.com/w/cpp/language/reference"` on `ref_const`
- [x] 4.7 Set `doc_url="https://en.cppreference.com/w/cpp/language/ub"` on `null_deref`
- [x] 4.8 Set `doc_url="https://en.cppreference.com/w/cpp/language/ub"` on `dangling_ptr`

## 5. Lab 2 — assign doc_url to each topic

- [x] 5.1 Set `doc_url="https://en.cppreference.com/w/cpp/memory/unique_ptr"` on `unique_basics`
- [x] 5.2 Set `doc_url="https://en.cppreference.com/w/cpp/memory/unique_ptr"` on `unique_move`
- [x] 5.3 Set `doc_url="https://en.cppreference.com/w/cpp/memory/unique_ptr"` on `unique_copy_err`
- [x] 5.4 Set `doc_url="https://en.cppreference.com/w/cpp/memory/shared_ptr"` on `shared_basics`
- [x] 5.5 Set `doc_url="https://en.cppreference.com/w/cpp/memory/shared_ptr"` on `shared_copy`
- [x] 5.6 Set `doc_url="https://en.cppreference.com/w/cpp/memory/weak_ptr"` on `weak_basics`
- [x] 5.7 Set `doc_url="https://en.cppreference.com/w/cpp/memory/weak_ptr"` on `weak_expired`

## 6. Verification

- [x] 6.1 Write integration test: assert all Lab 1 `TOPICS` have non-empty `doc_url`
- [x] 6.2 Write integration test: assert all Lab 2 `TOPICS` have non-empty `doc_url`
- [x] 6.3 Run `pytest cpp_ptr_lab/tests/` → all GREEN
- [ ] 6.4 Launch `python -m cpp_ptr_lab.run_ptrs` → confirm "cppreference ↗" button visible in each tab; click one and verify browser opens the correct URL
- [ ] 6.5 Launch `python -m cpp_ptr_lab.run_smart` → confirm same for Lab 2 tabs
