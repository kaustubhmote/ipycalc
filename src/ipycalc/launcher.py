from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ipycalc.config import init_user_config, save_python_path
from ipycalc.environment import format_report, validate_current
from ipycalc.paths import package_root, resource_path, runtime_home


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ipycalc")
    parser.add_argument("--python", metavar="PATH", help="use PATH for this launch")
    parser.add_argument("--configure-python", metavar="PATH", help="validate and save PATH")
    parser.add_argument("--show-python", action="store_true", help="print the selected interpreter")
    parser.add_argument("--check", action="store_true", help="check Python and Kitty without opening a window")
    parser.add_argument("--init-config", action="store_true", help="create example user configuration files")
    return parser


def _same_executable(left: str | Path, right: str | Path) -> bool:
    try:
        return Path(left).samefile(right)
    except (FileNotFoundError, OSError):
        return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()


def _reexec_if_requested(arguments: argparse.Namespace, original: list[str]) -> None:
    requested = arguments.configure_python or arguments.python
    if not requested or _same_executable(requested, sys.executable):
        return
    executable = Path(requested).expanduser()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise SystemExit(f"IPyCalc: Python is not executable: {executable}")
    environment = os.environ.copy()
    root = str(package_root())
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = f"{root}{os.pathsep}{existing}" if existing else root
    os.execve(str(executable.resolve()), [str(executable.resolve()), "-m", "ipycalc.launcher", *original], environment)


def _appdir() -> Path | None:
    value = os.environ.get("IPYCALC_APPDIR") or os.environ.get("APPDIR")
    return Path(value).resolve() if value else None


def find_kitty() -> Path | None:
    if configured := os.environ.get("IPYCALC_KITTY"):
        return Path(configured)
    if appdir := _appdir():
        candidate = appdir / "usr" / "lib" / "kitty.app" / "bin" / "kitty"
        if candidate.is_file():
            return candidate
    if discovered := shutil.which("kitty"):
        return Path(discovered)
    source_candidate = package_root() / "kitty.app" / "bin" / "kitty"
    return source_candidate if source_candidate.is_file() else None


def find_kitten(kitty: Path | None = None) -> Path | None:
    if configured := os.environ.get("IPYCALC_KITTEN"):
        return Path(configured)
    if kitty is not None:
        candidate = kitty.with_name("kitten")
        if candidate.is_file():
            return candidate
    if discovered := shutil.which("kitten"):
        return Path(discovered)
    return None


def _socket_path() -> Path:
    directory = runtime_home()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    return directory / "kitty.sock"


def _focus_existing(kitty: Path, socket: Path) -> bool:
    completed = subprocess.run(
        [str(kitty), "@", "--to", f"unix:{socket}", "focus-window", "--match", "all"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def _check(kitty: Path | None) -> int:
    report = validate_current()
    print(format_report(report))
    if kitty is None or not kitty.is_file():
        print("Kitty: not found")
        return 1
    print(f"Kitty: {kitty}")
    return 0 if report.valid else 1


def _launch(kitty: Path, ipython_arguments: list[str]) -> None:
    socket = _socket_path()
    if _focus_existing(kitty, socket):
        return
    try:
        socket.unlink(missing_ok=True)
    except OSError:
        pass
    kitten = find_kitten(kitty)
    environment = os.environ.copy()
    root = str(package_root())
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = f"{root}{os.pathsep}{existing}" if existing else root
    environment["IPYCALC_KITTY"] = str(kitty)
    if kitten is not None:
        environment["IPYCALC_KITTEN"] = str(kitten)
    if appdir := _appdir():
        environment["IPYCALC_APPDIR"] = str(appdir)
    command = [
        str(kitty),
        "--listen-on",
        f"unix:{socket}",
        "--config",
        str(resource_path("ipycalc_kitty.conf")),
        "--class",
        "org.ipycalc.IPyCalc",
        "--title",
        "IPyCalc",
        "-d",
        str(Path.home()),
        sys.executable,
        "-m",
        "ipycalc.bootstrap",
        *ipython_arguments,
    ]
    os.execvpe(str(kitty), command, environment)


def main(argv: list[str] | None = None) -> int:
    original = list(sys.argv[1:] if argv is None else argv)
    arguments, ipython_arguments = _parser().parse_known_args(original)
    _reexec_if_requested(arguments, original)
    report = validate_current()
    if arguments.configure_python:
        if not report.valid:
            print(format_report(report), file=sys.stderr)
            return 1
        destination = save_python_path(sys.executable)
        print(f"Saved Python interpreter to {destination}")
    if arguments.init_config:
        created, skipped = init_user_config()
        for path in created:
            print(f"Created {path}")
        for path in skipped:
            print(f"Skipped existing file {path}")
    if arguments.show_python:
        print(str(Path(sys.executable).resolve()))
    kitty = find_kitty()
    if arguments.check:
        return _check(kitty)
    if arguments.configure_python or arguments.init_config or arguments.show_python:
        return 0
    if not report.valid:
        print(format_report(report), file=sys.stderr)
        return 1
    if kitty is None:
        print("IPyCalc: cannot find Kitty", file=sys.stderr)
        return 1
    _launch(kitty, ipython_arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
