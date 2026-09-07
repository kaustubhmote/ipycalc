from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = PROJECT_ROOT / "packaging" / "appimage" / "build.sh"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_versions(tmp_path: Path, kitty: Path, appimagetool: Path, runtime: Path) -> Path:
    versions = tmp_path / "versions.env"
    versions.write_text(
        f"""KITTY_VERSION=1.0.0
KITTY_X86_64_URL={kitty.as_uri()}
KITTY_X86_64_SHA256={_sha256(kitty)}
KITTY_AARCH64_URL={kitty.as_uri()}
KITTY_AARCH64_SHA256={_sha256(kitty)}

APPIMAGETOOL_VERSION=continuous-oldbuild
APPIMAGETOOL_UPDATED_AT=2025-01-01T00:00:00Z
APPIMAGETOOL_X86_64_URL={appimagetool.as_uri()}
APPIMAGETOOL_X86_64_SHA256={_sha256(appimagetool)}
APPIMAGETOOL_AARCH64_URL={appimagetool.as_uri()}
APPIMAGETOOL_AARCH64_SHA256={_sha256(appimagetool)}

APPIMAGE_RUNTIME_VERSION=continuous
APPIMAGE_RUNTIME_X86_64_URL={runtime.as_uri()}
APPIMAGE_RUNTIME_X86_64_SHA256={_sha256(runtime)}
APPIMAGE_RUNTIME_AARCH64_URL={runtime.as_uri()}
APPIMAGE_RUNTIME_AARCH64_SHA256={_sha256(runtime)}
""",
        encoding="utf-8",
    )
    return versions


def _download_environment(tmp_path: Path, versions: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "IPYCALC_ARCH": "x86_64",
            "IPYCALC_BUILD_ROOT": str(tmp_path / "build"),
            "IPYCALC_DIST_DIR": str(tmp_path / "dist"),
            "IPYCALC_VERSIONS_FILE": str(versions),
        }
    )
    return environment


def _create_pinned_downloads(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    kitty = inputs / "kitty.txz"
    appimagetool = inputs / "appimagetool.AppImage"
    runtime = inputs / "runtime"
    kitty.write_bytes(b"cached kitty")
    appimagetool.write_bytes(b"cached appimagetool")
    runtime.write_bytes(b"cached runtime")
    versions = _write_versions(tmp_path, kitty, appimagetool, runtime)

    downloads = tmp_path / "build" / "downloads"
    downloads.mkdir(parents=True)
    (downloads / "kitty-1.0.0-x86_64.txz").write_bytes(kitty.read_bytes())
    (downloads / "appimagetool-continuous-oldbuild-x86_64.AppImage").write_bytes(appimagetool.read_bytes())
    (downloads / "runtime-continuous-x86_64").write_bytes(runtime.read_bytes())
    return versions, kitty, appimagetool, runtime


def test_downloads_only_reuses_verified_cache_without_network(tmp_path: Path) -> None:
    versions, _, _, _ = _create_pinned_downloads(tmp_path)
    environment = _download_environment(tmp_path, versions)
    environment.update(
        {
            "IPYCALC_REFRESH_DOWNLOADS": "never",
            "IPYCALC_KITTY_VERSION_URL": "file:///does-not-exist",
            "IPYCALC_APPIMAGETOOL_RELEASE_API": "file:///does-not-exist",
        }
    )

    completed = subprocess.run(
        [str(BUILD_SCRIPT), "--downloads-only"],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Downloads are ready" in completed.stdout


def test_refresh_does_not_download_same_versions(tmp_path: Path) -> None:
    versions, _, _, _ = _create_pinned_downloads(tmp_path)
    metadata = tmp_path / "metadata"
    metadata.mkdir()
    kitty_version = metadata / "kitty-version.txt"
    kitty_version.write_text("1.0.0\n", encoding="utf-8")
    appimagetool_release = metadata / "appimagetool.json"
    appimagetool_release.write_text(
        '{"target_commitish": "oldbuild", "updated_at": "2025-01-01T00:00:00Z", "assets": []}\n',
        encoding="utf-8",
    )
    environment = _download_environment(tmp_path, versions)
    environment.update(
        {
            "IPYCALC_REFRESH_DOWNLOADS": "always",
            "IPYCALC_KITTY_VERSION_URL": kitty_version.as_uri(),
            "IPYCALC_APPIMAGETOOL_RELEASE_API": appimagetool_release.as_uri(),
        }
    )

    completed = subprocess.run(
        [str(BUILD_SCRIPT), "--downloads-only"],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Cached Kitty 1.0.0 is current." in completed.stdout
    assert "Cached appimagetool is current." in completed.stdout
    assert len(list((tmp_path / "build" / "downloads").iterdir())) == 3


def test_refresh_downloads_and_records_only_newer_releases(tmp_path: Path) -> None:
    versions, _, _, _ = _create_pinned_downloads(tmp_path)
    inputs = tmp_path / "inputs"
    new_kitty = inputs / "new-kitty.txz"
    new_appimagetool = inputs / "new-appimagetool.AppImage"
    new_kitty.write_bytes(b"new kitty")
    new_appimagetool.write_bytes(b"new appimagetool")

    metadata = tmp_path / "metadata"
    metadata.mkdir()
    kitty_version = metadata / "kitty-version.txt"
    kitty_version.write_text("1.1.0\n", encoding="utf-8")
    kitty_release = metadata / "kitty.json"
    kitty_release.write_text(
        f"""{{
  "assets": [{{
    "name": "kitty-1.1.0-x86_64.txz",
    "digest": "sha256:{_sha256(new_kitty)}",
    "browser_download_url": "{new_kitty.as_uri()}"
  }}]
}}
""",
        encoding="utf-8",
    )
    appimagetool_release = metadata / "appimagetool.json"
    appimagetool_release.write_text(
        f"""{{
  "target_commitish": "newbuild12345678",
  "updated_at": "2026-01-01T00:00:00Z",
  "assets": [{{
    "name": "appimagetool-x86_64.AppImage",
    "digest": "sha256:{_sha256(new_appimagetool)}",
    "browser_download_url": "{new_appimagetool.as_uri()}"
  }}]
}}
""",
        encoding="utf-8",
    )
    environment = _download_environment(tmp_path, versions)
    environment.update(
        {
            "IPYCALC_REFRESH_DOWNLOADS": "always",
            "IPYCALC_KITTY_VERSION_URL": kitty_version.as_uri(),
            "IPYCALC_KITTY_RELEASE_API": kitty_release.as_uri(),
            "IPYCALC_APPIMAGETOOL_RELEASE_API": appimagetool_release.as_uri(),
        }
    )

    completed = subprocess.run(
        [str(BUILD_SCRIPT), "--downloads-only"],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    downloads = tmp_path / "build" / "downloads"
    kitty_download = downloads / "kitty-1.1.0-x86_64.txz"
    appimagetool_download = downloads / "appimagetool-continuous-newbuild-x86_64.AppImage"
    assert kitty_download.read_bytes() == new_kitty.read_bytes()
    assert appimagetool_download.read_bytes() == new_appimagetool.read_bytes()
    assert (kitty_download.with_suffix(".txz.sha256")).read_text(encoding="utf-8").strip() == _sha256(new_kitty)
    assert (appimagetool_download.with_suffix(".AppImage.release")).read_text(encoding="utf-8").strip() == (
        "2026-01-01T00:00:00Z"
    )

    (downloads / "kitty-1.0.0-x86_64.txz").unlink()
    (downloads / "appimagetool-continuous-oldbuild-x86_64.AppImage").unlink()
    new_kitty.unlink()
    new_appimagetool.unlink()
    environment["IPYCALC_REFRESH_DOWNLOADS"] = "never"

    cached_run = subprocess.run(
        [str(BUILD_SCRIPT), "--downloads-only"],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert cached_run.returncode == 0, cached_run.stderr
