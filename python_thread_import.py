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

    from myfuncs import redor, binding, titrate
    setattr(thismodule, "redor", redor)
    setattr(thismodule, "binding", binding)
    setattr(thismodule, "titrate", titrate)
    

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

    myfuncs= {
        "cos": np.cos,
        "sqrt": np.sqrt,
        "exp": np.exp,
        "pi": np.pi,
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "log": np.log,
        "log10": np.log10,
        "linspace": np.linspace,
        "arange": np.arange,
        "x": np.linspace(-10, 10, 100),


        "kb": 1.38064852e-23,
        "R": 8.314,
        "h": 6.62607015e-34,
        "hbar": 1.054571817e-34,

        "imshow": plt.imshow,
        "contour": plt.contour,
        "show": plt.show,
        "plot": plt.plot,
        "scatter": plt.scatter,

        "symbols": sym.symbols,
        "S": sym.S,
        "imag": sym.I,


        "spins": tins.Spins,
        "dipole": tins.Dipole,
        "jcoupling": tins.JCoupling,
        "shift": tins.Shift,
        "quadrupole": tins.Quadrupole,


        "mesolve": qutip.mesolve,
        "commutator": qutip.commutator,

    }

    for k, v in myfuncs.items():
        setattr(thismodule, k, v)

    set_prompt("after")



threading.Thread(target=do_import).start()

