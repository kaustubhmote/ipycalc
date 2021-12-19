import numpy as np
import matplotlib.pyplot as plt
from matplotlib import use
import nmrglue as ng
from numpy import sqrt, exp, pi, sin, cos, tan, log, log10, linspace, arange
from matplotlib.pyplot import plot, show, imshow, contour 
import qutip as q
from sympy import symbols, S, I
from sympy.physics.quantum.spin import JxOp, JyOp, JzOp
from sympy.physics.quantum import IdentityOperator, Commutator, represent
from ipython_prompt import set_prompt
import pulseplot as pplot
from tins import Spins


set_prompt()
use("module://matplotlib-backend-kitty")
plt.style.use("ggplot")
x = np.linspace(-10, 10, 100)
