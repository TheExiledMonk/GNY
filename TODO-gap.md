# Gap Plugin: Implementation Sub-TODOs

This checklist covers the steps needed to implement the gap plugin.

## 1. Receive and Parse Configuration
- [ ] Receive configuration from gather: exchanges, tokens, intervals.
- [ ] Parse and validate the configuration.
- [ ] Check for `context['command']` in the plugin and parse/handle command-line arguments if present.

## 2. Gap Detection
- [ ] For each exchange/token/interval in the config, scan the database for missing candle intervals (gaps) using the database specified by gather.
- [ ] Efficiently identify gaps in the time series for each collection.

## 3. Gap Fetching
- [ ] For each gap detected, attempt to fetch the missing candles from the corresponding exchange using the API.
- [ ] Insert the fetched candles into the correct collection in the database (as specified by gather), maintaining the format <exchangename>_<token><stablecoin>_<interval>.

## 4. Error Handling & Logging
- [ ] Log all errors with structured logging (context: exchange, token, interval, gap, error).
- [ ] Ensure no silent failures; all exceptions must be logged or raised.

## 5. Config Persistence
- [ ] Optionally, persist information about gaps that could not be filled for later review or retry.

## 6. Testing
- [ ] Add unit tests and integration tests for gap detection, gap fetching, and error handling.

---

Add more details or check off items as implementation progresses.
