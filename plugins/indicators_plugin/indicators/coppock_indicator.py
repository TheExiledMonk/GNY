import numpy as np

from typing import Tuple, Dict, Any

def calculate(df, params) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Fast Coppock Curve calculation using full numpy vectorization.
    Returns the most recent Coppock value and parameter settings.
    """
    prices = df['Close'].values.astype(float)
    wma_1 = int(params.get('wma_1', 10))
    roc_1 = int(params.get('roc_1', 14))
    roc_2 = int(params.get('roc_2', 11))
    length = len(prices)
    max_period = max(roc_1, roc_2, wma_1)
    if length < max_period + wma_1 - 1:
        return {'coppock': None}, {'wma_1': wma_1, 'roc_1': roc_1, 'roc_2': roc_2}

    # Vectorized ROC calculations
    with np.errstate(divide='ignore', invalid='ignore'):
        roc1 = np.full(length, np.nan)
        roc2 = np.full(length, np.nan)
        valid1 = prices[:-roc_1] != 0
        valid2 = prices[:-roc_2] != 0
        roc1[roc_1:] = np.where(valid1, (prices[roc_1:] - prices[:-roc_1]) / prices[:-roc_1], np.nan)
        roc2[roc_2:] = np.where(valid2, (prices[roc_2:] - prices[:-roc_2]) / prices[:-roc_2], np.nan)
        coppock_raw = roc1 + roc2

    # Fast weighted moving average using stride tricks
    def weighted_moving_average(arr: np.ndarray, window: int, weights: np.ndarray) -> np.ndarray:
        from numpy.lib.stride_tricks import sliding_window_view
        arr = arr.astype(float)
        out = np.full_like(arr, np.nan)
        if len(arr) < window:
            return out
        windows = sliding_window_view(arr, window_shape=window)
        mask = ~np.isnan(windows).any(axis=1)
        result = np.full(windows.shape[0], np.nan)
        valid_idx = np.where(mask)[0]
        if valid_idx.size > 0:
            result[valid_idx] = np.dot(windows[mask], weights) / weights.sum()
        out[window-1:] = result
        return out

    w = np.arange(wma_1, 0, -1)
    wma = weighted_moving_average(coppock_raw, wma_1, w)
    latest = wma[-1] if not np.isnan(wma[-1]) else None
    return {'coppock': float(latest) if latest is not None else None}, {'wma_1': wma_1, 'roc_1': roc_1, 'roc_2': roc_2}

