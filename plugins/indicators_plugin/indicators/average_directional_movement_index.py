import talib
import numpy as np

def calculate(df, params):
    period = params.get('Period', 14)
    high = df['High'].values.astype(float)
    low = df['Low'].values.astype(float)
    close = df['Close'].values.astype(float)
    adx = talib.ADX(high, low, close, timeperiod=period)
    return {
        'ADX': float(adx[-1]) if not np.isnan(adx[-1]) else None
    }, {
        'Period': period
    }
