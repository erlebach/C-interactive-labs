## MODIFIED Requirements

### Requirement: Lab 2 topics each carry a cppreference.com doc_url
Each of the 7 Smart Pointers topics SHALL have a `doc_url` pointing to the
most relevant cppreference.com page for the concept it demonstrates.

| Topic id | doc_url |
|---|---|
| `unique_basics` | `https://en.cppreference.com/w/cpp/memory/unique_ptr` |
| `unique_move` | `https://en.cppreference.com/w/cpp/memory/unique_ptr` |
| `unique_copy_err` | `https://en.cppreference.com/w/cpp/memory/unique_ptr` |
| `shared_basics` | `https://en.cppreference.com/w/cpp/memory/shared_ptr` |
| `shared_copy` | `https://en.cppreference.com/w/cpp/memory/shared_ptr` |
| `weak_basics` | `https://en.cppreference.com/w/cpp/memory/weak_ptr` |
| `weak_expired` | `https://en.cppreference.com/w/cpp/memory/weak_ptr` |

#### Scenario: unique_ptr topics link to unique_ptr page
- **WHEN** any of `unique_basics`, `unique_move`, or `unique_copy_err` tab is displayed
- **THEN** the "cppreference ↗" button is present and its topic's `doc_url` is `https://en.cppreference.com/w/cpp/memory/unique_ptr`

#### Scenario: weak_expired link to weak_ptr page
- **WHEN** the `weak_expired` tab is displayed
- **THEN** the "cppreference ↗" button is present and its topic's `doc_url` is `https://en.cppreference.com/w/cpp/memory/weak_ptr`

#### Scenario: All 7 Lab 2 topics have non-empty doc_url
- **WHEN** `TOPICS` is imported from `cpp_ptr_lab.smart_ptrs.topics`
- **THEN** every topic in the list has a non-empty `doc_url`
