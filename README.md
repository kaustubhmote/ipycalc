# IPyCalc

IPyCalc opens a focused IPython shell in a Kitty terminal. It loads common scientific names in the background and renders Matplotlib figures inside the terminal.

![IPyCalc demonstration](ipycalc.gif)

## What the AppImage contains

The AppImage contains Kitty and the pure-Python IPyCalc package. It does not contain a general-purpose Python environment or scientific Python packages. Select an existing Python environment before the first launch.

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

The selected environment can be a Conda environment, a uv environment, a virtual environment, or a system Python installation.

## Configure an AppImage

Save the Python interpreter that IPyCalc should use:

```bash
./IPyCalc-1.0.0-x86_64.AppImage \
    --configure-python /absolute/path/to/environment/bin/python
```

Check the environment without opening Kitty:

```bash
./IPyCalc-1.0.0-x86_64.AppImage --check
```

Start IPyCalc:

```bash
./IPyCalc-1.0.0-x86_64.AppImage
```

The AppImage stores the interpreter path in `~/.config/ipycalc/python-path`. If `XDG_CONFIG_HOME` is set, IPyCalc uses `$XDG_CONFIG_HOME/ipycalc/python-path` instead.

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

The repository also includes `ipycalc_conda.yml` as an example Conda environment.

## Build the AppImage

Build from the repository root:

```bash
packaging/appimage/build.sh
```

The build script verifies pinned checksums for Kitty, appimagetool, and the AppImage runtime. It writes the AppDir under `build/` and the AppImage under `dist/`.

See [the AppImage build guide](packaging/appimage/README.md) for an AppDir-only build and local archive overrides. Follow [the complete build and test guide](docs/build-and-test-appimage.md) to configure environments and test every user-visible feature.

## Platform support

The AppImage targets Linux. The first published build targets x86-64. The build script also contains pinned AArch64 inputs, but AArch64 requires its own build and test job.
