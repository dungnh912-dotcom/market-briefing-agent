const fs = require("node:fs");
const path = require("node:path");

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

function formatNumber(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "chưa có dữ liệu";
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: digits }).format(number);
}

function formatChange(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "n/a";
  const sign = number > 0 ? "+" : "";
  return `${sign}${new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(number)}%`;
}

function trendClass(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || Math.abs(number) < 0.01) return "flat";
  return number > 0 ? "up" : "down";
}

function impactClass(value) {
  if (value === "Hưởng lợi") return "positive";
  if (value === "Bất lợi") return "negative";
  return "neutral";
}

function todayVi(date = new Date()) {
  return new Intl.DateTimeFormat("vi-VN", {
    timeZone: "Asia/Ho_Chi_Minh",
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  }).format(date);
}

function reportDateKey(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(date);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function dashboardRows(marketData) {
  const vietnam = array(marketData.vietnam?.indices);
  const fx = marketData.vietnam?.fx?.label ? [marketData.vietnam.fx] : [];
  const global = [
    ...array(marketData.global?.indices).slice(0, 5),
    ...array(marketData.global?.commodities).slice(0, 3),
    ...array(marketData.global?.bonds),
    ...array(marketData.global?.crypto)
  ];
  return [...vietnam, ...fx, ...global].slice(0, 16);
}

function renderList(items) {
  const rows = array(items);
  if (!rows.length) return "<li>chưa đủ dữ liệu xác nhận</li>";
  return rows.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderDashboard(marketData) {
  return dashboardRows(marketData).map((item) => {
    const className = trendClass(item.changePct);
    const label = className === "up" ? "Tăng" : className === "down" ? "Giảm/áp lực" : "Trung tính";
    const value = item.value === null || item.value === undefined
      ? "chưa có dữ liệu"
      : `${formatNumber(item.value)}${item.currency ? ` ${escapeHtml(item.currency)}` : ""}`;
    return `
      <article class="metric-card">
        <header>
          <h3>${escapeHtml(item.label || item.symbol)}</h3>
          <span class="badge ${className}">${label}</span>
        </header>
        <div>
          <p class="metric-value">${value}</p>
          <span class="badge ${className}">${formatChange(item.changePct)}</span>
          <p class="metric-note">${escapeHtml(item.note || item.source || "Dữ liệu tổng hợp")}</p>
        </div>
      </article>
    `;
  }).join("");
}

function renderPulse(title, groups) {
  return `
    <div class="pulse-grid">
      ${groups.map((group) => `
        <article>
          <h3>${escapeHtml(group.title)}</h3>
          <ul>${renderList(group.items)}</ul>
        </article>
      `).join("")}
    </div>
  `;
}

function renderSectorTable(items) {
  return array(items).map((item) => `
    <tr>
      <td><strong>${escapeHtml(item.sector)}</strong></td>
      <td><span class="impact ${impactClass(item.impact)}">${escapeHtml(item.impact || "Trung tính")}</span></td>
      <td>${escapeHtml(item.reason)}</td>
      <td>${escapeHtml(item.tickers)}</td>
      <td>${escapeHtml(item.confirmation)}</td>
    </tr>
  `).join("");
}

function renderWatchlist(items) {
  return array(items).map((item) => `
    <article class="watch-card">
      <h3>${escapeHtml(item.symbol)}</h3>
      <dl>
        <div><dt>Ngành</dt><dd>${escapeHtml(item.sector)}</dd></div>
        <div><dt>Luận điểm</dt><dd>${escapeHtml(item.thesis)}</dd></div>
        <div><dt>Vùng quan sát</dt><dd>${escapeHtml(item.observationZone)}</dd></div>
        <div><dt>Điểm mua tham khảo</dt><dd>${escapeHtml(item.entryRule)}</dd></div>
        <div><dt>Vùng chốt lời tham khảo</dt><dd>${escapeHtml(item.takeProfit)}</dd></div>
        <div><dt>Cắt lỗ tham khảo</dt><dd>${escapeHtml(item.stopLoss)}</dd></div>
        <div><dt>Điều kiện kích hoạt</dt><dd>${escapeHtml(item.trigger)}</dd></div>
        <div><dt>Rủi ro chính</dt><dd>${escapeHtml(item.risk)}</dd></div>
      </dl>
    </article>
  `).join("");
}

function renderTechnical(items) {
  return array(items).map((item) => `
    <article>
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <p>${escapeHtml(item.note || "")}</p>
    </article>
  `).join("");
}

function renderScenarios(items) {
  return array(items).map((item) => `
    <article class="scenario-card">
      <h3>${escapeHtml(item.name)}</h3>
      <ul>
        <li>Điều kiện: ${escapeHtml(item.condition)}</li>
        <li>Vùng điểm VN-Index: ${escapeHtml(item.vnIndexRange)}</li>
        <li>Nhóm ngành ưu tiên: ${escapeHtml(item.preferredSectors)}</li>
        <li>Hành động broker: ${escapeHtml(item.brokerAction)}</li>
        <li>Rủi ro: ${escapeHtml(item.risk)}</li>
      </ul>
    </article>
  `).join("");
}

function renderEvents(items) {
  return array(items).map((item) => `
    <article class="event-card">
      <h3>${escapeHtml(item.group)}</h3>
      <p>${escapeHtml(item.detail)}</p>
    </article>
  `).join("");
}

function renderSources(items) {
  return array(items).map((group) => `
    <article class="source-group">
      <h3>${escapeHtml(group.group)}</h3>
      ${array(group.items).map((item) => `<a href="#">${escapeHtml(item)}</a>`).join("")}
    </article>
  `).join("");
}

function renderHtml({ briefing, marketData, outputDate = new Date() }) {
  const dateKey = reportDateKey(outputDate);
  const displayDate = todayVi(outputDate);
  const title = briefing.title || "HDINVEST Daily Market Briefing";
  const subtitle = briefing.subtitle || "Bản tin thị trường chứng khoán · Cập nhật 07:00 · Giờ Việt Nam";
  const disclaimer = briefing.disclaimer || "Bản tin chỉ nhằm mục đích cung cấp thông tin, không phải khuyến nghị giao dịch hay tư vấn đầu tư cá nhân. Nhà đầu tư cần tự chịu trách nhiệm với quyết định của mình.";

  return `<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="HDINVEST Daily Market Briefing ${escapeHtml(dateKey)}">
  <title>${escapeHtml(title)} | HDINVEST</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../preview/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand-lockup" href="../index.html" aria-label="HDINVEST Daily Market Brief">
      <span class="brand-mark">HD</span>
      <span>HDINVEST <span>DAILY MARKET BRIEF</span></span>
    </a>
    <time datetime="${escapeHtml(dateKey)}">${escapeHtml(displayDate)}</time>
    <a class="archive-link" href="../index.html">Tất cả bản tin</a>
  </header>

  <main>
    <section class="hero-section">
      <div class="hero-inner">
        <div class="hero-copy">
          <p class="section-kicker">Vietnam Equity Research</p>
          <h1>${escapeHtml(title)}</h1>
          <p class="hero-meta">${escapeHtml(subtitle)}</p>
          <p class="tagline">Dữ liệu là nền tảng, kỷ luật là lợi thế.</p>
          <span class="notice-badge">Tài liệu thông tin tổng hợp · Không phải khuyến nghị mua/bán</span>
        </div>
        <aside class="hero-brief" aria-label="Tình trạng dữ liệu">
          <div><span>Dữ liệu Việt Nam</span><strong>${escapeHtml(marketData.sourceStatus?.vietnam || "fallback")}</strong></div>
          <div><span>Dữ liệu quốc tế</span><strong>${escapeHtml(marketData.sourceStatus?.global || "fallback")}</strong></div>
          <div><span>Crypto / FX</span><strong>${escapeHtml(`${marketData.sourceStatus?.crypto || "fallback"} / ${marketData.sourceStatus?.fx || "fallback"}`)}</strong></div>
        </aside>
      </div>
    </section>

    <section class="paper-band">
      <div class="content-shell">
        <section class="summary-grid">
          <div class="section-heading"><span>01</span><div><p>Executive Summary</p><h2>Tóm tắt điều hành</h2></div></div>
          <div class="summary-panel">${array(briefing.executiveSummary).map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</div>
        </section>

        <section>
          <div class="section-heading"><span>02</span><div><p>Market Dashboard</p><h2>Bảng chỉ báo thị trường</h2></div></div>
          <div class="market-grid">${renderDashboard(marketData)}</div>
        </section>
      </div>
    </section>

    <section class="dark-band">
      <div class="content-shell">
        <div class="section-heading inverse"><span>03</span><div><p>Market Pulse</p><h2>Việt Nam và quốc tế</h2></div></div>
        ${renderPulse("Việt Nam", [
          { title: "Chỉ số & kỹ thuật", items: briefing.vietnamPulse?.technical },
          { title: "Dòng tiền & khối ngoại", items: briefing.vietnamPulse?.flow },
          { title: "Tỷ giá, lãi suất, vĩ mô", items: briefing.vietnamPulse?.macro }
        ])}
        <div class="pulse-grid secondary">
          ${[
            { title: "Mỹ & châu Âu", items: briefing.internationalPulse?.usEurope },
            { title: "Châu Á", items: briefing.internationalPulse?.asia },
            { title: "Hàng hóa & crypto", items: briefing.internationalPulse?.commoditiesCrypto }
          ].map((group) => `
            <article><h3>${escapeHtml(group.title)}</h3><ul>${renderList(group.items)}</ul></article>
          `).join("")}
        </div>
      </div>
    </section>

    <section class="paper-band">
      <div class="content-shell">
        <section>
          <div class="section-heading"><span>04</span><div><p>Sector Impact Map</p><h2>Mã & nhóm ngành tác động</h2></div></div>
          <div class="table-wrap">
            <table class="research-table">
              <thead><tr><th>Nhóm ngành</th><th>Mức tác động</th><th>Lý do</th><th>Mã theo dõi</th><th>Điều kiện xác nhận</th></tr></thead>
              <tbody>${renderSectorTable(briefing.sectorImpact)}</tbody>
            </table>
          </div>
        </section>

        <section class="watchlist-section">
          <div class="section-heading"><span>05</span><div><p>Conditional Watchlist</p><h2>Watchlist giao dịch có điều kiện</h2></div></div>
          <p class="disclaimer-line">Các vùng giá là tham khảo kỹ thuật, không phải khuyến nghị đầu tư cá nhân.</p>
          <div class="watchlist-grid">${renderWatchlist(briefing.watchlist)}</div>
        </section>
      </div>
    </section>

    <section class="strategy-band">
      <div class="content-shell">
        <div class="strategy-layout">
          <section>
            <div class="section-heading compact"><span>06</span><div><p>Technical View</p><h2>Góc nhìn kỹ thuật VN-Index</h2></div></div>
            <div class="technical-grid">${renderTechnical(briefing.technicalView)}</div>
          </section>
          <section>
            <div class="section-heading compact"><span>07</span><div><p>Broker Strategy</p><h2>Ba kịch bản thị trường</h2></div></div>
            <div class="scenario-stack">${renderScenarios(briefing.scenarios)}</div>
          </section>
        </div>
      </div>
    </section>

    <section class="paper-band">
      <div class="content-shell">
        <div class="events-sources">
          <section>
            <div class="section-heading compact"><span>08</span><div><p>Event Calendar</p><h2>Lịch sự kiện</h2></div></div>
            <div class="event-list">${renderEvents(briefing.events)}</div>
          </section>
          <section>
            <div class="section-heading compact"><span>09</span><div><p>References</p><h2>Nguồn tham khảo</h2></div></div>
            <div class="source-list">${renderSources(briefing.sources)}</div>
          </section>
        </div>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div><strong>HDINVEST Research</strong><span>Daily Market Briefing · ${escapeHtml(dateKey)}</span></div>
    <p>${escapeHtml(disclaimer)}</p>
  </footer>
</body>
</html>
`;
}

function writeHtml({ rootDir, briefing, marketData, outputDate = new Date() }) {
  const dateKey = reportDateKey(outputDate);
  const outputDir = path.join(rootDir, "bantin");
  fs.mkdirSync(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `${dateKey}.html`);
  fs.writeFileSync(outputPath, renderHtml({ briefing, marketData, outputDate }), "utf8");
  return { outputPath, dateKey };
}

module.exports = { renderHtml, writeHtml, reportDateKey, escapeHtml };
