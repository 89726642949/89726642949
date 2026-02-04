import os
from pathlib import Path


APP_DIR_NAME = "SistemaAtividades"


def get_base_dir() -> Path:
    appdata = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
    base = Path(appdata) if appdata else Path.home()
    return base / APP_DIR_NAME


def get_data_dir() -> Path:
    return get_base_dir() / "data"


def get_attachments_dir() -> Path:
    return get_data_dir() / "attachments"


def get_logs_dir() -> Path:
    return get_base_dir() / "logs"


def get_db_path() -> Path:
    return get_data_dir() / "app.db"
