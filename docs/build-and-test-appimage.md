# Build, use, and test the IPyCalc AppImage

This guide builds the AppImage, connects it to an external Python environment, and tests each user-visible feature.

## Check the host

Use a Linux x86-64 host for the first release. The build script also has AArch64 inputs, but the AArch64 artifact needs a native AArch64 test run.

Install these host commands:

```text
bash
curl
sha256sum
tar
```

Install `desktop-file-validate` and `appstreamcli` to run metadata checks. On Ubuntu or Debian, run:

```bash
sudo apt-get update
sudo apt-get install desktop-file-utils appstream
```

Install uv to build the Python package and run its tests. Confirm the tool versions:

```bash
uv --version
desktop-file-validate --version
appstreamcli --version
```

## Build from the repository

Switch to the implementation branch:

```bash
git switch appimage
```

Create the locked development environment:

```bash
uv sync --locked --group dev
```

Run the static checks and test suite:

```bash
uv run ruff check src/ipycalc tests
MPLCONFIGDIR=/tmp/ipycalc-matplotlib uv run pytest
```

The test run should report 20 passing tests.

Build the wheel and source archive:

```bash
uv build
```

The command writes these files under `dist/`:

```text
ipycalc-1.0.0-py3-none-any.whl
ipycalc-1.0.0.tar.gz
```

Build the AppImage:

```bash
packaging/appimage/build.sh
```

The build script performs these actions:

1. Reads pinned versions and checksums from `packaging/appimage/versions.env`.
2. Downloads Kitty, appimagetool, and the AppImage runtime when they are absent from `build/downloads/`.
3. Verifies every downloaded file with SHA-256.
4. Creates `build/IPyCalc.AppDir`.
5. Validates the desktop and AppStream metadata.
6. Writes `dist/IPyCalc-1.0.0-x86_64.AppImage`.

Inspect the result:

```bash
ls -lh dist/IPyCalc-1.0.0-x86_64.AppImage
file dist/IPyCalc-1.0.0-x86_64.AppImage
sha256sum dist/IPyCalc-1.0.0-x86_64.AppImage
```

The current build is about 40 MB. The exact checksum can change when source files or build metadata change.

### Build only the AppDir

To inspect the directory before packaging it, run:

```bash
packaging/appimage/build.sh --appdir-only
```

Validate its metadata:

```bash
desktop-file-validate build/IPyCalc.AppDir/org.ipycalc.IPyCalc.desktop
appstreamcli validate --no-net \
    build/IPyCalc.AppDir/usr/share/metainfo/org.ipycalc.IPyCalc.appdata.xml
```

Check that the AppDir contains no user-facing Python executable:

```bash
find build/IPyCalc.AppDir -type f \
    \( -name python -o -name python3 -o -name 'python3.*' \) -print
```

No path should print. Kitty includes private runtime libraries, but IPyCalc cannot use them as the user's scientific environment.

## Create an external Python environment with uv

Create a small uv project outside the repository:

```bash
mkdir -p "$HOME/.local/share/ipycalc-env"
cd "$HOME/.local/share/ipycalc-env"
uv init --bare
uv add \
    ipython \
    matplotlib \
    numpy \
    scipy \
    uncertainties \
    pint \
    pendulum \
    rich
```

The interpreter is:

```text
$HOME/.local/share/ipycalc-env/.venv/bin/python
```

Confirm the imports:

```bash
uv run python -c \
    'import IPython, matplotlib, numpy, scipy, uncertainties, pint, pendulum, rich; print("ready")'
```

The command should print `ready`.

## Create an external Python environment with Conda

From the repository, create the supplied environment:

```bash
conda env create \
    --prefix "$HOME/.local/share/ipycalc-conda" \
    --file ipycalc_conda.yml
```

The interpreter is:

```text
$HOME/.local/share/ipycalc-conda/bin/python
```

Confirm the imports:

```bash
"$HOME/.local/share/ipycalc-conda/bin/python" -c \
    'import IPython, matplotlib, numpy, scipy, uncertainties, pint, pendulum, rich; print("ready")'
```

## Configure the AppImage

Return to the repository and set a shell variable:

```bash
cd /path/to/ipycalc
APPIMAGE="$PWD/dist/IPyCalc-1.0.0-x86_64.AppImage"
chmod u+x "$APPIMAGE"
```

Configure the uv interpreter:

```bash
"$APPIMAGE" --configure-python \
    "$HOME/.local/share/ipycalc-env/.venv/bin/python"
```

Or configure the Conda interpreter:

```bash
"$APPIMAGE" --configure-python \
    "$HOME/.local/share/ipycalc-conda/bin/python"
```

IPyCalc writes the resolved path to `~/.config/ipycalc/python-path`. It uses `$XDG_CONFIG_HOME/ipycalc/python-path` when `XDG_CONFIG_HOME` is set.

Print the selected interpreter:

```bash
"$APPIMAGE" --show-python
```

Validate the selected environment and bundled Kitty:

```bash
"$APPIMAGE" --check
```

Expected output has this shape:

```text
Python: /absolute/path/to/python
Version: 3.11-or-newer
Environment: ready
Kitty: /temporary/AppImage/mount/path/usr/lib/kitty.app/bin/kitty
```

## Start IPyCalc

Run:

```bash
"$APPIMAGE"
```

A small Kitty window should open without an IPython banner. The input prompt starts in the loading color and changes to the ready color after background imports finish.

Check the loader state:

```python
ipycalc_ready
ipycalc_errors
```

The expected values are `True` and an empty tuple.

## Test the default namespace

Run these expressions inside IPyCalc:

```python
2 + 2
sqrt(81)
np.mean([1, 2, 3, 4])
(1 * unit.meter).to(unit.centimeter)
ufloat(10, 0.2) * 2
pendulum.now()
compound_interest(1000, 10, 7)
redor_pulse_scaling(10000, 10)
```

Expected results include:

- `4` for arithmetic.
- `9.0` for `sqrt(81)`.
- `2.5` for the NumPy mean.
- `100 centimeter` for the unit conversion.
- An uncertainty value centered on `20`.
- A Pendulum date and time.
- Numeric results for the finance and REDOR helpers.

## Test terminal plotting

Run this expression inside IPyCalc:

```python
plot(x, sin(x))
show()
```

Kitty should display the plot in the terminal. The image should fit the current window width and scroll with the terminal contents.

Test manual sizing:

```bash
MPLBACKEND_KITTY_SIZING=manual "$APPIMAGE"
```

Then run:

```python
plt.figure(figsize=(4, 2))
plot([0, 1, 4])
show()
```

The backend should preserve the requested figure size.

## Test custom functions

Create the example configuration:

```bash
"$APPIMAGE" --init-config
```

The command creates:

```text
~/.config/ipycalc/config.toml
~/.config/ipycalc/functions/_functions_example.py
```

Start IPyCalc and call the example function:

```python
square(7)
```

The result should be `49`.

Edit `_functions_example.py`, then reload it without closing IPython:

```python
thread = ipycalc_reload()
thread.join()
ipycalc_errors
```

The error tuple should remain empty. A function removed from the file also leaves the namespace unless you replaced that name manually during the session.

To test error isolation, add this file:

```text
~/.config/ipycalc/functions/_functions_broken.py
```

Give it this content:

```python
raise RuntimeError("test failure")
```

Reload and inspect the errors:

```python
thread = ipycalc_reload()
thread.join()
ipycalc_errors
square(7)
```

`ipycalc_errors` should identify `_functions_broken.py`. The working `square()` function should still return `49`.

## Test interpreter overrides

Use a different interpreter for one launch:

```bash
"$APPIMAGE" --python /absolute/path/to/another/python --check
```

The command must not change `python-path`.

Test the environment variable override:

```bash
IPYCALC_PYTHON=/absolute/path/to/another/python \
    "$APPIMAGE" --show-python
```

Interpreter selection uses this order:

1. `--python PATH`
2. `IPYCALC_PYTHON`
3. The saved `python-path`
4. `python3` from `PATH`

## Test environment failures

Pass an invalid path:

```bash
"$APPIMAGE" --python /path/that/does/not/exist --check
```

The command should exit nonzero and explain that the Python path is not executable.

Create an environment without the scientific packages:

```bash
uv venv /tmp/ipycalc-empty-env
"$APPIMAGE" --python /tmp/ipycalc-empty-env/bin/python --check
```

The command should exit nonzero and list every missing required import. It must not install anything into the environment.

## Test single-window behavior

Start IPyCalc and leave the window open:

```bash
"$APPIMAGE"
```

Run the same command from another terminal:

```bash
"$APPIMAGE"
```

The second command should focus the first IPyCalc window. It should not create another window.

Close the IPyCalc window, then start it again. A stale socket must not block the new window.

## Test relocation

Copy the AppImage to another directory:

```bash
cp "$APPIMAGE" /tmp/IPyCalc-test.AppImage
chmod u+x /tmp/IPyCalc-test.AppImage
/tmp/IPyCalc-test.AppImage --check
```

The check should still report the configured external interpreter and a Kitty path inside the temporary AppImage mount.

## Run without FUSE

If the host cannot mount AppImages through FUSE, use extraction mode:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGE" --check
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGE"
```

This mode extracts the image before each run, so startup takes longer.

## Add a desktop launcher

Install the AppImage under your user account:

```bash
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
cp "$APPIMAGE" "$HOME/.local/bin/IPyCalc.AppImage"
chmod u+x "$HOME/.local/bin/IPyCalc.AppImage"
```

Create `~/.local/share/applications/org.ipycalc.IPyCalc.desktop` with this content. Replace `/home/YOU` with your absolute home path.

```ini
[Desktop Entry]
Type=Application
Name=IPyCalc
Comment=Open a focused IPython calculator
Exec=/home/YOU/.local/bin/IPyCalc.AppImage
Icon=utilities-terminal
Terminal=false
Categories=Utility;
StartupWMClass=org.ipycalc.IPyCalc
```

Refresh the desktop database when the command is available:

```bash
update-desktop-database "$HOME/.local/share/applications"
```

You can now bind the desktop entry to a keyboard shortcut through your desktop environment.

## Troubleshoot startup

If `--check` reports missing imports, install them into the selected environment. Do not install packages into the AppImage.

If the saved path is wrong, configure it again:

```bash
"$APPIMAGE" --configure-python /correct/path/to/python
```

If plotting reports that Kitty is unavailable, confirm that you started IPyCalc through the AppImage. The backend intentionally rejects a shell that lacks the bundled Kitty tools.

If a stale control socket remains after a crash, close every IPyCalc window before deleting it. The socket is at `$XDG_RUNTIME_DIR/ipycalc/kitty.sock` when `XDG_RUNTIME_DIR` is set. Otherwise it is at `/tmp/ipycalc-$UID/kitty.sock`.

If the AppImage exits before opening a window, run the environment check first:

```bash
"$APPIMAGE" --check
```

Then run extraction mode to separate a FUSE problem from an IPyCalc problem:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGE" --check
```
