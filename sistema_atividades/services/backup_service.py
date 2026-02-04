import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Tuple

from sistema_atividades.paths import get_base_dir, get_data_dir, get_db_path


def create_backup(zip_path: Path) -> Tuple[bool, str]:
    data_dir = get_data_dir()
    db_path = get_db_path()
    if not db_path.exists():
        return False, "Banco de dados nao encontrado."

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in data_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(get_base_dir())
                    zf.write(file_path, arcname.as_posix())
            meta = {"created_at": datetime.utcnow().isoformat(), "version": "1.0.0"}
            zf.writestr("backup_metadata.json", json.dumps(meta, indent=2))
        return True, "Backup criado com sucesso."
    except (OSError, zipfile.BadZipFile) as exc:
        return False, f"Erro ao criar backup: {exc}"


def restore_backup(zip_path: Path) -> Tuple[bool, str]:
    if not zip_path.exists():
        return False, "Arquivo de backup nao encontrado."
    try:
        data_dir = get_data_dir()
        if data_dir.exists():
            shutil.rmtree(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(get_base_dir())
        return True, "Backup restaurado. Reinicie o aplicativo."
    except (OSError, zipfile.BadZipFile) as exc:
        return False, f"Erro ao restaurar backup: {exc}"
