from __future__ import annotations

import threading

from ipycalc.namespace import LoadResult, load_namespace
from ipycalc.prompts import set_prompt


def load_ipython_extension(ipython) -> None:
    from rich import traceback

    traceback.install()
    lock = threading.Lock()
    published: dict[str, object] = {}

    def publish(result: LoadResult) -> None:
        for name, previous in published.items():
            if name not in result.namespace and ipython.user_ns.get(name) is previous:
                ipython.user_ns.pop(name, None)
        ipython.user_ns.update(result.namespace)
        published.clear()
        published.update(result.namespace)
        ipython.user_ns["ipycalc_errors"] = result.errors
        ipython.user_ns["ipycalc_ready"] = True
        set_prompt(ipython, ready=True)
        if result.errors:
            ipython.write_err(f"IPyCalc loaded with {len(result.errors)} error(s). Inspect ipycalc_errors.\n")

    def load() -> None:
        if not lock.acquire(blocking=False):
            return
        try:
            ipython.user_ns["ipycalc_ready"] = False
            set_prompt(ipython, ready=False)
            try:
                from matplotlib import style, use

                use("module://ipycalc.backend_kitty")
                style.use("dark_background")
                result = load_namespace()
            except Exception as exc:
                from ipycalc.namespace import LoadError

                result = LoadResult({}, (LoadError("bootstrap", "matplotlib", str(exc)),))
            publish(result)
        finally:
            lock.release()

    def reload_namespace():
        thread = threading.Thread(target=load, name="ipycalc-imports", daemon=True)
        thread.start()
        return thread

    ipython.user_ns.update(
        {
            "ipycalc_ready": False,
            "ipycalc_errors": (),
            "ipycalc_reload": reload_namespace,
        }
    )
    reload_namespace()


def unload_ipython_extension(ipython) -> None:
    for name in ("ipycalc_ready", "ipycalc_errors", "ipycalc_reload"):
        ipython.user_ns.pop(name, None)
