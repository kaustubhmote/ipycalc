from __future__ import annotations

import os
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path


def config_home(env: Mapping[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    if configured := values.get("IPYCALC_CONFIG_HOME"):
        return Path(configured).expanduser()
    if xdg_home := values.get("XDG_CONFIG_HOME"):
        return Path(xdg_home).expanduser() / "ipycalc"
    return Path(values.get("HOME", str(Path.home()))).expanduser() / ".config" / "ipycalc"


def runtime_home(env: Mapping[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    if xdg_runtime := values.get("XDG_RUNTIME_DIR"):
        return Path(xdg_runtime) / "ipycalc"
    uid = os.getuid() if hasattr(os, "getuid") else 0
    return Path("/tmp") / f"ipycalc-{uid}"


def resource_path(*parts: str) -> Path:
    return Path(str(files("ipycalc.resources").joinpath(*parts)))


def package_root() -> Path:
    return Path(__file__).resolve().parents[1]

