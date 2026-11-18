"""Desktop interface for five best efficiency point (BEP) correlations for pumps as turbines (PAT)."""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QFrame, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget, QHeaderView, QAbstractItemView,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models import Prediction, calculate_from_percent


STYLESHEET = """
/* Light theme. Edit these colors to customize the interface. */
QMainWindow, QWidget#central {background: #FFFFFF; color: #172033;}
QWidget {font-family: 'Segoe UI', 'Arial'; font-size: 12px; color: #172033;}
QFrame#panel {background: #FFFFFF; border: 1px solid #DDE4EE; border-radius: 12px;}
QLabel#heading {font-size: 24px; font-weight: 700; color: #172033;}
QLabel#subheading {font-size: 12px; color: #596579;}
QLabel#section {font-size: 15px; font-weight: 650; color: #172033;}
QLabel#helper {font-size: 11px; color: #64748B;}
QLineEdit {background: #FFFFFF; padding: 10px 11px; border: 1px solid #CDD6E2;
           border-radius: 7px; color: #172033; selection-background-color: #FEE2E2;}
QLineEdit:focus {border: 1px solid #DC2626;}
QPushButton {background: #F8FAFC; color: #172033; padding: 11px 12px;
             border: 1px solid #CDD6E2; border-radius: 7px; font-weight: 600;}
QPushButton:hover {background: #EFF4FA;}
QPushButton:disabled {background: #F1F5F9; color: #94A3B8;}
QPushButton#primary {background: #DC2626; color: #FFFFFF; border: 1px solid #DC2626;}
QPushButton#primary:hover {background: #B91C1C;}
QTabWidget::pane {border: 1px solid #DDE4EE; background: #FFFFFF;
                  border-radius: 8px;}
QTabBar::tab {background: #F1F5F9; color: #475569; padding: 10px 18px; margin-right: 4px;
              border-top-left-radius: 6px; border-top-right-radius: 6px;}
QTabBar::tab:selected {background: #FFFFFF; color: #172033;}
QTabBar::tab:hover {background: #EAF0F8;}
QTableWidget {background: #FFFFFF; alternate-background-color: #F8FAFC;
              color: #172033; gridline-color: #E4EAF2;
              border: none; selection-background-color: #FEE2E2; selection-color: #172033;}
QTableWidget::item:selected {background: #FEE2E2; color: #172033;}
QHeaderView::section {background: #F1F5F9; color: #172033; padding: 10px 6px;
                      border: 1px solid #DDE4EE; font-weight: 600;}
QTextBrowser {background: #FFFFFF; color: #172033; border: 1px solid #DDE4EE;
              border-radius: 7px; padding: 9px;}
QScrollArea {border: none; background: #FFFFFF;}
QScrollBar:vertical {background: #F1F5F9; width: 11px;}
QScrollBar::handle:vertical {background: #C7D1DF; border-radius: 5px;}
"""


def parse_number(widget: QLineEdit, label: str, required: bool = False):
    text = widget.text().strip().replace(" ", "")
    if not text:
        if required:
            raise ValueError(f"Enter {label}.")
        return None
    # Accept a decimal comma (70,5) or point (70.5) without a thousands separator.
    if "," in text and "." in text:
        raise ValueError(f"{label}: use only one decimal separator (comma or point).")
    try:
        value = float(text.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"{label}: invalid numeric value.") from exc
    if not math.isfinite(value):
        raise ValueError(f"{label}: enter a finite number.")
    return value


def text_value(value, decimals=5) -> str:
    return "—" if value is None else f"{value:.{decimals}f}".replace(".", ",")


class ComparisonChart(FigureCanvas):
    def __init__(self):
        fig = Figure(figsize=(9.1, 5.2), facecolor="#FFFFFF", constrained_layout=True)
        super().__init__(fig)
        self.fig = fig
        self.empty()

    def empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#FFFFFF")
        ax.text(0.5, 0.5, "Enter the parameters and click Calculate all five methods",
                ha="center", va="center", color="#64838B", fontsize=13)
        ax.set_axis_off()
        self.draw_idle()

    def update_predictions(self, results: list[Prediction]):
        valid = [r for r in results if r.h is not None and r.q is not None]
        if not valid:
            self.empty()
            return
        self.fig.clear()
        ax_h, ax_q = self.fig.subplots(1, 2)
        for ax, key, title, color in [
            (ax_h, "h", "Head ratio (h)", "#6D6D6D"),
            (ax_q, "q", "Flow rate ratio (q)", "#6D6D6D"),
        ]:
            values = [getattr(r, key) for r in valid]
            ax.set_facecolor("#FFFFFF")
            ax.barh([r.method for r in valid], values, color=color, height=0.62)
            ax.invert_yaxis()
            ax.set_title(title, color="#172033", fontsize=11, pad=14)
            ax.tick_params(colors="#475569", labelsize=9, length=0)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.grid(axis="x", color="#DDE4EE", alpha=0.85)
            ax.set_axisbelow(True)
            ax.set_xlim(0, max(values) * 1.17)
            for i, value in enumerate(values):
                ax.text(value * 1.012, i, f"{value:.3f}", color="#172033", va="center", fontsize=9)
        self.draw_idle()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAT - BEP Simulator | Section 2.2 Correlations")
        self.setMinimumSize(1080, 700)
        self.resize(1360, 850)
        self.predictions: list[Prediction] = []
        self.build_ui()

    def build_ui(self):
        root = QWidget()
        root.setObjectName("central")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(17)

        title = QLabel("PAT - Physical Model Simulator")
        title.setObjectName("heading")
        subtitle = QLabel("Pump BEP → Turbine BEP | Section 2.2 correlations | One pump per calculation")
        subtitle.setObjectName("subheading")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter, 1)

        left = QScrollArea()
        left.setWidgetResizable(True)
        left.setMinimumWidth(315)
        left.setMaximumWidth(420)
        left_inner = QFrame()
        left_inner.setObjectName("panel")
        left.setWidget(left_inner)
        inputs = QVBoxLayout(left_inner)
        inputs.setContentsMargins(18, 20, 18, 18)
        inputs.setSpacing(13)
        section_input = QLabel("Input parameters")
        section_input.setObjectName("section")
        inputs.addWidget(section_input)
        hint = QLabel("Fields marked with * are required. Use a decimal comma or point.")
        hint.setObjectName("helper")
        inputs.addWidget(hint)

        self.eta_p = self.field(inputs, "Pump efficiency, ηp (%) *", "e.g., 70")
        self.eta_h = self.field(inputs, "Hydraulic efficiency, ηh (%)", "Optional (Schmiedl only)")
        hint_h = QLabel("Enter ηh separately from ηp. If ηh is unknown, the Schmiedl result is unavailable.")
        hint_h.setObjectName("helper")
        hint_h.setWordWrap(True)
        inputs.addWidget(hint_h)
        self.qp = self.field(inputs, "Pump BEP flow rate, Qp (m³/h)", "Optional, e.g., 35,0")
        self.hp = self.field(inputs, "Pump BEP head, Hp (m)", "Optional, e.g., 18,0")
        hint_bep = QLabel("Enter Qp to estimate Qt,BEP and Hp to estimate Ht,BEP. Leave both blank to see only h and q.")
        hint_bep.setObjectName("helper")
        hint_bep.setWordWrap(True)
        inputs.addWidget(hint_bep)
        calc = QPushButton("Calculate all five methods")
        calc.setObjectName("primary")
        calc.clicked.connect(self.calculate)
        inputs.addWidget(calc)
        controls = QHBoxLayout()
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_csv)
        controls.addWidget(self.export_btn)
        reset = QPushButton("Clear")
        reset.clicked.connect(self.reset_all)
        controls.addWidget(reset)
        inputs.addLayout(controls)
        inputs.addStretch()
        splitter.addWidget(left)

        right = QFrame()
        right.setObjectName("panel")
        content = QVBoxLayout(right)
        content.setContentsMargins(17, 18, 17, 16)
        content.setSpacing(11)
        results_label = QLabel("Comparison results")
        results_label.setObjectName("section")
        content.addWidget(results_label)
        self.message = QLabel("Enter ηp to calculate the results.")
        self.message.setObjectName("subheading")
        self.message.setWordWrap(True)
        content.addWidget(self.message)
        tabs = QTabWidget()
        content.addWidget(tabs, 1)

        table_page = QWidget()
        table_layout = QVBoxLayout(table_page)
        table_layout.setContentsMargins(9, 13, 9, 9)
        self.table = QTableWidget(5, 6)
        self.table.setHorizontalHeaderLabels([
            "Correlation", "h = Ht/Hp", "q = Qt/Qp", "Ht (m)", "Qt (m³/h)", "Status",
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setDefaultSectionSize(53)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        table_layout.addWidget(self.table, 1)
        self.table.itemSelectionChanged.connect(self.show_selected_formula)
        formula_title = QLabel("Selected model equation")
        formula_title.setObjectName("section")
        table_layout.addWidget(formula_title)
        self.formula_box = QTextBrowser()
        self.formula_box.setMinimumHeight(125)
        self.formula_box.setMaximumHeight(200)
        self.formula_box.setText("After calculating, select a row to view its equation and warnings.")
        table_layout.addWidget(self.formula_box)
        tabs.addTab(table_page, "Table and equations")

        plot_page = QWidget()
        plot_layout = QVBoxLayout(plot_page)
        plot_layout.setContentsMargins(9, 12, 9, 9)
        self.chart = ComparisonChart()
        plot_layout.addWidget(self.chart)
        tabs.addTab(plot_page, "Charts")
        splitter.addWidget(right)
        splitter.setSizes([345, 965])

        bottom = QLabel(
            "Source: Candidate physical models and correlations for hybrid PAT modeling, §§2.1–2.2 (2026). "
            "Check the range of applicability and validate empirical predictions against experimental data.")
        bottom.setObjectName("helper")
        bottom.setWordWrap(True)
        outer.addWidget(bottom)

    @staticmethod
    def field(layout: QVBoxLayout, label: str, placeholder: str) -> QLineEdit:
        caption = QLabel(label)
        layout.addWidget(caption)
        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        layout.addWidget(entry)
        return entry

    def calculate(self):
        try:
            ep = parse_number(self.eta_p, "ηp", required=True)
            eh = parse_number(self.eta_h, "ηh")
            qp = parse_number(self.qp, "Qp,BEP")
            hp = parse_number(self.hp, "Hp,BEP")
            results = calculate_from_percent(ep, eh, qp, hp)
        except (ValueError, OverflowError, ZeroDivisionError) as exc:
            QMessageBox.warning(self, "Invalid input", str(exc))
            return
        self.predictions = results
        self.table.clearContents()
        for i, pred in enumerate(results):
            row = [
                f"{pred.method} ({pred.year})",
                text_value(pred.h), text_value(pred.q),
                text_value(pred.ht_m, 4), text_value(pred.qt_m3h, 4),
                "Unavailable" if pred.h is None else ("Review" if pred.observation else "Calculated"),
            ]
            for j, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter |
                                      (Qt.AlignmentFlag.AlignLeft if j in (0, 5)
                                       else Qt.AlignmentFlag.AlignRight))
                self.table.setItem(i, j, item)
        self.table.selectRow(0)
        self.chart.update_predictions(results)
        self.export_btn.setEnabled(True)
        num = sum(p.h is not None for p in results)
        self.message.setText(
            f"Calculated {num} of 5 correlations. "
            + ("Qt and Ht are estimated in physical units." if qp is not None and hp is not None
               else "Enter Qp to estimate Qt or Hp to estimate Ht.")
            + " The values are empirical predictions.")

    def show_selected_formula(self):
        i = self.table.currentRow()
        if i < 0 or i >= len(self.predictions):
            return
        row = self.predictions[i]
        observation = row.observation or "No numerical warnings for these inputs."
        self.formula_box.setHtml(
            f"<div style='color:#172033;font-size:13px'>"
            f"<b>{row.method} ({row.year})</b><p>{row.formula}</p>"
            f"<p>h = Ht,BEP/Hp,BEP &nbsp;&nbsp; | &nbsp;&nbsp; q = Qt,BEP/Qp,BEP</p>"
            f"<p style='color:#64748b'>{observation}</p>"
            f"</div>"
        )

    def export_csv(self):
        if not self.predictions:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save results", "PAT_BEP_results.csv",
                                              "CSV (*.csv)")
        if not path:
            return
        try:
            with open(Path(path), "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Modelo", "Ano", "h=Ht/Hp", "q=Qt/Qp", "Ht_m", "Qt_m3h",
                                 "Observacoes"])
                for r in self.predictions:
                    writer.writerow([r.method, r.year, r.h, r.q, r.ht_m, r.qt_m3h, r.observation])
        except OSError as exc:
            QMessageBox.critical(self, "Export error", str(exc))
            return
        QMessageBox.information(self, "File saved", f"Results exported to:\n{path}")

    def reset_all(self):
        for field in (self.eta_p, self.eta_h, self.qp, self.hp):
            field.clear()
        self.predictions = []
        self.table.clearContents()
        self.chart.empty()
        self.formula_box.setText("After calculating, select a row to view its equation and warnings.")
        self.message.setText("Enter ηp to calculate the results.")
        self.export_btn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#172033"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F8FAFC"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#172033"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#F8FAFC"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#172033"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#FEE2E2"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#172033"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
