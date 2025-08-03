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
from views.monthly_store_report_view import MonthlyStoreReportView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("민원 관리 툴")
        self.resize(1000, 700)
        qss_files = [
            "base.qss",
            "buttons.qss",
            "inputs.qss",
            "combo.qss",
            "table.qss",
            "scrollbar.qss"
        ]
        qss_path = os.path.join(os.path.dirname(__file__), "styles")
        combined_style = ""
        for qss_file in qss_files:
            file_path = os.path.join(qss_path, qss_file)
            with open(file_path, "r", encoding="utf-8") as f:
                combined_style += f.read()
        self.setStyleSheet(combined_style)

        # 전체 레이아웃
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.full_df = None  # 전체민원 데이터 저장용

        # 사이드바 버튼 메뉴
        self.menu_items = [
            "전체민원", "일 단위 현황", "월별 카드사 증감 현황",
            "월별 가맹점 종합리포트", "전체미수채권", "가맹점별미수채권현황"
        ]
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebarFrame")
        sidebar_layout = QVBoxLayout()
        sidebar_frame.setLayout(sidebar_layout)
        sidebar_frame.setFixedWidth(200)

        # 테마 전환 버튼 영역
        theme_toggle_layout = QHBoxLayout()
        self.light_mode_btn = QPushButton("일반")
        self.dark_mode_btn = QPushButton("다크")

        for theme_btn in [self.light_mode_btn, self.dark_mode_btn]:
            theme_btn.setFixedHeight(45)
            theme_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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
        self.monthly_store_report_view = MonthlyStoreReportView()
        self.stack.addWidget(self.monthly_store_report_view)
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
            btn.setProperty("selected", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # 선택된 버튼 강조
        self.buttons[index].setProperty("selected", True)
        self.buttons[index].style().unpolish(self.buttons[index])
        self.buttons[index].style().polish(self.buttons[index])

    def receive_full_data(self, df):
        self.full_df = df
        self.daily_view.set_full_data(df)
        self.monthly_view.set_full_data(df)

    def apply_theme(self, mode):
        self.setStyleSheet(self.styleSheet())

if __name__ == "__main__":
    from splash import SplashScreen
    from PyQt6.QtCore import QTimer

    app = QApplication([])

    splash = SplashScreen()
    splash.show()

    def show_main():
        global window
        window = MainWindow()
        window.show()
        splash.close()

    QTimer.singleShot(2000, lambda: splash.fade_out(show_main))
    app.exec()