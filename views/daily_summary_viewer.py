# daily_summary_viewer.py
import pandas as pd
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QHeaderView
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from utils.pdf_exporter import export_table_to_pdf


class DailySummaryViewer(QDialog):
    def __init__(self, full_df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("일자별 요약 및 시각화")
        self.resize(800, 600)

        self.df = full_df.copy()
        self.df["접수일"] = pd.to_datetime(self.df["접수일"], errors="coerce").dt.date

        self.layout = QVBoxLayout()
        self.date_selector = QComboBox()
        self.date_selector.addItems(sorted({str(d) for d in self.df["접수일"].dropna().unique()}))
        self.date_selector.currentIndexChanged.connect(self.update_view)

        self.label = QLabel("날짜를 선택하세요")
        self.table = QTableWidget()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.date_selector)
        self.layout.addWidget(self.table)

        self.print_button = QPushButton("PDF로 저장")
        self.print_button.clicked.connect(self.handle_print)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)

        self.update_view()

    def update_view(self):
        selected_date = self.date_selector.currentText()
        if not selected_date:
            return

        filtered = self.df[self.df["접수일"].astype(str) == selected_date]
        filtered = filtered.fillna("")
        # Ensure 'TID명' column is one-dimensional and string-typed
        filtered["TID명"] = filtered["TID명"].apply(
            lambda x: x[0] if isinstance(x, (list, tuple)) and len(x) > 0 else ("" if pd.isna(x) else str(x))
        )
        filtered["TID명"] = filtered["TID명"].astype(str)
        print("TID명 column ndim:", filtered["TID명"].ndim)
        print("TID명 column type sample:", type(filtered["TID명"].iloc[0]))
        # ✅ groupby().agg()로 집계
        filtered["기한내처리여부"] = filtered["처리상태"].str.lower() == "y"
        grouped = (
            filtered.groupby(["가맹점명", "TID명"])
            .agg(
                민원건수=("TID명", "count"),
                기한내처리건수=("기한내처리여부", "sum")
            )
            .reset_index()
        )

        # ✅ 처리율 및 비중 계산 및 컬럼 순서 재배치
        total_complaints_day = grouped["민원건수"].sum()
        grouped["민원비중(%)"] = grouped["민원건수"].apply(
            lambda x: f"{(x / total_complaints_day * 100):.1f}%" if total_complaints_day else "0.0%"
        )
        grouped = grouped[["가맹점명", "TID명", "민원건수", "민원비중(%)", "기한내처리건수"]]
        grouped["처리율"] = ((grouped["기한내처리건수"] / grouped["민원건수"]) * 100).round(1).astype(str) + "%"
        grouped = grouped[["가맹점명", "TID명", "민원건수", "민원비중(%)", "기한내처리건수", "처리율"]]

        # 테이블에 데이터 표시
        self.table.setRowCount(len(grouped))
        self.table.setColumnCount(len(grouped.columns))
        self.table.setHorizontalHeaderLabels(grouped.columns)

        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        prev_store = None
        for i, row in grouped.iterrows():
            for j, val in enumerate(row):
                # Replace duplicate "가맹점명" values with empty string except first occurrence
                if j == 0:
                    if val == prev_store:
                        display_val = ""
                    else:
                        display_val = val
                        prev_store = val
                else:
                    display_val = val
                item = QTableWidgetItem(str(display_val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, j, item)

        # 합계 행 추가
        total_rows = len(grouped)
        self.table.insertRow(total_rows)
        self.table.setSpan(total_rows, 0, 1, 2)
        sum_item = QTableWidgetItem("합계")
        sum_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        sum_item.setFlags(sum_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(total_rows, 0, sum_item)

        total_complaints = grouped["민원건수"].sum()
        total_processed = grouped["기한내처리건수"].sum()
        total_rate = f"{(total_processed / total_complaints * 100):.1f}%" if total_complaints else "0.0%"

        self.table.setItem(total_rows, 2, QTableWidgetItem(str(total_complaints)))
        self.table.setItem(total_rows, 3, QTableWidgetItem("100.0%"))
        self.table.setItem(total_rows, 4, QTableWidgetItem(str(total_processed)))
        self.table.setItem(total_rows, 5, QTableWidgetItem(total_rate))
        for col in [2, 3, 4, 5]:
            item = self.table.item(total_rows, col)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)

        # 열 너비 자동 조정
        self.table.resizeColumnsToContents()

        # 글꼴 크기에 따라 행 높이 자동 조정
        font = self.table.font()
        font.setPointSize(16)
        self.table.setFont(font)

        metrics = self.table.fontMetrics()
        row_height = metrics.height() + 20  # Add padding

        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, row_height)

    def handle_print(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "PDF로 저장", "", "PDF Files (*.pdf)")
            if file_path:
                if not file_path.lower().endswith(".pdf"):
                    file_path += ".pdf"
                export_table_to_pdf(self.table, file_path, f"{self.date_selector.currentText()} 일일민원보고", orientation="portrait")
        except Exception as e:
            print(f"PDF 저장 중 오류 발생: {e}")