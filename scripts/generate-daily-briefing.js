const fs = require("node:fs");
const path = require("node:path");
const { loadEnv } = require("../src/config/loadEnv");
const { fetchMarketData, saveMarketData } = require("../src/data/fetchMarketData");
const { fetchNews } = require("../src/data/fetchNews");
const { buildPrompt } = require("../src/ai/buildPrompt");
const { callGemini } = require("../src/ai/geminiClient");
const { writeHtml } = require("../src/render/renderHtml");
const { updateIndex } = require("../src/render/updateIndex");

const rootDir = path.resolve(__dirname, "..");

function readJson(filePath, fallback) {
  if (!fs.existsSync(filePath)) return fallback;
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function loadWatchlist() {
  const filePath = path.join(rootDir, "data", "watchlist.json");
  const raw = readJson(filePath, { items: [] });
  return raw.items || raw.tickers || [];
}

async function main() {
  loadEnv(rootDir);

  console.log("Đang lấy dữ liệu thị trường...");
  const marketData = await fetchMarketData({ rootDir });
  console.log(`Dữ liệu thị trường: Việt Nam=${marketData.sourceStatus.vietnam}, global=${marketData.sourceStatus.global}, crypto=${marketData.sourceStatus.crypto}, fx=${marketData.sourceStatus.fx}`);

  console.log("Đang lấy tin tức...");
  const news = await fetchNews({ rootDir });
  console.log(`Đã nạp ${news.length} tin/tin fallback.`);

  console.log("Đang nạp watchlist...");
  const watchlist = loadWatchlist();
  console.log(`Đã nạp ${watchlist.length} mã watchlist.`);

  marketData.news = news;
  marketData.watchlist = watchlist;
  const cachePath = saveMarketData(rootDir, marketData);
  console.log(`Đã lưu cache dữ liệu: ${path.relative(rootDir, cachePath)}`);

  const brand = process.env.REPORT_BRAND || "HDINVEST";
  const prompt = buildPrompt({ marketData, news, watchlist, brand });

  console.log("Đang gọi Gemini...");
  const aiResult = await callGemini({ prompt, marketData, news, watchlist });
  if (aiResult.mode === "fallback") {
    console.log(`Gemini fallback: ${aiResult.error}`);
  } else {
    console.log(`Gemini OK: ${aiResult.model}`);
  }

  console.log("Đang render HTML...");
  const { outputPath, dateKey } = writeHtml({
    rootDir,
    briefing: aiResult.briefing,
    marketData,
    outputDate: new Date()
  });

  const indexResult = updateIndex(rootDir);
  console.log(`Đã tạo bản tin: ${path.relative(rootDir, outputPath)}`);
  console.log(`Đã cập nhật index: ${path.relative(rootDir, indexResult.outputPath)}`);
  console.log(`Đường dẫn file output: ${outputPath}`);
  console.log(`Ngày bản tin: ${dateKey}`);
}

main().catch((error) => {
  console.error("Không tạo được bản tin.");
  console.error(error?.stack || error?.message || error);
  process.exit(1);
});
