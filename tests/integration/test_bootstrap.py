from __future__ import annotations

import IPython

from ipycalc import bootstrap


def test_bootstrap_starts_ipython_with_extension(monkeypatch) -> None:
    captured = {}

    def fake_start_ipython(*, argv):
        captured["argv"] = argv

    monkeypatch.setattr(IPython, "start_ipython", fake_start_ipython)

    assert bootstrap.main(["--colors=NoColor"]) == 0
    assert captured["argv"] == [
        "--no-banner",
        "--no-confirm-exit",
        "--ext=ipycalc.extension",
        "--colors=NoColor",
    ]

