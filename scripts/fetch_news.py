from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup


def load_sources(path: str = "config/sources.yaml") -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def fetch_url(url: str, timeout: int, retries: int) -> requests.Response | None:
    headers = {"User-Agent": "market-briefing-agent/1.0 (+https://github.com/)"}
    last_error = None
    for _ in range(max(retries, 0) + 1):
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error))


def fetch_rss(source: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    response = fetch_url(source["url"], int(source.get("timeout", 12)), int(source.get("retries", 2)))
    parsed = feedparser.parse(response.content if response else b"")
    fetched_at = datetime.now(timezone.utc).isoformat()
    items = []
    for entry in parsed.entries[:10]:
        items.append(
            {
                "title": getattr(entry, "title", "").strip(),
                "url": getattr(entry, "link", "").strip(),
                "source": source["name"],
                "published": getattr(entry, "published", ""),
                "summary": BeautifulSoup(getattr(entry, "summary", ""), "html.parser").get_text(" ", strip=True)[:320],
                "fetched_at": fetched_at,
            }
        )
    meta = {"name": source["name"], "url": source["url"], "used_for": "Tin tuc RSS", "fetched_at": fetched_at}
    return [item for item in items if item["title"] and item["url"]], meta


def collect_news(path: str = "config/sources.yaml") -> dict[str, Any]:
    config = load_sources(path)
    defaults = config.get("defaults", {})
    sources = sorted(config.get("sources", []), key=lambda item: item.get("priority", 99))
    items: list[dict[str, Any]] = []
    used_sources: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for source in sources:
        if not source.get("enabled", True):
            continue
        merged = {**defaults, **source}
        try:
            if merged.get("type") == "rss":
                new_items, meta = fetch_rss(merged)
                items.extend(new_items)
                used_sources.append(meta)
            else:
                errors.append({"name": merged["name"], "url": merged.get("url", ""), "error": f"Adapter {merged.get('type')} chua duoc cai dat"})
        except Exception as exc:
            errors.append({"name": merged.get("name", "unknown"), "url": merged.get("url", ""), "error": str(exc)})

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = item["title"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return {
        "items": deduped[:40],
        "sources": used_sources,
        "errors": errors,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
