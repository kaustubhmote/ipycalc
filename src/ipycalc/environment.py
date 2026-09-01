from __future__ import annotations

import importlib
import json
import os
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_IMPORTS = (
    "IPython",
    "matplotlib",
    "numpy",
    "scipy",
    "uncertainties",
    "pint",
    "pendulum",
    "rich",
)


@dataclass(frozen=True)
class EnvironmentReport:
    executable: str
    version: str
    minimum_version: str
    missing: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.missing and not self.errors


def validate_current(imports: Iterable[str] = REQUIRED_IMPORTS) -> EnvironmentReport:
    errors: list[str] = []
    missing: list[str] = []
    if sys.version_info < (3, 11):
        errors.append(f"Python {sys.version.split()[0]} is too old; IPyCalc requires Python 3.11 or newer")
    executable = Path(sys.executable)
    if not executable.is_file() or not os.access(executable, os.X_OK):
        errors.append(f"Python executable is not an executable file: {executable}")
    for module_name in imports:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            missing.append(module_name)
            errors.append(f"cannot import {module_name}: {exc}")
    return EnvironmentReport(
        executable=str(executable.resolve()),
        version=sys.version.split()[0],
        minimum_version="3.11",
        missing=tuple(missing),
        errors=tuple(errors),
    )


def format_report(report: EnvironmentReport) -> str:
    lines = [f"Python: {report.executable}", f"Version: {report.version}"]
    if report.valid:
        lines.append("Environment: ready")
    else:
        lines.append("Environment: invalid")
        lines.extend(f"  - {error}" for error in report.errors)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    report = validate_current()
    if "--json" in arguments:
        payload = asdict(report)
        payload["valid"] = report.valid
        print(json.dumps(payload, sort_keys=True))
    else:
        print(format_report(report))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
