#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from scipy.special import jv


def redor(dc):
    """
    Calculates the REDOR dephasing profile for
    a given dipole-dople coupling
    [ipycalc entry point]

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


def redor_pulse_scaling(mas, plen):
    """
    Calculates the scaling factor associated with
    a finite pulse length in REDOR
    [ipycalc entry point]

    Parameters
    ----------
    mas : float
        MAS frequency in Hz
    plen : float
        length of the pi pulse in microseconds

    Returns
    -------
    scaling : float
        scaling factor
    """

    taur = 1e6 / mas
    phi = 2 * plen / taur
    scaling = np.cos(0.5 * np.pi * phi) / (1 - phi**2)

    return scaling


def binding(Kd, Mt, Lt):
    """
        Calculates the concentration of a bound species
    given the Kd, total enzyme concentration and
    total ligand concentration
    [ipycalc entry point]


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
    bound = (b - np.sqrt(b**2 - 4 * c)) / 2

    return Mt * bound


def titrate(Kd, Mt, L0, Lf):
    """
    titration for a system with a given
    Kd and total protein concentration
    [ipycalc entry point]

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


def s2cone(s):
    """
    Convert order-parameter to a cone angle
    [ipycalc entry point]

    Parameters
    ----------
    s : float
        order parameter (not squared)

    Returns
    -------
    angle: float
        cone angle for the Lipari-Sabo diffusion
        in a cone model

    """
    a0, a1, a2 = -2 * s, 1, 1
    root = np.roots([a2, a1, a0])
    root = [r for r in root if r > 0][0]
    angle = 180 / np.pi * np.arccos(root)

    return angle


def cone2s(angle):
    """
    Convert cone angle to order parameter
    [ipycalc entry point]

    Parameters
    ----------
    angle : float
        cone angle in degrees

    Returns
    -------
    s : float
        order parameter (not squared)

    """
    angle = np.pi / 180 * angle
    x = np.cos(angle)
    s = 0.5 * x * (1 + x)

    return s



def mw2radius(mw, hydration=2.5, density=1.37):
    """
    Parameters
    ----------
    mw : float
        molecular weight in kDa
    hydration : float, optional
        lenghth of hydration sphere in Å, default = 2.5 Å
    density : float, optional
        density (gm/mL), default = 1.37 gm/mL 

    Returns
    -------
    radius : float
        radius of the object in Å

    [ipycalc entry point]

    """
    term = 3 * mw * 1e3 / (4 * np.pi * density * 0.6023) 
    radius = term ** (1/3) + hydration

    return radius


def radius2tc(r, temperature=25, viscosity=None):
    """
    Parameters
    ----------
    r : float
        radius of protein in Å
    temperature : int, optional
        temperature in °C, by default 25
    viscosity : _type_, optional
        _description_, by default None

    Returns
    -------
    tc: float
        rotational correlation time in nanoseconds

    [ipycalc entry point]

    """
    temperature += 273.15

    if viscosity is None:
        A, B, C = 2.414e-5, 247.8, 140
        viscosity = A * 10 ** (B / (temperature - C))

    kb = 1.380649
    tc = 1e2 * 4 * np.pi * viscosity * r ** 3 / (3 * kb * temperature) 

    return tc


def mw2tc(mw,  temperature=25, viscosity=None, hydration=2.5, density=1.37):
    """
    Parameters
    ----------
    mw : _type_
        _description_
    temperature : int, optional
        _description_, by default 25
    viscosity : _type_, optional
        _description_, by default None
    hydration : float, optional
        _description_, by default 2.5
    density : float, optional
        _description_, by default 1.37

    Returns
    -------
    _type_
        _description_

    [ipycalc entry point]

    """
    r = mw2radius(mw=mw, hydration=hydration, density=density)
    
    return radius2tc(r=r, temperature=temperature, viscosity=viscosity)