#!/usr/bin/env python
# -*- coding: utf-8 -*-


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


def compound_interest_years(starting_amount, years, annual_interest_percent_rate):
    """
    Coumpound interest calculator
    [ipycalc entry point]

    Parameters
    ----------
    starting_amount : float
        initial amount
    years : int
        number of years
    annual_interest_percent_rate : float
        percentage interest 
    """

    time_blocks = years * 12
    interest = 1 + annual_interest_rate / 1200

    return compound_interest(starting_amount, time_blocks, interest_per_block)


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
    for _ in range(time_blocks):
        total = total + investment_per_time
        total = total * interest
        total_over_time.append(total)
        total = total_over_time[-1]

    return total_over_time[-1]
