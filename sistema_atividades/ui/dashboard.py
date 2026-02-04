from datetime import date

from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sistema_atividades import db
from sistema_atividades.constants import CATEGORIES, STATUSES


class StatCard(QWidget):
    def __init__(self, title: str, color: str):
        super().__init__()
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.value_label)
        layout.addWidget(title_label)
        self.setLayout(layout)
        self.setStyleSheet(
            f"background-color: {color}; border-radius: 8px; padding: 8px;"
        )

    def set_value(self, value: int) -> None:
        self.value_label.setText(str(value))


class DashboardWidget(QWidget):
    new_record_requested = Signal()
    monthly_report_requested = Signal()
    annual_report_requested = Signal()
    backup_requested = Signal()

    def __init__(self):
        super().__init__()
        self.month_total_label = QLabel("Total do mes: 0")
        self.month_total_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.category_cards = {cat: StatCard(cat, "#F9E5D4") for cat in CATEGORIES}
        self.status_cards = {status: StatCard(status, "#DCECF9") for status in STATUSES}

        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(240)

        layout = QVBoxLayout()
        layout.addWidget(self.month_total_label)
        layout.addWidget(self._build_shortcuts_group())
        layout.addWidget(self._build_cards_group("Totais por categoria", self.category_cards))
        layout.addWidget(self._build_cards_group("Totais por status", self.status_cards))
        layout.addWidget(self._build_chart_group())
        layout.addStretch()
        self.setLayout(layout)

        self.refresh()

    def _build_cards_group(self, title: str, cards: dict) -> QGroupBox:
        group = QGroupBox(title)
        grid = QGridLayout()
        row = 0
        col = 0
        for card in cards.values():
            grid.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        group.setLayout(grid)
        return group

    def _build_shortcuts_group(self) -> QGroupBox:
        group = QGroupBox("Atalhos")
        layout = QHBoxLayout()
        new_btn = QPushButton("Novo Registro")
        month_btn = QPushButton("Relatorio Mensal")
        year_btn = QPushButton("Relatorio Anual")
        backup_btn = QPushButton("Backup")
        new_btn.clicked.connect(self.new_record_requested.emit)
        month_btn.clicked.connect(self.monthly_report_requested.emit)
        year_btn.clicked.connect(self.annual_report_requested.emit)
        backup_btn.clicked.connect(self.backup_requested.emit)
        layout.addWidget(new_btn)
        layout.addWidget(month_btn)
        layout.addWidget(year_btn)
        layout.addWidget(backup_btn)
        group.setLayout(layout)
        return group

    def _build_chart_group(self) -> QGroupBox:
        group = QGroupBox("Lancamentos por dia")
        layout = QHBoxLayout()
        layout.addWidget(self.chart_view)
        group.setLayout(layout)
        return group

    def refresh(self) -> None:
        today = date.today()
        month_records = db.list_records_in_month(today.year, today.month)
        self.month_total_label.setText(f"Total do mes: {len(month_records)}")

        cat_counts = db.get_counts_by_category(today.year, today.month)
        for cat, card in self.category_cards.items():
            card.set_value(cat_counts.get(cat, 0))

        status_counts = db.get_counts_by_status(today.year, today.month)
        for status, card in self.status_cards.items():
            card.set_value(status_counts.get(status, 0))

        day_counts = db.get_counts_by_day(today.year, today.month)
        self._update_chart(day_counts, today)

    def _update_chart(self, day_counts: dict, today: date) -> None:
        bar_set = QBarSet("Registros")
        categories = []
        for day in range(1, 32):
            if day > 28:
                try:
                    date(today.year, today.month, day)
                except ValueError:
                    break
            bar_set.append(day_counts.get(day, 0))
            categories.append(str(day))

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Registros por dia do mes")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        self.chart_view.setChart(chart)
