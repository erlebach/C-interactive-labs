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


def test_skill_md_frontmatter():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---"), "SKILL.md must start with YAML frontmatter"
    fm = yaml.safe_load(text.split("---", 2)[1])
    assert fm["name"] == "demonstration-builder"
    assert "demonstration" in fm["description"].lower()


def test_bundled_engine_is_self_contained():
    """The skill must carry a complete copy of the engine so it works in any project."""
    eng = SKILL / "engine"
    assert (eng / "build_labs.sh").exists(), "engine/build_labs.sh missing"
    assert (eng / "requirements.txt").exists(), "engine/requirements.txt missing"

    pkg = eng / "cpp_labs"
    for mod in (
        "__init__.py", "build_html.py", "code_generator.py", "compiler_runner.py",
        "components.py", "html_renderer.py", "topic_yaml.py",
    ):
        assert (pkg / mod).exists(), f"bundled engine missing cpp_labs/{mod}"
    for mod in ("__init__.py", "render_page.py", "interface_catalog.py"):
        assert (pkg / "yaml_engine" / mod).exists(), \
            f"bundled engine missing cpp_labs/yaml_engine/{mod}"

    # Runtime assets components.py reads at import time (else import blows up).
    vendor = pkg / "vendor" / "highlightjs"
    for asset in ("highlight.min.js", "atom-one-dark.min.css"):
        assert (vendor / asset).exists(), f"bundled engine missing vendor asset {asset}"


def test_bundled_engine_matches_source():
    """Vendored copy must not silently drift from the repo's live engine."""
    pkg = SKILL / "engine" / "cpp_labs"
    src = Path(__file__).resolve().parents[1]  # the repo cpp_labs/
    for rel in (
        "build_html.py", "code_generator.py", "compiler_runner.py",
        "components.py", "html_renderer.py", "topic_yaml.py",
        "yaml_engine/render_page.py", "yaml_engine/interface_catalog.py",
    ):
        assert (pkg / rel).read_bytes() == (src / rel).read_bytes(), \
            f"bundled engine/cpp_labs/{rel} drifted from source cpp_labs/{rel}"


def test_engine_scripts_present_and_executable():
    for name in ("install_engine.sh", "sync_engine.sh", "scaffold_subject.sh"):
        p = SKILL / "scripts" / name
        assert p.exists(), f"scripts/{name} missing"
        assert p.stat().st_mode & 0o111, f"scripts/{name} is not executable"


def test_install_guide_present():
    text = (SKILL / "INSTALL.md").read_text(encoding="utf-8").strip()
    assert text, "INSTALL.md is missing or empty"
    assert "install_engine.sh" in text, "INSTALL.md should tell the user to install the engine"


def test_no_machine_specific_absolute_paths():
    """The skill is relocatable: no hard-coded per-machine paths in any text file."""
    import re
    bad = re.compile(r"/Users/|/home/[a-z]|/opt/miniconda|/private/var|/var/folders")
    offenders = []
    for p in SKILL.rglob("*"):
        if not p.is_file() or p.suffix in {".js", ".css", ".png", ".pyc"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if bad.search(text):
            offenders.append(str(p.relative_to(SKILL)))
    assert not offenders, f"machine-specific absolute paths found in: {offenders}"
