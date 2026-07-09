from __future__ import annotations

from datetime import datetime
import json
import logging
import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def vietnam_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))


def vietnamese_date_label(dt: datetime) -> str:
    weekdays = {
        0: "THỨ HAI",
        1: "THỨ BA",
        2: "THỨ TƯ",
        3: "THỨ NĂM",
        4: "THỨ SÁU",
        5: "THỨ BẢY",
        6: "CHỦ NHẬT",
    }
    return f"{weekdays[dt.weekday()]} · {dt:%d.%m.%Y}"


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def get_with_retry(url: str, *, timeout: int, retries: int) -> requests.Response | None:
    logger = logging.getLogger(__name__)
    headers = {"User-Agent": "market-briefing-agent/1.0"}
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            logger.warning("HTTP error %s/%s for %s: %s", attempt, retries, url, exc)
            if attempt < retries:
                time.sleep(1.5 * attempt)
    return None
