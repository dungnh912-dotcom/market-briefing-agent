function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stripJsonFence(text) {
  return String(text || "")
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function fallbackBriefing({ marketData, news, watchlist, reason }) {
  const vnIndex = marketData.vietnam?.indices?.find((item) => item.symbol === "VNINDEX");
  const liveGlobal = [
    ...(marketData.global?.indices || []),
    ...(marketData.global?.commodities || []),
    ...(marketData.global?.bonds || []),
    ...(marketData.global?.crypto || [])
  ].filter((item) => item.sourceType === "live").slice(0, 6);

  return {
    title: "VN-Index cần thêm dữ liệu xác nhận, dòng tiền theo dõi nhóm dẫn dắt",
    subtitle: "Bản tin thị trường chứng khoán · Cập nhật 07:00 · Giờ Việt Nam",
    executiveSummary: [
      `Trạng thái dữ liệu: Việt Nam ${marketData.sourceStatus?.vietnam || "fallback"}, quốc tế ${marketData.sourceStatus?.global || "fallback"}, crypto ${marketData.sourceStatus?.crypto || "fallback"}.`,
      vnIndex?.value
        ? `VN-Index ghi nhận ${vnIndex.value}, biến động ${vnIndex.changePct ?? "chưa có"}%.`
        : "Dữ liệu chỉ số Việt Nam chưa đủ dữ liệu xác nhận, cần bổ sung thủ công nếu nguồn live không ổn định.",
      liveGlobal.length
        ? `Quốc tế có dữ liệu live cho: ${liveGlobal.map((item) => item.label).join(", ")}.`
        : "Dữ liệu quốc tế chưa lấy được live trong lần chạy này.",
      "Watchlist được giữ ở dạng điều kiện, không phát sinh khuyến nghị mua/bán chắc chắn.",
      reason ? `Gemini không được dùng trong lần chạy này: ${reason}. Bản tin fallback chỉ tổng hợp dữ liệu đầu vào.` : "Bản tin fallback chỉ tổng hợp dữ liệu đầu vào."
    ],
    marketDashboardNotes: [
      "Các trường có nguồn manual/fallback cần được kiểm tra trước khi sử dụng trong trao đổi với khách hàng.",
      "Không suy luận vùng giá kỹ thuật nếu dữ liệu giá chưa được cập nhật."
    ],
    vietnamPulse: {
      technical: [
        "VN-Index: chưa đủ dữ liệu xác nhận nếu file manual chưa cập nhật vùng điểm.",
        "VN30, HNX-Index, UPCoM: ưu tiên đọc theo dữ liệu manual khi nguồn realtime chưa ổn định."
      ],
      flow: [
        `Thanh khoản: ${marketData.vietnam?.liquidity?.comment || "chưa đủ dữ liệu xác nhận"}.`,
        `Khối ngoại: ${marketData.vietnam?.foreignFlow?.comment || "chưa đủ dữ liệu xác nhận"}.`
      ],
      macro: [
        `USD/VND: ${marketData.vietnam?.fx?.value || "chưa đủ dữ liệu xác nhận"}.`,
        `Lãi suất liên ngân hàng: ${marketData.vietnam?.rates?.interbank?.comment || "chưa đủ dữ liệu xác nhận"}.`
      ]
    },
    internationalPulse: {
      usEurope: liveGlobal.filter((item) => ["S&P 500", "Nasdaq", "Dow Jones", "DAX"].includes(item.label)).map((item) => `${item.label}: ${item.value ?? "chưa có dữ liệu"}`),
      asia: liveGlobal.filter((item) => ["Nikkei 225", "Hang Seng", "Shanghai Composite", "KOSPI"].includes(item.label)).map((item) => `${item.label}: ${item.value ?? "chưa có dữ liệu"}`),
      commoditiesCrypto: liveGlobal.filter((item) => ["Vàng thế giới", "Dầu WTI", "Dầu Brent", "Bitcoin", "Ethereum"].includes(item.label)).map((item) => `${item.label}: ${item.value ?? "chưa có dữ liệu"}`)
    },
    sectorImpact: [
      { sector: "Ngân hàng", impact: "Trung tính", reason: "Chưa đủ dữ liệu xác nhận về dòng tiền ngành.", tickers: "VCB, BID, CTG, MBB, TCB, VPB", confirmation: "Thanh khoản nhóm vượt trung bình và VN30 đồng thuận." },
      { sector: "Chứng khoán", impact: "Trung tính", reason: "Phụ thuộc thanh khoản toàn thị trường.", tickers: "SSI, VND, HCM", confirmation: "Giá trị khớp lệnh tăng bền." },
      { sector: "Dầu khí", impact: "Trung tính", reason: "Theo dõi biến động dầu Brent/WTI.", tickers: "GAS, PVD, PVS", confirmation: "Giá dầu duy trì tích cực và nhóm có thanh khoản." },
      { sector: "Bất động sản", impact: "Trung tính", reason: "Cần thêm dữ liệu về pháp lý và lãi suất.", tickers: "VHM, VIC, VRE, KBC, NLG", confirmation: "Tin hỗ trợ đi cùng dòng tiền lan tỏa." },
      { sector: "Thép", impact: "Trung tính", reason: "Cần thêm dữ liệu nhu cầu và giá nguyên liệu.", tickers: "HPG", confirmation: "Giá giữ nền và ngành vật liệu cải thiện." }
    ],
    watchlist: safeArray(watchlist).map((item) => ({
      symbol: item.symbol,
      sector: item.sector,
      thesis: item.thesis,
      observationZone: `Hỗ trợ ${item.support}; kháng cự ${item.resistance}`,
      entryRule: item.entryRule,
      takeProfit: item.takeProfit,
      stopLoss: item.stopLoss,
      trigger: item.entryRule,
      risk: item.risk
    })),
    technicalView: [
      { label: "Xu hướng ngắn hạn", value: "Chưa đủ dữ liệu xác nhận nếu chưa cập nhật dữ liệu kỹ thuật VN-Index." },
      { label: "Hỗ trợ gần", value: "cần cập nhật thủ công" },
      { label: "Kháng cự gần", value: "cần cập nhật thủ công" },
      { label: "MA20/MA50", value: "chưa đủ dữ liệu xác nhận" },
      { label: "RSI/MACD", value: "chưa đủ dữ liệu xác nhận" },
      { label: "Thanh khoản", value: marketData.vietnam?.liquidity?.comment || "chưa đủ dữ liệu xác nhận" },
      { label: "Kịch bản vượt cản", value: "Chỉ xác nhận nếu vượt kháng cự với thanh khoản cải thiện." },
      { label: "Kịch bản mất hỗ trợ", value: "Giảm tỷ trọng quan sát nếu VN-Index mất hỗ trợ chính với độ rộng xấu." }
    ],
    scenarios: [
      { name: "Tích cực", condition: "VN-Index vượt kháng cự với thanh khoản cao.", vnIndexRange: "cần cập nhật thủ công", preferredSectors: "Ngân hàng, chứng khoán, dầu khí", brokerAction: "Theo dõi cổ phiếu vượt nền có điều kiện.", risk: "Bứt phá thiếu thanh khoản." },
      { name: "Trung tính", condition: "Chỉ số đi ngang trong biên hỗ trợ/kháng cự.", vnIndexRange: "cần cập nhật thủ công", preferredSectors: "Cổ phiếu nền chặt, thanh khoản tốt", brokerAction: "Không mua đuổi, ưu tiên quản trị vị thế.", risk: "Phân hóa mạnh." },
      { name: "Tiêu cực", condition: "VN-Index thủng hỗ trợ và độ rộng xấu.", vnIndexRange: "cần cập nhật thủ công", preferredSectors: "Tiền mặt, phòng thủ", brokerAction: "Giảm đòn bẩy, chờ tín hiệu cân bằng.", risk: "Bán ròng lan rộng." }
    ],
    events: safeArray(news).slice(0, 8).map((item) => ({
      group: item.tags?.join(", ") || item.source || "Tin tức",
      detail: `${item.title}${item.summary ? ` - ${item.summary}` : ""}`
    })),
    sources: [
      { group: "Dữ liệu thị trường Việt Nam", items: ["data/manual_market_data.json", "Yahoo Finance adapter cho một số mã nếu khả dụng"] },
      { group: "Dữ liệu quốc tế", items: ["Yahoo Finance"] },
      { group: "Tin tức vĩ mô", items: ["Google News RSS", "data/manual_news.json"] },
      { group: "Tin doanh nghiệp", items: ["data/manual_news.json"] },
      { group: "Dữ liệu kỹ thuật", items: ["data/watchlist.json", "manual technical levels"] }
    ],
    disclaimer: "Bản tin chỉ nhằm mục đích cung cấp thông tin, không phải khuyến nghị giao dịch hay tư vấn đầu tư cá nhân. Nhà đầu tư cần tự chịu trách nhiệm với quyết định của mình."
  };
}

async function callGemini({ prompt, marketData, news, watchlist, retries = 2 }) {
  const apiKey = process.env.GEMINI_API_KEY;
  const model = process.env.GEMINI_MODEL || "gemini-1.5-flash";

  if (!apiKey) {
    return {
      mode: "fallback",
      error: "Thiếu GEMINI_API_KEY. Hãy thêm key vào .env hoặc GitHub Secrets.",
      briefing: fallbackBriefing({ marketData, news, watchlist, reason: "thiếu GEMINI_API_KEY" })
    };
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(apiKey)}`;
  let lastError;

  for (let attempt = 1; attempt <= retries + 1; attempt += 1) {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig: {
            temperature: 0.35,
            topP: 0.9,
            responseMimeType: "application/json"
          }
        })
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(`Gemini HTTP ${response.status}: ${body.slice(0, 240)}`);
      }

      const payload = await response.json();
      const text = payload?.candidates?.[0]?.content?.parts?.map((part) => part.text || "").join("") || "";
      const briefing = JSON.parse(stripJsonFence(text));
      return { mode: "gemini", model, briefing };
    } catch (error) {
      lastError = error;
      if (attempt <= retries) {
        await sleep(1000 * attempt);
      }
    }
  }

  return {
    mode: "fallback",
    model,
    error: lastError?.message || "Gemini API lỗi không xác định.",
    briefing: fallbackBriefing({ marketData, news, watchlist, reason: lastError?.message || "Gemini API lỗi" })
  };
}

module.exports = { callGemini, fallbackBriefing };
