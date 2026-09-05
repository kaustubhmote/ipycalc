from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from ipycalc import backend_kitty


def test_icat_prefers_explicit_kitten(monkeypatch, tmp_path: Path) -> None:
    kitten = tmp_path / "kitten"
    monkeypatch.setenv("IPYCALC_KITTEN", str(kitten))
    monkeypatch.setenv("IPYCALC_KITTY", str(tmp_path / "kitty"))

    assert backend_kitty._icat_command() == [str(kitten), "icat"]


def test_show_sends_png_bytes_to_icat_without_capturing_output(monkeypatch) -> None:
    calls: list[tuple[list[str], bytes]] = []

    def fake_display(command, png):
        calls.append((command, png))

    monkeypatch.setenv("MPLBACKEND_KITTY_SIZING", "manual")
    monkeypatch.setattr(backend_kitty, "_icat_command", lambda: ["kitten", "icat"])
    monkeypatch.setattr(backend_kitty, "_display", fake_display)
    figure = Figure()
    canvas = backend_kitty.FigureCanvasICat(figure)
    manager = backend_kitty.FigureManagerICat(canvas, 1)

    manager.show()

    assert calls[0][0] == ["kitten", "icat"]
    assert calls[0][1].startswith(b"\x89PNG")


def test_display_inherits_stdout_for_kitty_graphics_protocol(monkeypatch) -> None:
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs

    monkeypatch.setattr(backend_kitty.subprocess, "run", fake_run)

    backend_kitty._display(["kitten", "icat"], b"png-data")

    assert captured == {
        "command": ["kitten", "icat", "--align", "left"],
        "kwargs": {"input": b"png-data", "check": True},
    }
