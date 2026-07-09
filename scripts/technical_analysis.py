from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

MISSING = "cần cập nhật thêm dữ liệu giá"


def _last_number(series: pd.Series) -> float | None:
    clean = series.dropna()
    if clean.empty:
        return None
    return round(float(clean.iloc[-1]), 2)


def _fmt(value: Any, suffix: str = "") -> str:
    if value is None or value == "":
        return MISSING
    try:
        return f"{float(value):,.2f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal
    return macd_line, signal, histogram


def support_resistance(history: pd.DataFrame, window: int = 60) -> tuple[float | None, float | None]:
    if history is None or history.empty:
        return None, None
    recent = history.tail(window)
    low_col = "Low" if "Low" in recent.columns else "Close"
    high_col = "High" if "High" in recent.columns else "Close"
    support = recent[low_col].dropna().min()
    resistance = recent[high_col].dropna().max()
    return (
        round(float(support), 2) if pd.notna(support) else None,
        round(float(resistance), 2) if pd.notna(resistance) else None,
    )


def analyze_price_history(history: pd.DataFrame | None) -> dict[str, Any]:
    if history is None or history.empty or "Close" not in history.columns:
        return {"available": False, "message": MISSING}

    close = history["Close"].dropna()
    if len(close) < 20:
        return {"available": False, "message": MISSING}

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    rsi14 = calculate_rsi(close, 14)
    macd_line, macd_signal, macd_hist = calculate_macd(close)
    support, resistance = support_resistance(history, 60)
    last_close = _last_number(close)
    last_ma20 = _last_number(ma20)
    last_ma50 = _last_number(ma50)

    trend = "trung tính"
    if last_close is not None and last_ma20 is not None:
        if last_close > last_ma20:
            trend = "tích cực ngắn hạn"
        elif last_close < last_ma20:
            trend = "thận trọng ngắn hạn"

    volume_vs_avg20 = None
    if "Volume" in history.columns:
        volume = history["Volume"].dropna()
        if len(volume) >= 20:
            avg20 = volume.rolling(20).mean().iloc[-1]
            if avg20:
                volume_vs_avg20 = round(float(volume.iloc[-1] / avg20), 2)

    return {
        "available": True,
        "last_close": last_close,
        "support": support,
        "resistance": resistance,
        "ma20": last_ma20,
        "ma50": last_ma50,
        "rsi14": _last_number(rsi14),
        "macd": _last_number(macd_line),
        "macd_signal": _last_number(macd_signal),
        "macd_hist": _last_number(macd_hist),
        "volume_vs_avg20": volume_vs_avg20,
        "trend": trend,
        "breakout_scenario": f"Vượt { _fmt(resistance) } với thanh khoản cải thiện sẽ củng cố nhịp hồi." if resistance else MISSING,
        "breakdown_scenario": f"Thủng { _fmt(support) } làm tăng rủi ro hạ tỷ trọng trading." if support else MISSING,
    }


def build_manual_technical(row: dict[str, Any]) -> dict[str, Any]:
    support = row.get("support")
    resistance = row.get("resistance")
    ma20 = row.get("ma20")
    ma50 = row.get("ma50")
    available = any(value not in (None, "") for value in [support, resistance, ma20, ma50])
    return {
        "available": available,
        "last_close": row.get("last_close"),
        "support": support,
        "resistance": resistance,
        "ma20": ma20,
        "ma50": ma50,
        "rsi14": row.get("rsi14"),
        "macd": row.get("macd"),
        "macd_signal": row.get("macd_signal"),
        "macd_hist": row.get("macd_hist"),
        "trend": row.get("trend") or ("theo dõi nền giá thủ công" if available else MISSING),
        "breakout_scenario": row.get("breakout_scenario") or (f"Vượt {_fmt(resistance)} có thể cải thiện xu hướng." if resistance else MISSING),
        "breakdown_scenario": row.get("breakdown_scenario") or (f"Thủng {_fmt(support)} cần hạ rủi ro." if support else MISSING),
        "message": "" if available else MISSING,
    }


def technical_to_text(technical: dict[str, Any]) -> str:
    if not technical.get("available"):
        return technical.get("message") or MISSING
    parts = [
        f"Hỗ trợ {_fmt(technical.get('support'))}",
        f"kháng cự {_fmt(technical.get('resistance'))}",
        f"MA20 {_fmt(technical.get('ma20'))}",
        f"MA50 {_fmt(technical.get('ma50'))}",
    ]
    if technical.get("rsi14") is not None:
        parts.append(f"RSI14 {_fmt(technical.get('rsi14'))}")
    if technical.get("macd") is not None:
        parts.append(f"MACD {_fmt(technical.get('macd'))}")
    return "; ".join(parts)


def build_watchlist_rows(watchlist: list[dict[str, Any]], automated: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    automated = automated or {}
    rows: list[dict[str, Any]] = []
    for item in watchlist:
        ticker = item.get("ticker", "")
        auto = automated.get(ticker, {})
        technical = auto.get("technical") if auto.get("technical", {}).get("available") else build_manual_technical(item)
        entry = item.get("entry_zone")
        take_profit = item.get("take_profit_zone")
        stop_loss = item.get("stop_loss_zone")
        if technical.get("available"):
            entry = entry if entry and entry != MISSING else f"Có thể theo dõi quanh hỗ trợ {_fmt(technical.get('support'))}, chỉ xem xét nếu có tín hiệu giữ nền."
            take_profit = take_profit if take_profit and take_profit != MISSING else f"Vùng kháng cự gần {_fmt(technical.get('resistance'))}."
            stop_loss = stop_loss if stop_loss and stop_loss != MISSING else f"Dưới hỗ trợ {_fmt(technical.get('support'))} hoặc khi kịch bản bị phủ định."

        rows.append(
            {
                "ticker": ticker,
                "sector": item.get("sector", ""),
                "thesis": item.get("thesis") or item.get("condition") or "Có thể theo dõi khi dữ liệu giá và dòng tiền xác nhận.",
                "entry_zone": entry or MISSING,
                "take_profit_zone": take_profit or MISSING,
                "stop_loss_zone": stop_loss or MISSING,
                "activation": item.get("condition") or "Chỉ xem xét nếu thanh khoản và xu hướng xác nhận.",
                "risk": item.get("risk") or "Rủi ro thị trường chung và tin doanh nghiệp.",
                "technical": technical,
                "technical_view": technical_to_text(technical),
            }
        )
    return rows
