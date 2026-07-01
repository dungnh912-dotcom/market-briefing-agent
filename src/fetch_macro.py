from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import yfinance as yf

from technical import technical_snapshot

logger = logging.getLogger(__name__)


MACRO_SYMBOLS = {
    "US Dollar Index": "DX-Y.NYB",
    "US 10Y Yield": "^TNX",
    "VIX": "^VIX",
}


def fetch_macro(lookback_days: int = 180) -> dict[str, Any]:
    start = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    macro: dict[str, Any] = {}
    for name, ticker in MACRO_SYMBOLS.items():
        try:
            df = yf.download(ticker, start=start, progress=False, auto_adjust=False, threads=False)
            macro[name] = technical_snapshot(df)
            macro[name]["ticker"] = ticker
        except Exception as exc:
            logger.warning("Failed to fetch macro series %s: %s", name, exc)
            macro[name] = {"available": False, "ticker": ticker, "reason": str(exc)}
    return macro
