import talib
import numpy as np

def calculate(df, params):
    high = df['High'].values.astype(float)
    low = df['Low'].values.astype(float)
    close = df['Close'].values.astype(float)
    volume = df['Volume'].values.astype(float)
    fast_period = params.get('Fast_Period', 3)
    slow_period = params.get('Slow_Period', 10)
    adosc = talib.ADOSC(high, low, close, volume, fastperiod=fast_period, slowperiod=slow_period)
    return {
        'ADOSC': float(adosc[-1]) if not np.isnan(adosc[-1]) else None
    }, {'Fast_Period': fast_period, 'Slow_Period': slow_period}
