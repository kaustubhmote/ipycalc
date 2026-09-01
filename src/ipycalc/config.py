from __future__ import annotations

import os
import shutil
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ipycalc.paths import config_home, resource_path


def python_path_file(env: Mapping[str, str] | None = None) -> Path:
    return config_home(env) / "python-path"


def read_python_path(env: Mapping[str, str] | None = None) -> Path | None:
    path_file = python_path_file(env)
    try:
        first_line = path_file.read_text(encoding="utf-8").splitlines()[0].strip()
    except (FileNotFoundError, IndexError, OSError):
        return None
    return Path(first_line).expanduser() if first_line else None


def save_python_path(executable: str | Path, env: Mapping[str, str] | None = None) -> Path:
    resolved = Path(executable).expanduser().resolve(strict=True)
    destination = python_path_file(env)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(destination.parent, 0o700)
    destination.write_text(f"{resolved}\n", encoding="utf-8")
    os.chmod(destination, 0o600)
    return destination


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def load_config(env: Mapping[str, str] | None = None) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {"modules": {}, "functions": {}}
    paths = [resource_path("config.toml"), config_home(env) / "config.toml"]
    for path in paths:
        if not path.is_file():
            continue
        data = _read_toml(path)
        for section in ("modules", "functions"):
            values = data.get(section, {})
            if not isinstance(values, dict):
                raise TypeError(f"{path}: [{section}] must be a table")
            merged[section].update({str(key): str(value) for key, value in values.items()})
    return merged


def init_user_config(env: Mapping[str, str] | None = None) -> tuple[list[Path], list[Path]]:
    destination = config_home(env)
    functions = destination / "functions"
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    functions.mkdir(mode=0o700, parents=True, exist_ok=True)
    created: list[Path] = []
    skipped: list[Path] = []
    copies = (
        (resource_path("config.example.toml"), destination / "config.toml"),
        (resource_path("functions", "_functions_example.py"), functions / "_functions_example.py"),
    )
    for source, target in copies:
        if target.exists():
            skipped.append(target)
            continue
        shutil.copyfile(source, target)
        created.append(target)
    return created, skipped


def custom_function_paths(env: Mapping[str, str] | None = None) -> list[Path]:
    directory = config_home(env) / "functions"
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("_functions*.py") if path.is_file())
