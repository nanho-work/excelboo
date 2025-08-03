from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel, QFileDialog, QPushButton
from utils.pdf_chart_exporter import export_qchartview_to_pdf
import pandas as pd
from widgets.bar_chart_widget import BarChartWidget

class MonthlyPieDialog(QDialog):
    # 바 차트로 구성된 월별 증감률 다이얼로그
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowTitle("월 단위 민원 비중 차트")
        self.resize(500, 400)

        self.layout = QVBoxLayout()

        self.df = df.copy()
        self.df["접수일"] = pd.to_datetime(self.df["접수일"], errors="coerce")
        self.df["연월"] = self.df["접수일"].dt.to_period("M")
        self.months = sorted(self.df["연월"].dropna().unique())

        self.combo = QComboBox()
        for m in self.months:
            self.combo.addItem(str(m))
        self.combo.currentIndexChanged.connect(self.update_chart)

        self.layout.addWidget(QLabel("월 선택"))
        self.layout.addWidget(self.combo)

        self.export_button = QPushButton("PDF로 저장")
        self.export_button.clicked.connect(self.export_pdf)
        self.layout.addWidget(self.export_button)

        self.chart = None

        self.setLayout(self.layout)

        self.update_chart()

    def update_chart(self):
        selected_month = self.combo.currentText()
        if not selected_month or not self.df is not None:
            return

        try:
            selected_period = pd.Period(selected_month)
            df = self.df.copy()
            df["월"] = df["접수일"].dt.to_period("M").astype(str)
            df["카드사"] = df["카드사"].astype(str).str.strip()
            df["가맹점명"] = df["가맹점명"].astype(str).str.strip()

            grouped = df.groupby(["월", "가맹점명", "카드사"]).size().reset_index(name="민원건수")
            pivot = grouped.pivot_table(index=["가맹점명", "카드사"], columns="월", values="민원건수", fill_value=0)
            pivot = pivot.sort_index(axis=1)

            if selected_month not in pivot.columns:
                chart_data = {}
                if self.chart:
                    self.layout.removeWidget(self.chart)
                    self.chart.deleteLater()
                self.chart = BarChartWidget(f"{selected_month} 가맹점별 카드사 증감률", chart_data)
                from PyQt6.QtWidgets import QSizePolicy
                self.chart.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
                self.layout.addWidget(self.chart)
                return

            month_index = list(pivot.columns).index(selected_month)
            if month_index == 0:
                return  # 전월이 존재하지 않음

            pre_month = list(pivot.columns)[month_index - 1]
            cur_month = selected_month

            pivot = pivot.reset_index()
            merchants = pivot["가맹점명"].unique()
            chart_data = {}

            for merchant in merchants:
                merchant_df = pivot[pivot["가맹점명"] == merchant]
                card_data = {}
                for _, row in merchant_df.iterrows():
                    pre = row.get(pre_month, 0)
                    cur = row.get(cur_month, 0)
                    if pre == 0:
                        rate = 0
                    else:
                        rate = ((cur - pre) / pre) * 100
                    card_data[row["카드사"]] = round(rate, 1)
                chart_data[merchant] = card_data

            if self.chart:
                self.layout.removeWidget(self.chart)
                self.chart.deleteLater()

            self.chart = BarChartWidget(f"{selected_month} 가맹점별 카드사 증감률", chart_data)
            from PyQt6.QtWidgets import QSizePolicy
            self.chart.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            self.layout.addWidget(self.chart)

        except Exception as e:
            print(f"차트 갱신 오류: {e}")

    def export_pdf(self):
        if not self.chart:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "PDF로 저장", "", "PDF Files (*.pdf)")
        if file_path:
            selected_month = self.combo.currentText()
            title = f"{selected_month} 가맹점별 카드사 증감률"
            export_qchartview_to_pdf(self.chart.chart_view, file_path, title=title)