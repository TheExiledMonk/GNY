import numpy as np
import talib


def calculate(df, params):
    open_ = df["Open"].values.astype(float)
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)
    close = df["Close"].values.astype(float)
    avgprice = talib.AVGPRICE(open_, high, low, close)
    return {"AVGPRICE": float(avgprice[-1]) if not np.isnan(avgprice[-1]) else None}, {}
