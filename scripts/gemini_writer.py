from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover
    genai = None
    types = None

try:
    from scripts.technical_analysis import build_watchlist_rows, technical_to_text
    from scripts.validate_output import DISCLAIMER, parse_and_validate, validate_briefing
except ImportError:
    from technical_analysis import build_watchlist_rows, technical_to_text
    from validate_output import DISCLAIMER, parse_and_validate, validate_briefing

MISSING = "chưa có dữ liệu cập nhật"

REQUIRED_SECTION_TITLES = [
    "Tóm tắt nhanh",
    "Dashboard chỉ số",
    "TTCK Việt Nam",
    "Vĩ mô trong nước",
    "Dòng tiền & vị thế",
    "Nhóm ngành",
    "Mã & nhóm ngành tác động",
    "Watchlist giao dịch có điều kiện",
    "Phân tích kỹ thuật",
    "Vĩ mô & thời sự quốc tế",
    "Lịch sự kiện",
    "Góc nhìn & chiến lược",
    "CTA liên hệ",
    "Nguồn tham khảo",
]

SYSTEM_PROMPT = f"""Bạn là AI Market Research Engineer viết bản tin cho broker chứng khoán Việt Nam.
Viết bằng tiếng Việt, ngắn gọn, rõ ý, văn phong chuyên nghiệp.
Luôn phân biệt dữ liệu thực tế, kỳ vọng thị trường và suy luận.
Không bịa số liệu, không tạo nguồn giả, không dùng ngôn ngữ cam kết lợi nhuận.
Nếu thiếu dữ liệu, ghi đúng: "{MISSING}".
Không đưa khuyến nghị mua/bán chắc chắn; chỉ dùng ngôn ngữ có điều kiện như "có thể theo dõi", "chỉ xem xét nếu", "phù hợp trading tỷ trọng nhỏ nếu".
Disclaimer bắt buộc: {DISCLAIMER}
"""


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    market = payload.get("market_data", {})
    news = payload.get("news", {})
    return {
        "date": payload.get("date"),
        "updated_label": payload.get("updated_label"),
        "brand": payload.get("brand"),
        "market_data": {
            "vietnam_markets": market.get("vietnam_markets", []),
            "global_markets": market.get("global_markets", []),
            "market_breadth": market.get("market_breadth", {}),
            "liquidity": market.get("liquidity", {}),
            "foreign_flow": market.get("foreign_flow", {}),
            "proprietary_flow": market.get("proprietary_flow", {}),
            "sector_flow": market.get("sector_flow", []),
            "top_gainers": market.get("top_gainers", []),
            "top_losers": market.get("top_losers", []),
        },
        "news": {"items": news.get("items", [])[:25], "errors": news.get("errors", [])},
        "watchlist_rows": payload.get("watchlist_rows", [])[:20],
        "sources": payload.get("sources", []),
    }


def build_prompt(payload: dict[str, Any]) -> str:
    data_json = json.dumps(compact_payload(payload), ensure_ascii=False, default=str)
    sections = "\n".join(f"- {title}" for title in REQUIRED_SECTION_TITLES)
    return f"""Hãy sinh một bản tin HTML-ready cho HDUNGINVEST Daily Research.

Các phần bắt buộc:
{sections}

Yêu cầu nội dung:
- Hero có format: HDUNGINVEST · DAILY RESEARCH · ngày tháng.
- Tiêu đề lớn nên nêu VN-Index, dầu WTI, Nasdaq hoặc tài sản nổi bật nếu có dữ liệu.
- Tóm tắt 5-7 dòng như broker chứng khoán tại Việt Nam.
- Dashboard gồm VN-Index, VN30, HNX-Index, UPCoM, USD/VND, S&P 500, Dow Jones, Nasdaq, Nikkei 225, vàng, bạc, dầu WTI, dầu Brent, Bitcoin nếu đáng chú ý.
- TTCK Việt Nam phải nói về VN-Index/VN30/HNX, độ rộng, thanh khoản, khối ngoại, tự doanh, cổ phiếu tác động; ghi rõ đâu là dữ liệu thực tế/kỳ vọng/suy luận.
- Nhóm ngành gồm ngân hàng, chứng khoán, bất động sản, thép, dầu khí, bán lẻ, xuất khẩu, công nghệ, vàng/bạc nếu có liên quan.
- Watchlist chỉ là giao dịch có điều kiện; không dùng câu khẳng định phải mua/bán.
- Phân tích kỹ thuật gồm hỗ trợ, kháng cự, MA20, MA50, RSI/MACD nếu có; nếu thiếu thì ghi "{MISSING}".
- Góc nhìn có 3 kịch bản: tích cực, trung tính, tiêu cực; hành động cho broker: không mua đuổi, ưu tiên cổ phiếu có nền, giữ kỷ luật cắt lỗ, tách trading T+ và nắm giữ.

Trả về JSON hợp lệ theo schema:
{{
  "title": "...",
  "subtitle": "...",
  "date_label": "DD/MM/YYYY",
  "updated_label": "Cập nhật: HH:mm · DD/MM/YYYY · Giờ Việt Nam",
  "hero_summary": ["5-7 dòng"],
  "market_cards": [{{"label":"VN-Index","value":"...","change":"...","tone":"up|down|neutral","note":"..."}}],
  "sections": [{{"number":"01","title":"TTCK Việt Nam","kicker":"Dữ liệu thực tế / Kỳ vọng / Suy luận","paragraphs":["..."],"bullets":["..."]}}],
  "sector_rows": [{{"sector":"Ngân hàng","impact":"Hưởng lợi|Bất lợi|Trung tính","reason":"...","tickers":"MBB, HDB","risk":"..."}}],
  "impact_rows": [{{"target":"Dầu khí","impact":"Hưởng lợi","reason":"Dầu WTI tăng hỗ trợ GAS, PVD, PVS, BSR"}}],
  "watchlist_rows": [{{"ticker":"MBB","sector":"Ngân hàng","thesis":"...","entry_zone":"...","take_profit_zone":"...","stop_loss_zone":"...","activation":"...","risk":"..."}}],
  "technical_rows": [{{"ticker":"VN-Index","support":"...","resistance":"...","ma20":"...","ma50":"...","rsi":"...","macd":"...","breakout":"...","breakdown":"..."}}],
  "events": [{{"timeframe":"Hôm nay","event":"...","impact":"...","affected_groups":"..."}}],
  "scenarios": [{{"name":"Tích cực","condition":"...","strategy":"..."}}],
  "sources": [{{"name":"...","url":"...","used_for":"...","fetched_at":"..."}}],
  "disclaimer": "{DISCLAIMER}"
}}

Dữ liệu đầu vào:
{data_json}
"""


def _generate_with_gemini(prompt: str) -> str:
    if genai is None or types is None:
        raise RuntimeError("google-genai chưa được cài đặt")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.35,
        response_mime_type="application/json",
    )
    response = client.models.generate_content(model=model, contents=prompt, config=config)
    return response.text or "{}"


def write_briefing(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = build_prompt(payload)
    last_error: Exception | None = None
    if os.environ.get("GEMINI_API_KEY"):
        for _ in range(3):
            try:
                generated = parse_and_validate(_generate_with_gemini(prompt))
                return enrich_generated(generated, payload)
            except Exception as exc:
                last_error = exc
    return fallback_briefing(payload, str(last_error) if last_error else "Không có GEMINI_API_KEY")


def enrich_generated(briefing: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    fallback = fallback_briefing(payload, "Bổ sung trường thiếu từ fallback")
    for key in ["market_cards", "watchlist_rows", "technical_rows", "sources"]:
        if not briefing.get(key):
            briefing[key] = fallback[key]
    if len(briefing.get("hero_summary", [])) < 5:
        briefing["hero_summary"] = fallback["hero_summary"]
    briefing["disclaimer"] = DISCLAIMER
    return validate_briefing(briefing)


def find_metric(cards: list[dict[str, Any]], label: str) -> dict[str, Any]:
    for card in cards:
        if card.get("label") == label:
            return card
    return {"label": label, "value": MISSING, "change": MISSING, "tone": "neutral", "note": MISSING}


def build_market_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    market = payload.get("market_data", {})
    preferred = [
        "VN-Index",
        "VN30",
        "HNX-Index",
        "UPCoM",
        "USD/VND",
        "S&P 500",
        "Dow Jones",
        "Nasdaq",
        "Nikkei 225",
        "Vàng thế giới",
        "Bạc",
        "Dầu WTI",
        "Dầu Brent",
        "Bitcoin",
    ]
    raw_cards = market.get("vietnam_markets", []) + market.get("global_markets", [])
    cards = []
    for label in preferred:
        metric = find_metric(raw_cards, label)
        cards.append(
            {
                "label": metric.get("label", label),
                "value": metric.get("value", MISSING),
                "change": metric.get("change", MISSING),
                "tone": metric.get("tone", "neutral"),
                "note": metric.get("note", MISSING),
            }
        )
    return cards


def default_sector_rows() -> list[dict[str, str]]:
    return [
        {"sector": "Ngân hàng", "impact": "Trung tính", "reason": "Theo dõi tín dụng, NIM, nợ xấu và diễn biến lãi suất liên ngân hàng.", "tickers": "MBB, HDB", "risk": "Chi phí vốn tăng hoặc nợ xấu xấu đi."},
        {"sector": "Chứng khoán", "impact": "Trung tính", "reason": "Nhạy với thanh khoản thị trường và tâm lý margin.", "tickers": "SSI, VND, VCI", "risk": "Thanh khoản suy yếu làm giảm kỳ vọng môi giới."},
        {"sector": "Bất động sản", "impact": "Trung tính", "reason": "Phụ thuộc pháp lý dự án, trái phiếu và mặt bằng lãi suất.", "tickers": "VHM, NLG, KBC", "risk": "Tin pháp lý hoặc dòng tiền trái phiếu kém thuận lợi."},
        {"sector": "Thép", "impact": "Trung tính", "reason": "Theo dõi giá thép, nhu cầu xây dựng và đầu tư công.", "tickers": "HPG, HSG", "risk": "Biên lợi nhuận bị ép bởi giá nguyên liệu."},
        {"sector": "Dầu khí", "impact": "Trung tính", "reason": "Nhạy với WTI/Brent và tiến độ dự án thượng nguồn.", "tickers": "GAS, PVD, PVS", "risk": "Giá dầu đảo chiều hoặc dự án chậm."},
        {"sector": "Bán lẻ", "impact": "Trung tính", "reason": "Theo dõi sức mua, biên lợi nhuận và mùa cao điểm.", "tickers": "MWG, FRT, PNJ", "risk": "Cầu tiêu dùng phục hồi chậm."},
        {"sector": "Xuất khẩu", "impact": "Trung tính", "reason": "Phụ thuộc đơn hàng quốc tế, tỷ giá và logistics.", "tickers": "GMD, VNM", "risk": "Cầu thế giới yếu hoặc chi phí tăng."},
        {"sector": "Công nghệ", "impact": "Trung tính", "reason": "Theo dõi Nasdaq, USD và câu chuyện tăng trưởng dài hạn.", "tickers": "FPT", "risk": "Áp lực định giá khi Nasdaq điều chỉnh."},
        {"sector": "Vàng/bạc", "impact": "Trung tính", "reason": "Liên quan biến động vàng, bạc và sức mua trang sức.", "tickers": "PNJ", "risk": "Biến động giá vàng quá mạnh ảnh hưởng tồn kho và nhu cầu."},
    ]


def build_impact_rows(cards: list[dict[str, Any]]) -> list[dict[str, str]]:
    wti = find_metric(cards, "Dầu WTI")
    nasdaq = find_metric(cards, "Nasdaq")
    usd = find_metric(cards, "USD/VND")
    return [
        {"target": "Dầu khí", "impact": "Trung tính", "reason": f"Dầu WTI {wti.get('change')} cần theo dõi tác động tới GAS, PVD, PVS, BSR."},
        {"target": "FPT/Công nghệ", "impact": "Trung tính", "reason": f"Nasdaq {nasdaq.get('change')} có thể ảnh hưởng tâm lý nhóm công nghệ."},
        {"target": "Ngân hàng", "impact": "Trung tính", "reason": f"USD/VND {usd.get('change')} và lãi suất cần được cập nhật thêm trước khi kết luận."},
    ]


def build_technical_rows(payload: dict[str, Any], watchlist_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for metric in payload.get("market_data", {}).get("vietnam_markets", []):
        if metric.get("label") != "VN-Index":
            continue
        tech = metric.get("technical", {})
        rows.append(
            {
                "ticker": "VN-Index",
                "support": str(tech.get("support") or MISSING),
                "resistance": str(tech.get("resistance") or MISSING),
                "ma20": str(tech.get("ma20") or MISSING),
                "ma50": str(tech.get("ma50") or MISSING),
                "rsi": str(tech.get("rsi14") or MISSING),
                "macd": str(tech.get("macd") or MISSING),
                "breakout": tech.get("breakout_scenario") or MISSING,
                "breakdown": tech.get("breakdown_scenario") or MISSING,
            }
        )
    if not rows:
        rows.append({"ticker": "VN-Index", "support": MISSING, "resistance": MISSING, "ma20": MISSING, "ma50": MISSING, "rsi": MISSING, "macd": MISSING, "breakout": MISSING, "breakdown": MISSING})

    for row in watchlist_rows[:7]:
        tech = row.get("technical", {})
        rows.append(
            {
                "ticker": row.get("ticker", ""),
                "support": str(tech.get("support") or MISSING),
                "resistance": str(tech.get("resistance") or MISSING),
                "ma20": str(tech.get("ma20") or MISSING),
                "ma50": str(tech.get("ma50") or MISSING),
                "rsi": str(tech.get("rsi14") or MISSING),
                "macd": str(tech.get("macd") or MISSING),
                "breakout": tech.get("breakout_scenario") or MISSING,
                "breakdown": tech.get("breakdown_scenario") or MISSING,
            }
        )
    return rows


def fallback_sections(payload: dict[str, Any], cards: list[dict[str, Any]], reason: str) -> list[dict[str, Any]]:
    market = payload.get("market_data", {})
    news = payload.get("news", {}).get("items", [])
    breadth = market.get("market_breadth", {}).get("comment", MISSING)
    liquidity = market.get("liquidity", {}).get("comment", MISSING)
    foreign = market.get("foreign_flow", {}).get("comment", MISSING)
    proprietary = market.get("proprietary_flow", {}).get("comment", MISSING)
    top_news = [item.get("title", "") for item in news[:4] if item.get("title")]
    news_text = "; ".join(top_news) if top_news else MISSING
    return [
        {"number": "01", "title": "Tóm tắt nhanh", "kicker": "Fallback AI", "paragraphs": [f"Bản tin được tạo bằng fallback vì {reason}. Hệ thống chỉ sử dụng dữ liệu có nguồn và ghi rõ phần thiếu."], "bullets": [
            "Thị trường quốc tế được lấy từ Yahoo Finance nếu truy cập được.",
            "Dữ liệu Việt Nam ưu tiên file manual_market_data.json khi API công khai không ổn định.",
            f"Dòng tiền/khối ngoại: {foreign}.",
            "Rủi ro trong ngày nằm ở biến động lãi suất, tỷ giá, hàng hóa và tâm lý quốc tế.",
            "Không mua đuổi; chỉ theo dõi các kịch bản có điều kiện."
        ]},
        {"number": "02", "title": "Dashboard chỉ số", "kicker": "Dữ liệu thực tế", "paragraphs": ["Các card chỉ số phía trên là dữ liệu đầu vào chính cho bản tin. Mục nào thiếu sẽ ghi rõ chưa có dữ liệu cập nhật."], "bullets": []},
        {"number": "03", "title": "TTCK Việt Nam", "kicker": "Dữ liệu thực tế / Suy luận", "paragraphs": [f"VN-Index, VN30, HNX và UPCoM đang phụ thuộc dữ liệu nhập tay. Độ rộng thị trường: {breadth}. Thanh khoản: {liquidity}."], "bullets": [f"Khối ngoại: {foreign}.", f"Tự doanh: {proprietary}.", "Cổ phiếu tác động mạnh cần bổ sung trong manual_market_data.json nếu có dữ liệu phiên gần nhất."]},
        {"number": "04", "title": "Vĩ mô trong nước", "kicker": "Theo dõi", "paragraphs": ["Tỷ giá USD/VND, lãi suất liên ngân hàng, chính sách SBV/Bộ Tài chính và thông tin nâng hạng cần được cập nhật từ nguồn chính thức trước giờ gửi khách hàng."], "bullets": ["Tác động chính thường đi qua nhóm ngân hàng, chứng khoán, bất động sản và xuất khẩu."]},
        {"number": "05", "title": "Dòng tiền & vị thế", "kicker": "Suy luận broker", "paragraphs": ["Khi chưa có số liệu dòng tiền đầy đủ, ưu tiên đọc thanh khoản thị trường, độ lan tỏa và phản ứng tại nhóm dẫn dắt."], "bullets": ["Nếu dòng tiền chỉ tập trung vào trụ, nên thận trọng với mua đuổi.", "Nếu thanh khoản lan tỏa kèm độ rộng tốt, có thể theo dõi trading tỷ trọng nhỏ."]},
        {"number": "06", "title": "Nhóm ngành", "kicker": "Kỳ vọng thị trường", "paragraphs": ["Ngân hàng, chứng khoán, bất động sản, thép, dầu khí, bán lẻ, xuất khẩu, công nghệ và vàng/bạc được theo dõi trong bảng ngành phía dưới."], "bullets": ["Tác động từng ngành cần xác nhận bằng dữ liệu giá, dòng tiền và tin doanh nghiệp."]},
        {"number": "07", "title": "Mã & nhóm ngành tác động", "kicker": "Bảng tác động", "paragraphs": ["Bảng tác động phía dưới liên kết hàng hóa, quốc tế và vĩ mô với nhóm cổ phiếu Việt Nam."], "bullets": []},
        {"number": "08", "title": "Watchlist giao dịch có điều kiện", "kicker": "Không phải khuyến nghị", "paragraphs": ["Watchlist chỉ dùng để theo dõi. Vùng mua/chốt lời/cắt lỗ phải được xác nhận thêm bằng hỗ trợ, kháng cự, MA20/MA50 hoặc nền tích lũy."], "bullets": []},
        {"number": "09", "title": "Phân tích kỹ thuật", "kicker": "MA20 / MA50 / RSI / MACD", "paragraphs": ["Nếu không đủ dữ liệu lịch sử 60 phiên, hệ thống ghi cần cập nhật thêm dữ liệu giá thay vì suy diễn vùng kỹ thuật."], "bullets": []},
        {"number": "10", "title": "Vĩ mô & thời sự quốc tế", "kicker": "Mỹ / Châu Á / Hàng hóa", "paragraphs": [f"Tin đáng chú ý: {news_text}. Cần theo dõi Dow Jones, S&P 500, Nasdaq, Nikkei, vàng, bạc, dầu WTI/Brent, USD Index, lợi suất 10 năm Mỹ và crypto nếu biến động lớn."], "bullets": []},
        {"number": "11", "title": "Lịch sự kiện", "kicker": "Hôm nay / Tuần này", "paragraphs": ["Theo dõi lịch công bố CPI, PPI, PMI, việc làm Mỹ, phát biểu Fed, tin chính sách trong nước và mùa báo cáo KQKD."], "bullets": ["Sự kiện lãi suất/tỷ giá ảnh hưởng ngân hàng, chứng khoán, bất động sản.", "Sự kiện dầu khí và hàng hóa ảnh hưởng dầu khí, thép, xuất khẩu."]},
        {"number": "12", "title": "Góc nhìn & chiến lược", "kicker": "Kịch bản hành động", "paragraphs": ["Luận điểm tích cực là thị trường giữ hỗ trợ và thanh khoản lan tỏa. Luận điểm rủi ro là thủng hỗ trợ kèm bán ròng/áp lực quốc tế."], "bullets": ["Không mua đuổi.", "Ưu tiên cổ phiếu có nền.", "Giữ kỷ luật cắt lỗ.", "Tách rõ trading T+ và nắm giữ."]},
        {"number": "13", "title": "CTA liên hệ", "kicker": "HDUNGINVEST", "paragraphs": ["Liên hệ tư vấn đầu tư HDUNGINVEST qua hotline placeholder và QR Zalo placeholder ở cuối bài."], "bullets": []},
        {"number": "14", "title": "Nguồn tham khảo", "kicker": "Minh bạch nguồn", "paragraphs": ["Nguồn tham khảo gồm Vietstock, CafeF, VnEconomy, Reuters/CNBC nếu truy cập được, Yahoo Finance và file dữ liệu thủ công."], "bullets": []},
    ]


def fallback_briefing(payload: dict[str, Any], reason: str) -> dict[str, Any]:
    cards = build_market_cards(payload)
    vnindex = find_metric(cards, "VN-Index")
    wti = find_metric(cards, "Dầu WTI")
    nasdaq = find_metric(cards, "Nasdaq")
    watchlist_data = payload.get("watchlist", [])
    automated = payload.get("market_data", {}).get("automated_watchlist", {})
    watchlist_rows = build_watchlist_rows(watchlist_data, automated)[:12]
    technical_rows = build_technical_rows(payload, watchlist_rows)
    sources = payload.get("sources", [])

    data = {
        "title": f"VN-Index {vnindex.get('change')}, dầu WTI {wti.get('change')}, Nasdaq {nasdaq.get('change')}",
        "subtitle": "Bản tin thị trường theo dữ liệu công khai và dữ liệu nhập tay.",
        "date_label": payload.get("date_label", ""),
        "updated_label": payload.get("updated_label", ""),
        "hero_summary": [
            f"Thị trường Việt Nam: VN-Index ghi nhận {vnindex.get('value')} với biến động {vnindex.get('change')}.",
            f"Quốc tế: Nasdaq {nasdaq.get('change')}; diễn biến này có thể ảnh hưởng nhóm công nghệ và khẩu vị rủi ro.",
            f"Hàng hóa: dầu WTI {wti.get('change')}, cần theo dõi tác động tới nhóm dầu khí.",
            f"Dòng tiền/khối ngoại: {payload.get('market_data', {}).get('foreign_flow', {}).get('comment', MISSING)}.",
            "Nhóm ngành nổi bật cần xác nhận thêm qua thanh khoản, độ rộng và tin doanh nghiệp.",
            "Rủi ro trong ngày gồm tỷ giá, lợi suất Mỹ, giá hàng hóa và áp lực bán ròng nếu có.",
        ],
        "market_cards": cards,
        "sections": fallback_sections(payload, cards, reason),
        "sector_rows": default_sector_rows(),
        "impact_rows": build_impact_rows(cards),
        "watchlist_rows": watchlist_rows,
        "technical_rows": technical_rows,
        "events": [
            {"timeframe": "Hôm nay", "event": "Cập nhật dữ liệu phiên gần nhất, tỷ giá, khối ngoại và tin doanh nghiệp.", "impact": "Ảnh hưởng trực tiếp tới chiến lược trong phiên.", "affected_groups": "Ngân hàng, chứng khoán, bất động sản, nhóm trụ."},
            {"timeframe": "Tuần này", "event": "Theo dõi Fed, CPI/PPI/PMI, việc làm Mỹ, giá dầu và lợi suất 10 năm.", "impact": "Tác động tới khẩu vị rủi ro toàn cầu.", "affected_groups": "Công nghệ, xuất khẩu, dầu khí, vàng/bạc."},
            {"timeframe": "Trong nước", "event": "Theo dõi SBV, Bộ Tài chính, nâng hạng thị trường và KQKD.", "impact": "Ảnh hưởng định giá và dòng tiền theo ngành.", "affected_groups": "Ngân hàng, chứng khoán, bất động sản."},
        ],
        "scenarios": [
            {"name": "Tích cực", "condition": "VN-Index giữ hỗ trợ, thanh khoản cải thiện và độ rộng lan tỏa.", "strategy": "Có thể nâng tỷ trọng từng phần ở cổ phiếu có nền, tránh mua đuổi khi tăng nóng."},
            {"name": "Trung tính", "condition": "Chỉ số đi ngang, dòng tiền phân hóa và chưa xác nhận xu hướng mới.", "strategy": "Giữ tỷ trọng cân bằng, ưu tiên trading tỷ trọng nhỏ và quản trị rủi ro."},
            {"name": "Tiêu cực", "condition": "Thủng hỗ trợ kèm thanh khoản cao hoặc khối ngoại bán ròng mạnh.", "strategy": "Hạ tỷ trọng tham khảo, ưu tiên bảo toàn vốn và giữ kỷ luật cắt lỗ."},
        ],
        "sources": sources,
        "disclaimer": DISCLAIMER,
    }
    return validate_briefing(data)
