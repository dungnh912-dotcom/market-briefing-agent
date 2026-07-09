from __future__ import annotations

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - dependency is optional at import time
    load_dotenv = None

try:
    from scripts.data_collector import collect_market_data
    from scripts.gemini_writer import write_briefing
    from scripts.html_renderer import render_briefing
    from scripts.news_collector import collect_news
    from scripts.update_index import write_indexes
except ImportError:
    from data_collector import collect_market_data
    from gemini_writer import write_briefing
    from html_renderer import render_briefing
    from news_collector import collect_news
    from update_index import write_indexes

ROOT = Path(__file__).resolve().parents[1]
BANTIN_DIR = ROOT / "bantin"
ASSETS_DIR = ROOT / "assets"
DATA_DIR = ROOT / "data"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def load_environment() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env")


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def brand_config() -> dict[str, str]:
    config = load_json(DATA_DIR / "config.json", {})
    return {
        "name": os.environ.get("BRAND_NAME", config.get("brand", "HDUNGINVEST")),
        "site_name": os.environ.get("SITE_NAME", config.get("site_name", "HDUNGINVEST Daily Research")),
        "footer": os.environ.get("FOOTER_TEXT", config.get("footer", "HDUNGINVEST")),
        "hotline": os.environ.get("CONTACT_PHONE", config.get("hotline", "0387337164")),
        "qr_path": os.environ.get("ZALO_QR_PATH", config.get("qr_path", "assets/qr-zalo.png")),
        "logo_path": os.environ.get("LOGO_PATH", config.get("logo_path", "assets/logo.png")),
    }


def load_watchlist() -> list[dict]:
    return load_json(DATA_DIR / "watchlist.json", {}).get("tickers", [])


def ensure_static_assets() -> None:
    ASSETS_DIR.mkdir(exist_ok=True)
    (ASSETS_DIR / "css").mkdir(exist_ok=True)
    png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")
    for filename in ["qr-zalo.png", "logo.png"]:
        path = ASSETS_DIR / filename
        if not path.exists():
            path.write_bytes(png)


def collect_sources(market_data: dict, news: dict) -> list[dict]:
    sources: list[dict] = []
    sources.extend(market_data.get("sources", []))
    sources.extend(news.get("sources", []))
    for error in news.get("errors", []):
        sources.append(
            {
                "name": error.get("name", "Nguồn tin"),
                "url": error.get("url") or "#",
                "used_for": f"Nguồn chưa truy cập được trong lần chạy này: {error.get('error', '')}",
                "fetched_at": news.get("fetched_at", ""),
                "updated_at": error.get("updated_at") or news.get("updated_at", ""),
            }
        )
    sources.extend(
        [
            {
                "name": "Vietstock / CafeF / VnEconomy",
                "url": "https://vietstock.vn/",
                "used_for": "Tin thị trường Việt Nam khi RSS/public page truy cập được hoặc khi người dùng bổ sung thủ công.",
                "fetched_at": news.get("fetched_at", ""),
                "updated_at": news.get("updated_at", ""),
            },
            {
                "name": "SBV",
                "url": "https://www.sbv.gov.vn/",
                "used_for": "Tham khảo tỷ giá và thông tin chính sách nếu được nhập vào dữ liệu thủ công.",
                "fetched_at": market_data.get("fetched_at", ""),
                "updated_at": market_data.get("updated_at", ""),
            },
        ]
    )
    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for source in sources:
        key = (source.get("name", ""), source.get("url", ""))
        if key not in seen:
            seen.add(key)
            source.setdefault("updated_at", source.get("fetched_at", ""))
            deduped.append(source)
    return deduped


def build_payload(now: datetime) -> dict:
    market_data = collect_market_data()
    news = collect_news()
    payload = {
        "date": now.date().isoformat(),
        "date_label": now.strftime("%d/%m/%Y"),
        "updated_at": now.isoformat(),
        "updated_label": f"Cập nhật lúc: {now.strftime('%H:%M')} {now.strftime('%d/%m/%Y')}, giờ Việt Nam",
        "brand": brand_config(),
        "market_data": market_data,
        "news": news,
        "watchlist": load_watchlist(),
    }
    payload["sources"] = collect_sources(market_data, news)
    return payload


def main() -> None:
    load_environment()
    now = datetime.now(VN_TZ)
    BANTIN_DIR.mkdir(exist_ok=True)
    ensure_static_assets()

    payload = build_payload(now)
    briefing = write_briefing(payload)
    html = render_briefing(briefing, payload)

    date_name = now.date().isoformat()
    html_path = BANTIN_DIR / f"{date_name}.html"
    json_path = BANTIN_DIR / f"{date_name}.json"
    html_path.write_text(html, encoding="utf-8")
    json_path.write_text(json.dumps({"payload": payload, "briefing": briefing}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_indexes(payload["brand"])
    print(f"Generated {html_path.relative_to(ROOT)}")
    ai_status = briefing.get("ai_status", {})
    print(f"AI mode: {ai_status.get('mode', 'unknown')} - {ai_status.get('message', '')}")


if __name__ == "__main__":
    main()
