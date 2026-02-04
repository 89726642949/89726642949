from typing import Any, Dict, List, Optional, Tuple

from .db import Database, update_timestamps, get_setting
from .utils import normalize_tags


CATEGORIES = [
    "Protocolos Judiciais",
    "Informacoes",
    "Oficios",
    "Convocacoes",
    "Agendamentos",
    "Despachos",
    "Memorandos",
    "Projetos",
    "Outros",
]


STATUSES = ["Aberto", "Em andamento", "Concluido", "Arquivado"]


def get_outros_label(db: Database) -> str:
    return get_setting(db, "custom_outros_name", "Outros") or "Outros"


def get_categories(db: Database) -> List[str]:
    custom_outros = get_outros_label(db)
    categories = CATEGORIES[:-1] + [custom_outros]
    return categories


def to_storage_category(db: Database, category: str) -> str:
    custom_outros = get_outros_label(db)
    if category == custom_outros:
        return "Outros"
    return category


def to_display_category(db: Database, category: str) -> str:
    if category == "Outros":
        return get_outros_label(db)
    return category


def insert_record(db: Database, values: Dict[str, Any]) -> int:
    values = update_timestamps(values, is_new=True)
    values["tags"] = normalize_tags(values.get("tags", ""))
    columns = ", ".join(values.keys())
    placeholders = ", ".join(["?"] * len(values))
    sql = f"INSERT INTO records ({columns}) VALUES ({placeholders})"
    cur = db.execute(sql, tuple(values.values()))
    return int(cur.lastrowid)


def update_record(db: Database, record_id: int, values: Dict[str, Any]) -> None:
    values = update_timestamps(values, is_new=False)
    values["tags"] = normalize_tags(values.get("tags", ""))
    sets = ", ".join([f"{k} = ?" for k in values.keys()])
    sql = f"UPDATE records SET {sets} WHERE id = ?"
    db.execute(sql, tuple(values.values()) + (record_id,))


def delete_record(db: Database, record_id: int) -> None:
    db.execute("DELETE FROM records WHERE id = ?", (record_id,))


def get_record(db: Database, record_id: int) -> Optional[Dict[str, Any]]:
    row = db.fetchone("SELECT * FROM records WHERE id = ?", (record_id,))
    return dict(row) if row else None


def search_records(
    db: Database,
    query: str = "",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    order_by: str = "record_date DESC, id DESC",
) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM records WHERE 1=1"
    params: List[Any] = []
    if query:
        sql += " AND (doc_number LIKE ? OR subject LIKE ? OR interested LIKE ? OR origin LIKE ?)"
        like = f"%{query}%"
        params += [like, like, like, like]
    if date_from:
        sql += " AND record_date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND record_date <= ?"
        params.append(date_to)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if tags:
        for tag in tags:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag}%")
    sql += f" ORDER BY {order_by}"
    rows = db.fetchall(sql, tuple(params))
    return [dict(r) for r in rows]


def find_similar(
    db: Database,
    doc_number: str,
    record_date: str,
    category: str,
    exclude_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM records WHERE doc_number = ? AND record_date = ? AND category = ?"
    params: List[Any] = [doc_number, record_date, category]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    rows = db.fetchall(sql, tuple(params))
    return [dict(r) for r in rows]


def count_by_category(db: Database, year: int, month: int) -> List[Tuple[str, int]]:
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-31"
    rows = db.fetchall(
        """
        SELECT category, COUNT(*) as total
        FROM records
        WHERE record_date BETWEEN ? AND ?
        GROUP BY category
        ORDER BY total DESC
        """,
        (start, end),
    )
    return [(r["category"], r["total"]) for r in rows]


def count_by_status(db: Database, year: int, month: int) -> List[Tuple[str, int]]:
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-31"
    rows = db.fetchall(
        """
        SELECT status, COUNT(*) as total
        FROM records
        WHERE record_date BETWEEN ? AND ?
        GROUP BY status
        ORDER BY total DESC
        """,
        (start, end),
    )
    return [(r["status"], r["total"]) for r in rows]


def count_total_month(db: Database, year: int, month: int) -> int:
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-31"
    row = db.fetchone(
        "SELECT COUNT(*) as total FROM records WHERE record_date BETWEEN ? AND ?",
        (start, end),
    )
    return int(row["total"]) if row else 0


def count_per_day(db: Database, year: int, month: int) -> List[Tuple[int, int]]:
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-31"
    rows = db.fetchall(
        """
        SELECT substr(record_date, 9, 2) as day, COUNT(*) as total
        FROM records
        WHERE record_date BETWEEN ? AND ?
        GROUP BY day
        ORDER BY day ASC
        """,
        (start, end),
    )
    return [(int(r["day"]), r["total"]) for r in rows]


def totals_by_month(db: Database, year: int) -> List[Tuple[int, int]]:
    rows = db.fetchall(
        """
        SELECT substr(record_date, 6, 2) as month, COUNT(*) as total
        FROM records
        WHERE substr(record_date, 1, 4) = ?
        GROUP BY month
        ORDER BY month ASC
        """,
        (f"{year:04d}",),
    )
    return [(int(r["month"]), r["total"]) for r in rows]


def totals_by_category_year(db: Database, year: int) -> List[Tuple[str, int]]:
    rows = db.fetchall(
        """
        SELECT category, COUNT(*) as total
        FROM records
        WHERE substr(record_date, 1, 4) = ?
        GROUP BY category
        ORDER BY total DESC
        """,
        (f"{year:04d}",),
    )
    return [(r["category"], r["total"]) for r in rows]


def totals_by_status_year(db: Database, year: int) -> List[Tuple[str, int]]:
    rows = db.fetchall(
        """
        SELECT status, COUNT(*) as total
        FROM records
        WHERE substr(record_date, 1, 4) = ?
        GROUP BY status
        ORDER BY total DESC
        """,
        (f"{year:04d}",),
    )
    return [(r["status"], r["total"]) for r in rows]


def records_for_month(db: Database, year: int, month: int) -> List[Dict[str, Any]]:
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-31"
    rows = db.fetchall(
        "SELECT * FROM records WHERE record_date BETWEEN ? AND ? ORDER BY record_date ASC",
        (start, end),
    )
    return [dict(r) for r in rows]


def records_for_year(db: Database, year: int) -> List[Dict[str, Any]]:
    rows = db.fetchall(
        "SELECT * FROM records WHERE substr(record_date, 1, 4) = ? ORDER BY record_date ASC",
        (f"{year:04d}",),
    )
    return [dict(r) for r in rows]
