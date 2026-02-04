import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Qt, QEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sistema_atividades import db
from sistema_atividades.constants import APP_NAME, CATEGORIES
from sistema_atividades.services.backup_service import create_backup, restore_backup
from sistema_atividades.services.report_service import (
    generate_annual_report,
    generate_monthly_report,
)
from sistema_atividades.ui.dashboard import DashboardWidget
from sistema_atividades.ui.dialogs import LoginDialog, RecordDialog, SettingsDialog
from sistema_atividades.ui.records_page import RecordsPage


logger = logging.getLogger(__name__)


class IdleMonitor(QObject):
    def __init__(self):
        super().__init__()
        self.last_activity = datetime.now()

    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.Wheel,
        ):
            self.last_activity = datetime.now()
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 720)
        self.locked = False

        self.dashboard = DashboardWidget()
        self.records_page = RecordsPage()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.records_page)

        self.sidebar = QListWidget()
        self.sidebar.addItem(QListWidgetItem("Dashboard"))
        for cat in CATEGORIES:
            self.sidebar.addItem(QListWidgetItem(cat))
        self.sidebar.setFixedWidth(220)
        self.sidebar.currentRowChanged.connect(self._handle_sidebar_change)

        self.new_button = QPushButton("Novo Registro")
        self.month_report_button = QPushButton("Relatorio Mensal")
        self.year_report_button = QPushButton("Relatorio Anual")
        self.backup_button = QPushButton("Backup")
        self.restore_button = QPushButton("Restaurar")
        self.lock_button = QPushButton("Bloquear")
        self.settings_button = QPushButton("Configuracoes")

        self.new_button.clicked.connect(self._handle_new)
        self.month_report_button.clicked.connect(self._handle_month_report)
        self.year_report_button.clicked.connect(self._handle_year_report)
        self.backup_button.clicked.connect(self._handle_backup)
        self.restore_button.clicked.connect(self._handle_restore)
        self.lock_button.clicked.connect(self._handle_lock)
        self.settings_button.clicked.connect(self._handle_settings)

        self.dashboard.new_record_requested.connect(self._handle_new)
        self.dashboard.monthly_report_requested.connect(self._handle_month_report)
        self.dashboard.annual_report_requested.connect(self._handle_year_report)
        self.dashboard.backup_requested.connect(self._handle_backup)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.new_button)
        top_bar.addWidget(self.month_report_button)
        top_bar.addWidget(self.year_report_button)
        top_bar.addWidget(self.backup_button)
        top_bar.addWidget(self.restore_button)
        top_bar.addWidget(self.lock_button)
        top_bar.addWidget(self.settings_button)
        top_bar.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.stack)

        content = QWidget()
        content.setLayout(main_layout)

        root_layout = QHBoxLayout()
        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(content)

        root = QWidget()
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        self.idle_monitor = IdleMonitor()
        self.installEventFilter(self.idle_monitor)
        self._start_idle_timer()

        self.sidebar.setCurrentRow(0)

    def _handle_sidebar_change(self, index: int) -> None:
        if index == 0:
            self.stack.setCurrentWidget(self.dashboard)
            self.dashboard.refresh()
            return
        category = self.sidebar.item(index).text()
        self.stack.setCurrentWidget(self.records_page)
        self.records_page.set_category_filter(category)
        self.records_page.refresh()

    def _handle_new(self) -> None:
        dialog = RecordDialog(parent=self)
        if dialog.exec():
            self.refresh_all()

    def _handle_month_report(self) -> None:
        from sistema_atividades.ui.dialogs import MonthlyReportDialog

        dialog = MonthlyReportDialog(parent=self)
        if dialog.exec():
            month, year, output_dir = dialog.get_values()
            if output_dir:
                generate_monthly_report(year, month, Path(output_dir))
                QMessageBox.information(
                    self,
                    "Relatorio",
                    "Relatorio mensal gerado com sucesso.",
                )

    def _handle_year_report(self) -> None:
        from sistema_atividades.ui.dialogs import AnnualReportDialog

        dialog = AnnualReportDialog(parent=self)
        if dialog.exec():
            year, output_dir = dialog.get_values()
            if output_dir:
                generate_annual_report(year, Path(output_dir))
                QMessageBox.information(
                    self,
                    "Relatorio",
                    "Relatorio anual gerado com sucesso.",
                )

    def _handle_backup(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar backup", "backup_sistema.zip", "Backup (*.zip)"
        )
        if not file_path:
            return
        ok, message = create_backup(Path(file_path))
        if ok:
            QMessageBox.information(self, "Backup", message)
        else:
            QMessageBox.warning(self, "Backup", message)

    def _handle_restore(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Restaurar backup", "", "Backup (*.zip)"
        )
        if not file_path:
            return
        res = QMessageBox.question(
            self,
            "Restaurar",
            "Restaurar backup vai substituir os dados atuais. Continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return
        ok, message = restore_backup(Path(file_path))
        if ok:
            QMessageBox.information(self, "Backup", message)
        else:
            QMessageBox.warning(self, "Backup", message)

    def _handle_lock(self) -> None:
        self._lock_now()

    def _handle_settings(self) -> None:
        dialog = SettingsDialog(parent=self)
        if dialog.exec():
            QMessageBox.information(self, "Configuracoes", "Configuracoes salvas.")

    def _lock_now(self) -> None:
        if self.locked:
            return
        self.locked = True
        dialog = LoginDialog(allow_cancel=False, parent=self)
        if dialog.exec():
            self.locked = False
            self.idle_monitor.last_activity = datetime.now()

    def _start_idle_timer(self) -> None:
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(30_000)
        self.idle_timer.timeout.connect(self._check_idle)
        self.idle_timer.start()

    def _check_idle(self) -> None:
        minutes = db.get_auto_lock_minutes()
        if minutes <= 0 or self.locked:
            return
        delta = datetime.now() - self.idle_monitor.last_activity
        if delta.total_seconds() >= minutes * 60:
            self._lock_now()

    def refresh_all(self) -> None:
        self.dashboard.refresh()
        self.records_page.refresh()
