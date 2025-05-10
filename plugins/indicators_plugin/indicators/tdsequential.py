import numpy as np
from typing import Dict, Any, Tuple

def _setup_phase(closes: np.ndarray, length: int) -> Tuple[np.ndarray, int, float, float]:
    setup = np.zeros(length, dtype=int)
    setup_direction = 0
    highest_high = np.nan
    lowest_low = np.nan
    for i in range(length):
        if i < 4:
            continue
        if setup_direction == 0:
            if closes[i] > closes[i - 4]:
                setup[i] = 1
                setup_direction = 1
                highest_high = closes[i]
            elif closes[i] < closes[i - 4]:
                setup[i] = -1
                setup_direction = -1
                lowest_low = closes[i]
        else:
            if setup_direction == 1 and closes[i] > closes[i - 4]:
                setup[i] = setup[i - 1] + 1
                highest_high = max(highest_high, closes[i])
            elif setup_direction == -1 and closes[i] < closes[i - 4]:
                setup[i] = setup[i - 1] - 1
                lowest_low = min(lowest_low, closes[i])
            else:
                setup[i] = 0
                setup_direction = 0
    return setup, setup_direction, highest_high, lowest_low

def _tdst_and_risk(setup: np.ndarray, setup_direction: int, highest_high: float, lowest_low: float, length: int) -> Tuple[np.ndarray, np.ndarray]:
    TDST = np.full(length, np.nan)
    risk_level = np.full(length, np.nan)
    for i in range(length):
        if setup[i] != 0:
            if setup_direction == 1:
                TDST[i] = highest_high
                risk_level[i] = highest_high * 1.05
            elif setup_direction == -1:
                TDST[i] = lowest_low
                risk_level[i] = lowest_low * 0.95
    return TDST, risk_level

def _countdown_phase(closes: np.ndarray, setup_direction: int, length: int) -> Tuple[np.ndarray, bool]:
    countdown = np.zeros(length, dtype=int)
    in_countdown = False
    for i in range(length):
        if in_countdown:
            if setup_direction == 1 and closes[i] <= closes[i - 2]:
                countdown[i] = countdown[i - 1] + 1
            elif setup_direction == -1 and closes[i] >= closes[i - 2]:
                countdown[i] = countdown[i - 1] - 1
            else:
                countdown[i] = countdown[i - 1]
            if abs(countdown[i]) == 13:
                in_countdown = False
    return countdown, in_countdown

def _build_output(setup: np.ndarray, countdown: np.ndarray, TDST: np.ndarray, risk_level: np.ndarray, in_countdown: bool, length: int) -> Dict[str, Any]:
    i = length - 1
    return {
        'setup': int(setup[i]),
        'countdown': int(countdown[i]),
        'TDST': float(TDST[i]) if not np.isnan(TDST[i]) else None,
        'riskLevel': float(risk_level[i]) if not np.isnan(risk_level[i]) else None,
        'exhaustionSignal': 'Yes' if (in_countdown and abs(countdown[i]) == 13) else 'No',
        'perfectSetup': 'Yes' if (abs(setup[i]) == 9 and i >= 8) else 'No'
    }

def calculate(df, params) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    closes = df['Close'].values.astype(float)
    length = len(closes)
    setup, setup_direction, highest_high, lowest_low = _setup_phase(closes, length)
    TDST, risk_level = _tdst_and_risk(setup, setup_direction, highest_high, lowest_low, length)
    countdown, in_countdown = _countdown_phase(closes, setup_direction, length)
    out = _build_output(setup, countdown, TDST, risk_level, in_countdown, length)
    return out, {}

