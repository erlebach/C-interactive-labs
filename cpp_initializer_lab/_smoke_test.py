"""Tiny smoke test for dearpygui.

This module exists only to verify that the ``dearpygui`` package imports
correctly on the student's machine. It is **not** imported by the app; it is
meant to be run directly::

    python -m cpp_initializer_lab._smoke_test

It creates a minimal window and immediately exits, so it can be run even in
environments where a long-lived GUI loop would block (CI, headless boxes).
"""

from __future__ import annotations

import dearpygui.dearpygui as dpg


def main() -> int:
    # Importing dearpygui already exercises the native extension load.
    # Creating a context + a viewport + a window confirms the full stack
    # initializes without raising.
    dpg.create_context()
    with dpg.window(label="Smoke Test"):
        dpg.add_text("dearpygui is working.")
    dpg.create_viewport(title="Smoke Test", width=300, height=200)
    dpg.setup_dearpygui()
    # We deliberately do NOT call dpg.show_viewport() / dpg.start_dearpygui()
    # so this script returns immediately and stays headless-friendly.
    dpg.destroy_context()
    print("dearpygui smoke test OK:", getattr(dpg, "__version__", "unknown"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
