import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sistema_atividades.constants import DEFAULT_AUTO_LOCK_MINUTES
from sistema_atividades.paths import get_attachments_dir, get_data_dir, get_db_path


RECORD_COLUMNS = [
    "category",
    "doc_number",
    "record_date",
    "interested",
    "origin",
    "subject",
    "status",
    "tags",
    "notes",
    "protocol_process_number",
    "protocol_court",
    "protocol_deadline_date",
    "protocol_deadline_status",
    "convocation_date",
    "convocation_location",
    "convocation_person",
    "convocation_attended",
    "convocation_justification",
    "schedule_datetime",
    "schedule_type",
    "schedule_location",
    "schedule_confirmed",
    "send_recipient",
    "send_medium",
    "send_date",
    "project_stage",
    "project_owner",
    "project_due_date",
    "project_status",
    "created_at",
    "updated_at",
]


def ensure_dirs() -> None:
    get_data_dir().mkdir(parents=True, exist_ok=True)
    get_attachments_dir().mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    ensure_dirs()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    ensure_dirs()
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                doc_number TEXT,
                record_date TEXT NOT NULL,
                interested TEXT,
                origin TEXT,
                subject TEXT,
                status TEXT,
                tags TEXT,
                notes TEXT,
                protocol_process_number TEXT,
                protocol_court TEXT,
                protocol_deadline_date TEXT,
                protocol_deadline_status TEXT,
                convocation_date TEXT,
                convocation_location TEXT,
                convocation_person TEXT,
                convocation_attended INTEGER,
                convocation_justification TEXT,
                schedule_datetime TEXT,
                schedule_type TEXT,
                schedule_location TEXT,
                schedule_confirmed INTEGER,
                send_recipient TEXT,
                send_medium TEXT,
                send_date TEXT,
                project_stage TEXT,
                project_owner TEXT,
                project_due_date TEXT,
                project_status TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(record_id) REFERENCES records(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_records_date ON records(record_date)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_records_category ON records(category)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_records_status ON records(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_records_doc_number ON records(doc_number)"
        )
        conn.commit()

    if get_setting("auto_lock_minutes") is None:
        set_setting("auto_lock_minutes", str(DEFAULT_AUTO_LOCK_MINUTES))


def get_setting(key: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()


def get_password_hash() -> Optional[str]:
    return get_setting("password_hash")


def set_password_hash(password_hash: str) -> None:
    set_setting("password_hash", password_hash)


def get_auto_lock_minutes() -> int:
    value = get_setting("auto_lock_minutes")
    if value is None:
        return DEFAULT_AUTO_LOCK_MINUTES
    try:
        return max(0, int(value))
    except ValueError:
        return DEFAULT_AUTO_LOCK_MINUTES


def set_auto_lock_minutes(minutes: int) -> None:
    set_setting("auto_lock_minutes", str(max(0, minutes)))


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row) if row else {}


def create_record(data: Dict[str, Any]) -> int:
    now = datetime.utcnow().isoformat()
    record = {col: data.get(col) for col in RECORD_COLUMNS}
    record["created_at"] = now
    record["updated_at"] = now
    columns = ", ".join(RECORD_COLUMNS)
    placeholders = ", ".join(["?"] * len(RECORD_COLUMNS))
    values = [record[col] for col in RECORD_COLUMNS]

    with get_connection() as conn:
        cur = conn.execute(
            f"INSERT INTO records ({columns}) VALUES ({placeholders})", values
        )
        conn.commit()
        return int(cur.lastrowid)


def update_record(record_id: int, data: Dict[str, Any]) -> None:
    record = {col: data.get(col) for col in RECORD_COLUMNS if col not in {"created_at"}}
    record["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join([f"{col} = ?" for col in record.keys()])
    values = list(record.values()) + [record_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE records SET {set_clause} WHERE id = ?", values)
        conn.commit()


def delete_record(record_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM attachments WHERE record_id = ?", (record_id,))
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()


def get_record(record_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        return _row_to_dict(row) if row else None


def list_attachments(record_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM attachments WHERE record_id = ? ORDER BY id",
            (record_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def add_attachment(record_id: int, file_name: str, stored_path: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO attachments (record_id, file_name, stored_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (record_id, file_name, stored_path, now),
        )
        conn.commit()
        return int(cur.lastrowid)


def delete_attachment(attachment_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
        conn.commit()


def find_similar_records(doc_number: str, year: int, month: int) -> List[Dict[str, Any]]:
    if not doc_number:
        return []
    start = date(year, month, 1)
    end = start + timedelta(days=32)
    end = date(end.year, end.month, 1) - timedelta(days=1)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM records
            WHERE doc_number = ?
              AND record_date BETWEEN ? AND ?
            ORDER BY record_date DESC
            """,
            (doc_number, start.isoformat(), end.isoformat()),
        ).fetchall()
        return [dict(row) for row in rows]


def list_records(
    search: str = "",
    category: Optional[str] = None,
    status: Optional[str] = None,
    tags: str = "",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    order_by: str = "record_date DESC, id DESC",
) -> List[Dict[str, Any]]:
    where = ["1=1"]
    params: List[Any] = []

    if category and category != "Todos":
        where.append("category = ?")
        params.append(category)

    if status and status != "Todos":
        where.append("status = ?")
        params.append(status)

    if date_from:
        where.append("record_date >= ?")
        params.append(date_from)

    if date_to:
        where.append("record_date <= ?")
        params.append(date_to)

    if tags:
        where.append("tags LIKE ?")
        params.append(f"%{tags}%")

    if search:
        where.append(
            "("
            "doc_number LIKE ? OR subject LIKE ? OR interested LIKE ? "
            "OR origin LIKE ? OR record_date LIKE ? OR category LIKE ? "
            "OR status LIKE ? OR tags LIKE ? OR protocol_process_number LIKE ?"
            ")"
        )
        like = f"%{search}%"
        params.extend([like] * 9)

    query = f"SELECT * FROM records WHERE {' AND '.join(where)} ORDER BY {order_by}"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def list_records_in_month(year: int, month: int) -> List[Dict[str, Any]]:
    start = date(year, month, 1)
    end = start + timedelta(days=32)
    end = date(end.year, end.month, 1) - timedelta(days=1)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM records
            WHERE record_date BETWEEN ? AND ?
            ORDER BY record_date ASC
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [dict(row) for row in rows]


def list_records_in_year(year: int) -> List[Dict[str, Any]]:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM records
            WHERE record_date BETWEEN ? AND ?
            ORDER BY record_date ASC
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [dict(row) for row in rows]


def get_counts_by_category(year: int, month: int) -> Dict[str, int]:
    records = list_records_in_month(year, month)
    result: Dict[str, int] = {}
    for rec in records:
        result[rec["category"]] = result.get(rec["category"], 0) + 1
    return result


def get_counts_by_status(year: int, month: int) -> Dict[str, int]:
    records = list_records_in_month(year, month)
    result: Dict[str, int] = {}
    for rec in records:
        result[rec["status"]] = result.get(rec["status"], 0) + 1
    return result


def get_counts_by_day(year: int, month: int) -> Dict[int, int]:
    records = list_records_in_month(year, month)
    result: Dict[int, int] = {}
    for rec in records:
        try:
            rec_date = datetime.fromisoformat(rec["record_date"]).date()
        except ValueError:
            continue
        if rec_date.month != month or rec_date.year != year:
            continue
        result[rec_date.day] = result.get(rec_date.day, 0) + 1
    return result


def get_annual_monthly_totals(year: int) -> Dict[int, int]:
    records = list_records_in_year(year)
    result: Dict[int, int] = {m: 0 for m in range(1, 13)}
    for rec in records:
        try:
            rec_date = datetime.fromisoformat(rec["record_date"]).date()
        except ValueError:
            continue
        if rec_date.year == year:
            result[rec_date.month] += 1
    return result


def get_annual_category_totals(year: int) -> Dict[str, int]:
    records = list_records_in_year(year)
    result: Dict[str, int] = {}
    for rec in records:
        result[rec["category"]] = result.get(rec["category"], 0) + 1
    return result


def get_annual_status_totals(year: int) -> Dict[str, int]:
    records = list_records_in_year(year)
    result: Dict[str, int] = {}
    for rec in records:
        result[rec["status"]] = result.get(rec["status"], 0) + 1
    return result


def get_deadline_highlights(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    today = date.today()
    highlights: List[Dict[str, Any]] = []
    for rec in records:
        deadline = rec.get("protocol_deadline_date")
        if not deadline:
            continue
        try:
            deadline_date = datetime.fromisoformat(deadline).date()
        except ValueError:
            continue
        delta = (deadline_date - today).days
        if delta < 0:
            rec["deadline_status"] = "Atrasado"
            highlights.append(rec)
        elif delta <= 7:
            rec["deadline_status"] = "Alerta"
            highlights.append(rec)
    return highlights


def seed_sample_data() -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(1) AS total FROM records").fetchone()
        total = row["total"] if row else 0
        if total and total > 0:
            return

    samples = [
        {
            "category": "Protocolos Judiciais",
            "doc_number": "PJ-2026-0001",
            "record_date": date.today().isoformat(),
            "interested": "Maria Souza",
            "origin": "Vara Civel",
            "subject": "Intimacao",
            "status": "Aberto",
            "tags": "prazo,urgente",
            "notes": "Aguardar cumprimento do prazo.",
            "protocol_process_number": "0001234-56.2026.8.01.0001",
            "protocol_court": "Comarca Central",
            "protocol_deadline_date": (date.today() + timedelta(days=5)).isoformat(),
            "protocol_deadline_status": "Alerta",
        },
        {
            "category": "Informacoes",
            "doc_number": "INF-2026-010",
            "record_date": date.today().isoformat(),
            "interested": "Carlos Lima",
            "origin": "Ouvidoria",
            "subject": "Pedido de informacao",
            "status": "Em andamento",
            "tags": "retorno",
            "notes": "Responder ate sexta-feira.",
            "send_recipient": "Ouvidoria Geral",
            "send_medium": "E-mail",
        },
        {
            "category": "Oficios",
            "doc_number": "OF-2026-077",
            "record_date": (date.today() - timedelta(days=1)).isoformat(),
            "interested": "Secretaria X",
            "origin": "SEI",
            "subject": "Solicitacao de dados",
            "status": "Concluido",
            "tags": "documento",
            "notes": "Dados enviados.",
            "send_recipient": "Secretaria X",
            "send_medium": "SEI",
            "send_date": (date.today() - timedelta(days=1)).isoformat(),
        },
        {
            "category": "Convocacoes",
            "doc_number": "CONV-2026-002",
            "record_date": (date.today() - timedelta(days=2)).isoformat(),
            "interested": "Joao Pereira",
            "origin": "RH",
            "subject": "Convocacao para reuniao",
            "status": "Aberto",
            "tags": "reuniao",
            "notes": "Confirmar presenca.",
            "convocation_date": (date.today() + timedelta(days=3)).isoformat(),
            "convocation_location": "Sala 2",
            "convocation_person": "Joao Pereira",
            "convocation_attended": 0,
        },
        {
            "category": "Agendamentos",
            "doc_number": "AG-2026-009",
            "record_date": (date.today() - timedelta(days=3)).isoformat(),
            "interested": "Ana Costa",
            "origin": "Protocolo",
            "subject": "Consulta medica",
            "status": "Em andamento",
            "tags": "saude",
            "notes": "Confirmar horario.",
            "schedule_datetime": (
                datetime.now() + timedelta(days=2)
            ).replace(second=0, microsecond=0).isoformat(sep=" "),
            "schedule_type": "Medico",
            "schedule_location": "Clinica Central",
            "schedule_confirmed": 1,
        },
        {
            "category": "Despachos",
            "doc_number": "DESP-2026-014",
            "record_date": (date.today() - timedelta(days=4)).isoformat(),
            "interested": "Setor Financeiro",
            "origin": "Diretoria",
            "subject": "Despacho interno",
            "status": "Arquivado",
            "tags": "interno",
            "notes": "Despacho arquivado.",
            "send_recipient": "Diretoria",
            "send_medium": "Outro",
        },
        {
            "category": "Memorandos",
            "doc_number": "MEM-2026-031",
            "record_date": (date.today() - timedelta(days=5)).isoformat(),
            "interested": "Equipe A",
            "origin": "Gerencia",
            "subject": "Memorando semanal",
            "status": "Concluido",
            "tags": "rotina",
            "notes": "Ciente.",
            "send_recipient": "Equipe A",
            "send_medium": "E-mail",
            "send_date": (date.today() - timedelta(days=5)).isoformat(),
        },
        {
            "category": "Projetos",
            "doc_number": "PROJ-2026-001",
            "record_date": (date.today() - timedelta(days=6)).isoformat(),
            "interested": "Projeto Alfa",
            "origin": "Planejamento",
            "subject": "Implantacao sistema",
            "status": "Em andamento",
            "tags": "estrategico",
            "notes": "Em fase de analise.",
            "project_stage": "Planejamento",
            "project_owner": "Luciana",
            "project_due_date": (date.today() + timedelta(days=60)).isoformat(),
            "project_status": "Em andamento",
        },
        {
            "category": "Outros",
            "doc_number": "OUT-2026-005",
            "record_date": (date.today() - timedelta(days=7)).isoformat(),
            "interested": "Arquivo Geral",
            "origin": "Setor B",
            "subject": "Registro diverso",
            "status": "Aberto",
            "tags": "diverso",
            "notes": "Acompanhar.",
        },
        {
            "category": "Protocolos Judiciais",
            "doc_number": "PJ-2026-0002",
            "record_date": (date.today() - timedelta(days=8)).isoformat(),
            "interested": "Paulo Mendes",
            "origin": "Vara Criminal",
            "subject": "Notificacao",
            "status": "Em andamento",
            "tags": "prazo",
            "notes": "Analisar documentos.",
            "protocol_process_number": "0009876-12.2026.8.01.0002",
            "protocol_court": "Comarca Norte",
            "protocol_deadline_date": (date.today() - timedelta(days=1)).isoformat(),
            "protocol_deadline_status": "Atrasado",
        },
    ]

    for sample in samples:
        sample.setdefault("record_date", date.today().isoformat())
        sample.setdefault("status", "Aberto")
        create_record(sample)
