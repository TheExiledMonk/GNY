import numpy as np
import talib


def calculate(df, params):
    acceleration = params.get("Acceleration", 0.2)
    maximum = params.get("Maximum", 2)
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)
    sar = talib.SAR(high, low, acceleration=acceleration, maximum=maximum)
    return {"SAR": float(sar[-1]) if not np.isnan(sar[-1]) else None}, {
        "Acceleration": acceleration,
        "Maximum": maximum,
    }
