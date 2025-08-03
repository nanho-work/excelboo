import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt, QMarginsF, QSize


class BarChartWidget(QWidget):
    def __init__(self, title: str, data: dict[str, int], parent=None):
        """
        재사용 가능한 그룹화 막대 차트 위젯 클래스 (PDF 저장용 고정 사이즈)

        :param title: 차트 제목 (문자열)
        :param data: 막대 차트에 표시할 데이터 (예: {"A": 10, "B": 20})
        :param parent: 부모 위젯
        """
        super().__init__(parent)
        self.title = title
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        chart = QChart()
        chart.setTitle(self.title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        if sys.platform == "darwin":
            font = QFont("Apple SD Gothic Neo", 12)
        else:
            font = QFont("Malgun Gothic", 12)
        font.setPointSize(14)
        chart.setFont(font)

        series = QBarSeries()

        merchants = list(self.data.keys())
        all_cards = set()
        for card_data in self.data.values():
            all_cards.update(card_data.keys())
        all_cards = sorted(all_cards)

        colors = [
            "#e41a1c",  # red
            "#377eb8",  # blue
            "#4daf4a",  # green
            "#984ea3",  # purple
            "#ff7f00",  # orange
            "#ffff33",  # yellow
            "#a65628",  # brown
            "#f781bf",  # pink
            "#999999",  # grey
            "#66c2a5"   # teal
        ]

        for card in all_cards:
            bar_set = QBarSet(card)
            bar_set.setColor(QColor(colors[all_cards.index(card) % len(colors)]))
            for merchant in merchants:
                bar_set.append(self.data[merchant].get(card, 0))
            series.append(bar_set)

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(merchants)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        axis_x.setLabelsAngle(40)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        legend_font = QFont(font)
        legend_font.setPointSizeF(16.0)  # or 12.0 등으로 조정
        chart.legend().setFont(legend_font)

        self.chart_view = QChartView(chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ✅ A4 사이즈 기준 고정 크기 설정 (단위: px, 300dpi 기준)
        A4_WIDTH = 1450
        A4_HEIGHT = 900
        self.chart_view.setFixedSize(A4_WIDTH, A4_HEIGHT)

        layout.addWidget(self.chart_view)
        self.setLayout(layout)

    def get_chart_view_copy(self) -> QChartView:
        original_chart = self.chart_view.chart()

        new_chart = QChart()
        new_chart.setTitle(original_chart.title())
        new_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        copied_font = QFont(original_chart.font())
        copied_font.setPointSize(16)
        new_chart.setFont(copied_font)

        for original_series in original_chart.series():
            if isinstance(original_series, QBarSeries):
                copied_series = QBarSeries()
                for original_set in original_series.barSets():
                    new_set = QBarSet(original_set.label())
                    for value in original_set:
                        new_set.append(value)
                    copied_series.append(new_set)
                new_chart.addSeries(copied_series)

                for axis in original_chart.axes():
                    if isinstance(axis, QBarCategoryAxis):
                        new_axis = QBarCategoryAxis()
                        new_axis.append(axis.categories())
                        new_chart.addAxis(new_axis, Qt.AlignmentFlag.AlignBottom)
                        copied_series.attachAxis(new_axis)
                    elif isinstance(axis, QValueAxis):
                        new_axis = QValueAxis()
                        new_chart.addAxis(new_axis, Qt.AlignmentFlag.AlignLeft)
                        copied_series.attachAxis(new_axis)

        new_chart.legend().setVisible(True)
        new_chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        legend_font = QFont(original_chart.legend().font())
        legend_font.setPointSizeF(16.0)  # 고정 크기 적용
        new_chart.legend().setFont(legend_font)

        chart_view_copy = QChartView(new_chart)
        chart_view_copy.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view_copy.setFixedSize(self.chart_view.size())

        return chart_view_copy