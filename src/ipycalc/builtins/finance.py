def compound_interest_base(starting_amount, time_blocks, interest_per_block):
    """Calculate compound interest for uniform time blocks.

    [ipycalc entry point]
    """

    return starting_amount * ((1 + interest_per_block) ** time_blocks)


def compound_interest(starting_amount, years, annual_interest_percent_rate):
    """Calculate monthly compound interest from an annual percentage rate.

    [ipycalc entry point]
    """

    return compound_interest_base(
        starting_amount,
        years * 12,
        annual_interest_percent_rate / 1200,
    )


def sip_base(seed=0, investment_per_time=0, time_blocks=0, interest_per_block=0):
    """Calculate a recurring investment over uniform time blocks.

    [ipycalc entry point]
    """

    total = seed
    for _ in range(time_blocks):
        total = (total + investment_per_time) * (1 + interest_per_block)
    return total


def sip(seed=0, monthly_investment=0, years=0, annual_interest_percent=0):
    """Calculate a monthly systematic investment plan.

    [ipycalc entry point]
    """

    return sip_base(
        seed=seed,
        investment_per_time=monthly_investment,
        time_blocks=12 * years,
        interest_per_block=annual_interest_percent / 1200,
    )

