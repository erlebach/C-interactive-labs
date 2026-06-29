"""Launcher for Lab 2 — C++ Smart Pointers.

Run with::

    python -m cpp_ptr_lab.run_smart
"""

from __future__ import annotations

from pathlib import Path

from .app_base import PtrLabApp
from .smart_ptrs.topics import TOPICS
from .yaml_config import load_enabled_topics

_CONFIG = Path(__file__).parent / "lab_config.yaml"


def main() -> int:
    topics = load_enabled_topics(_CONFIG, "smart_ptrs", TOPICS)
    if not topics:
        print("All smart_ptrs topics are disabled in lab_config.yaml — exiting.")
        return 0
    app = PtrLabApp(topics, "C++ Smart Pointers Lab")
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
