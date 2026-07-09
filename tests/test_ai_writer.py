from scripts.gemini_writer import REQUIRED_SECTION_TITLES, build_prompt, fallback_briefing
from scripts.validate_output import DISCLAIMER


def minimal_payload():
    return {
        "date": "2026-07-09",
        "date_label": "09/07/2026",
        "updated_label": "Cập nhật: 07:00 · 09/07/2026 · Giờ Việt Nam",
        "brand": {"name": "HDUNGINVEST"},
        "market_data": {
            "vietnam_markets": [],
            "global_markets": [],
            "foreign_flow": {"comment": "chưa có dữ liệu cập nhật"},
            "market_breadth": {"comment": "chưa có dữ liệu cập nhật"},
            "liquidity": {"comment": "chưa có dữ liệu cập nhật"},
        },
        "news": {"items": [], "errors": []},
        "watchlist": [],
        "sources": [{"name": "manual", "url": "data/manual_market_data.json", "used_for": "test", "fetched_at": ""}],
    }


def test_prompt_contains_required_sections():
    prompt = build_prompt(minimal_payload())
    for section in REQUIRED_SECTION_TITLES:
        assert section in prompt
    assert "HDUNGINVEST Daily Research" in prompt


def test_fallback_briefing_is_complete_without_ai_key():
    briefing = fallback_briefing(minimal_payload(), "test")
    assert len(briefing["sections"]) == 14
    assert len(briefing["market_cards"]) == 14
    assert briefing["disclaimer"] == DISCLAIMER
