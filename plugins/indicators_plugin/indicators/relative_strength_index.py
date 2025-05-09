import talib
import numpy as np

def calculate(df, params):
    period = params.get('Period', 14)
    close = df['Close'].values.astype(float)
    rsi = talib.RSI(close, timeperiod=period)
    return {
        'RSI': float(rsi[-1]) if not np.isnan(rsi[-1]) else None
    }, {'Period': period}
