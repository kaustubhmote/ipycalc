import numpy as np
from scipy.special import jv


def redor(dc):
    """
    Calculates the REDOR dephasing profile for 
    a given dipole-dople coupling

    Parameters
    ----------
    dc: float
        dipole-dipole coupling in Hz


    Returns
    -------

    time: np.ndarray
        time points
    ds_s0: np.ndarray
        REDOR dephasing profile

    Usage
    -----
    >>> r = redor(100)
    >>> plt.plot(*r)
    >>> plt.show()

    """

    time = np.linspace(1e-10, 10 / dc, 1000)
    J1 = jv( 0.25, np.sqrt(2) * dc * time)
    J2 = jv(-0.25, np.sqrt(2) * dc * time)
    ds_s0 = 1 - np.sqrt(2) * np.pi / 4 * J1 * J2
    return time, ds_s0
