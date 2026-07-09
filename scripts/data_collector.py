from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yfinance as yf

try:
    from scripts.technical_analysis import analyze_price_history
except ImportError:
    from technical_analysis import analyze_price_history

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MISSING = "chưa có dữ liệu cập nhật"

GLOBAL_SYMBOLS: list[tuple[str, str, str]] = [
    ("S&P 500", "^GSPC", "Chứng khoán Mỹ"),
    ("Dow Jones", "^DJI", "Chứng khoán Mỹ"),
    ("Nasdaq", "^IXIC", "Chứng khoán Mỹ"),
    ("Nikkei 225", "^N225", "Chứng khoán châu Á"),
    ("Vàng thế giới", "GC=F", "Hàng hóa"),
    ("Bạc", "SI=F", "Hàng hóa"),
    ("Dầu WTI", "CL=F", "Năng lượng"),
    ("Dầu Brent", "BZ=F", "Năng lượng"),
    ("Bitcoin", "BTC-USD", "Crypto"),
    ("USD Index", "DX-Y.NYB", "Tiền tệ"),
    ("US 10Y", "^TNX", "Trái phiếu Mỹ"),
]

VIETNAM_KEYS = ["VNINDEX", "VN30", "HNX", "UPCOM", "USDVND"]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def tone(change_pct: float | None) -> str:
    if change_pct is None:
        return "neutral"
    if change_pct > 0.05:
        return "up"
    if change_pct < -0.05:
        return "down"
    return "neutral"


def format_number(value: Any, digits: int = 2) -> str:
    if value is None or value == "":
        return MISSING
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def format_change(change: Any, change_pct: Any) -> str:
    if change is None and change_pct is None:
        return MISSING
    pieces = []
    if change is not None:
        try:
            pieces.append(f"{float(change):+,.2f}")
        except (TypeError, ValueError):
            pieces.append(str(change))
    if change_pct is not None:
        try:
            pieces.append(f"({float(change_pct):+.2f}%)")
        except (TypeError, ValueError):
            pieces.append(f"({change_pct})")
    return " ".join(pieces) if pieces else MISSING


def unavailable_metric(label: str, symbol: str, reason: str, source: str = "Yahoo Finance") -> dict[str, Any]:
    return {
        "label": label,
        "symbol": symbol,
        "value": MISSING,
        "raw_value": None,
        "change": MISSING,
        "change_pct": None,
        "tone": "neutral",
        "note": reason or MISSING,
        "source": source,
        "technical": {"available": False, "message": MISSING},
    }


def fetch_yfinance_metric(label: str, symbol: str, period: str = "6mo") -> dict[str, Any]:
    try:
        history = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=False)
        if history.empty or "Close" not in history.columns:
            return unavailable_metric(label, symbol, "Yahoo Finance không trả dữ liệu")
        close = history["Close"].dropna()
        if close.empty:
            return unavailable_metric(label, symbol, "thiếu giá đóng cửa")

        last = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) > 1 else last
        change = last - previous
        change_pct = (change / previous * 100) if previous else None
        return {
            "label": label,
            "symbol": symbol,
            "value": format_number(last),
            "raw_value": round(last, 4),
            "change": format_change(change, change_pct),
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "tone": tone(change_pct),
            "note": "Nguồn Yahoo Finance, dữ liệu có thể trễ theo từng thị trường.",
            "source": "Yahoo Finance",
            "technical": analyze_price_history(history),
        }
    except Exception as exc:
        return unavailable_metric(label, symbol, str(exc))


def metric_from_manual(key: str, data: dict[str, Any]) -> dict[str, Any]:
    indexes = data.get("indexes", {})
    raw = indexes.get(key, {})
    label = raw.get("label") or key
    value = raw.get("value")
    change_pct = raw.get("change_pct")
    return {
        "label": label,
        "symbol": key,
        "value": format_number(value, 0 if key == "USDVND" else 2),
        "raw_value": value,
        "change": format_change(raw.get("change"), change_pct),
        "change_pct": change_pct,
        "tone": tone(float(change_pct)) if isinstance(change_pct, (int, float)) else "neutral",
        "note": raw.get("comment") or MISSING,
        "source": raw.get("source") or "manual_market_data.json",
        "technical": {"available": False, "message": MISSING},
    }


def collect_global_markets() -> list[dict[str, Any]]:
    return [fetch_yfinance_metric(label, symbol) | {"group": group} for label, symbol, group in GLOBAL_SYMBOLS]


def collect_vietnam_markets(manual: dict[str, Any]) -> list[dict[str, Any]]:
    return [metric_from_manual(key, manual) for key in VIETNAM_KEYS]


def collect_watchlist_market_data(watchlist: list[dict[str, Any]], limit: int = 10) -> dict[str, dict[str, Any]]:
    automated: dict[str, dict[str, Any]] = {}
    for item in watchlist[:limit]:
        ticker = item.get("ticker")
        if not ticker:
            continue
        metric = fetch_yfinance_metric(ticker, f"{ticker}.VN", period="9mo")
        automated[ticker] = metric
    return automated


def collect_market_data() -> dict[str, Any]:
    manual = load_json(DATA_DIR / "manual_market_data.json", {})
    watchlist = load_json(DATA_DIR / "watchlist.json", {}).get("tickers", [])
    fetched_at = now_utc()

    global_markets = collect_global_markets()
    vietnam_markets = collect_vietnam_markets(manual)
    automated_watchlist = collect_watchlist_market_data(watchlist)

    return {
        "fetched_at": fetched_at,
        "vietnam_markets": vietnam_markets,
        "global_markets": global_markets,
        "market_breadth": manual.get("market_breadth", {"comment": MISSING}),
        "liquidity": manual.get("liquidity", {"comment": MISSING}),
        "foreign_flow": manual.get("foreign_flow", {"comment": MISSING}),
        "proprietary_flow": manual.get("proprietary_flow", {"comment": MISSING}),
        "sector_flow": manual.get("sector_flow", []),
        "top_gainers": manual.get("top_gainers", []),
        "top_losers": manual.get("top_losers", []),
        "watchlist_prices": manual.get("watchlist_prices", {}),
        "automated_watchlist": automated_watchlist,
        "manual_updated_at": manual.get("updated_at") or MISSING,
        "sources": [
            {
                "name": "Yahoo Finance",
                "url": "https://finance.yahoo.com/",
                "used_for": "Chỉ số quốc tế, hàng hóa, crypto và dữ liệu kỹ thuật nếu truy cập được.",
                "fetched_at": fetched_at,
            },
            {
                "name": "manual_market_data.json",
                "url": "data/manual_market_data.json",
                "used_for": "Dữ liệu Việt Nam, dòng tiền, độ rộng, thanh khoản và phần thiếu từ nguồn tự động.",
                "fetched_at": fetched_at,
            },
        ],
    }
