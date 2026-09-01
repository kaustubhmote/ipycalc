from __future__ import annotations

import os
import subprocess
import sys
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


def test_reexec_preserves_virtual_environment_symlink(monkeypatch, tmp_path: Path) -> None:
    real_python = tmp_path / "python-real"
    real_python.touch(mode=0o755)
    environment_python = tmp_path / "environment" / "bin" / "python"
    environment_python.parent.mkdir(parents=True)
    environment_python.symlink_to(real_python)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "current-python"))
    captured = {}

    def fake_exec(file, command, environment):
        captured.update(file=file, command=command, environment=environment)
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(os, "execve", fake_exec)
    arguments = SimpleNamespace(configure_python=None, python=str(environment_python))

    try:
        launcher._reexec_if_requested(arguments, ["--python", str(environment_python)])
    except RuntimeError as exc:
        assert str(exc) == "exec intercepted"

    assert captured["file"] == str(environment_python)
    assert captured["command"][0] == str(environment_python)


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


def test_init_environment_saves_managed_interpreter(monkeypatch, tmp_path: Path, capsys) -> None:
    environment_home = tmp_path / "environment"
    saved = {}
    monkeypatch.setenv("IPYCALC_MANAGED_ENVIRONMENT", str(environment_home))
    monkeypatch.setattr(launcher, "save_python_path", lambda executable: saved.setdefault("python", executable))

    result = launcher.main(["--init-environment"])

    assert result == 0
    assert saved["python"] == sys.executable
    assert f"Managed uv environment: {environment_home}" in capsys.readouterr().out


def test_init_environment_requires_appimage(monkeypatch, capsys) -> None:
    monkeypatch.delenv("IPYCALC_MANAGED_ENVIRONMENT", raising=False)

    result = launcher.main(["--init-environment"])

    assert result == 1
    assert "must be run through the AppImage" in capsys.readouterr().err


def test_init_environment_does_not_select_invalid_environment(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("IPYCALC_MANAGED_ENVIRONMENT", str(tmp_path / "environment"))
    monkeypatch.setattr(launcher, "validate_current", lambda: SimpleNamespace(valid=False))
    monkeypatch.setattr(launcher, "format_report", lambda report: "Environment: invalid")

    result = launcher.main(["--init-environment"])

    assert result == 1
    assert "Environment: invalid" in capsys.readouterr().err
