from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates"


def jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_briefing(briefing: dict[str, Any], payload: dict[str, Any]) -> str:
    template = jinja_env().get_template("briefing_template.html")
    return template.render(briefing=briefing, payload=payload, brand=payload["brand"], asset_prefix="../")


def render_index(items: list[dict[str, Any]], brand: dict[str, str], latest_href: str = "", asset_prefix: str = "") -> str:
    template = jinja_env().get_template("index_template.html")
    return template.render(items=items, brand=brand, latest_href=latest_href, asset_prefix=asset_prefix)
