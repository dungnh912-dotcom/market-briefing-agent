from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MISSING = "chưa có dữ liệu cập nhật"
CACHE_FILE = DATA_DIR / "cache" / "google_finance_metrics.json"

GOOGLE_FINANCE_BASE = "https://www.google.com/finance/quote"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

GLOBAL_SYMBOLS: list[tuple[str, str, str]] = [
    ("S&P 500", ".INX:INDEXSP", "Chứng khoán Mỹ"),
    ("Dow Jones", ".DJI:INDEXDJX", "Chứng khoán Mỹ"),
    ("Nasdaq", ".IXIC:INDEXNASDAQ", "Chứng khoán Mỹ"),
    ("Nikkei 225", "NI225:INDEXNIKKEI", "Chứng khoán châu Á"),
    ("Vàng thế giới", "GCW00:COMEX", "Hàng hóa"),
    ("Bạc", "SIW00:COMEX", "Hàng hóa"),
    ("Dầu WTI", "CLW00:NYMEX", "Năng lượng"),
    ("Dầu Brent", "BZW00:NYMEX", "Năng lượng"),
    ("Bitcoin", "BTC-USD", "Crypto"),
    ("USD Index", "DXY:INDEXNYSEGIS", "Tiền tệ"),
    ("US 10Y", "US10Y:INDEXCBOE", "Trái phiếu Mỹ"),
]

VIETNAM_KEYS = ["VNINDEX", "VN30", "HNX", "UPCOM", "USDVND"]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return default if data is None else data
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def tone(change_pct: float | None) -> str:
    if change_pct is None:
        return "neutral"
    if change_pct > 0.05:
        return "up"
    if change_pct < -0.05:
        return "down"
    return "neutral"


def format_number(value: Any, digits: int = 2) -> str:
    if value is None or value == "":
        return MISSING
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def format_change(change: Any, change_pct: Any) -> str:
    if change is None and change_pct is None:
        return MISSING
    pieces = []
    if change is not None:
        try:
            pieces.append(f"{float(change):+,.2f}")
        except (TypeError, ValueError):
            pieces.append(str(change))
    if change_pct is not None:
        try:
            pieces.append(f"({float(change_pct):+.2f}%)")
        except (TypeError, ValueError):
            pieces.append(f"({change_pct})")
    return " ".join(pieces) if pieces else MISSING


def to_float(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").replace("\u202f", "").strip()
    return float(cleaned)


def google_quote_url(quote: str) -> str:
    return f"{GOOGLE_FINANCE_BASE}/{quote}?hl=en"


def load_metric_cache() -> dict[str, Any]:
    return load_json(CACHE_FILE, {})


def save_metric_cache(symbol: str, metric: dict[str, Any]) -> None:
    cache = load_metric_cache()
    cache[symbol] = metric
    write_json(CACHE_FILE, cache)


def cached_metric(label: str, symbol: str, reason: str) -> dict[str, Any] | None:
    metric = load_metric_cache().get(symbol)
    if not metric:
        return None
    restored = dict(metric)
    restored["label"] = label
    restored["note"] = f"Dữ liệu cache gần nhất: {restored.get('as_of', MISSING)}. Google Finance hiện chưa cập nhật được: {reason}"
    restored["updated_at"] = restored.get("updated_at") or MISSING
    restored["source"] = "Google Finance cache"
    return restored


def unavailable_metric(label: str, symbol: str, reason: str, source: str = "Google Finance") -> dict[str, Any]:
    fetched_at = now_utc()
    return {
        "label": label,
        "symbol": symbol,
        "value": MISSING,
        "raw_value": None,
        "change": MISSING,
        "change_pct": None,
        "tone": "neutral",
        "note": reason or MISSING,
        "source": source,
        "updated_at": fetched_at,
        "as_of": MISSING,
        "technical": {"available": False, "message": MISSING},
    }


def parse_google_finance_text(label: str, symbol: str, text: str, fetched_at: str) -> dict[str, Any]:
    pattern = re.compile(
        r"check_indeterminate_small\s+(?:Add to list\s+)?(.+?)\s+"
        r"(\$?[0-9][0-9,]*(?:\.[0-9]+)?)\s+"
        r"arrow_(upward|downward)\s+"
        r"([+-]?[0-9]+(?:\.[0-9]+)?)%\s+"
        r"\(\s*([+-]?[0-9,]+(?:\.[0-9]+)?)\s*\)\s+"
        r"(?:Today|1D)\s+(.+?)\s+area_chart"
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("Không tìm thấy block giá trong Google Finance")

    price = to_float(match.group(2))
    direction = match.group(3)
    change_pct = float(match.group(4))
    abs_change = to_float(match.group(5))
    if direction == "downward" and abs_change > 0:
        abs_change = -abs_change
    as_of = match.group(6).replace("\xa0", " ").strip()
    metric = {
        "label": label,
        "symbol": symbol,
        "value": format_number(price, 4 if label == "USD/VND" else 2),
        "raw_value": round(price, 6),
        "change": format_change(abs_change, change_pct),
        "change_pct": round(change_pct, 2),
        "tone": tone(change_pct),
        "note": f"Google Finance, dữ liệu gần nhất: {as_of}.",
        "source": "Google Finance",
        "updated_at": fetched_at,
        "as_of": as_of,
        "technical": {"available": False, "message": "Google Finance quote page không cung cấp đủ lịch sử giá để tính kỹ thuật."},
    }
    return metric


def fetch_google_finance_metric(label: str, symbol: str) -> dict[str, Any]:
    fetched_at = now_utc()
    try:
        response = requests.get(google_quote_url(symbol), timeout=18, headers=HEADERS)
        response.raise_for_status()
        text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
        metric = parse_google_finance_text(label, symbol, text, fetched_at)
        save_metric_cache(symbol, metric)
        return metric
    except Exception as exc:
        return cached_metric(label, symbol, str(exc)) or unavailable_metric(label, symbol, str(exc))


def metric_from_manual(key: str, data: dict[str, Any]) -> dict[str, Any]:
    indexes = data.get("indexes", {})
    raw = indexes.get(key, {})
    label = raw.get("label") or key
    value = raw.get("value")
    change_pct = raw.get("change_pct")
    updated_at = raw.get("updated_at") or data.get("updated_at") or MISSING
    return {
        "label": label,
        "symbol": key,
        "value": format_number(value, 0 if key == "USDVND" else 2),
        "raw_value": value,
        "change": format_change(raw.get("change"), change_pct),
        "change_pct": change_pct,
        "tone": tone(float(change_pct)) if isinstance(change_pct, (int, float)) else "neutral",
        "note": raw.get("comment") or MISSING,
        "source": raw.get("source") or "manual_market_data.json",
        "updated_at": updated_at,
        "as_of": updated_at,
        "technical": {"available": False, "message": MISSING},
    }


def manual_card(label: str, value: Any, note: str, updated_at: str, unit: str = "") -> dict[str, Any]:
    display = MISSING if value in (None, "") else f"{format_number(value)}{unit}"
    return {
        "label": label,
        "symbol": label,
        "value": display,
        "raw_value": value,
        "change": MISSING,
        "change_pct": None,
        "tone": "neutral",
        "note": note or MISSING,
        "source": "manual_market_data.json",
        "updated_at": updated_at or MISSING,
        "as_of": updated_at or MISSING,
        "technical": {"available": False, "message": MISSING},
    }


def collect_global_markets() -> list[dict[str, Any]]:
    return [fetch_google_finance_metric(label, symbol) | {"group": group} for label, symbol, group in GLOBAL_SYMBOLS]


def collect_vietnam_markets(manual: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key in VIETNAM_KEYS:
        metric = metric_from_manual(key, manual)
        if key == "USDVND" and metric["value"] == MISSING:
            metric = fetch_google_finance_metric("USD/VND", "USD-VND")
        rows.append(metric)
    updated_at = manual.get("updated_at") or MISSING
    liquidity = manual.get("liquidity", {})
    foreign = manual.get("foreign_flow", {})
    proprietary = manual.get("proprietary_flow", {})
    interbank = manual.get("interbank_rate", {})
    rows.extend(
        [
            manual_card("Thanh khoản HOSE", liquidity.get("value"), liquidity.get("comment"), updated_at, f" {liquidity.get('unit', 'tỷ đồng')}"),
            manual_card("Khối ngoại", foreign.get("net_value"), foreign.get("comment"), updated_at, f" {foreign.get('unit', 'tỷ đồng')}"),
            manual_card("Tự doanh", proprietary.get("net_value"), proprietary.get("comment"), updated_at, f" {proprietary.get('unit', 'tỷ đồng')}"),
            manual_card("Lãi suất liên ngân hàng", interbank.get("value"), interbank.get("comment", MISSING), updated_at, f" {interbank.get('unit', '%')}"),
        ]
    )
    return rows


def collect_watchlist_market_data(watchlist: list[dict[str, Any]], limit: int = 10) -> dict[str, dict[str, Any]]:
    # Google Finance không có coverage ổn định cho toàn bộ mã Việt Nam dạng API công khai.
    # Vùng kỹ thuật của watchlist được lấy từ data/watchlist.json khi thiếu dữ liệu tự động.
    return {}


def collect_market_data() -> dict[str, Any]:
    manual = load_json(DATA_DIR / "manual_market_data.json", {})
    watchlist = load_json(DATA_DIR / "watchlist.json", {}).get("tickers", [])
    fetched_at = now_utc()
    manual_updated_at = manual.get("updated_at") or MISSING

    global_markets = collect_global_markets()
    vietnam_markets = collect_vietnam_markets(manual)
    automated_watchlist = collect_watchlist_market_data(watchlist)

    return {
        "fetched_at": fetched_at,
        "updated_at": fetched_at,
        "vietnam_markets": vietnam_markets,
        "global_markets": global_markets,
        "market_breadth": manual.get("market_breadth", {"comment": MISSING, "updated_at": manual_updated_at}),
        "liquidity": manual.get("liquidity", {"comment": MISSING, "updated_at": manual_updated_at}),
        "foreign_flow": manual.get("foreign_flow", {"comment": MISSING, "updated_at": manual_updated_at}),
        "proprietary_flow": manual.get("proprietary_flow", {"comment": MISSING, "updated_at": manual_updated_at}),
        "interbank_rate": manual.get("interbank_rate", {"comment": MISSING, "updated_at": manual_updated_at}),
        "sector_flow": manual.get("sector_flow", []),
        "top_gainers": manual.get("top_gainers", []),
        "top_losers": manual.get("top_losers", []),
        "watchlist_prices": manual.get("watchlist_prices", {}),
        "automated_watchlist": automated_watchlist,
        "manual_updated_at": manual_updated_at,
        "sources": [
            {
                "name": "Google Finance",
                "url": "https://www.google.com/finance/",
                "used_for": "Chỉ số quốc tế, hàng hóa, crypto và tỷ giá USD/VND nếu truy cập được.",
                "fetched_at": fetched_at,
                "updated_at": fetched_at,
            },
            {
                "name": "manual_market_data.json",
                "url": "data/manual_market_data.json",
                "used_for": "Dữ liệu Việt Nam, dòng tiền, độ rộng, thanh khoản và phần thiếu từ nguồn tự động.",
                "fetched_at": fetched_at,
                "updated_at": manual_updated_at,
            },
        ],
    }
