function compactJson(value) {
  return JSON.stringify(value, null, 2);
}

function buildPrompt({ marketData, news, watchlist, brand = "HDINVEST" }) {
  return `
Bạn là bộ phận research của ${brand}, viết bản tin thị trường chứng khoán hằng ngày cho broker tại Việt Nam.

Yêu cầu bắt buộc:
- Viết tiếng Việt chuẩn, giọng broker chuyên nghiệp, ngắn gọn nhưng đủ ý.
- Không hô hào, không dùng các cụm "mua ngay", "chắc chắn tăng", "cam kết".
- Không khuyến nghị mua/bán chắc chắn. Watchlist chỉ được viết theo điều kiện.
- Mỗi nhận định phải dựa trên dữ liệu đầu vào. Nếu thiếu dữ liệu, ghi "chưa đủ dữ liệu xác nhận".
- Phân biệt rõ dữ liệu thực tế, kỳ vọng thị trường và suy luận của broker.
- Các vùng giá watchlist chỉ là tham khảo kỹ thuật, không phải tư vấn đầu tư cá nhân.
- Không thêm thông tin liên hệ, mã quét, kênh chat hay số điện thoại.

Trả về DUY NHẤT một JSON object hợp lệ, không bọc markdown, theo schema:
{
  "title": "Tiêu đề nổi bật",
  "subtitle": "Bản tin thị trường chứng khoán · Cập nhật 07:00 · Giờ Việt Nam",
  "executiveSummary": ["5-7 ý chính"],
  "marketDashboardNotes": ["ghi chú ngắn về dashboard"],
  "vietnamPulse": {
    "technical": ["chỉ số & kỹ thuật"],
    "flow": ["dòng tiền & khối ngoại"],
    "macro": ["tỷ giá, lãi suất, vĩ mô"]
  },
  "internationalPulse": {
    "usEurope": ["Mỹ & châu Âu"],
    "asia": ["châu Á"],
    "commoditiesCrypto": ["hàng hóa & crypto"]
  },
  "sectorImpact": [
    {
      "sector": "Ngành",
      "impact": "Hưởng lợi/Trung tính/Bất lợi",
      "reason": "Lý do",
      "tickers": "Mã cần theo dõi",
      "confirmation": "Điều kiện xác nhận"
    }
  ],
  "watchlist": [
    {
      "symbol": "Mã",
      "sector": "Ngành",
      "thesis": "Luận điểm theo dõi",
      "observationZone": "Vùng quan sát",
      "entryRule": "Điểm mua tham khảo dạng điều kiện",
      "takeProfit": "Vùng chốt lời tham khảo",
      "stopLoss": "Cắt lỗ tham khảo",
      "trigger": "Điều kiện kích hoạt",
      "risk": "Rủi ro chính"
    }
  ],
  "technicalView": [
    {"label": "Xu hướng ngắn hạn", "value": "nội dung"},
    {"label": "Hỗ trợ gần", "value": "nội dung"},
    {"label": "Kháng cự gần", "value": "nội dung"},
    {"label": "MA20/MA50", "value": "nội dung"},
    {"label": "RSI/MACD", "value": "nội dung"},
    {"label": "Thanh khoản", "value": "nội dung"},
    {"label": "Kịch bản vượt cản", "value": "nội dung"},
    {"label": "Kịch bản mất hỗ trợ", "value": "nội dung"}
  ],
  "scenarios": [
    {
      "name": "Tích cực/Trung tính/Tiêu cực",
      "condition": "Điều kiện xảy ra",
      "vnIndexRange": "Vùng điểm VN-Index",
      "preferredSectors": "Nhóm ngành ưu tiên",
      "brokerAction": "Hành động phù hợp cho broker",
      "risk": "Rủi ro cần cảnh giác"
    }
  ],
  "events": [
    {"group": "Việt Nam trong ngày/Việt Nam trong tuần/Quốc tế/KQKD/ETF", "detail": "nội dung"}
  ],
  "sources": [
    {"group": "Dữ liệu thị trường Việt Nam", "items": ["nguồn"]},
    {"group": "Dữ liệu quốc tế", "items": ["nguồn"]},
    {"group": "Tin tức vĩ mô", "items": ["nguồn"]},
    {"group": "Tin doanh nghiệp", "items": ["nguồn"]},
    {"group": "Dữ liệu kỹ thuật", "items": ["nguồn"]}
  ],
  "disclaimer": "Bản tin chỉ nhằm mục đích cung cấp thông tin, không phải khuyến nghị giao dịch hay tư vấn đầu tư cá nhân. Nhà đầu tư cần tự chịu trách nhiệm với quyết định của mình."
}

Dữ liệu thị trường đầu vào:
${compactJson(marketData)}

Tin tức đầu vào:
${compactJson(news)}

Watchlist đầu vào:
${compactJson(watchlist)}
`.trim();
}

module.exports = { buildPrompt };
