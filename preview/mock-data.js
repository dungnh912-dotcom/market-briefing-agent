const marketData = [
  { name: "VN-Index", value: "1.281,4", change: "+0,32%", trend: "up", label: "Tăng", note: "Giữ trên hỗ trợ 1.270-1.275 điểm" },
  { name: "VN30", value: "1.318,6", change: "+0,18%", trend: "up", label: "Tăng", note: "Cần thêm đồng thuận từ nhóm vốn hóa lớn" },
  { name: "HNX-Index", value: "242,9", change: "-0,11%", trend: "down", label: "Giảm", note: "Thanh khoản còn mỏng, phân hóa cao" },
  { name: "USD/VND", value: "25.455", change: "+0,08%", trend: "down", label: "Áp lực", note: "Áp lực tỷ giá cần theo dõi trong tuần" },
  { name: "S&P 500", value: "5.624", change: "+0,41%", trend: "up", label: "Tăng", note: "Tâm lý quốc tế hỗ trợ nhóm rủi ro" },
  { name: "Nasdaq", value: "18.742", change: "+0,67%", trend: "up", label: "Tăng", note: "Công nghệ tiếp tục dẫn dắt" },
  { name: "Dow Jones", value: "40.182", change: "-0,05%", trend: "flat", label: "Trung tính", note: "Nhóm chu kỳ đi ngang" },
  { name: "Nikkei 225", value: "41.230", change: "+0,53%", trend: "up", label: "Tăng", note: "Yen yếu hỗ trợ xuất khẩu" },
  { name: "Vàng thế giới", value: "2.382 USD", change: "+0,24%", trend: "up", label: "Tăng", note: "Nhu cầu phòng vệ duy trì" },
  { name: "Dầu Brent", value: "86,4 USD", change: "+1,12%", trend: "up", label: "Tăng", note: "Tích cực cho nhóm dầu khí" },
  { name: "Bitcoin", value: "64.800 USD", change: "-0,36%", trend: "down", label: "Giảm", note: "Biến động hẹp sau nhịp tăng" },
  { name: "US 10Y Yield", value: "4,28%", change: "+3 bps", trend: "down", label: "Áp lực", note: "Lợi suất tăng gây áp lực định giá" }
];

const sectors = [
  ["Ngân hàng", "Hưởng lợi", "Dòng tiền phòng thủ quay lại nhóm vốn hóa lớn, biên lãi ròng ổn định hơn.", "VCB, BID, CTG, MBB, ACB", "VN30 đồng thuận và thanh khoản ngân hàng vượt trung bình 20 phiên"],
  ["Chứng khoán", "Trung tính", "Kỳ vọng thanh khoản cải thiện nhưng độ rộng thị trường chưa đủ mạnh.", "SSI, VND, HCM, VCI", "Giá trị khớp lệnh toàn thị trường vượt 20.000 tỷ đồng"],
  ["Bất động sản", "Bất lợi", "Áp lực lãi vay và pháp lý khiến dòng tiền chọn lọc, chưa tạo xu hướng ngành.", "VHM, KDH, NLG, DXG", "Tín hiệu hồi phục bán hàng và trái phiếu rõ hơn"],
  ["Thép", "Trung tính", "Giá thép ổn định nhưng nhu cầu nội địa chưa bứt phá.", "HPG, HSG, NKG", "Sản lượng bán hàng và biên lợi nhuận cải thiện"],
  ["Dầu khí", "Hưởng lợi", "Giá dầu tăng và kỳ vọng dự án mới hỗ trợ câu chuyện lợi nhuận.", "GAS, PVD, PVS, BSR", "Brent giữ trên 84 USD và nhóm duy trì thanh khoản cao"],
  ["Bán lẻ", "Trung tính", "Tiêu dùng hồi phục chậm, chỉ phù hợp với mã có kết quả kinh doanh xác nhận.", "MWG, FRT, DGW", "Doanh thu cùng cửa hàng tăng trở lại"],
  ["Xuất khẩu", "Trung tính", "Đơn hàng cải thiện nhưng tỷ giá và chi phí logistics tạo phân hóa.", "VHC, ANV, TNG, GMD", "PMI và đơn hàng quý tới phục hồi bền"],
  ["Công nghệ", "Hưởng lợi", "Tâm lý khu vực hỗ trợ nhờ Nasdaq và nhu cầu chuyển đổi số.", "FPT, CMG", "FPT giữ xu hướng và khối ngoại giảm bán"],
  ["Điện", "Trung tính", "Tính phòng thủ tốt, nhưng thiếu chất xúc tác tăng trưởng ngắn hạn.", "POW, NT2, REE, PC1", "Sản lượng huy động và giá điện cạnh tranh cải thiện"],
  ["Đầu tư công", "Hưởng lợi", "Giải ngân hạ tầng là câu chuyện xuyên suốt, phù hợp khi thị trường cần nhóm dẫn dắt nội địa.", "HHV, CII, VCG, LCG", "Tin giải ngân và backlog chuyển thành doanh thu"]
];

const watchlist = [
  {
    code: "MBB",
    thesis: "Ngân hàng có dòng tiền, nền giá tích lũy chặt và định giá còn hợp lý.",
    zone: "22,8-23,4",
    entry: "Chỉ xem xét khi giữ trên hỗ trợ và thanh khoản cải thiện.",
    target: "24,8-25,5",
    stop: "Thủng 22,4 với thanh khoản tăng.",
    trigger: "VN-Index giữ 1.270 điểm, nhóm ngân hàng lan tỏa.",
    risk: "Khối ngoại bán ròng mạnh hoặc VN30 suy yếu."
  },
  {
    code: "PVS",
    thesis: "Dầu khí hút tiền nhờ giá dầu và câu chuyện dự án trung hạn.",
    zone: "38,5-39,5",
    entry: "Ưu tiên nhịp kiểm định lại nền sau phiên tăng mạnh.",
    target: "42,0-43,5",
    stop: "Mất vùng 37,8.",
    trigger: "Brent duy trì trên 84 USD, thanh khoản ngành vượt trung bình.",
    risk: "Giá dầu đảo chiều hoặc dòng tiền đầu cơ rút nhanh."
  },
  {
    code: "FPT",
    thesis: "Công nghệ giữ xu hướng dài hạn, hưởng lợi từ tâm lý Nasdaq.",
    zone: "118-121",
    entry: "Chỉ giải ngân khi giá giữ MA20 và khối lượng không đột biến bán.",
    target: "126-130",
    stop: "Đóng cửa dưới 116.",
    trigger: "Nasdaq tích cực và khối ngoại giảm áp lực bán.",
    risk: "Định giá cao khiến cổ phiếu nhạy với lãi suất Mỹ."
  }
];

const scenarios = [
  {
    name: "Tích cực",
    items: [
      "Điều kiện: VN-Index vượt 1.300 điểm với thanh khoản tăng và VN30 đồng thuận.",
      "Vùng điểm: 1.300-1.325.",
      "Nhóm ưu tiên: ngân hàng, dầu khí, chứng khoán, công nghệ.",
      "Hành động broker: nâng tỷ trọng có chọn lọc, ưu tiên cổ phiếu vượt nền có dòng tiền.",
      "Rủi ro: vượt cản thiếu thanh khoản dễ tạo bẫy tăng ngắn hạn."
    ]
  },
  {
    name: "Trung tính",
    items: [
      "Điều kiện: chỉ số dao động trong 1.270-1.300 điểm, thanh khoản trung bình.",
      "Vùng điểm: 1.270-1.300.",
      "Nhóm ưu tiên: cổ phiếu nền chặt, kết quả kinh doanh rõ, beta vừa phải.",
      "Hành động broker: giao dịch theo điều kiện, hạn chế mua đuổi.",
      "Rủi ro: phân hóa mạnh khiến danh mục dễ lệch pha chỉ số."
    ]
  },
  {
    name: "Tiêu cực",
    items: [
      "Điều kiện: VN-Index mất 1.270 điểm, khối ngoại bán ròng và tỷ giá tăng nhanh.",
      "Vùng điểm: 1.250-1.255, sâu hơn là 1.230.",
      "Nhóm ưu tiên: phòng thủ, tiền mặt, cổ phiếu có thanh khoản cao.",
      "Hành động broker: giảm đòn bẩy, ưu tiên quản trị rủi ro.",
      "Rủi ro: lực bán lan rộng sang nhóm dẫn dắt."
    ]
  }
];

const events = [
  ["Việt Nam trong ngày", "Theo dõi giao dịch khối ngoại, diễn biến tỷ giá trung tâm và thanh khoản liên ngân hàng."],
  ["Việt Nam trong tuần", "Cập nhật số liệu CPI, tín dụng, tiến độ giải ngân đầu tư công và lịch công bố KQKD quý."],
  ["Quốc tế", "CPI Mỹ, PPI, phát biểu của Fed, PMI sản xuất, dữ liệu việc làm và tồn kho dầu thô."],
  ["ETF & cơ cấu chỉ số", "Theo dõi lịch review ETF nội, hoạt động cơ cấu VN30/VNDiamond nếu có thông báo mới."]
];

const sources = [
  ["Dữ liệu thị trường Việt Nam", ["HOSE placeholder", "HNX placeholder", "Vietstock placeholder"]],
  ["Dữ liệu quốc tế", ["Yahoo Finance placeholder", "Investing.com placeholder", "TradingView placeholder"]],
  ["Tin tức vĩ mô", ["Tổng cục Thống kê placeholder", "SBV placeholder", "FRED placeholder"]],
  ["Tin doanh nghiệp", ["HOSE disclosures placeholder", "HNX disclosures placeholder"]],
  ["Dữ liệu kỹ thuật", ["OHLCV provider placeholder", "Internal indicator engine placeholder"]]
];

const impactClass = {
  "Hưởng lợi": "positive",
  "Bất lợi": "negative",
  "Trung tính": "neutral"
};

function renderMarketDashboard() {
  const dashboard = document.querySelector("#marketDashboard");
  dashboard.innerHTML = marketData.map((item) => `
    <article class="metric-card">
      <header>
        <h3>${item.name}</h3>
        <span class="badge ${item.trend}">${item.label}</span>
      </header>
      <div>
        <p class="metric-value">${item.value}</p>
        <span class="badge ${item.trend}">${item.change}</span>
        <p class="metric-note">${item.note}</p>
      </div>
    </article>
  `).join("");
}

function renderSectorTable() {
  const body = document.querySelector("#sectorTable tbody");
  body.innerHTML = sectors.map(([name, impact, reason, tickers, confirm]) => `
    <tr>
      <td><strong>${name}</strong></td>
      <td><span class="impact ${impactClass[impact]}">${impact}</span></td>
      <td>${reason}</td>
      <td>${tickers}</td>
      <td>${confirm}</td>
    </tr>
  `).join("");
}

function renderWatchlist() {
  const grid = document.querySelector("#watchlistGrid");
  grid.innerHTML = watchlist.map((item) => `
    <article class="watch-card">
      <h3>${item.code}</h3>
      <dl>
        <div><dt>Luận điểm</dt><dd>${item.thesis}</dd></div>
        <div><dt>Vùng quan sát</dt><dd>${item.zone}</dd></div>
        <div><dt>Điểm mua tham khảo</dt><dd>${item.entry}</dd></div>
        <div><dt>Vùng chốt lời tham khảo</dt><dd>${item.target}</dd></div>
        <div><dt>Cắt lỗ tham khảo</dt><dd>${item.stop}</dd></div>
        <div><dt>Điều kiện kích hoạt</dt><dd>${item.trigger}</dd></div>
        <div><dt>Rủi ro chính</dt><dd>${item.risk}</dd></div>
      </dl>
    </article>
  `).join("");
}

function renderScenarios() {
  const stack = document.querySelector("#scenarioStack");
  stack.innerHTML = scenarios.map((scenario) => `
    <article class="scenario-card">
      <h3>${scenario.name}</h3>
      <ul>${scenario.items.map((item) => `<li>${item}</li>`).join("")}</ul>
    </article>
  `).join("");
}

function renderEvents() {
  const list = document.querySelector("#eventList");
  list.innerHTML = events.map(([name, detail]) => `
    <article class="event-card">
      <h3>${name}</h3>
      <p>${detail}</p>
    </article>
  `).join("");
}

function renderSources() {
  const list = document.querySelector("#sourceList");
  list.innerHTML = sources.map(([group, links]) => `
    <article class="source-group">
      <h3>${group}</h3>
      ${links.map((link) => `<a href="#">${link}</a>`).join("")}
    </article>
  `).join("");
}

renderMarketDashboard();
renderSectorTable();
renderWatchlist();
renderScenarios();
renderEvents();
renderSources();
