"""Tests for cpp_labs.html_renderer (RED phase — all will fail until implemented)."""

from __future__ import annotations

import re

import pytest

from cpp_labs.html_renderer import assemble_page, render_fragment, svg_renderer, _marker_defs, _arrow_v, _vbox, _LH, _stack_svg
from cpp_labs.code_generator import ControlDef, TopicTemplate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_topic(tid: str = "basic_ptr", controls=None) -> TopicTemplate:
    return TopicTemplate(
        id=tid,
        name="Test Topic",
        template="",
        controls=controls or [],
        explanation="",
        group="Core",
    )


def _raw_pd(**kwargs) -> dict:
    base = {
        "type": "raw",
        "ptr_addr": "0x16b949ac0",
        "target_addr": "0x16b949ac8",
        "target_val": "42",
    }
    base.update(kwargs)
    return base


def _variant(label: str = "int", failed: bool = False, **kwargs) -> dict:
    return {
        "label": label,
        "svg": svg_renderer(None if failed else _raw_pd()),
        "source": "int main(){}",
        "stdout": "",
        "membytes": "n/a",
        "failed": failed,
        "stderr": "error: blah" if failed else "",
        **kwargs,
    }


# ---------------------------------------------------------------------------
# svg_renderer — raw pointer
# ---------------------------------------------------------------------------


class TestSvgRendererRaw:
    def test_returns_string(self):
        out = svg_renderer(_raw_pd())
        assert isinstance(out, str)

    def test_contains_two_rects(self):
        out = svg_renderer(_raw_pd())
        assert out.count("<rect") == 2

    def test_contains_arrow_line(self):
        out = svg_renderer(_raw_pd())
        assert "<line" in out or "<polygon" in out

    def test_contains_ptr_address(self):
        out = svg_renderer(_raw_pd())
        assert "0x16b949ac0" in out

    def test_contains_target_address(self):
        out = svg_renderer(_raw_pd())
        assert "0x16b949ac8" in out

    def test_contains_value(self):
        out = svg_renderer(_raw_pd())
        assert "42" in out

    def test_has_title_and_desc(self):
        out = svg_renderer(_raw_pd())
        assert "<title" in out
        assert "<desc" in out

    def test_has_role_img(self):
        out = svg_renderer(_raw_pd())
        assert 'role="img"' in out

    def test_has_viewbox(self):
        out = svg_renderer(_raw_pd())
        assert 'viewBox="0 0 500 160"' in out

    def test_aria_labelledby_references_title_and_desc(self):
        out = svg_renderer(_raw_pd())
        assert "aria-labelledby" in out


# ---------------------------------------------------------------------------
# svg_renderer — null pointer
# ---------------------------------------------------------------------------


class TestSvgRendererNull:
    def test_null_type_shows_null_label(self):
        pd = {"type": "null", "ptr_addr": "0x0"}
        out = svg_renderer(pd)
        assert "NULL" in out

    def test_null_has_role_img(self):
        pd = {"type": "null", "ptr_addr": "0x0"}
        out = svg_renderer(pd)
        assert 'role="img"' in out


# ---------------------------------------------------------------------------
# svg_renderer — missing keys degrade safely
# ---------------------------------------------------------------------------


class TestSvgRendererMissingKeys:
    def test_missing_keys_returns_svg(self):
        out = svg_renderer({"type": "raw"})
        assert "<svg" in out

    def test_missing_keys_uses_placeholder(self):
        out = svg_renderer({"type": "raw"})
        assert "?" in out

    def test_does_not_raise(self):
        svg_renderer({"type": "raw"})  # must not raise


# ---------------------------------------------------------------------------
# svg_renderer — smart-pointer dispatch
# ---------------------------------------------------------------------------


class TestSvgRendererSmartPtrs:
    def test_unique_dispatched(self):
        pd = {
            "type": "unique",
            "ptr_addr": "0xabc",
            "target_addr": "0xdef",
            "val": "7",
            "is_null": "0",
        }
        out = svg_renderer(pd)
        assert "<svg" in out
        assert "unique" in out.lower()

    def test_shared_dispatched(self):
        pd = {
            "type": "shared",
            "ptr_addr": "0xabc",
            "target_addr": "0xdef",
            "val": "7",
            "use_count": "1",
        }
        out = svg_renderer(pd)
        assert "<svg" in out
        assert "shared" in out.lower()

    def test_weak_dispatched(self):
        pd = {
            "type": "weak",
            "ptr_addr": "0xabc",
            "expired": "0",
            "use_count": "1",
        }
        out = svg_renderer(pd)
        assert "<svg" in out
        assert "weak" in out.lower()


# ---------------------------------------------------------------------------
# render_fragment — multiple variants
# ---------------------------------------------------------------------------


def _dropdown(cid: str, options: list[str]) -> ControlDef:
    return ControlDef(
        id=cid,
        label=cid.title(),
        kind="dropdown",
        options=options,
        default=options[0],
        placeholder=f"<<{cid}>>",
    )


class TestRenderFragmentMultiVariant:
    def _fragment(self, tid="basic_ptr", options=None):
        options = options or ["int", "double", "float"]
        topic = _make_topic(tid, controls=[_dropdown("type", options)])
        variants = [{"label": o, "svg": "", "source": "", "stdout": "", "membytes": "n/a", "failed": False, "stderr": ""} for o in options]
        return render_fragment(topic, variants)

    def test_one_radio_per_variant(self):
        frag = self._fragment()
        assert frag.count('type="radio"') == 3

    def test_one_panel_per_variant(self):
        frag = self._fragment()
        assert frag.count('class="panel"') == 3 or frag.count('id="basic_ptr-panel-') == 3

    def test_first_variant_checked(self):
        frag = self._fragment()
        # The first radio must carry 'checked'
        first_radio_match = re.search(r'<input[^>]*type="radio"[^>]*/?>|<input[^>]*type="radio"[^>]*>', frag)
        assert first_radio_match is not None
        assert "checked" in first_radio_match.group(0)

    def test_ids_namespaced_by_topic_id(self):
        frag = self._fragment(tid="basic_ptr")
        assert "basic_ptr-" in frag

    def test_no_cross_contamination_between_topics(self):
        topic_a = _make_topic("alpha", controls=[_dropdown("type", ["x", "y"])])
        topic_b = _make_topic("beta", controls=[_dropdown("type", ["x", "y"])])
        vs = [{"label": o, "svg": "", "source": "", "stdout": "", "membytes": "n/a", "failed": False, "stderr": ""} for o in ["x", "y"]]
        frag_a = render_fragment(topic_a, vs)
        frag_b = render_fragment(topic_b, vs)
        # Extract all id= values from each fragment
        ids_a = set(re.findall(r'id="([^"]+)"', frag_a))
        ids_b = set(re.findall(r'id="([^"]+)"', frag_b))
        assert ids_a.isdisjoint(ids_b), f"Shared ids: {ids_a & ids_b}"

    def test_output_is_section(self):
        frag = self._fragment()
        assert "<section" in frag

    def test_ids_are_css_safe_with_punctuated_labels(self):
        # Variant labels with parens/commas (e.g. const taxonomy) must still
        # yield ids usable in an unescaped CSS `#id` selector. Raw '(', ')',
        # ',' silently break the `:checked ~` rule, leaving the panel empty.
        labels = [
            "int* (pointer and value both mutable)",
            "const int* (value immutable, pointer mutable)",
        ]
        frag = self._fragment(tid="const_taxonomy", options=labels)
        ids = re.findall(r'id="([^"]+)"', frag)
        bad = [i for i in ids if not re.fullmatch(r"[A-Za-z0-9_-]+", i)]
        assert not bad, f"CSS-unsafe ids: {bad}"


class TestRenderFragmentMultiCase:
    def _case(self, label, failed=False):
        return {
            "label": label,
            "source": f"int main(){{ /* {label} */ }}",
            "stdout": f"ran: {label}",
            "membytes": "n/a",
            "failed": failed,
            "stderr": "error: read-only" if failed else "",
            "ptrdata": None if failed else _raw_pd(),
        }

    def _fragment(self):
        topic = _make_topic("const_taxonomy", controls=[_dropdown("type", ["a", "b"])])
        variants = [
            {"label": "a", "cases": [self._case("Write *ptr"), self._case("Rebind ptr", failed=True)]},
            {"label": "b", "cases": [self._case("Write *ptr", failed=True), self._case("Rebind ptr")]},
        ]
        return render_fragment(topic, variants)

    def test_case_labels_present(self):
        frag = self._fragment()
        assert "Write *ptr" in frag
        assert "Rebind ptr" in frag

    def test_one_code_block_per_case(self):
        frag = self._fragment()
        # 2 variants x 2 cases = 4 code blocks
        assert frag.count("<pre><code>") == 4

    def test_failing_case_shows_compile_failed_and_stderr(self):
        frag = self._fragment()
        assert "Compile failed" in frag
        assert "read-only" in frag

    def test_no_bare_pre_stderr_wrapped_in_samp(self):
        # Compiler stderr is program output -> belongs in <samp> (SIA-R79), not a
        # bare <pre>. Every <pre> must carry a semantic child (<code> or <samp>).
        frag = self._fragment()
        for m in re.finditer(r"<pre\b[^>]*>", frag):
            after = frag[m.end():m.end() + 6]
            assert after.startswith("<code") or after.startswith("<samp"), \
                f"bare <pre>: {m.group(0)!r} -> {after!r}"
        assert "<samp>error: read-only</samp>" in frag

    def test_passing_case_shows_stdout(self):
        frag = self._fragment()
        assert "ran: Write *ptr" in frag

    def test_no_duplicate_ids(self):
        frag = self._fragment()
        ids = re.findall(r'id="([^"]+)"', frag)
        assert len(ids) == len(set(ids)), f"dup ids: {[i for i in ids if ids.count(i) > 1]}"

    def test_multicase_panel_scrolls(self):
        # Stacked sub-cases must not be clipped: the .panel that holds them
        # scrolls vertically (regression: multi-case lost scrolling).
        page = assemble_page([self._fragment()])
        m = re.search(r"\.panel\s*\{([^}]*)\}", page)
        assert m, ".panel CSS rule missing"
        assert "overflow-y: auto" in m.group(1), f"no vertical scroll on .panel: {m.group(1)!r}"

    def test_failed_case_out_box_has_error_border_class(self):
        # _fragment has exactly 2 failing sub-cases (one per variant); only
        # those compiler-output boxes get the error-border modifier.
        frag = self._fragment()
        assert frag.count("out--err") == 2

    def test_error_border_css_defines_red_border(self):
        # The .out--err rule lives in the page-level inlined CSS (assemble_page),
        # while the marker class is applied on the box inside the fragment.
        page = assemble_page([self._fragment()])
        m = re.search(r"\.out--err\s*\{([^}]*)\}", page)
        assert m, ".out--err CSS rule missing"
        rule = m.group(1)
        assert "border" in rule
        assert re.search(r"#(c2|b0|8b|a0|d0|cc)0{0,2}0", rule) or "var(--err" in rule, \
            f"no red border colour in: {rule!r}"


class TestNoDiagramLeavesEmptySpace:
    def _variants(self):
        return [
            {"label": "ok", "source": "x", "stdout": "ran", "membytes": "n/a",
             "failed": False, "stderr": "", "ptrdata": _raw_pd()},
            {"label": "bad", "source": "x", "stdout": "", "membytes": "n/a",
             "failed": True, "stderr": "err: boom", "ptrdata": None},
        ]

    def _fragment(self):
        topic = _make_topic("t", controls=[_dropdown("type", ["ok", "bad"])])
        return render_fragment(topic, self._variants())

    def test_only_diagram_variant_has_svg(self):
        frag = self._fragment()
        assert frag.count("<svg") == 1  # only the variant with ptrdata

    def test_no_placeholder_text_when_no_diagram(self):
        frag = self._fragment()
        assert "no diagram" not in frag

    def test_no_diagram_heading_for_empty_case(self):
        frag = self._fragment()
        assert frag.count("Memory diagram") == 1  # only the diagram variant

    def test_empty_diagram_column_marker_present(self):
        frag = self._fragment()
        assert "diagram-col--empty" in frag


# ---------------------------------------------------------------------------
# render_fragment — single variant
# ---------------------------------------------------------------------------


class TestRenderFragmentSingleVariant:
    def _fragment(self, tid="ref_must_bind"):
        topic = _make_topic(tid, controls=[])
        variants = [{"label": "", "svg": "", "source": "int main(){}", "stdout": "", "membytes": "n/a", "failed": False, "stderr": ""}]
        return render_fragment(topic, variants)

    def test_no_radio_controls_emitted(self):
        frag = self._fragment()
        assert 'type="radio"' not in frag

    def test_panel_content_present(self):
        frag = self._fragment()
        assert "int main(){}" in frag or "<section" in frag


# ---------------------------------------------------------------------------
# assemble_page
# ---------------------------------------------------------------------------


class TestAssemblePage:
    def _two_fragments(self):
        t1 = _make_topic("alpha")
        t2 = _make_topic("beta")
        vs = [{"label": "", "svg": "", "source": "", "stdout": "", "membytes": "n/a", "failed": False, "stderr": ""}]
        return [render_fragment(t1, vs), render_fragment(t2, vs)]

    def test_has_lang_attribute(self):
        page = assemble_page(self._two_fragments())
        assert 'lang="en"' in page or "lang=" in page

    def test_has_skip_link(self):
        page = assemble_page(self._two_fragments())
        assert 'href="#main"' in page or "skip" in page.lower()

    def test_contains_all_fragments(self):
        vs = [{"label": "", "svg": "", "source": "", "stdout": "", "membytes": "n/a", "failed": False, "stderr": ""}]
        t1 = _make_topic("alpha")
        t2 = _make_topic("beta")
        f1 = render_fragment(t1, vs)
        f2 = render_fragment(t2, vs)
        page = assemble_page([f1, f2])
        assert "alpha" in page
        assert "beta" in page

    def test_no_duplicate_ids(self):
        page = assemble_page(self._two_fragments())
        ids = re.findall(r'id="([^"]+)"', page)
        assert len(ids) == len(set(ids)), f"Duplicate ids: {[i for i in ids if ids.count(i) > 1]}"

    def test_css_inlined(self):
        page = assemble_page(self._two_fragments())
        assert "<style" in page

    def test_no_external_resources(self):
        page = assemble_page(self._two_fragments())
        assert "<script src=" not in page
        assert '<link rel="stylesheet"' not in page


# ---------------------------------------------------------------------------
# Task 1.1 — TestAssemblePageTopicNav (RED)
# ---------------------------------------------------------------------------


class TestAssemblePageTopicNav:
    def _two_frags_with_topics(self):
        t1 = _make_topic("basic_ptr")
        t2 = _make_topic("const_taxonomy")
        vs = [_variant()]
        f1 = render_fragment(t1, vs)
        f2 = render_fragment(t2, vs)
        topics = [("basic_ptr", "Basic Pointer"), ("const_taxonomy", "const Taxonomy")]
        return [f1, f2], topics

    def test_topic_radio_inputs_present(self):
        frags, topics = self._two_frags_with_topics()
        page = assemble_page(frags, topics=topics)
        assert 'class="vtopic"' in page

    def test_first_topic_checked(self):
        frags, topics = self._two_frags_with_topics()
        page = assemble_page(frags, topics=topics)
        first_radio = re.search(r'<input[^>]*class="vtopic"[^>]*/?>|<input[^>]*class="vtopic"[^>]*>', page)
        assert first_radio is not None
        assert "checked" in first_radio.group(0)

    def test_topic_panel_divs_present(self):
        frags, topics = self._two_frags_with_topics()
        page = assemble_page(frags, topics=topics)
        assert 'id="tp-basic_ptr"' in page
        assert 'id="tp-const_taxonomy"' in page

    def test_topic_nav_labels_present(self):
        frags, topics = self._two_frags_with_topics()
        page = assemble_page(frags, topics=topics)
        assert 'class="topic-nav"' in page
        assert 'for="t-basic_ptr"' in page
        assert 'for="t-const_taxonomy"' in page

    def test_body_css_height_100vh_scoped_to_lab_shell(self):
        # The DPG-era viewport lock is preserved for the legacy lab page, but is
        # now scoped to `body.lab-shell` (opted into via the body class) rather
        # than the shared base body rule.
        frags, topics = self._two_frags_with_topics()
        page = assemble_page(frags, topics=topics)
        assert 'class="lab-shell"' in page
        css = re.search(r'<style>(.*?)</style>', page, re.DOTALL).group(1).replace(" ", "")
        shell = re.search(r'body\.lab-shell\{[^}]*\}', css)
        assert shell and "height:100vh" in shell.group(0)

    def test_body_css_overflow_hidden_scoped_to_lab_shell(self):
        frags, topics = self._two_frags_with_topics()
        page = assemble_page(frags, topics=topics)
        css = re.search(r'<style>(.*?)</style>', page, re.DOTALL).group(1).replace(" ", "")
        shell = re.search(r'body\.lab-shell\{[^}]*\}', css)
        assert shell and "overflow:hidden" in shell.group(0)

    def test_no_topic_nav_when_topics_none(self):
        t1 = _make_topic("basic_ptr")
        vs = [_variant()]
        f1 = render_fragment(t1, vs)
        page = assemble_page([f1])
        assert 'class="topic-nav"' not in page
        assert 'class="vtopic"' not in page


# ---------------------------------------------------------------------------
# Task 1.2 — TestAssemblePageBackwardCompat (RED)
# ---------------------------------------------------------------------------


class TestAssemblePageBackwardCompat:
    def test_no_topic_nav_without_kwarg(self):
        t1 = _make_topic("alpha")
        vs = [_variant()]
        frag = render_fragment(t1, vs)
        page = assemble_page([frag])
        assert 'class="topic-nav"' not in page

    def test_lang_en_present(self):
        t1 = _make_topic("alpha")
        vs = [_variant()]
        frag = render_fragment(t1, vs)
        page = assemble_page([frag])
        assert 'lang="en"' in page

    def test_skip_link_present(self):
        t1 = _make_topic("alpha")
        vs = [_variant()]
        frag = render_fragment(t1, vs)
        page = assemble_page([frag])
        assert 'href="#main"' in page or 'class="skip"' in page


# ---------------------------------------------------------------------------
# Task 1.3 — TestRenderFragmentLayout (RED)
# ---------------------------------------------------------------------------


class TestRenderFragmentLayout:
    def _multi_variant_frag(self, tid="basic_ptr"):
        topic = _make_topic(tid, controls=[_dropdown("type", ["int", "double", "float"])])
        variants = [_variant(label=o) for o in ["int", "double", "float"]]
        return render_fragment(topic, variants)

    def test_tabs_before_panels(self):
        frag = self._multi_variant_frag()
        tabs_pos = frag.find('class="tabs"')
        panels_pos = frag.find('class="panels"')
        assert tabs_pos != -1 and panels_pos != -1
        assert tabs_pos < panels_pos

    def test_diagram_column_has_flex(self):
        frag = self._multi_variant_frag()
        # The diagram column div must carry display:flex
        assert "display:flex" in frag.replace(" ", "") or "display: flex" in frag


class TestVerticalPrimitives:
    def test_marker_defs_has_marker_and_color(self):
        out = _marker_defs("m1", "#0b5394")
        assert out.startswith("<defs>")
        assert "<marker" in out
        assert 'id="m1"' in out
        assert 'orient="auto-start-reverse"' in out
        assert "#0b5394" in out

    def test_arrow_v_references_marker_and_is_not_forced_horizontal(self):
        out = _arrow_v(50, 20, 50, 120, "#0b5394", "m1")
        assert 'marker-end="url(#m1)"' in out
        # vertical: y1 != y2 (the old _arrow forced mid_y = y1)
        assert 'y1="20"' in out and 'y2="120"' in out

    def test_vbox_height_scales_with_line_count(self):
        svg2, h2 = _vbox(10, 10, 160, [("ptr", "#1a1a1a"), ("0xabc", "#555555")], "#0b5394")
        svg3, h3 = _vbox(10, 10, 160,
                         [("a", "#1a1a1a"), ("b", "#555"), ("c", "#555")], "#0b5394")
        assert h3 == h2 + _LH
        assert 'font-size="14"' in svg2      # matches code panel
        assert "<rect" in svg2 and "ptr" in svg2


# ---------------------------------------------------------------------------
# _stack_svg tests
# ---------------------------------------------------------------------------

def _box(lines, stroke="#0b5394"):
    return {"lines": lines, "stroke": stroke}


class TestStackSvg:
    def _one(self):
        return _stack_svg("t", "title", "desc",
                          [_box([("ptr", "#1a1a1a"), ("0xa", "#555")])],
                          _box([("val=42", "#1a1a1a"), ("0xb", "#555")]))

    def test_single_source_is_vertical_viewbox(self):
        out = self._one()
        assert "<svg" in out and 'role="img"' in out
        import re
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', out)
        w, h = int(m.group(1)), int(m.group(2))
        assert h > w
        assert (w, h) != (500, 160)

    def test_single_source_one_arrow(self):
        assert self._one().count("<line") == 1

    def test_two_sources_converge_two_arrows(self):
        out = _stack_svg("t", "title", "desc",
                         [_box([("sp1", "#1a1a1a")]), _box([("sp2", "#1a1a1a")])],
                         _box([("val=42", "#1a1a1a")]))
        assert out.count("<line") == 2

    def test_three_sources_stack_three_arrows(self):
        out = _stack_svg("t", "title", "desc",
                         [_box([("a", "#1a1a1a")]), _box([("b", "#1a1a1a")]),
                          _box([("c", "#1a1a1a")])],
                         _box([("val", "#1a1a1a")]))
        assert out.count("<path") >= 3

    def test_no_target_draws_no_arrow(self):
        out = _stack_svg("t", "weak", "desc",
                         [_box([("weak_ptr", "#1a1a1a"), ("exp", "#555")])], None)
        assert out.count("<line") == 0 and "url(#" not in out
