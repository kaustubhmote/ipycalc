from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--check"]:
        from ipycalc.environment import main as environment_main

        return environment_main([])
    from IPython import start_ipython

    defaults = ["--no-banner", "--no-confirm-exit", "--ext=ipycalc.extension"]
    start_ipython(argv=[*defaults, *arguments])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
