from datetime import date

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QPushButton,
    QMessageBox,
)

from app.services.reports import generate_monthly_report, generate_annual_report


class MonthlyReportDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Relatorio Mensal")
        self.setModal(True)

        layout = QVBoxLayout()
        form = QFormLayout()
        today = date.today()

        self.month = QSpinBox()
        self.month.setRange(1, 12)
        self.month.setValue(today.month)
        self.year = QSpinBox()
        self.year.setRange(2000, 2100)
        self.year.setValue(today.year)

        form.addRow("Mes:", self.month)
        form.addRow("Ano:", self.year)
        layout.addLayout(form)

        btn = QPushButton("Gerar")
        btn.clicked.connect(self._generate)
        layout.addWidget(btn)
        self.setLayout(layout)

    def _generate(self):
        pdf_path, xlsx_path = generate_monthly_report(
            self.db, self.year.value(), self.month.value()
        )
        QMessageBox.information(
            self,
            "Relatorio gerado",
            f"PDF: {pdf_path}\nExcel: {xlsx_path}",
        )
        self.accept()


class AnnualReportDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Relatorio Anual")
        self.setModal(True)

        layout = QVBoxLayout()
        form = QFormLayout()
        today = date.today()

        self.year = QSpinBox()
        self.year.setRange(2000, 2100)
        self.year.setValue(today.year)

        form.addRow("Ano:", self.year)
        layout.addLayout(form)

        btn = QPushButton("Gerar")
        btn.clicked.connect(self._generate)
        layout.addWidget(btn)
        self.setLayout(layout)

    def _generate(self):
        pdf_path, xlsx_path = generate_annual_report(self.db, self.year.value())
        QMessageBox.information(
            self,
            "Relatorio gerado",
            f"PDF: {pdf_path}\nExcel: {xlsx_path}",
        )
        self.accept()
