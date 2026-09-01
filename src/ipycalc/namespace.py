from __future__ import annotations

import hashlib
import importlib
import importlib.util
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from ipycalc.builtins.constants import load_constants
from ipycalc.config import custom_function_paths, load_config

ENTRY_POINT_MARKER = "[ipycalc entry point]"
BUILTIN_FUNCTION_MODULES = (
    "ipycalc.builtins.finance",
    "ipycalc.builtins.special",
)


@dataclass(frozen=True)
class LoadError:
    source: str
    name: str
    message: str


@dataclass(frozen=True)
class LoadResult:
    namespace: dict[str, object]
    errors: tuple[LoadError, ...]


def _function_target(alias: str, specification: str) -> tuple[str, str]:
    if ":" in specification:
        module_name, attribute = specification.split(":", 1)
        return module_name, attribute
    return specification, alias


def _load_configured_names(
    namespace: dict[str, object],
    errors: list[LoadError],
    configuration: Mapping[str, Mapping[str, str]],
) -> None:
    for alias, module_name in configuration.get("modules", {}).items():
        try:
            namespace[alias] = importlib.import_module(module_name)
        except Exception as exc:
            errors.append(LoadError("config.modules", alias, str(exc)))
    for alias, specification in configuration.get("functions", {}).items():
        module_name, attribute = _function_target(alias, specification)
        try:
            namespace[alias] = getattr(importlib.import_module(module_name), attribute)
        except Exception as exc:
            errors.append(LoadError("config.functions", alias, str(exc)))


def _export_marked_functions(module: ModuleType, namespace: dict[str, object]) -> None:
    for name in dir(module):
        value = getattr(module, name)
        docstring = getattr(value, "__doc__", None)
        if callable(value) and isinstance(docstring, str) and ENTRY_POINT_MARKER in docstring:
            namespace[name] = value


def _load_file(path: Path) -> ModuleType:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    module_name = f"_ipycalc_user_{path.stem}_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create an import specification for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_namespace(env: Mapping[str, str] | None = None) -> LoadResult:
    namespace: dict[str, object] = {}
    errors: list[LoadError] = []
    try:
        configuration = load_config(env)
    except Exception as exc:
        configuration = {"modules": {}, "functions": {}}
        errors.append(LoadError("config", "config.toml", str(exc)))
    _load_configured_names(namespace, errors, configuration)
    try:
        namespace.update(load_constants())
    except Exception as exc:
        errors.append(LoadError("builtins", "constants", str(exc)))
    for module_name in BUILTIN_FUNCTION_MODULES:
        try:
            _export_marked_functions(importlib.import_module(module_name), namespace)
        except Exception as exc:
            errors.append(LoadError("builtins", module_name, str(exc)))
    for path in custom_function_paths(env):
        try:
            _export_marked_functions(_load_file(path), namespace)
        except Exception as exc:
            errors.append(LoadError(str(path), path.name, str(exc)))
    try:
        from pint import UnitRegistry

        namespace["unit"] = UnitRegistry()
    except Exception as exc:
        errors.append(LoadError("builtins", "unit", str(exc)))
    return LoadResult(namespace=namespace, errors=tuple(errors))
