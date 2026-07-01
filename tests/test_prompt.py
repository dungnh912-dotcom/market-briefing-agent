from datetime import date

from src.prompt import GUARDRAILS, build_prompt, required_sections_for


def test_prompt_contains_required_sections():
    report_date = date(2026, 7, 1)
    prompt = build_prompt({"global": {}, "vietnam": {}}, report_date)
    for section in required_sections_for("01/07/2026"):
        assert section in prompt


def test_prompt_contains_guardrails():
    assert "Không được đưa khuyến nghị chắc chắn" in GUARDRAILS
    prompt = build_prompt({}, date(2026, 7, 1))
    assert "Có thể mua thăm dò nếu" in prompt
    assert "Không mua đuổi nếu" in prompt
