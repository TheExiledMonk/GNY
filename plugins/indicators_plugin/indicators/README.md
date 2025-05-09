# Indicator Plugin System

This directory contains indicator calculation plugins for DataWarehouse.

## How to Add an Indicator
- Add a new Python file (e.g., `macd.py`) with a `calculate(df, params)` function.
- Use TA-Lib (from GitHub) for indicator calculations.
- The function should return `(indicator_data: dict, indicator_settings: dict)`.
- `indicator_data` keys/structure are adjustable per plugin.

## Example Plugin: Bollinger Bands
```
def calculate(df, params):
    # ...
    return {
        'UpperBand': ...,
        'MiddleBand': ...,
        'LowerBand': ...,
    }, params
```

## Loader
- Use `loader.py` to dynamically load all plugins and run calculations.
