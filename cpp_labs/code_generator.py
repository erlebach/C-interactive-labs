"""Code Generation Module for the C++ Pointer Lab.

Defines the data structures for topic templates and UI controls, and the
:func:`generate_source` function that substitutes control values into a C++
template and injects the memory-dump instrumentation harness.

Placeholder syntax
------------------
Templates use ``<<name>>`` double-angle-bracket placeholders (e.g.
``<<type>>``, ``<<value>>``) rather than ``str.format`` braces.  This avoids
all brace-escaping conflicts with C++ code, which is full of ``{`` and ``}``.

A special placeholder ``<<HARNESS>>`` marks where the memory-dump
instrumentation block is inserted.  The harness references the topic's
``target_var`` (the variable being initialized) and prints its raw bytes to
stdout in a parseable ``MEMBYTES:`` line.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ControlDef:
    """Definition of a single UI control and its template mapping."""

    id: str
    label: str
    kind: str
    options: list[str] = field(default_factory=list)
    default: str | bool = ""
    placeholder: str = ""
    value_map: dict[str, str] | None = None


@dataclass
class CaseDef:
    """A build-time sub-case shown within one variant panel.

    Each case is compiled independently; ``subs`` fills extra template
    placeholders (e.g. ``<<op>>``) to vary one operation while the
    variant's control state (e.g. the declaration) stays fixed.
    """

    label: str
    subs: dict[str, str] = field(default_factory=dict)


@dataclass
class TopicTemplate:
    """A single lab topic: its template, controls, and metadata."""

    id: str
    name: str
    template: str
    controls: list[ControlDef]
    explanation: str
    group: str
    target_var: str = "x"
    sanitize: bool = False
    has_ptrdata: bool = True
    doc_url: str = ""
    cases: list[CaseDef] | None = None


# ---------------------------------------------------------------------------
# Harness construction
# ---------------------------------------------------------------------------

_HARNESS_TEMPLATE = """\
    // --- instrumentation (not part of the lesson) ---
    {{
        unsigned char* p = reinterpret_cast<unsigned char*>(&{var});
        std::cout << "MEMBYTES:";
        for (size_t i = 0; i < sizeof({var}); ++i) {{
            printf(" %02x", p[i]);
        }}
        std::cout << std::endl;
    }}
    // --- end instrumentation ---"""


def _build_harness(target_var: str) -> str:
    """Return the instrumentation block that dumps ``target_var``'s bytes."""
    return _HARNESS_TEMPLATE.format(var=target_var)


# ---------------------------------------------------------------------------
# Value resolution
# ---------------------------------------------------------------------------


def _resolve_control_value(ctrl: ControlDef, raw: str | bool) -> str:
    if ctrl.value_map is not None:
        if isinstance(raw, bool):
            key = "true" if raw else "false"
        else:
            key = str(raw)
        return ctrl.value_map.get(key, str(raw))
    return str(raw)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_source(
    topic: TopicTemplate,
    control_state: dict,
    extra_subs: dict[str, str] | None = None,
) -> str:
    """Generate the full C++ source for *topic* given *control_state*.

    *extra_subs* (used for per-case sub-case rendering) are applied on top
    of the control-resolved substitutions, filling placeholders such as
    ``<<op>>`` that no control owns.
    """
    subs: dict[str, str] = {}
    for ctrl in topic.controls:
        raw = control_state.get(ctrl.id, ctrl.default)
        subs[ctrl.placeholder] = _resolve_control_value(ctrl, raw)

    if extra_subs:
        subs.update(extra_subs)

    subs["<<HARNESS>>"] = _build_harness(topic.target_var)

    result = topic.template
    for _ in range(8):
        previous = result
        for placeholder, value in subs.items():
            result = result.replace(placeholder, value)
        if result == previous:
            break
    return result
