from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MISSING = "chưa có dữ liệu cập nhật"

RSS_SOURCES: list[dict[str, Any]] = [
    {"name": "Vietstock", "url": "https://vietstock.vn/rss/chung-khoan-830.rss", "priority": 1},
    {"name": "CafeF", "url": "https://cafef.vn/thi-truong-chung-khoan.rss", "priority": 2},
    {"name": "VnEconomy", "url": "https://vneconomy.vn/chung-khoan.rss", "priority": 3},
    {"name": "VnExpress Kinh doanh", "url": "https://vnexpress.net/rss/kinh-doanh.rss", "priority": 4},
    {"name": "CNBC Markets", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "priority": 5},
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manual_news(path: Path = DATA_DIR / "manual_news.json") -> dict[str, Any]:
    if not path.exists():
        return {"items": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"items": []}


def clean_summary(text: str, limit: int = 420) -> str:
    cleaned = BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)
    return cleaned[:limit] if cleaned else MISSING


def fetch_rss(source: dict[str, Any], timeout: int = 12) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    headers = {"User-Agent": "HDUNGINVEST-market-briefing-agent/1.0"}
    fetched_at = now_utc()
    response = requests.get(source["url"], timeout=timeout, headers=headers)
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    items: list[dict[str, Any]] = []
    for entry in parsed.entries[:12]:
        title = getattr(entry, "title", "").strip()
        url = getattr(entry, "link", "").strip()
        if not title or not url:
            continue
        published = getattr(entry, "published", "") or getattr(entry, "updated", "")
        items.append(
            {
                "title": title,
                "url": url,
                "source": source["name"],
                "published": published,
                "summary": clean_summary(getattr(entry, "summary", "")),
                "tags": [],
                "fetched_at": fetched_at,
                "updated_at": published or fetched_at,
            }
        )
    meta = {
        "name": source["name"],
        "url": source["url"],
        "used_for": "Tin tức RSS/public feed.",
        "fetched_at": fetched_at,
        "updated_at": fetched_at,
    }
    return items, meta


def normalize_manual_item(item: dict[str, Any], default_updated_at: str) -> dict[str, Any] | None:
    title = (item.get("title") or "").strip()
    summary = (item.get("summary") or "").strip()
    if not title and not summary:
        return None
    if title.lower().startswith("bo sung") and not item.get("url"):
        return None
    updated_at = item.get("updated_at") or item.get("published") or default_updated_at
    return {
        "title": title or MISSING,
        "url": item.get("url") or "",
        "source": item.get("source") or "manual_news.json",
        "published": item.get("published") or "",
        "summary": summary or MISSING,
        "tags": item.get("tags") or [],
        "fetched_at": now_utc(),
        "updated_at": updated_at,
    }


def collect_news(limit: int = 40) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    fetched_at = now_utc()

    manual = load_manual_news()
    manual_updated_at = manual.get("updated_at") or fetched_at
    for item in manual.get("items", []):
        normalized = normalize_manual_item(item, manual_updated_at)
        if normalized:
            items.append(normalized)
    sources.append(
        {
            "name": "manual_news.json",
            "url": "data/manual_news.json",
            "used_for": "Tin bổ sung thủ công khi RSS/public pages thiếu dữ liệu.",
            "fetched_at": fetched_at,
            "updated_at": manual_updated_at,
        }
    )

    for source in sorted(RSS_SOURCES, key=lambda row: row["priority"]):
        try:
            new_items, meta = fetch_rss(source)
            items.extend(new_items)
            sources.append(meta)
        except Exception as exc:
            errors.append({"name": source["name"], "url": source["url"], "error": str(exc), "updated_at": fetched_at})

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("url") or item.get("title") or "").lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)

    return {
        "items": deduped[:limit],
        "sources": sources,
        "errors": errors,
        "fetched_at": fetched_at,
        "updated_at": fetched_at,
    }
