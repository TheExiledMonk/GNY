import numpy as np
import talib


def calculate(df, params):
    data = df["Close"].values.astype(float)
    period = int(params.get("period", 19))
    ema_period = int(params.get("ema_period", 39))
    if len(data) < max(period, ema_period):
        return {"mcclellan_oscillator": None}, {
            "period": period,
            "ema_period": ema_period,
        }
    ema_short = talib.EMA(data, timeperiod=period)
    ema_long = talib.EMA(data, timeperiod=ema_period)
    mcclellan = ema_short - ema_long
    latest = mcclellan[-1] if len(mcclellan) else None
    return {
        "mcclellan_oscillator": (
            float(latest) if latest is not None and not np.isnan(latest) else None
        )
    }, {"period": period, "ema_period": ema_period}
