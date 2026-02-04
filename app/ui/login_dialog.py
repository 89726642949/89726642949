from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QMessageBox,
)


class PasswordDialog(QDialog):
    def __init__(self, mode: str, parent=None):
        super().__init__(parent)
        self.mode = mode  # "create" or "login" or "unlock"
        self.setWindowTitle("Acesso")
        self.setModal(True)

        layout = QVBoxLayout()
        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        form = QFormLayout()
        self.username = QLineEdit("admin")
        self.username.setReadOnly(True)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)

        form.addRow("Usuario:", self.username)
        form.addRow("Senha:", self.password)
        if mode == "create":
            form.addRow("Confirmar:", self.confirm)
        layout.addLayout(form)

        self.btn_ok = QPushButton("Continuar")
        self.btn_ok.clicked.connect(self._on_ok)
        layout.addWidget(self.btn_ok)

        self.setLayout(layout)
        self._update_texts()

    def _update_texts(self):
        if self.mode == "create":
            self.info_label.setText("Crie uma senha para acessar o sistema.")
        elif self.mode == "unlock":
            self.info_label.setText("Sistema bloqueado. Digite a senha.")
        else:
            self.info_label.setText("Digite sua senha para acessar.")

    def _on_ok(self):
        if not self.password.text().strip():
            QMessageBox.warning(self, "Atencao", "Senha obrigatoria.")
            return
        if self.mode == "create":
            if self.password.text() != self.confirm.text():
                QMessageBox.warning(self, "Atencao", "Senhas nao conferem.")
                return
        self.accept()

    def get_password(self) -> str:
        return self.password.text().strip()
