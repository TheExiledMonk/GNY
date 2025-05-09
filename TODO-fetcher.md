# Fetcher Plugin: Implementation Sub-TODOs

This checklist breaks down the steps required to fully implement the fetcher plugin as described in the main TODO-plugins.md.

## 1. Receive and Parse Configuration
- [ ] Receive configuration from gather: exchanges, tokens, intervals.
- [ ] Parse and validate the configuration.

## 2. Recent Pipeline Logic
- [ ] For the 'recent' pipeline, fetch all required intervals for the last 24 hours for each exchange/token pair.
- [ ] Patch any missing candles in this window.

## 3. Historical Pipeline Logic
- [ ] For pipelines including 'historical' (historical or fetch_historical):
    - [ ] Start at 2025-01-01 for each exchange/token/interval.
    - [ ] Attempt to fetch 1 candle at this date.
    - [ ] If found, go 1 year back and repeat until no candle is found.
    - [ ] Once yearly search fails, repeat by months, then days, then hours to find the earliest available candle (listing date).
    - [ ] If no candles are found at 2025-01-01, search forward (month, day, hour) for the first available candle, unless start date is >2 years ago, then search forward for true listing date.
    - [ ] Save the discovered listing date for each exchange/token pair in the config to avoid redundant lookups.

## 4. Historical Candle Fetching
- [ ] After finding the listing date, fetch all candles from the start date until now for each exchange/token/interval.
- [ ] If intervals have a common denominator (e.g., 1h, 6h, 1d), only fetch the smallest (e.g., 1h); higher intervals will be calculated later by another plugin.
- [ ] If no common denominator (e.g., 23m, 57m, 1h), fetch all intervals.

## 5. Database Storage
- [ ] Store fetched candles in the configured database (database name set in plugin config page).
- [ ] Use collection name format: <exchangename>_<token><stablecoin>_<interval>.

## 6. Error Handling & Logging
- [ ] Log all errors with structured logging (context: exchange, token, interval, error).
- [ ] Ensure no silent failures; all exceptions must be logged or raised.

## 7. Config Persistence
- [ ] Persist discovered listing dates and other relevant metadata in the config/database for future runs.

## 8. Testing
- [ ] Add unit tests and integration tests for all major logic branches (recent, historical, DB storage, error handling).

---

Add more details or check off items as implementation progresses.
