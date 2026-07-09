from __future__ import annotations

from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent))

from ai_writer import write_briefing
from collect_data import collect_all
from config import load_settings
from render_html import render_report
from utils import setup_logging, vietnam_now, write_json


def main() -> None:
    setup_logging()
    settings = load_settings()
    report_date = vietnam_now()

    data = collect_all(settings, report_date)
    briefing = write_briefing(data, settings)

    reports_dir = Path(settings.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / f"{report_date.date().isoformat()}.json"
    write_json(json_path, data)

    html_path = render_report(
        briefing=briefing,
        data=data,
        report_date=report_date,
        template_path=settings.template_path,
        reports_dir=settings.reports_dir,
        public_dir=settings.public_dir,
    )
    print(f"Generated {html_path} and {json_path}")


if __name__ == "__main__":
    main()
