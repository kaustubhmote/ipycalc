import threading
from rich import traceback

traceback.install()

from ipython_prompt import set_prompt

set_prompt("before")


def do_import():

    import sys

    thismodule = sys.modules[__name__]

    import numpy as np

    setattr(thismodule, "np", np)

    from matplotlib import use

    use("module://matplotlib-backend-kitty")

    from rich import print

    setattr(thismodule, "print", print)

    import _functions

    for function in dir(_functions):
        try:
            f = getattr(_functions, function)
            if "[ipycalc entry point]" in f.__doc__:
                setattr(thismodule, f.__name__, f)
        except (AttributeError, TypeError):
            pass

    import matplotlib.pyplot as plt

    setattr(thismodule, "plt", plt)
    plt.style.use("dark_background")

    import sympy as sym

    setattr(thismodule, "sym", sym)

    import qutip

    setattr(thismodule, "qutip", qutip)

    import tins

    setattr(thismodule, "tins", tins)

    from rich import print

    setattr(thismodule, "print", print)

    to_import = {
        "cos": np.cos,
        "sqrt": np.sqrt,
        "exp": np.exp,
        "pi": np.pi,
        "π": np.pi,
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "log": np.log,
        "ln": np.log,
        "log10": np.log10,
        "linspace": np.linspace,
        "arange": np.arange,
        "x": np.linspace(-10, 10, 100),
        "constants": {
            "kb": 1.38064852e-23,
            "R": 8.314,
            "h": 6.62607015e-34,
            "hbar": 1.054571817e-34,
        },
    }

    for k, v in to_import.items():
        setattr(thismodule, k, v)

    set_prompt("after")


threading.Thread(target=do_import).start()