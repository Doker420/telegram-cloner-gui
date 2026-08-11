"""Глобальная конфигурация приложения: пути, настройки, контакты."""
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = BASE_DIR / "sessions"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

for d in (DATA_DIR, SESSIONS_DIR):
    d.mkdir(exist_ok=True)

# ---------- Контакты разработчика ----------
DEV_NAME = "doker420"
DEV_TELEGRAM = "https://t.me/doker420"
DEV_GITHUB = "https://github.com/doker420"
DEV_GITHUB_LOGO = f"{DEV_GITHUB}.png"  # аватар GitHub

DEFAULT_SETTINGS = {
    "api_id": "",
    "api_hash": "",
    "bot_link": "https://t.me/your_bot",
    "hashtags": ["#крипта", "#LTC", "#бонус", "#промокод"],
    "delay_min": 2.0,
    "delay_max": 8.0,
    "clear_target": True,
    "theme": "dark",            # dark | light | custom
    "accent_color": "#7c4dff",
    "bg_color": "#181a20",
    "text_color": "#e6e6f0",
    "font_size": 13,
}


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_SETTINGS)
            merged.update(data)
            return merged
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_accounts() -> list:
    if ACCOUNTS_FILE.exists():
        try:
            return json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_accounts(accounts: list) -> None:
    ACCOUNTS_FILE.write_text(
        json.dumps(accounts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
