import numpy as np
import talib


def calculate(df, params):
    period = params.get("Period", 10)
    close = df["Close"].values.astype(float)
    mom = talib.MOM(close, timeperiod=period)
    return {"MOM": float(mom[-1]) if not np.isnan(mom[-1]) else None}, {
        "Period": period
    }
