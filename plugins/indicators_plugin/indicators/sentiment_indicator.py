import talib
import numpy as np

def calculate(df, params):
    sentiment_descriptions = {
        0: 'Oversold',
        25: 'Uneasy',
        40: 'Neutral',
        55: 'Optimistic',
        70: 'Overbought'
    }
    close = df['Close'].values.astype(float)
    high = df['High'].values.astype(float)
    low = df['Low'].values.astype(float)

    # Calculate indicators
    rsi = talib.RSI(close)
    upper, middle, lower = talib.BBANDS(close)
    macd, macdsignal, macdhist = talib.MACD(close)
    ultosc = talib.ULTOSC(high, low, close)
    slowk, slowd = talib.STOCH(high, low, close)

    latestRSI = rsi[-1] if len(rsi) else None
    latestUpperBand = upper[-1] if len(upper) else None
    latestLowerBand = lower[-1] if len(lower) else None
    latestHistogram = macdhist[-1] if len(macdhist) else None
    latestUltimateOscillator = ultosc[-1] if len(ultosc) else None
    latestSlowK = slowk[-1] if len(slowk) else None
    latestSlowD = slowd[-1] if len(slowd) else None

    # RSI-based sentiment value
    def safe(val):
        return 0 if val is None or (isinstance(val, float) and np.isnan(val)) else val
    rsiValue = safe(latestRSI)
    # MACD-based sentiment value
    if latestHistogram is None or (isinstance(latestHistogram, float) and np.isnan(latestHistogram)):
        macdValue = 0
    elif latestHistogram < 0:
        macdValue = 25
    elif latestHistogram == 0:
        macdValue = 50
    else:
        macdValue = 75
    # Ultimate Oscillator-based sentiment value
    ultimateOscillatorValue = safe(latestUltimateOscillator)
    # Stochastic Oscillator-based sentiment value
    if latestSlowK is not None and latestSlowD is not None and not np.isnan(latestSlowK) and not np.isnan(latestSlowD):
        stochasticValue = (latestSlowK + latestSlowD) / 2
    else:
        stochasticValue = 0
    # Bollinger Bands-based sentiment value (not well defined in PHP, so set to 0)
    bbValue = 0
    # Calculate the average sentiment value
    averageSentimentValue = round((rsiValue + bbValue + macdValue + ultimateOscillatorValue + stochasticValue) / 5)
    # Find the closest sentiment description
    sentimentDescription = ''
    for value in sorted(sentiment_descriptions.keys()):
        if averageSentimentValue >= value:
            sentimentDescription = sentiment_descriptions[value]
    return {
        'sentimentValue': averageSentimentValue,
        'sentimentDescription': sentimentDescription
    }, {}
