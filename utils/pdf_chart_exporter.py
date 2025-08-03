from PyQt6.QtCore import QSize, QRectF, Qt, QSizeF, QMarginsF
from PyQt6.QtGui import QPixmap, QPainter, QPdfWriter, QPageSize, QPageLayout
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCharts import QChartView
from PyQt6.QtCharts import QPieSeries

# QChartView에서 내부 차트 영역만 캡처하여 PDF로 저장하는 함수
def export_qchartview_to_pdf(chart_view, file_path: str, title: str = ""):
    pdf_writer = QPdfWriter(file_path)
    pdf_writer.setResolution(300)
    pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))  # 크기 설정
    pdf_writer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Landscape, QMarginsF(0, 0, 0, 0)))

    chart = chart_view.chart()

    # 공통 폰트 설정
    base_font = chart.font()
    base_font.setPointSizeF(10.0)
    chart.setFont(base_font)

    # 시리즈 유형별로 설정 적용
    for series in chart.series():
        if isinstance(series, QPieSeries):
            series.setLabelsVisible(True)
            for slice in series.slices():
                slice.setLabelFont(base_font)
        elif hasattr(series, "barSets"):  # QBarSeries 또는 유사 객체
            chart.legend().setFont(base_font)

    chart.legend().setFont(base_font)

    painter = QPainter(pdf_writer)
    try:
        y_offset = 60
        
        # 렌더링 준비
        QApplication.processEvents()
        chart_view.repaint()

        # PDF 안에서 사용할 영역
        available_width = pdf_writer.width()
        available_height = pdf_writer.height() - y_offset

        # 차트 원본 크기
        chart_width = chart_view.size().width() or available_width
        chart_height = chart_view.size().height() or available_height

        # 축소 비율만 허용 (업스케일 금지)
        scale_x = available_width / chart_width
        scale_y = available_height / chart_height
        scale = min(scale_x, scale_y, 1.0)  # 1.0 초과하면 확대하지 않음

        # 원하는 위치: 위/왼쪽으로 붙이기. 중앙 정렬을 제거하고 좌측 마진과 제목 아래 여백만 적용
        left_margin = 20  # 좌측으로부터의 여백
        top_margin = 10   # 제목 아래로 약간 띄움
        x = left_margin
        y = y_offset + top_margin
        painter.save()
        # 위치를 왼쪽 위 기준으로 이동시키고 스케일 적용
        painter.translate(x, y)
        # 기존 계산된 scale은 그대로 유지하여 필요한 경우 축소(또는 확대 허용 시) 적용
        painter.scale(scale, scale)
        chart_view.render(painter)
        painter.restore()
    finally:
        painter.end()