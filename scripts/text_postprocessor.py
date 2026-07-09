from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

TYPO_REPLACEMENTS: dict[str, str] = {
    "chua co du lieu cap nhat": "chưa có dữ liệu cập nhật",
    "sảy ra": "xảy ra",
    "cồ phiếu": "cổ phiếu",
    "thi trường": "thị trường",
    "ngnahf": "ngành",
    "chung trung": "chúng tôi",
    "ngan hang": "ngân hàng",
    "chung khoan": "chứng khoán",
    "thep": "thép",
    "rui ro thi truong": "rủi ro thị trường",
    "chi xem xet neu": "chỉ xem xét nếu",
    "vnindex": "VN-Index",
    "vn-index": "VN-Index",
    "vn30": "VN30",
    "hnx-index": "HNX-Index",
    "upcom": "UPCoM",
    "hose": "HOSE",
    "hnx": "HNX",
    "sbv": "SBV",
    "fed": "Fed",
    "cpi": "CPI",
    "pmi": "PMI",
    "usd/vnd": "USD/VND",
}

STANDARD_TERMS = {
    "VNINDEX": "VN-Index",
    "VN Index": "VN-Index",
    "HNXIndex": "HNX-Index",
    "Upcom": "UPCoM",
    "Usd/Vnd": "USD/VND",
}

FORBIDDEN_UNSUPPORTED = [
    "doanh nghiệp chắc chắn lừa đảo",
    "chủ tịch đang cắm hàng",
    "đội lái đang quay tay",
    "sắp úp bô",
]

SKIP_KEYS = {"url", "href", "qr_path", "logo_path", "name"}
FILE_EXTENSIONS = ("json", "html", "py", "yml", "yaml", "css", "png", "svg", "md", "txt")


def fix_text(text: str) -> str:
    value = text
    for wrong, right in TYPO_REPLACEMENTS.items():
        value = re.sub(re.escape(wrong), right, value, flags=re.IGNORECASE)
    for wrong, right in STANDARD_TERMS.items():
        value = value.replace(wrong, right)

    value = re.sub(r"\s+([,.;:%])", r"\1", value)
    value = re.sub(r"([,;:])([^\s\d])", r"\1 \2", value)
    value = re.sub(r"\.([^\s\d])", r". \1", value)
    for extension in FILE_EXTENSIONS:
        value = re.sub(rf"\.\s+{extension}\b", f".{extension}", value, flags=re.IGNORECASE)
    value = re.sub(r"\s{2,}", " ", value).strip()
    value = value.replace(" tỉ đồng", " tỷ đồng")
    value = value.replace(" tỷ VND", " tỷ đồng")
    value = value.replace(" USD / thùng", " USD/thùng")
    value = value.replace(" USD / oz", " USD/oz")
    value = value.replace(" điểm điểm", " điểm")

    lowered = value.lower()
    for phrase in FORBIDDEN_UNSUPPORTED:
        if phrase in lowered:
            value = re.sub(
                re.escape(phrase),
                "giả thuyết rủi ro cần kiểm chứng",
                value,
                flags=re.IGNORECASE,
            )
    return value


def postprocess(value: Any, key: str | None = None) -> Any:
    if isinstance(value, str):
        return value if key in SKIP_KEYS else fix_text(value)
    if isinstance(value, list):
        return [postprocess(item, key=key) for item in value]
    if isinstance(value, dict):
        return {item_key: postprocess(item_value, key=item_key) for item_key, item_value in value.items()}
    return value


def postprocess_briefing(data: dict[str, Any]) -> dict[str, Any]:
    return postprocess(deepcopy(data))
