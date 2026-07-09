from scripts.gemini_writer import REQUIRED_SECTION_TITLES, build_prompt, fallback_briefing
from scripts.text_postprocessor import fix_text, postprocess_briefing
from scripts.validate_output import DISCLAIMER


def minimal_payload():
    return {
        "date": "2026-07-09",
        "date_label": "09/07/2026",
        "updated_label": "Cập nhật lúc: 07:00 09/07/2026, giờ Việt Nam",
        "brand": {"name": "HDUNGINVEST"},
        "market_data": {
            "vietnam_markets": [],
            "global_markets": [],
            "foreign_flow": {"comment": "chưa có dữ liệu cập nhật"},
            "market_breadth": {"comment": "chưa có dữ liệu cập nhật"},
            "liquidity": {"comment": "chưa có dữ liệu cập nhật"},
            "proprietary_flow": {"comment": "chưa có dữ liệu cập nhật"},
        },
        "news": {"items": [], "errors": []},
        "watchlist": [],
        "sources": [{"name": "manual", "url": "data/manual_market_data.json", "used_for": "test", "updated_at": ""}],
    }


def test_prompt_contains_required_sections_and_flow_check_schema():
    prompt = build_prompt(minimal_payload())
    for section in REQUIRED_SECTION_TITLES:
        assert section in prompt
    assert "flow_reality_check" in prompt
    assert "HDUNGINVEST Daily Research" in prompt


def test_fallback_briefing_is_complete_without_ai_key():
    briefing = fallback_briefing(minimal_payload(), "test")
    assert len(briefing["sections"]) == 14
    assert len(briefing["market_cards"]) == 17
    assert briefing["disclaimer"] == DISCLAIMER
    assert "flow_reality_check" in briefing["sections"][0]


def test_text_postprocessor_preserves_source_filenames():
    text = "Nguồn gồm Google Finance, manual_market_data.json, manual_news.json."
    assert fix_text(text) == text

    briefing = postprocess_briefing(
        {
            "sources": [
                {
                    "name": "manual_market_data.json",
                    "url": "data/manual_market_data.json",
                    "used_for": "chua co du lieu cap nhat",
                }
            ]
        }
    )
    assert briefing["sources"][0]["name"] == "manual_market_data.json"
    assert briefing["sources"][0]["used_for"] == "chưa có dữ liệu cập nhật"
