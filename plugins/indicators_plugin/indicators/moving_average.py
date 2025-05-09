import talib
import numpy as np

def calculate(df, params):
    period = params.get('Period', 14)
    ma_type = params.get('MA_Type', 'SMA').upper()
    close = df['Close'].values.astype(float)
    if ma_type == 'EMA':
        ma = talib.EMA(close, timeperiod=period)
    else:
        ma = talib.SMA(close, timeperiod=period)
    return {
        'MA': float(ma[-1]) if not np.isnan(ma[-1]) else None
    }, {'Period': period, 'MA_Type': ma_type}
