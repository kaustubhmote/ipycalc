from __future__ import annotations


def load_constants() -> dict[str, object]:
    import numpy as np

    return {
        "x": np.linspace(-10, 10, 100),
        "ln": np.log,
        "kb": 1.38064852e-23,
        "R": 8.314,
        "h": 6.62607015e-34,
        "hbar": 1.054571817e-34,
        "π": np.pi,
    }

