import talib
import numpy as np

def get_multiplier(interval):
    if interval.endswith('m'):
        return int(1440 / int(interval[:-1]))
    elif interval.endswith('h'):
        return int(24 / int(interval[:-1]))
    elif interval.endswith('d'):
        return 1
    elif interval.endswith('w'):
        return 1 / 7
    else:
        return 1

def calculate(df, params):
    period = 20
    interval = params.get('Interval', '1d')
    multiplier = get_multiplier(interval)
    lookback = int(period * multiplier)
    close = df['Close'].values.astype(float)
    if lookback > len(close):
        return {'EMA20d': None}, {'Lookback': lookback, 'Interval': interval}
    ema = talib.EMA(close, timeperiod=lookback)
    return {
        'EMA20d': float(ema[-1]) if not np.isnan(ema[-1]) else None
    }, {'Lookback': lookback, 'Interval': interval}
