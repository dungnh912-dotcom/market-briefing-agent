import pandas as pd

from scripts.data_collector import MISSING, metric_from_manual, parse_google_finance_text
from scripts.technical_analysis import analyze_price_history, build_watchlist_rows


def test_metric_from_manual_marks_missing_data():
    metric = metric_from_manual("VNINDEX", {"indexes": {"VNINDEX": {"label": "VN-Index", "value": None}}})
    assert metric["label"] == "VN-Index"
    assert metric["value"] == MISSING
    assert metric["tone"] == "neutral"


def test_parse_google_finance_text_extracts_quote():
    text = (
        "Research .INX:INDEXSP check_indeterminate_small S&P 500 "
        "7,482.71 arrow_downward -0.28% ( -21.14 ) 1D Jul 8, 4:48:41 PM GMT-4 area_chart"
    )
    metric = parse_google_finance_text("S&P 500", ".INX:INDEXSP", text, "2026-07-09T00:00:00Z")
    assert metric["value"] == "7,482.71"
    assert metric["change"] == "-21.14 (-0.28%)"
    assert metric["tone"] == "down"


def test_technical_analysis_calculates_levels():
    history = pd.DataFrame(
        {
            "Close": list(range(100, 170)),
            "Low": list(range(98, 168)),
            "High": list(range(102, 172)),
            "Volume": [1000 + i for i in range(70)],
        }
    )
    technical = analyze_price_history(history)
    assert technical["available"] is True
    assert technical["ma20"] is not None
    assert technical["ma50"] is not None
    assert technical["support"] == 108
    assert technical["resistance"] == 171


def test_watchlist_uses_manual_fallback_when_auto_missing():
    rows = build_watchlist_rows(
        [
            {
                "ticker": "MBB",
                "sector": "Ngan hang",
                "support": 20,
                "resistance": 24,
                "condition": "Chi xem xet neu giu nen.",
                "risk": "Rui ro thi truong.",
            }
        ]
    )
    assert rows[0]["ticker"] == "MBB"
    assert "20.00" in rows[0]["entry_zone"]
