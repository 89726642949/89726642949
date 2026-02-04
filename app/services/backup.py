import os
import shutil
import zipfile

from .utils import base_dir, data_dir, attachments_dir, ensure_dirs


def create_backup(zip_path: str) -> None:
    ensure_dirs()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        db_file = os.path.join(data_dir(), "app.db")
        if os.path.exists(db_file):
            zf.write(db_file, arcname=os.path.join("data", "app.db"))
        if os.path.isdir(attachments_dir()):
            for root, _, files in os.walk(attachments_dir()):
                for name in files:
                    full_path = os.path.join(root, name)
                    rel_path = os.path.relpath(full_path, base_dir())
                    zf.write(full_path, arcname=rel_path)


def restore_backup(zip_path: str) -> None:
    ensure_dirs()
    # Clear existing data/attachments to avoid stale files
    if os.path.isdir(data_dir()):
        shutil.rmtree(data_dir(), ignore_errors=True)
    if os.path.isdir(attachments_dir()):
        shutil.rmtree(attachments_dir(), ignore_errors=True)
    os.makedirs(data_dir(), exist_ok=True)
    os.makedirs(attachments_dir(), exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(base_dir())
