import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt

from views.daily_status_view import DailyStatusView
from views.monthly_status_view import MonthlyStatusView
from views.complaints_view import ComplaintsView
#
from views.unpaid_total_view import UnpaidTotalView
from views.unpaid_by_store_view import UnpaidByStoreView
#

from styles.button_styles import modern_default_button_style, selected_button_style, gradient_button_style
from styles.theme_dark import dark_style
from styles.theme_light import light_style

from styles.scrollbar_styles import modern_scrollbar_style

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("민원 관리 툴")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #ffffff;")

        # 전체 레이아웃
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.full_df = None  # 전체민원 데이터 저장용

        # 사이드바 버튼 메뉴
        self.menu_items = [
            "전체민원", "일 단위 현황", "월 단위 현황",
            "전체미수채권", "가맹점별미수채권현황"
        ]
        sidebar_frame = QFrame()
        sidebar_layout = QVBoxLayout()
        sidebar_frame.setLayout(sidebar_layout)
        sidebar_frame.setFixedWidth(200)
        sidebar_frame.setStyleSheet("""
            background-color: #f5f0e6;
            border-top-right-radius: 12px;
            border-bottom-right-radius: 12px;
        """)

        # 테마 전환 버튼 영역
        theme_toggle_layout = QHBoxLayout()
        self.light_mode_btn = QPushButton("일반")
        self.dark_mode_btn = QPushButton("다크")

        for theme_btn in [self.light_mode_btn, self.dark_mode_btn]:
            theme_btn.setFixedHeight(45)
            theme_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            theme_btn.setStyleSheet(modern_default_button_style)

        self.light_mode_btn.clicked.connect(lambda: self.apply_theme("light"))
        self.dark_mode_btn.clicked.connect(lambda: self.apply_theme("dark"))

        theme_toggle_layout.addWidget(self.light_mode_btn)
        theme_toggle_layout.addWidget(self.dark_mode_btn)
        sidebar_layout.addLayout(theme_toggle_layout)

        self.buttons = []
        for index, name in enumerate(self.menu_items):
            btn = QPushButton(name)
            btn.setFixedHeight(45)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(modern_default_button_style)
            btn.clicked.connect(lambda checked, idx=index: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)
        sidebar_layout.addStretch()

        # 콘텐츠 영역
        self.complaints_view = ComplaintsView()
        self.complaints_view.data_loaded.connect(self.receive_full_data)
        self.daily_view = DailyStatusView()
        self.monthly_view = MonthlyStatusView()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.complaints_view)  # 전체민원 첫 페이지로
        self.stack.addWidget(self.daily_view)
        self.stack.addWidget(self.monthly_view)
        self.stack.addWidget(UnpaidTotalView())
        self.stack.addWidget(UnpaidByStoreView())

        self.stack.setCurrentIndex(0)  # 첫 페이지 설정

        # 레이아웃 배치
        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.stack)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)

        # 모든 버튼 기본 스타일로 리셋
        for i, btn in enumerate(self.buttons):
            btn.setStyleSheet(modern_default_button_style)

        # 선택된 버튼 강조
        self.buttons[index].setStyleSheet(selected_button_style)

    def receive_full_data(self, df):
        self.full_df = df
        self.daily_view.set_full_data(df)
        self.monthly_view.set_full_data(df)

    def apply_theme(self, mode):
        if mode == "dark":
            self.setStyleSheet(dark_style)
            self.dark_mode_btn.setStyleSheet(selected_button_style)
            self.light_mode_btn.setStyleSheet(modern_default_button_style)
        else:
            self.setStyleSheet(light_style)
            self.light_mode_btn.setStyleSheet(selected_button_style)
            self.dark_mode_btn.setStyleSheet(modern_default_button_style)

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(modern_scrollbar_style)
    window = MainWindow()
    window.show()
    app.exec()