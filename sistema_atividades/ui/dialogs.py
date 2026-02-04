import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from PySide6.QtCore import QDate, QDateTime, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from sistema_atividades import db
from sistema_atividades.constants import (
    CATEGORIES,
    DEADLINE_STATUSES,
    PROJECT_STATUSES,
    SCHEDULE_TYPES,
    SEND_MEDIA,
    STATUSES,
)
from sistema_atividades.paths import get_attachments_dir, get_data_dir
from sistema_atividades.security import hash_password, verify_password


class LoginDialog(QDialog):
    def __init__(self, allow_cancel: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setModal(True)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.info_label = QLabel("Digite sua senha para continuar.")

        form = QFormLayout()
        form.addRow("Senha:", self.password_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        if allow_cancel:
            buttons.addButton(QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._handle_login)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _handle_login(self) -> None:
        password = self.password_input.text().strip()
        password_hash = db.get_password_hash()
        if not password_hash:
            QMessageBox.warning(self, "Senha", "Senha nao configurada.")
            return
        if verify_password(password, password_hash):
            self.accept()
            return
        QMessageBox.warning(self, "Senha", "Senha incorreta.")


class SetPasswordDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Definir senha")
        self.setModal(True)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Nova senha:", self.password_input)
        form.addRow("Confirmar:", self.confirm_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._handle_save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Defina uma senha para proteger o sistema."))
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _handle_save(self) -> None:
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        if len(password) < 6:
            QMessageBox.warning(self, "Senha", "Use pelo menos 6 caracteres.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Senha", "As senhas nao conferem.")
            return
        db.set_password_hash(hash_password(password))
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Configuracoes")
        self.setModal(True)

        self.auto_lock_spin = QSpinBox()
        self.auto_lock_spin.setRange(0, 240)
        self.auto_lock_spin.setValue(db.get_auto_lock_minutes())

        form = QFormLayout()
        form.addRow("Bloqueio automatico (minutos):", self.auto_lock_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._handle_save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _handle_save(self) -> None:
        db.set_auto_lock_minutes(self.auto_lock_spin.value())
        self.accept()


class RecordDialog(QDialog):
    def __init__(
        self,
        record: Optional[Dict] = None,
        is_duplicate: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Registro")
        self.setModal(True)
        self.record_id = record.get("id") if record else None
        if is_duplicate:
            self.record_id = None

        self.attachments_to_add: List[Dict] = []
        self.attachments_to_delete: List[int] = []

        self.category_input = QComboBox()
        self.category_input.addItems(CATEGORIES)

        self.doc_number_input = QLineEdit()
        self.record_date_input = QDateEdit()
        self.record_date_input.setCalendarPopup(True)
        self.record_date_input.setDate(QDate.currentDate())

        self.interested_input = QLineEdit()
        self.origin_input = QLineEdit()
        self.subject_input = QLineEdit()

        self.status_input = QComboBox()
        self.status_input.addItems(STATUSES)

        self.tags_input = QLineEdit()
        self.notes_input = QPlainTextEdit()

        self._build_extra_groups()
        self._build_attachments_group()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_main_tab(), "Principal")
        self.tabs.addTab(self._build_extra_tab(), "Extras")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._handle_save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)
        self.setLayout(layout)

        self.category_input.currentTextChanged.connect(self._update_extra_visibility)
        if record:
            self._load_record(record, is_duplicate)
        self._update_extra_visibility(self.category_input.currentText())

    def _build_main_tab(self) -> QWidget:
        main_widget = QWidget()
        form = QFormLayout()
        form.addRow("Categoria:", self.category_input)
        form.addRow("Numero:", self.doc_number_input)
        form.addRow("Data do registro:", self.record_date_input)
        form.addRow("Interessado/Servidor:", self.interested_input)
        form.addRow("Orgao/Setor/Origem:", self.origin_input)
        form.addRow("Assunto:", self.subject_input)
        form.addRow("Status:", self.status_input)
        form.addRow("Tags:", self.tags_input)
        form.addRow("Observacoes:", self.notes_input)
        form.addRow(self.attachments_group)
        main_widget.setLayout(form)
        return main_widget

    def _build_extra_tab(self) -> QWidget:
        extra_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.protocol_group)
        layout.addWidget(self.convocation_group)
        layout.addWidget(self.schedule_group)
        layout.addWidget(self.send_group)
        layout.addWidget(self.project_group)
        layout.addStretch()
        extra_widget.setLayout(layout)
        return extra_widget

    def _build_extra_groups(self) -> None:
        self.protocol_group = QGroupBox("Protocolos Judiciais")
        self.protocol_process_input = QLineEdit()
        self.protocol_court_input = QLineEdit()
        self.protocol_deadline_input = QDateEdit()
        self.protocol_deadline_input.setCalendarPopup(True)
        self.protocol_deadline_input.setDate(QDate.currentDate())
        self.protocol_deadline_status = QComboBox()
        self.protocol_deadline_status.addItems(DEADLINE_STATUSES)
        form = QFormLayout()
        form.addRow("Nº processo:", self.protocol_process_input)
        form.addRow("Vara/Comarca:", self.protocol_court_input)
        form.addRow("Prazo:", self.protocol_deadline_input)
        form.addRow("Situacao:", self.protocol_deadline_status)
        self.protocol_group.setLayout(form)

        self.convocation_group = QGroupBox("Convocacoes")
        self.convocation_date = QDateEdit()
        self.convocation_date.setCalendarPopup(True)
        self.convocation_date.setDate(QDate.currentDate())
        self.convocation_location = QLineEdit()
        self.convocation_person = QLineEdit()
        self.convocation_attended = QComboBox()
        self.convocation_attended.addItems(["Nao", "Sim"])
        self.convocation_justification = QLineEdit()
        form = QFormLayout()
        form.addRow("Data:", self.convocation_date)
        form.addRow("Local:", self.convocation_location)
        form.addRow("Pessoa convocada:", self.convocation_person)
        form.addRow("Compareceu:", self.convocation_attended)
        form.addRow("Justificativa:", self.convocation_justification)
        self.convocation_group.setLayout(form)

        self.schedule_group = QGroupBox("Agendamentos")
        self.schedule_datetime = QDateTimeEdit()
        self.schedule_datetime.setCalendarPopup(True)
        self.schedule_datetime.setDateTime(QDateTime.currentDateTime())
        self.schedule_type = QComboBox()
        self.schedule_type.addItems(SCHEDULE_TYPES)
        self.schedule_location = QLineEdit()
        self.schedule_confirmed = QComboBox()
        self.schedule_confirmed.addItems(["Nao", "Sim"])
        form = QFormLayout()
        form.addRow("Data e hora:", self.schedule_datetime)
        form.addRow("Tipo:", self.schedule_type)
        form.addRow("Local:", self.schedule_location)
        form.addRow("Confirmado:", self.schedule_confirmed)
        self.schedule_group.setLayout(form)

        self.send_group = QGroupBox("Envio (Oficios/Informacoes/Despachos/Memorandos)")
        self.send_recipient = QLineEdit()
        self.send_medium = QComboBox()
        self.send_medium.addItems(SEND_MEDIA)
        self.send_date = QDateEdit()
        self.send_date.setCalendarPopup(True)
        self.send_date.setDate(QDate.currentDate())
        form = QFormLayout()
        form.addRow("Destinatario:", self.send_recipient)
        form.addRow("Meio:", self.send_medium)
        form.addRow("Data envio:", self.send_date)
        self.send_group.setLayout(form)

        self.project_group = QGroupBox("Projetos")
        self.project_stage = QLineEdit()
        self.project_owner = QLineEdit()
        self.project_due_date = QDateEdit()
        self.project_due_date.setCalendarPopup(True)
        self.project_due_date.setDate(QDate.currentDate())
        self.project_status = QComboBox()
        self.project_status.addItems(PROJECT_STATUSES)
        form = QFormLayout()
        form.addRow("Etapa:", self.project_stage)
        form.addRow("Responsavel:", self.project_owner)
        form.addRow("Data prevista:", self.project_due_date)
        form.addRow("Status projeto:", self.project_status)
        self.project_group.setLayout(form)

    def _build_attachments_group(self) -> None:
        self.attachments_group = QGroupBox("Anexos")
        self.attachments_list = QListWidget()
        add_btn = QPushButton("Adicionar")
        remove_btn = QPushButton("Remover")
        open_btn = QPushButton("Abrir")

        add_btn.clicked.connect(self._handle_add_attachment)
        remove_btn.clicked.connect(self._handle_remove_attachment)
        open_btn.clicked.connect(self._handle_open_attachment)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(open_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.attachments_list)
        layout.addLayout(btn_layout)
        self.attachments_group.setLayout(layout)

    def _handle_add_attachment(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo")
        if not file_path:
            return
        source = Path(file_path)
        attachments_dir = get_attachments_dir()
        attachments_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid4().hex}{source.suffix}"
        dest = attachments_dir / unique_name
        shutil.copy2(source, dest)
        rel_path = dest.relative_to(get_data_dir()).as_posix()
        item = QListWidgetItem(source.name)
        item.setData(Qt.UserRole, {"id": None, "path": rel_path})
        self.attachments_list.addItem(item)
        self.attachments_to_add.append({"file_name": source.name, "path": rel_path})

    def _handle_remove_attachment(self) -> None:
        item = self.attachments_list.currentItem()
        if not item:
            return
        info = item.data(Qt.UserRole) or {}
        attachment_id = info.get("id")
        rel_path = info.get("path")
        if attachment_id:
            self.attachments_to_delete.append(attachment_id)
        if rel_path:
            try:
                (get_data_dir() / rel_path).unlink(missing_ok=True)
            except OSError:
                pass
        self.attachments_list.takeItem(self.attachments_list.row(item))

    def _handle_open_attachment(self) -> None:
        item = self.attachments_list.currentItem()
        if not item:
            return
        info = item.data(Qt.UserRole) or {}
        rel_path = info.get("path")
        if not rel_path:
            return
        file_path = get_data_dir() / rel_path
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))

    def _update_extra_visibility(self, category: str) -> None:
        is_protocol = category == "Protocolos Judiciais"
        is_convocation = category == "Convocacoes"
        is_schedule = category == "Agendamentos"
        is_send = category in {"Oficios", "Informacoes", "Despachos", "Memorandos"}
        is_project = category == "Projetos"

        self.protocol_group.setVisible(is_protocol)
        self.convocation_group.setVisible(is_convocation)
        self.schedule_group.setVisible(is_schedule)
        self.send_group.setVisible(is_send)
        self.project_group.setVisible(is_project)

    def _load_record(self, record: Dict, is_duplicate: bool) -> None:
        self.category_input.setCurrentText(record.get("category", CATEGORIES[0]))
        self.doc_number_input.setText(record.get("doc_number", "") or "")
        if record.get("record_date"):
            try:
                self.record_date_input.setDate(
                    QDate.fromString(record["record_date"], "yyyy-MM-dd")
                )
            except Exception:
                pass
        if is_duplicate:
            self.record_date_input.setDate(QDate.currentDate())
        self.interested_input.setText(record.get("interested", "") or "")
        self.origin_input.setText(record.get("origin", "") or "")
        self.subject_input.setText(record.get("subject", "") or "")
        if record.get("status"):
            self.status_input.setCurrentText(record["status"])
        self.tags_input.setText(record.get("tags", "") or "")
        self.notes_input.setPlainText(record.get("notes", "") or "")

        self.protocol_process_input.setText(record.get("protocol_process_number", "") or "")
        self.protocol_court_input.setText(record.get("protocol_court", "") or "")
        if record.get("protocol_deadline_date"):
            self.protocol_deadline_input.setDate(
                QDate.fromString(record["protocol_deadline_date"], "yyyy-MM-dd")
            )
        if record.get("protocol_deadline_status"):
            self.protocol_deadline_status.setCurrentText(record["protocol_deadline_status"])

        if record.get("convocation_date"):
            self.convocation_date.setDate(
                QDate.fromString(record["convocation_date"], "yyyy-MM-dd")
            )
        self.convocation_location.setText(record.get("convocation_location", "") or "")
        self.convocation_person.setText(record.get("convocation_person", "") or "")
        if record.get("convocation_attended") is not None:
            self.convocation_attended.setCurrentText(
                "Sim" if record.get("convocation_attended") else "Nao"
            )
        self.convocation_justification.setText(
            record.get("convocation_justification", "") or ""
        )

        if record.get("schedule_datetime"):
            self.schedule_datetime.setDateTime(
                QDateTime.fromString(record["schedule_datetime"], "yyyy-MM-dd HH:mm:ss")
            )
        if record.get("schedule_type"):
            self.schedule_type.setCurrentText(record["schedule_type"])
        self.schedule_location.setText(record.get("schedule_location", "") or "")
        if record.get("schedule_confirmed") is not None:
            self.schedule_confirmed.setCurrentText(
                "Sim" if record.get("schedule_confirmed") else "Nao"
            )

        self.send_recipient.setText(record.get("send_recipient", "") or "")
        if record.get("send_medium"):
            self.send_medium.setCurrentText(record["send_medium"])
        if record.get("send_date"):
            self.send_date.setDate(QDate.fromString(record["send_date"], "yyyy-MM-dd"))

        self.project_stage.setText(record.get("project_stage", "") or "")
        self.project_owner.setText(record.get("project_owner", "") or "")
        if record.get("project_due_date"):
            self.project_due_date.setDate(
                QDate.fromString(record["project_due_date"], "yyyy-MM-dd")
            )
        if record.get("project_status"):
            self.project_status.setCurrentText(record["project_status"])

        if self.record_id and not is_duplicate:
            for attachment in db.list_attachments(self.record_id):
                item = QListWidgetItem(attachment["file_name"])
                item.setData(
                    Qt.UserRole,
                    {"id": attachment["id"], "path": attachment["stored_path"]},
                )
                self.attachments_list.addItem(item)

    def _handle_save(self) -> None:
        if not self.category_input.currentText().strip():
            QMessageBox.warning(self, "Validacao", "Categoria obrigatoria.")
            return

        record_date = self.record_date_input.date().toString("yyyy-MM-dd")
        if not record_date:
            QMessageBox.warning(self, "Validacao", "Data obrigatoria.")
            return

        is_protocol = self.protocol_group.isVisible()
        is_convocation = self.convocation_group.isVisible()
        is_schedule = self.schedule_group.isVisible()
        is_send = self.send_group.isVisible()
        is_project = self.project_group.isVisible()

        record_data = {
            "category": self.category_input.currentText(),
            "doc_number": self.doc_number_input.text().strip(),
            "record_date": record_date,
            "interested": self.interested_input.text().strip(),
            "origin": self.origin_input.text().strip(),
            "subject": self.subject_input.text().strip(),
            "status": self.status_input.currentText(),
            "tags": self.tags_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "protocol_process_number": self.protocol_process_input.text().strip(),
            "protocol_court": self.protocol_court_input.text().strip(),
            "protocol_deadline_date": self.protocol_deadline_input.date().toString(
                "yyyy-MM-dd"
            )
            if is_protocol
            else None,
            "protocol_deadline_status": self.protocol_deadline_status.currentText()
            if is_protocol
            else None,
            "convocation_date": self.convocation_date.date().toString("yyyy-MM-dd")
            if is_convocation
            else None,
            "convocation_location": self.convocation_location.text().strip()
            if is_convocation
            else None,
            "convocation_person": self.convocation_person.text().strip()
            if is_convocation
            else None,
            "convocation_attended": 1
            if is_convocation and self.convocation_attended.currentText() == "Sim"
            else 0
            if is_convocation
            else None,
            "convocation_justification": self.convocation_justification.text().strip()
            if is_convocation
            else None,
            "schedule_datetime": self.schedule_datetime.dateTime().toString(
                "yyyy-MM-dd HH:mm:ss"
            )
            if is_schedule
            else None,
            "schedule_type": self.schedule_type.currentText() if is_schedule else None,
            "schedule_location": self.schedule_location.text().strip()
            if is_schedule
            else None,
            "schedule_confirmed": 1
            if is_schedule and self.schedule_confirmed.currentText() == "Sim"
            else 0
            if is_schedule
            else None,
            "send_recipient": self.send_recipient.text().strip() if is_send else None,
            "send_medium": self.send_medium.currentText() if is_send else None,
            "send_date": self.send_date.date().toString("yyyy-MM-dd")
            if is_send
            else None,
            "project_stage": self.project_stage.text().strip() if is_project else None,
            "project_owner": self.project_owner.text().strip() if is_project else None,
            "project_due_date": self.project_due_date.date().toString("yyyy-MM-dd")
            if is_project
            else None,
            "project_status": self.project_status.currentText() if is_project else None,
        }

        try:
            rec_date = datetime.fromisoformat(record_data["record_date"]).date()
        except ValueError:
            QMessageBox.warning(self, "Validacao", "Data invalida.")
            return

        if record_data["doc_number"]:
            similar = db.find_similar_records(
                record_data["doc_number"], rec_date.year, rec_date.month
            )
            if similar and not self.record_id:
                res = QMessageBox.question(
                    self,
                    "Aviso",
                    "Ja existe registro parecido neste mes. Deseja salvar mesmo assim?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if res != QMessageBox.Yes:
                    return

        if self.record_id:
            db.update_record(self.record_id, record_data)
            record_id = self.record_id
        else:
            record_id = db.create_record(record_data)

        for item in self.attachments_to_add:
            db.add_attachment(record_id, item["file_name"], item["path"])

        for attachment_id in self.attachments_to_delete:
            db.delete_attachment(attachment_id)

        self.accept()


class MonthlyReportDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Relatorio Mensal")
        self.setModal(True)

        today = date.today()
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(today.month)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(today.year)

        self.output_input = QLineEdit()
        browse_btn = QPushButton("Selecionar pasta")
        browse_btn.clicked.connect(self._choose_folder)

        form = QFormLayout()
        form.addRow("Mes:", self.month_spin)
        form.addRow("Ano:", self.year_spin)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(browse_btn)
        form.addRow("Pasta de saida:", output_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Selecionar pasta")
        if folder:
            self.output_input.setText(folder)

    def get_values(self):
        return self.month_spin.value(), self.year_spin.value(), self.output_input.text()


class AnnualReportDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Relatorio Anual")
        self.setModal(True)

        today = date.today()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(today.year)

        self.output_input = QLineEdit()
        browse_btn = QPushButton("Selecionar pasta")
        browse_btn.clicked.connect(self._choose_folder)

        form = QFormLayout()
        form.addRow("Ano:", self.year_spin)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(browse_btn)
        form.addRow("Pasta de saida:", output_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Selecionar pasta")
        if folder:
            self.output_input.setText(folder)

    def get_values(self):
        return self.year_spin.value(), self.output_input.text()
