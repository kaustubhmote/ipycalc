from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from ipycalc import backend_kitty


def test_icat_prefers_explicit_kitten(monkeypatch, tmp_path: Path) -> None:
    kitten = tmp_path / "kitten"
    monkeypatch.setenv("IPYCALC_KITTEN", str(kitten))
    monkeypatch.setenv("IPYCALC_KITTY", str(tmp_path / "kitty"))

    assert backend_kitty._icat_command() == [str(kitten), "icat"]


def test_show_sends_png_bytes_to_icat(monkeypatch) -> None:
    calls: list[tuple[list[str], tuple[str, ...], bytes | None]] = []

    def fake_run(command, *arguments, input_bytes=None):
        calls.append((command, arguments, input_bytes))
        return ""

    monkeypatch.setenv("MPLBACKEND_KITTY_SIZING", "manual")
    monkeypatch.setattr(backend_kitty, "_icat_command", lambda: ["kitten", "icat"])
    monkeypatch.setattr(backend_kitty, "_run", fake_run)
    figure = Figure()
    canvas = backend_kitty.FigureCanvasICat(figure)
    manager = backend_kitty.FigureManagerICat(canvas, 1)

    manager.show()

    assert calls[0][0] == ["kitten", "icat"]
    assert calls[0][1] == ("--align", "left")
    assert calls[0][2].startswith(b"\x89PNG")
