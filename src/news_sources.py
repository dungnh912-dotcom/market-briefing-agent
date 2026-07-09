from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import feedparser

try:
    from .config import Settings
    from .utils import get_with_retry
except ImportError:
    from config import Settings
    from utils import get_with_retry


LOGGER = logging.getLogger(__name__)


def fetch_rss_feed(url: str, settings: Settings, limit: int = 8) -> list[dict[str, Any]]:
    response = get_with_retry(url, timeout=settings.request_timeout, retries=settings.request_retries)
    if response is None:
        return []
    parsed = feedparser.parse(response.content)
    items: list[dict[str, Any]] = []
    for entry in parsed.entries[:limit]:
        items.append(
            {
                "title": getattr(entry, "title", "").strip(),
                "link": getattr(entry, "link", "").strip(),
                "source": getattr(parsed.feed, "title", "RSS"),
                "published": getattr(entry, "published", ""),
                "summary": getattr(entry, "summary", ""),
            }
        )
    return [item for item in items if item["title"]]


def collect_news(settings: Settings) -> dict[str, Any]:
    all_items: list[dict[str, Any]] = []
    for feed_url in settings.rss_feeds:
        try:
            all_items.extend(fetch_rss_feed(feed_url, settings))
        except Exception as exc:
            LOGGER.warning("RSS feed failed %s: %s", feed_url, exc)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in all_items:
        key = item["title"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return {
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "items": deduped[:30],
        "notes": [] if deduped else ["Chưa thu thập được tin RSS; bản tin vẫn được tạo bằng dữ liệu sẵn có."],
    }
