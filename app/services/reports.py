import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import xlsxwriter

from .records import (
    count_by_category,
    count_by_status,
    count_total_month,
    records_for_month,
    records_for_year,
    totals_by_month,
    totals_by_category_year,
    totals_by_status_year,
)
from .utils import reports_dir


def _table(data: List[List[str]]):
    tbl = Table(data, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return tbl


def _deadline_highlights(records: List[Dict]) -> List[Dict]:
    highlights = []
    today = date.today()
    limit = today + timedelta(days=5)
    for rec in records:
        deadline = rec.get("deadline_date") or ""
        if not deadline:
            continue
        try:
            d = datetime.strptime(deadline, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d <= limit:
            rec_copy = dict(rec)
            rec_copy["deadline_status_calc"] = "Atrasado" if d < today else "Alerta"
            highlights.append(rec_copy)
    return highlights


def generate_monthly_report(db, year: int, month: int) -> Tuple[str, str]:
    os.makedirs(reports_dir(), exist_ok=True)
    pdf_path = os.path.join(reports_dir(), f"relatorio_mensal_{year}_{month:02d}.pdf")
    xlsx_path = os.path.join(reports_dir(), f"relatorio_mensal_{year}_{month:02d}.xlsx")

    records = records_for_month(db, year, month)
    total = count_total_month(db, year, month)
    by_cat = count_by_category(db, year, month)
    by_status = count_by_status(db, year, month)
    highlights = _deadline_highlights(records)

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"Relatorio Mensal - {month:02d}/{year}", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total do mes: {total}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Totais por categoria", styles["Heading2"]))
    data_cat = [["Categoria", "Total"]] + [[c, str(t)] for c, t in by_cat]
    story.append(_table(data_cat))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Totais por status", styles["Heading2"]))
    data_status = [["Status", "Total"]] + [[s, str(t)] for s, t in by_status]
    story.append(_table(data_status))
    story.append(Spacer(1, 12))

    if highlights:
        story.append(Paragraph("Destaques: prazos proximos/atrasados", styles["Heading2"]))
        data_high = [
            ["ID", "Data", "Categoria", "Numero", "Prazo", "Situacao"],
        ]
        for r in highlights:
            data_high.append(
                [
                    str(r.get("id", "")),
                    r.get("record_date", ""),
                    r.get("category", ""),
                    r.get("doc_number", ""),
                    r.get("deadline_date", ""),
                    r.get("deadline_status_calc", ""),
                ]
            )
        story.append(_table(data_high))
        story.append(Spacer(1, 12))

    story.append(Paragraph("Lista completa do mes", styles["Heading2"]))
    data_list = [
        ["ID", "Data", "Categoria", "Numero", "Assunto", "Status"],
    ]
    for r in records:
        data_list.append(
            [
                str(r.get("id", "")),
                r.get("record_date", ""),
                r.get("category", ""),
                r.get("doc_number", ""),
                r.get("subject", ""),
                r.get("status", ""),
            ]
        )
    story.append(_table(data_list))

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    doc.build(story)

    _write_monthly_excel(xlsx_path, year, month, total, by_cat, by_status, records, highlights)
    return pdf_path, xlsx_path


def _write_monthly_excel(
    xlsx_path: str,
    year: int,
    month: int,
    total: int,
    by_cat: List[Tuple[str, int]],
    by_status: List[Tuple[str, int]],
    records: List[Dict],
    highlights: List[Dict],
) -> None:
    wb = xlsxwriter.Workbook(xlsx_path)
    ws = wb.add_worksheet("Resumo")
    ws.write(0, 0, "Relatorio Mensal")
    ws.write(1, 0, f"{month:02d}/{year}")
    ws.write(3, 0, "Total do mes")
    ws.write(3, 1, total)

    ws.write(5, 0, "Totais por categoria")
    row = 6
    for cat, val in by_cat:
        ws.write(row, 0, cat)
        ws.write(row, 1, val)
        row += 1

    row += 1
    ws.write(row, 0, "Totais por status")
    row += 1
    for status, val in by_status:
        ws.write(row, 0, status)
        ws.write(row, 1, val)
        row += 1

    ws2 = wb.add_worksheet("Registros")
    headers = ["ID", "Data", "Categoria", "Numero", "Assunto", "Status", "Tags"]
    for col, h in enumerate(headers):
        ws2.write(0, col, h)
    for i, r in enumerate(records, start=1):
        ws2.write(i, 0, r.get("id", ""))
        ws2.write(i, 1, r.get("record_date", ""))
        ws2.write(i, 2, r.get("category", ""))
        ws2.write(i, 3, r.get("doc_number", ""))
        ws2.write(i, 4, r.get("subject", ""))
        ws2.write(i, 5, r.get("status", ""))
        ws2.write(i, 6, r.get("tags", ""))

    ws3 = wb.add_worksheet("Destaques")
    headers = ["ID", "Data", "Categoria", "Numero", "Prazo", "Situacao"]
    for col, h in enumerate(headers):
        ws3.write(0, col, h)
    for i, r in enumerate(highlights, start=1):
        ws3.write(i, 0, r.get("id", ""))
        ws3.write(i, 1, r.get("record_date", ""))
        ws3.write(i, 2, r.get("category", ""))
        ws3.write(i, 3, r.get("doc_number", ""))
        ws3.write(i, 4, r.get("deadline_date", ""))
        ws3.write(i, 5, r.get("deadline_status_calc", ""))

    wb.close()


def generate_annual_report(db, year: int) -> Tuple[str, str]:
    os.makedirs(reports_dir(), exist_ok=True)
    pdf_path = os.path.join(reports_dir(), f"relatorio_anual_{year}.pdf")
    xlsx_path = os.path.join(reports_dir(), f"relatorio_anual_{year}.xlsx")

    totals_month = totals_by_month(db, year)
    by_cat = totals_by_category_year(db, year)
    by_status = totals_by_status_year(db, year)
    records = records_for_year(db, year)

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"Relatorio Anual - {year}", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Totais mes a mes", styles["Heading2"]))
    data_month = [["Mes", "Total"]] + [[str(m), str(t)] for m, t in totals_month]
    story.append(_table(data_month))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Totais por categoria", styles["Heading2"]))
    data_cat = [["Categoria", "Total"]] + [[c, str(t)] for c, t in by_cat]
    story.append(_table(data_cat))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Totais por status", styles["Heading2"]))
    data_status = [["Status", "Total"]] + [[s, str(t)] for s, t in by_status]
    story.append(_table(data_status))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Lista consolidada", styles["Heading2"]))
    data_list = [
        ["ID", "Data", "Categoria", "Numero", "Assunto", "Status"],
    ]
    for r in records:
        data_list.append(
            [
                str(r.get("id", "")),
                r.get("record_date", ""),
                r.get("category", ""),
                r.get("doc_number", ""),
                r.get("subject", ""),
                r.get("status", ""),
            ]
        )
    story.append(_table(data_list))

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    doc.build(story)

    _write_annual_excel(xlsx_path, year, totals_month, by_cat, by_status, records)
    return pdf_path, xlsx_path


def _write_annual_excel(
    xlsx_path: str,
    year: int,
    totals_month: List[Tuple[int, int]],
    by_cat: List[Tuple[str, int]],
    by_status: List[Tuple[str, int]],
    records: List[Dict],
) -> None:
    wb = xlsxwriter.Workbook(xlsx_path)
    ws = wb.add_worksheet("Resumo")
    ws.write(0, 0, "Relatorio Anual")
    ws.write(1, 0, str(year))

    ws.write(3, 0, "Totais mes a mes")
    row = 4
    for m, t in totals_month:
        ws.write(row, 0, m)
        ws.write(row, 1, t)
        row += 1

    row += 1
    ws.write(row, 0, "Totais por categoria")
    row += 1
    for cat, val in by_cat:
        ws.write(row, 0, cat)
        ws.write(row, 1, val)
        row += 1

    row += 1
    ws.write(row, 0, "Totais por status")
    row += 1
    for status, val in by_status:
        ws.write(row, 0, status)
        ws.write(row, 1, val)
        row += 1

    ws2 = wb.add_worksheet("Registros")
    headers = ["ID", "Data", "Categoria", "Numero", "Assunto", "Status", "Tags"]
    for col, h in enumerate(headers):
        ws2.write(0, col, h)
    for i, r in enumerate(records, start=1):
        ws2.write(i, 0, r.get("id", ""))
        ws2.write(i, 1, r.get("record_date", ""))
        ws2.write(i, 2, r.get("category", ""))
        ws2.write(i, 3, r.get("doc_number", ""))
        ws2.write(i, 4, r.get("subject", ""))
        ws2.write(i, 5, r.get("status", ""))
        ws2.write(i, 6, r.get("tags", ""))

    wb.close()


def export_records_to_excel(records: List[Dict], output_path: str) -> None:
    wb = xlsxwriter.Workbook(output_path)
    ws = wb.add_worksheet("Registros")
    headers = [
        "ID",
        "Categoria",
        "Numero",
        "Data",
        "Interessado",
        "Origem",
        "Assunto",
        "Status",
        "Tags",
    ]
    for col, h in enumerate(headers):
        ws.write(0, col, h)
    for i, r in enumerate(records, start=1):
        ws.write(i, 0, r.get("id", ""))
        ws.write(i, 1, r.get("category", ""))
        ws.write(i, 2, r.get("doc_number", ""))
        ws.write(i, 3, r.get("record_date", ""))
        ws.write(i, 4, r.get("interested", ""))
        ws.write(i, 5, r.get("origin", ""))
        ws.write(i, 6, r.get("subject", ""))
        ws.write(i, 7, r.get("status", ""))
        ws.write(i, 8, r.get("tags", ""))
    wb.close()
