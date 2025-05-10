# Aggregate Higher Candles Plugin: Implementation Sub-TODOs

This checklist covers the steps needed to implement the aggregate_higher_candles plugin.

## 1. Receive and Parse Configuration
- [ ] Receive configuration: exchanges, tokens, intervals, and database settings (from gather).
- [ ] Parse and validate the configuration.
- [ ] Check for `context['command']` in the plugin and parse/handle command-line arguments if present.

## 2. Base Candle Retrieval
- [ ] For each exchange/token/interval, retrieve the base/common denominator candles from the configured database.
- [ ] Identify which higher intervals can be calculated from the available base candles.

## 3. Aggregation Logic
- [ ] For each required higher interval (e.g., 6h, 1d):
    - [ ] Check if it can be perfectly constructed from the base interval (e.g., 6h = 6 x 1h, aligned to 00:00).
    - [ ] Only calculate and store candles for periods that align perfectly (e.g., 6h from 00:00-05:59:59.999, 1d at 00:00).
    - [ ] If an interval cannot be calculated (e.g., due to missing base data or non-alignment), skip calculation (fetcher should have fetched it).
- [ ] For each calculated aggregate candle, store it with unixtime milliseconds corresponding to the interval start (e.g., 00:00 for 1d).

## 4. Database Storage
- [ ] Store calculated higher interval candles in the database specified by gather.
- [ ] Use collection name format: <exchangename>_<token><stablecoin>_<interval>.

## 5. Error Handling & Logging
- [ ] Log all errors with structured logging (context: exchange, token, interval, error).
- [ ] Ensure no silent failures; all exceptions must be logged or raised.

## 6. Testing
- [ ] Add unit tests and integration tests for aggregation logic, alignment, and error handling.

---

Add more details or check off items as implementation progresses.
