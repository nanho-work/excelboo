# QPixmap: 이미지를 생성하고 조작하는 데 사용하는 클래스 (렌더링용)
from PyQt6.QtGui import QPixmap

# QSize: 너비와 높이를 나타내는 크기 객체
from PyQt6.QtCore import QSize

# QPainter: PDF 또는 이미지에 그래픽을 그릴 수 있게 해주는 클래스
# QPdfWriter: PDF 파일을 생성하고 작성하는 데 사용하는 클래스
# QPageSize: 페이지 크기를 설정하기 위한 클래스
from PyQt6.QtGui import QPainter, QPdfWriter, QPageSize

# QRectF: 부동소수점 기반 사각형 좌표 (텍스트 정렬 등에서 사용)
# Qt: Qt에서 제공하는 다양한 상수 (정렬 옵션 등 포함)
from PyQt6.QtCore import QRectF, Qt

# QChartView: Qt 차트를 포함하는 뷰 위젯
from PyQt6.QtCharts import QChartView

# QSizeF: 부동소수점 기반의 크기 정보
from PyQt6.QtCore import QSizeF

# QChartView에서 내부 차트 영역만 캡처하여 PDF로 저장하는 함수
def export_qchartview_to_pdf(chart_view, file_path: str, title: str = ""):
    from PyQt6.QtCore import QRectF, Qt
    from PyQt6.QtGui import QPainter, QPdfWriter, QPageSize
    from PyQt6.QtWidgets import QApplication

    pdf_writer = QPdfWriter(file_path)
    pdf_writer.setResolution(300)
    pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

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