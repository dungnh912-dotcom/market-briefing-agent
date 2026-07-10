# HDINVEST Daily Market Briefing

Project tạo bản tin thị trường chứng khoán hằng ngày cho broker tại Việt Nam. Hệ thống lấy dữ liệu public/fallback, gọi Gemini để viết bản tin theo format HDINVEST, render HTML vào `bantin/YYYY-MM-DD.html`, cập nhật `index.html`, và có thể chạy tự động bằng GitHub Actions lúc 07:00 giờ Việt Nam.

Tagline: **Dữ liệu là nền tảng, kỷ luật là lợi thế.**

## Cài đặt local

Yêu cầu Node.js 18 trở lên.

```bash
npm install
```

Tạo file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Điền key Google AI Studio:

```text
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-1.5-flash
TIMEZONE=Asia/Ho_Chi_Minh
REPORT_BRAND=HDINVEST
```

Không đưa API key thật vào repo.

## Kiểm tra cấu hình

```bash
npm run check
```

Lệnh này kiểm tra Node version, `GEMINI_API_KEY`, `data/manual_market_data.json`, `data/manual_news.json`, `data/watchlist.json` và preview đã duyệt. Nếu thiếu key, lệnh sẽ báo lỗi rõ ràng.

## Tạo bản tin realtime local

```bash
npm run generate
```

Lệnh trên sẽ:

1. Load `.env`.
2. Lấy dữ liệu thị trường từ Yahoo Finance/CoinGecko nếu truy cập được.
3. Đọc fallback Việt Nam từ `data/manual_market_data.json`.
4. Lấy tin từ Google News RSS nếu truy cập được và trộn với `data/manual_news.json`.
5. Đọc watchlist từ `data/watchlist.json`.
6. Gọi Gemini bằng `GEMINI_API_KEY`.
7. Nếu thiếu key hoặc Gemini lỗi, tạo bản tin `data-only summary` thay vì dừng toàn bộ pipeline.
8. Render HTML vào `bantin/YYYY-MM-DD.html`.
9. Cập nhật `index.html`.
10. Lưu dữ liệu chuẩn hóa vào `data/cache/latest-market-data.json`.

## Nguồn dữ liệu

Live khi truy cập được:

- Yahoo Finance: S&P 500, Nasdaq, Dow Jones, Nikkei 225, Hang Seng, Shanghai Composite, KOSPI, DAX, vàng, dầu WTI/Brent, bạc, DXY, USD/VND, US 10Y Yield, một số mã Việt Nam nếu Yahoo hỗ trợ.
- CoinGecko: Bitcoin, Ethereum.
- Google News RSS: tin Việt Nam, vĩ mô, Fed/CPI/PMI/dầu/Trung Quốc.

Fallback/manual:

- `data/manual_market_data.json`: VN-Index, VN30, HNX-Index, UPCoM, thanh khoản, độ rộng, khối ngoại, tỷ giá, lãi suất liên ngân hàng, dòng tiền ngành.
- `data/manual_news.json`: tin quan trọng có thể tự nhập mỗi sáng.
- `data/watchlist.json`: mã, ngành, luận điểm, hỗ trợ, kháng cự, điểm mua tham khảo, chốt lời, cắt lỗ, rủi ro.

Trong bản tin, dữ liệu live/fallback/manual được phản ánh qua trạng thái nguồn để broker biết phần nào cần kiểm tra thêm.

## Watchlist

Watchlist chỉ viết theo điều kiện, ví dụ:

- Chỉ xem xét khi giữ trên hỗ trợ và thanh khoản cải thiện.
- Chỉ theo dõi nếu breakout có thanh khoản.
- Không dùng ngôn ngữ khuyến nghị chắc chắn như “mua ngay” hoặc “cam kết”.

Nếu thiếu dữ liệu giá, điền `cần cập nhật thủ công` trong `data/watchlist.json`. AI không được tự bịa vùng kỹ thuật.

## Preview

Giao diện preview đã duyệt nằm tại:

```text
preview/index.html
```

Pipeline realtime dùng lại CSS từ `preview/styles.css`.

## GitHub Secret

Thêm Gemini key:

1. Vào repo GitHub.
2. Chọn `Settings > Secrets and variables > Actions`.
3. Chọn `New repository secret`.
4. Tạo secret:

```text
GEMINI_API_KEY
```

Có thể tùy chọn repository variable:

```text
GEMINI_MODEL=gemini-1.5-flash
```

## GitHub Actions

Workflow nằm tại:

```text
.github/workflows/daily-briefing.yml
```

Workflow chạy tự động mỗi ngày lúc 07:00 giờ Việt Nam, tương ứng:

```yaml
- cron: "0 0 * * *"
```

Chạy thủ công:

1. Vào tab `Actions`.
2. Chọn workflow `HDINVEST Daily Briefing`.
3. Bấm `Run workflow`.

Workflow sẽ chạy `npm install`, `npm run generate`, commit `bantin/YYYY-MM-DD.html`, `index.html`, `data/cache/latest-market-data.json`, sau đó deploy GitHub Pages bằng Pages Actions.

## Bật GitHub Pages

1. Vào `Settings > Pages`.
2. Chọn source `GitHub Actions`.
3. Chạy workflow thủ công lần đầu để tạo bản tin và deploy.

## File quan trọng

```text
scripts/generate-daily-briefing.js
scripts/check-config.js
src/data/fetchMarketData.js
src/data/fetchNews.js
src/ai/buildPrompt.js
src/ai/geminiClient.js
src/render/renderHtml.js
src/render/updateIndex.js
data/manual_market_data.json
data/manual_news.json
data/watchlist.json
data/cache/latest-market-data.json
preview/index.html
preview/styles.css
.github/workflows/daily-briefing.yml
```

## Disclaimer

Bản tin chỉ nhằm mục đích cung cấp thông tin, không phải khuyến nghị giao dịch hay tư vấn đầu tư cá nhân. Nhà đầu tư cần tự chịu trách nhiệm với quyết định của mình.
