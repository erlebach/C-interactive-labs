"""YAML-based topic visibility configuration for the C++ Pointer Lab."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cpp_ptr_lab.code_generator import TopicTemplate

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def load_enabled_topics(
    yaml_path: Path | str,
    lab_key: str,
    all_topics: list[TopicTemplate],
) -> list[TopicTemplate]:
    """Return the subset of *all_topics* enabled by *yaml_path* for *lab_key*.

    Falls back to returning all topics if the file is missing or malformed.
    """
    if yaml is None:  # pragma: no cover
        print(
            "pyyaml not installed — all topics enabled. "
            "Run: pip install pyyaml",
            file=sys.stderr,
        )
        return list(all_topics)

    yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        print(
            f"lab_config.yaml not found — all topics enabled ({yaml_path})",
            file=sys.stderr,
        )
        return list(all_topics)

    try:
        with open(yaml_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"lab_config.yaml parse error — all topics enabled: {exc}", file=sys.stderr)
        return list(all_topics)

    if not isinstance(config, dict):
        print("lab_config.yaml: unexpected format — all topics enabled", file=sys.stderr)
        return list(all_topics)

    lab_config = config.get(lab_key, {})
    if not isinstance(lab_config, dict):
        return list(all_topics)

    if lab_config.get("enabled", True) is False:
        return []

    topic_flags = lab_config.get("topics", {}) or {}
    return [t for t in all_topics if topic_flags.get(t.id, True) is not False]
