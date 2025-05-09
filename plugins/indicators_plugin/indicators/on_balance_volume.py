import talib
import numpy as np

def calculate(df, params):
    close = df['Close'].values.astype(float)
    volume = df['Volume'].values.astype(float)
    obv = talib.OBV(close, volume)
    return {
        'OBV': float(obv[-1]) if not np.isnan(obv[-1]) else None
    }, {}
