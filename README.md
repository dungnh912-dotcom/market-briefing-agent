# market-briefing-agent

AI agent tạo bản tin thị trường chứng khoán quốc tế và Việt Nam mỗi sáng lúc 7:00 giờ Việt Nam bằng GitHub Actions.

## Tính năng

- Lấy dữ liệu quốc tế: SPY, QQQ, DIA, GLD, USO, TLT, BTC-USD.
- Theo dõi watchlist Việt Nam gồm ngân hàng, chứng khoán, bất động sản, thép, dầu khí, bán lẻ, công nghệ, logistics, thủy sản, dệt may và đầu tư công.
- Tin tức dùng NewsAPI nếu có `NEWSAPI_KEY`; nếu không có key hoặc lỗi thì fallback sang RSS miễn phí.
- Dữ liệu Việt Nam ưu tiên `vnstock`; nếu lỗi thì fallback sang yfinance với hậu tố `.VN`, và ghi rõ mã thiếu dữ liệu.
- Tính MA20, MA50, RSI14, khối lượng trung bình 20 phiên, hỗ trợ 20 phiên, kháng cự 20 phiên, xu hướng và trạng thái giao dịch.
- Sinh báo cáo tiếng Việt theo cấu trúc 9 mục, lưu tại `reports/YYYY-MM-DD-market-briefing.md`.
- Lưu dữ liệu thô tại `data/YYYY-MM-DD-market-data.json`.

## Cấu trúc

```text
.github/workflows/daily_market_briefing.yml
src/
reports/
data/
tests/
```

## Cài đặt local

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

Các biến môi trường tùy chọn:

- `NEWSAPI_KEY`: dùng NewsAPI cho tin tức.
- `OPENAI_API_KEY`: dùng OpenAI-compatible LLM để viết bản tin tự nhiên hơn.
- `OPENAI_MODEL`: mặc định `gpt-4o-mini`.
- `GITHUB_TOKEN`: GitHub Actions tự cấp token này.
- `GITHUB_MODEL`: mặc định `openai/gpt-4.1-mini` cho GitHub Models.
- `LOOKBACK_DAYS`: số ngày dữ liệu lịch sử, mặc định `180`.

Nếu không có LLM key, project vẫn chạy và tạo bản tin bằng deterministic fallback writer.

## GitHub Actions

Workflow `.github/workflows/daily_market_briefing.yml` chạy:

- Thứ 2 đến thứ 6 lúc 7:00 sáng giờ Việt Nam.
- Cron: `0 0 * * 1-5` vì GitHub Actions dùng UTC.
- Có `workflow_dispatch` để chạy thủ công.
- Dùng Python 3.11.
- Có quyền `contents: write` để commit báo cáo và `models: read` để dùng GitHub Models.

Workflow sẽ chạy `python src/main.py`, sau đó commit file mới trong `reports/` và `data/`.

## Kiểm thử

```bash
pytest
```

## Lưu ý giao dịch

Bản tin không đưa khuyến nghị chắc chắn. Ngôn ngữ mặc định luôn ở dạng điều kiện như:

- Có thể mua thăm dò nếu...
- Chỉ mua khi...
- Không mua đuổi nếu...
- Cắt lỗ nếu...
- Chốt lời từng phần nếu...

Người dùng cần tự kiểm chứng dữ liệu, trạng thái thị trường và khẩu vị rủi ro trước khi ra quyết định.
