# HDUNGINVEST Daily Research

Website tĩnh tạo bản tin thị trường chứng khoán hằng ngày cho broker/chuyên viên tư vấn tại Việt Nam. Project dùng Python để thu thập dữ liệu, gọi Gemini nếu có API key, render HTML vào `bantin/YYYY-MM-DD.html`, cập nhật `index.html` và deploy bằng GitHub Pages.

## Cách hoạt động

1. `scripts/data_collector.py` lấy chỉ số quốc tế, hàng hóa, Bitcoin và USD/VND từ Google Finance nếu truy cập được.
2. Dữ liệu Việt Nam ưu tiên `data/manual_market_data.json`: VN-Index, VN30, HNX-Index, UPCoM, thanh khoản HOSE, khối ngoại, tự doanh, USD/VND, lãi suất liên ngân hàng.
3. `scripts/news_collector.py` đọc RSS/public feeds và trộn tin thủ công từ `data/manual_news.json`.
4. `scripts/gemini_writer.py` gửi prompt cho Gemini theo phong cách broker thực chiến, tập trung dòng tiền, thanh khoản, margin, khối ngoại và rủi ro phân phối. Nếu Gemini lỗi hoặc thiếu key, hệ thống vẫn sinh fallback và ghi rõ `chưa có dữ liệu cập nhật`.
5. `scripts/text_postprocessor.py` chuẩn hóa lỗi gõ tiếng Việt, tên riêng, dấu câu và các cụm nhạy cảm trước khi render.
6. `templates/briefing_template.html` và `assets/css/style.css` tạo giao diện báo cáo research cao cấp.

## Chạy local

```bash
pip install -r requirements.txt
python scripts/generate_briefing.py
python -m http.server 8000
```

Mở trình duyệt tại `http://localhost:8000`.

Nếu muốn dùng Gemini khi chạy local:

```powershell
$env:GEMINI_API_KEY="your_google_ai_studio_key"
$env:GEMINI_MODEL="gemini-1.5-flash"
python scripts/generate_briefing.py
```

## Thay QR Zalo

Lưu ảnh QR thật vào:

```text
assets/qr-zalo.png
```

Ảnh sẽ được dùng trong CTA cuối bản tin. CSS đã đặt `object-fit: contain` để QR không bị méo.

## Thay hotline và brand

Sửa file:

```text
data/config.json
```

Ví dụ:

```json
{
  "brand": "HDUNGINVEST",
  "site_name": "HDUNGINVEST Daily Research",
  "footer": "HDUNGINVEST",
  "hotline": "0387337164",
  "qr_path": "assets/qr-zalo.png",
  "logo_path": "assets/logo.png"
}
```

Trên GitHub Actions cũng có thể override bằng biến môi trường trong `.github/workflows/daily-briefing.yml`.

## Nhập dữ liệu thủ công

Sửa:

```text
data/manual_market_data.json
```

Các nhóm chính:

- `indexes`: VNINDEX, VN30, HNX, UPCOM, USDVND.
- `liquidity`: thanh khoản HOSE.
- `foreign_flow`: khối ngoại mua/bán ròng.
- `proprietary_flow`: tự doanh.
- `interbank_rate`: lãi suất liên ngân hàng nếu có.
- `market_breadth`: số mã tăng/giảm/đứng giá.
- `sector_flow`: dòng tiền theo nhóm ngành.

Nếu thiếu dữ liệu, để `value` là `null`; bản tin sẽ ghi `chưa có dữ liệu cập nhật`.

Tin thủ công nằm tại:

```text
data/manual_news.json
```

Watchlist và vùng kỹ thuật nằm tại:

```text
data/watchlist.json
```

## Gemini API Key trên GitHub

1. Tạo API key từ Google AI Studio.
2. Vào repo GitHub: `Settings > Secrets and variables > Actions`.
3. Chọn `New repository secret`.
4. Thêm một trong hai secret:

```text
GEMINI_API_KEY
GOOGLE_API_KEY
```

Tuỳ chọn model bằng repository variable:

```text
GEMINI_MODEL=gemini-1.5-flash
```

## Chạy GitHub Actions thủ công

1. Vào tab `Actions`.
2. Chọn workflow `HDUNGINVEST Daily Briefing`.
3. Bấm `Run workflow`.

Workflow chạy hằng ngày lúc 07:00 giờ Việt Nam, tương ứng cron UTC:

```yaml
- cron: "0 0 * * *"
```

## Bật GitHub Pages

1. Vào `Settings > Pages`.
2. Chọn source `GitHub Actions`.
3. Chạy workflow thủ công lần đầu để tạo artifact và deploy.

## File quan trọng

```text
.github/workflows/daily-briefing.yml
assets/css/style.css
assets/qr-zalo.png
data/config.json
data/manual_market_data.json
data/manual_news.json
data/watchlist.json
scripts/generate_briefing.py
scripts/data_collector.py
scripts/news_collector.py
scripts/gemini_writer.py
scripts/text_postprocessor.py
templates/briefing_template.html
templates/index_template.html
```

Project chỉ giữ một workflow chính và một entrypoint chính:

- `.github/workflows/daily-briefing.yml`
- `scripts/generate_briefing.py`

## Disclaimer

Tài liệu thông tin tổng hợp, KHÔNG phải khuyến nghị giao dịch hay đầu tư. Nhà đầu tư cần tự chịu trách nhiệm với quyết định của mình.
