"""Dear PyGui entry point for the C++ Initializer Lab.

This module builds the desktop GUI: a tabbed interface where each tab is one
of the 9 lab topics.  Each tab has a control panel (left), a read-only code
display (top right), an output panel (middle right), and a memory-bytes
panel (bottom right).  A Run button compiles and runs the generated C++
snippet in a background thread so the UI stays responsive.

Run with::

    python -m cpp_initializer_lab.app
"""

from __future__ import annotations

import threading
import queue
from dataclasses import dataclass, field
from typing import Any

import dearpygui.dearpygui as dpg

from .code_generator import generate_source
from .compiler_runner import (
    GppStatus,
    RunResult,
    build_compile_command,
    compile_and_run,
    compile_only,
    probe_gpp,
)
from .topics import TOPICS, TOPIC_BY_ID, TopicTemplate


# ---------------------------------------------------------------------------
# Per-topic UI state
# ---------------------------------------------------------------------------


@dataclass
class TopicState:
    """Mutable per-topic state retained across tab switches.

    Attributes
    ----------
    control_state:
        Maps control id → current value (str for dropdown/text, bool for
        checkbox).  Initialised from each control's ``default``.
    last_result:
        The most recent :class:`RunResult` for this topic, or ``None`` if it
        has not been run yet.
    last_action:
        ``"compile"``, ``"run"``, or ``None``.  Records which button
        produced ``last_result`` so the UI can restore the right state
        (e.g. memory shows "n/a (compile only)" after a Compile).
    """

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


class InitializerLabApp:
    """Controller object wiring topics, state, and the Dear PyGui UI.

    The UI is built once in :meth:`build_ui`.  Per-topic widgets are tagged
    with stable, predictable names so callbacks can look them up by topic id.
    """

    # Tag prefix used for every widget so we can find them reliably.
    _TAG_PREFIX = "cil"

    def __init__(self) -> None:
        # Per-topic state, keyed by topic id.
        self.states: dict[str, TopicState] = {
            t.id: _initial_state(t) for t in TOPICS
        }
        # g++ availability, probed at startup.
        self.gpp_status: GppStatus = probe_gpp()
        # Background-run plumbing.  Only one run is in flight at a time.
        self._result_queue: queue.Queue[RunResult] = queue.Queue()
        self._run_thread: threading.Thread | None = None
        self._running_topic_id: str | None = None
        # Which action is in flight: "compile" or "run" (None when idle).
        self._running_action: str | None = None
        # Cancellation support: a fresh Event is created per Run/Compile.
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

        with dpg.window(tag="primary", label="C++ Initializer Lab"):
            # Status banner for g++ availability.
            self._build_status_banner()

            with dpg.tab_bar(
                tag="topic_tab_bar",
                callback=self._on_tab_changed,
            ):
                for topic in TOPICS:
                    label = f"[{topic.group}] {topic.name}"
                    with dpg.tab(label=label, tag=self._tag(topic.id, "tab")):
                        self._build_topic_tab(topic)

        dpg.create_viewport(
            title="C++ Initializer Lab — ISC5305",
            width=1280,
            height=800,
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # NOTE: polling is scheduled on-demand in _start_action via
        # dpg.set_frame_callback, which is one-shot and re-arms itself
        # inside _poll_result until the result queue is drained.

        # Generate the initial source for the first tab so the code panel
        # is not empty on launch.  We refresh whichever tab is active.
        first_topic = TOPICS[0]
        self._refresh_code_panel(first_topic.id)
        # Populate the compiler-command box for the first tab too.
        self._populate_command_box(first_topic.id)

    def _build_status_banner(self) -> None:
        """Show a one-line banner describing g++ availability."""
        ok = self.gpp_status.status == "available"
        color = (50, 180, 50, 255) if ok else (220, 80, 80, 255)
        with dpg.group(horizontal=True):
            dpg.add_text("g++ status:")
            dpg.add_text(self.gpp_status.message, color=color)

    def _build_topic_tab(self, topic: TopicTemplate) -> None:
        """Build the two-column layout for a single topic tab."""
        with dpg.group(horizontal=True):
            # ---- Left column: controls + explanation + Run button ----
            with dpg.group(width=360):
                dpg.add_text(topic.name, color=(230, 220, 120, 255))
                dpg.add_separator()
                dpg.add_text("Explanation", color=(180, 180, 180, 255))
                # Wrap the explanation text so it fits the narrow column.
                dpg.add_text(topic.explanation, wrap=340)
                dpg.add_spacer(height=8)
                dpg.add_separator()
                dpg.add_text("Controls", color=(180, 180, 180, 255))

                # Render one widget per control definition.
                for ctrl in topic.controls:
                    self._build_control(topic, ctrl)

                dpg.add_spacer(height=10)
                gpp_ok = self.gpp_status.status == "available"
                run_label = "Run" if gpp_ok else "Run (g++ unavailable)"
                compile_label = "Compile" if gpp_ok else "Compile (g++ unavailable)"
                # Compile, Run, and Stop stacked vertically (single column).
                # Stop is disabled until a compile/run is in flight.
                with dpg.group():
                    dpg.add_button(
                        label=compile_label,
                        tag=self._tag(topic.id, "compile_btn"),
                        callback=self._on_compile_clicked,
                        user_data=topic.id,
                        enabled=gpp_ok,
                    )
                    dpg.add_button(
                        label=run_label,
                        tag=self._tag(topic.id, "run_btn"),
                        callback=self._on_run_clicked,
                        user_data=topic.id,
                        enabled=gpp_ok,
                    )
                    dpg.add_button(
                        label="Stop",
                        tag=self._tag(topic.id, "stop_btn"),
                        callback=self._on_stop_clicked,
                        user_data=topic.id,
                        enabled=False,
                    )

            # ---- Right column: code / output / memory panels ----
            with dpg.group():
                # Code panel (top).
                dpg.add_text("Generated C++ source", color=(180, 180, 180, 255))
                dpg.add_input_text(
                    tag=self._tag(topic.id, "code"),
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=260,
                )

                dpg.add_spacer(height=6)

                # Compiler command panel (between code and output).
                dpg.add_text("Compiler command", color=(180, 180, 180, 255))
                dpg.add_input_text(
                    tag=self._tag(topic.id, "command"),
                    readonly=True,
                    width=-1,
                    height=30,
                    default_value="",
                )

                dpg.add_spacer(height=6)

                # Output panel (middle).
                dpg.add_text(
                    "Output (compiler stderr / program stdout / program stderr)",
                    color=(180, 180, 180, 255),
                )
                dpg.add_input_text(
                    tag=self._tag(topic.id, "output"),
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=200,
                    default_value="",
                )

                dpg.add_spacer(height=6)

                # Memory panel (bottom).
                dpg.add_text("Memory bytes (hex)", color=(180, 180, 180, 255))
                dpg.add_input_text(
                    tag=self._tag(topic.id, "memory"),
                    readonly=True,
                    width=-1,
                    height=30,
                    default_value="n/a",
                )

    def _build_control(self, topic: TopicTemplate, ctrl: Any) -> None:
        """Render a single control widget and wire its callback."""
        # Label + widget on the same row for compactness.
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
        """Read the current value of a control widget from the UI."""
        tag = self._tag(topic_id, f"ctrl_{ctrl.id}")
        if ctrl.kind == "checkbox":
            return bool(dpg.get_value(tag))
        return dpg.get_value(tag)

    def _on_control_changed(self, sender, app_data, user_data) -> None:
        """A control changed: update state and refresh the code panel."""
        topic_id = user_data
        topic = TOPIC_BY_ID[topic_id]
        # Re-read every control so the state dict stays in sync even if
        # the changed widget was not the one we expected.
        for ctrl in topic.controls:
            self.states[topic_id].control_state[ctrl.id] = (
                self._read_control_value(topic_id, ctrl)
            )
        self._refresh_code_panel(topic_id)
        # If the topic has not been compiled/run yet, refresh the expected
        # command string to match the new source.  If it has a last result,
        # leave the command box showing the actual command that was run
        # (it will update on the next Compile/Run).
        if self.states[topic_id].last_result is None:
            self._populate_command_box(topic_id)

    def _refresh_code_panel(self, topic_id: str) -> None:
        """Regenerate source from current state and update the code widget."""
        topic = TOPIC_BY_ID[topic_id]
        state = self.states[topic_id]
        source = generate_source(topic, state.control_state)
        dpg.set_value(self._tag(topic_id, "code"), source)

    def _on_tab_changed(self, sender, app_data, user_data) -> None:
        """Tab switch: refresh the code panel and restore last run output.

        Dear PyGui fires this with ``app_data`` set to the tag of the newly
        active tab.  We parse the topic id back out of that tag, regenerate
        the source for the now-visible topic, and restore its last
        ``RunResult`` (if any) into the output + memory panels.
        """
        active_tab_tag = app_data
        if not isinstance(active_tab_tag, str):
            return
        # Tab tags have the form ``cil_<topic_id>_tab``.
        prefix = f"{self._TAG_PREFIX}_"
        suffix = "_tab"
        if not (active_tab_tag.startswith(prefix) and active_tab_tag.endswith(suffix)):
            return
        topic_id = active_tab_tag[len(prefix):-len(suffix)]
        if topic_id not in self.states:
            return
        # Repopulate the code panel for the newly active topic.
        self._refresh_code_panel(topic_id)
        # Restore the output + memory panels from per-topic state.
        self._restore_panels(topic_id)

    def _populate_command_box(self, topic_id: str) -> None:
        """Fill the Compiler Command box with the expected g++ command.

        Used on tab switch and on control change when the topic has not yet
        been compiled/run, so the box is never empty.  Builds the command
        string via :func:`build_compile_command` without invoking g++.
        """
        topic = TOPIC_BY_ID[topic_id]
        state = self.states[topic_id]
        source = generate_source(topic, state.control_state)
        cmd = build_compile_command(source)
        dpg.set_value(self._tag(topic_id, "command"), cmd)

    def _restore_panels(self, topic_id: str) -> None:
        """Restore output + memory widgets from the topic's last RunResult.

        If the topic has never been compiled/run, the panels are reset to
        their empty/default state and the command box is populated with the
        *expected* g++ command (via :func:`build_compile_command`) so it is
        never empty.
        """
        state = self.states[topic_id]
        result = state.last_result
        if result is None:
            dpg.set_value(self._tag(topic_id, "output"), "")
            dpg.set_value(self._tag(topic_id, "memory"), "n/a")
            # Show the expected command string even before any compile/run.
            self._populate_command_box(topic_id)
        else:
            self._display_result(topic_id, result)

    def _on_compile_clicked(self, sender, app_data, user_data) -> None:
        """Compile button: compile-only (no execution) in a background thread."""
        self._start_action(user_data, action="compile")

    def _on_run_clicked(self, sender, app_data, user_data) -> None:
        """Run button: compile + execute in a background thread."""
        self._start_action(user_data, action="run")

    def _start_action(self, topic_id: str, action: str) -> None:
        """Shared launch logic for the Compile and Run buttons.

        ``action`` is ``"compile"`` or ``"run"``.  Generates the source,
        disables both action buttons, enables Stop, clears the panels, and
        starts the background worker thread.
        """
        # Refuse if an action is already in flight.
        if self._running_topic_id is not None:
            return
        topic = TOPIC_BY_ID[topic_id]
        state = self.states[topic_id]
        source = generate_source(topic, state.control_state)

        # Show the in-flight state on the relevant button.
        if action == "compile":
            dpg.set_item_label(self._tag(topic_id, "compile_btn"), "Compiling...")
        else:
            dpg.set_item_label(self._tag(topic_id, "run_btn"), "Running...")
        # Disable both action buttons while in flight; enable Stop.
        dpg.configure_item(self._tag(topic_id, "compile_btn"), enabled=False)
        dpg.configure_item(self._tag(topic_id, "run_btn"), enabled=False)
        dpg.configure_item(self._tag(topic_id, "stop_btn"), enabled=True)
        # Clear the output / command / memory panels so the user sees
        # something is happening.
        busy_msg = (
            "(compiling...)" if action == "compile"
            else "(compiling and running...)"
        )
        dpg.set_value(self._tag(topic_id, "output"), busy_msg)
        dpg.set_value(self._tag(topic_id, "command"), "")
        dpg.set_value(self._tag(topic_id, "memory"), "n/a")

        # Fresh cancel event for this action.
        self._cancel_event = threading.Event()
        self._running_topic_id = topic_id
        self._running_action = action
        thread = threading.Thread(
            target=self._run_in_thread,
            args=(source, self._cancel_event, action),
            daemon=True,
        )
        self._run_thread = thread
        thread.start()

        # Schedule a one-shot frame callback to poll for completion.
        # _poll_result re-arms itself until the result queue is drained.
        self._schedule_poll()

    def _on_stop_clicked(self, sender, app_data, user_data) -> None:
        """Stop button: signal the in-flight run to cancel."""
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
    ) -> None:
        """Worker: run compile_only / compile_and_run and push the result."""
        try:
            if action == "compile":
                result = compile_only(source, cancel_event=cancel_event)
            else:
                result = compile_and_run(source, cancel_event=cancel_event)
        except Exception as exc:  # pragma: no cover — defensive
            result = RunResult(
                stdout="",
                stderr=f"Internal error: {exc}",
                exit_code=None,
                memory_bytes="n/a",
                status="execution-error",
            )
        self._result_queue.put(result)

    def _schedule_poll(self) -> None:
        """Register a one-shot frame callback to check for completion.

        ``dpg.set_frame_callback`` fires once on the given future frame.
        We use a small delay (2 frames) and re-arm inside ``_poll_result``
        until the result is ready, so the UI thread stays responsive.
        """
        dpg.set_frame_callback(2, callback=self._poll_result)

    def _poll_result(self) -> None:
        """Frame callback: if the action finished, update the UI.

        Registered via :meth:`_schedule_poll` and re-armed on each call
        until the result queue is drained.
        """
        try:
            result = self._result_queue.get_nowait()
        except queue.Empty:
            # Not done yet — re-arm the poller.
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

        # Persist the result + which action produced it so a tab switch
        # restores the right state later.
        state = self.states[topic_id]
        state.last_result = result
        state.last_action = action
        self._display_result(topic_id, result)

        # Restore the button labels and enable state.
        gpp_ok = self.gpp_status.status == "available"
        dpg.set_item_label(self._tag(topic_id, "compile_btn"), "Compile")
        dpg.set_item_label(self._tag(topic_id, "run_btn"), "Run")
        dpg.configure_item(
            self._tag(topic_id, "compile_btn"), enabled=gpp_ok
        )
        dpg.configure_item(self._tag(topic_id, "run_btn"), enabled=gpp_ok)
        dpg.configure_item(self._tag(topic_id, "stop_btn"), enabled=False)

    def _display_result(self, topic_id: str, result: RunResult) -> None:
        """Push a RunResult's fields into the output + memory widgets.

        The output panel shows three clearly-labelled sections — compiler
        stderr, program stdout, program stderr — plus status and exit code.
        The compiler command string goes in its own box above the output.
        The memory panel reflects whether this was a compile-only action.
        """
        # If the user has switched away from this tab, the widgets still
        # exist (we built them all up front), so updating them is safe and
        # means the result will be visible when they switch back.
        output_text = (
            f"--- status: {result.status} ---\n"
            f"--- exit code: {result.exit_code} ---\n"
            f"\n[compiler stderr]\n{result.compiler_stderr}\n"
            f"\n[program stdout]\n{result.stdout}\n"
            f"\n[program stderr]\n{result.stderr}\n"
        )
        dpg.set_value(self._tag(topic_id, "output"), output_text)

        # Compiler command box.
        dpg.set_value(self._tag(topic_id, "command"), result.command)

        # Memory panel: depends on the action that produced this result.
        state = self.states[topic_id]
        if result.status == "compile-failed":
            mem = "n/a (compile failed)"
        elif result.status == "cancelled":
            mem = "n/a (cancelled)"
        elif state.last_action == "compile":
            # Compile-only succeeded — no program was run, so no bytes.
            mem = "n/a (compile only)"
        else:
            mem = result.memory_bytes
        dpg.set_value(self._tag(topic_id, "memory"), mem)

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Build the UI and enter the Dear PyGui event loop."""
        self.build_ui()
        dpg.start_dearpygui()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Launch the C++ Initializer Lab GUI."""
    app = InitializerLabApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
