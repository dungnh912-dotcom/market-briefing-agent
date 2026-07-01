from __future__ import annotations

import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from config import get_settings
from fetch_global import fetch_global_markets
from fetch_macro import fetch_macro
from fetch_news import fetch_news
from fetch_vietnam import VIETNAM_TECHNICAL_NOTE, fetch_vietnam_market
from llm import generate_with_llm
from prompt import build_prompt
from report_writer import build_fallback_report, write_json, write_report


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    settings = get_settings()
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    report_date = now_vn.date()
    date_slug = report_date.isoformat()

    logger.info("Building market briefing for %s", date_slug)
    market_data = {
        "generated_at": now_vn.isoformat(),
        "global": fetch_global_markets(settings.global_symbols, settings.lookback_days),
        "macro": fetch_macro(settings.lookback_days),
        "news": fetch_news(settings.newsapi_key),
        "vietnam": fetch_vietnam_market(settings.vietnam_watchlist, settings.lookback_days),
    }

    data_path = settings.data_dir / f"{date_slug}-market-data.json"
    write_json(data_path, market_data)
    logger.info("Wrote raw data to %s", data_path)

    prompt = build_prompt(market_data, report_date)
    report = generate_with_llm(prompt, settings) or build_fallback_report(market_data, report_date)
    report = _ensure_vietnam_data_note(report, market_data)

    report_path = settings.reports_dir / f"{date_slug}-market-briefing.md"
    write_report(report_path, report)
    logger.info("Wrote report to %s", report_path)


def _ensure_vietnam_data_note(report: str, market_data: dict) -> str:
    vietnam = market_data.get("vietnam", {})
    stocks = vietnam.get("stocks", {})
    has_missing_vietnam_data = vietnam.get("fallback") or any(
        not stock.get("available") for stock in stocks.values()
    )
    if not has_missing_vietnam_data or VIETNAM_TECHNICAL_NOTE in report:
        return report
    return f"{report.rstrip()}\n\n> {VIETNAM_TECHNICAL_NOTE}\n"


if __name__ == "__main__":
    main()
