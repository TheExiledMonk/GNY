import importlib
import os


def load_indicator_plugins(indicator_dir):
    plugins = {}
    for fname in os.listdir(indicator_dir):
        if fname.endswith(".py") and fname not in ("__init__.py", "loader.py"):
            name = fname[:-3]
            module = importlib.import_module(f"datawarehouse.indicators.{name}")
            plugins[name] = module
    return plugins


# Usage: plugins = load_indicator_plugins('datawarehouse/indicators')


def run_indicator(plugin, df, params):
    # plugin: loaded module
    # df: pandas DataFrame
    # params: dict
    # Returns: (indicator_data, indicator_settings)
    return plugin.calculate(df, params)
