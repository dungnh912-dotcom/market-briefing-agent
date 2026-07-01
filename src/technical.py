from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50)
    return rsi.fillna(50)


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    normalized = df.copy()
    if isinstance(normalized.columns, pd.MultiIndex):
        normalized.columns = [col[0] for col in normalized.columns]
    rename_map = {c: c.title() for c in normalized.columns}
    normalized = normalized.rename(columns=rename_map)
    return normalized


def technical_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    df = normalize_ohlcv(df)
    required = {"Close", "Volume"}
    if df.empty or not required.issubset(df.columns):
        return {
            "available": False,
            "reason": "Thiếu dữ liệu giá hoặc khối lượng.",
        }

    work = df.dropna(subset=["Close"]).copy()
    if work.empty:
        return {"available": False, "reason": "Không có giá đóng cửa hợp lệ."}

    close = work["Close"].astype(float)
    volume = work["Volume"].fillna(0).astype(float)
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    rsi = calculate_rsi(close, 14)
    support20 = close.rolling(20).min()
    resistance20 = close.rolling(20).max()
    avg_volume20 = volume.rolling(20).mean()

    latest_close = float(close.iloc[-1])
    latest_ma20 = _last_number(ma20)
    latest_ma50 = _last_number(ma50)
    latest_rsi = float(rsi.iloc[-1])
    latest_support = _last_number(support20)
    latest_resistance = _last_number(resistance20)
    latest_avg_volume = _last_number(avg_volume20)
    latest_volume = float(volume.iloc[-1])

    trend = classify_trend(latest_close, latest_ma20, latest_ma50)
    trade_status = classify_trade_status(latest_close, latest_ma20, latest_rsi, latest_volume, latest_avg_volume)

    return {
        "available": True,
        "last_price": round(latest_close, 2),
        "ma20": _round_or_none(latest_ma20),
        "ma50": _round_or_none(latest_ma50),
        "rsi14": round(latest_rsi, 2),
        "avg_volume20": _round_or_none(latest_avg_volume),
        "volume": round(latest_volume, 2),
        "support20": _round_or_none(latest_support),
        "resistance20": _round_or_none(latest_resistance),
        "trend": trend,
        "trade_status": trade_status,
    }


def classify_trend(price: float, ma20: float | None, ma50: float | None) -> str:
    if ma20 is None or ma50 is None:
        return "Chưa đủ dữ liệu"
    if price > ma20 > ma50:
        return "Tăng"
    if price < ma20 < ma50:
        return "Giảm"
    if price > ma20 and ma20 < ma50:
        return "Hồi phục"
    if price < ma20 and ma20 > ma50:
        return "Điều chỉnh"
    return "Đi ngang"


def classify_trade_status(
    price: float,
    ma20: float | None,
    rsi: float,
    volume: float,
    avg_volume20: float | None,
) -> str:
    if ma20 is None:
        return "Quan sát"
    strong_liquidity = avg_volume20 is not None and volume >= avg_volume20
    if price > ma20 and 45 <= rsi <= 70 and strong_liquidity:
        return "Có thể mua thăm dò nếu vượt vùng xác nhận"
    if rsi > 75:
        return "Không mua đuổi nếu RSI quá nóng"
    if price < ma20:
        return "Chỉ mua khi lấy lại MA20"
    return "Quan sát thêm"


def _last_number(series: pd.Series) -> float | None:
    valid = series.dropna()
    if valid.empty:
        return None
    return float(valid.iloc[-1])


def _round_or_none(value: float | None) -> float | None:
    return None if value is None else round(value, 2)
