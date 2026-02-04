import os
import logging
from datetime import datetime, date

from PySide6.QtCore import Qt, QEvent, QTimer, QDate
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QGroupBox,
    QFormLayout,
)
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis

from app.services import records as records_service
from app.services.auth import verify_user
from app.services.backup import create_backup, restore_backup
from app.services.reports import export_records_to_excel
from app.services.db import get_setting
from app.ui.record_dialog import RecordDialog
from app.ui.report_dialogs import MonthlyReportDialog, AnnualReportDialog
from app.ui.login_dialog import PasswordDialog
from app.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Sistema de Atividades")
        self.resize(1200, 700)
        self.last_activity = datetime.now()
        self.is_locked = False

        self._init_ui()
        self._load_records()
        self._refresh_dashboard()
        self._setup_idle_timer()

    def _init_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout()

        self.sidebar = QVBoxLayout()
        btn_dash = QPushButton("Dashboard")
        btn_dash.clicked.connect(self._show_dashboard)
        btn_records = QPushButton("Registros")
        btn_records.clicked.connect(self._show_records)
        btn_settings = QPushButton("Configuracoes")
        btn_settings.clicked.connect(self._open_settings)
        self.sidebar.addWidget(btn_dash)
        self.sidebar.addWidget(btn_records)
        self.sidebar.addWidget(btn_settings)

        cat_group = QGroupBox("Pastas/Categorias")
        cat_layout = QVBoxLayout()
        self.cat_list = QListWidget()
        self.cat_list.addItem("Todas")
        for cat in records_service.get_categories(self.db):
            self.cat_list.addItem(cat)
        self.cat_list.currentItemChanged.connect(self._on_category_selected)
        cat_layout.addWidget(self.cat_list)
        cat_group.setLayout(cat_layout)
        self.sidebar.addWidget(cat_group)
        self.sidebar.addStretch()

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(self.sidebar)

        self.pages = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.records_page = self._build_records_page()
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.records_page)

        main_layout.addWidget(sidebar_widget, 1)
        main_layout.addWidget(self.pages, 4)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.cat_list.setCurrentRow(0)

    def _build_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.total_label = QLabel("Total do mes: 0")
        layout.addWidget(self.total_label)

        stats_layout = QHBoxLayout()
        self.cat_stats = QGroupBox("Totais por categoria")
        self.cat_stats_layout = QVBoxLayout()
        self.cat_stats.setLayout(self.cat_stats_layout)

        self.status_stats = QGroupBox("Totais por status")
        self.status_stats_layout = QVBoxLayout()
        self.status_stats.setLayout(self.status_stats_layout)

        stats_layout.addWidget(self.cat_stats)
        stats_layout.addWidget(self.status_stats)
        layout.addLayout(stats_layout)

        chart_group = QGroupBox("Lancamentos por dia")
        chart_layout = QVBoxLayout()
        self.chart_view = QChartView()
        chart_layout.addWidget(self.chart_view)
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        quick_layout = QHBoxLayout()
        btn_new = QPushButton("Novo Registro")
        btn_new.clicked.connect(self._new_record)
        btn_month = QPushButton("Relatorio Mensal")
        btn_month.clicked.connect(self._monthly_report)
        btn_year = QPushButton("Relatorio Anual")
        btn_year.clicked.connect(self._annual_report)
        btn_backup = QPushButton("Backup")
        btn_backup.clicked.connect(self._backup)
        quick_layout.addWidget(btn_new)
        quick_layout.addWidget(btn_month)
        quick_layout.addWidget(btn_year)
        quick_layout.addWidget(btn_backup)
        layout.addLayout(quick_layout)

        page.setLayout(layout)
        return page

    def _build_records_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Busca global...")
        self.search.textChanged.connect(self._load_records)

        self.filter_category = QComboBox()
        self.filter_category.addItem("")
        self.filter_category.addItems(records_service.get_categories(self.db))
        self.filter_category.currentTextChanged.connect(self._load_records)

        self.filter_status = QComboBox()
        self.filter_status.addItem("")
        self.filter_status.addItems(records_service.STATUSES)
        self.filter_status.currentTextChanged.connect(self._load_records)

        self.filter_tags = QLineEdit()
        self.filter_tags.setPlaceholderText("Tags (virgula)")
        self.filter_tags.textChanged.connect(self._load_records)

        self.order_by = QComboBox()
        self.order_by.addItem("Data (desc)", "record_date DESC, id DESC")
        self.order_by.addItem("Data (asc)", "record_date ASC, id ASC")
        self.order_by.addItem("Numero (asc)", "doc_number ASC, id ASC")
        self.order_by.addItem("Numero (desc)", "doc_number DESC, id DESC")
        self.order_by.currentIndexChanged.connect(self._load_records)

        self.filter_date_from = QDateEdit()
        self.filter_date_from.setCalendarPopup(True)
        self.filter_date_from.setDate(QDate.currentDate().addMonths(-1))
        self.filter_date_from.dateChanged.connect(self._load_records)

        self.filter_date_to = QDateEdit()
        self.filter_date_to.setCalendarPopup(True)
        self.filter_date_to.setDate(QDate.currentDate())
        self.filter_date_to.dateChanged.connect(self._load_records)

        self.filter_date_enabled = QCheckBox("Filtrar data")
        self.filter_date_enabled.setChecked(True)
        self.filter_date_enabled.stateChanged.connect(self._load_records)

        filter_layout.addWidget(self.search)
        filter_layout.addWidget(QLabel("Categoria"))
        filter_layout.addWidget(self.filter_category)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self.filter_status)
        filter_layout.addWidget(QLabel("Tags"))
        filter_layout.addWidget(self.filter_tags)
        filter_layout.addWidget(QLabel("Ordenar"))
        filter_layout.addWidget(self.order_by)
        filter_layout.addWidget(QLabel("De"))
        filter_layout.addWidget(self.filter_date_from)
        filter_layout.addWidget(QLabel("Ate"))
        filter_layout.addWidget(self.filter_date_to)
        filter_layout.addWidget(self.filter_date_enabled)

        layout.addLayout(filter_layout)

        buttons_layout = QHBoxLayout()
        btn_new = QPushButton("Novo")
        btn_new.clicked.connect(self._new_record)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self._edit_record)
        btn_dup = QPushButton("Duplicar")
        btn_dup.clicked.connect(self._duplicate_record)
        btn_del = QPushButton("Excluir")
        btn_del.clicked.connect(self._delete_record)
        btn_export = QPushButton("Exportar Excel")
        btn_export.clicked.connect(self._export_filtered)
        btn_backup = QPushButton("Backup")
        btn_backup.clicked.connect(self._backup)
        btn_restore = QPushButton("Restore")
        btn_restore.clicked.connect(self._restore)
        btn_month = QPushButton("Relatorio Mensal")
        btn_month.clicked.connect(self._monthly_report)
        btn_year = QPushButton("Relatorio Anual")
        btn_year.clicked.connect(self._annual_report)

        for b in [btn_new, btn_edit, btn_dup, btn_del, btn_export, btn_backup, btn_restore, btn_month, btn_year]:
            buttons_layout.addWidget(b)
        layout.addLayout(buttons_layout)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Data", "Categoria", "Numero", "Assunto", "Status", "Tags"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_record)

        layout.addWidget(self.table)
        page.setLayout(layout)
        return page

    def _show_dashboard(self):
        self.pages.setCurrentWidget(self.dashboard_page)

    def _show_records(self):
        self.pages.setCurrentWidget(self.records_page)

    def _open_settings(self):
        dlg = SettingsDialog(self.db, self)
        if dlg.exec():
            self._refresh_categories()
            self._refresh_dashboard()

    def _refresh_categories(self):
        self.cat_list.clear()
        self.cat_list.addItem("Todas")
        for cat in records_service.get_categories(self.db):
            self.cat_list.addItem(cat)
        self.filter_category.clear()
        self.filter_category.addItem("")
        self.filter_category.addItems(records_service.get_categories(self.db))

    def _on_category_selected(self, current: QListWidgetItem):
        if not current:
            return
        text = current.text()
        if text == "Todas":
            self.filter_category.setCurrentText("")
        else:
            self.filter_category.setCurrentText(text)
        self._show_records()
        self._load_records()

    def _load_records(self):
        try:
            tags = [t.strip() for t in self.filter_tags.text().split(",") if t.strip()]
            date_from = None
            date_to = None
            if self.filter_date_enabled.isChecked():
                date_from = self.filter_date_from.date().toString("yyyy-MM-dd")
                date_to = self.filter_date_to.date().toString("yyyy-MM-dd")
            category_filter = self.filter_category.currentText().strip() or None
            if category_filter:
                category_filter = records_service.to_storage_category(self.db, category_filter)
            records = records_service.search_records(
                self.db,
                query=self.search.text().strip(),
                date_from=date_from,
                date_to=date_to,
                category=category_filter,
                status=self.filter_status.currentText().strip() or None,
                tags=tags or None,
                order_by=self.order_by.currentData(),
            )
            self.table.setRowCount(len(records))
            for row, rec in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(str(rec.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(rec.get("record_date", "")))
                display_cat = records_service.to_display_category(self.db, rec.get("category", ""))
                self.table.setItem(row, 2, QTableWidgetItem(display_cat))
                self.table.setItem(row, 3, QTableWidgetItem(rec.get("doc_number", "")))
                self.table.setItem(row, 4, QTableWidgetItem(rec.get("subject", "")))
                self.table.setItem(row, 5, QTableWidgetItem(rec.get("status", "")))
                self.table.setItem(row, 6, QTableWidgetItem(rec.get("tags", "")))
            self._refresh_dashboard()
        except Exception as exc:
            logging.exception("Erro ao carregar registros")
            QMessageBox.critical(self, "Erro", f"Falha ao carregar registros: {exc}")

    def _selected_record_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return int(items[0].text())

    def _new_record(self):
        dlg = RecordDialog(self.db, self)
        if dlg.exec():
            values = dlg.get_values()
            self._save_record(values)

    def _edit_record(self):
        record_id = self._selected_record_id()
        if not record_id:
            QMessageBox.warning(self, "Atencao", "Selecione um registro.")
            return
        record = records_service.get_record(self.db, record_id)
        if not record:
            QMessageBox.warning(self, "Atencao", "Registro nao encontrado.")
            return
        dlg = RecordDialog(self.db, self)
        dlg.set_record(record)
        if dlg.exec():
            values = dlg.get_values()
            self._save_record(values, record_id=record_id)

    def _duplicate_record(self):
        record_id = self._selected_record_id()
        if not record_id:
            QMessageBox.warning(self, "Atencao", "Selecione um registro.")
            return
        record = records_service.get_record(self.db, record_id)
        if not record:
            QMessageBox.warning(self, "Atencao", "Registro nao encontrado.")
            return
        dlg = RecordDialog(self.db, self)
        dlg.set_record(record, is_duplicate=True)
        if dlg.exec():
            values = dlg.get_values()
            self._save_record(values)

    def _save_record(self, values, record_id=None):
        similar = records_service.find_similar(
            self.db,
            values.get("doc_number", ""),
            values.get("record_date", ""),
            values.get("category", ""),
            exclude_id=record_id,
        )
        if similar:
            res = QMessageBox.question(
                self,
                "Aviso",
                "Ja existe registro parecido. Deseja salvar mesmo?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res != QMessageBox.Yes:
                return
        if record_id:
            records_service.update_record(self.db, record_id, values)
        else:
            records_service.insert_record(self.db, values)
        self._load_records()

    def _delete_record(self):
        record_id = self._selected_record_id()
        if not record_id:
            QMessageBox.warning(self, "Atencao", "Selecione um registro.")
            return
        res = QMessageBox.question(
            self,
            "Confirmacao",
            "Deseja excluir este registro?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if res == QMessageBox.Yes:
            records_service.delete_record(self.db, record_id)
            self._load_records()

    def _export_filtered(self):
        category_filter = self.filter_category.currentText().strip() or None
        if category_filter:
            category_filter = records_service.to_storage_category(self.db, category_filter)
        records = records_service.search_records(
            self.db,
            query=self.search.text().strip(),
            date_from=self.filter_date_from.date().toString("yyyy-MM-dd")
            if self.filter_date_enabled.isChecked()
            else None,
            date_to=self.filter_date_to.date().toString("yyyy-MM-dd")
            if self.filter_date_enabled.isChecked()
            else None,
            category=category_filter,
            status=self.filter_status.currentText().strip() or None,
            tags=[t.strip() for t in self.filter_tags.text().split(",") if t.strip()] or None,
            order_by=self.order_by.currentData(),
        )
        if not records:
            QMessageBox.information(self, "Info", "Nenhum registro para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Excel", "", "Excel (*.xlsx)")
        if not path:
            return
        export_records_to_excel(records, path)
        QMessageBox.information(self, "OK", f"Arquivo salvo: {path}")

    def _monthly_report(self):
        dlg = MonthlyReportDialog(self.db, self)
        dlg.exec()

    def _annual_report(self):
        dlg = AnnualReportDialog(self.db, self)
        dlg.exec()

    def _backup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar backup", "", "Backup (*.zip)")
        if not path:
            return
        create_backup(path)
        QMessageBox.information(self, "OK", f"Backup salvo: {path}")

    def _restore(self):
        res = QMessageBox.question(
            self,
            "Confirmacao",
            "Restaurar backup ira substituir os dados atuais. Continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar backup", "", "Backup (*.zip)")
        if not path:
            return
        self.db.close()
        restore_backup(path)
        from app.services.db import Database, init_db

        self.db = Database()
        init_db(self.db)
        self._refresh_categories()
        self._load_records()
        QMessageBox.information(self, "OK", "Backup restaurado.")

    def _refresh_dashboard(self):
        try:
            today = date.today()
            year = today.year
            month = today.month
            total = records_service.count_total_month(self.db, year, month)
            self.total_label.setText(f"Total do mes: {total}")

            for i in reversed(range(self.cat_stats_layout.count())):
                item = self.cat_stats_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
            for i in reversed(range(self.status_stats_layout.count())):
                item = self.status_stats_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)

            for cat, val in records_service.count_by_category(self.db, year, month):
                display_cat = records_service.to_display_category(self.db, cat)
                self.cat_stats_layout.addWidget(QLabel(f"{display_cat}: {val}"))
            for status, val in records_service.count_by_status(self.db, year, month):
                self.status_stats_layout.addWidget(QLabel(f"{status}: {val}"))

            self._update_chart(year, month)
        except Exception as exc:
            logging.exception("Erro no dashboard")
            QMessageBox.critical(self, "Erro", f"Falha ao atualizar dashboard: {exc}")

    def _update_chart(self, year: int, month: int):
        counts = records_service.count_per_day(self.db, year, month)
        day_map = {day: total for day, total in counts}
        days = [str(i) for i in range(1, 32)]
        values = [day_map.get(i, 0) for i in range(1, 32)]

        bar_set = QBarSet("Lancamentos")
        bar_set.append(values)
        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Lancamentos por dia")
        axis = QBarCategoryAxis()
        axis.append(days)
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)
        self.chart_view.setChart(chart)

    def _setup_idle_timer(self):
        self.installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_idle)
        self.timer.start(30000)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.KeyPress):
            self.last_activity = datetime.now()
        return super().eventFilter(obj, event)

    def _check_idle(self):
        if self.is_locked:
            return
        minutes = int(get_setting(self.db, "autolock_minutes", "10"))
        idle = (datetime.now() - self.last_activity).total_seconds() / 60.0
        if idle >= minutes:
            self._lock()

    def _lock(self):
        self.is_locked = True
        while self.is_locked:
            dlg = PasswordDialog("unlock", self)
            if dlg.exec():
                if verify_user(self.db, "admin", dlg.get_password()):
                    self.is_locked = False
                    self.last_activity = datetime.now()
                    break
                QMessageBox.warning(self, "Atencao", "Senha incorreta.")
            else:
                QMessageBox.warning(self, "Atencao", "Senha obrigatoria para desbloquear.")
