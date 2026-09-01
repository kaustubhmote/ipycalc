from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from ipycalc import launcher


def test_find_kitty_prefers_environment(monkeypatch, tmp_path: Path) -> None:
    kitty = tmp_path / "kitty"
    kitty.touch()
    monkeypatch.setenv("IPYCALC_KITTY", str(kitty))

    assert launcher.find_kitty() == kitty


def test_runtime_socket_directory_is_private(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))

    socket = launcher._socket_path()

    assert socket == tmp_path / "ipycalc" / "kitty.sock"
    assert socket.parent.stat().st_mode & 0o777 == 0o700


def test_focus_existing_uses_argument_list(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    kitty = tmp_path / "kitty"
    socket = tmp_path / "kitty.sock"

    assert launcher._focus_existing(kitty, socket)
    assert captured["command"] == [
        str(kitty),
        "@",
        "--to",
        f"unix:{socket}",
        "focus-window",
        "--match",
        "all",
    ]


def test_launch_execs_kitty_in_foreground(monkeypatch, tmp_path: Path) -> None:
    kitty = tmp_path / "kitty"
    kitten = tmp_path / "kitten"
    kitty.touch()
    kitten.touch()
    captured = {}
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(launcher, "_focus_existing", lambda *_: False)
    monkeypatch.setattr(launcher, "find_kitten", lambda *_: kitten)

    def fake_exec(file, command, environment):
        captured.update(file=file, command=command, environment=environment)
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(os, "execvpe", fake_exec)

    try:
        launcher._launch(kitty, ["--TerminalInteractiveShell.confirm_exit=False"])
    except RuntimeError as exc:
        assert str(exc) == "exec intercepted"

    assert captured["file"] == str(kitty)
    assert captured["command"][0] == str(kitty)
    assert "&" not in captured["command"]
    assert captured["command"][-3:] == [
        "-m",
        "ipycalc.bootstrap",
        "--TerminalInteractiveShell.confirm_exit=False",
    ]
    assert captured["environment"]["IPYCALC_KITTEN"] == str(kitten)
