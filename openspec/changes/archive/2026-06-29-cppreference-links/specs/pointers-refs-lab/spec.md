## MODIFIED Requirements

### Requirement: Lab 1 topics each carry a cppreference.com doc_url
Each of the 8 Pointers & References topics SHALL have a `doc_url` pointing to the
most relevant cppreference.com page for the concept it demonstrates.

| Topic id | doc_url |
|---|---|
| `basic_ptr` | `https://en.cppreference.com/w/cpp/language/pointer` |
| `const_taxonomy` | `https://en.cppreference.com/w/cpp/language/cv` |
| `ref_must_bind` | `https://en.cppreference.com/w/cpp/language/reference` |
| `ref_no_null` | `https://en.cppreference.com/w/cpp/language/reference` |
| `ref_rebind_illusion` | `https://en.cppreference.com/w/cpp/language/reference` |
| `ref_const` | `https://en.cppreference.com/w/cpp/language/reference` |
| `null_deref` | `https://en.cppreference.com/w/cpp/language/ub` |
| `dangling_ptr` | `https://en.cppreference.com/w/cpp/language/ub` |

#### Scenario: basic_ptr link button points to pointer page
- **WHEN** the `basic_ptr` tab is displayed
- **THEN** the "cppreference ↗" button is present and its topic's `doc_url` is `https://en.cppreference.com/w/cpp/language/pointer`

#### Scenario: null_deref and dangling_ptr link to UB page
- **WHEN** either the `null_deref` or `dangling_ptr` tab is displayed
- **THEN** the "cppreference ↗" button is present and its topic's `doc_url` is `https://en.cppreference.com/w/cpp/language/ub`

#### Scenario: All 8 Lab 1 topics have non-empty doc_url
- **WHEN** `TOPICS` is imported from `cpp_ptr_lab.pointers_refs.topics`
- **THEN** every topic in the list has a non-empty `doc_url`
