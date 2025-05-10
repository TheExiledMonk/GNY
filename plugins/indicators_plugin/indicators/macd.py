import numpy as np
import talib


def calculate(df, params):
    fast_period = params.get("Fast_Period", 12)
    slow_period = params.get("Slow_Period", 26)
    signal_period = params.get("Signal_Period", 9)
    close = df["Close"].values.astype(float)
    macd, macdsignal, macdhist = talib.MACD(
        close,
        fastperiod=fast_period,
        slowperiod=slow_period,
        signalperiod=signal_period,
    )
    return {
        "MACD": float(macd[-1]) if not np.isnan(macd[-1]) else None,
        "MACD_signal": float(macdsignal[-1]) if not np.isnan(macdsignal[-1]) else None,
        "MACD_hist": float(macdhist[-1]) if not np.isnan(macdhist[-1]) else None,
    }, {
        "Fast_Period": fast_period,
        "Slow_Period": slow_period,
        "Signal_Period": signal_period,
    }
