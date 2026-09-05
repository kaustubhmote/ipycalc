# IPyCalc

IPyCalc opens a focused IPython shell in a Kitty terminal. It loads common scientific names in the background and renders Matplotlib figures inside the terminal.

![IPyCalc demonstration](ipycalc.gif)

## What the AppImage contains

The AppImage contains Kitty and the pure-Python IPyCalc package. It uses uv to create a Python environment under the IPyCalc configuration directory. The AppImage does not bundle Python or scientific Python packages.

IPyCalc requires Python 3.11 or newer and these imports:

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

Install [uv](https://docs.astral.sh/uv/) on the host before the first launch. uv can download Python when the host does not have a compatible interpreter.

## Create the default environment

Create, sync, and select the default environment:

```bash
./IPyCalc-1.0.0-x86_64.AppImage --init-environment
```

IPyCalc creates the uv project at `~/.config/ipycalc/environment`. If `XDG_CONFIG_HOME` is set, it uses `$XDG_CONFIG_HOME/ipycalc/environment`. A fresh AppImage launch creates the same environment when no other interpreter is configured.

Add custom packages to the environment with `uv add`:

```bash
uv add --project "${XDG_CONFIG_HOME:-$HOME/.config}/ipycalc/environment" \
    sympy qutip
```

The command updates both `pyproject.toml` and `uv.lock`, then syncs `.venv`. You can edit the project file directly and run `uv sync --project PATH` instead.

Check the environment without opening Kitty:

```bash
./IPyCalc-1.0.0-x86_64.AppImage --check
```

Start IPyCalc:

```bash
./IPyCalc-1.0.0-x86_64.AppImage
```

`--init-environment` stores the managed interpreter path in `~/.config/ipycalc/python-path`. If `XDG_CONFIG_HOME` is set, IPyCalc uses `$XDG_CONFIG_HOME/ipycalc/python-path` instead.

To use an existing Python environment instead, save its interpreter:

```bash
./IPyCalc-1.0.0-x86_64.AppImage \
    --configure-python /absolute/path/to/environment/bin/python
```

Use another interpreter for one launch:

```bash
./IPyCalc-1.0.0-x86_64.AppImage --python /another/environment/bin/python
```

`IPYCALC_PYTHON` provides the same one-launch override.

## Create user configuration

Create the example configuration and function file:

```bash
./IPyCalc-1.0.0-x86_64.AppImage --init-config
```

IPyCalc creates this layout without overwriting existing files:

```text
~/.config/ipycalc/
├── python-path
├── config.toml
├── environment/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── .venv/
└── functions/
    └── _functions_example.py
```

Add module aliases and functions to `config.toml`:

```toml
[modules]
fft = "numpy.fft"

[functions]
gamma = "scipy.special"
```

A function in `_functions*.py` enters the namespace when its docstring contains `[ipycalc entry point]`:

```python
def double(value):
    """Return twice the supplied value.

    [ipycalc entry point]
    """

    return 2 * value
```

Run `ipycalc_reload()` inside IPython after changing a custom function. Inspect `ipycalc_errors` when a custom import fails. `ipycalc_ready` becomes `True` when background loading finishes.

## Default namespace

The default configuration loads NumPy as `np`, Matplotlib as `plt`, Pint, Pendulum, uncertainties, common NumPy and Matplotlib functions, physical constants, finance helpers, and the scientific helpers carried by the original IPyCalc implementation.

The input prompt uses the loading color until the namespace is ready. You can type during loading, but a name is unavailable until the ready prompt appears.

## Develop from source

Install uv, then create the locked development environment:

```bash
uv sync --group dev
```

Run the checks:

```bash
uv run ipycalc --check
uv run pytest
```

Run the source version with a system Kitty installation:

```bash
uv run ipycalc
```

## Build the AppImage

Build from the repository root:

```bash
packaging/appimage/build.sh
```

The build script reuses verified Kitty and appimagetool files from `build/downloads/`. In an interactive shell, it asks whether to check for newer upstream releases. Press Enter to keep the cached files. The script verifies new release assets against the SHA-256 digests in GitHub's release metadata.

It writes the AppDir under `build/` and the AppImage under `dist/`.

See [the AppImage build guide](packaging/appimage/README.md) for an AppDir-only build and local archive overrides. Follow [the complete build and test guide](docs/build-and-test-appimage.md) to configure environments and test every user-visible feature.

## Platform support

The AppImage targets Linux. The first published build targets x86-64. The build script also contains pinned AArch64 inputs, but AArch64 requires its own build and test job.
