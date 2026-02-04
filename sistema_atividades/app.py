import logging
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox

from sistema_atividades import db
from sistema_atividades.logging_config import setup_logging
from sistema_atividades.ui.dialogs import LoginDialog, SetPasswordDialog
from sistema_atividades.ui.main_window import MainWindow


logger = logging.getLogger(__name__)


def _apply_styles(app: QApplication) -> None:
    app.setStyleSheet(
        """
        QMainWindow {
            background-color: #F7F7F7;
        }
        QListWidget {
            background-color: #DCECF9;
            border: none;
            font-size: 14px;
        }
        QListWidget::item {
            padding: 10px;
        }
        QListWidget::item:selected {
            background-color: #BFD7F2;
        }
        QPushButton {
            background-color: #DFF3E4;
            border: 1px solid #CFEBD6;
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #CFEBD6;
        }
        QGroupBox {
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            margin-top: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }
        QLineEdit, QDateEdit, QDateTimeEdit, QComboBox, QPlainTextEdit {
            background-color: #FFFFFF;
            border: 1px solid #DADADA;
            border-radius: 4px;
            padding: 4px;
        }
        QTableWidget {
            background-color: #FFFFFF;
            gridline-color: #E6E6E6;
        }
        """
    )


def _handle_exception(exc_type, exc_value, exc_traceback):
    logger.exception("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    QMessageBox.critical(
        None,
        "Erro",
        "Ocorreu um erro inesperado. Consulte o log para detalhes.",
    )


def main() -> None:
    setup_logging()
    db.initialize_database()
    db.seed_sample_data()

    app = QApplication(sys.argv)
    _apply_styles(app)
    sys.excepthook = _handle_exception

    if not db.get_password_hash():
        setup_dialog = SetPasswordDialog()
        if not setup_dialog.exec():
            sys.exit(0)

    login_dialog = LoginDialog()
    if not login_dialog.exec():
        sys.exit(0)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
