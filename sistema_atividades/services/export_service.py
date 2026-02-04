from pathlib import Path
from typing import Dict, Iterable, List

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


EXPORT_COLUMNS = [
    ("id", "ID"),
    ("record_date", "Data"),
    ("category", "Categoria"),
    ("doc_number", "Numero"),
    ("subject", "Assunto"),
    ("status", "Status"),
    ("interested", "Interessado"),
    ("origin", "Origem"),
    ("tags", "Tags"),
]


def export_records_to_excel(records: Iterable[Dict], output_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Registros"

    headers = [col[1] for col in EXPORT_COLUMNS]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for record in records:
        row = [record.get(col[0], "") or "" for col in EXPORT_COLUMNS]
        ws.append(row)

    for col_cells in ws.columns:
        length = max(len(str(cell.value or "")) for cell in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(50, length + 2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
