"""Topics surfaced on the basic_ptr page.

`basic_ptr` belongs to the Pointers & References lab, so its `TopicTemplate` is
defined once in `cpp_ptr_lab/pointers_refs/topics.py` and re-exported here — NOT
duplicated. This gives every subject package the same shape (`topics.py` +
`<subject>.page.yaml` + `test_<subject>.py`) while keeping a single source of
truth for the definition. A subject that introduces genuinely new topics (e.g.
`function_args`) defines them in its own `topics.py` instead.
"""

from __future__ import annotations

from cpp_ptr_lab.pointers_refs.topics import basic_ptr

TOPICS = [basic_ptr]
