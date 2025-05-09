from typing import List, Dict, Any
import ccxt
import re
import json
from bson import ObjectId

def get_default_config() -> Dict[str, Any]:
    """
    Return the config schema for the Gather plugin.
    All operational defaults (e.g., intervals) must come from the config system/database, not from code.
    """
    return {
        "exchanges": [],
        "tokens": [],
        "stablecoins": [],
        "base_stablecoin": None,
        "intervals": [],  # Always present, but empty by default
        "exchange_tokenpairs": {},  # Always present, but empty by default
        "exchange_database": "",
        "indicator_database": ""
    }

def get_supported_exchanges() -> List[str]:
    """
    Return a list of exchanges that have fetchOHLCV capability (candles).

    Returns:
        List[str]: Alphabetically sorted list of supported exchange names.
    """
    supported = []
    from fastapi import logger as fastapi_logger
    for ex in ccxt.exchanges:
        try:
            ex_obj = getattr(ccxt, ex)()
            if ex_obj.has.get('fetchOHLCV') is True:
                supported.append(ex)
        except (ccxt.BaseError, AttributeError, KeyError) as err:
            fastapi_logger.error({
                "event": "gather_plugin_exchange_capability_check_failed",
                "exchange": ex,
                "error": str(err)
            })
            continue
    return sorted(supported)

def _get_markets_for_exchanges(exchanges: List[str]) -> dict:
    """
    Fetch and return markets dict for each exchange only once.

    Args:
        exchanges (List[str]): List of exchange names.
    Returns:
        dict: Mapping of exchange name to markets dict (may be empty if error).
    """
    markets_per_exchange = {}
    from fastapi import logger as fastapi_logger
    for ex in exchanges:
        try:
            ex_obj = getattr(ccxt, ex)()
            markets_per_exchange[ex] = ex_obj.load_markets()
        except (ccxt.BaseError, AttributeError, KeyError) as err:
            fastapi_logger.error({
                "event": "gather_plugin_market_load_failed",
                "exchange": ex,
                "error": str(err)
            })
            markets_per_exchange[ex] = {}
    return markets_per_exchange

def get_tokens_for_exchanges(exchanges: List[str]) -> List[str]:
    """
    Return a sorted list of available tokens across selected exchanges (no duplicates),
    filtering out synthetic/leveraged tokens (e.g., ADA3L, ADAUP, etc).

    Args:
        exchanges (List[str]): List of exchange names.
    Returns:
        List[str]: Sorted list of unique token symbols.
    """
    from fastapi import logger as fastapi_logger
    tokens: set[str] = set()
    synthetic_pattern = re.compile(r"(3L|3S|5L|5S|UP|DOWN)$", re.IGNORECASE)
    try:
        markets_per_exchange = _get_markets_for_exchanges(exchanges)
        for markets in markets_per_exchange.values():
            for m in markets.values():
                if 'base' in m:
                    base = m['base']
                    if not synthetic_pattern.search(base):
                        tokens.add(base)
    except Exception as err:
        fastapi_logger.error({
            "event": "gather_plugin_tokens_extraction_failed",
            "function": "get_tokens_for_exchanges",
            "exchanges": exchanges,
            "error": str(err)
        })
        raise
    return sorted(tokens)

def get_stablecoins_for_exchanges(exchanges: List[str]) -> List[str]:
    """
    Return a sorted list of available stablecoins across selected exchanges (no duplicates).

    Args:
        exchanges (List[str]): List of exchange names.
    Returns:
        List[str]: Sorted list of unique stablecoin symbols.
    """
    from fastapi import logger as fastapi_logger
    stablecoin_candidates: set[str] = {
        'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'PAX', 'GUSD', 'USDP', 'USDS', 'SUSD', 'EURS', 'USDN', 'USDK', 'XUSD', 'EURT', 'USDSB', 'USDTZ', 'UST', 'FRAX', 'LUSD', 'USD', 'FDUSD', 'PYUSD', 'ALUSD', 'MIM', 'FEI', 'HUSD', 'QUSD', 'CUSD', 'XSGD', 'BUSD', 'XUSD', 'VAI', 'RSV', 'CEUR', 'BIDR', 'TRYB', 'BRZ', 'NZDS', 'ZUSD', 'GUSD', 'JPYC', 'XIDR', 'USDP', 'USDX', 'USDS', 'TUSD', 'DAI', 'PAX', 'SUSD', 'EURS', 'USDN', 'USDK', 'XUSD', 'EURT', 'USDSB', 'USDTZ', 'UST', 'FRAX', 'LUSD', 'USD', 'FDUSD', 'PYUSD', 'ALUSD', 'MIM', 'FEI', 'HUSD', 'QUSD', 'CUSD', 'XSGD', 'VAI', 'RSV', 'CEUR', 'BIDR', 'TRYB', 'BRZ', 'NZDS', 'ZUSD', 'JPYC', 'XIDR', 'USDX'
    }
    found_stablecoins: set[str] = set()
    try:
        markets_per_exchange = _get_markets_for_exchanges(exchanges)
        for markets in markets_per_exchange.values():
            for m in markets.values():
                if 'quote' in m:
                    quote = m['quote']
                    if quote in stablecoin_candidates:
                        found_stablecoins.add(quote)
    except Exception as err:
        fastapi_logger.error({
            "event": "gather_plugin_stablecoins_extraction_failed",
            "function": "get_stablecoins_for_exchanges",
            "exchanges": exchanges,
            "error": str(err)
        })
        raise
    return sorted(found_stablecoins)


def get_config_ui() -> Dict[str, Any]:
    """Return default config structure for the plugin (used for form defaults)."""
    return get_default_config()
