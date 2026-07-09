from __future__ import annotations

import json
import re
from typing import Any

FORBIDDEN_PATTERNS = [
    re.compile(r"chắc\s+chắn\s+mua", re.IGNORECASE),
    re.compile(r"mua\s+chắc\s+chắn", re.IGNORECASE),
    re.compile(r"cam\s+kết\s+lợi\s+nhuận", re.IGNORECASE),
    re.compile(r"đảm\s+bảo\s+lợi\s+nhuận", re.IGNORECASE),
]

DISCLAIMER = "Tài liệu thông tin tổng hợp, KHÔNG phải khuyến nghị giao dịch hay đầu tư."


class ValidationError(ValueError):
    pass


def parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalize_briefing(data: dict[str, Any]) -> dict[str, Any]:
    data.setdefault("title", "Bản tin thị trường")
    data.setdefault("subtitle", "")
    data.setdefault("hero_summary", [])
    if isinstance(data["hero_summary"], str):
        data["hero_summary"] = [line.strip() for line in data["hero_summary"].splitlines() if line.strip()]
    data.setdefault("market_cards", [])
    data.setdefault("sections", [])
    data.setdefault("sector_rows", data.get("sector_table", []))
    data.setdefault("impact_rows", [])
    data.setdefault("watchlist_rows", data.get("stock_watchlist", []))
    data.setdefault("technical_rows", [])
    data.setdefault("events", [])
    data.setdefault("scenarios", [])
    data.setdefault("sources", [])
    data.setdefault("disclaimer", DISCLAIMER)
    data["hero_summary"] = _list(data["hero_summary"])
    data["market_cards"] = _list(data["market_cards"])
    data["sections"] = _list(data["sections"])
    data["sector_rows"] = _list(data["sector_rows"])
    data["impact_rows"] = _list(data["impact_rows"])
    data["watchlist_rows"] = _list(data["watchlist_rows"])
    data["technical_rows"] = _list(data["technical_rows"])
    data["events"] = _list(data["events"])
    data["scenarios"] = _list(data["scenarios"])
    data["sources"] = _list(data["sources"])
    return data


def validate_briefing(data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_briefing(data)
    if not normalized.get("title"):
        raise ValidationError("title rỗng")
    if not normalized["sections"]:
        raise ValidationError("sections rỗng")
    if not normalized["sources"]:
        raise ValidationError("sources rỗng")
    for source in normalized["sources"]:
        if not source.get("url"):
            source["url"] = "#"

    serialized = json.dumps(normalized, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(serialized):
            raise ValidationError(f"Phát hiện cụm từ không phù hợp: {pattern.pattern}")
    if "KHÔNG phải khuyến nghị" not in normalized.get("disclaimer", ""):
        raise ValidationError("Thiếu disclaimer bắt buộc")
    return normalized


def parse_and_validate(text: str) -> dict[str, Any]:
    return validate_briefing(parse_json_text(text))
