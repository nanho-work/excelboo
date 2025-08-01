import pandas as pd

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QFileDialog, QHeaderView, QComboBox, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, QMarginsF, QRectF
from PyQt6.QtGui import QPainter, QFontMetrics
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPageLayout, QPageSize

from utils.pdf_exporter import export_table_to_pdf

from styles.theme_dark import dark_style
from styles.theme_light import light_style

from PyQt6.QtCore import QTimer


class MonthlySummaryViewer(QDialog):
    def __init__(self, full_df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("월별 요약 및 시각화")
        self.resize(800, 600)

        self.df = full_df.copy()
        self.df["접수일"] = pd.to_datetime(self.df["접수일"], errors="coerce")
        self.df = self.df.dropna(subset=["접수일"])
        self.df["월"] = self.df["접수일"].dt.to_period("M")

        self.layout = QVBoxLayout()
        self.label = QLabel("월별 요약 정보")
        self.table = QTableWidget()

        # --- Add month selector before generate_summary ---
        self.month_selector_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.available_months = sorted(self.df["월"].astype(str).unique())
        self.month_combo.addItems(self.available_months)
        self.month_combo.setCurrentIndex(len(self.available_months) - 1)
        self.month_combo.currentIndexChanged.connect(self.generate_summary)

        self.month_selector_layout.addWidget(QLabel("기준 월 선택:"))
        self.month_selector_layout.addWidget(self.month_combo)
        self.layout.insertLayout(0, self.month_selector_layout)
        # --- End month selector ---

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.table)

        self.print_button = QPushButton("PDF로 저장")
        self.print_button.clicked.connect(self.handle_print)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)

        self.setStyleSheet(dark_style)  # or light_style, depending on app logic

        # QTimer.singleShot(0, self.delayed_generate_summary)


    def showEvent(self, event):
        super().showEvent(event)
        self.generate_summary()

    def create_summary_table(self, curr_df, prev_df):
        df = pd.concat([prev_df, curr_df])

        prev_summary = prev_df.groupby(["가맹점명", "카드사"]).size().reset_index(name="전월")
        curr_summary = curr_df.groupby(["가맹점명", "카드사"]).size().reset_index(name="당월")

        merged = pd.merge(prev_summary, curr_summary, on=["가맹점명", "카드사"], how="outer").fillna(0)
        merged["전월"] = merged["전월"].astype(int)
        merged["당월"] = merged["당월"].astype(int)
        merged["증감률"] = ((merged["당월"] - merged["전월"]) / merged["전월"].replace(0, pd.NA)) * 100
        merged["증감률"] = pd.to_numeric(merged["증감률"], errors="coerce").round(1).fillna(0)

        all_cards = merged["카드사"].unique().tolist()
        reshaped = []
        for name, group in merged.groupby("가맹점명"):
            row = {"가맹점명": name}
            for card in all_cards:
                row[f"{card}_전월"] = 0
                row[f"{card}_당월"] = 0
                row[f"{card}_증감률"] = "0.0%"
            for _, r in group.iterrows():
                card = r["카드사"]
                row[f"{card}_전월"] = r["전월"]
                row[f"{card}_당월"] = r["당월"]
                arrow = "▲" if r["증감률"] > 0 else ("▼" if r["증감률"] < 0 else "")
                color = "🔴" if r["증감률"] > 0 else ("🔵" if r["증감률"] < 0 else "")
                row[f"{card}_증감률"] = f"{color} {abs(r['증감률'])}% {arrow}"
            reshaped.append(row)

        return pd.DataFrame(reshaped).fillna("")

    def populate_table(self, result_df):
        self.table.setRowCount(len(result_df))
        self.table.setColumnCount(len(result_df.columns))
        new_headers = []
        for col in result_df.columns:
            if "_" in col and not col.startswith("가맹점명"):
                parts = col.split("_")
                new_headers.append(f"{parts[0]}\n({parts[1]})")
            else:
                new_headers.append(col)
        self.table.setHorizontalHeaderLabels(new_headers)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        for i, row in result_df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if item:
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(i, j, item)

        font = self.table.font()
        font.setPointSize(13)
        self.table.setFont(font)
        self.table.resizeColumnsToContents()

    def generate_summary(self):
        df = self.df.copy()
        curr_month_str = self.month_combo.currentText()
        self.curr_month_str = curr_month_str
        curr_month = pd.Period(curr_month_str, freq='M')
        all_months = sorted(df["월"].unique())
        curr_index = all_months.index(curr_month)
        if curr_index == 0:
            self.table.clearContents()
            self.table.setRowCount(0)
            return
        prev_month = all_months[curr_index - 1]
        curr_df = df[df["월"] == curr_month]
        prev_df = df[df["월"] == prev_month]
        result_df = self.create_summary_table(curr_df, prev_df)
        self.populate_table(result_df)

    def handle_print(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "PDF로 저장", "", "PDF Files (*.pdf)")
            file_path = str(file_path)
            if not file_path:
                return
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'

            title = f"월 단위 현황 ({getattr(self, 'curr_month_str', '선택된 월')})"

            try:
                export_table_to_pdf(self.table, file_path, title, orientation="landscape", font_size=12)
            except Exception as export_error:
                print(f"[DEBUG] PDF Export Error: {export_error}")
                raise

        except Exception as e:
            print(f"[DEBUG] PDF Save Error: {e}")
            QMessageBox.critical(self, "오류", f"PDF 저장 중 오류 발생:\n{str(e)}")
