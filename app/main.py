import sys
import logging

from PySide6.QtWidgets import QApplication, QMessageBox

from app.services.utils import setup_logging, resource_path
from app.services.db import Database, init_db
from app.services.auth import has_user, create_user, verify_user
from app.services.sample_data import seed_sample_data
from app.ui.login_dialog import PasswordDialog
from app.ui.main_window import MainWindow


def load_styles(app: QApplication):
    try:
        with open(resource_path("app/assets/style.qss"), "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass


def main():
    setup_logging()
    app = QApplication(sys.argv)
    load_styles(app)

    db = Database()
    init_db(db)
    seed_sample_data(db)

    if not has_user(db):
        dlg = PasswordDialog("create")
        if dlg.exec():
            create_user(db, "admin", dlg.get_password())
        else:
            QMessageBox.warning(None, "Saindo", "Senha nao criada. Encerrando.")
            return

    login = PasswordDialog("login")
    if login.exec():
        if not verify_user(db, "admin", login.get_password()):
            QMessageBox.critical(None, "Erro", "Senha incorreta.")
            return
    else:
        return

    window = MainWindow(db)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logging.exception("Erro fatal")
        QMessageBox.critical(None, "Erro", f"Erro fatal: {exc}")
