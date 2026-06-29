"""Launcher for Lab 1 — C++ Pointers & References.

Run with::

    python -m cpp_ptr_lab.run_ptrs
"""

from __future__ import annotations

from pathlib import Path

from .app_base import PtrLabApp
from .pointers_refs.topics import TOPICS
from .yaml_config import load_enabled_topics

_CONFIG = Path(__file__).parent / "lab_config.yaml"


def main() -> int:
    topics = load_enabled_topics(_CONFIG, "pointers_refs", TOPICS)
    if not topics:
        print("All pointers_refs topics are disabled in lab_config.yaml — exiting.")
        return 0
    app = PtrLabApp(topics, "C++ Pointers & References Lab")
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
