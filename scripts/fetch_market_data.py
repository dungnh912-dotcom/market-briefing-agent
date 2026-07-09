from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf

try:
    from scripts.technical_analysis import analyze_price_history
except ImportError:
    from technical_analysis import analyze_price_history


GLOBAL_SYMBOLS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    "Nikkei 225": "^N225",
    "DXY": "DX-Y.NYB",
    "US 10Y": "^TNX",
    "Gold": "GC=F",
    "WTI Oil": "CL=F",
    "Brent Oil": "BZ=F",
    "Bitcoin": "BTC-USD",
}

VIETNAM_SYMBOLS = {
    "VN-Index": "^VNINDEX",
    "VN30": "VN30.VN",
    "HNX-Index": "HNX.VN",
    "UPCoM": "UPCOM.VN",
    "USD/VND": "VND=X",
}


def _tone(change_pct: float | None) -> str:
    if change_pct is None:
        return "neutral"
    if change_pct > 0.05:
        return "up"
    if change_pct < -0.05:
        return "down"
    return "neutral"


def unavailable(label: str, symbol: str, reason: str) -> dict[str, Any]:
    return {
        "label": label,
        "symbol": symbol,
        "value": "N/A",
        "change": "N/A",
        "change_pct": None,
        "tone": "neutral",
        "note": f"N/A - {reason}",
        "source": "Yahoo Finance",
    }


def fetch_yfinance_metric(label: str, symbol: str, period: str = "90d") -> dict[str, Any]:
    try:
        history = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=False)
        if history.empty or "Close" not in history:
            return unavailable(label, symbol, "Yahoo Finance khong tra du lieu")
        close = history["Close"].dropna()
        if close.empty:
            return unavailable(label, symbol, "thieu gia dong cua")

        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else last
        change = last - prev
        change_pct = (change / prev * 100) if prev else 0
        tech = analyze_price_history(history)
        return {
            "label": label,
            "symbol": symbol,
            "value": f"{last:,.2f}",
            "raw_value": last,
            "change": f"{change:+,.2f} ({change_pct:+.2f}%)",
            "change_pct": round(change_pct, 2),
            "tone": _tone(change_pct),
            "note": "Yahoo Finance, du lieu co the tre theo san",
            "source": "Yahoo Finance",
            "technical": tech,
        }
    except Exception as exc:
        return unavailable(label, symbol, str(exc))


def fetch_market_data() -> dict[str, Any]:
    global_markets = [fetch_yfinance_metric(label, symbol) for label, symbol in GLOBAL_SYMBOLS.items()]
    vietnam_markets = [fetch_yfinance_metric(label, symbol) for label, symbol in VIETNAM_SYMBOLS.items()]
    flow_placeholders = [
        {
            "label": "Lai suat lien ngan hang",
            "value": "N/A",
            "change": "N/A",
            "tone": "neutral",
            "note": "Chua co adapter nguon cong khai on dinh; khong hard-code so lieu.",
            "source": "N/A",
        },
        {
            "label": "Khoi ngoai mua/ban rong",
            "value": "N/A",
            "change": "N/A",
            "tone": "neutral",
            "note": "Nguon mien phi co the bi chan; adapter fallback de workflow khong fail.",
            "source": "N/A",
        },
        {
            "label": "Tu doanh",
            "value": "N/A",
            "change": "N/A",
            "tone": "neutral",
            "note": "Chua co nguon cong khai on dinh.",
            "source": "N/A",
        },
        {
            "label": "Do rong thi truong",
            "value": "N/A",
            "change": "N/A",
            "tone": "neutral",
            "note": "Can nguon breadth chinh thuc hoac vendor du lieu.",
            "source": "N/A",
        },
    ]
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "global_markets": global_markets,
        "vietnam_markets": vietnam_markets,
        "flows": flow_placeholders,
        "sources": [
            {
                "name": "Yahoo Finance",
                "url": "https://finance.yahoo.com/",
                "used_for": "Chi so quoc te, hang hoa, crypto va mot so ma/chung chi co the truy cap",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }


def fetch_watchlist_technicals(watchlist: dict[str, list[str]], limit: int = 12) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sector, tickers in watchlist.items():
        for ticker in tickers:
            metric = fetch_yfinance_metric(ticker, f"{ticker}.VN", period="9mo")
            tech = metric.get("technical", {})
            notable = False
            reasons: list[str] = []
            if metric.get("change_pct") is not None and abs(float(metric["change_pct"])) >= 2:
                notable = True
                reasons.append(f"bien dong {metric['change']}")
            if tech.get("available"):
                last = tech.get("last_close")
                support = tech.get("support")
                resistance = tech.get("resistance")
                if last and support and abs(last - support) / support <= 0.025:
                    notable = True
                    reasons.append("gan vung ho tro ky thuat")
                if last and resistance and abs(last - resistance) / resistance <= 0.025:
                    notable = True
                    reasons.append("gan vung khang cu ky thuat")
                if tech.get("volume_vs_avg20") and tech["volume_vs_avg20"] >= 1.5:
                    notable = True
                    reasons.append("thanh khoan cao hon trung binh 20 phien")
            if notable:
                rows.append(
                    {
                        "ticker": ticker,
                        "sector": sector,
                        "metric": metric,
                        "technical": tech,
                        "reasons": reasons or ["co tin hieu can theo doi"],
                    }
                )
            if len(rows) >= limit:
                return rows
    return rows
