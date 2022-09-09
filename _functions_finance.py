import numpy as np


def compound_interest(starting_amount, time_blocks, interest_per_block):
    """
    Coumpound interest calculator
    [ipycalc entry point]

    Parameters
    ----------
    starting_amount : float
        initial amount
    time_blocks : int
        number of blocks (years/months/daays)
    interest_per_block : float
        interest per time block

    """

    interest = 1 + interest_per_block

    return starting_amount * (interest ** time_blocks)


def sip(seed=0, investment_per_time=0, time_blocks=0, interest_per_block=0):
    """
    _summary_

    [ipycalc entry point]

    Parameters
    ----------
    seed : int, optional
        _description_, by default 0
    investment_per_time : int, optional
        _description_, by default 0
    time_blocks : int, optional
        _description_, by default 0
    interest_per_block : int, optional
        _description_, by default 0

    Returns
    -------
    _type_
        _description_


    """

    interest = 1 + interest_per_block

    total_over_time = []
    total = seed
    for i in range(time_blocks):
        total = total + investment_per_time
        total = total * interest
        total_over_time.append(total)
        total = total_over_time[-1]

    return total_over_time[-1]
