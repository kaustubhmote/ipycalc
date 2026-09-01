import numpy as np
from scipy.special import jv


def redor(dc, time=None, npts=None):
    """Calculate a REDOR dephasing profile.

    [ipycalc entry point]
    """

    if npts is None:
        npts = 1000
    elif not isinstance(npts, int):
        raise ValueError(f"Number of points must be an integer, not {npts!r}")
    final_time = 10 / dc if time is None else time
    times = np.linspace(1e-10, final_time, npts)
    first = jv(0.25, np.sqrt(2) * dc * times)
    second = jv(-0.25, np.sqrt(2) * dc * times)
    dephasing = 1 - np.sqrt(2) * np.pi / 4 * first * second
    return times, dephasing


def redor_pulse_scaling(mas, plen):
    """Calculate the finite-pulse REDOR scaling factor.

    [ipycalc entry point]
    """

    rotor_period = 1e6 / mas
    fraction = 2 * plen / rotor_period
    return np.cos(0.5 * np.pi * fraction) / (1 - fraction**2)


def binding(Kd, Mt, Lt):
    """Calculate the concentration of a bound species.

    [ipycalc entry point]
    """

    ratio = Kd / Mt
    ligand = Lt / Mt
    term = 1 + ratio + ligand
    fraction_bound = (term - np.sqrt(term**2 - 4 * ligand)) / 2
    return Mt * fraction_bound


def titrate(Kd, Mt, L0, Lf):
    """Calculate a binding titration.

    [ipycalc entry point]
    """

    ligand = np.logspace(L0, Lf, 1000)
    titration = [binding(Kd, Mt, value) / Mt for value in ligand]
    return ligand, np.array(titration)


def s2cone(s):
    """Convert an order parameter to a cone angle.

    [ipycalc entry point]
    """

    root = next(value for value in np.roots([1, 1, -2 * s]) if value > 0)
    return 180 / np.pi * np.arccos(root)


def cone2s(angle):
    """Convert a cone angle to an order parameter.

    [ipycalc entry point]
    """

    cosine = np.cos(np.pi / 180 * angle)
    return 0.5 * cosine * (1 + cosine)


def mw2radius(mw, hydration=2.5, density=1.37):
    """Convert molecular weight in kDa to a hydrated radius in angstroms.

    [ipycalc entry point]
    """

    term = 3 * mw * 1e3 / (4 * np.pi * density * 0.6023)
    return term ** (1 / 3) + hydration


def radius2tc(r, temperature=25, viscosity=None):
    """Convert a radius in angstroms to a correlation time in nanoseconds.

    [ipycalc entry point]
    """

    kelvin = temperature + 273.15
    if viscosity is None:
        coefficient, numerator, offset = 2.414e-5, 247.8, 140
        viscosity = coefficient * 10 ** (numerator / (kelvin - offset))
    return 1e2 * 4 * np.pi * viscosity * r**3 / (3 * 1.380649 * kelvin)


def mw2tc(mw, temperature=25, viscosity=None, hydration=2.5, density=1.37):
    """Convert molecular weight in kDa to correlation time in nanoseconds.

    [ipycalc entry point]
    """

    radius = mw2radius(mw=mw, hydration=hydration, density=density)
    return radius2tc(r=radius, temperature=temperature, viscosity=viscosity)


def ipycalc_version():
    """Print the IPyCalc version.

    [ipycalc entry point]
    """

    from ipycalc import __version__

    print(__version__)
