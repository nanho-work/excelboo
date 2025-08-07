from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QLabel, QTableWidget
)
from PyQt6.QtCore import Qt
import pandas as pd


class BaseReportWidget(QWidget):
    def __init__(
        self,
        title_text: str,
        parent=None,
        pdf_button_label: str = "PDF 저장",
        on_combo_change=None,
        on_pdf_click=None,
        extra_buttons=None
    ):
        super().__init__(parent)
        self.full_df = None
        self.on_combo_change = on_combo_change
        self.setWindowTitle(title_text)
        self.resize(1200, 800)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 필터 레이아웃 (월 콤보박스 + PDF 버튼)
        self.filter_layout = QHBoxLayout()

        self.year_combo = QComboBox()
        self.month_combo = QComboBox()
        self.day_combo = QComboBox()


        # 라벨과 콤보박스를 명확하게 세트로 추가
        self.filter_layout.addWidget(self.year_combo)
        self.filter_layout.addWidget(self.month_combo)
        self.filter_layout.addWidget(self.day_combo)

        self.export_button = QPushButton(pdf_button_label)
        if on_pdf_click:
            self.export_button.clicked.connect(on_pdf_click)
        else:
            self.export_button.clicked.connect(self.export_pdf)
        self.filter_layout.addWidget(self.export_button)

        # extra_buttons 추가
        if extra_buttons:
            for text, slot in extra_buttons:
                btn = QPushButton(text)
                btn.clicked.connect(slot)
                self.filter_layout.addWidget(btn)

        self.layout.addLayout(self.filter_layout)

        # 타이틀 라벨
        self.label = QLabel(title_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        # 테이블
        self.table = QTableWidget()
        # 콤보박스 필터 초기화 (초기 데이터가 있다면 적용)
        if self.full_df is not None:
            from utils.combo_filter import combo_fillter  # 필요한 경우 파일 경로 조정
            combo_fillter(
                self.full_df,
                self.year_combo,
                self.month_combo,
                self.day_combo,
                date_column="접수일",
                on_change_callback=on_combo_change
            )
        self.layout.addWidget(self.table)

    def set_data(self, df: pd.DataFrame):
        from utils.combo_filter import combo_fillter  # 필요한 경우 파일 경로 조정
        self.full_df = df
        combo_fillter(
            df,
            self.year_combo,
            self.month_combo,
            self.day_combo,
            date_column="접수일",
            on_change_callback=self.on_combo_change  # ensure this is stored in __init__
        )