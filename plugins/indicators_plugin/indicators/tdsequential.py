def calculate(df, params):
    import numpy as np
    closes = df['Close'].values.astype(float)
    length = len(closes)
    setup = np.zeros(length, dtype=int)
    countdown = np.zeros(length, dtype=int)
    TDST = np.full(length, np.nan)
    riskLevel = np.full(length, np.nan)
    setupDirection = 0
    highestHigh = np.nan
    lowestLow = np.nan
    inCountdown = False
    for i in range(length):
        if i < 4:
            continue
        # Setup Phase
        if setupDirection == 0:
            if closes[i] > closes[i - 4]:
                setup[i] = 1
                setupDirection = 1
                highestHigh = closes[i]
            elif closes[i] < closes[i - 4]:
                setup[i] = -1
                setupDirection = -1
                lowestLow = closes[i]
        else:
            if setupDirection == 1 and closes[i] > closes[i - 4]:
                setup[i] = setup[i - 1] + 1
                highestHigh = max(highestHigh, closes[i])
            elif setupDirection == -1 and closes[i] < closes[i - 4]:
                setup[i] = setup[i - 1] - 1
                lowestLow = min(lowestLow, closes[i])
            else:
                setup[i] = 0
                setupDirection = 0
        # TDST and Risk Level
        if setup[i] != 0:
            if setupDirection == 1:
                TDST[i] = highestHigh
                riskLevel[i] = highestHigh * 1.05
            elif setupDirection == -1:
                TDST[i] = lowestLow
                riskLevel[i] = lowestLow * 0.95
        # Countdown Phase
        if inCountdown:
            if setupDirection == 1 and closes[i] <= closes[i - 2]:
                countdown[i] = countdown[i - 1] + 1
            elif setupDirection == -1 and closes[i] >= closes[i - 2]:
                countdown[i] = countdown[i - 1] - 1
            else:
                countdown[i] = countdown[i - 1]
            if abs(countdown[i]) == 13:
                inCountdown = False
    # Build output dict for last bar
    i = length - 1
    out = {
        'setup': int(setup[i]),
        'countdown': int(countdown[i]),
        'TDST': float(TDST[i]) if not np.isnan(TDST[i]) else None,
        'riskLevel': float(riskLevel[i]) if not np.isnan(riskLevel[i]) else None,
        'exhaustionSignal': 'Yes' if (inCountdown and abs(countdown[i]) == 13) else 'No',
        'perfectSetup': 'Yes' if (abs(setup[i]) == 9 and i >= 8) else 'No'
    }
    return out, {}

