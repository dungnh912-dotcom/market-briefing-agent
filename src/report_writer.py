from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from sector_mapping import SECTOR_THEMES


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def write_report(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def build_fallback_report(market_data: dict[str, Any], report_date: date) -> str:
    date_text = report_date.strftime("%d/%m/%Y")
    global_lines = _global_market_lines(market_data.get("global", {}))
    news_lines = _news_lines(market_data.get("news", {}))
    vietnam = market_data.get("vietnam", {})
    stock_lines = _stock_watchlist_lines(vietnam.get("stocks", {}))
    vnindex = vietnam.get("vnindex", {})

    return f"""# BẢN TIN THỊ TRƯỜNG NGÀY {date_text}

## 1. Tóm tắt nhanh
- Bản tin được tạo tự động từ dữ liệu thị trường, tin tức và các chỉ báo kỹ thuật cơ bản.
- Ưu tiên giao dịch có điều kiện: chỉ mua khi giá xác nhận, không mua đuổi nếu cổ phiếu tăng nóng.
- Nếu dữ liệu Việt Nam thiếu, hệ thống đã ghi chú trong file dữ liệu thô để broker kiểm tra bổ sung.

## 2. Thị trường quốc tế
{global_lines}

## 3. Tin tức và thị trường Việt Nam
{news_lines}

## 4. Tác động theo nhóm ngành
{_sector_impact_lines()}

## 5. Danh sách cổ phiếu cần theo dõi
{stock_lines}

## 6. Phân tích kỹ thuật VN-Index nếu có dữ liệu
{_technical_sentence("VN-Index", vnindex)}

## 7. Kế hoạch giao dịch trong ngày
- Có thể mua thăm dò nếu chỉ số giữ được vùng hỗ trợ gần nhất và cổ phiếu vượt vùng mua với thanh khoản cải thiện.
- Chỉ mua khi cổ phiếu không vi phạm hỗ trợ 20 phiên và RSI chưa rơi vào trạng thái quá nóng.
- Không mua đuổi nếu giá tăng mạnh đầu phiên nhưng thanh khoản không xác nhận.
- Cắt lỗ nếu giá đóng cửa thủng hỗ trợ hoặc thủng vùng mua kèm thanh khoản cao.
- Chốt lời từng phần nếu giá tiếp cận kháng cự 20 phiên hoặc RSI vượt vùng nóng.

## 8. Rủi ro cần theo dõi
- Biến động lãi suất, tỷ giá USD/VND, lợi suất trái phiếu Mỹ và giá dầu.
- Tin bất ngờ từ Fed, căng thẳng địa chính trị, hoặc thanh khoản thị trường suy yếu.
- Rủi ro dữ liệu: một số mã có thể thiếu dữ liệu nếu vnstock/yfinance không phản hồi.

## 9. Lời thoại ngắn cho broker nói với khách hàng
Thị trường sáng nay nên tiếp cận thận trọng. Anh/chị có thể giải ngân thăm dò ở các mã giữ nền tốt, nhưng chỉ mua khi giá vượt vùng xác nhận với thanh khoản phù hợp. Không mua đuổi ở nhịp tăng nóng; ưu tiên quản trị rủi ro bằng điểm cắt lỗ rõ ràng.
"""


def _global_market_lines(global_data: dict[str, Any]) -> str:
    if not global_data:
        return "- Chưa có dữ liệu quốc tế."
    return "\n".join(f"- {symbol}: {_technical_sentence(symbol, data)}" for symbol, data in global_data.items())


def _news_lines(news_data: dict[str, Any]) -> str:
    items = news_data.get("items", [])
    if not items:
        return "- Chưa lấy được tin mới; cần kiểm tra thêm trước giờ giao dịch."
    lines = [f"- Nguồn tin: {news_data.get('source', 'RSS')}."]
    for item in items[:8]:
        title = item.get("title", "").strip()
        source = item.get("source", "").strip()
        url = item.get("url", "").strip()
        if title:
            lines.append(f"- {title} ({source}) {url}")
    if news_data.get("note"):
        lines.append(f"- Ghi chú: {news_data['note']}")
    return "\n".join(lines)


def _sector_impact_lines() -> str:
    lines = []
    for sector, themes in SECTOR_THEMES.items():
        joined = ", ".join(themes)
        lines.append(f"- {sector}: theo dõi {joined}; chỉ ưu tiên mã có nền kỹ thuật xác nhận.")
    return "\n".join(lines)


def _stock_watchlist_lines(stocks: dict[str, Any]) -> str:
    if not stocks:
        return "- Chưa có dữ liệu watchlist."
    blocks = []
    for symbol, data in stocks.items():
        sector = data.get("sector", "Khác")
        if not data.get("available"):
            reason = data.get("reason", "Thiếu dữ liệu.")
            blocks.append(
                f"""### {symbol}
- Mã: {symbol}
- Ngành: {sector}
- Lý do theo dõi: nằm trong watchlist, cần cập nhật lại khi có dữ liệu.
- Xu hướng kỹ thuật: Thiếu dữ liệu
- Giá gần nhất: Thiếu dữ liệu
- MA20 / MA50: Thiếu dữ liệu
- RSI: Thiếu dữ liệu
- Hỗ trợ: Thiếu dữ liệu
- Kháng cự: Thiếu dữ liệu
- Thanh khoản: Thiếu dữ liệu
- Có mua được không: Chỉ mua khi dữ liệu được xác nhận lại.
- Điều kiện mua: Chỉ mua khi có giá, thanh khoản và xu hướng rõ ràng.
- Vùng mua tham khảo: Chờ dữ liệu rõ hơn
- Vùng chốt lời: Chờ dữ liệu rõ hơn
- Vùng cắt lỗ: Cắt lỗ nếu dữ liệu sau cập nhật cho thấy giá thủng hỗ trợ.
- Rủi ro: {reason}"""
            )
            continue
        price = data.get("last_price")
        support = data.get("support20")
        resistance = data.get("resistance20")
        buy_zone = _zone(price, support)
        take_profit = _zone(resistance, price)
        stop_loss = _stop_loss(support)
        blocks.append(
            f"""### {symbol}
- Mã: {symbol}
- Ngành: {sector}
- Lý do theo dõi: thuộc nhóm {sector}, cần theo dõi phản ứng với dòng tiền và tin ngành.
- Xu hướng kỹ thuật: {data.get("trend")}
- Giá gần nhất: {price}
- MA20 / MA50: {data.get("ma20")} / {data.get("ma50")}
- RSI: {data.get("rsi14")}
- Hỗ trợ: {support}
- Kháng cự: {resistance}
- Thanh khoản: phiên gần nhất {data.get("volume")}, trung bình 20 phiên {data.get("avg_volume20")}
- Có mua được không: {data.get("trade_status")}
- Điều kiện mua: Chỉ mua khi giá giữ trên hỗ trợ và vượt vùng xác nhận với thanh khoản tốt hơn trung bình.
- Vùng mua tham khảo: {buy_zone}
- Vùng chốt lời: Chốt lời từng phần nếu tiếp cận {take_profit}.
- Vùng cắt lỗ: Cắt lỗ nếu đóng cửa dưới {stop_loss}.
- Rủi ro: Tin ngành xấu, thị trường chung suy yếu hoặc thanh khoản không xác nhận."""
        )
    return "\n\n".join(blocks)


def _technical_sentence(name: str, data: dict[str, Any]) -> str:
    if not data.get("available"):
        return f"{name}: thiếu dữ liệu ({data.get('reason', 'không rõ nguyên nhân')})."
    return (
        f"{name} giá {data.get('last_price')}, xu hướng {data.get('trend')}, "
        f"MA20/MA50 {data.get('ma20')}/{data.get('ma50')}, RSI {data.get('rsi14')}, "
        f"hỗ trợ {data.get('support20')}, kháng cự {data.get('resistance20')}."
    )


def _zone(a: Any, b: Any) -> str:
    if a is None or b is None:
        return "Chờ dữ liệu rõ hơn"
    low = min(float(a), float(b))
    high = max(float(a), float(b))
    return f"{low:.2f} - {high:.2f}"


def _stop_loss(support: Any) -> str:
    if support is None:
        return "vùng hỗ trợ gần nhất"
    return f"{float(support) * 0.97:.2f}"
