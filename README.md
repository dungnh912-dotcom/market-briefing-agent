# HDUNGINVEST Daily Research

Project tạo website bản tin thị trường chứng khoán hằng ngày cho broker tại Việt Nam. Pipeline chạy bằng Python, dùng Gemini API để tổng hợp dữ liệu công khai và dữ liệu nhập tay, render HTML tĩnh vào `bantin/YYYY-MM-DD.html`, cập nhật `index.html`, rồi deploy bằng GitHub Pages.

## Cấu trúc chính

```text
.github/workflows/daily-briefing.yml
assets/css/style.css
assets/qr-zalo.png
assets/logo.png
bantin/.gitkeep
data/manual_market_data.json
data/manual_news.json
data/watchlist.json
scripts/generate_briefing.py
scripts/data_collector.py
scripts/news_collector.py
scripts/gemini_writer.py
scripts/technical_analysis.py
scripts/html_renderer.py
scripts/update_index.py
templates/briefing_template.html
templates/index_template.html
requirements.txt
index.html
```

## Cách hoạt động

1. `scripts/data_collector.py` lấy chỉ số quốc tế, hàng hóa và crypto từ Yahoo Finance nếu truy cập được.
2. Dữ liệu Việt Nam như VN-Index, VN30, HNX, UPCoM, USD/VND, khối ngoại, tự doanh, sector flow được đọc từ `data/manual_market_data.json` để tránh phụ thuộc API không ổn định.
3. `scripts/news_collector.py` đọc RSS/public feeds và trộn thêm tin thủ công từ `data/manual_news.json`.
4. `scripts/technical_analysis.py` tính MA20, MA50, RSI14, MACD, hỗ trợ/kháng cự khi có lịch sử giá; nếu thiếu thì dùng vùng nhập tay trong `data/watchlist.json`.
5. `scripts/gemini_writer.py` gọi Gemini để sinh JSON bản tin. Nếu không có key hoặc API lỗi, script vẫn tạo bản tin fallback và ghi rõ phần thiếu dữ liệu.
6. `scripts/html_renderer.py` render HTML bằng Jinja2, `scripts/update_index.py` cập nhật trang danh sách bản tin.

## Chạy local

```bash
pip install -r requirements.txt
python scripts/generate_briefing.py
```

PowerShell nếu muốn dùng Gemini:

```powershell
$env:GEMINI_API_KEY="your_google_ai_studio_key"
$env:GEMINI_MODEL="gemini-1.5-flash"
python scripts/generate_briefing.py
```

Nếu không có `GEMINI_API_KEY`, project vẫn sinh bản tin fallback để kiểm tra layout.

## Lấy Gemini API key

1. Vào Google AI Studio.
2. Tạo API key mới.
3. Trên GitHub repo, vào `Settings > Secrets and variables > Actions > New repository secret`.
4. Thêm secret `GEMINI_API_KEY`.
5. Nếu muốn đổi model, thêm biến repository `GEMINI_MODEL`, ví dụ `gemini-1.5-flash` hoặc model mới hơn mà tài khoản hỗ trợ.

## GitHub Actions

Workflow nằm tại `.github/workflows/daily-briefing.yml`.

- Chạy tự động mỗi ngày lúc 07:00 giờ Việt Nam.
- Cron dùng UTC: `0 0 * * *`.
- Có `workflow_dispatch` để chạy thủ công.
- Cài dependencies, chạy `python scripts/generate_briefing.py`, commit HTML/JSON mới, sau đó deploy GitHub Pages.

## Bật GitHub Pages

1. Vào `Settings > Pages`.
2. Chọn `GitHub Actions` làm nguồn deploy.
3. Vào tab `Actions`, chọn `HDUNGINVEST Daily Briefing`.
4. Bấm `Run workflow` để tạo bản tin đầu tiên và deploy.

## Đổi brand, màu, hotline, QR

- Brand mặc định: `HDUNGINVEST`.
- Website: `HDUNGINVEST Daily Research`.
- Footer: `HDUNGINVEST · Daily Market Briefing`.
- Hotline placeholder: `098xxxxxxx`.
- QR placeholder: `assets/qr-zalo.png`.

File cần sửa:

- Màu sắc, spacing, layout: `assets/css/style.css`.
- HTML bản tin: `templates/briefing_template.html`.
- HTML index: `templates/index_template.html`.
- Hotline/brand qua env trong workflow: `.github/workflows/daily-briefing.yml`.
- QR thật: thay file `assets/qr-zalo.png`.
- Logo thật: thay file `assets/logo.png`.

## Nhập dữ liệu thủ công

Sửa `data/manual_market_data.json` khi nguồn tự động thiếu:

- `indexes`: VNINDEX, VN30, HNX, UPCOM, USDVND.
- `market_breadth`: số mã tăng/giảm/đứng giá.
- `liquidity`: thanh khoản.
- `foreign_flow`: khối ngoại mua/bán ròng.
- `proprietary_flow`: tự doanh.
- `sector_flow`: dòng tiền theo nhóm ngành.
- `top_gainers`, `top_losers`.
- `watchlist_prices` nếu có giá riêng.

Sửa `data/manual_news.json` để bổ sung link/tin thủ công.

Sửa `data/watchlist.json` để đổi danh sách mã, vùng hỗ trợ/kháng cự, MA20/MA50, vùng mua/chốt lời/cắt lỗ tham khảo và rủi ro. Watchlist mẫu gồm MBB, HDB, SSI, VND, VCI, HPG, HSG, PVS, PVD, GAS, MWG, FRT, FPT, GMD, VNM, PNJ, NLG, KBC, VHM.

## Lưu ý nội dung

Bản tin luôn dùng disclaimer:

> Tài liệu thông tin tổng hợp, KHÔNG phải khuyến nghị giao dịch hay đầu tư.

Prompt Gemini yêu cầu không bịa số liệu, không tạo nguồn giả, không khuyến nghị mua/bán chắc chắn và phải ghi `chưa có dữ liệu cập nhật` khi thiếu dữ liệu.
