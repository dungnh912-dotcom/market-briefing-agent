const fs = require("node:fs");
const path = require("node:path");
const { loadEnv } = require("../src/config/loadEnv");

const rootDir = path.resolve(__dirname, "..");
loadEnv(rootDir);

const checks = [];

function addCheck(name, ok, detail) {
  checks.push({ name, ok, detail });
}

function fileExists(relativePath) {
  return fs.existsSync(path.join(rootDir, relativePath));
}

const major = Number(process.versions.node.split(".")[0]);
addCheck("Node version >= 18", major >= 18, process.version);
addCheck("GEMINI_API_KEY", Boolean(process.env.GEMINI_API_KEY), process.env.GEMINI_API_KEY ? "đã cấu hình" : "thiếu GEMINI_API_KEY trong .env hoặc GitHub Secrets");
addCheck("data/manual_market_data.json", fileExists("data/manual_market_data.json"), "fallback dữ liệu thị trường");
addCheck("data/manual_news.json", fileExists("data/manual_news.json"), "fallback tin tức");
addCheck("data/watchlist.json", fileExists("data/watchlist.json"), "watchlist điều kiện");
addCheck("preview/index.html", fileExists("preview/index.html"), "giao diện preview đã duyệt");

for (const check of checks) {
  const icon = check.ok ? "OK" : "FAIL";
  console.log(`[${icon}] ${check.name}: ${check.detail}`);
}

const failed = checks.filter((check) => !check.ok);
if (failed.length) {
  console.error("\nCấu hình chưa hoàn tất. Hãy tạo .env từ .env.example và điền GEMINI_API_KEY nếu muốn dùng Gemini thật.");
  process.exit(1);
}

console.log("\nCấu hình sẵn sàng.");
