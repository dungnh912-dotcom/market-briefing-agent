from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scripts.html_renderer import render_index
except ImportError:
    from html_renderer import render_index

ROOT = Path(__file__).resolve().parents[1]
BANTIN_DIR = ROOT / "bantin"


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def date_label(date_text: str) -> str:
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return date_text


def build_archive_items(prefix: str = "") -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for html_path in sorted(BANTIN_DIR.glob("20*.html"), reverse=True):
        json_path = html_path.with_suffix(".json")
        data = load_json(json_path)
        briefing = data.get("briefing", {})
        items.append(
            {
                "href": f"{prefix}{html_path.name}",
                "date": html_path.stem,
                "date_label": briefing.get("date_label") or date_label(html_path.stem),
                "title": briefing.get("title") or "Bản tin thị trường",
                "subtitle": briefing.get("subtitle") or "Daily Market Briefing for Vietnamese Brokers",
            }
        )
    return items


def write_indexes(brand: dict[str, str]) -> None:
    BANTIN_DIR.mkdir(exist_ok=True)
    root_items = build_archive_items(prefix="bantin/")
    bantin_items = build_archive_items(prefix="")
    latest_root = root_items[0]["href"] if root_items else ""
    latest_bantin = bantin_items[0]["href"] if bantin_items else ""
    (ROOT / "index.html").write_text(render_index(root_items, brand, latest_root, asset_prefix=""), encoding="utf-8")
    (BANTIN_DIR / "index.html").write_text(render_index(bantin_items, brand, latest_bantin, asset_prefix="../"), encoding="utf-8")


if __name__ == "__main__":
    write_indexes(
        {
            "name": "HDINVEST",
            "site_name": "HDINVEST Daily Market Briefing",
            "footer": "HDINVEST Research",
        }
    )
