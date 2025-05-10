import numpy as np
import talib


def calculate(df, params):
    period = params.get("Period", 26)
    fast_period = params.get("Fast_Period", 12)
    slow_period = params.get("Slow_Period", 26)
    ma_type = params.get("MA_Type", "SMA").upper()
    close = df["Close"].values.astype(float)
    matype = 0 if ma_type == "SMA" else 1
    apo = talib.APO(
        close, fastperiod=fast_period, slowperiod=slow_period, matype=matype
    )
    return {"APO": float(apo[-1]) if not np.isnan(apo[-1]) else None}, {
        "Period": period,
        "Fast_Period": fast_period,
        "Slow_Period": slow_period,
        "MA_Type": ma_type,
    }
