# Plugin TODOs

This document tracks the main plugins and their current status or next steps.

## Plugins

- **gather**: ✅ Done
- **fetcher**: 🔄 Receives configuration from gather (list of exchanges, tokens, intervals, database, base stablecoin, etc.).
    - For the 'current' pipeline: fetches all required intervals for the last 24 hours to patch any missing candles.
    - For pipelines including 'historical' (historical or fetch_historical):
        - Start at 2025-01-01 and attempt to fetch 1 candle for each exchange/token/interval.
        - If a candle is found, go 1 year back and repeat, until no candle is found for that date.
        - Once yearly search fails, repeat the process searching by months, then days, then hours, to find the earliest available candle (token listing date).
        - If no candles are found at the start date (2025-01-01), search forward (by month, day, hour) for the first available candle, unless the start date is more than 2 years ago, in which case do the same forward search for the true listing date.
        - Save the discovered listing date for each exchange/token pair in the config to avoid redundant lookups if repopulation is needed.
        - Next, provide the start date for that exchange/token pair to the historical fetcher, which fetches all candles from the start date until now.
        - If intervals have a common denominator (e.g., 1h, 6h, 1d), only fetch the smallest interval (e.g., 1h), and higher intervals will be calculated later by another plugin.
        - If there is no common denominator (e.g., 23m, 57m, 1h), fetch all intervals.
        - Store the fetched candles in the configured database (database name set in the plugin's config page). The collection name will always be <exchangename>_<token><stablecoin>_<interval>.

- **gap**: 🔄 Checks each exchange/token pair in the database for gaps in any interval. If gaps are found, tries to fetch the missing data from the exchange. Receives configuration (including database) from gather. Pipeline type does not matter.
- **aggregate_higher_candles**: 🔄 Calculates higher interval candles from the base/common denominator candles in the database. If some intervals cannot be calculated (e.g., 50m, 1h present but need 6h, 1d), only calculate those that align perfectly (e.g., 6h from 00:00-05:59:59.999, 1d every 24h at 00:00). Stores results in the database specified by gather. If an interval cannot be calculated, the fetcher should have already fetched it.
- **aggregate_allmarkets**: 🔄 Calculates synthetic all-market candles (OHLCV) for each pair (e.g., BTC/USDT) across all exchanges, converting all to the base stablecoin (e.g., USDT) using volume-weighted conversion rates (e.g., USDC/USDT). Two modes: current (only from fetcher candles), historical (all candles in DB). Stores results as allmarket_<pair>_<interval> in the database specified by gather.
- **indicators**: 🔄 For 'current', fetch period+1 candles for each indicator (from indicators.yaml) and calculate the indicator, storing results in the indicator_database from config. For 'historical', process all stored data in the database for each allmarkets tokenpair/interval, storing results in collections named allmarkets_<tokenpair>_<interval>_<indicator>.

---

Add details for each plugin below as context is defined.
