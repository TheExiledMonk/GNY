# Aggregate AllMarkets Plugin: Implementation Sub-TODOs

This checklist covers the steps needed to implement the aggregate_allmarkets plugin.

## 1. Receive and Parse Configuration
- [ ] Receive configuration: exchanges, tokens, intervals, base stablecoin, and database settings (from gather).
- [ ] Parse and validate the configuration.
- [ ] Check for `context['command']` in the plugin and parse/handle command-line arguments if present.

## 2. Data Collection
- [ ] For each pair (e.g., BTC/USDT, BTC/USDC, USDC/USDT, etc.) and interval, collect all available candles from all exchanges (from DB).

## 3. Stablecoin Conversion Rate Calculation
- [ ] For each stablecoin pair (e.g., USDC/USDT), calculate the volume-weighted open, high, low, close, and volume, using data from all exchanges (if available).
- [ ] Use these conversion rates to convert all other pairs to the base stablecoin (e.g., all BTC/USDC to BTC/USDT equivalent).

## 4. Synthetic All-Market Candle Calculation
- [ ] For each main pair (e.g., BTC/USDT), aggregate all converted candles across exchanges to compute the true all-market OHLCV, weighted by volume.
- [ ] Ensure precise time alignment for all candles.

## 5. Modes
- [ ] Support 'current' mode: calculate only from the candles produced by fetcher (last 24h).
- [ ] Support 'historical' mode: calculate from all candles in the database.

## 6. Storage
- [ ] Store results as allmarket_<pair>_<interval> in the database specified by gather.

## 7. Error Handling & Logging
- [ ] Log all errors with structured logging (context: pair, interval, error).
- [ ] Ensure no silent failures; all exceptions must be logged or raised.

## 8. Testing
- [ ] Add unit tests and integration tests for conversion, aggregation, and error handling.

---

Add more details or check off items as implementation progresses.
