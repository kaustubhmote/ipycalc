# Build the IPyCalc AppImage

Run the build from the repository root:

```bash
packaging/appimage/build.sh
```

The script downloads checksum-pinned Kitty, appimagetool, and AppImage runtime artifacts. It writes temporary files under `build/` and the finished AppImage under `dist/`.

To inspect the generated AppDir without downloading appimagetool, run:

```bash
packaging/appimage/build.sh --appdir-only
```

To build without downloading Kitty, set `IPYCALC_KITTY_ARCHIVE` to an archive that matches the pinned version and checksum:

```bash
IPYCALC_KITTY_ARCHIVE=/path/to/kitty-0.48.1-x86_64.txz \
    packaging/appimage/build.sh --appdir-only
```

The AppImage contains Kitty and the pure-Python IPyCalc package. It uses a Python environment configured by the user.

Follow [the complete build and test guide](../../docs/build-and-test-appimage.md) to create an environment, configure the AppImage, test plotting and custom functions, and install a desktop launcher.
