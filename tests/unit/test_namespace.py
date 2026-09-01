from __future__ import annotations

import os
import threading
from pathlib import Path
from types import SimpleNamespace

from ipycalc import extension
from ipycalc.namespace import LoadResult, load_namespace


def test_namespace_preserves_cwd_and_loads_builtin_names(tmp_path: Path) -> None:
    before = Path.cwd()
    result = load_namespace({"XDG_CONFIG_HOME": str(tmp_path)})

    assert Path.cwd() == before
    assert result.errors == ()
    for name in ("np", "plt", "sqrt", "unit", "compound_interest", "redor", "π"):
        assert name in result.namespace


def test_broken_custom_file_does_not_block_other_files(tmp_path: Path) -> None:
    function_dir = tmp_path / "ipycalc" / "functions"
    function_dir.mkdir(parents=True)
    (function_dir / "_functions_broken.py").write_text("raise RuntimeError('broken on purpose')\n", encoding="utf-8")
    (function_dir / "_functions_working.py").write_text(
        'def custom_value():\n    """[ipycalc entry point]"""\n    return 42\n',
        encoding="utf-8",
    )

    result = load_namespace({"XDG_CONFIG_HOME": str(tmp_path)})

    assert result.namespace["custom_value"]() == 42
    assert any(error.name == "_functions_broken.py" for error in result.errors)


def test_custom_module_directory_is_not_added_to_sys_path(tmp_path: Path) -> None:
    import sys

    function_dir = tmp_path / "ipycalc" / "functions"
    function_dir.mkdir(parents=True)
    (function_dir / "_functions_empty.py").write_text("VALUE = 1\n", encoding="utf-8")
    before = list(sys.path)

    load_namespace({"XDG_CONFIG_HOME": str(tmp_path)})

    assert sys.path == before
    assert os.fspath(function_dir) not in sys.path


def test_reload_removes_a_name_only_when_the_user_did_not_replace_it(monkeypatch) -> None:
    values = iter(
        (
            LoadResult({"removed": object(), "preserved": object()}, ()),
            LoadResult({}, ()),
        )
    )
    fake_ipython = SimpleNamespace(user_ns={})
    fake_ipython.write_err = lambda message: None
    monkeypatch.setattr(extension, "load_namespace", lambda: next(values))
    monkeypatch.setattr(extension, "set_prompt", lambda *args, **kwargs: None)

    extension.load_ipython_extension(fake_ipython)
    for initial_thread in threading.enumerate():
        if initial_thread.name == "ipycalc-imports":
            initial_thread.join()
    assert fake_ipython.user_ns["ipycalc_ready"]
    fake_ipython.user_ns["preserved"] = "user value"
    reload_thread = fake_ipython.user_ns["ipycalc_reload"]()
    reload_thread.join()

    assert "removed" not in fake_ipython.user_ns
    assert fake_ipython.user_ns["preserved"] == "user value"
