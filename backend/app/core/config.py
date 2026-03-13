import os
from functools import lru_cache
from pathlib import Path


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#") or "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


class Settings:
    def __init__(self) -> None:
        self.apify_token = os.getenv("APIFY_TOKEN", "")
        self.apify_actor_id = os.getenv("APIFY_ACTOR_ID", "sama4/greentrace-scrapper")
        self.apify_timeout_secs = int(os.getenv("APIFY_TIMEOUT_SECS", "300"))


@lru_cache
def get_settings() -> Settings:
    return Settings()