import talib
import numpy as np

def calculate(df, params):
    fastk_period = params.get('FastK_Period', 5)
    slowk_period = params.get('SlowK_Period', 3)
    slowd_period = params.get('SlowD_Period', 3)
    slowk_ma_type = params.get('SlowK_MA_Type', 'SMA').upper()
    slowd_ma_type = params.get('SlowD_MA_Type', 'SMA').upper()
    high = df['High'].values.astype(float)
    low = df['Low'].values.astype(float)
    close = df['Close'].values.astype(float)
    matype_map = {'SMA': 0, 'EMA': 1}
    slowk_matype = matype_map.get(slowk_ma_type, 0)
    slowd_matype = matype_map.get(slowd_ma_type, 0)
    slowk, slowd = talib.STOCH(high, low, close, fastk_period=fastk_period, slowk_period=slowk_period, slowk_matype=slowk_matype, slowd_period=slowd_period, slowd_matype=slowd_matype)
    return {
        'STOCH_k': float(slowk[-1]) if not np.isnan(slowk[-1]) else None,
        'STOCH_d': float(slowd[-1]) if not np.isnan(slowd[-1]) else None
    }, {
        'FastK_Period': fastk_period,
        'SlowK_Period': slowk_period,
        'SlowD_Period': slowd_period,
        'SlowK_MA_Type': slowk_ma_type,
        'SlowD_MA_Type': slowd_ma_type
    }
