import talib
import numpy as np

from typing import Tuple, Dict, Any
import talib
import numpy as np

def _calculate_indicators(df) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    close = df['Close'].values.astype(float)
    high = df['High'].values.astype(float)
    low = df['Low'].values.astype(float)
    rsi = talib.RSI(close)
    upper, middle, lower = talib.BBANDS(close)
    macd, macdsignal, macdhist = talib.MACD(close)
    ultosc = talib.ULTOSC(high, low, close)
    slowk, slowd = talib.STOCH(high, low, close)
    return rsi, upper, middle, lower, macd, macdhist, ultosc, slowk, slowd

def _calculate_sentiment_values(rsi, macdhist, ultosc, slowk, slowd) -> Tuple[int, int, int, float]:
    def safe(val):
        return 0 if val is None or (isinstance(val, float) and np.isnan(val)) else val
    latest_rsi = rsi[-1] if len(rsi) else None
    latest_hist = macdhist[-1] if len(macdhist) else None
    latest_ultosc = ultosc[-1] if len(ultosc) else None
    latest_slowk = slowk[-1] if len(slowk) else None
    latest_slowd = slowd[-1] if len(slowd) else None
    rsi_value = safe(latest_rsi)
    if latest_hist is None or (isinstance(latest_hist, float) and np.isnan(latest_hist)):
        macd_value = 0
    elif latest_hist < 0:
        macd_value = 25
    elif latest_hist == 0:
        macd_value = 50
    else:
        macd_value = 75
    ultimate_osc_value = safe(latest_ultosc)
    if latest_slowk is not None and latest_slowd is not None and not np.isnan(latest_slowk) and not np.isnan(latest_slowd):
        stochastic_value = (latest_slowk + latest_slowd) / 2
    else:
        stochastic_value = 0
    return rsi_value, macd_value, ultimate_osc_value, stochastic_value

def _get_sentiment_description(value: int) -> str:
    sentiment_descriptions = {0: 'Oversold', 25: 'Uneasy', 40: 'Neutral', 55: 'Optimistic', 70: 'Overbought'}
    description = ''
    for v in sorted(sentiment_descriptions.keys()):
        if value >= v:
            description = sentiment_descriptions[v]
    return description

def calculate(df, params) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rsi, upper, middle, lower, macd, macdhist, ultosc, slowk, slowd = _calculate_indicators(df)
    rsi_value, macd_value, ultimate_osc_value, stochastic_value = _calculate_sentiment_values(rsi, macdhist, ultosc, slowk, slowd)
    bb_value = 0  # Not well defined, set to 0
    avg_sentiment = round((rsi_value + bb_value + macd_value + ultimate_osc_value + stochastic_value) / 5)
    description = _get_sentiment_description(avg_sentiment)
    return {'sentimentValue': avg_sentiment, 'sentimentDescription': description}, {}
