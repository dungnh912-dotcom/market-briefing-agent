from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    reports_dir: Path = ROOT_DIR / "reports"
    lookback_days: int = int(os.getenv("LOOKBACK_DAYS", "180"))
    newsapi_key: str | None = os.getenv("NEWSAPI_KEY") or None
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    github_token: str | None = os.getenv("GITHUB_TOKEN") or None
    github_model: str = os.getenv("GITHUB_MODEL", "openai/gpt-4.1-mini")
    global_symbols: list[str] = field(
        default_factory=lambda: ["SPY", "QQQ", "DIA", "GLD", "USO", "TLT", "BTC-USD"]
    )
    vietnam_watchlist: list[str] = field(
        default_factory=lambda: [
            "VCB", "BID", "CTG", "TCB", "MBB", "ACB",
            "SSI", "VND", "HCM", "VCI",
            "VHM", "VIC", "KDH", "NLG", "DXG",
            "HPG", "HSG", "NKG",
            "GAS", "PVD", "PVS",
            "MWG", "FRT", "PNJ", "FPT", "GMD",
            "VHC", "ANV", "TNG", "STK",
            "VCG", "HHV", "CII", "LCG",
        ]
    )


def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    return settings
