from datetime import date
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QFileDialog,
)

from sistema_atividades import db
from sistema_atividades.constants import CATEGORIES, STATUSES
from sistema_atividades.services.export_service import export_records_to_excel
from sistema_atividades.ui.dialogs import RecordDialog


class RecordsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Busca global (numero, assunto, nome, data)")
        self.category_filter = QComboBox()
        self.category_filter.addItem("Todos")
        self.category_filter.addItems(CATEGORIES)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos")
        self.status_filter.addItems(STATUSES)
        self.tags_filter = QLineEdit()
        self.tags_filter.setPlaceholderText("Tags")

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(date.today().replace(day=1))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(date.today())

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Data", "Categoria", "Numero", "Assunto", "Status", "Interessado"]
        )
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.new_button = QPushButton("Novo Registro")
        self.edit_button = QPushButton("Editar")
        self.duplicate_button = QPushButton("Duplicar")
        self.delete_button = QPushButton("Excluir")
        self.export_button = QPushButton("Exportar Excel")
        self.clear_button = QPushButton("Limpar filtros")

        self._build_layout()
        self._connect_signals()
        self.refresh()

    def _build_layout(self) -> None:
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Buscar:"))
        filters_layout.addWidget(self.search_input)
        filters_layout.addWidget(QLabel("Categoria:"))
        filters_layout.addWidget(self.category_filter)
        filters_layout.addWidget(QLabel("Status:"))
        filters_layout.addWidget(self.status_filter)
        filters_layout.addWidget(QLabel("Tags:"))
        filters_layout.addWidget(self.tags_filter)
        filters_layout.addWidget(QLabel("De:"))
        filters_layout.addWidget(self.date_from)
        filters_layout.addWidget(QLabel("Ate:"))
        filters_layout.addWidget(self.date_to)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.duplicate_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addWidget(self.clear_button)

        layout = QVBoxLayout()
        layout.addLayout(filters_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self.refresh)
        self.category_filter.currentTextChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        self.tags_filter.textChanged.connect(self.refresh)
        self.date_from.dateChanged.connect(self.refresh)
        self.date_to.dateChanged.connect(self.refresh)
        self.new_button.clicked.connect(self._handle_new)
        self.edit_button.clicked.connect(self._handle_edit)
        self.duplicate_button.clicked.connect(self._handle_duplicate)
        self.delete_button.clicked.connect(self._handle_delete)
        self.export_button.clicked.connect(self._handle_export)
        self.clear_button.clicked.connect(self._clear_filters)
        self.table.doubleClicked.connect(self._handle_edit)

    def _selected_record_id(self) -> Optional[int]:
        selected = self.table.currentRow()
        if selected < 0:
            return None
        item = self.table.item(selected, 0)
        return int(item.text()) if item else None

    def _handle_new(self) -> None:
        dialog = RecordDialog(parent=self)
        if dialog.exec():
            self.refresh()

    def _handle_edit(self) -> None:
        record_id = self._selected_record_id()
        if not record_id:
            QMessageBox.information(self, "Editar", "Selecione um registro.")
            return
        record = db.get_record(record_id)
        if not record:
            return
        dialog = RecordDialog(record=record, parent=self)
        if dialog.exec():
            self.refresh()

    def _handle_duplicate(self) -> None:
        record_id = self._selected_record_id()
        if not record_id:
            QMessageBox.information(self, "Duplicar", "Selecione um registro.")
            return
        record = db.get_record(record_id)
        if not record:
            return
        dialog = RecordDialog(record=record, is_duplicate=True, parent=self)
        if dialog.exec():
            self.refresh()

    def _handle_delete(self) -> None:
        record_id = self._selected_record_id()
        if not record_id:
            QMessageBox.information(self, "Excluir", "Selecione um registro.")
            return
        res = QMessageBox.question(
            self,
            "Confirmar exclusao",
            "Deseja excluir este registro?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return
        db.delete_record(record_id)
        self.refresh()

    def _handle_export(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Excel", "registros.xlsx", "Excel (*.xlsx)"
        )
        if not file_path:
            return
        records = self._fetch_records()
        export_records_to_excel(records, Path(file_path))
        QMessageBox.information(self, "Exportar", "Arquivo salvo com sucesso.")

    def _clear_filters(self) -> None:
        self.search_input.clear()
        self.category_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.tags_filter.clear()
        self.date_from.setDate(date.today().replace(day=1))
        self.date_to.setDate(date.today())
        self.refresh()

    def set_category_filter(self, category: str) -> None:
        if category and category in CATEGORIES:
            self.category_filter.setCurrentText(category)

    def _fetch_records(self):
        return db.list_records(
            search=self.search_input.text().strip(),
            category=self.category_filter.currentText(),
            status=self.status_filter.currentText(),
            tags=self.tags_filter.text().strip(),
            date_from=self.date_from.date().toString("yyyy-MM-dd"),
            date_to=self.date_to.date().toString("yyyy-MM-dd"),
        )

    def refresh(self) -> None:
        records = self._fetch_records()
        self.table.setRowCount(0)
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(record.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(record.get("record_date", "")))
            self.table.setItem(row, 2, QTableWidgetItem(record.get("category", "")))
            self.table.setItem(row, 3, QTableWidgetItem(record.get("doc_number", "")))
            self.table.setItem(row, 4, QTableWidgetItem(record.get("subject", "")))
            self.table.setItem(row, 5, QTableWidgetItem(record.get("status", "")))
            self.table.setItem(row, 6, QTableWidgetItem(record.get("interested", "")))

        self.table.resizeColumnsToContents()
