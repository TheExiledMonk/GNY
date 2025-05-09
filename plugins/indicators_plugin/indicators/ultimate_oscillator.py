import talib
import numpy as np

def calculate(df, params):
    high = df['High'].values.astype(float)
    low = df['Low'].values.astype(float)
    close = df['Close'].values.astype(float)
    ultosc = talib.ULTOSC(high, low, close)
    latest = ultosc[-1] if len(ultosc) else None
    return {'ultimate_oscillator': float(latest) if latest is not None and not np.isnan(latest) else None}, {}
