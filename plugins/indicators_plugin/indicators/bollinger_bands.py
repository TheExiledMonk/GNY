import talib
import numpy as np

def calculate(df, params):
    period = params.get('Period', 5)
    upper_mult = params.get('Upper_Deviation_Multiplier', 2.0)
    lower_mult = params.get('Lower_Deviation_Multiplier', 2.0)
    ma_type = params.get('MA_Type', 'SMA').upper()
    close = df['Close'].values.astype(float)
    matype = 0 if ma_type == 'SMA' else 1
    upper, middle, lower = talib.BBANDS(close, timeperiod=period, nbdevup=upper_mult, nbdevdn=lower_mult, matype=matype)
    result = {
        'BB_upper': float(upper[-1]) if not np.isnan(upper[-1]) else None,
        'BB_middle': float(middle[-1]) if not np.isnan(middle[-1]) else None,
        'BB_lower': float(lower[-1]) if not np.isnan(lower[-1]) else None
    }
    return result, {
        'Period': period,
        'Upper_Deviation_Multiplier': upper_mult,
        'Lower_Deviation_Multiplier': lower_mult,
        'MA_Type': ma_type
    }
