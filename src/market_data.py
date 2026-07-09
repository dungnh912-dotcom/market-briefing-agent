from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf


LOGGER = logging.getLogger(__name__)


def direction_marker(change_pct: float | None) -> str:
    if change_pct is None:
        return "●"
    if change_pct > 0.05:
        return "▲"
    if change_pct < -0.05:
        return "▼"
    return "●"


def fetch_symbol(label: str, symbol: str, lookback_days: int) -> dict[str, Any]:
    try:
        history = yf.Ticker(symbol).history(period=f"{lookback_days}d", interval="1d")
        if history.empty or "Close" not in history:
            LOGGER.warning("No yfinance data for %s (%s)", label, symbol)
            return unavailable_metric(label, symbol, "Nguồn dữ liệu chưa trả kết quả.")

        close = history["Close"].dropna()
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else last
        change = last - prev
        change_pct = (change / prev * 100) if prev else 0.0
        volume = None
        if "Volume" in history and not history["Volume"].dropna().empty:
            volume = float(history["Volume"].dropna().iloc[-1])

        return {
            "label": label,
            "symbol": symbol,
            "value": last,
            "change": change,
            "change_pct": change_pct,
            "direction": direction_marker(change_pct),
            "display": f"{last:,.2f}",
            "change_display": f"{change:+,.2f} ({change_pct:+.2f}%)",
            "volume": volume,
            "note": None,
        }
    except Exception as exc:
        LOGGER.warning("Failed to fetch %s (%s): %s", label, symbol, exc)
        return unavailable_metric(label, symbol, str(exc))


def unavailable_metric(label: str, symbol: str, note: str) -> dict[str, Any]:
    return {
        "label": label,
        "symbol": symbol,
        "value": None,
        "change": None,
        "change_pct": None,
        "direction": "●",
        "display": "chưa có dữ liệu",
        "change_display": "chưa có dữ liệu",
        "volume": None,
        "note": note,
    }


def collect_market_data(symbols: dict[str, str], lookback_days: int) -> list[dict[str, Any]]:
    return [fetch_symbol(label, symbol, lookback_days) for label, symbol in symbols.items()]


def estimate_domestic_flows() -> list[dict[str, str]]:
    return [
        {
            "label": "Thanh khoản HOSE",
            "value": "chưa có dữ liệu",
            "note": "Cần nguồn HOSE/FiinTrade/SSI iBoard công khai ổn định.",
        },
        {
            "label": "Khối ngoại",
            "value": "chưa có dữ liệu",
            "note": "Không hard-code khi nguồn miễn phí chưa ổn định.",
        },
        {
            "label": "Tự doanh",
            "value": "chưa có dữ liệu",
            "note": "Không hard-code khi nguồn miễn phí chưa ổn định.",
        },
    ]


def vnindex_technical(market_data: list[dict[str, Any]]) -> dict[str, Any]:
    vnindex = next((item for item in market_data if item["label"] == "VN-Index"), None)
    if not vnindex or vnindex.get("value") is None:
        return {
            "available": False,
            "support": None,
            "resistance": None,
            "comment": "Chưa có dữ liệu kỹ thuật VN-Index.",
        }
    value = float(vnindex["value"])
    return {
        "available": True,
        "support": round(value * 0.985, 2),
        "resistance": round(value * 1.015, 2),
        "comment": "Vùng tham chiếu ước tính theo biên 1,5% quanh điểm đóng cửa gần nhất.",
    }
