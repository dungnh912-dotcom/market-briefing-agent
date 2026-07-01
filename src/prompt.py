from __future__ import annotations

from datetime import date
from typing import Any


REPORT_SECTIONS = [
    "# BẢN TIN THỊ TRƯỜNG NGÀY {date}",
    "## 1. Tóm tắt nhanh",
    "## 2. Thị trường quốc tế",
    "## 3. Tin tức và thị trường Việt Nam",
    "## 4. Tác động theo nhóm ngành",
    "## 5. Danh sách cổ phiếu cần theo dõi",
    "## 6. Phân tích kỹ thuật VN-Index nếu có dữ liệu",
    "## 7. Kế hoạch giao dịch trong ngày",
    "## 8. Rủi ro cần theo dõi",
    "## 9. Lời thoại ngắn cho broker nói với khách hàng",
]


GUARDRAILS = """
Không được đưa khuyến nghị chắc chắn. Chỉ dùng ngôn ngữ điều kiện:
- Có thể mua thăm dò nếu...
- Chỉ mua khi...
- Không mua đuổi nếu...
- Cắt lỗ nếu...
- Chốt lời từng phần nếu...
Không dùng các câu như "nên mua chắc chắn", "đảm bảo", "cam kết lợi nhuận".
""".strip()


def build_prompt(market_data: dict[str, Any], report_date: date) -> str:
    date_text = report_date.strftime("%d/%m/%Y")
    return f"""
Bạn là trợ lý phân tích thị trường cho broker tại Việt Nam. Viết bản tin tiếng Việt, rõ ràng,
thực dụng, không phóng đại, ưu tiên điều kiện giao dịch và quản trị rủi ro.

{GUARDRAILS}

Bắt buộc dùng đúng các mục sau:
{chr(10).join(section.format(date=date_text) for section in REPORT_SECTIONS)}

Với mỗi cổ phiếu cần có: Mã, Ngành, Lý do theo dõi, Xu hướng kỹ thuật, Giá gần nhất,
MA20 / MA50, RSI, Hỗ trợ, Kháng cự, Thanh khoản, Có mua được không, Điều kiện mua,
Vùng mua tham khảo, Vùng chốt lời, Vùng cắt lỗ, Rủi ro.

Dữ liệu đầu vào:
{market_data}
""".strip()


def required_sections_for(date_text: str) -> list[str]:
    return [section.format(date=date_text) for section in REPORT_SECTIONS]
