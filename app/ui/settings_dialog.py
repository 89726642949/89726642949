from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QMessageBox,
)

from app.services.db import get_setting, set_setting


class SettingsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Configuracoes")
        self.setModal(True)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.autolock = QSpinBox()
        self.autolock.setRange(1, 180)
        self.autolock.setValue(int(get_setting(db, "autolock_minutes", "10")))

        self.custom_outros = QLineEdit(get_setting(db, "custom_outros_name", "Outros"))

        form.addRow("Bloquear apos (min):", self.autolock)
        form.addRow("Nome da pasta 'Outros':", self.custom_outros)
        layout.addLayout(form)

        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def _save(self):
        if not self.custom_outros.text().strip():
            QMessageBox.warning(self, "Atencao", "Nome da pasta nao pode ser vazio.")
            return
        set_setting(self.db, "autolock_minutes", str(self.autolock.value()))
        set_setting(self.db, "custom_outros_name", self.custom_outros.text().strip())
        self.accept()
