import os
import shutil
from datetime import datetime

from PySide6.QtCore import QDate, QDateTime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QDateEdit,
    QDateTimeEdit,
    QWidget,
    QStackedWidget,
    QLabel,
)

from app.services.records import STATUSES, get_categories, to_storage_category, to_display_category
from app.services.utils import attachments_dir


class RecordDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Registro")
        self.setMinimumWidth(600)
        self.record_id = None
        self.attachment_real_path = ""

        layout = QVBoxLayout()
        form = QFormLayout()

        self.category = QComboBox()
        self.category.addItems(get_categories(db))
        self.category.currentTextChanged.connect(self._on_category_changed)

        self.doc_number = QLineEdit()
        self.record_date = QDateEdit()
        self.record_date.setCalendarPopup(True)
        self.record_date.setDate(QDate.currentDate())
        self.interested = QLineEdit()
        self.origin = QLineEdit()
        self.subject = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(STATUSES)
        self.tags = QLineEdit()
        self.notes = QTextEdit()

        form.addRow("Categoria*:", self.category)
        form.addRow("Numero:", self.doc_number)
        form.addRow("Data*:", self.record_date)
        form.addRow("Interessado/Servidor:", self.interested)
        form.addRow("Orgao/Setor/Origem:", self.origin)
        form.addRow("Assunto:", self.subject)
        form.addRow("Status*:", self.status)
        form.addRow("Tags (separar por virgula):", self.tags)
        form.addRow("Observacoes:", self.notes)

        layout.addLayout(form)

        attach_layout = QHBoxLayout()
        self.attachment_path = QLineEdit()
        self.attachment_path.setReadOnly(True)
        self.attachment_mode = QComboBox()
        self.attachment_mode.addItems(["Copiar para app", "Link externo"])
        btn_attach = QPushButton("Anexar arquivo")
        btn_attach.clicked.connect(self._choose_attachment)
        attach_layout.addWidget(self.attachment_path)
        attach_layout.addWidget(self.attachment_mode)
        attach_layout.addWidget(btn_attach)
        layout.addWidget(QLabel("Anexos:"))
        layout.addLayout(attach_layout)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_protocolos())
        self.stack.addWidget(self._build_convocacoes())
        self.stack.addWidget(self._build_agendamentos())
        self.stack.addWidget(self._build_envio())
        self.stack.addWidget(self._build_projetos())
        self.stack.addWidget(self._build_empty())
        layout.addWidget(self.stack)

        buttons = QHBoxLayout()
        self.btn_save = QPushButton("Salvar")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)
        layout.addLayout(buttons)

        self.setLayout(layout)
        self._on_category_changed(self.category.currentText())

    def _build_protocolos(self) -> QWidget:
        w = QWidget()
        form = QFormLayout()
        self.process_number = QLineEdit()
        self.court = QLineEdit()
        self.deadline_date = QDateEdit()
        self.deadline_date.setCalendarPopup(True)
        self.deadline_date.setDate(QDate.currentDate())
        self.deadline_status = QComboBox()
        self.deadline_status.addItems(["OK", "Alerta", "Atrasado"])
        form.addRow("N. do processo:", self.process_number)
        form.addRow("Vara/Comarca:", self.court)
        form.addRow("Prazo:", self.deadline_date)
        form.addRow("Situacao do prazo:", self.deadline_status)
        w.setLayout(form)
        return w

    def _build_convocacoes(self) -> QWidget:
        w = QWidget()
        form = QFormLayout()
        self.convocation_date = QDateEdit()
        self.convocation_date.setCalendarPopup(True)
        self.convocation_date.setDate(QDate.currentDate())
        self.convocation_location = QLineEdit()
        self.convoked_person = QLineEdit()
        self.attended = QComboBox()
        self.attended.addItems(["Sim", "Nao"])
        self.justification = QLineEdit()
        form.addRow("Data convocacao:", self.convocation_date)
        form.addRow("Local:", self.convocation_location)
        form.addRow("Pessoa convocada:", self.convoked_person)
        form.addRow("Compareceu?:", self.attended)
        form.addRow("Justificativa (se nao):", self.justification)
        w.setLayout(form)
        return w

    def _build_agendamentos(self) -> QWidget:
        w = QWidget()
        form = QFormLayout()
        self.schedule_datetime = QDateTimeEdit()
        self.schedule_datetime.setCalendarPopup(True)
        self.schedule_datetime.setDateTime(QDateTime.currentDateTime())
        self.schedule_type = QComboBox()
        self.schedule_type.addItems(["Medico", "Psicologico", "Outro"])
        self.schedule_location = QLineEdit()
        self.schedule_confirmed = QComboBox()
        self.schedule_confirmed.addItems(["Sim", "Nao"])
        form.addRow("Data e hora:", self.schedule_datetime)
        form.addRow("Tipo:", self.schedule_type)
        form.addRow("Local:", self.schedule_location)
        form.addRow("Confirmado?:", self.schedule_confirmed)
        w.setLayout(form)
        return w

    def _build_envio(self) -> QWidget:
        w = QWidget()
        form = QFormLayout()
        self.recipient = QLineEdit()
        self.send_method = QComboBox()
        self.send_method.addItems(["E-mail", "SEI", "Outro"])
        self.send_date = QDateEdit()
        self.send_date.setCalendarPopup(True)
        self.send_date.setDate(QDate.currentDate())
        form.addRow("Destinatario:", self.recipient)
        form.addRow("Meio de envio:", self.send_method)
        form.addRow("Data de envio:", self.send_date)
        w.setLayout(form)
        return w

    def _build_projetos(self) -> QWidget:
        w = QWidget()
        form = QFormLayout()
        self.project_stage = QLineEdit()
        self.project_responsible = QLineEdit()
        self.project_due_date = QDateEdit()
        self.project_due_date.setCalendarPopup(True)
        self.project_due_date.setDate(QDate.currentDate())
        self.project_status = QLineEdit()
        form.addRow("Etapa:", self.project_stage)
        form.addRow("Responsavel:", self.project_responsible)
        form.addRow("Data prevista:", self.project_due_date)
        form.addRow("Status do projeto:", self.project_status)
        w.setLayout(form)
        return w

    def _build_empty(self) -> QWidget:
        w = QWidget()
        form = QFormLayout()
        form.addRow("Campos extras:", QLabel("Sem campos adicionais para esta categoria."))
        w.setLayout(form)
        return w

    def _on_category_changed(self, category: str):
        if category == "Protocolos Judiciais":
            self.stack.setCurrentIndex(0)
        elif category == "Convocacoes":
            self.stack.setCurrentIndex(1)
        elif category == "Agendamentos":
            self.stack.setCurrentIndex(2)
        elif category in ["Oficios", "Informacoes", "Despachos", "Memorandos"]:
            self.stack.setCurrentIndex(3)
        elif category == "Projetos":
            self.stack.setCurrentIndex(4)
        else:
            self.stack.setCurrentIndex(5)

    def _choose_attachment(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo")
        if not file_path:
            return
        mode = self.attachment_mode.currentText()
        if mode == "Copiar para app":
            os.makedirs(attachments_dir(), exist_ok=True)
            base_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest = os.path.join(attachments_dir(), f"{timestamp}_{base_name}")
            shutil.copy2(file_path, dest)
            rel = os.path.relpath(dest, os.path.abspath(os.path.join(attachments_dir(), "..")))
            self.attachment_real_path = dest
            self.attachment_path.setText(rel)
        else:
            self.attachment_real_path = file_path
            self.attachment_path.setText(file_path)

    def _on_save(self):
        if not self.category.currentText().strip():
            QMessageBox.warning(self, "Atencao", "Categoria obrigatoria.")
            return
        if not self.record_date.date().isValid():
            QMessageBox.warning(self, "Atencao", "Data invalida.")
            return
        if not self.status.currentText().strip():
            QMessageBox.warning(self, "Atencao", "Status obrigatorio.")
            return
        self.accept()

    def set_record(self, record: dict, is_duplicate: bool = False):
        self.record_id = record.get("id")
        if is_duplicate:
            self.record_id = None
        self.category.setCurrentText(to_display_category(self.db, record.get("category", "")))
        self.doc_number.setText(record.get("doc_number", ""))
        rd = record.get("record_date", "")
        if rd:
            self.record_date.setDate(QDate.fromString(rd, "yyyy-MM-dd"))
        self.interested.setText(record.get("interested", ""))
        self.origin.setText(record.get("origin", ""))
        self.subject.setText(record.get("subject", ""))
        self.status.setCurrentText(record.get("status", ""))
        self.tags.setText(record.get("tags", ""))
        self.notes.setPlainText(record.get("notes", ""))
        self.attachment_path.setText(record.get("attachment_path", ""))
        mode = record.get("attachment_mode", "Copiar para app")
        self.attachment_mode.setCurrentText(mode)
        self.attachment_real_path = record.get("attachment_path", "")

        self.process_number.setText(record.get("process_number", ""))
        self.court.setText(record.get("court", ""))
        dd = record.get("deadline_date", "")
        if dd:
            self.deadline_date.setDate(QDate.fromString(dd, "yyyy-MM-dd"))
        self.deadline_status.setCurrentText(record.get("deadline_status", "OK"))

        cd = record.get("convocation_date", "")
        if cd:
            self.convocation_date.setDate(QDate.fromString(cd, "yyyy-MM-dd"))
        self.convocation_location.setText(record.get("convocation_location", ""))
        self.convoked_person.setText(record.get("convoked_person", ""))
        self.attended.setCurrentText("Sim" if record.get("attended") else "Nao")
        self.justification.setText(record.get("justification", ""))

        sched = record.get("schedule_datetime", "")
        if sched:
            self.schedule_datetime.setDateTime(QDateTime.fromString(sched, "yyyy-MM-dd HH:mm"))
        self.schedule_type.setCurrentText(record.get("schedule_type", "Medico"))
        self.schedule_location.setText(record.get("schedule_location", ""))
        self.schedule_confirmed.setCurrentText("Sim" if record.get("schedule_confirmed") else "Nao")

        self.recipient.setText(record.get("recipient", ""))
        self.send_method.setCurrentText(record.get("send_method", "E-mail"))
        sd = record.get("send_date", "")
        if sd:
            self.send_date.setDate(QDate.fromString(sd, "yyyy-MM-dd"))

        self.project_stage.setText(record.get("project_stage", ""))
        self.project_responsible.setText(record.get("project_responsible", ""))
        pd = record.get("project_due_date", "")
        if pd:
            self.project_due_date.setDate(QDate.fromString(pd, "yyyy-MM-dd"))
        self.project_status.setText(record.get("project_status", ""))

    def get_values(self) -> dict:
        category_display = self.category.currentText().strip()
        category = to_storage_category(self.db, category_display)
        values = {
            "category": category,
            "doc_number": self.doc_number.text().strip(),
            "record_date": self.record_date.date().toString("yyyy-MM-dd"),
            "interested": self.interested.text().strip(),
            "origin": self.origin.text().strip(),
            "subject": self.subject.text().strip(),
            "status": self.status.currentText().strip(),
            "tags": self.tags.text().strip(),
            "notes": self.notes.toPlainText().strip(),
            "attachment_path": self.attachment_path.text().strip(),
            "attachment_mode": self.attachment_mode.currentText(),
        }
        if category_display == "Protocolos Judiciais":
            values.update(
                {
                    "process_number": self.process_number.text().strip(),
                    "court": self.court.text().strip(),
                    "deadline_date": self.deadline_date.date().toString("yyyy-MM-dd"),
                    "deadline_status": self.deadline_status.currentText(),
                }
            )
        else:
            values.update({"process_number": "", "court": "", "deadline_date": "", "deadline_status": ""})

        if category_display == "Convocacoes":
            values.update(
                {
                    "convocation_date": self.convocation_date.date().toString("yyyy-MM-dd"),
                    "convocation_location": self.convocation_location.text().strip(),
                    "convoked_person": self.convoked_person.text().strip(),
                    "attended": 1 if self.attended.currentText() == "Sim" else 0,
                    "justification": self.justification.text().strip(),
                }
            )
        else:
            values.update(
                {
                    "convocation_date": "",
                    "convocation_location": "",
                    "convoked_person": "",
                    "attended": 0,
                    "justification": "",
                }
            )

        if category_display == "Agendamentos":
            values.update(
                {
                    "schedule_datetime": self.schedule_datetime.dateTime().toString("yyyy-MM-dd HH:mm"),
                    "schedule_type": self.schedule_type.currentText(),
                    "schedule_location": self.schedule_location.text().strip(),
                    "schedule_confirmed": 1 if self.schedule_confirmed.currentText() == "Sim" else 0,
                }
            )
        else:
            values.update(
                {
                    "schedule_datetime": "",
                    "schedule_type": "",
                    "schedule_location": "",
                    "schedule_confirmed": 0,
                }
            )

        if category_display in ["Oficios", "Informacoes", "Despachos", "Memorandos"]:
            values.update(
                {
                    "recipient": self.recipient.text().strip(),
                    "send_method": self.send_method.currentText(),
                    "send_date": self.send_date.date().toString("yyyy-MM-dd"),
                }
            )
        else:
            values.update({"recipient": "", "send_method": "", "send_date": ""})

        if category_display == "Projetos":
            values.update(
                {
                    "project_stage": self.project_stage.text().strip(),
                    "project_responsible": self.project_responsible.text().strip(),
                    "project_due_date": self.project_due_date.date().toString("yyyy-MM-dd"),
                    "project_status": self.project_status.text().strip(),
                }
            )
        else:
            values.update(
                {
                    "project_stage": "",
                    "project_responsible": "",
                    "project_due_date": "",
                    "project_status": "",
                }
            )
        return values
