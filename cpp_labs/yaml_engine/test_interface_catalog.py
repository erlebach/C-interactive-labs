"""Tests for the interface-element catalog generator.

The catalog ``usage/INTERFACE_ELEMENTS.md`` is *generated* from the engine's
dispatch tables (never hand-edited), so it can never drift from the code. These
tests are that drift guard:

1. **Completeness** — every author-usable block keyword the engine dispatches
   (``_DISPATCH`` + ``_BUILDERS``) appears in the generated catalog.
2. **Freshness** — the committed ``usage/INTERFACE_ELEMENTS.md`` is byte-identical
   to a fresh generation, so adding an element without regenerating fails CI.

TDD: RED before GREEN (feedback/testing.md).
"""

from __future__ import annotations

from cpp_labs.yaml_engine import interface_catalog as IC
from cpp_labs.yaml_engine import render_page as R


class TestCatalogCompleteness:
    """Every keyword the engine will dispatch must be documented."""

    def test_every_block_keyword_appears(self) -> None:
        text = IC.generate_catalog()
        for keyword in list(R._DISPATCH) + list(R._BUILDERS):
            assert f"`{keyword}`" in text, (
                f"block keyword {keyword!r} is dispatched by the engine but "
                f"missing from the generated catalog")


class TestElementTiers:
    """Every author-usable element must carry a reuse tier, shown in the table."""

    def test_every_block_keyword_has_a_tier(self) -> None:
        for keyword in list(R._DISPATCH) + list(R._BUILDERS):
            assert keyword in IC._TIER, (
                f"block keyword {keyword!r} has no reuse tier in _TIER — a new "
                f"element must be classified generic / code / cpp-memory")

    def test_catalog_shows_a_tier_column(self) -> None:
        assert "| tier |" in IC.generate_catalog()


class TestCatalogFreshness:
    """The committed markdown file must match the generator exactly."""

    def test_committed_file_matches_generator(self) -> None:
        text = IC.generate_catalog()
        path = IC.CATALOG_PATH
        assert path.exists(), (
            f"{path} is missing — regenerate with "
            f"`python -m cpp_labs.yaml_engine.interface_catalog`")
        assert path.read_text(encoding="utf-8") == text, (
            "usage/INTERFACE_ELEMENTS.md is stale — regenerate with "
            "`python -m cpp_labs.yaml_engine.interface_catalog`")
