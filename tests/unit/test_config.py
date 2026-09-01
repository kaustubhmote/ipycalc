from __future__ import annotations

import os
from pathlib import Path

from ipycalc.config import (
    init_user_config,
    load_config,
    read_python_path,
    save_python_path,
)


def test_python_path_round_trip_uses_private_permissions(tmp_path: Path) -> None:
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    destination = save_python_path(Path(os.sys.executable), env)

    assert read_python_path(env) == Path(os.sys.executable).resolve()
    assert destination.stat().st_mode & 0o777 == 0o600
    assert destination.parent.stat().st_mode & 0o777 == 0o700


def test_user_config_replaces_default_values(tmp_path: Path) -> None:
    config_dir = tmp_path / "ipycalc"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        '[modules]\nnp = "numpy.random"\n\n[functions]\nsqrt = "math"\n',
        encoding="utf-8",
    )

    config = load_config({"XDG_CONFIG_HOME": str(tmp_path)})

    assert config["modules"]["np"] == "numpy.random"
    assert config["functions"]["sqrt"] == "math"
    assert config["modules"]["plt"] == "matplotlib.pyplot"


def test_init_user_config_never_overwrites_files(tmp_path: Path) -> None:
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    created, skipped = init_user_config(env)
    original = created[0].read_text(encoding="utf-8")
    created_again, skipped_again = init_user_config(env)

    assert len(created) == 2
    assert skipped == []
    assert created_again == []
    assert len(skipped_again) == 2
    assert created[0].read_text(encoding="utf-8") == original
