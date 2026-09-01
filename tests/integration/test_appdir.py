from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_RUN = PROJECT_ROOT / "packaging" / "appimage" / "AppRun"
DESKTOP_FILE = PROJECT_ROOT / "packaging" / "appimage" / "org.ipycalc.IPyCalc.desktop"
METAINFO_FILE = PROJECT_ROOT / "packaging" / "appimage" / "org.ipycalc.IPyCalc.metainfo.xml"


def test_app_run_has_valid_shell_syntax() -> None:
    subprocess.run(["sh", "-n", str(APP_RUN)], check=True)


def test_desktop_file_is_valid() -> None:
    validator = shutil.which("desktop-file-validate")
    if validator is None:
        return
    subprocess.run([validator, str(DESKTOP_FILE)], check=True)


def test_appstream_metadata_is_valid_when_validator_is_available() -> None:
    validator = shutil.which("appstreamcli")
    if validator is None:
        return
    subprocess.run([validator, "validate", "--no-net", str(METAINFO_FILE)], check=True)


def test_app_run_passes_a_spaced_python_path_as_one_argument(tmp_path: Path) -> None:
    appdir = tmp_path / "IPyCalc Test.AppDir"
    package = appdir / "opt" / "ipycalc"
    kitty_bin = appdir / "usr" / "lib" / "kitty.app" / "bin"
    package.mkdir(parents=True)
    kitty_bin.mkdir(parents=True)
    capture = tmp_path / "arguments.txt"
    python = tmp_path / "Python Env" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{capture}"\n', encoding="utf-8")
    python.chmod(0o755)
    environment = os.environ.copy()
    environment.update({"APPDIR": str(appdir), "XDG_CONFIG_HOME": str(tmp_path / "config")})

    completed = subprocess.run(
        [str(APP_RUN), "--python", str(python), "--show-python"],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert capture.read_text(encoding="utf-8").splitlines() == [
        "-m",
        "ipycalc.launcher",
        "--python",
        str(python),
        "--show-python",
    ]
