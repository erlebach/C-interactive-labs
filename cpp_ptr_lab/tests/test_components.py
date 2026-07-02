"""Tests for the interactive component library (cpp_ptr_lab.components).

TDD: every RED test here precedes the implementation of the component it covers
(applies memory rule feedback/testing.md, overriding OpenSpec's tests-last
ordering). Shared invariants (purity, id-namespacing, CSS-id-safety, zero-JS,
focus-preservation, color-not-alone) are parametrized across every registered
component.
"""

from __future__ import annotations

import re

import pytest

from cpp_ptr_lab.html_renderer import SEMANTIC_PALETTE, _CSS, _BOX_STROKE, svg_renderer
from cpp_ptr_lab import components as C


# ---------------------------------------------------------------------------
# WCAG contrast helper (computed, not trusted from a comment)
# ---------------------------------------------------------------------------


def _luminance(hexv: str) -> float:
    hexv = hexv.lstrip("#")
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    R, G, B = lin(r), lin(g), lin(b)
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def _contrast(fg: str, bg: str) -> float:
    l1, l2 = _luminance(fg), _luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------------------
# 1.2 — semantic color tokens (static-html-renderer delta)
# ---------------------------------------------------------------------------

ROLES = ["addr", "val", "type", "const", "err"]
PAGE_BG = "#ffffff"


class TestSemanticTokens:
    def test_all_roles_present(self):
        for role in ROLES:
            assert role in SEMANTIC_PALETTE, f"missing palette role: {role}"

    def test_tokens_defined_in_root(self):
        for role in ROLES:
            assert f"--c-{role}:" in _CSS, f"--c-{role} not declared in :root"

    def test_css_value_matches_palette(self):
        for role in ROLES:
            hexv = SEMANTIC_PALETTE[role]
            assert f"--c-{role}: {hexv};" in _CSS

    def test_each_token_meets_aa_contrast(self):
        for role in ROLES:
            ratio = _contrast(SEMANTIC_PALETTE[role], PAGE_BG)
            assert ratio >= 4.5, f"{role}={SEMANTIC_PALETTE[role]} only {ratio:.2f}:1"

    def test_svg_palette_resolves_to_same_values(self):
        # The SVG address color is the same value as the --c-addr token.
        assert _BOX_STROKE == SEMANTIC_PALETTE["addr"]
        out = svg_renderer({
            "type": "raw", "ptr_addr": "0x1", "target_addr": "0x2", "target_val": "5",
        })
        assert SEMANTIC_PALETTE["addr"] in out


# ---------------------------------------------------------------------------
# 2.x — shared-invariant registry (Task 2.7: grows as components land)
# ---------------------------------------------------------------------------

PD = {"type": "raw", "ptr_addr": "0x16b1", "target_addr": "0x16b9", "target_val": "42"}


class Comp:
    """A registered component: how to render it + which invariants apply."""

    def __init__(self, name, render, *, in_page=True, hidden_inputs=False, color_state=False):
        self.name = name
        self.render = render
        self.in_page = in_page          # participates in two-instance dedup
        self.hidden_inputs = hidden_inputs
        self.color_state = color_state


REGISTRY = [
    Comp("page_shell", lambda c: C.page_shell(c, "<p>Body</p>", title="T"), in_page=False),
    Comp("color_legend", lambda c: C.color_legend(c), color_state=True),
    Comp("callout_note", lambda c: C.callout_note(c, "Pointers store addresses."), color_state=True),
    Comp("memory_diagram", lambda c: C.memory_diagram(c, PD)),
    Comp("hover_link_diagram", lambda c: C.hover_link_diagram(c, PD)),
    Comp("before_after_toggle", lambda c: C.before_after_toggle(c, "<svg>A</svg>", "<svg>B</svg>"),
         hidden_inputs=True),
    Comp("predict_reveal_quiz",
         lambda c: C.predict_reveal_quiz(c, "What prints?", ["1", "2", "3"], 1, explanation="prints 2"),
         hidden_inputs=True, color_state=True),
    Comp("compile_status_badge", lambda c: C.compile_status_badge(c, False), color_state=True),
    Comp("output_console", lambda c: C.output_console(c, "boom", error=True), color_state=True),
    Comp("byte_grid", lambda c: C.byte_grid(c, ["c0", "9a", "b1", "16", "00", "00", "00", "00"])),
    Comp("code_line_link",
         lambda c: C.code_line_link(c, [("int* p = ptr;", "p"), ("return 0;", None)], ptrdata=PD)),
    Comp("variant_tabs", lambda c: C.variant_tabs(c, [("int", "<p>i</p>"), ("double", "<p>d</p>")]),
         hidden_inputs=True),
    Comp("code_diagram_panel", lambda c: C.code_diagram_panel(c, "<pre>code</pre>", "<svg></svg>")),
    Comp("stacked_subcases", lambda c: C.stacked_subcases(c, [("Case A", "<p>a</p>"), ("Case B", "<p>b</p>")])),
    Comp("progressive_steps", lambda c: C.progressive_steps(c, [("Step 1", "<p>1</p>"), ("Step 2", "<p>2</p>")])),
]

ALL = [pytest.param(c, id=c.name) for c in REGISTRY]
IN_PAGE = [pytest.param(c, id=c.name) for c in REGISTRY if c.in_page]
HIDDEN = [pytest.param(c, id=c.name) for c in REGISTRY if c.hidden_inputs]
COLORED = [pytest.param(c, id=c.name) for c in REGISTRY if c.color_state]


def _ids(frag):
    return re.findall(r'\bid="([^"]+)"', frag)


def _id_like_attrs(frag):
    """All id/for/name attribute values that must be CSS-id-safe."""
    out = []
    for attr in ("id", "for", "name"):
        out += re.findall(rf'\b{attr}="([^"]+)"', frag)
    return out


class TestInvariantPurity:
    @pytest.mark.parametrize("comp", ALL)
    def test_returns_string(self, comp):
        assert isinstance(comp.render("demo"), str)

    @pytest.mark.parametrize("comp", ALL)
    def test_deterministic(self, comp):
        assert comp.render("demo") == comp.render("demo")


class TestInvariantNamespacing:
    @pytest.mark.parametrize("comp", IN_PAGE)
    def test_two_instances_no_dup_ids(self, comp):
        doc = comp.render("one") + comp.render("two")
        ids = _ids(doc)
        assert len(ids) == len(set(ids)), f"dup ids: {[i for i in ids if ids.count(i) > 1]}"

    @pytest.mark.parametrize("comp", IN_PAGE)
    def test_emitted_ids_contain_comp_id(self, comp):
        ids = _ids(comp.render("zappa"))
        if ids:  # components that emit ids must namespace them
            assert any("zappa" in i for i in ids)


class TestInvariantCssIdSafety:
    @pytest.mark.parametrize("comp", IN_PAGE)
    def test_punctuated_comp_id_yields_safe_ids(self, comp):
        frag = comp.render("a (b), *c / d")
        bad = [v for v in _id_like_attrs(frag) if not re.fullmatch(r"[A-Za-z0-9_-]+", v)]
        assert not bad, f"CSS-unsafe id/for/name: {bad}"


class TestInvariantZeroJsZeroNetwork:
    @pytest.mark.parametrize("comp", ALL)
    def test_no_script(self, comp):
        assert "<script" not in comp.render("demo").lower()

    @pytest.mark.parametrize("comp", ALL)
    def test_no_external_reference(self, comp):
        frag = comp.render("demo")
        assert "http://" not in frag and "https://" not in frag
        assert "src=" not in frag


class TestInvariantFocusPreservation:
    @pytest.mark.parametrize("comp", HIDDEN)
    def test_state_driving_inputs_use_clip_not_display_none(self, comp):
        frag = comp.render("demo")
        radios = re.findall(r'<input[^>]*type="(?:radio|checkbox)"[^>]*>', frag)
        assert radios, "component flagged hidden_inputs emitted no radio/checkbox"
        for r in radios:
            flat = r.replace(" ", "")
            assert "clip:" in r, f"radio not clip-hidden: {r}"
            assert "display:none" not in flat, f"radio uses display:none: {r}"
            assert "visibility:hidden" not in flat, f"radio uses visibility:hidden: {r}"


class TestInvariantColorNotAlone:
    @pytest.mark.parametrize("comp", COLORED)
    def test_colored_state_has_border_cue(self, comp):
        frag = comp.render("demo")
        assert "border" in frag.lower(), "colored component lacks a border/non-color cue"


# ---------------------------------------------------------------------------
# 3.x — Chrome components
# ---------------------------------------------------------------------------


class TestPageShell:
    def _frag(self):
        return C.page_shell("shell", "<p id='content'>hi</p>", title="My Demo")

    def test_declares_lang(self):
        assert 'lang="en"' in self._frag()

    def test_skip_link_targets_existing_main(self):
        frag = self._frag()
        assert 'href="#main"' in frag
        assert 'id="main"' in frag

    def test_has_main_landmark(self):
        assert "<main" in self._frag()

    def test_css_inlined(self):
        assert "<style" in self._frag()

    def test_no_external_refs(self):
        frag = self._frag()
        assert "<script" not in frag and "http" not in frag and "src=" not in frag

    def test_title_present(self):
        assert "My Demo" in self._frag()

    def test_body_content_present(self):
        assert "hi" in self._frag()

    def test_document_flow_no_viewport_lock(self):
        # Document pages must NOT opt into the legacy DPG viewport lock: the body
        # is plain document flow (no `lab-shell` class, no inline height/overflow
        # workaround). The shared stylesheet may still define `body.lab-shell`.
        body_tag = re.search(r"<body[^>]*>", self._frag()).group(0)
        assert body_tag == "<body>"


class TestColorLegend:
    def test_each_role_named_in_text(self):
        frag = C.color_legend("lg")
        for word in ("address", "value", "type", "const", "error"):
            assert word in frag.lower(), f"missing role name: {word}"

    def test_each_role_has_swatch_token(self):
        frag = C.color_legend("lg")
        for role in ROLES:
            assert f"--c-{role}" in frag, f"missing swatch for {role}"


class TestCalloutNote:
    def test_is_semantic_aside(self):
        assert "<aside" in C.callout_note("n", "remember this")

    def test_has_text_label(self):
        assert "Note" in C.callout_note("n", "remember this")

    def test_has_border_cue(self):
        assert "border" in C.callout_note("n", "remember this").lower()

    def test_content_present(self):
        assert "remember this" in C.callout_note("n", "remember this")


# ---------------------------------------------------------------------------
# 4.x — memory-diagram
# ---------------------------------------------------------------------------


class TestMemoryDiagram:
    def test_role_img(self):
        assert 'role="img"' in C.memory_diagram("d", PD)

    def test_title_and_desc(self):
        frag = C.memory_diagram("d", PD)
        assert "<title" in frag and "<desc" in frag

    def test_aria_labelledby_references_title_and_desc(self):
        frag = C.memory_diagram("d", PD)
        m = re.search(r'aria-labelledby="([^"]+)"', frag)
        assert m
        for ref in m.group(1).split():
            assert f'id="{ref}"' in frag, f"aria-labelledby ref {ref} has no element"

    def test_desc_narrates_pointer_to_target(self):
        frag = C.memory_diagram("d", PD).lower()
        assert "42" in frag  # the target value is narrated
        assert "0x16b9" in frag

    def test_missing_keys_degrade_to_question_mark(self):
        frag = C.memory_diagram("d", {"type": "raw"})  # no addresses
        assert "?" in frag

    def test_missing_keys_does_not_raise(self):
        C.memory_diagram("d", {"type": "raw"})
        C.memory_diagram("d", None)


# ---------------------------------------------------------------------------
# 5.x — high-value interactions
# ---------------------------------------------------------------------------


class TestHoverLinkDiagram:
    def _frag(self):
        return C.hover_link_diagram("hl", PD)

    def test_uses_hover_and_focus(self):
        frag = self._frag()
        assert ":hover" in frag and ":focus" in frag

    def test_non_color_cue_stroke_width(self):
        assert "stroke-width" in self._frag()

    def test_no_js(self):
        assert "<script" not in self._frag()

    def test_namespaced(self):
        assert "hl" in self._frag()


class TestBeforeAfterToggle:
    def _frag(self):
        return C.before_after_toggle("ba", "<svg>BEFORE</svg>", "<svg>AFTER</svg>")

    def test_two_radios(self):
        assert self._frag().count('type="radio"') == 2

    def test_both_states_baked(self):
        frag = self._frag()
        assert "BEFORE" in frag and "AFTER" in frag

    def test_checked_rule_present(self):
        assert ":checked" in self._frag()

    def test_first_option_checked(self):
        frag = self._frag()
        first = re.search(r'<input[^>]*type="radio"[^>]*>', frag)
        assert first and "checked" in first.group(0)


class TestPredictRevealQuiz:
    def _frag(self):
        return C.predict_reveal_quiz("q", "What prints?", ["1", "2", "3"], 1, explanation="prints 2")

    def test_one_radio_per_option(self):
        assert self._frag().count('type="radio"') == 3

    def test_checked_reveals_feedback(self):
        assert ":checked" in self._frag()

    def test_correct_and_incorrect_icons(self):
        frag = self._frag()
        assert "✓" in frag and "✗" in frag

    def test_real_answer_baked(self):
        assert "prints 2" in self._frag()

    def test_no_js(self):
        assert "<script" not in self._frag()


# ---------------------------------------------------------------------------
# 6.x — output + status
# ---------------------------------------------------------------------------


class TestCompileStatusBadge:
    def test_fail_shows_text(self):
        assert "fail" in C.compile_status_badge("b", False).lower()

    def test_pass_shows_text(self):
        frag = C.compile_status_badge("b", True).lower()
        assert "compil" in frag

    def test_fail_has_icon(self):
        assert "✗" in C.compile_status_badge("b", False)

    def test_pass_has_icon(self):
        assert "✓" in C.compile_status_badge("b", True)

    def test_has_border_cue(self):
        assert "border" in C.compile_status_badge("b", False).lower()


class TestOutputConsole:
    def test_monospaced_block(self):
        frag = C.output_console("o", "hello\nworld")
        assert "<pre" in frag or "monospace" in frag

    def test_output_verbatim(self):
        assert "hello" in C.output_console("o", "hello world")

    def test_error_variant_text_and_border(self):
        frag = C.output_console("o", "boom", error=True)
        assert "error" in frag.lower()
        assert "border" in frag.lower()

    def test_error_variant_distinct_class(self):
        ok = C.output_console("o", "x", error=False)
        err = C.output_console("o", "x", error=True)
        assert ok != err

    def test_output_wrapped_in_samp_not_bare_pre(self):
        # SIA-R79 / WCAG 1.4.12: a <pre> needs a semantic child. Program output is
        # sample output -> <samp>. No bare <pre> may be emitted.
        frag = C.output_console("o", "PTRDATA: type=raw\nMEMBYTES: 18")
        assert re.search(r"<pre[^>]*>\s*<samp>", frag) and "</samp></pre>" in frag
        assert not re.search(r"<pre\b[^>]*>(?!\s*<(?:code|samp)\b)", frag)


# ---------------------------------------------------------------------------
# 7.x — secondary diagram interactions
# ---------------------------------------------------------------------------


class TestByteGrid:
    def _frag(self):
        return C.byte_grid("bg", ["c0", "9a", "b1", "16", "00", "00", "00", "00"], caption="ptr bytes")

    def test_each_byte_present(self):
        frag = self._frag()
        for b in ("c0", "9a", "b1", "16"):
            assert b in frag

    def test_has_accessible_caption(self):
        frag = self._frag()
        assert "<caption" in frag or "ptr bytes" in frag

    def test_byte_cells_are_readable_size(self):
        # Regression: byte-grid cells were 13px — the smallest text on the page
        # and cramped/hard to read (user report). Keep them at a readable size.
        rule = re.search(r"\.byte-grid td, \.byte-grid th \{.*?\}",
                         C.COMPONENT_CSS, re.DOTALL)
        assert rule, "byte-grid cell rule not found"
        assert "13px" not in rule.group(0)
        assert "15px" in rule.group(0)

    def test_eight_cells(self):
        # eight byte values -> eight labelled cells
        frag = self._frag()
        assert frag.count("byte-cell") >= 8 or frag.count("<td") >= 8


class TestCodeLineLink:
    def _frag(self):
        return C.code_line_link("cl", [("int* p = ptr;", "p"), ("return 0;", None)], ptrdata=PD)

    def test_hover_and_focus_rules(self):
        frag = self._frag()
        assert ":hover" in frag and ":focus" in frag

    def test_shared_namespaced_link_id(self):
        frag = self._frag()
        # the link key 'p' is namespaced by comp id and appears on both sides
        assert "cl" in frag

    def test_no_js(self):
        assert "<script" not in self._frag()

    def test_code_present(self):
        assert "int* p = ptr;" in self._frag()

    def test_linked_line_and_diagram_share_a_parent(self):
        # The `~` highlight rule only matches if the linked line and the diagram
        # box are siblings under one parent. Parse the real structure so a
        # broken combinator (e.g. the line trapped inside <pre>) can't slip past.
        from html.parser import HTMLParser

        class _P(HTMLParser):
            VOID = {"input", "img", "br", "hr", "meta", "link", "source",
                    "col", "area", "base", "embed", "param", "track", "wbr"}

            def __init__(self):
                super().__init__()
                self.stack = []
                self.records = []  # (attrs, parent_attrs)

            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                self.records.append((a, self.stack[-1] if self.stack else None))
                if tag not in self.VOID:
                    self.stack.append(a)

            def handle_endtag(self, tag):
                if self.stack:
                    self.stack.pop()

        parser = _P()
        parser.feed(self._frag())
        line_parent = next(par for a, par in parser.records if "ln-p" in a.get("class", ""))
        diag_parent = next(par for a, par in parser.records if a.get("class", "") == "cll-diagram")
        assert line_parent is not None and diag_parent is not None
        # both must be direct children of the namespaced container (#cl)
        assert line_parent.get("id") == "cl"
        assert diag_parent.get("id") == "cl"


# ---------------------------------------------------------------------------
# 8.x — layout + stepped
# ---------------------------------------------------------------------------


class TestVariantTabs:
    def _frag(self):
        return C.variant_tabs("vt", [("int", "<p>i</p>"), ("double", "<p>d</p>"), ("float", "<p>f</p>")])

    def test_one_radio_per_panel(self):
        assert self._frag().count('type="radio"') == 3

    def test_exactly_one_checked(self):
        assert self._frag().count(" checked") == 1

    def test_checked_show_rule(self):
        assert ":checked" in self._frag()

    def test_focus_visible_outline(self):
        assert ":focus-visible" in self._frag()

    def test_panels_present(self):
        frag = self._frag()
        assert "<p>i</p>" in frag and "<p>d</p>" in frag and "<p>f</p>" in frag


class TestCodeDiagramPanel:
    def _frag(self):
        return C.code_diagram_panel("cd", "<pre>code here</pre>", "<svg>diagram</svg>")

    def test_both_columns_present(self):
        frag = self._frag()
        assert "code here" in frag and "diagram" in frag

    def test_code_column_scrolls(self):
        assert "overflow" in self._frag()

    def test_reflow_breakpoint(self):
        assert "@media" in self._frag()


class TestStackedSubcases:
    def _frag(self):
        return C.stacked_subcases("sc", [("Case A", "<p>a</p>"), ("Case B", "<p>b</p>")])

    def test_all_subcases_present(self):
        frag = self._frag()
        assert "Case A" in frag and "Case B" in frag
        assert "<p>a</p>" in frag and "<p>b</p>" in frag

    def test_panel_scrolls(self):
        assert "overflow" in self._frag()


class TestProgressiveSteps:
    def _frag(self):
        return C.progressive_steps("ps", [("Step 1", "<p>one</p>"), ("Step 2", "<p>two</p>")])

    def test_details_per_step(self):
        assert self._frag().count("<details") == 2

    def test_summary_present(self):
        frag = self._frag()
        assert "<summary" in frag
        assert "Step 1" in frag and "Step 2" in frag

    def test_content_present(self):
        frag = self._frag()
        assert "one" in frag and "two" in frag

    def test_no_js(self):
        assert "<script" not in self._frag()
