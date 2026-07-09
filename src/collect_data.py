from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from .config import Settings
    from .market_data import collect_market_data, estimate_domestic_flows, vnindex_technical
    from .news_sources import collect_news
except ImportError:
    from config import Settings
    from market_data import collect_market_data, estimate_domestic_flows, vnindex_technical
    from news_sources import collect_news


def collect_all(settings: Settings, report_date: datetime) -> dict[str, Any]:
    market = collect_market_data(settings.market_symbols, settings.lookback_days)
    return {
        "report_date": report_date.date().isoformat(),
        "market_data": market,
        "domestic_flows": estimate_domestic_flows(),
        "technical": vnindex_technical(market),
        "news": collect_news(settings),
        "metadata": {
            "timezone": settings.timezone,
            "lookback_days": settings.lookback_days,
            "generated_by": "market-briefing-agent",
        },
    }
