# 월 단위 현황
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtWidgets import QPushButton, QFileDialog
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt
import pandas as pd

from openpyxl import load_workbook
from PyQt6.QtGui import QFont, QColor, QBrush

class MonthlyStatusView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("월 단위 현황")

        layout = QVBoxLayout()
        self.label = QLabel("월 단위 현황 데이터 없음")
        self.summary_button = QPushButton("PDF 파일 생성")
        self.summary_button.clicked.connect(self.show_summary_viewer)
        self.table = QTableWidget()
        layout.addWidget(self.label)
        layout.addWidget(self.summary_button)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # self.load_monthly_stats()  # 외부에서 set_full_data로 로드

    def set_full_data(self, df):
        self.full_df = df
        self.generate_report()

    # Updated generate_report logic to format in 가맹점별 x 카드사 3열 그룹 형태 as per user design
    def generate_report(self):
        if self.full_df is None:
            return
        try:
            df = self.full_df.copy()
            df = df.fillna("")
            df.columns = df.columns.str.strip()
            if "접수일" not in df.columns or "카드사" not in df.columns or "가맹점명" not in df.columns:
                return

            df["접수일"] = pd.to_datetime(df["접수일"], errors="coerce")
            df = df.dropna(subset=["접수일"])
            df["월"] = df["접수일"].dt.to_period("M").astype(str)

            # 가맹점 + 카드사 별로 월 단위 민원 수 집계
            df["카드사"] = df["카드사"].astype(str).str.strip()
            df["가맹점명"] = df["가맹점명"].astype(str).str.strip()

            grouped = df.groupby(["월", "가맹점명", "카드사"]).size().reset_index(name="민원건수")

            # 전월/당월 데이터 pivot
            pivot = grouped.pivot_table(index=["가맹점명", "카드사"], columns="월", values="민원건수", fill_value=0)

            # 월 정렬을 위해 컬럼 정렬
            pivot = pivot.sort_index(axis=1)

            # 최근 2개월만 추출 및 새로운 구조로 변환
            if len(pivot.columns) >= 2:
                last_two_months = pivot.columns[-2:]
                pre_month = last_two_months[-2]
                cur_month = last_two_months[-1]

                # Prepare a DataFrame with 가맹점명 as index and 카드사 as columns
                # We want columns: for each 카드사: pre_month count, cur_month count, 증감률

                # Reset index to access columns
                pivot = pivot.reset_index()

                # Get unique 가맹점명
                merchants = pivot["가맹점명"].unique()

                # Get unique 카드사
                card_companies = pivot["카드사"].unique()

                # Prepare a dict to collect data for each merchant
                data = {"가맹점명": merchants}

                # Create a DataFrame to accumulate results
                result_df = pd.DataFrame({"가맹점명": merchants})

                for card in card_companies:
                    # Filter rows for this 카드사
                    card_df = pivot[pivot["카드사"] == card]

                    # Create Series indexed by 가맹점명 for pre and cur month counts
                    pre_counts = card_df.set_index("가맹점명").get(pre_month, pd.Series(dtype=int))
                    cur_counts = card_df.set_index("가맹점명").get(cur_month, pd.Series(dtype=int))

                    # Align with all merchants, fill missing with 0
                    pre_counts = pre_counts.reindex(merchants, fill_value=0)
                    cur_counts = cur_counts.reindex(merchants, fill_value=0)

                    # Compute 증감률 safely
                    with pd.option_context('mode.use_inf_as_na', True):
                        diff = cur_counts - pre_counts
                        rate = pd.Series(index=merchants, dtype=float)
                        rate = (diff / pre_counts.replace(0, pd.NA)) * 100
                        rate = rate.fillna(0)

                    # Add columns to result_df
                    result_df[f"{card}_전월"] = pre_counts.values
                    result_df[f"{card}_당월"] = cur_counts.values
                    result_df[f"{card}_증감률"] = rate.values.round(1)

                self.populate_table(result_df)
            else:
                self.populate_table(pd.DataFrame(columns=["가맹점명"]))

        except Exception as e:
            print("월 단위 현황 생성 실패:", e)

    def populate_table(self, df):
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        from PyQt6.QtGui import QFont, QColor, QBrush

        # 헤더 스타일 적용
        header_font = QFont()
        header_font.setBold(True)

        for i in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(i)
            if item:
                item.setFont(header_font)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(QColor("#f0f0f0")))

        # 테이블 기본 스타일
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setAlternatingRowColors(True)

        for row_idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                col_name = df.columns[col_idx]
                if col_name == "가맹점명":
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                elif col_name.endswith("_전월") or col_name.endswith("_당월"):
                    # Format as int with thousands separator
                    try:
                        int_val = int(value)
                        item = QTableWidgetItem(f"{int_val:,}")
                    except:
                        item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col_name.endswith("_증감률"):
                    # Format as float with 1 decimal and % sign, with arrow and color
                    try:
                        float_val = float(value)
                        if float_val > 0:
                            text = f"▲ {float_val:.1f}%"
                            item = QTableWidgetItem(text)
                            item.setForeground(QBrush(QColor("#e74c3c")))  # red
                        elif float_val < 0:
                            text = f"▼ {abs(float_val):.1f}%"
                            item = QTableWidgetItem(text)
                            item.setForeground(QBrush(QColor("#3498db")))  # blue
                        else:
                            text = f"{float_val:.1f}%"
                            item = QTableWidgetItem(text)
                            item.setForeground(QBrush(QColor("#7f8c8d")))  # gray
                    except:
                        item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()
    def show_summary_viewer(self):
        if self.full_df is not None:
            # TODO: Replace 'MonthlySummaryViewer' with actual viewer dialog class
            from .monthly_summary_viewer import MonthlySummaryViewer
            dlg = MonthlySummaryViewer(self.full_df, self)
            dlg.exec()