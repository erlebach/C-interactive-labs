## ADDED Requirements

### Requirement: Lab window with 7 topic tabs
The lab SHALL open a separate Dear PyGui viewport titled "C++ Smart Pointers Lab"
containing a tab bar with one tab per enabled topic, ordered as defined in
`smart_ptrs/topics.py`. Topics disabled via `lab_config.yaml` SHALL be absent.

#### Scenario: All topics enabled
- **WHEN** `lab_config.yaml` has all 7 smart-ptrs topics set to `true`
- **THEN** the tab bar shows exactly 7 tabs in declaration order

### Requirement: unique_ptr topics cover ownership lifecycle
The lab SHALL include three `unique_ptr` topics:

- `unique_basics`: demonstrates `make_unique<int>(v)`, `.get()`, `.operator*()`,
  `.reset()`; diagram shows the owning pointer box and heap target
- `unique_move`: demonstrates `auto q = std::move(p)`; after move, diagram shows
  p box with NULL target and q box with arrow to heap value
- `unique_copy_err`: attempts `auto q = p` (copy); compilation SHALL fail; diagram
  canvas SHALL show red border; explanation SHALL state copy constructor is deleted

#### Scenario: unique_move — source is null after move
- **WHEN** `unique_move` topic is run
- **THEN** program stdout prints `p is null after move: true`;
  diagram shows p→NULL and q→value

#### Scenario: unique_copy_err — compile error with red border
- **WHEN** `unique_copy_err` topic Run is clicked
- **THEN** compilation fails; diagram canvas shows red border;
  output panel shows "call to deleted function" or equivalent g++ message

### Requirement: shared_ptr topics expose use_count
The lab SHALL include two `shared_ptr` topics:

- `shared_basics`: demonstrates `make_shared<int>(v)`, `use_count()=1`,
  `.get()`, `.operator*()`
- `shared_copy`: demonstrates `auto sp2 = sp1` then `use_count()=2`;
  when sp2 goes out of scope, `use_count()` returns to 1; diagram SHALL
  show two pointer boxes both pointing to the same target box, annotated with
  `use_count=N`

#### Scenario: shared_copy use_count in diagram
- **WHEN** `shared_copy` is run
- **THEN** program stdout prints `use_count after copy: 2` and
  `use_count after sp2 scope: 1`; diagram shows two boxes→one target with
  `use_count=2` annotation

### Requirement: weak_ptr topics demonstrate non-owning semantics
The lab SHALL include two `weak_ptr` topics:

- `weak_basics`: demonstrates `weak_ptr<int> wp = sp`; `use_count` of sp
  SHALL remain 1 after wp is created; `wp.lock()` returns a valid shared_ptr
- `weak_expired`: sp is destroyed (goes out of scope); `wp.expired()` returns
  true; `wp.lock()` returns an empty shared_ptr; program prints confirmation

#### Scenario: weak_basics — use_count unaffected
- **WHEN** `weak_basics` is run
- **THEN** stdout prints `use_count with weak_ptr: 1`

#### Scenario: weak_expired — lock returns empty
- **WHEN** `weak_expired` is run
- **THEN** stdout prints `expired: true` and `lock empty: true`
