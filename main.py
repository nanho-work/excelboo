from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt

from views.daily_status_view import DailyStatusView
from views.monthly_status_view import MonthlyStatusView
from views.complaints_view import ComplaintsView
from views.transfer_view import TransferView
from views.submall_view import SubmallView
from views.unpaid_total_view import UnpaidTotalView
from views.unpaid_by_store_view import UnpaidByStoreView
from views.galaxia_policy_view import GalaxiaPolicyView
from views.hanacard_incident_view import HanacardIncidentView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("민원 관리 툴")
        self.resize(1000, 700)

        # 전체 레이아웃
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.full_df = None  # 전체민원 데이터 저장용

        # 사이드바 버튼 메뉴
        self.menu_items = [
            "전체민원", "일 단위 현황", "월 단위 현황", "민원 이관",
            "하위몰", "전체미수채권", "가맹점별미수채권현황", "갤럭시아정책", "하나카드 사고건"
        ]
        sidebar_frame = QFrame()
        sidebar_layout = QVBoxLayout()
        sidebar_frame.setLayout(sidebar_layout)
        sidebar_frame.setFixedWidth(200)
        sidebar_frame.setStyleSheet("background-color: #f0f0f0;")

        self.buttons = []
        for index, name in enumerate(self.menu_items):
            btn = QPushButton(name)
            btn.setFixedHeight(50)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: none;
                    padding: 1px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #d0e7ff;
                }
                QPushButton:pressed {
                    background-color: #a0cfff;
                }
            """)
            btn.clicked.connect(lambda checked, idx=index: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)

        # 콘텐츠 영역
        self.complaints_view = ComplaintsView()
        self.complaints_view.data_loaded.connect(self.receive_full_data)
        self.daily_view = DailyStatusView()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.complaints_view)  # 전체민원 첫 페이지로
        self.stack.addWidget(self.daily_view)
        self.stack.addWidget(MonthlyStatusView())
        self.stack.addWidget(TransferView())
        self.stack.addWidget(SubmallView())
        self.stack.addWidget(UnpaidTotalView())
        self.stack.addWidget(UnpaidByStoreView())
        self.stack.addWidget(GalaxiaPolicyView())
        self.stack.addWidget(HanacardIncidentView())

        self.stack.setCurrentIndex(0)  # 첫 페이지 설정

        # 레이아웃 배치
        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.stack)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)

    def receive_full_data(self, df):
        self.full_df = df
        self.daily_view.set_full_data(df)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()