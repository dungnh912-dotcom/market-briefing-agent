from __future__ import annotations

import json
import os
from typing import Any

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover
    genai = None
    types = None

try:
    from scripts.technical_analysis import build_watchlist_rows
    from scripts.validate_output import DISCLAIMER, parse_and_validate, validate_briefing
except ImportError:
    from technical_analysis import build_watchlist_rows
    from validate_output import DISCLAIMER, parse_and_validate, validate_briefing

MISSING = "chưa có dữ liệu cập nhật"

REQUIRED_SECTION_TITLES = [
    "Tóm tắt nhanh",
    "Dashboard chỉ số",
    "TTCK Việt Nam",
    "Vĩ mô trong nước",
    "Dòng tiền & vị thế",
    "Tin Việt Nam mới nhất",
    "Tin quốc tế mới nhất",
    "Nhóm ngành",
    "Mã & nhóm ngành tác động",
    "Watchlist giao dịch có điều kiện",
    "Phân tích kỹ thuật",
    "Lịch sự kiện",
    "Góc nhìn & chiến lược",
    "Nguồn tham khảo",
]

SYSTEM_PROMPT = f"""Bạn là một Market Briefing Agent cho broker chứng khoán tại Việt Nam.
Bạn có tư duy hoài nghi, thực chiến, tập trung vào dòng tiền, thanh khoản, khối ngoại, margin, áp lực nợ, game kéo-xả và rủi ro phân phối.
Tuy nhiên, bạn không được bịa dữ liệu, không được vu cáo doanh nghiệp, và phải phân biệt rõ dữ liệu thực tế, kỳ vọng thị trường, suy luận.

Được dùng văn phong trực diện như: cần cảnh giác, rủi ro phân phối, dòng tiền có dấu hiệu không tự nhiên, khả năng tạo thanh khoản kỹ thuật, áp lực margin/force sell, game kéo-xả cần theo dõi, nhỏ lẻ dễ bị cuốn vào nhịp FOMO.
Không dùng câu cáo buộc chắc chắn như "doanh nghiệp chắc chắn lừa đảo", "chủ tịch đang cắm hàng", "đội lái đang quay tay", "sắp úp bô" nếu không có nguồn chính thức.
Nếu thiếu dữ liệu, ghi đúng: "{MISSING}".
Không khuyến nghị mua/bán chắc chắn và không cam kết lợi nhuận.
Disclaimer bắt buộc: {DISCLAIMER}
"""


def get_gemini_api_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


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
            "interbank_rate": market.get("interbank_rate", {}),
            "sector_flow": market.get("sector_flow", []),
            "top_gainers": market.get("top_gainers", []),
            "top_losers": market.get("top_losers", []),
        },
        "news": {"items": news.get("items", [])[:30], "errors": news.get("errors", [])},
        "watchlist": payload.get("watchlist", [])[:20],
        "sources": payload.get("sources", []),
    }


def build_prompt(payload: dict[str, Any]) -> str:
    sections = "\n".join(f"- {title}" for title in REQUIRED_SECTION_TITLES)
    data_json = json.dumps(compact_payload(payload), ensure_ascii=False, default=str)
    return f"""Hãy viết bản tin HDINVEST Daily Market Briefing bằng tiếng Việt, phong cách báo cáo research cao cấp cho broker/chuyên viên tư vấn chứng khoán.

Các phần bắt buộc:
{sections}

Yêu cầu phân tích:
- Ngắn gọn, sắc, có góc nhìn dòng tiền thực chiến.
- Không bịa số liệu; thiếu dữ liệu thì ghi "{MISSING}".
- Với mỗi tin doanh nghiệp/tin ngành/tin vĩ mô quan trọng, phải có flow_reality_check gồm:
  1. mask: Bức màn truyền thông, thị trường muốn nhà đầu tư hiểu tin này theo hướng tích cực ra sao.
  2. reality_to_verify: Bản chất cần kiểm chứng: dòng tiền thật, thanh khoản thật/kéo kỹ thuật, margin/force sell, đảo nợ, phát hành, pha loãng, bán vốn, trái phiếu đáo hạn, cổ đông lớn/khối ngoại/tự doanh bán ra.
  3. stock_impact: Hệ quả với cổ phiếu nếu dòng tiền xác nhận hoặc nếu chỉ là kéo giá tạo thanh khoản; vùng giá/rủi ro cần theo dõi.
- Luôn phân biệt factual_data, market_expectation, inference.
- Watchlist chỉ là giao dịch có điều kiện, luôn có ý "chỉ phù hợp khi thị trường xác nhận thanh khoản".

Trả về JSON sạch theo schema:
{{
  "title": "...",
  "subtitle": "Daily Market Briefing for Vietnamese Brokers",
  "updated_at": "...",
  "executive_summary": ["5-7 dòng"],
  "market_cards": [{{"label":"VN-Index","value":"...","change":"...","tone":"up|down|neutral","note":"market takeaway ngắn"}}],
  "sections": [{{
    "number":"01",
    "title":"...",
    "factual_data":"...",
    "market_expectation":"...",
    "inference":"...",
    "flow_reality_check": {{
      "mask":"...",
      "reality_to_verify":"...",
      "stock_impact":"..."
    }}
  }}],
  "sector_impacts": [{{"sector":"Ngân hàng","impact":"Hưởng lợi|Bất lợi|Trung tính","reason":"...","tickers":"MBB, HDB","risk":"..."}}],
  "watchlist": [{{"ticker":"MBB","sector":"Ngân hàng","thesis":"...","entry_zone":"...","take_profit_zone":"...","stop_loss_zone":"...","activation":"...","risk":"..."}}],
  "technical_analysis": [{{"ticker":"VN-Index","support":"...","resistance":"...","ma20":"...","ma50":"...","rsi":"...","macd":"...","breakout":"...","breakdown":"..."}}],
  "event_calendar": [{{"timeframe":"Hôm nay","event":"...","impact":"...","affected_groups":"...","flow_reality_check":{{"mask":"...","reality_to_verify":"...","stock_impact":"..."}}}}],
  "strategy_view": [{{"name":"Tích cực","condition":"...","strategy":"..."}}],
  "sources": [{{"name":"...","url":"...","used_for":"...","updated_at":"..."}}],
  "disclaimer": "{DISCLAIMER}"
}}

Dữ liệu đầu vào:
{data_json}
"""


def _generate_with_gemini(prompt: str) -> str:
    if genai is None or types is None:
        raise RuntimeError("google-genai chưa được cài đặt")
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.32,
        response_mime_type="application/json",
    )
    response = client.models.generate_content(model=model, contents=prompt, config=config)
    return response.text or "{}"


def write_briefing(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = build_prompt(payload)
    last_error: Exception | None = None
    if get_gemini_api_key():
        for _ in range(3):
            try:
                generated = parse_and_validate(_generate_with_gemini(prompt))
                return enrich_generated(generated, payload)
            except Exception as exc:
                last_error = exc
    return fallback_briefing(payload, str(last_error) if last_error else "Không có GEMINI_API_KEY")


def enrich_generated(briefing: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    fallback = fallback_briefing(payload, "Bổ sung trường thiếu từ fallback")
    for key in ["market_cards", "sector_rows", "impact_rows", "watchlist_rows", "technical_rows", "events", "scenarios", "sources"]:
        if not briefing.get(key):
            briefing[key] = fallback[key]
    if len(briefing.get("hero_summary", [])) < 5:
        briefing["hero_summary"] = fallback["hero_summary"]
    briefing["subtitle"] = briefing.get("subtitle") or "Daily Market Briefing for Vietnamese Brokers"
    briefing["disclaimer"] = DISCLAIMER
    briefing["ai_status"] = {
        "mode": "gemini",
        "model": os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
        "message": "Gemini API đã tạo nội dung.",
    }
    return validate_briefing(briefing)


def find_metric(cards: list[dict[str, Any]], label: str) -> dict[str, Any]:
    fallback = None
    for card in cards:
        if card.get("label") == label:
            if MISSING not in f"{card.get('value', '')}{card.get('change', '')}{card.get('note', '')}":
                return card
            fallback = fallback or card
    return fallback or {"label": label, "value": MISSING, "change": MISSING, "tone": "neutral", "note": MISSING}


def build_market_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    market = payload.get("market_data", {})
    preferred = [
        "VN-Index",
        "VN30",
        "HNX-Index",
        "UPCoM",
        "Thanh khoản HOSE",
        "Khối ngoại",
        "Tự doanh",
        "USD/VND",
        "Lãi suất liên ngân hàng",
        "S&P 500",
        "Dow Jones",
        "Nasdaq",
        "Nikkei 225",
        "Vàng thế giới",
        "Dầu WTI",
        "Dầu Brent",
        "Bitcoin",
    ]
    raw_cards = market.get("vietnam_markets", []) + market.get("global_markets", [])
    cards = []
    for label in preferred:
        metric = find_metric(raw_cards, label)
        note = metric.get("note", MISSING)
        if metric.get("updated_at") and metric.get("updated_at") != MISSING:
            note = f"{note} Cập nhật nguồn: {metric.get('updated_at')}."
        cards.append(
            {
                "label": metric.get("label", label),
                "value": metric.get("value", MISSING),
                "change": metric.get("change", MISSING),
                "tone": metric.get("tone", "neutral"),
                "note": note,
            }
        )
    return cards


def flow_check(mask: str, reality: str, impact: str) -> dict[str, str]:
    return {"mask": mask, "reality_to_verify": reality, "stock_impact": impact}


def section(number: str, title: str, factual: str, expectation: str, inference: str, flow: dict[str, str]) -> dict[str, Any]:
    return {
        "number": number,
        "title": title,
        "kicker": "Dữ liệu thực tế / Kỳ vọng thị trường / Suy luận",
        "paragraphs": [],
        "bullets": [],
        "factual_data": factual,
        "market_expectation": expectation,
        "inference": inference,
        "flow_reality_check": flow,
    }


def default_sector_rows() -> list[dict[str, str]]:
    return [
        {"sector": "Ngân hàng", "impact": "Trung tính", "reason": "Theo dõi tín dụng, NIM, nợ xấu, lãi suất liên ngân hàng và áp lực chi phí vốn.", "tickers": "MBB, HDB", "risk": "Margin/force sell hoặc chi phí vốn tăng có thể làm dòng tiền yếu đi."},
        {"sector": "Chứng khoán", "impact": "Trung tính", "reason": "Nhạy với thanh khoản HOSE, tâm lý margin và mức độ lan tỏa của dòng tiền.", "tickers": "SSI, VND, VCI", "risk": "Thanh khoản tăng nhưng chỉ tập trung vào trụ có thể là tín hiệu thiếu bền."},
        {"sector": "Bất động sản", "impact": "Trung tính", "reason": "Phụ thuộc pháp lý, trái phiếu đáo hạn, đảo nợ, phát hành và mặt bằng lãi suất.", "tickers": "VHM, NLG, KBC", "risk": "Tin tốt nhưng đi kèm áp lực bán vốn/pha loãng cần kiểm chứng."},
        {"sector": "Thép", "impact": "Trung tính", "reason": "Theo dõi giá thép, đầu tư công, cầu xây dựng và biên lợi nhuận.", "tickers": "HPG, HSG", "risk": "Nhỏ lẻ dễ FOMO nếu giá kéo nhanh trong khi sản lượng chưa xác nhận."},
        {"sector": "Dầu khí", "impact": "Trung tính", "reason": "Nhạy với WTI/Brent và tiến độ dự án.", "tickers": "GAS, PVD, PVS", "risk": "Dầu tăng không đồng nghĩa mọi cổ phiếu dầu khí đều hút tiền thật."},
        {"sector": "Bán lẻ", "impact": "Trung tính", "reason": "Theo dõi sức mua, biên lợi nhuận và câu chuyện tái cấu trúc.", "tickers": "MWG, FRT, PNJ", "risk": "Kỳ vọng hồi phục cần đi kèm doanh thu và dòng tiền xác nhận."},
        {"sector": "Xuất khẩu", "impact": "Trung tính", "reason": "Phụ thuộc đơn hàng quốc tế, tỷ giá, logistics và cầu thế giới.", "tickers": "GMD, VNM", "risk": "USD mạnh có thể vừa hỗ trợ doanh thu vừa gây áp lực chi phí."},
        {"sector": "Công nghệ", "impact": "Trung tính", "reason": "Theo dõi Nasdaq, USD và kỳ vọng tăng trưởng dài hạn.", "tickers": "FPT", "risk": "Định giá cao dễ nhạy với điều chỉnh của Nasdaq."},
        {"sector": "Vàng/bạc", "impact": "Trung tính", "reason": "Liên quan biến động vàng, bạc và sức mua trang sức.", "tickers": "PNJ", "risk": "Giá vàng biến động mạnh có thể làm hành vi tiêu dùng khó đoán."},
    ]


def build_impact_rows(cards: list[dict[str, Any]]) -> list[dict[str, str]]:
    wti = find_metric(cards, "Dầu WTI")
    nasdaq = find_metric(cards, "Nasdaq")
    usd = find_metric(cards, "USD/VND")
    return [
        {"target": "Dầu khí", "impact": "Trung tính", "reason": f"Dầu WTI {wti.get('change')} hỗ trợ tâm lý, nhưng cần kiểm chứng dòng tiền thật ở GAS, PVD, PVS, BSR."},
        {"target": "FPT/Công nghệ", "impact": "Trung tính", "reason": f"Nasdaq {nasdaq.get('change')} ảnh hưởng khẩu vị rủi ro; nếu thanh khoản yếu, nhịp kéo có thể chỉ là kỹ thuật."},
        {"target": "Ngân hàng", "impact": "Trung tính", "reason": f"USD/VND {usd.get('change')} và lãi suất cần được cập nhật trước khi đánh giá chi phí vốn."},
    ]


def build_technical_rows(payload: dict[str, Any], watchlist_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
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
    vn_news = "; ".join(item.get("title", "") for item in news[:3] if item.get("title")) or MISSING
    intl_news = "; ".join(item.get("title", "") for item in news[3:6] if item.get("title")) or MISSING
    return [
        section("01", "Tóm tắt nhanh", f"Bản tin được tạo bằng fallback vì {reason}. Hệ thống chỉ dùng dữ liệu có nguồn.", "Thị trường có thể phản ứng mạnh với tỷ giá, lãi suất, giá dầu và Nasdaq.", "Ưu tiên quan sát dòng tiền thật thay vì chạy theo headline.", flow_check("Headline thường nhấn vào điểm tích cực để kích hoạt chú ý.", "Cần kiểm chứng thanh khoản lan tỏa hay chỉ kéo kỹ thuật ở một vài trụ.", "Nếu dòng tiền không xác nhận, nhỏ lẻ dễ bị cuốn vào nhịp FOMO.")),
        section("02", "Dashboard chỉ số", "Các card chỉ số phía trên giữ nguyên layout; mục thiếu ghi chưa có dữ liệu cập nhật.", "Card tăng/giảm chỉ là tín hiệu đầu vào, không phải kết luận giao dịch.", "Market takeaway cần đi cùng thanh khoản và độ rộng.", flow_check("Màu xanh trên chỉ số dễ tạo cảm giác an toàn.", "Kiểm chứng số mã tăng/giảm, giá trị khớp lệnh và khối ngoại.", "Nếu chỉ số xanh nhưng độ rộng hẹp, rủi ro phân phối vẫn cần cảnh giác.")),
        section("03", "TTCK Việt Nam", f"Độ rộng: {breadth}. Thanh khoản HOSE: {liquidity}. Khối ngoại: {foreign}. Tự doanh: {proprietary}.", "Thị trường cần xác nhận bằng thanh khoản và nhóm dẫn dắt.", "Nếu tiền chỉ tập trung vào trụ, broker nên hạn chế mua đuổi.", flow_check("Chỉ số tăng có thể che đi nền thanh khoản yếu.", "Kiểm tra dòng tiền thật vào midcap/bluechip hay chỉ tạo thanh khoản kỹ thuật.", "Thủng vùng hỗ trợ kèm bán ròng mạnh là tín hiệu giảm tỷ trọng trading.")),
        section("04", "Vĩ mô trong nước", "USD/VND, lãi suất liên ngân hàng, SBV, Bộ Tài chính và nâng hạng cần cập nhật từ nguồn chính thức.", "Tỷ giá/lãi suất ổn định sẽ hỗ trợ tâm lý nhóm ngân hàng, chứng khoán, bất động sản.", "Nếu lãi suất hoặc tỷ giá căng, margin và định giá có thể chịu áp lực.", flow_check("Tin chính sách thường được diễn giải tích cực trước.", "Kiểm chứng có dòng tiền thật vào nhóm hưởng lợi hay không.", "Nếu tin tốt đi kèm bán ròng, cần coi đó là giả thuyết rủi ro cần kiểm chứng.")),
        section("05", "Dòng tiền & vị thế", f"Dữ liệu khối ngoại: {foreign}. Dữ liệu tự doanh: {proprietary}.", "Dòng tiền lan tỏa sẽ tốt hơn nhịp kéo hẹp ở trụ.", "Cần cảnh giác rủi ro phân phối nếu thanh khoản tăng nhưng giá đóng cửa yếu.", flow_check("Thanh khoản lớn dễ được hiểu là tiền vào mạnh.", "Phân biệt mua chủ động với kéo giá tạo thanh khoản; theo dõi margin/force sell.", "Nếu lực cầu không giữ được cuối phiên, giảm tỷ trọng trading là lựa chọn thận trọng.")),
        section("06", "Tin Việt Nam mới nhất", vn_news, "Tin doanh nghiệp/ngành có thể kích hoạt dòng tiền ngắn hạn.", "Tin tốt chỉ có giá trị khi đi cùng giá, volume và hành vi mua ròng xác nhận.", flow_check("Bức màn truyền thông thường làm nổi bật kỳ vọng lợi nhuận hoặc catalyst.", "Kiểm chứng phát hành, pha loãng, trái phiếu đáo hạn, cổ đông lớn bán ra.", "Nếu chỉ là kéo giá theo tin, rủi ro phân phối sau nhịp FOMO cần theo dõi.")),
        section("07", "Tin quốc tế mới nhất", intl_news, "Fed, CPI, PMI, lợi suất Mỹ, dầu và Nasdaq ảnh hưởng khẩu vị rủi ro.", "Tác động vào Việt Nam thường qua tỷ giá, khối ngoại và nhóm công nghệ/dầu khí.", flow_check("Tin quốc tế tích cực có thể kích hoạt gap tăng đầu phiên.", "Kiểm chứng khối ngoại có quay lại mua ròng hay không.", "Nếu gap tăng không có thanh khoản, rủi ro bull-trap cần cảnh giác.")),
        section("08", "Nhóm ngành", "Ngân hàng, chứng khoán, bất động sản, thép, dầu khí, bán lẻ, xuất khẩu, công nghệ và vàng/bạc được theo dõi.", "Dòng tiền chỉ đáng tin khi có lan tỏa và nền giá đủ chặt.", "Game kéo-xả cần theo dõi ở nhóm tăng nóng nhưng thiếu nền tích lũy.", flow_check("Câu chuyện ngành dễ kéo dòng tiền ngắn hạn.", "Kiểm chứng dòng tiền thật, margin và thanh khoản từng mã.", "Nhóm tăng nóng nhưng volume không bền có rủi ro phân phối.")),
        section("09", "Mã & nhóm ngành tác động", "Bảng tác động liên kết hàng hóa, quốc tế và vĩ mô với cổ phiếu Việt Nam.", "Tác động liên thị trường chỉ là giả thuyết cho đến khi giá/volume xác nhận.", "Không đánh đồng giá dầu/Nasdaq với mọi cổ phiếu liên quan.", flow_check("Headline liên thị trường thường tạo liên tưởng nhanh.", "Kiểm chứng mã nào thật sự hút tiền.", "Nếu cổ phiếu không phản ứng với tin tốt, đó là tín hiệu yếu cần chú ý.")),
        section("10", "Watchlist giao dịch có điều kiện", "Watchlist chỉ dùng để theo dõi, không phải khuyến nghị.", "Chỉ phù hợp khi thị trường xác nhận thanh khoản.", "Không mua đuổi; tách trading T+ và nắm giữ.", flow_check("Danh sách theo dõi dễ bị hiểu nhầm là khuyến nghị mua.", "Chỉ xem xét nếu hỗ trợ/kháng cự, MA20/MA50 và thanh khoản xác nhận.", "Nếu vi phạm cắt lỗ hoặc mất nền, dừng quan sát hoặc giảm tỷ trọng trading.")),
        section("11", "Phân tích kỹ thuật", "Nếu thiếu lịch sử giá, hệ thống ghi cần cập nhật thêm dữ liệu giá.", "Vượt kháng cự cần thanh khoản xác nhận; thủng hỗ trợ cần hạ rủi ro.", "MA/RSI/MACD chỉ là công cụ, không thay thế quản trị vốn.", flow_check("Tín hiệu kỹ thuật đẹp có thể hút FOMO.", "Kiểm chứng volume, vị thế margin và cung treo phía trên.", "Nếu break giả, cổ phiếu dễ quay lại nền và gây kẹp T+.")),
        section("12", "Lịch sự kiện", "Theo dõi CPI, PPI, PMI, Fed, việc làm Mỹ, SBV, Bộ Tài chính và KQKD.", "Sự kiện mạnh có thể làm biến động tỷ giá, dầu, vàng và khối ngoại.", "Không nên tăng rủi ro trước sự kiện nếu thiếu lợi thế dữ liệu.", flow_check("Lịch sự kiện thường tạo kỳ vọng trước tin.", "Kiểm chứng phản ứng sau tin thay vì mua trước theo đồn đoán.", "Nếu tin ra mà giá không tăng, cần cảnh giác áp lực phân phối.")),
        section("13", "Góc nhìn & chiến lược", "Kịch bản tích cực cần hỗ trợ giữ vững và thanh khoản lan tỏa.", "Kịch bản trung tính là đi ngang phân hóa; kịch bản tiêu cực là thủng hỗ trợ kèm bán ròng.", "Broker nên không mua đuổi, ưu tiên cổ phiếu có nền, giữ kỷ luật cắt lỗ.", flow_check("Thị trường thường tạo cảm giác rõ xu hướng sau một phiên mạnh.", "Kiểm chứng 2-3 phiên để tránh nhiễu kỹ thuật.", "Tách rõ trading T+ và nắm giữ để tránh bị động khi biến động đảo chiều.")),
        section("14", "Nguồn tham khảo", "Nguồn gồm Google Finance, manual_market_data.json, manual_news.json và RSS/public feeds nếu truy cập được.", "Nguồn nào thiếu sẽ ghi chưa có dữ liệu cập nhật.", "Không dùng số liệu không có nguồn.", flow_check("Nguồn tổng hợp có thể trễ hoặc thiếu.", "Kiểm tra updated_at của từng nguồn trước khi gửi khách hàng.", "Nếu dữ liệu stale, chỉ nên dùng như bối cảnh, không dùng làm tín hiệu giao dịch.")),
    ]


def fallback_briefing(payload: dict[str, Any], reason: str) -> dict[str, Any]:
    cards = build_market_cards(payload)
    vnindex = find_metric(cards, "VN-Index")
    wti = find_metric(cards, "Dầu WTI")
    nasdaq = find_metric(cards, "Nasdaq")
    watchlist_rows = build_watchlist_rows(payload.get("watchlist", []), payload.get("market_data", {}).get("automated_watchlist", {}))[:12]
    technical_rows = build_technical_rows(payload, watchlist_rows)
    data = {
        "title": f"VN-Index {vnindex.get('change')}, dầu WTI {wti.get('change')}, Nasdaq {nasdaq.get('change')}",
        "subtitle": "Daily Market Briefing for Vietnamese Brokers",
        "date_label": payload.get("date_label", ""),
        "updated_label": payload.get("updated_label", ""),
        "updated_at": payload.get("updated_at", ""),
        "hero_summary": [
            f"VN-Index ghi nhận {vnindex.get('value')} với biến động {vnindex.get('change')}.",
            f"Nasdaq {nasdaq.get('change')}; tác động tới khẩu vị rủi ro cần kiểm chứng qua khối ngoại.",
            f"Dầu WTI {wti.get('change')}; nhóm dầu khí chỉ đáng theo dõi nếu dòng tiền xác nhận.",
            f"Khối ngoại: {payload.get('market_data', {}).get('foreign_flow', {}).get('comment', MISSING)}.",
            "Cần cảnh giác rủi ro phân phối nếu thanh khoản tăng nhưng độ rộng hẹp.",
            "Watchlist chỉ phù hợp khi thị trường xác nhận thanh khoản.",
        ],
        "market_cards": cards,
        "sections": fallback_sections(payload, cards, reason),
        "sector_rows": default_sector_rows(),
        "impact_rows": build_impact_rows(cards),
        "watchlist_rows": watchlist_rows,
        "technical_rows": technical_rows,
        "events": [
            {"timeframe": "Hôm nay", "event": "Cập nhật dữ liệu phiên gần nhất, tỷ giá, khối ngoại và tin doanh nghiệp.", "impact": "Ảnh hưởng trực tiếp tới chiến lược trong phiên.", "affected_groups": "Ngân hàng, chứng khoán, bất động sản, nhóm trụ.", "flow_mask": "Tin tốt có thể kích hoạt FOMO đầu phiên.", "flow_reality": "Kiểm chứng khối ngoại, tự doanh và thanh khoản thực.", "flow_impact": "Nếu lực cầu yếu cuối phiên, nên giảm rủi ro trading."},
            {"timeframe": "Tuần này", "event": "Theo dõi Fed, CPI/PPI/PMI, việc làm Mỹ, giá dầu và lợi suất 10 năm.", "impact": "Tác động tới khẩu vị rủi ro toàn cầu.", "affected_groups": "Công nghệ, xuất khẩu, dầu khí, vàng/bạc.", "flow_mask": "Dữ liệu quốc tế dễ tạo gap tâm lý.", "flow_reality": "Kiểm chứng phản ứng của USD/VND và khối ngoại.", "flow_impact": "Nếu thị trường không giữ gap, rủi ro bull-trap tăng."},
            {"timeframe": "Trong nước", "event": "Theo dõi SBV, Bộ Tài chính, nâng hạng thị trường và KQKD.", "impact": "Ảnh hưởng định giá và dòng tiền theo ngành.", "affected_groups": "Ngân hàng, chứng khoán, bất động sản.", "flow_mask": "Tin chính sách thường được diễn giải tích cực.", "flow_reality": "Kiểm chứng tiền thật có vào ngành hưởng lợi không.", "flow_impact": "Nếu tin tốt đi kèm bán ròng, cần cảnh giác rủi ro phân phối."},
        ],
        "scenarios": [
            {"name": "Tích cực", "condition": "VN-Index giữ hỗ trợ, thanh khoản cải thiện và độ rộng lan tỏa.", "strategy": "Có thể nâng tỷ trọng từng phần ở cổ phiếu có nền, tránh mua đuổi khi tăng nóng."},
            {"name": "Trung tính", "condition": "Chỉ số đi ngang, dòng tiền phân hóa và chưa xác nhận xu hướng mới.", "strategy": "Giữ tỷ trọng cân bằng, ưu tiên trading tỷ trọng nhỏ và quản trị rủi ro."},
            {"name": "Tiêu cực", "condition": "Thủng hỗ trợ kèm thanh khoản cao hoặc khối ngoại bán ròng mạnh.", "strategy": "Hạ tỷ trọng tham khảo, ưu tiên bảo toàn vốn và giữ kỷ luật cắt lỗ."},
        ],
        "sources": payload.get("sources", []),
        "disclaimer": DISCLAIMER,
        "ai_status": {
            "mode": "fallback",
            "model": os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
            "message": reason,
        },
    }
    return validate_briefing(data)
