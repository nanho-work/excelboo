from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtWidgets import QFileDialog, QPushButton
from utils.pdf_chart_exporter import export_qchartview_to_pdf
import pandas as pd
from widgets.pie_chart_widget import PieChartWidget

class DailyPieDialog(QDialog):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowTitle("일 단위 민원 비중 차트")
        self.setMinimumSize(600, 500)
        self.setMaximumSize(600, 500)

        # 전체 레이아웃
        self.layout = QVBoxLayout()

        # 콤보박스용 데이터 로딩
        self.df = df.copy()
        self.df["접수일"] = pd.to_datetime(self.df["접수일"], errors="coerce").dt.date
        self.dates = sorted(self.df["접수일"].dropna().unique())
        

        # 날짜 선택 콤보박스
        self.combo = QComboBox()
        for d in self.dates:
            self.combo.addItem(str(d))
        self.combo.currentIndexChanged.connect(self.update_chart)

        self.layout.addWidget(QLabel("날짜 선택"))
        self.layout.addWidget(self.combo)

        self.export_button = QPushButton("PDF로 저장")
        self.export_button.clicked.connect(self.export_pdf)
        self.layout.addWidget(self.export_button)

        # 첫 날짜 차트 생성
        self.chart = None
        self.update_chart()

        self.setLayout(self.layout)

    def update_chart(self):
        # 현재 날짜 선택
        selected_date = self.combo.currentText()
        if not selected_date:
            return

        filtered = self.df[self.df["접수일"] == pd.to_datetime(selected_date).date()]
        total = filtered["TID명"].count()
        data_dict = {
            name: {"count": count, "percent": round(count / total * 100, 1)}
            for name, count in filtered.groupby("가맹점명")["TID명"].count().items()
        }
        chart_data = {k: v["count"] for k, v in data_dict.items()}

        # 기존 차트 제거
        if self.chart:
            self.layout.removeWidget(self.chart)
            self.chart.deleteLater()

        # 새 차트 추가
        self.chart = PieChartWidget(f"{selected_date} 가맹점별 민원 비중", chart_data)
        from PyQt6.QtWidgets import QSizePolicy
        self.chart.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.layout.addWidget(self.chart)

    def export_pdf(self):
        if not self.chart:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "PDF로 저장", "", "PDF Files (*.pdf)")
        if file_path:
            selected_date = self.combo.currentText()
            title = f"{selected_date} 가맹점별 민원 비중 차트"
            export_qchartview_to_pdf(self.chart.chart_view, file_path, title=title)