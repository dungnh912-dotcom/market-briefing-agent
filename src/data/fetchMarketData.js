const fs = require("node:fs");
const path = require("node:path");

const REQUEST_TIMEOUT_MS = 12000;

const yahooAssets = {
  globalIndices: [
    ["S&P 500", "^GSPC", "global"],
    ["Nasdaq", "^IXIC", "global"],
    ["Dow Jones", "^DJI", "global"],
    ["Nikkei 225", "^N225", "global"],
    ["Hang Seng", "^HSI", "global"],
    ["Shanghai Composite", "000001.SS", "global"],
    ["KOSPI", "^KS11", "global"],
    ["DAX", "^GDAXI", "global"]
  ],
  commodities: [
    ["Vàng thế giới", "GC=F", "commodity"],
    ["Dầu WTI", "CL=F", "commodity"],
    ["Dầu Brent", "BZ=F", "commodity"],
    ["Bạc", "SI=F", "commodity"]
  ],
  bonds: [
    ["US 10Y Yield", "^TNX", "bond"]
  ],
  fx: [
    ["DXY", "DX-Y.NYB", "fx"],
    ["USD/VND", "VND=X", "fx"]
  ],
  vietnamStocks: [
    "VCB", "BID", "CTG", "MBB", "TCB", "VPB", "HPG", "FPT", "MWG", "VHM",
    "VIC", "VRE", "SSI", "VND", "HCM", "GAS", "PVD", "PVS", "MSN", "VNM",
    "GMD", "KBC", "NLG"
  ]
};

function readJson(filePath, fallback) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    return { ...fallback, _error: error.message };
  }
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function nowIso(timezone) {
  const now = new Date();
  const offset = timezone === "Asia/Ho_Chi_Minh" ? "+07:00" : "Z";
  if (offset === "+07:00") {
    return new Date(now.getTime() + 7 * 60 * 60 * 1000).toISOString().replace("Z", "+07:00");
  }
  return now.toISOString();
}

function numberOrNull(value) {
  return Number.isFinite(Number(value)) ? Number(value) : null;
}

function percentChange(price, previousClose) {
  if (!Number.isFinite(price) || !Number.isFinite(previousClose) || previousClose === 0) {
    return null;
  }
  return ((price - previousClose) / previousClose) * 100;
}

async function fetchJson(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        "User-Agent": "HDINVEST-market-briefing/1.0"
      }
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function fetchYahooQuote(label, symbol, type) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=5d&interval=1d`;
  const data = await fetchJson(url);
  const result = data?.chart?.result?.[0];
  if (!result) {
    throw new Error(`Yahoo returned no result for ${symbol}`);
  }

  const meta = result.meta || {};
  const price = numberOrNull(meta.regularMarketPrice ?? meta.previousClose);
  const previousClose = numberOrNull(meta.previousClose);
  const change = Number.isFinite(price) && Number.isFinite(previousClose) ? price - previousClose : null;

  return {
    label,
    symbol,
    type,
    value: price,
    change,
    changePct: percentChange(price, previousClose),
    currency: meta.currency || "",
    source: "Yahoo Finance",
    sourceType: "live",
    updatedAt: meta.regularMarketTime
      ? new Date(meta.regularMarketTime * 1000).toISOString()
      : new Date().toISOString(),
    note: "Dữ liệu lấy tự động từ Yahoo Finance."
  };
}

async function fetchManyYahoo(items) {
  const output = [];
  for (const [label, symbol, type] of items) {
    try {
      output.push(await fetchYahooQuote(label, symbol, type));
    } catch (error) {
      output.push({
        label,
        symbol,
        type,
        value: null,
        change: null,
        changePct: null,
        source: "Yahoo Finance",
        sourceType: "error",
        note: `Không lấy được dữ liệu live: ${error.message}`
      });
    }
  }
  return output;
}

async function fetchCrypto() {
  const url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true";
  try {
    const data = await fetchJson(url);
    return [
      {
        label: "Bitcoin",
        symbol: "BTC",
        type: "crypto",
        value: numberOrNull(data.bitcoin?.usd),
        changePct: numberOrNull(data.bitcoin?.usd_24h_change),
        currency: "USD",
        source: "CoinGecko",
        sourceType: "live",
        note: "Dữ liệu giá crypto 24h từ CoinGecko."
      },
      {
        label: "Ethereum",
        symbol: "ETH",
        type: "crypto",
        value: numberOrNull(data.ethereum?.usd),
        changePct: numberOrNull(data.ethereum?.usd_24h_change),
        currency: "USD",
        source: "CoinGecko",
        sourceType: "live",
        note: "Dữ liệu giá crypto 24h từ CoinGecko."
      }
    ];
  } catch (error) {
    return ["BTC", "ETH"].map((symbol) => ({
      label: symbol === "BTC" ? "Bitcoin" : "Ethereum",
      symbol,
      type: "crypto",
      value: null,
      changePct: null,
      currency: "USD",
      source: "CoinGecko",
      sourceType: "error",
      note: `Không lấy được dữ liệu live: ${error.message}`
    }));
  }
}

function manualIndexToRows(manualMarket) {
  const indexes = manualMarket.indexes || {};
  return Object.entries(indexes).map(([symbol, item]) => ({
    label: item.label || symbol,
    symbol,
    type: symbol === "USDVND" ? "fx" : "index",
    value: numberOrNull(item.value),
    change: numberOrNull(item.change),
    changePct: numberOrNull(item.change_pct),
    source: item.source || "manual",
    sourceType: Number.isFinite(Number(item.value)) ? "fallback" : "manual",
    note: item.comment || "Dữ liệu thủ công/fallback."
  }));
}

async function fetchVietnamStocks() {
  const rows = [];
  for (const symbol of yahooAssets.vietnamStocks) {
    try {
      rows.push(await fetchYahooQuote(symbol, `${symbol}.VN`, "stock"));
    } catch (error) {
      rows.push({
        label: symbol,
        symbol,
        type: "stock",
        value: null,
        change: null,
        changePct: null,
        source: "Yahoo Finance",
        sourceType: "manual",
        note: "Chưa có dữ liệu live ổn định cho mã Việt Nam; cần cập nhật thủ công nếu dùng vùng kỹ thuật."
      });
    }
  }
  return rows;
}

function statusFromRows(rows, fallbackRows = []) {
  if (rows.some((row) => row.sourceType === "live" && Number.isFinite(Number(row.value)))) return "live";
  if (fallbackRows.some((row) => Number.isFinite(Number(row.value)))) return "fallback";
  if (rows.some((row) => row.sourceType === "error")) return "error";
  return "fallback";
}

async function fetchMarketData(options = {}) {
  const rootDir = options.rootDir || process.cwd();
  const timezone = process.env.TIMEZONE || "Asia/Ho_Chi_Minh";
  const manualMarket = readJson(path.join(rootDir, "data", "manual_market_data.json"), {});

  const [globalIndices, commodities, bonds, fxRows, crypto, vietnamStocks] = await Promise.all([
    fetchManyYahoo(yahooAssets.globalIndices),
    fetchManyYahoo(yahooAssets.commodities),
    fetchManyYahoo(yahooAssets.bonds),
    fetchManyYahoo(yahooAssets.fx),
    fetchCrypto(),
    fetchVietnamStocks()
  ]);

  const manualVietnamIndices = manualIndexToRows(manualMarket).filter((row) => row.type !== "fx");
  const manualFx = manualIndexToRows(manualMarket).filter((row) => row.type === "fx");
  const liveUsdVnd = fxRows.find((row) => row.symbol === "VND=X" && Number.isFinite(Number(row.value)));

  const marketData = {
    updatedAt: nowIso(timezone),
    timezone,
    sourceStatus: {
      vietnam: statusFromRows(vietnamStocks, manualVietnamIndices),
      global: statusFromRows([...globalIndices, ...commodities, ...bonds, ...fxRows]),
      crypto: statusFromRows(crypto),
      fx: liveUsdVnd ? "live" : statusFromRows(fxRows, manualFx)
    },
    vietnam: {
      indices: manualVietnamIndices,
      stocks: vietnamStocks,
      marketBreadth: manualMarket.market_breadth || {},
      foreignFlow: manualMarket.foreign_flow || {},
      liquidity: manualMarket.liquidity || {},
      fx: liveUsdVnd || manualFx[0] || {},
      rates: {
        interbank: manualMarket.interbank_rate || {}
      },
      sectorFlow: manualMarket.sector_flow || [],
      topGainers: manualMarket.top_gainers || [],
      topLosers: manualMarket.top_losers || []
    },
    global: {
      indices: globalIndices,
      commodities,
      bonds,
      fx: fxRows,
      crypto
    },
    news: [],
    watchlist: []
  };

  const cachePath = path.join(rootDir, "data", "cache", "latest-market-data.json");
  ensureDir(path.dirname(cachePath));
  fs.writeFileSync(cachePath, `${JSON.stringify(marketData, null, 2)}\n`, "utf8");

  return marketData;
}

function saveMarketData(rootDir, marketData) {
  const cachePath = path.join(rootDir, "data", "cache", "latest-market-data.json");
  ensureDir(path.dirname(cachePath));
  fs.writeFileSync(cachePath, `${JSON.stringify(marketData, null, 2)}\n`, "utf8");
  return cachePath;
}

module.exports = { fetchMarketData, saveMarketData };
