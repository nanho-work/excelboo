import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt


class PieChartWidget(QWidget):
    def __init__(self, title: str, data: dict[str, int], parent=None):
        """
        재사용 가능한 파이 차트 위젯 클래스

        :param title: 차트 제목 (문자열)
        :param data: 파이 차트에 표시할 데이터 (예: {"A": 10, "B": 20})
        :param parent: 부모 위젯
        """
        super().__init__(parent)  # 부모 클래스 초기화
        self.title = title      # 차트 제목 저장
        self.data = data        # 차트 데이터 저장

        self.init_ui()          # UI 구성 함수 호출

    def init_ui(self):
        # 전체 레이아웃을 수직 박스로 설정
        layout = QVBoxLayout(self)

        # QChart 객체 생성 (차트의 메인 영역)
        chart = QChart()
        chart.setTitle(self.title)  # 차트 상단 제목 설정
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)  # 애니메이션 효과 활성화

        # 시스템에 따라 한글 폰트 설정 (macOS: AppleGothic, Windows: Malgun Gothic)
        if sys.platform == "darwin":
            font = QFont("Apple SD Gothic Neo", 10)
        else:
            font = QFont("Malgun Gothic", 10)

        chart.setFont(font)  # 차트 제목 폰트 적용

        # 파이 데이터 시리즈 객체 생성
        series = QPieSeries()

        # 파스텔톤 색상 리스트 (연녹색, 연주황, 연파랑 등)
        colors = ["#A8E6CF", "#FFD3B6", "#B3E5FC", "#FFFACD", "#D7BDE2"]

        # 전달받은 딕셔너리 데이터를 기반으로 파이 조각 추가
        for index, (label, value) in enumerate(self.data.items()):
            slice = QPieSlice(label, value)
            slice.setBrush(QColor(colors[index % len(colors)]))
            slice.setLabelVisible(True)
            percentage = value / sum(self.data.values()) * 100
            slice.setLabel(f"{label} ({value}건, {percentage:.1f}%)")
            if slice.percentage() > 0.3:
                slice.setLabelPosition(QPieSlice.LabelPosition.LabelInsideHorizontal)
            else:
                slice.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)
            series.append(slice)

        # 차트에 시리즈 추가
        chart.addSeries(series)

        # 범례(legend) 표시 및 우측 정렬
        chart.legend().setVisible(True)  # 범례 보이기
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)  # 우측 정렬
        chart.legend().setFont(font)  # 범례 폰트 적용

        # 차트를 보여줄 뷰 생성 및 부드럽게 렌더링 설정
        self.chart_view = QChartView(chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)  # 안티앨리어싱(부드럽게)

        # 최종 차트 뷰를 레이아웃에 추가
        layout.addWidget(self.chart_view)

        # 레이아웃 설정
        self.setLayout(layout)

    def get_chart_view_copy(self) -> QChartView:
        """
        현재 chart_view의 복사본을 생성하여 반환 (PDF 저장용)
        원본 미리보기에 영향을 주지 않기 위해 별도 인스턴스를 사용
        """
        original_chart = self.chart_view.chart()

        # 새로운 QChart 인스턴스 생성
        new_chart = QChart()
        new_chart.setTitle(original_chart.title())
        new_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        new_chart.setFont(original_chart.font())

        # 시리즈 복사 (깊은 복사)
        for original_series in original_chart.series():
            if isinstance(original_series, QPieSeries):
                copied_series = QPieSeries()
                for original_slice in original_series.slices():
                    new_slice = QPieSlice(original_slice.label(), original_slice.value())
                    new_slice.setBrush(original_slice.brush())
                    new_slice.setLabelVisible(original_slice.isLabelVisible())
                    new_slice.setLabel(original_slice.label())
                    new_slice.setLabelPosition(original_slice.labelPosition())
                    copied_series.append(new_slice)
                new_chart.addSeries(copied_series)

        # 범례 설정 복사
        new_chart.legend().setVisible(True)
        new_chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        new_chart.legend().setFont(original_chart.legend().font())

        # QChartView 복사본 생성 (사이즈 설정은 익스포터에서 조절)
        chart_view_copy = QChartView(new_chart)
        chart_view_copy.setRenderHint(QPainter.RenderHint.Antialiasing)
        return chart_view_copy
    
