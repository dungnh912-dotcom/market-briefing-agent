import pandas as pd

from src.technical import calculate_rsi, classify_trend, technical_snapshot


def test_calculate_rsi_returns_bounded_values():
    close = pd.Series([10, 11, 12, 11, 13, 14, 13, 15, 16, 15, 17, 18, 19, 18, 20, 21])
    rsi = calculate_rsi(close)
    assert rsi.iloc[-1] >= 0
    assert rsi.iloc[-1] <= 100


def test_technical_snapshot_contains_required_fields():
    df = pd.DataFrame(
        {
            "Close": list(range(100, 160)),
            "Volume": [1000 + i for i in range(60)],
        }
    )
    snapshot = technical_snapshot(df)
    assert snapshot["available"] is True
    assert snapshot["ma20"] is not None
    assert snapshot["ma50"] is not None
    assert snapshot["support20"] == 140
    assert snapshot["resistance20"] == 159
    assert "trade_status" in snapshot


def test_classify_trend_uptrend():
    assert classify_trend(120, 110, 100) == "Tăng"
