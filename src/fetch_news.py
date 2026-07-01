from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import feedparser
import requests

logger = logging.getLogger(__name__)


RSS_FEEDS = [
    "https://vnexpress.net/rss/kinh-doanh.rss",
    "https://cafef.vn/thi-truong-chung-khoan.rss",
    "https://www.investing.com/rss/news_25.rss",
]


def fetch_news(newsapi_key: str | None = None, limit: int = 20) -> dict[str, Any]:
    if newsapi_key:
        try:
            return {"source": "NewsAPI", "items": _fetch_newsapi(newsapi_key, limit)}
        except Exception as exc:
            logger.warning("NewsAPI failed, falling back to RSS: %s", exc)

    items = _fetch_rss(limit)
    return {
        "source": "RSS",
        "items": items,
        "note": "Không có NEWSAPI_KEY hoặc NewsAPI lỗi; đã dùng RSS miễn phí.",
    }


def _fetch_newsapi(api_key: str, limit: int) -> list[dict[str, str]]:
    from_date = (date.today() - timedelta(days=3)).isoformat()
    params = {
        "q": "(stock market OR Vietnam stock OR VN-Index OR Fed OR oil OR gold)",
        "language": "en",
        "sortBy": "publishedAt",
        "from": from_date,
        "pageSize": min(limit, 100),
        "apiKey": api_key,
    }
    response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    return [
        {
            "title": article.get("title") or "",
            "url": article.get("url") or "",
            "source": (article.get("source") or {}).get("name") or "NewsAPI",
            "published_at": article.get("publishedAt") or "",
            "summary": article.get("description") or "",
        }
        for article in data.get("articles", [])[:limit]
    ]


def _fetch_rss(limit: int) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:limit]:
                items.append(
                    {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "source": feed.feed.get("title", feed_url),
                        "published_at": entry.get("published", ""),
                        "summary": entry.get("summary", ""),
                    }
                )
        except Exception as exc:
            logger.warning("RSS feed failed %s: %s", feed_url, exc)
    return items[:limit]
