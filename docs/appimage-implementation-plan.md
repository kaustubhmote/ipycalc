# Build IPyCalc as a Kitty AppImage with an external Python environment

## Goal

Build a Linux AppImage that opens the existing IPyCalc experience in a bundled Kitty terminal. The AppImage must use a Python interpreter selected by the user. It must not bundle Python, IPython, NumPy, SciPy, Matplotlib, or the user's custom dependencies.

The first release targets x86-64 Linux. The design must leave room for an AArch64 build without changing the runtime interface.

## Product contract

The AppImage owns these files and behaviors:

- The complete Kitty distribution and its shared libraries.
- The Kitty configuration used for the IPyCalc window.
- The IPyCalc bootstrap, prompt classes, namespace loader, and Matplotlib backend.
- Default constants, default functions, and example configuration.
- The desktop file and application icon.
- Python environment discovery, validation, and error messages.
- Single-window startup and focus behavior.

The user owns these files and behaviors:

- A Python 3.11 or newer interpreter.
- IPython and the scientific packages imported by the default configuration.
- Packages imported by custom functions.
- Persistent configuration under the XDG configuration directory.
- Custom function files.

The AppImage must never modify the selected Python environment. It may inspect the interpreter and import packages to validate the environment.

## Non-goals

The first release will not:

- Bundle a Python runtime or a Conda environment.
- Create, update, or delete a user environment.
- Install missing Python packages.
- Publish a Flatpak, Debian package, RPM package, or macOS application.
- Add a graphical configuration window.
- Add automatic AppImage updates.
- Replace IPython with a custom terminal interface.

## Runtime design

### Select the Python interpreter

Resolve the interpreter in this order:

1. Use the path passed through `--python PATH` for the current launch.
2. Use `IPYCALC_PYTHON` when the environment variable is set.
3. Read the first line of `$XDG_CONFIG_HOME/ipycalc/python-path`.
4. Use `$HOME/.config/ipycalc/python-path` when `XDG_CONFIG_HOME` is unset.
5. Test `python3` from `PATH` as a final fallback.

Add `--configure-python PATH` to validate and save an interpreter. Create the configuration directory with mode `0700` and the `python-path` file with mode `0600`. Store one absolute path followed by a newline. Do not source the file as shell code.

Add `--show-python` to print the resolved interpreter and its source. Add `--check` to validate the interpreter without opening Kitty.

Reject an interpreter when any of these conditions is true:

- The path does not name an executable regular file.
- The interpreter is older than Python 3.11.
- `IPython` cannot be imported.
- A required default dependency cannot be imported.
- The bundled IPyCalc bootstrap cannot start with that interpreter.

Report every missing dependency in one validation run. Do not stop at the first failed import.

The required import set for the first release is:

```text
IPython
matplotlib
numpy
scipy
uncertainties
pint
pendulum
rich
```

Treat `lmfit` and packages referenced only by user functions as optional. Report those failures when the corresponding function module loads.

### Start and focus Kitty

Store the control socket under `$XDG_RUNTIME_DIR/ipycalc/kitty.sock`. If `XDG_RUNTIME_DIR` is unavailable, create `/tmp/ipycalc-$UID` with mode `0700` and place the socket there.

On each launch:

1. Ask the bundled Kitty remote-control client to focus a window through the socket.
2. Exit with status 0 when the focus command succeeds.
3. Remove the socket only when the focus command fails and no process owns it.
4. Start a new Kitty process when no live instance exists.
5. Replace `AppRun` with the Kitty process by using `exec`.

Do not background the first Kitty process. The AppImage mount must remain active while Kitty and the external interpreter read bundled files.

Start Kitty with a dedicated class and title so desktop environments identify the window consistently:

```text
--class org.ipycalc.IPyCalc
--title IPyCalc
```

Keep `allow_remote_control socket-only`. Do not open remote control through a TCP socket.

### Start IPython

Prepend `APPDIR/opt/ipycalc` to `PYTHONPATH`. Call the selected interpreter with the bundled module:

```text
PYTHON -m ipycalc.bootstrap
```

Pass these paths through environment variables:

```text
IPYCALC_APPDIR
IPYCALC_KITTY
IPYCALC_KITTEN
IPYCALC_CONFIG_HOME
```

Prepend the bundled Kitty `bin` directory to `PATH`. The Matplotlib backend must prefer `IPYCALC_KITTEN`, then `IPYCALC_KITTY`, and then executable discovery through `PATH`.

`ipycalc.bootstrap` must call the public `IPython.start_ipython()` API. It must not execute a startup file with `exec(open(...), globals())`.

### Load the namespace

Move namespace construction into a package that accepts explicit paths. No loader function may call `os.chdir()`.

The bootstrap must perform these actions:

1. Install Rich tracebacks.
2. Set the loading prompt.
3. Start one named background thread.
4. Load modules, functions, constants, and custom functions into a temporary dictionary.
5. Insert the completed dictionary into `ipython.user_ns` in one update.
6. Record import errors in `ipycalc_errors`.
7. Set the ready prompt after the namespace update.

Keep the existing `[ipycalc entry point]` docstring marker for backward compatibility. Load custom files with `importlib.util.spec_from_file_location()` and an absolute path. Do not depend on the current working directory or add the custom directory to global `sys.path`.

Expose these diagnostic names inside IPython:

```text
ipycalc_ready
ipycalc_errors
ipycalc_reload
```

`ipycalc_reload()` must rebuild only the user configuration and custom functions. It must leave IPython history and the current working directory unchanged.

### Store user configuration

Use this directory layout:

```text
$XDG_CONFIG_HOME/ipycalc/
├── python-path
├── config.toml
└── functions/
    └── _functions_example.py
```

Use `$HOME/.config/ipycalc` when `XDG_CONFIG_HOME` is unset.

Merge configuration in this order:

1. Read the bundled default configuration.
2. Read the user `config.toml` when it exists.
3. Let user keys replace default keys with the same name.

Add `--init-config` to copy an example configuration and function file without overwriting existing files. Print every skipped path.

### Render Matplotlib figures

Move the backend into the IPyCalc Python package under the importable name `ipycalc.backend_kitty`. Configure Matplotlib with:

```text
module://ipycalc.backend_kitty
```

Preserve the current Agg-to-PNG rendering behavior. Replace the hard-coded `kitty +kitten icat` invocation with the resolved bundled executable.

The backend must:

- Return a useful error when it runs outside Kitty.
- Handle a failed terminal-size query without crashing IPython.
- Preserve the user's current figure size when automatic sizing is disabled.
- Close figure managers only after a successful display.
- Avoid shell command strings. Pass an argument list to `subprocess.run()`.

## Repository changes

### Create the Python package

Replace the current single-file launcher with this source layout:

```text
src/ipycalc/
├── __init__.py
├── bootstrap.py
├── cli.py
├── config.py
├── environment.py
├── launcher.py
├── namespace.py
├── prompts.py
├── backend_kitty.py
└── resources/
    ├── config.toml
    ├── ipycalc_kitty.conf
    └── functions/
```

Rename or remove the current `src/ipycalc` shell script before creating the package directory. Keep compatibility through a generated launcher under `build/`, not through a second source file with the same name.

Add a `pyproject.toml` with:

- Python 3.11 as the minimum version.
- Runtime dependency ranges for the required import set.
- A console script entry point for local development.
- A test dependency group.
- Package-data rules for the configuration and default function files.

Use uv for the development environment and lock file. The AppImage runtime must not call uv.

### Create tracked AppImage sources

Do not commit a populated AppDir. Replace the ignored `IPyCalc.AppDir` experiment with tracked source templates under:

```text
packaging/appimage/
├── AppRun
├── org.ipycalc.IPyCalc.desktop
├── org.ipycalc.IPyCalc.svg
├── build.sh
├── versions.env
└── README.md
```

Generate the working tree under `build/IPyCalc.AppDir`. Keep `build/` ignored.

`versions.env` must pin:

- The Kitty version.
- The Kitty archive URL for each supported architecture.
- The SHA-256 checksum for each Kitty archive.
- The appimagetool version and checksum.

`build.sh` must fail when a checksum does not match. It must never run a downloaded executable before checksum verification.

Generate this AppDir layout:

```text
build/IPyCalc.AppDir/
├── AppRun
├── org.ipycalc.IPyCalc.desktop
├── org.ipycalc.IPyCalc.svg
├── .DirIcon -> org.ipycalc.IPyCalc.svg
├── opt/ipycalc/
│   └── ipycalc/
└── usr/
    ├── bin/
    │   ├── kitty -> ../lib/kitty.app/bin/kitty
    │   └── kitten -> ../lib/kitty.app/bin/kitten
    ├── lib/kitty.app/
    └── share/
        ├── applications/
        └── icons/hicolor/scalable/apps/
```

Preserve the complete Kitty archive layout. Do not copy only the Kitty executable and selected libraries.

Set `Terminal=false` in the desktop file because the application opens its own Kitty window. Use `Categories=Utility;Science;` only if both categories pass `desktop-file-validate`; otherwise keep `Utility;`.

### Remove obsolete installation paths

After the new launcher passes its integration tests:

- Remove the interactive Conda installer from `install.sh`.
- Remove hard-coded checkout paths from all launchers.
- Remove `src/custom/install_custom_conda_env.sh` from the AppImage path.
- Keep the Conda YAML file as an optional environment example.
- Update the README so users know that the AppImage does not contain Python.

Do not remove the legacy source files until tests cover their behavior.

## Implementation phases

### Phase 1: establish the Python package

Create `pyproject.toml`, `uv.lock`, and the `src/ipycalc/` package. Move the prompt classes and default resources without changing behavior.

Acceptance criteria:

- `uv sync` creates the development environment.
- `uv run python -m ipycalc.bootstrap --check` exits successfully in the development environment.
- Package resources resolve from any working directory.
- No production module contains `/opt/labware/ipycalc`.

### Phase 2: implement environment selection

Implement interpreter precedence, persistent configuration, `--configure-python`, `--show-python`, and `--check` in the shell launcher.

Acceptance criteria:

- Each precedence level has a unit test.
- Paths containing spaces work.
- An invalid path produces one actionable error and a nonzero exit status.
- Validation lists all missing required imports.
- No test sources the `python-path` file as shell code.

### Phase 3: refactor namespace loading

Replace `python_thread_import.py` with the package-based namespace loader. Preserve the loading and ready prompts. Keep the existing default names and custom entry-point marker.

Acceptance criteria:

- The default namespace contains the same public names as the current application.
- The process working directory does not change during loading.
- One broken custom file does not block other custom files.
- `ipycalc_errors` records the broken file and exception.
- `ipycalc_reload()` reloads a changed custom function.

### Phase 4: integrate the Kitty backend

Move the backend into `ipycalc.backend_kitty` and resolve the bundled Kitty executable through environment variables.

Acceptance criteria:

- A backend unit test receives an in-memory PNG.
- A stub `kitten` executable receives the expected `icat` arguments and PNG bytes.
- A terminal-size failure falls back to the current Matplotlib figure size.
- `MPLBACKEND_KITTY_SIZING=manual` disables automatic resizing.

### Phase 5: build the launcher and single-instance flow

Implement the control socket, focus behavior, and foreground Kitty launch. Pass the selected interpreter, `-m`, and `ipycalc.bootstrap` as separate arguments.

Acceptance criteria:

- The first launch replaces `AppRun` with Kitty and does not use `&`.
- The second launch focuses the existing window and exits.
- A stale socket does not prevent a new window.
- Socket directories use mode `0700`.
- Launcher tests use a Kitty stub and do not require a display server.

### Phase 6: generate the AppDir and AppImage

Create the tracked templates and reproducible build script. Download the pinned Kitty archive, verify it, assemble the AppDir, and call appimagetool.

Acceptance criteria:

- `desktop-file-validate` accepts the desktop file.
- The root desktop file and icon match the AppDir specification.
- `AppRun` resolves every bundled path relative to `APPDIR`.
- `appimagetool` produces one x86-64 AppImage.
- Extracting the AppImage reproduces the expected AppDir layout.

### Phase 7: run end-to-end tests

Test the AppImage with a disposable uv environment and a disposable Conda environment. The environments must remain outside the AppImage.

For each environment:

1. Configure its Python executable.
2. Launch IPyCalc.
3. Confirm that the prompt appears before background imports finish.
4. Confirm that the prompt changes after imports finish.
5. Evaluate arithmetic, NumPy, Pint, uncertainties, and a SciPy function.
6. Render a Matplotlib plot inside Kitty.
7. Load and call a custom function.
8. Launch the AppImage again and confirm that it focuses the first window.

Acceptance criteria:

- Both environments pass the same behavior checks.
- The AppImage contains no user-facing Python interpreter or scientific Python packages. Kitty may contain its private runtime libraries.
- The AppImage works after it moves to a different directory.
- The selected environment receives no new or modified files.

### Phase 8: document and publish

Update the README and add `packaging/appimage/README.md` with build and troubleshooting instructions. Add a CI workflow that builds the AppImage from a tagged commit and publishes the artifact with a SHA-256 file.

Acceptance criteria:

- A new user can configure an existing environment with one command.
- The documentation lists the required imports and minimum Python version.
- The troubleshooting section covers a missing interpreter, missing packages, an invalid Kitty socket, and plotting outside Kitty.
- CI builds from an empty checkout without using files from a developer machine.

## Test structure

Add these test areas:

```text
tests/
├── unit/
│   ├── test_config.py
│   ├── test_environment.py
│   ├── test_namespace.py
│   └── test_backend_kitty.py
├── integration/
│   ├── test_launcher.py
│   ├── test_bootstrap.py
│   └── test_appdir.py
└── fixtures/
    ├── fake_kitty/
    ├── fake_python/
    └── custom_functions/
```

Run static checks and unit tests on every change. Run AppImage construction and graphical smoke tests in CI jobs that provide the required Linux environment.

## Risks and responses

### The selected Python cannot import bundled code

Put the bundled package first on `PYTHONPATH` and start `ipycalc.bootstrap` with `-m`. Keep IPyCalc code pure Python and compatible with Python 3.11 and newer. Test all supported Python minor versions.

### The AppImage mount disappears

Use `exec` for the first Kitty launch. Do not background Kitty from `AppRun`.

### Kitty cannot find its libraries

Preserve the complete upstream directory layout. Set only the environment variables required by the upstream archive. Test the extracted AppDir before creating the AppImage.

### Scientific package versions differ

Define minimum and excluded versions in one compatibility table. Validate imports at startup. Test the oldest and newest supported dependency sets in CI.

### A custom module blocks startup

Catch errors per file. Continue loading the remaining files. Expose the failures through `ipycalc_errors` and print a compact summary after the prompt becomes ready.

### Background imports race with user input

Build the namespace in a private dictionary. Publish the dictionary in one update. Document that names become available when the prompt changes to the ready color.

### Remote-control sockets outlive Kitty

Use a private runtime directory. Check the socket before deletion. Cover stale-socket recovery with an integration test.

## Commit sequence

Keep the work reviewable with this commit order:

1. `Add Python package and resource layout`
2. `Add external Python selection and validation`
3. `Refactor namespace loading without cwd changes`
4. `Integrate the Kitty Matplotlib backend`
5. `Add the AppImage launcher and single-instance flow`
6. `Add reproducible AppDir and AppImage builds`
7. `Add AppImage integration tests`
8. `Document external Python setup and releases`

Each commit must pass the tests introduced up to that point. Do not combine downloaded Kitty binaries or generated AppImages with source commits.

## Definition of done

The AppImage work is complete when all these statements are true:

- A user can run `IPyCalc.AppImage --configure-python /absolute/path/to/python`.
- A later desktop launch opens a clean Kitty window and starts IPython from that interpreter.
- The default namespace loads in the background and reports failures.
- Custom functions load from the user's XDG configuration directory.
- Matplotlib figures render inside the bundled Kitty terminal.
- A second launch focuses the existing window.
- The AppImage contains Kitty and IPyCalc code but no user-facing Python interpreter. Kitty may contain its private runtime libraries.
- The build uses pinned, checksum-verified inputs.
- CI reproduces and tests the AppImage from an empty checkout.
