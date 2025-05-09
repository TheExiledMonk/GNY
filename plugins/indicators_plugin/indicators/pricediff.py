def calculate(df, params):
    closes = df['Close'].values.astype(float)
    if len(closes) < 2:
        return {'price_diff': None}, {}
    price_diff = ((closes[-1] - closes[-2]) / closes[-2]) * 100
    return {'price_diff': round(price_diff, 2)}, {}
