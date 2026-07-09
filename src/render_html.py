from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from .utils import ensure_dir, vietnamese_date_label
except ImportError:
    from utils import ensure_dir, vietnamese_date_label


def render_report(
    *,
    briefing: dict[str, Any],
    data: dict[str, Any],
    report_date,
    template_path: str,
    reports_dir: str,
    public_dir: str,
) -> Path:
    template_file = Path(template_path)
    env = Environment(
        loader=FileSystemLoader(str(template_file.parent)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )
    template = env.get_template(template_file.name)
    html = template.render(
        briefing=briefing,
        data=data,
        date_label=vietnamese_date_label(report_date),
        report_date=report_date.date().isoformat(),
        dashboard=build_dashboard(data),
    )

    reports_path = ensure_dir(reports_dir)
    public_path = ensure_dir(public_dir)
    report_path = reports_path / f"{report_date.date().isoformat()}.html"
    report_path.write_text(html, encoding="utf-8")
    (public_path / "index.html").write_text(html, encoding="utf-8")
    return report_path


def build_dashboard(data: dict[str, Any]) -> list[dict[str, Any]]:
    dashboard = []
    for flow in data.get("domestic_flows", []):
        dashboard.append(
            {
                "label": flow["label"],
                "display": flow["value"],
                "direction": "●",
                "change_display": flow.get("note", ""),
            }
        )
    for item in data.get("market_data", []):
        dashboard.append(
            {
                "label": item["label"],
                "display": item.get("display", "chưa có dữ liệu"),
                "direction": item.get("direction", "●"),
                "change_display": item.get("change_display") or item.get("note") or "",
            }
        )
    return dashboard
