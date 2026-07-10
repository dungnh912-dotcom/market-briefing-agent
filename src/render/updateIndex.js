const fs = require("node:fs");
const path = require("node:path");
const { escapeHtml } = require("./renderHtml");

function readTitle(filePath) {
  const html = fs.readFileSync(filePath, "utf8");
  const h1 = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1];
  const title = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1];
  return (h1 || title || path.basename(filePath, ".html")).replace(/<[^>]+>/g, "").replace(/\s+\| HDINVEST$/, "").trim();
}

function isCurrentHdinvestBriefing(filePath) {
  const html = fs.readFileSync(filePath, "utf8");
  return html.includes("HDINVEST") && !html.includes("HDUNGINVEST") && !html.includes("HIEUINVEST");
}

function updateIndex(rootDir) {
  const briefingDir = path.join(rootDir, "bantin");
  fs.mkdirSync(briefingDir, { recursive: true });
  const reports = fs.readdirSync(briefingDir)
    .filter((file) => /^\d{4}-\d{2}-\d{2}\.html$/.test(file))
    .filter((file) => isCurrentHdinvestBriefing(path.join(briefingDir, file)))
    .sort()
    .reverse()
    .map((file) => {
      const filePath = path.join(briefingDir, file);
      return {
        file,
        date: file.replace(".html", ""),
        title: readTitle(filePath)
      };
    });

  const latest = reports[0];
  const html = `<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="HDINVEST Daily Market Briefing archive">
  <title>HDINVEST Daily Market Briefing</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="preview/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand-lockup" href="index.html" aria-label="HDINVEST Daily Market Brief">
      <span class="brand-mark">HD</span>
      <span>HDINVEST <span>DAILY MARKET BRIEF</span></span>
    </a>
    <time datetime="${escapeHtml(latest?.date || "")}">${escapeHtml(latest?.date || "Chưa có bản tin")}</time>
    <a class="archive-link" href="preview/index.html">Xem preview</a>
  </header>

  <main>
    <section class="hero-section">
      <div class="hero-inner">
        <div class="hero-copy">
          <p class="section-kicker">HDINVEST Research</p>
          <h1>Daily Market Briefing</h1>
          <p class="hero-meta">Bản tin thị trường hằng ngày dành cho nhà đầu tư Việt Nam</p>
          <p class="tagline">Dữ liệu là nền tảng, kỷ luật là lợi thế.</p>
          ${latest ? `<a class="notice-badge" href="bantin/${escapeHtml(latest.file)}">Mở bản tin mới nhất · ${escapeHtml(latest.date)}</a>` : '<span class="notice-badge">Chưa có bản tin được tạo</span>'}
        </div>
      </div>
    </section>

    <section class="paper-band">
      <div class="content-shell">
        <div class="section-heading">
          <span>01</span>
          <div><p>Archive</p><h2>Tất cả bản tin</h2></div>
        </div>
        <div class="event-list">
          ${reports.map((report) => `
            <article class="event-card">
              <h3><a href="bantin/${escapeHtml(report.file)}">${escapeHtml(report.title)}</a></h3>
              <p>${escapeHtml(report.date)} · HDINVEST Daily Market Briefing</p>
            </article>
          `).join("") || '<article class="event-card"><h3>Chưa có bản tin</h3><p>Chạy npm run generate để tạo bản tin đầu tiên.</p></article>'}
        </div>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div><strong>HDINVEST Research</strong><span>Daily Market Briefing</span></div>
    <p>Bản tin chỉ nhằm mục đích cung cấp thông tin, không phải khuyến nghị giao dịch hay tư vấn đầu tư cá nhân. Nhà đầu tư cần tự chịu trách nhiệm với quyết định của mình.</p>
  </footer>
</body>
</html>
`;

  const outputPath = path.join(rootDir, "index.html");
  fs.writeFileSync(outputPath, html, "utf8");
  return { outputPath, count: reports.length, latest };
}

module.exports = { updateIndex };
