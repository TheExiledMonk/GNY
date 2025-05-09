import talib
import numpy as np

def calculate(df, params):
    period = params.get('Period', 10)
    close = df['Close'].values.astype(float)
    ema = talib.EMA(close, timeperiod=period)
    return {
        'EMA': float(ema[-1]) if not np.isnan(ema[-1]) else None
    }, {'Period': period}
