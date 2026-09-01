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


def test_app_run_creates_default_uv_environment_in_config_home(tmp_path: Path) -> None:
    appdir = tmp_path / "IPyCalc Test.AppDir"
    resources = appdir / "opt" / "ipycalc" / "ipycalc" / "resources"
    kitty_bin = appdir / "usr" / "lib" / "kitty.app" / "bin"
    resources.mkdir(parents=True)
    kitty_bin.mkdir(parents=True)
    template = resources / "environment.pyproject.toml"
    template.write_text('[project]\nname = "test-environment"\nversion = "1.0.0"\n', encoding="utf-8")

    config_root = tmp_path / "config"
    environment_home = config_root / "ipycalc" / "environment"
    managed_python = environment_home / ".venv" / "bin" / "python"
    python_capture = tmp_path / "python-arguments.txt"
    source_python = tmp_path / "managed-python"
    source_python.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$@" > "{python_capture}"\n',
        encoding="utf-8",
    )
    source_python.chmod(0o755)

    uv_capture = tmp_path / "uv-arguments.txt"
    tools = tmp_path / "tools"
    tools.mkdir()
    fake_uv = tools / "uv"
    fake_uv.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$@" > "{uv_capture}"\n'
        f'mkdir -p "{managed_python.parent}"\n'
        f'cp "{source_python}" "{managed_python}"\n',
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "APPDIR": str(appdir),
            "PATH": f"{tools}:/usr/bin:/bin",
            "XDG_CONFIG_HOME": str(config_root),
        }
    )

    completed = subprocess.run(
        [str(APP_RUN), "--show-python"],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert (environment_home / "pyproject.toml").read_text(encoding="utf-8") == template.read_text(encoding="utf-8")
    assert uv_capture.read_text(encoding="utf-8").splitlines() == [
        "sync",
        "--project",
        str(environment_home),
    ]
    assert python_capture.read_text(encoding="utf-8").splitlines() == [
        "-m",
        "ipycalc.launcher",
        "--show-python",
    ]


def test_app_run_reuses_default_uv_environment_without_uv(tmp_path: Path) -> None:
    appdir = tmp_path / "IPyCalc.AppDir"
    (appdir / "opt" / "ipycalc").mkdir(parents=True)
    (appdir / "usr" / "lib" / "kitty.app" / "bin").mkdir(parents=True)
    config_root = tmp_path / "config"
    managed_python = config_root / "ipycalc" / "environment" / ".venv" / "bin" / "python"
    managed_python.parent.mkdir(parents=True)
    capture = tmp_path / "arguments.txt"
    managed_python.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{capture}"\n', encoding="utf-8")
    managed_python.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "APPDIR": str(appdir),
            "PATH": "/usr/bin:/bin",
            "XDG_CONFIG_HOME": str(config_root),
        }
    )

    completed = subprocess.run(
        [str(APP_RUN), "--show-python"],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert capture.read_text(encoding="utf-8").splitlines() == [
        "-m",
        "ipycalc.launcher",
        "--show-python",
    ]
