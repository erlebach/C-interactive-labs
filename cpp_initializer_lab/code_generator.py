"""Code Generation Module for the C++ Initializer Lab.

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
    """Definition of a single UI control and its template mapping.

    Fields
    ------
    id
        Short identifier matching the key used in ``control_state`` dicts
        (e.g. ``"type"``, ``"value"``, ``"explicit"``).
    label
        Human-readable label shown beside the control in the UI.
    kind
        One of ``"dropdown"``, ``"text"``, ``"checkbox"``.
    options
        For dropdowns: the selectable values.  Empty for text/checkbox.
    default
        Default value — a string for dropdown/text, a bool for checkbox.
    placeholder
        The template placeholder this control fills, including the angle
        brackets (e.g. ``"<<type>>"``).
    value_map
        Optional mapping from a control's raw value to the C++ snippet that
        should actually be substituted.  Keys are strings; boolean values
        are normalised to ``"true"``/``"false"``.  This lets a "form"
        dropdown whose options are ``["copy", "direct"]`` produce real C++
        fragments like ``" = 42"`` or ``"(42)"``.  Mapped values may
        themselves contain placeholders (e.g. ``"{<<value>>}"``) which are
        resolved iteratively.
    """

    id: str
    label: str
    kind: str
    options: list[str] = field(default_factory=list)
    default: str | bool = ""
    placeholder: str = ""
    value_map: dict[str, str] | None = None


@dataclass
class TopicTemplate:
    """A single lab topic: its template, controls, and metadata.

    Fields
    ------
    id
        Short identifier (e.g. ``"value"``, ``"most-vexing-parse"``).
    name
        Display name shown on the tab (e.g. ``"Value Initialization"``).
    template
        The full C++ source template with ``<<placeholder>>`` markers.
        Must contain a ``<<HARNESS>>`` marker where the instrumentation
        block goes (typically right after the initialization line).
    controls
        The UI controls for this topic.
    explanation
        2-4 sentence explanatory text shown in the tab.
    group
        ``"Core"`` or ``"Gotchas"``.
    target_var
        The name of the variable the instrumentation harness inspects.
        Defaults to ``"x"``; override for topics that use ``s``, ``w``,
        or ``f``.
    """

    id: str
    name: str
    template: str
    controls: list[ControlDef]
    explanation: str
    group: str
    target_var: str = "x"


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
    """Resolve a control's raw value to the C++ snippet to substitute.

    If the control has a ``value_map``, the raw value is looked up there
    (booleans normalised to ``"true"``/``"false"``); otherwise the raw
    value is stringified directly.
    """
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


def generate_source(topic: TopicTemplate, control_state: dict) -> str:
    """Generate the full C++ source for *topic* given *control_state*.

    ``control_state`` maps control ``id`` → current value.  Missing values
    fall back to each control's ``default``.

    Substitution is iterative so that a ``value_map`` entry may itself
    contain placeholders (e.g. ``"{<<value>>}"``) that are resolved in a
    later pass once the inner placeholder's value is known.
    """
    # Build the substitution table from controls + defaults.
    subs: dict[str, str] = {}
    for ctrl in topic.controls:
        raw = control_state.get(ctrl.id, ctrl.default)
        subs[ctrl.placeholder] = _resolve_control_value(ctrl, raw)

    # The harness is always provided.
    subs["<<HARNESS>>"] = _build_harness(topic.target_var)

    result = topic.template
    # Iterate to resolve nested placeholders (value_map entries that
    # reference other placeholders).  A handful of passes is always enough.
    for _ in range(8):
        previous = result
        for placeholder, value in subs.items():
            result = result.replace(placeholder, value)
        if result == previous:
            break
    return result
