import os
import logging
from datetime import datetime, date


APP_NAME = "Sistema de Atividades"


def base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def data_dir() -> str:
    return os.path.join(base_dir(), "data")


def attachments_dir() -> str:
    return os.path.join(base_dir(), "attachments")


def reports_dir() -> str:
    return os.path.join(base_dir(), "reports")


def logs_dir() -> str:
    return os.path.join(base_dir(), "logs")


def ensure_dirs() -> None:
    for path in [data_dir(), attachments_dir(), reports_dir(), logs_dir()]:
        os.makedirs(path, exist_ok=True)


def setup_logging() -> None:
    ensure_dirs()
    log_path = os.path.join(logs_dir(), "app.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_datetime(value: str):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def normalize_tags(text: str) -> str:
    if not text:
        return ""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    return ", ".join(sorted(set(parts)))


def split_tags(text: str):
    if not text:
        return []
    return [p.strip() for p in text.split(",") if p.strip()]
