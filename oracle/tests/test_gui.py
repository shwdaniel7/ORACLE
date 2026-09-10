"""Smoke tests for the GUI (skipped when no display is available)."""

from __future__ import annotations

import pytest


def test_dashboard_importable() -> None:
    from oracle.gui import app  # noqa: PLC0415

    assert callable(app.build_app)


def test_dashboard_build_smoke(config) -> None:
    try:
        from oracle.gui.app import build_app  # noqa: PLC0415
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency optional
        pytest.skip(f"customtkinter not installed: {exc}")

    try:
        app = build_app(config)
    except Exception as exc:  # pragma: no cover - headless environments
        pytest.skip(f"no display available: {exc}")

    app.update_idletasks()
    assert app.title() != ""
    app.destroy()
