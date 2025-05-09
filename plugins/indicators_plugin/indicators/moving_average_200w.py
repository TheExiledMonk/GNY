import talib
import numpy as np

def get_multiplier(interval):
    if interval.endswith('m'):
        return int(10080 / int(interval[:-1]))
    elif interval.endswith('h'):
        return int(168 / int(interval[:-1]))
    elif interval.endswith('d'):
        return 7
    elif interval.endswith('w'):
        return 1
    else:
        return 1

def calculate(df, params):
    period = 200
    interval = params.get('Interval', '1w')
    multiplier = get_multiplier(interval)
    lookback = int(period * multiplier)
    close = df['Close'].values.astype(float)
    if lookback > len(close):
        return {'MA200w': None}, {'Lookback': lookback, 'Interval': interval}
    ma = talib.SMA(close, timeperiod=lookback)
    return {
        'MA200w': float(ma[-1]) if not np.isnan(ma[-1]) else None
    }, {'Lookback': lookback, 'Interval': interval}
