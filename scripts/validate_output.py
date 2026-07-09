from __future__ import annotations

import json
import re
from typing import Any

try:
    from scripts.text_postprocessor import postprocess_briefing
except ImportError:
    from text_postprocessor import postprocess_briefing

DISCLAIMER = (
    "Tài liệu thông tin tổng hợp, KHÔNG phải khuyến nghị giao dịch hay đầu tư. "
    "Nhà đầu tư cần tự chịu trách nhiệm với quyết định của mình."
)

FORBIDDEN_PATTERNS = [
    re.compile(r"chắc\s+chắn\s+mua", re.IGNORECASE),
    re.compile(r"mua\s+chắc\s+chắn", re.IGNORECASE),
    re.compile(r"cam\s+kết\s+lợi\s+nhuận", re.IGNORECASE),
    re.compile(r"đảm\s+bảo\s+lợi\s+nhuận", re.IGNORECASE),
    re.compile(r"doanh\s+nghiệp\s+chắc\s+chắn\s+lừa\s+đảo", re.IGNORECASE),
    re.compile(r"chủ\s+tịch\s+đang\s+cắm\s+hàng", re.IGNORECASE),
    re.compile(r"đội\s+lái\s+đang\s+quay\s+tay", re.IGNORECASE),
    re.compile(r"sắp\s+úp\s+bô", re.IGNORECASE),
]


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
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def normalize_section(section: dict[str, Any], index: int) -> dict[str, Any]:
    flow = section.get("flow_reality_check") or {}
    paragraphs = _list(section.get("paragraphs"))
    if section.get("factual_data"):
        paragraphs.append(section["factual_data"])
    return {
        "number": str(section.get("number") or f"{index:02d}").zfill(2),
        "title": section.get("title") or "Điểm cần theo dõi",
        "kicker": section.get("kicker") or "Dữ liệu thực tế / Kỳ vọng / Suy luận",
        "paragraphs": paragraphs,
        "bullets": _list(section.get("bullets")),
        "factual_data": section.get("factual_data") or "",
        "market_expectation": section.get("market_expectation") or "",
        "inference": section.get("inference") or "",
        "flow_reality_check": {
            "mask": flow.get("mask") or "chưa có dữ liệu cập nhật",
            "reality_to_verify": flow.get("reality_to_verify") or "Cần kiểm chứng dòng tiền thật, thanh khoản và hành vi khối ngoại/tự doanh.",
            "stock_impact": flow.get("stock_impact") or "Chỉ phù hợp khi thị trường xác nhận thanh khoản.",
        },
    }


def normalize_watchlist(row: dict[str, Any]) -> dict[str, Any]:
    activation = row.get("activation") or row.get("condition") or "Chỉ xem xét nếu thanh khoản và xu hướng xác nhận."
    if "chỉ phù hợp khi thị trường xác nhận thanh khoản" not in activation.lower():
        activation = f"{activation} Chỉ phù hợp khi thị trường xác nhận thanh khoản."
    return {
        "ticker": row.get("ticker") or row.get("code") or "",
        "sector": row.get("sector") or row.get("industry") or "",
        "thesis": row.get("thesis") or row.get("reason") or row.get("luan_diem") or "Có thể theo dõi khi dữ liệu giá và dòng tiền xác nhận.",
        "entry_zone": row.get("entry_zone") or row.get("buy_zone") or "cần cập nhật thêm dữ liệu giá",
        "take_profit_zone": row.get("take_profit_zone") or row.get("resistance") or "cần cập nhật thêm dữ liệu giá",
        "stop_loss_zone": row.get("stop_loss_zone") or row.get("stop_loss") or "cần cập nhật thêm dữ liệu giá",
        "activation": activation,
        "risk": row.get("risk") or "Rủi ro thị trường chung, margin và tin doanh nghiệp.",
        "technical": row.get("technical", {}),
    }


def normalize_technical(row: dict[str, Any]) -> dict[str, str]:
    return {
        "ticker": row.get("ticker") or row.get("code") or "VN-Index",
        "support": str(row.get("support") or "cần cập nhật thêm dữ liệu giá"),
        "resistance": str(row.get("resistance") or "cần cập nhật thêm dữ liệu giá"),
        "ma20": str(row.get("ma20") or "cần cập nhật thêm dữ liệu giá"),
        "ma50": str(row.get("ma50") or "cần cập nhật thêm dữ liệu giá"),
        "rsi": str(row.get("rsi") or row.get("rsi14") or "cần cập nhật thêm dữ liệu giá"),
        "macd": str(row.get("macd") or "cần cập nhật thêm dữ liệu giá"),
        "breakout": row.get("breakout") or row.get("breakout_scenario") or "cần cập nhật thêm dữ liệu giá",
        "breakdown": row.get("breakdown") or row.get("breakdown_scenario") or "cần cập nhật thêm dữ liệu giá",
    }


def normalize_event(row: dict[str, Any]) -> dict[str, str]:
    flow = row.get("flow_reality_check") or {}
    return {
        "timeframe": row.get("timeframe") or row.get("date") or "Theo dõi",
        "event": row.get("event") or row.get("title") or "chưa có dữ liệu cập nhật",
        "impact": row.get("impact") or row.get("why_it_matters") or "chưa có dữ liệu cập nhật",
        "affected_groups": row.get("affected_groups") or "chưa có dữ liệu cập nhật",
        "flow_mask": flow.get("mask") or "Cần kiểm chứng cách thị trường diễn giải sự kiện.",
        "flow_reality": flow.get("reality_to_verify") or "Quan sát dòng tiền thật, thanh khoản và hành vi khối ngoại/tự doanh.",
        "flow_impact": flow.get("stock_impact") or "Nếu chỉ là kéo giá tạo thanh khoản, rủi ro phân phối cần được đặt lên trước.",
    }


def normalize_scenario(row: dict[str, Any]) -> dict[str, str]:
    return {
        "name": row.get("name") or "Trung tính",
        "condition": row.get("condition") or "Thị trường chưa xác nhận xu hướng mới.",
        "strategy": row.get("strategy") or row.get("action") or "Không mua đuổi, ưu tiên cổ phiếu có nền và giữ kỷ luật cắt lỗ.",
    }


def normalize_source(row: dict[str, Any]) -> dict[str, str]:
    fetched_at = row.get("updated_at") or row.get("fetched_at") or ""
    return {
        "name": row.get("name") or "Nguồn dữ liệu",
        "url": row.get("url") or "#",
        "used_for": row.get("used_for") or "Tham khảo dữ liệu thị trường.",
        "fetched_at": fetched_at,
        "updated_at": fetched_at,
    }


def normalize_briefing(data: dict[str, Any]) -> dict[str, Any]:
    data = dict(data)
    data.setdefault("title", "Bản tin thị trường")
    data.setdefault("subtitle", "Daily Market Briefing for Vietnamese Brokers")
    summary = data.get("executive_summary", data.get("hero_summary", []))
    if isinstance(summary, str):
        summary = [line.strip() for line in summary.splitlines() if line.strip()]
    data["hero_summary"] = _list(summary)
    data["market_cards"] = _list(data.get("market_cards"))
    data["sections"] = [normalize_section(section, index) for index, section in enumerate(_list(data.get("sections")), start=1)]
    data["sector_rows"] = _list(data.get("sector_rows") or data.get("sector_impacts") or data.get("sector_table"))
    data["impact_rows"] = _list(data.get("impact_rows"))
    data["watchlist_rows"] = [normalize_watchlist(row) for row in _list(data.get("watchlist_rows") or data.get("watchlist") or data.get("stock_watchlist"))]
    data["technical_rows"] = [normalize_technical(row) for row in _list(data.get("technical_rows") or data.get("technical_analysis"))]
    data["events"] = [normalize_event(row) for row in _list(data.get("events") or data.get("event_calendar"))]
    data["scenarios"] = [normalize_scenario(row) for row in _list(data.get("scenarios") or data.get("strategy_view"))]
    data["sources"] = [normalize_source(row) for row in _list(data.get("sources"))]
    data["disclaimer"] = DISCLAIMER
    return postprocess_briefing(data)


def validate_briefing(data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_briefing(data)
    if not normalized.get("title"):
        raise ValidationError("title rỗng")
    if not normalized["sections"]:
        raise ValidationError("sections rỗng")
    if not normalized["sources"]:
        raise ValidationError("sources rỗng")

    serialized = json.dumps(normalized, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(serialized):
            raise ValidationError(f"Phát hiện cụm từ không phù hợp: {pattern.pattern}")
    if "KHÔNG phải khuyến nghị" not in normalized.get("disclaimer", ""):
        raise ValidationError("Thiếu disclaimer bắt buộc")
    return normalized


def parse_and_validate(text: str) -> dict[str, Any]:
    return validate_briefing(parse_json_text(text))
