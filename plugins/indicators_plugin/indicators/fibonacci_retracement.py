import numpy as np

from typing import Tuple, Dict, Any

def calculate(df, params) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Fast Fibonacci retracement calculation using numpy vectorization.
    Returns only the last period's levels as named keys.
    """
    fib_levels = np.array([0, 0.236, 0.382, 0.5, 0.618, 0.786, 1])
    reverse = params.get('Reverse', False)
    highs = df['High'].values.astype(float)
    lows = df['Low'].values.astype(float)
    if highs.size == 0 or lows.size == 0:
        return {f'Fib_{str(f)}': None for f in fib_levels}, {'Reverse': reverse}
    if reverse:
        fibs = fib_levels[::-1]
        h, low_val = lows[-1], highs[-1]
    else:
        fibs = fib_levels
        h, low_val = highs[-1], lows[-1]
    levels = h - (h - low_val) * fibs
    result = {f'Fib_{str(f)}': float(v) for f, v in zip(fib_levels, levels)}
    return result, {'Reverse': reverse}
