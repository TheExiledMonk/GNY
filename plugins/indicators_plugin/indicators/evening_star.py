import talib


def calculate(df, params):
    open_ = df["Open"].values.astype(float)
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)
    close = df["Close"].values.astype(float)
    val = talib.CDLEVENINGSTAR(open_, high, low, close)
    return {"CDLEVENINGSTAR": int(val[-1])}, params
