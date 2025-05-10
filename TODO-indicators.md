# Indicators Plugin: Implementation Sub-TODOs

All indicator calculation modules are implemented under `plugins/indicators_plugin/indicators/` as individual files for each indicator (e.g., `macd.py`, `bollinger_bands.py`, etc.).

This checklist covers the steps needed to implement the indicators plugin.

## 1. Receive and Parse Configuration
- [ ] Receive configuration: indicator_database, allmarkets tokenpairs/intervals, and indicator definitions (from indicators.yaml and gather config).
- [ ] Parse and validate the configuration.

## 2. Indicator Calculation Modes
- [ ] For 'current' mode:
    - [ ] For each indicator, fetch the correct number of candles for the relevant tokenpair/interval:
        - [ ] If Fixed_Day_Interval: true, fetch <multiplier>*Period candles per interval (e.g., 1d=1*Period, 6h=4*Period, 1h=24*Period, 30m=48*Period, etc).
        - [ ] Otherwise, fetch (period + 1) candles (period from indicators.yaml).
    - [ ] Calculate the indicator value(s).
    - [ ] Store results in the indicator_database as specified in config.
- [ ] For 'historical' mode:
    - [ ] For each indicator, process all stored data in the database for each allmarkets tokenpair/interval.
    - [ ] Calculate the indicator value(s) for the full historical dataset.
    - [ ] Store results in collections named allmarkets_<tokenpair>_<interval>_<indicator> in the indicator_database.

## 3. Storage
- [ ] Use the indicator_database name from the config for all writes.
- [ ] Use collection naming format: allmarkets_<tokenpair>_<interval>_<indicator>.

### Example document layout for indicator results
Each indicator result should be stored as a document with the following structure:

```json
{
    "_id": 1746489600000,
    "interval": "1d",
    "DateTime": {
        "$date": { "$numberLong": "1746489600000" }
    },
    "Exchange": "allmarkets",
    "Ticker": "BTCUSDT",
    "IndicatorName": "Bollinger_Bands",
    "IndicatorSettings": {
        "Period": 5,
        "Upper_Deviation_Multiplier": 2,
        "Lower_Deviation_Multiplier": 2,
        "MA_Type": "SMA"
    },
    "IndicatorData": {
        "UpperBand": 97846.909,
        "MiddleBand": 95717.834,
        "LowerBand": 93588.76
    }
}
```

## 4. Error Handling & Logging
- [ ] Log all errors with structured logging (context: tokenpair, interval, indicator, error).
- [ ] Ensure no silent failures; all exceptions must be logged or raised.

## 5. Testing
- [ ] Add unit tests and integration tests for indicator calculation, data fetching, and error handling.

---

Add more details or check off items as implementation progresses.
