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
    J1 = jv(0.25, np.sqrt(2) * dc * time)
    J2 = jv(-0.25, np.sqrt(2) * dc * time)
    ds_s0 = 1 - np.sqrt(2) * np.pi / 4 * J1 * J2
    return time, ds_s0


def binding(Kd, Mt, Lt):
    """
        Calculates the concentration of a bound species
    given the Kd, total enzyme concentration and 
    total ligand concentration


    Parameters
    ----------
    Kd : float
        dissociatio constant
    Mt : float
        total protein concentration
    Lt : float
        total ligand concentration

    Returns
    -------
    bound : float
        total concentratioin of bound species
    """

    r = Kd / Mt
    x = Lt / Mt
    b = 1 + r + x
    a = 1
    c = x
    bound = (b - np.sqrt(b ** 2 - 4 * c)) / 2

    return Mt * bound


def titrate(Kd, Mt, L0, Lf):
    """
    titration for a system with a given
    Kd and total protein concentration

    Parameters
    ----------
    Kd : float
        dissociation constant
    Mt : float
        total protein concentration
    L0 : float
        exponent of initial ligand conc.
        concentration is 10^L0
    Lf : float
        exponent of final ligand conc.

    Returns
    -------
    ligand : np.ndarray
        array of ligand cocentrations
    titration : np.ndarray
        array of fraction bound at each ligand 
        concentration
    """

    ligand = np.logspace(L0, Lf, 1000)
    titration = [binding(Kd, Mt, L) / Mt for L in ligand]

    return ligand, np.array(titration)
