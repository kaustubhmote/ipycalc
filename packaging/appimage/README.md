# Build the IPyCalc AppImage

Run the build from the repository root:

```bash
packaging/appimage/build.sh
```

The script reuses verified Kitty and appimagetool files from `build/downloads/`. It asks whether to check for newer upstream releases. The default answer keeps the cached files. If a newer release exists, the script downloads it and verifies the asset against the SHA-256 digest in GitHub's release metadata.

Set `IPYCALC_REFRESH_DOWNLOADS=always` to check without a prompt. Set it to `never` for an offline or automated build:

```bash
IPYCALC_REFRESH_DOWNLOADS=never packaging/appimage/build.sh
```

The script writes temporary files under `build/` and the finished AppImage under `dist/`.

To populate or update only the download cache, run:

```bash
packaging/appimage/build.sh --downloads-only
```

To inspect the generated AppDir without downloading appimagetool, run:

```bash
packaging/appimage/build.sh --appdir-only
```

To build without downloading Kitty, set `IPYCALC_KITTY_ARCHIVE` to an archive that matches the pinned version and checksum:

```bash
IPYCALC_KITTY_ARCHIVE=/path/to/kitty-0.48.1-x86_64.txz \
    packaging/appimage/build.sh --appdir-only
```

The AppImage contains Kitty and the pure-Python IPyCalc package. On first launch, it uses the host's uv installation to create a Python environment under the IPyCalc configuration directory.

Follow [the complete build and test guide](../../docs/build-and-test-appimage.md) to create the managed environment, add packages, test plotting and custom functions, and install a desktop launcher.
