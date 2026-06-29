"""Dear PyGui application base for the C++ Pointer Lab.

Provides :class:`PtrLabApp`, a parametric class that accepts a list of
:class:`~cpp_ptr_lab.code_generator.TopicTemplate` objects and a window title
and builds the full tabbed GUI with compile/run infrastructure.

Run with one of the launchers::

    python -m cpp_ptr_lab.run_ptrs
    python -m cpp_ptr_lab.run_smart
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import Any

import dearpygui.dearpygui as dpg

from .code_generator import TopicTemplate, generate_source
from .compiler_runner import (
    GppStatus,
    RunResult,
    build_compile_command,
    compile_and_run,
    compile_only,
    probe_gpp,
)

# ---------------------------------------------------------------------------
# ASan compile flags
# ---------------------------------------------------------------------------

_ASAN_FLAGS = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]

# ---------------------------------------------------------------------------
# Diagram colors
# ---------------------------------------------------------------------------

_BORDER_ERROR = (220, 50, 50, 255)
_BORDER_WARN = (220, 150, 50, 255)
_BORDER_OK = (80, 80, 80, 255)
_COLOR_BOX_FILL = (40, 40, 60, 255)
_COLOR_BOX_OUTLINE = (160, 160, 200, 255)
_COLOR_ARROW = (180, 220, 255, 255)
_COLOR_LABEL = (230, 230, 255, 255)
_COLOR_NULL = (160, 80, 80, 255)
_COLOR_DIM = (120, 120, 140, 255)

# Canvas dimensions
_CW, _CH = 500, 160

# ---------------------------------------------------------------------------
# Per-topic UI state
# ---------------------------------------------------------------------------


@dataclass
class TopicState:
    """Mutable per-topic state retained across tab switches."""

    control_state: dict[str, Any] = field(default_factory=dict)
    last_result: RunResult | None = None
    last_action: str | None = None


def _initial_state(topic: TopicTemplate) -> TopicState:
    """Build a :class:`TopicState` seeded from the topic's control defaults."""
    cs: dict[str, Any] = {}
    for ctrl in topic.controls:
        cs[ctrl.id] = ctrl.default
    return TopicState(control_state=cs)


# ---------------------------------------------------------------------------
# Application controller
# ---------------------------------------------------------------------------


class PtrLabApp:
    """Controller for the C++ Pointer / Smart-Pointer Lab GUI.

    Parameters
    ----------
    topics:
        Ordered list of :class:`TopicTemplate` instances — one tab per topic.
    lab_title:
        Viewport title string (e.g. ``"C++ Pointers & References Lab"``).
    """

    _TAG_PREFIX = "cpl"

    def __init__(self, topics: list[TopicTemplate], lab_title: str) -> None:
        self.topics = topics
        self.topic_by_id: dict[str, TopicTemplate] = {t.id: t for t in topics}
        self.lab_title = lab_title
        self.states: dict[str, TopicState] = {
            t.id: _initial_state(t) for t in topics
        }
        self.gpp_status: GppStatus = probe_gpp()
        self._result_queue: queue.Queue[RunResult] = queue.Queue()
        self._run_thread: threading.Thread | None = None
        self._running_topic_id: str | None = None
        self._running_action: str | None = None
        self._cancel_event: threading.Event | None = None

    # ------------------------------------------------------------------
    # Tag helpers
    # ------------------------------------------------------------------

    @classmethod
    def _tag(cls, topic_id: str, suffix: str) -> str:
        return f"{cls._TAG_PREFIX}_{topic_id}_{suffix}"

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def build_ui(self) -> None:
        """Create the viewport, primary window, and all topic tabs."""
        dpg.create_context()

        with dpg.window(tag="primary", label=self.lab_title):
            self._build_status_banner()

            with dpg.tab_bar(
                tag="topic_tab_bar",
                callback=self._on_tab_changed,
            ):
                for topic in self.topics:
                    label = f"[{topic.group}] {topic.name}"
                    with dpg.tab(label=label, tag=self._tag(topic.id, "tab")):
                        self._build_topic_tab(topic)

        dpg.create_viewport(
            title=self.lab_title,
            width=1280,
            height=860,
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()

        if self.topics:
            first_topic = self.topics[0]
            self._refresh_code_panel(first_topic.id)
            self._populate_command_box(first_topic.id)

    def _build_status_banner(self) -> None:
        """Show a one-line banner describing g++ and ASan availability."""
        ok = self.gpp_status.status == "available"
        color = (50, 180, 50, 255) if ok else (220, 80, 80, 255)
        with dpg.group(horizontal=True):
            dpg.add_text("g++ status:")
            dpg.add_text(self.gpp_status.message, color=color)
            if ok and not self.gpp_status.asan_available:
                dpg.add_text(
                    "  [ASan unavailable — gotcha topics disabled]",
                    color=(220, 150, 50, 255),
                )

    def _build_topic_tab(self, topic: TopicTemplate) -> None:
        """Build the two-column layout for a single topic tab."""
        gpp_ok = self.gpp_status.status == "available"
        asan_ok = self.gpp_status.asan_available
        # For sanitize=True topics, Run/Compile require ASan.
        action_enabled = gpp_ok and (not topic.sanitize or asan_ok)

        with dpg.group(horizontal=True):
            # ---- Left column ----
            with dpg.group(width=360):
                dpg.add_text(topic.name, color=(230, 220, 120, 255))
                dpg.add_separator()
                dpg.add_text("Explanation", color=(180, 180, 180, 255))
                dpg.add_text(topic.explanation, wrap=340)
                dpg.add_spacer(height=8)
                dpg.add_separator()
                dpg.add_text("Controls", color=(180, 180, 180, 255))

                for ctrl in topic.controls:
                    self._build_control(topic, ctrl)

                dpg.add_spacer(height=10)

                if topic.sanitize and not asan_ok:
                    run_label = "Run (ASan unavailable)"
                    compile_label = "Compile (ASan unavailable)"
                elif not gpp_ok:
                    run_label = "Run (g++ unavailable)"
                    compile_label = "Compile (g++ unavailable)"
                else:
                    run_label = "Run"
                    compile_label = "Compile"

                with dpg.group():
                    compile_btn = dpg.add_button(
                        label=compile_label,
                        tag=self._tag(topic.id, "compile_btn"),
                        callback=self._on_compile_clicked,
                        user_data=topic.id,
                        enabled=action_enabled,
                    )
                    if topic.sanitize and not asan_ok:
                        with dpg.tooltip(compile_btn):
                            dpg.add_text(
                                "This topic requires AddressSanitizer.\n"
                                "Install GCC >= 11 or clang >= 12."
                            )
                    run_btn = dpg.add_button(
                        label=run_label,
                        tag=self._tag(topic.id, "run_btn"),
                        callback=self._on_run_clicked,
                        user_data=topic.id,
                        enabled=action_enabled,
                    )
                    if topic.sanitize and not asan_ok:
                        with dpg.tooltip(run_btn):
                            dpg.add_text(
                                "This topic requires AddressSanitizer.\n"
                                "Install GCC >= 11 or clang >= 12."
                            )
                    dpg.add_button(
                        label="Stop",
                        tag=self._tag(topic.id, "stop_btn"),
                        callback=self._on_stop_clicked,
                        user_data=topic.id,
                        enabled=False,
                    )

            # ---- Right column ----
            with dpg.group():
                dpg.add_text("Generated C++ source", color=(180, 180, 180, 255))
                dpg.add_input_text(
                    tag=self._tag(topic.id, "code"),
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=230,
                )

                dpg.add_spacer(height=4)

                dpg.add_text("Compiler command", color=(180, 180, 180, 255))
                dpg.add_input_text(
                    tag=self._tag(topic.id, "command"),
                    readonly=True,
                    width=-1,
                    height=30,
                    default_value="",
                )

                dpg.add_spacer(height=4)

                dpg.add_text(
                    "Output (compiler stderr / program stdout / program stderr)",
                    color=(180, 180, 180, 255),
                )
                dpg.add_input_text(
                    tag=self._tag(topic.id, "output"),
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=160,
                    default_value="",
                )

                dpg.add_spacer(height=4)

                dpg.add_text("Memory bytes (hex)", color=(180, 180, 180, 255))
                dpg.add_input_text(
                    tag=self._tag(topic.id, "memory"),
                    readonly=True,
                    width=-1,
                    height=30,
                    default_value="n/a",
                )

                dpg.add_spacer(height=4)

                dpg.add_text("Pointer/Reference Diagram", color=(180, 180, 180, 255))
                dpg.add_drawlist(
                    tag=self._tag(topic.id, "diagram"),
                    width=_CW,
                    height=_CH,
                )
                # Draw initial neutral border.
                self._draw_border(self._tag(topic.id, "diagram"), _BORDER_OK)

    def _build_control(self, topic: TopicTemplate, ctrl: Any) -> None:
        """Render a single control widget and wire its callback."""
        with dpg.group(horizontal=True):
            dpg.add_text(ctrl.label)
            if ctrl.kind == "dropdown":
                dpg.add_combo(
                    items=list(ctrl.options),
                    default_value=ctrl.default,
                    tag=self._tag(topic.id, f"ctrl_{ctrl.id}"),
                    callback=self._on_control_changed,
                    user_data=topic.id,
                    width=200,
                )
            elif ctrl.kind == "text":
                dpg.add_input_text(
                    default_value=str(ctrl.default),
                    tag=self._tag(topic.id, f"ctrl_{ctrl.id}"),
                    callback=self._on_control_changed,
                    user_data=topic.id,
                    width=200,
                )
            elif ctrl.kind == "checkbox":
                dpg.add_checkbox(
                    default_value=bool(ctrl.default),
                    tag=self._tag(topic.id, f"ctrl_{ctrl.id}"),
                    callback=self._on_control_changed,
                    user_data=topic.id,
                )
            else:
                raise ValueError(f"Unknown control kind: {ctrl.kind!r}")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _read_control_value(self, topic_id: str, ctrl: Any) -> Any:
        tag = self._tag(topic_id, f"ctrl_{ctrl.id}")
        if ctrl.kind == "checkbox":
            return bool(dpg.get_value(tag))
        return dpg.get_value(tag)

    def _on_control_changed(self, sender, app_data, user_data) -> None:
        topic_id = user_data
        topic = self.topic_by_id[topic_id]
        for ctrl in topic.controls:
            self.states[topic_id].control_state[ctrl.id] = (
                self._read_control_value(topic_id, ctrl)
            )
        self._refresh_code_panel(topic_id)
        if self.states[topic_id].last_result is None:
            self._populate_command_box(topic_id)

    def _refresh_code_panel(self, topic_id: str) -> None:
        topic = self.topic_by_id[topic_id]
        state = self.states[topic_id]
        source = generate_source(topic, state.control_state)
        dpg.set_value(self._tag(topic_id, "code"), source)

    def _on_tab_changed(self, sender, app_data, user_data) -> None:
        active_tab_tag = app_data
        if not isinstance(active_tab_tag, str):
            return
        prefix = f"{self._TAG_PREFIX}_"
        suffix = "_tab"
        if not (active_tab_tag.startswith(prefix) and active_tab_tag.endswith(suffix)):
            return
        topic_id = active_tab_tag[len(prefix):-len(suffix)]
        if topic_id not in self.states:
            return
        self._refresh_code_panel(topic_id)
        self._restore_panels(topic_id)

    def _populate_command_box(self, topic_id: str) -> None:
        topic = self.topic_by_id[topic_id]
        state = self.states[topic_id]
        source = generate_source(topic, state.control_state)
        extra_flags = _ASAN_FLAGS if topic.sanitize else None
        cmd = build_compile_command(source, extra_flags=extra_flags)
        dpg.set_value(self._tag(topic_id, "command"), cmd)

    def _restore_panels(self, topic_id: str) -> None:
        state = self.states[topic_id]
        result = state.last_result
        if result is None:
            dpg.set_value(self._tag(topic_id, "output"), "")
            dpg.set_value(self._tag(topic_id, "memory"), "n/a")
            self._populate_command_box(topic_id)
        else:
            self._display_result(topic_id, result)

    def _on_compile_clicked(self, sender, app_data, user_data) -> None:
        self._start_action(user_data, action="compile")

    def _on_run_clicked(self, sender, app_data, user_data) -> None:
        self._start_action(user_data, action="run")

    def _start_action(self, topic_id: str, action: str) -> None:
        if self._running_topic_id is not None:
            return
        topic = self.topic_by_id[topic_id]
        state = self.states[topic_id]
        source = generate_source(topic, state.control_state)
        extra_flags = _ASAN_FLAGS if topic.sanitize else None

        if action == "compile":
            dpg.set_item_label(self._tag(topic_id, "compile_btn"), "Compiling...")
        else:
            dpg.set_item_label(self._tag(topic_id, "run_btn"), "Running...")
        dpg.configure_item(self._tag(topic_id, "compile_btn"), enabled=False)
        dpg.configure_item(self._tag(topic_id, "run_btn"), enabled=False)
        dpg.configure_item(self._tag(topic_id, "stop_btn"), enabled=True)
        busy_msg = (
            "(compiling...)" if action == "compile" else "(compiling and running...)"
        )
        dpg.set_value(self._tag(topic_id, "output"), busy_msg)
        dpg.set_value(self._tag(topic_id, "command"), "")
        dpg.set_value(self._tag(topic_id, "memory"), "n/a")

        self._cancel_event = threading.Event()
        self._running_topic_id = topic_id
        self._running_action = action
        thread = threading.Thread(
            target=self._run_in_thread,
            args=(source, self._cancel_event, action, extra_flags),
            daemon=True,
        )
        self._run_thread = thread
        thread.start()
        self._schedule_poll()

    def _on_stop_clicked(self, sender, app_data, user_data) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()

    # ------------------------------------------------------------------
    # Background run + polling
    # ------------------------------------------------------------------

    def _run_in_thread(
        self,
        source: str,
        cancel_event: threading.Event,
        action: str,
        extra_flags: list[str] | None,
    ) -> None:
        try:
            if action == "compile":
                result = compile_only(
                    source, cancel_event=cancel_event, extra_flags=extra_flags
                )
            else:
                result = compile_and_run(
                    source, cancel_event=cancel_event, extra_flags=extra_flags
                )
        except Exception as exc:
            result = RunResult(
                stdout="",
                stderr=f"Internal error: {exc}",
                exit_code=None,
                memory_bytes="n/a",
                status="execution-error",
            )
        self._result_queue.put(result)

    def _schedule_poll(self) -> None:
        dpg.set_frame_callback(
            dpg.get_frame_count() + 2,
            callback=self._poll_result,
        )

    def _poll_result(self) -> None:
        try:
            result = self._result_queue.get_nowait()
        except queue.Empty:
            self._schedule_poll()
            return

        topic_id = self._running_topic_id
        action = self._running_action
        self._running_topic_id = None
        self._running_action = None
        self._run_thread = None
        self._cancel_event = None

        if topic_id is None:
            return

        state = self.states[topic_id]
        state.last_result = result
        state.last_action = action
        self._display_result(topic_id, result)

        topic = self.topic_by_id[topic_id]
        gpp_ok = self.gpp_status.status == "available"
        asan_ok = self.gpp_status.asan_available
        action_enabled = gpp_ok and (not topic.sanitize or asan_ok)
        dpg.set_item_label(self._tag(topic_id, "compile_btn"), "Compile")
        dpg.set_item_label(self._tag(topic_id, "run_btn"), "Run")
        dpg.configure_item(self._tag(topic_id, "compile_btn"), enabled=action_enabled)
        dpg.configure_item(self._tag(topic_id, "run_btn"), enabled=action_enabled)
        dpg.configure_item(self._tag(topic_id, "stop_btn"), enabled=False)

    def _display_result(self, topic_id: str, result: RunResult) -> None:
        output_text = (
            f"--- status: {result.status} ---\n"
            f"--- exit code: {result.exit_code} ---\n"
            f"\n[compiler stderr]\n{result.compiler_stderr}\n"
            f"\n[program stdout]\n{result.stdout}\n"
            f"\n[program stderr]\n{result.stderr}\n"
        )
        dpg.set_value(self._tag(topic_id, "output"), output_text)
        dpg.set_value(self._tag(topic_id, "command"), result.command)

        state = self.states[topic_id]
        if result.status == "compile-failed":
            mem = "n/a (compile failed)"
        elif result.status == "cancelled":
            mem = "n/a (cancelled)"
        elif state.last_action == "compile":
            mem = "n/a (compile only)"
        else:
            mem = result.memory_bytes
        dpg.set_value(self._tag(topic_id, "memory"), mem)

        topic = self.topic_by_id[topic_id]
        has_warn = self._has_warnings(result.compiler_stderr, result.status)
        self._render_diagram(topic_id, result.ptrdata, result.status, has_warn)

    # ------------------------------------------------------------------
    # Diagram rendering
    # ------------------------------------------------------------------

    @staticmethod
    def _has_warnings(compiler_stderr: str, status: str) -> bool:
        """Return True when g++ emitted stderr but compilation succeeded."""
        return bool(compiler_stderr.strip()) and status != "compile-failed"

    def _draw_border(self, diagram_tag: str, color: tuple) -> None:
        dpg.draw_rectangle(
            [2, 2], [_CW - 2, _CH - 2],
            parent=diagram_tag,
            color=color,
            thickness=2,
        )

    def _render_diagram(
        self,
        topic_id: str,
        ptrdata: dict | None,
        status: str,
        has_warnings: bool,
    ) -> None:
        diagram_tag = self._tag(topic_id, "diagram")
        dpg.delete_item(diagram_tag, children_only=True)

        if status == "compile-failed":
            border_color = _BORDER_ERROR
        elif has_warnings:
            border_color = _BORDER_WARN
        else:
            border_color = _BORDER_OK

        self._draw_border(diagram_tag, border_color)

        topic = self.topic_by_id[topic_id]
        if ptrdata is None or not topic.has_ptrdata:
            return

        ptr_type = ptrdata.get("type")
        if ptr_type == "raw":
            self._draw_raw_ptr(diagram_tag, ptrdata)
        elif ptr_type == "null":
            self._draw_null_ptr(diagram_tag, ptrdata)
        elif ptr_type == "ref":
            self._draw_ref(diagram_tag, ptrdata)
        elif ptr_type == "unique":
            self._draw_unique(diagram_tag, ptrdata)
        elif ptr_type == "shared":
            self._draw_shared(diagram_tag, ptrdata)
        elif ptr_type == "weak":
            self._draw_weak(diagram_tag, ptrdata)

    def _draw_box(
        self,
        parent: str,
        x1: float, y1: float, x2: float, y2: float,
        color: tuple = _COLOR_BOX_OUTLINE,
    ) -> None:
        dpg.draw_rectangle(
            [x1, y1], [x2, y2], parent=parent,
            color=color, fill=_COLOR_BOX_FILL, thickness=1,
        )

    def _draw_label(
        self,
        parent: str,
        x: float, y: float,
        text: str,
        color: tuple = _COLOR_LABEL,
    ) -> None:
        dpg.draw_text([x, y], text, parent=parent, color=color, size=13)

    def _draw_raw_ptr(self, tag: str, pd: dict) -> None:
        """Two-box + arrow diagram for raw pointer."""
        addr = pd.get("ptr_addr", "?")
        tgt = pd.get("target_addr", "?")
        val = pd.get("target_val", "?")
        # Left box: pointer variable
        self._draw_box(tag, 10, 50, 190, 110)
        self._draw_label(tag, 15, 55, "ptr")
        self._draw_label(tag, 15, 73, addr, _COLOR_DIM)
        # Arrow
        dpg.draw_arrow([190, 80], [310, 80], parent=tag, color=_COLOR_ARROW, size=6)
        # Right box: target value
        self._draw_box(tag, 310, 50, 490, 110)
        self._draw_label(tag, 315, 55, f"val={val}")
        self._draw_label(tag, 315, 73, tgt, _COLOR_DIM)

    def _draw_null_ptr(self, tag: str, pd: dict) -> None:
        """Left box with NULL arrow for null pointer."""
        addr = pd.get("ptr_addr", "0x0")
        self._draw_box(tag, 10, 50, 190, 110)
        self._draw_label(tag, 15, 55, "ptr")
        self._draw_label(tag, 15, 73, addr, _COLOR_DIM)
        dpg.draw_arrow([190, 80], [310, 80], parent=tag, color=_COLOR_NULL, size=6)
        self._draw_box(tag, 310, 50, 490, 110, color=_COLOR_NULL)
        self._draw_label(tag, 355, 70, "NULL", _COLOR_NULL)

    def _draw_ref(self, tag: str, pd: dict) -> None:
        """Two-box + arrow diagram for reference."""
        ref_addr = pd.get("ref_addr", "?")
        tgt = pd.get("target_addr", "?")
        val = pd.get("target_val", "?")
        self._draw_box(tag, 10, 50, 190, 110)
        self._draw_label(tag, 15, 55, "ref")
        self._draw_label(tag, 15, 73, ref_addr, _COLOR_DIM)
        dpg.draw_arrow([190, 80], [310, 80], parent=tag, color=_COLOR_ARROW, size=6)
        self._draw_box(tag, 310, 50, 490, 110)
        self._draw_label(tag, 315, 55, f"val={val}")
        self._draw_label(tag, 315, 73, tgt, _COLOR_DIM)

    def _draw_unique(self, tag: str, pd: dict) -> None:
        """Unique pointer: box to target (or NULL)."""
        ptr_addr = pd.get("ptr_addr", "?")
        tgt = pd.get("target_addr", "?")
        val = pd.get("val", "?")
        is_null = pd.get("is_null", "0") == "1"
        self._draw_box(tag, 10, 50, 190, 110)
        self._draw_label(tag, 15, 55, "unique_ptr")
        self._draw_label(tag, 15, 73, ptr_addr, _COLOR_DIM)
        if is_null:
            dpg.draw_arrow([190, 80], [310, 80], parent=tag, color=_COLOR_NULL, size=6)
            self._draw_box(tag, 310, 50, 490, 110, color=_COLOR_NULL)
            self._draw_label(tag, 355, 70, "NULL", _COLOR_NULL)
        else:
            dpg.draw_arrow([190, 80], [310, 80], parent=tag, color=_COLOR_ARROW, size=6)
            self._draw_box(tag, 310, 50, 490, 110)
            self._draw_label(tag, 315, 55, f"val={val}")
            self._draw_label(tag, 315, 73, tgt, _COLOR_DIM)

    def _draw_shared(self, tag: str, pd: dict) -> None:
        """Shared pointer: one or two source boxes → one target, use_count."""
        ptr_addr = pd.get("ptr_addr", "?")
        ptr2_addr = pd.get("ptr2_addr")
        tgt = pd.get("target_addr", "?")
        val = pd.get("val", "?")
        use_count = pd.get("use_count", "?")

        if ptr2_addr:
            # Two source boxes
            self._draw_box(tag, 10, 20, 170, 70)
            self._draw_label(tag, 15, 25, "sp1")
            self._draw_label(tag, 15, 42, ptr_addr, _COLOR_DIM)
            dpg.draw_arrow([170, 45], [310, 80], parent=tag, color=_COLOR_ARROW, size=5)

            self._draw_box(tag, 10, 90, 170, 140)
            self._draw_label(tag, 15, 95, "sp2")
            self._draw_label(tag, 15, 112, ptr2_addr, _COLOR_DIM)
            dpg.draw_arrow([170, 115], [310, 80], parent=tag, color=_COLOR_ARROW, size=5)
        else:
            self._draw_box(tag, 10, 50, 170, 110)
            self._draw_label(tag, 15, 55, "shared_ptr")
            self._draw_label(tag, 15, 73, ptr_addr, _COLOR_DIM)
            dpg.draw_arrow([170, 80], [310, 80], parent=tag, color=_COLOR_ARROW, size=6)

        # Target box
        self._draw_box(tag, 310, 50, 490, 110)
        self._draw_label(tag, 315, 55, f"val={val}")
        self._draw_label(tag, 315, 73, tgt, _COLOR_DIM)
        self._draw_label(tag, 315, 91, f"use_count={use_count}", (200, 220, 100, 255))

    def _draw_weak(self, tag: str, pd: dict) -> None:
        """Weak pointer: single box with expired + use_count."""
        ptr_addr = pd.get("ptr_addr", "?")
        expired = pd.get("expired", "?")
        use_count = pd.get("use_count", "?")
        self._draw_box(tag, 10, 30, 490, 130)
        self._draw_label(tag, 20, 40, "weak_ptr")
        self._draw_label(tag, 20, 58, ptr_addr, _COLOR_DIM)
        self._draw_label(tag, 20, 78, f"expired={expired}", _COLOR_LABEL)
        self._draw_label(tag, 20, 96, f"use_count={use_count}", (200, 220, 100, 255))

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Build the UI and enter the Dear PyGui event loop."""
        self.build_ui()
        dpg.start_dearpygui()
        dpg.destroy_context()
