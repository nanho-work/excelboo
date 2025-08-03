from PyQt6.QtWidgets import QLineEdit
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
import os
import datetime

class MonthlyStoreReportView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("월별 가맹점 종합리포트")
        self.resize(1200, 800)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        filter_layout = QHBoxLayout()

        current_year = datetime.datetime.now().year
        self.year_combo = QComboBox()
        self.year_combo.addItems([str(y) for y in range(current_year - 5, current_year + 1)])
        self.year_combo.setCurrentText("2025")

        self.month_combo = QComboBox()
        self.month_combo.addItems([f"{m:02}" for m in range(1, 13)])
        self.month_combo.setCurrentText("07")

        filter_button = QPushButton("조회")
        filter_button.clicked.connect(self.apply_filter)

        filter_layout.addWidget(self.year_combo)
        filter_layout.addWidget(self.month_combo)
        filter_layout.addWidget(filter_button)
        self.layout.addLayout(filter_layout)

        label = QLabel("2025년 7월 가맹점 종합 리포트")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(label)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("검색어를 입력하세요...")
        self.search_box.setProperty("class", "search-box")
        self.search_box.textChanged.connect(self.search_data)
        self.layout.addWidget(self.search_box)

        self.load_data("2025", "07")

    def load_data(self, year, month):
        if not hasattr(self, "full_df") or self.full_df is None:
            return
        df = self.full_df.copy()

        # 날짜 전처리 및 필터링
        df["접수일"] = pd.to_datetime(df["접수일"], errors="coerce")
        filtered_df = df[df["접수일"].dt.strftime("%Y-%m") == f"{year}-{month}"]

        # 숫자 컬럼 처리
        filtered_df["입금금액"] = filtered_df["입금금액"].fillna(0).astype(int)
        filtered_df["승인금액"] = filtered_df["승인금액"].fillna(0)
        filtered_df["할부"] = pd.to_numeric(filtered_df["할부"], errors="coerce").fillna(0)

        민원발생건수 = filtered_df.groupby(['가맹점명', 'TID명']).size().reset_index(name='민원발생건수')
        전체민원수 = filtered_df.shape[0]
        민원발생건수['비중(%)'] = (민원발생건수['민원발생건수'] / 전체민원수 * 100).round(1)

        처리완료_df = filtered_df[filtered_df['처리결과'] == 'Y']
        민원처리건수 = 처리완료_df.groupby(['가맹점명', 'TID명']).size().reset_index(name='민원처리건수')

        결과 = 민원발생건수.merge(민원처리건수, on=['가맹점명', 'TID명'], how='left')
        결과['민원처리건수'] = 결과['민원처리건수'].fillna(0).astype(int)
        결과['회신율(%)'] = ((결과['민원처리건수'] / 결과['민원발생건수']) * 100).round(1)

        거래액 = filtered_df.groupby(['가맹점명', 'TID명'])['승인금액'].sum().reset_index(name='거래액')
        취소금액 = filtered_df.groupby(['가맹점명', 'TID명'])['입금금액'].sum().reset_index(name='취소금액')
        미수금_df = filtered_df[filtered_df['입금여부'] == '미입금']
        미수금 = 미수금_df.groupby(['가맹점명', 'TID명'])['입금금액'].sum().reset_index(name='미수금')

        결과 = 결과.merge(거래액, on=['가맹점명', 'TID명'], how='left')
        결과 = 결과.merge(취소금액, on=['가맹점명', 'TID명'], how='left')
        결과 = 결과.merge(미수금, on=['가맹점명', 'TID명'], how='left')
        결과[['취소금액', '미수금']] = 결과[['취소금액', '미수금']].fillna(0).astype(int)
        결과['취소비율(%)'] = ((결과['취소금액'] / 결과['거래액']) * 100).round(1)
        결과['미수비율(%)'] = ((결과['미수금'] / 결과['거래액']) * 100).round(1)

        거래건수 = filtered_df.groupby(['가맹점명', 'TID명']).size().reset_index(name='거래건수')
        결과 = 결과.merge(거래건수, on=['가맹점명', 'TID명'], how='left')
        결과['평균객단가'] = (결과['거래액'] / 결과['거래건수']).round(0).fillna(0).astype(int)

        평균할부 = filtered_df.groupby(['가맹점명', 'TID명'])['할부'].mean().reset_index(name='평균할부')
        결과 = 결과.merge(평균할부, on=['가맹점명', 'TID명'], how='left')
        결과['평균할부'] = 결과['평균할부'].fillna(0).round(1)

        결과 = 결과.fillna("")

        unique_stores = 결과['가맹점명'].nunique()
        store_summary_label = QLabel(f"총 가맹점 수: {unique_stores}")
        store_summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(store_summary_label)

        header = [
            "가맹점명", "TID명", "민원발생건수", "비중(%)", "민원처리건수", "회신율(%)", "거래액", "취소금액",
            "미수금", "취소비율(%)", "미수비율(%)", "거래건수", "평균객단가", "평균할부"
        ]
        self.table.setColumnCount(len(header))
        self.table.setRowCount(len(결과))
        self.table.setHorizontalHeaderLabels(header)

        for row_idx, row_data in 결과.iterrows():
            for col_idx, col_name in enumerate(header):
                value = row_data[col_name]

                if col_name in ["거래액", "취소금액", "미수금", "평균객단가"]:
                    display_value = f"{int(value):,}" if str(value).isdigit() else str(value)
                else:
                    display_value = str(value)

                item = QTableWidgetItem(display_value)
                if col_name in ["거래액", "취소금액", "미수금", "평균객단가"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def apply_filter(self):
        selected_year = self.year_combo.currentText()
        selected_month = self.month_combo.currentText()
        self.load_data(selected_year, selected_month)
    def search_data(self, text):
        for row in range(self.table.rowCount()):
            row_match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    value = item.text()
                    item.setBackground(Qt.GlobalColor.white)
                    if text.lower() in value.lower():
                        item.setBackground(Qt.GlobalColor.yellow)
                        row_match = True
            self.table.setRowHidden(row, not row_match if text.strip() else False)
    def set_full_data(self, df):
        self.full_df = df
        self.load_data(self.year_combo.currentText(), self.month_combo.currentText())