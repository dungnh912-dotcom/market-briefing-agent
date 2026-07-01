from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from sector_mapping import get_sector
from technical import technical_snapshot

logger = logging.getLogger(__name__)

VIETNAM_FALLBACK_REASON = "Chưa lấy được dữ liệu từ vnstock, cần kiểm tra API key hoặc nguồn dữ liệu"
VIETNAM_TECHNICAL_NOTE = (
    "Chưa có dữ liệu kỹ thuật đầy đủ cho cổ phiếu Việt Nam do nguồn vnstock chưa được cấu hình/kích hoạt."
)


def fetch_vietnam_market(symbols: list[str], lookback_days: int = 180) -> dict[str, Any]:
    try:
        return _fetch_vietnam_market(symbols, lookback_days)
    except BaseException as exc:
        logger.exception("Vietnam market data fetch failed; using fallback data: %s", exc)
        return _fallback_vietnam_market(symbols, VIETNAM_FALLBACK_REASON)


def _fetch_vietnam_market(symbols: list[str], lookback_days: int) -> dict[str, Any]:
    stocks: dict[str, Any] = {}
    notes: list[str] = []

    for symbol in symbols:
        data, vnstock_error = _fetch_with_vnstock(symbol, lookback_days)
        if vnstock_error:
            stocks[symbol] = _fallback_stock(symbol, VIETNAM_FALLBACK_REASON)
            notes.append(f"{symbol}: {VIETNAM_FALLBACK_REASON}.")
            continue

        if data is None:
            data = _fetch_with_yfinance_vn(symbol, lookback_days)

        if data is None:
            stocks[symbol] = _fallback_stock(symbol, VIETNAM_FALLBACK_REASON)
            notes.append(f"{symbol}: {VIETNAM_FALLBACK_REASON}.")
            continue

        snapshot = technical_snapshot(data)
        snapshot["sector"] = get_sector(symbol)
        stocks[symbol] = snapshot

    vnindex = _fetch_vnindex(lookback_days)
    if vnindex is None:
        notes.append(VIETNAM_TECHNICAL_NOTE)

    return {
        "stocks": stocks,
        "vnindex": technical_snapshot(vnindex) if vnindex is not None else {"available": False, "reason": VIETNAM_FALLBACK_REASON},
        "notes": notes,
        "technical_note": VIETNAM_TECHNICAL_NOTE,
        "fallback": any(not stock.get("available") for stock in stocks.values()),
    }


def _fetch_with_vnstock(symbol: str, lookback_days: int) -> tuple[pd.DataFrame | None, bool]:
    try:
        from vnstock import Vnstock

        start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")
        stock = Vnstock().stock(symbol=symbol, source="VCI")
        df = stock.quote.history(start=start, end=end, interval="1D")
        if df is None or df.empty:
            return None, False
        return (
            df.rename(
                columns={
                    "time": "Date",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            ).set_index("Date", drop=True),
            False,
        )
    except BaseException as exc:
        logger.warning("vnstock unavailable for %s; using fallback data: %s", symbol, exc)
        return None, True


def _fetch_with_yfinance_vn(symbol: str, lookback_days: int) -> pd.DataFrame | None:
    try:
        start = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        df = yf.download(f"{symbol}.VN", start=start, progress=False, auto_adjust=False, threads=False)
        if df.empty:
            return None
        return df
    except BaseException as exc:
        logger.info("yfinance Vietnam fallback failed for %s: %s", symbol, exc)
        return None


def _fetch_vnindex(lookback_days: int) -> pd.DataFrame | None:
    for symbol in ("VNINDEX", "^VNINDEX", "VNINDEX.VN"):
        if symbol == "VNINDEX":
            data, vnstock_error = _fetch_with_vnstock(symbol, lookback_days)
            if vnstock_error:
                continue
        else:
            data = _fetch_with_yfinance_index(symbol, lookback_days)
        if data is not None and not data.empty:
            return data
    return None


def _fetch_with_yfinance_index(symbol: str, lookback_days: int) -> pd.DataFrame | None:
    try:
        start = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        df = yf.download(symbol, start=start, progress=False, auto_adjust=False, threads=False)
        return None if df.empty else df
    except BaseException:
        return None


def _fallback_vietnam_market(symbols: list[str], reason: str) -> dict[str, Any]:
    return {
        "stocks": {symbol: _fallback_stock(symbol, reason) for symbol in symbols},
        "vnindex": {"available": False, "reason": reason},
        "notes": [VIETNAM_TECHNICAL_NOTE],
        "technical_note": VIETNAM_TECHNICAL_NOTE,
        "fallback": True,
    }


def _fallback_stock(symbol: str, reason: str) -> dict[str, Any]:
    return {
        "available": False,
        "sector": get_sector(symbol),
        "reason": reason,
    }
