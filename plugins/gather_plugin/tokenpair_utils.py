"""
Utility for calculating supported token pairs per exchange, given selected tokens and stablecoins.
"""

from typing import Dict, List

import ccxt


def get_supported_tokenpairs_for_exchange(
    exchange_name: str, tokens: List[str], stablecoins: List[str]
) -> List[str]:
    """
    For a given exchange, return all supported token pairs of the form TOKEN/STABLECOIN,
    plus stablecoin-to-stablecoin pairs (e.g., USDC/USDT), based on what the exchange supports.
    """
    try:
        ex_obj = getattr(ccxt, exchange_name)()
        markets = ex_obj.load_markets()
    except Exception:
        return []
    pairs = []
    # Token/Stablecoin pairs
    for token in tokens:
        for stable in stablecoins:
            symbol = f"{token}/{stable}"
            if symbol in markets:
                pairs.append(symbol)
    # Stablecoin-to-stablecoin pairs
    for i, s1 in enumerate(stablecoins):
        for s2 in stablecoins[i + 1 :]:
            for a, b in [(s1, s2), (s2, s1)]:
                symbol = f"{a}/{b}"
                if symbol in markets:
                    pairs.append(symbol)
    return pairs


def get_all_exchange_tokenpairs(
    exchanges: List[str], tokens: List[str], stablecoins: List[str]
) -> Dict[str, List[str]]:
    """
    For each exchange, compute the supported token pairs using get_supported_tokenpairs_for_exchange.
    """
    result = {}
    for ex in exchanges:
        pairs = get_supported_tokenpairs_for_exchange(ex, tokens, stablecoins)
        result[ex] = pairs
    return result
