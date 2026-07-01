from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import yfinance as yf

from technical import technical_snapshot

logger = logging.getLogger(__name__)


def fetch_global_markets(symbols: list[str], lookback_days: int = 180) -> dict[str, Any]:
    start = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    result: dict[str, Any] = {}
    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start, progress=False, auto_adjust=False, threads=False)
            snapshot = technical_snapshot(df)
            result[symbol] = snapshot
            if df.empty:
                result[symbol]["note"] = "Không tải được dữ liệu từ yfinance."
        except Exception as exc:
            logger.exception("Failed to fetch global symbol %s", symbol)
            result[symbol] = {"available": False, "reason": str(exc)}
    return result
