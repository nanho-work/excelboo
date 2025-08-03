import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from .daily_detail_dialog import DailyDetailDialog
from .daily_summary_viewer import DailySummaryViewer
from widgets.pie_chart_widget import PieChartWidget
from .daily_pie_dialog import DailyPieDialog

class DailyStatusView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.summary_button = QPushButton("PDF 파일 생성")
        self.summary_button.clicked.connect(self.show_summary_viewer)
        self.chart_button = QPushButton("차트 보기")
        self.chart_button.clicked.connect(self.show_chart_dialog)
        self.full_df = None  # To hold externally provided DataFrame

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.summary_button)
        button_layout.addWidget(self.chart_button)
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)
        self.table.cellDoubleClicked.connect(self.show_detail_popup)

    def set_full_data(self, df):
        self.full_df = df
        self.generate_report()

    def generate_report(self):
        if self.full_df is None:
            # self.label.setText("전체민원 데이터가 없습니다.")
            return
        try:
            df = self.full_df.copy()
            df = df.fillna("")
            df.columns = df.columns.str.strip()
            required_cols = ["접수일", "가맹점명", "TID명", "처리상태"]
            if not all(col in df.columns for col in required_cols):
                # self.label.setText("필수 컬럼이 누락됨")
                return
            df["접수일"] = pd.to_datetime(df["접수일"], errors="coerce")
            df = df.dropna(subset=["접수일"])
            df["접수일"] = df["접수일"].dt.date
            grouped = df.groupby(["접수일", "가맹점명", "TID명"]).agg(
                민원건수=("TID명", "count"),
                기한내처리건수=("처리상태", lambda x: x.str.lower().eq("y").sum())
            ).reset_index()
            grouped["회신율"] = ((grouped["기한내처리건수"] / grouped["민원건수"]) * 100).round(1).astype(str) + "%"
            total_by_date = grouped.groupby("접수일")["민원건수"].transform("sum")
            grouped["날짜별민원비중"] = ((grouped["민원건수"] / total_by_date) * 100).round(1).astype(str) + "%"
            column_order = ["접수일", "가맹점명", "TID명", "날짜별민원비중", "민원건수", "기한내처리건수", "회신율"]
            grouped = grouped[column_order]
            self.display_table(grouped)
            # self.label.setText("일 단위 현황 생성 완료")
            self.debug_column_types()
        except Exception as e:
            # self.label.setText(f"현황 생성 실패: {e}")
            pass

    def display_table(self, df):
        # 접수일 + 가맹점명 기준 중복 제거 표시
        df = df.copy()
        df["__combined_key"] = df["접수일"].astype(str) + "|" + df["가맹점명"]
        df.loc[df["__combined_key"].duplicated(), "접수일"] = ""
        df.loc[df["__combined_key"].duplicated(), "가맹점명"] = ""
        df.drop(columns=["__combined_key"], inplace=True)

        self.table.clear()
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df))
        self.table.setHorizontalHeaderLabels(df.columns)

        # Set header font, alignment, and background
        from PyQt6.QtGui import QFont, QColor, QBrush
        header_font = QFont()
        header_font.setBold(True)
        for i in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(i)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(QColor("#f0f0f0")))

        # Set default row height and alternating row colors
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setAlternatingRowColors(True)

        for i, row in df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                if j == 0 or j == 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                elif "건수" in df.columns[j] or "율" in df.columns[j] or "비중" in df.columns[j]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()

    def show_detail_popup(self, row, column):
        date_item = self.table.item(row, 0)  # Assumes 접수일 is in the first column
        if date_item is None or not date_item.text().strip():
            return
        selected_date = date_item.text().strip()
        detail_df = self.full_df.copy()
        detail_df["접수일"] = pd.to_datetime(detail_df["접수일"], errors="coerce").dt.date
        filtered = detail_df[detail_df["접수일"].astype(str) == selected_date]

        if not filtered.empty:
            dlg = DailyDetailDialog(filtered, selected_date, self)
            dlg.exec()

    def show_summary_viewer(self):
        if self.full_df is not None:
            dlg = DailySummaryViewer(self.full_df, self)
            dlg.exec()

    def show_chart_dialog(self):
        if self.full_df is None:
            return
        df = self.full_df.copy()
        dlg = DailyPieDialog(df, self)
        dlg.exec()
    def debug_column_types(self):
        if self.full_df is not None:
            print("📌 전체 컬럼 데이터 타입:")
            for col in self.full_df.columns:
                print(f"{col}: {self.full_df[col].dtype}")
            print("\n📌 컬럼별 실제 타입 샘플:")
            for col in self.full_df.columns:
                types = self.full_df[col].apply(lambda x: str(type(x))).value_counts()
                print(f"{col}: {dict(types)}")
        else:
            print("❌ 전체민원 데이터가 없습니다.")