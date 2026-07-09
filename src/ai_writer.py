from __future__ import annotations

import json
import logging
from typing import Any

try:
    from .config import Settings
except ImportError:  # Allows `python src/main.py` without installing the package.
    from config import Settings


LOGGER = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Bạn là AI Market Briefing Agent cho broker chứng khoán Việt Nam. Nhiệm vụ của bạn là tạo bản tin trước giờ giao dịch, kết nối tin quốc tế, dữ liệu vĩ mô, dòng tiền và cổ phiếu với tác động đến VN-Index và các nhóm ngành. Viết cô đọng, có số liệu, có nhận định nhưng không đưa khuyến nghị đầu tư chắc chắn.
"""

OUTPUT_CONTRACT = """
Trả về JSON hợp lệ với các khóa:
headline: tiêu đề ngắn.
summary: danh sách 4-6 câu tóm tắt mở đầu.
sections: danh sách 8 object có title và bullets. Tiêu đề đúng lần lượt:
§01. Qua đêm — toàn cầu
§02. Địa chính trị & rủi ro toàn cầu
§03. Dòng tiền & vị thế
§04. Trong nước — tín hiệu thị trường
§05. Vĩ mô & tiền tệ
§06. Doanh nghiệp & cổ phiếu đáng chú ý
§07. Lịch sự kiện
§08. Góc nhìn & chiến lược
sector_view: object theo nhóm ngân hàng, chứng khoán, bất động sản, thép, dầu khí, bán lẻ, xuất khẩu, khu công nghiệp, công nghệ.
scenarios: object gồm tích cực, trung tính, tiêu cực.
checklist: danh sách việc theo dõi trong phiên.
disclaimer: luôn là "Không phải khuyến nghị đầu tư".

Yêu cầu phong cách:
- Viết bằng tiếng Việt, góc nhìn broker chứng khoán tại Việt Nam.
- Không chỉ liệt kê tin; giải thích ảnh hưởng đến thị trường Việt Nam.
- Mỗi tin quốc tế quan trọng cần có dòng bắt đầu bằng "→ VN:".
- Không khuyến nghị mua/bán chắc chắn.
"""

SECTION_TITLES = [
    "§01. Qua đêm — toàn cầu",
    "§02. Địa chính trị & rủi ro toàn cầu",
    "§03. Dòng tiền & vị thế",
    "§04. Trong nước — tín hiệu thị trường",
    "§05. Vĩ mô & tiền tệ",
    "§06. Doanh nghiệp & cổ phiếu đáng chú ý",
    "§07. Lịch sự kiện",
    "§08. Góc nhìn & chiến lược",
]


def build_user_prompt(data: dict[str, Any]) -> str:
    compact = json.dumps(data, ensure_ascii=False, default=str)[:18000]
    return f"{OUTPUT_CONTRACT}\n\nDữ liệu thô:\n{compact}"


def write_briefing(data: dict[str, Any], settings: Settings) -> dict[str, Any]:
    prompt = build_user_prompt(data)
    if settings.gemini_api_key:
        try:
            return _write_with_gemini(prompt, settings)
        except Exception as exc:
            LOGGER.warning("Gemini writer failed, falling back: %s", exc)
    if settings.openai_api_key:
        try:
            return _write_with_openai(prompt, settings)
        except Exception as exc:
            LOGGER.warning("OpenAI writer failed, falling back: %s", exc)
    return raw_summary(data)


def _write_with_gemini(prompt: str, settings: Settings) -> dict[str, Any]:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model, system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(prompt)
    return _parse_json_response(response.text)


def _write_with_openai(prompt: str, settings: Settings) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    return _parse_json_response(response.choices[0].message.content or "{}")


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    return normalize_briefing(json.loads(cleaned))


def normalize_briefing(briefing: dict[str, Any]) -> dict[str, Any]:
    fallback = raw_summary({})
    merged = {**fallback, **briefing}
    merged["sections"] = normalize_sections(merged.get("sections", []))
    merged["disclaimer"] = "Không phải khuyến nghị đầu tư"
    return merged


def normalize_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_title = {item.get("title"): item for item in sections if isinstance(item, dict)}
    normalized = []
    for title in SECTION_TITLES:
        item = by_title.get(title, {})
        bullets = item.get("bullets") or ["Chưa có dữ liệu đủ chắc để kết luận; tiếp tục theo dõi trong phiên."]
        normalized.append({"title": title, "bullets": bullets})
    return normalized


def raw_summary(data: dict[str, Any]) -> dict[str, Any]:
    market = data.get("market_data", []) if data else []
    news = data.get("news", {}).get("items", []) if data else []
    vnindex = next((item for item in market if item.get("label") == "VN-Index"), {})
    headline = "Bản tin thị trường: dữ liệu đang được cập nhật"
    if vnindex.get("value") is not None:
        headline = f"VN-Index {vnindex.get('direction', '●')} {vnindex.get('change_display', '')}"

    summary = [
        "Bản tin được tạo ở chế độ raw summary vì chưa có khóa AI hợp lệ hoặc API AI chưa phản hồi.",
        "Các số liệu lấy từ nguồn miễn phí có thể thiếu hoặc trễ; mục thiếu dữ liệu được ghi rõ thay vì hard-code.",
        "Nhà đầu tư nên ưu tiên quan sát phản ứng của VN-Index tại các vùng hỗ trợ/kháng cự gần nhất.",
        "Tin quốc tế được diễn giải theo hướng tác động có thể có đến tâm lý và dòng tiền tại Việt Nam.",
    ]
    sections = normalize_sections(
        [
            {"title": "§01. Qua đêm — toàn cầu", "bullets": _global_bullets(market, news)},
            {"title": "§02. Địa chính trị & rủi ro toàn cầu", "bullets": ["→ VN: Rủi ro bên ngoài nếu tăng có thể làm dòng tiền ngắn hạn thận trọng hơn tại nhóm beta cao."]},
            {"title": "§03. Dòng tiền & vị thế", "bullets": ["Thanh khoản HOSE, khối ngoại và tự doanh: chưa có dữ liệu từ nguồn miễn phí ổn định."]},
            {"title": "§04. Trong nước — tín hiệu thị trường", "bullets": [f"VN-Index: {vnindex.get('display', 'chưa có dữ liệu')} {vnindex.get('change_display', '')}".strip()]},
            {"title": "§05. Vĩ mô & tiền tệ", "bullets": ["Theo dõi DXY, UST 10Y, giá dầu và tỷ giá vì đây là nhóm biến số ảnh hưởng khẩu vị rủi ro."]},
            {"title": "§06. Doanh nghiệp & cổ phiếu đáng chú ý", "bullets": [item.get("title", "") for item in news[:5]] or ["Chưa có tin doanh nghiệp nổi bật."]},
            {"title": "§07. Lịch sự kiện", "bullets": ["Theo dõi lịch công bố KQKD, họp ĐHĐCĐ, dữ liệu CPI/tỷ giá/lãi suất và tin từ Fed."]},
            {"title": "§08. Góc nhìn & chiến lược", "bullets": ["Ưu tiên quản trị tỷ trọng, tránh mua đuổi khi chỉ số tăng nhanh nhưng thanh khoản không xác nhận."]},
        ]
    )
    return {
        "headline": headline,
        "summary": summary,
        "sections": sections,
        "sector_view": {
            "ngân hàng": "Theo dõi vai trò dẫn dắt chỉ số và tín hiệu nợ xấu/lãi suất.",
            "chứng khoán": "Nhạy với thanh khoản và kỳ vọng nâng hạng.",
            "bất động sản": "Phụ thuộc lãi suất, pháp lý và trái phiếu.",
            "thép": "Theo dõi giá nguyên liệu, đầu tư công và nhu cầu xây dựng.",
            "dầu khí": "Nhạy với Brent và tiến độ dự án thượng nguồn.",
            "bán lẻ": "Phụ thuộc sức mua và biên lợi nhuận.",
            "xuất khẩu": "Theo dõi USD, đơn hàng Mỹ/EU và chi phí logistics.",
            "khu công nghiệp": "Hưởng lợi FDI nhưng cần theo dõi định giá.",
            "công nghệ": "Ít tỷ trọng chỉ số nhưng có câu chuyện tăng trưởng riêng.",
        },
        "scenarios": {
            "tích cực": "VN-Index giữ trên hỗ trợ, thanh khoản cải thiện và khối ngoại giảm bán.",
            "trung tính": "Chỉ số đi ngang, phân hóa theo kết quả kinh doanh và tin riêng.",
            "tiêu cực": "Gãy hỗ trợ gần, áp lực bán lan rộng ở nhóm vốn hóa lớn.",
        },
        "checklist": [
            "Thanh khoản 30 phút đầu so với trung bình 20 phiên.",
            "Độ rộng thị trường và vai trò của VN30.",
            "Giao dịch khối ngoại ở ngân hàng, chứng khoán, bất động sản.",
            "Biến động DXY, UST 10Y, dầu Brent và thị trường khu vực.",
        ],
        "disclaimer": "Không phải khuyến nghị đầu tư",
    }


def _global_bullets(market: list[dict[str, Any]], news: list[dict[str, Any]]) -> list[str]:
    bullets = []
    labels = {"S&P 500", "Nasdaq", "Dow Jones", "Nikkei 225", "Dầu Brent", "DXY", "UST 10Y", "Vàng", "Bitcoin"}
    for item in market:
        if item.get("label") in labels:
            bullets.append(
                f"{item['label']}: {item.get('display')} {item.get('change_display', '')}. → VN: biến động này ảnh hưởng tâm lý mở cửa và nhóm ngành liên quan."
            )
    bullets.extend([f"{item.get('title')}. → VN: cần đánh giá tác động đến dòng tiền và khẩu vị rủi ro." for item in news[:3]])
    return bullets[:8] or ["Chưa có dữ liệu quốc tế đáng tin cậy trong lần chạy này."]
