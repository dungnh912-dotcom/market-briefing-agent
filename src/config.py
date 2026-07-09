from __future__ import annotations

from dataclasses import dataclass, field
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    timezone: str = os.getenv("TZ", "Asia/Ho_Chi_Minh")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")
    public_dir: str = os.getenv("PUBLIC_DIR", "public")
    template_path: str = os.getenv("TEMPLATE_PATH", "templates/report.html.j2")
    lookback_days: int = int(os.getenv("LOOKBACK_DAYS", "10"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "12"))
    request_retries: int = int(os.getenv("REQUEST_RETRIES", "3"))
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    market_symbols: dict[str, str] = field(
        default_factory=lambda: {
            "VN-Index": "^VNINDEX",
            "HNX-Index": "HNX.VN",
            "VN30": "VN30.VN",
            "S&P 500": "^GSPC",
            "Nasdaq": "^IXIC",
            "Dow Jones": "^DJI",
            "Nikkei 225": "^N225",
            "Dầu Brent": "BZ=F",
            "DXY": "DX-Y.NYB",
            "UST 10Y": "^TNX",
            "Vàng": "GC=F",
            "Bitcoin": "BTC-USD",
        }
    )
    rss_feeds: list[str] = field(
        default_factory=lambda: [
            "https://news.google.com/rss/search?q=chung+khoan+Viet+Nam&hl=vi&gl=VN&ceid=VN:vi",
            "https://news.google.com/rss/search?q=VN-Index+thi+truong+chung+khoan&hl=vi&gl=VN&ceid=VN:vi",
            "https://news.google.com/rss/search?q=kinh+te+vi+mo+Viet+Nam&hl=vi&gl=VN&ceid=VN:vi",
            "https://news.google.com/rss/search?q=stock+market+Fed+oil+China&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=geopolitics+markets+oil+Asia&hl=en-US&gl=US&ceid=US:en",
        ]
    )


def load_settings() -> Settings:
    return Settings()
