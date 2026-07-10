const fs = require("node:fs");
const path = require("node:path");

const feeds = [
  {
    name: "Google News Việt Nam chứng khoán",
    url: "https://news.google.com/rss/search?q=chung%20khoan%20Viet%20Nam&hl=vi&gl=VN&ceid=VN:vi",
    tags: ["Việt Nam", "chứng khoán"]
  },
  {
    name: "Google News vĩ mô Việt Nam",
    url: "https://news.google.com/rss/search?q=kinh%20te%20vi%20mo%20Viet%20Nam&hl=vi&gl=VN&ceid=VN:vi",
    tags: ["Việt Nam", "vĩ mô"]
  },
  {
    name: "Google News Fed CPI PMI oil China",
    url: "https://news.google.com/rss/search?q=Fed%20CPI%20PMI%20oil%20China%20markets&hl=en-US&gl=US&ceid=US:en",
    tags: ["quốc tế"]
  }
];

function readJson(filePath, fallback) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    return { ...fallback, _error: error.message };
  }
}

function decodeEntities(value = "") {
  return value
    .replace(/<!\[CDATA\[(.*?)\]\]>/gs, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/<[^>]+>/g, "")
    .trim();
}

function tagValue(item, tag) {
  const match = item.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i"));
  return decodeEntities(match?.[1] || "");
}

async function fetchText(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { "User-Agent": "HDINVEST-market-briefing/1.0" }
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.text();
  } finally {
    clearTimeout(timer);
  }
}

async function fetchFeed(feed) {
  const xml = await fetchText(feed.url);
  return [...xml.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)].slice(0, 6).map((match) => {
    const item = match[1];
    return {
      title: tagValue(item, "title"),
      url: tagValue(item, "link"),
      source: tagValue(item, "source") || feed.name,
      published: tagValue(item, "pubDate"),
      summary: tagValue(item, "description"),
      tags: feed.tags,
      sourceType: "live"
    };
  }).filter((item) => item.title);
}

async function fetchNews(options = {}) {
  const rootDir = options.rootDir || process.cwd();
  const manual = readJson(path.join(rootDir, "data", "manual_news.json"), { items: [] });
  const news = [];

  for (const feed of feeds) {
    try {
      news.push(...await fetchFeed(feed));
    } catch (error) {
      news.push({
        title: `Không lấy được feed: ${feed.name}`,
        url: feed.url,
        source: feed.name,
        published: "",
        summary: error.message,
        tags: feed.tags,
        sourceType: "error"
      });
    }
  }

  const manualItems = (manual.items || []).map((item) => ({
    title: item.title,
    url: item.url || "",
    source: item.source || "manual",
    published: item.published || "",
    summary: item.summary || "",
    tags: item.tags || ["manual"],
    sourceType: "manual"
  }));

  return [...manualItems, ...news].slice(0, 24);
}

module.exports = { fetchNews };
