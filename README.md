# ipycalc

`ipycalc` (IPython Calculator) is a quick way to start an [IPython](https://ipython.org/) console in a [kitty terminal](https://github.com/kovidgoyal/kitty) window. Its main feature is that it loads specified modules (that you regularly use) in the background in a separate non-blocking thread, allowing you to start typing without waiting for all modules to load. Here's how it looks when set up:

![Demo](ipycalc.gif)

## Features

- **Quick plotting** in the terminal using `matplotlib` and `matplotlib-kitty-backend`.
- **Unit conversion** with the `pint` library.
- **Uncertainty calculations** using the `uncertainties` library.
- **Datetime functionality** with the `pendulum` library.
- **Basic financial functions** (e.g., compound interest, SIP).
- **Custom function integration**, allowing you to preload your own functions.

## Installation

`ipycalc` has been tested on Linux and should work on macOS. It won't work on Windows as `kitty` is not yet compatible with WSL.

### Prerequisites

Ensure you have [`conda`](https://docs.conda.io/en/latest/) installed and available in your terminal.

### Steps

1. Clone the `ipycalc` repository and navigate to the directory:
    ```bash
    git clone https://github.com/kaustubhmote/ipycalc
    cd ipycalc
    ```

2. Run the installation script:
    ```bash
    ./install.sh
    ```

The install script will:
- Download [Kitty](https://sw.kovidgoyal.net/kitty/) and place it in the correct location.
- Set up a Python (Conda) environment at `ipycalc/src/ipycalc_conda_env`
- Generate an executable called `ipycalc` in the `src` folder.

### Final Setup

You will need to manually add a keyboard shortcut to run the `ipycalc` script. This will depend on your desktop environment. For GNOME, see [this link](https://help.gnome.org/users/gnome-help/stable/keyboard-shortcuts-set.html.en). I recommend `Ctrl Alt =` as the shortcut.


### Default Functionality

ipycalc runs the equivalent of following import and assignment commands in the background as soon as it starts.

```python
import numpy as np
from numpy import sqrt, pi, sin, cos, tan, log, log10, linspace, arange, random

import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, show, hist, scatter, imshow

import uncertainities.umath as umath
from uncertainities import ufloat

import pint
import pendulum

x = linspace(-10, 10, 100)
ln = np.log
kb =  1.38064852e-23
R = 8.314
h = 6.62607015e-34
hbar = 1.054571817e-34
π = np.pi

```
The loading of functions happens in the background, allowing you to start typing before all functions are fully loaded. The prompt will be colored red if all imports have not been completed and will turn green once they are done. You don't need to wait for the prompt to turn green; you can start typing as soon as the Python console opens.


### Custom Functionality

Inside the `src` folder, there is a folder called `custom`. You can add any number of Python scripts starting with the name `_functions` (e.g., `_functions_pandas.py`). Any function declared in these scripts that has a line declaring `"[ipycalc entry point]"` in its docstring will be automatically imported when you run `ipycalc`. An example script is provided in the folder.

To install any additional packages required by your custom scripts, you can either:

1. Install them directly in the Conda environment that was created.
2. Modify the `.yml` file in the `custom` folder to include the additional libraries. After editing this file, run the `install_custom_conda_env.sh` script to update the Conda environment.



---
