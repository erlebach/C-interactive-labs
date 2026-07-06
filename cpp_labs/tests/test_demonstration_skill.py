from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "demonstration-builder"


def test_template_skeletons_parse():
    topic = yaml.safe_load((SKILL / "templates" / "topic.topic.yaml").read_text())
    for k in ("id", "name", "template", "explanation", "group"):
        assert k in topic, f"template topic missing required key {k!r}"

    demo = yaml.safe_load((SKILL / "templates" / "demo.demo.yaml").read_text())
    assert "bake" in demo and "blocks" in demo

    layout = yaml.safe_load((SKILL / "templates" / "layout.rail.yaml").read_text())
    assert layout.get("style") and "demos" in layout


def test_reference_files_present():
    for f in ("PATTERN.md", "DIAGRAMS.md", "CHECKLIST.md"):
        assert (SKILL / "reference" / f).read_text(encoding="utf-8").strip(), \
            f"reference/{f} is missing or empty"
